# -*- encoding: utf-8 -*-

"""

SOAP client for Anevia interfaces

Method calls only return the return field of the response.
An exception is thrown when receiving a non-0 status code.
SOAP lists and maps are converted from/to python types.

SOAP structures can be provided as tuples (positional arguments) or dicts
(named arguments).
StringMaps can be provided as dicts.
Most SOAP lists with a single 'item' field (for instance, StringLists) can be
provided as Python lists.


Example:

  from SoapClient import SoapClient
  # create client, provide the SOAP server address and the interface name
  cl = SoapClient('localhost', 'vod')

  # call API methods
  rec = cl.Create_record_session('udp://239.2.1.1:1234', 'file://disk1:rec.ts')
  print(cl.Get_session_info(rec))
  cb = cl.Create_circular_buffer('disk1:news', 'udp://239.2.1.1', {
    'cbDuration': 47*60, 'fragmentDuration': 7*60,
  })

"""

import suds, suds.client
import re
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
import ssl
import SoapGen


# python3 compatibility
import sys
if sys.version_info > (3, 0):
    long = int
    basestring = str

class SoapError(Exception):
    pass

class SoapStatusError(SoapError):
    def __init__(self, code, msg=None, ret=None):
        if msg is None:
            SoapError.__init__(self, code)
        else:
            SoapError.__init__(self, msg)
        self.code = code
        self.msg = msg
        self.ret = ret

    def __str__(self):
        if self.ret is not None:
            return "(%d) %s, returns: %s" % (self.code, self.msg, self.ret)
        else:
            return "(%d) %s" % (self.code, self.msg)


class ClientRedirectException(Exception):
    def __init__(self, oldurl, newurl):
        self.oldurl = oldurl
        self.newurl = newurl

    def __str__(self):
        return "client redirect from '%s' to '%s'" % (self.oldurl, self.newurl)

class MyHttpRedirectHandler(urllib2.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # throw an exception on redirect for WSDL fetch
        # it will be detected to create an new client
        # it's rough but it will work for our case
        oldurl = req.get_full_url()
        if oldurl.endswith('/wsdl/'):
            m = req.get_method()
            if code in (301, 302, 303, 307) and m in ('GET', 'HEAD'):
                raise ClientRedirectException(oldurl, newurl)
        return urllib2.HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)


class SoapClient(object):
    """
    Client for Anevia SOAP interfaces.
    """

    def __init__(self, addr, intf=None, auth=None):
        """Create a new SOAP client.

        addr -- HTTP URI of the SOAP server
        intf -- a SoapGen.Interface instance, a SOAP name or None
        auth -- a (username, password) pair, True or None

        addr may be a full URI or only an address (host:port).
        A 'soap-NAME' part will be appended if needed.
        The WSDL address is obtained by appending 'wsdl/' to the URI.

        If intf is None, no Anevia-specific processing is applied to URIs.
        addr must be a full URI, intf is built from the WSDL and service location
        is found in the WSDL.

        If auth is True, ('admin', 'paris') will be used.

        Examples, if intf.namespace is 'foo':
          flamingo:1980 -> http://flamingo:1980/soap-foo/
          http://localhost/sub/path -> http://localhost/sub/path/soap-foo/
          http://localhost/soap-bar -> http://localhost/soap-bar/

        """

        self.soap_name = None
        if intf is not None:
            if '/' not in addr:
                addr = 'http://%s/' % addr
            elif not addr.endswith('/'):
                addr += '/'
            if re.search(r'/soap-\w+/$', addr) is None:
                try:
                    soap_name = intf.namespace
                except AttributeError:
                    soap_name = intf
                if soap_name is not None:
                    addr = '%ssoap-%s/' % (addr, soap_name)
                    self.soap_name = soap_name
            addr, location = addr + 'wsdl/', addr
        else:
            location = None

        def create_transport(auth):
            if auth is True:
                auth = ('admin', 'paris')
            if auth:
                tr = suds.transport.http.HttpAuthenticated()
                tr.options.username, tr.options.password = auth
            else:
                tr = suds.transport.http.HttpTransport()
            return tr

        tr = create_transport(auth)
        if location is not None:
            # it only handles case when we compute location
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            tr.urlopener = urllib2.build_opener(urllib2.HTTPSHandler(context=context), MyHttpRedirectHandler(), *tr.u2handlers())

        try:
            self.client = suds.client.Client(addr, location=location, cache=None, transport=tr)
        except ClientRedirectException as e:
            print(e)
            # we need to recreate transport since it has already been used
            tr = create_transport(auth)
            addr = e.newurl
            location = addr.rsplit('/', 2)[0] + '/'
            self.client = suds.client.Client(addr, location=location, cache=None, transport=tr)

        if not isinstance(intf, SoapGen.Interface):
            intf = parse_intf(self.client)
        self.intf = intf

        self.methods = dict((m.name, self._method_call_wrapper(m)) for m in intf.methods)

    def __getattr__(self, name):
        """Return callable objects for interface methods."""
        if name in self.methods:
            return self.methods[name]
        raise AttributeError("no attribute '%s'" % name)

    def _method_call_wrapper(self, m):
        return lambda *a: self.method_call(m, *a)

    def method_call(self, m, *args):
        """Handle method calls."""
        dargs = m.type_in.check_type(self.intf, args)
        args = [self._process_param(dargs[e.name], e) for e in m.type_in.elems]
        try:
            r = getattr(self.client.service, m.name)(*args)
        except suds.WebFault as e:
            fault = e.fault
            if hasattr(fault, 'faultcode'):
                code = fault.faultcode
                try:
                    code = int(code)
                except ValueError:
                    code = -1 # PHP fatal errors: value is not an int
                raise SoapStatusError(code, getattr(fault, 'faultstring', None))
            else:
                # not a SOAP API error (HTTP, ...)
                raise SoapError(str(e))
        if r['status_code'] != 0:
            raise SoapStatusError(r['status_code'], r['status_message'], self._process_return(r['return'], m.return_type()))
        return self._process_return(r['return'], m.return_type())

    @classmethod
    def _process_param(cls, val, t):
        """Transform method arguments for use with suds."""
        if t.etype == 'Map':
            if val is None:
                val = {}
            return {'item': [{'key': k, 'value': v} for k, v in val.items()]}
        else:
            return val

    def _process_return(self, val, t):
        """Transform method response from suds."""
        if isinstance(t, basestring) and t in self.intf.types:
            t = self.intf.types[t]
        if t in SoapGen.XMLSCHEMA_TYPES:
            if val is None or val == '':
                return None
            conv = SoapGen.XMLSCHEMA_TYPES[t]
            if not isinstance(conv, type):
                conv = conv[1]
            return conv(val)
        elif t == 'Map':
            if val is None or val == '':
                return {}
            return dict((str(x.key), None if x.value is None else str(x.value)) for x in val.item)
        elif isinstance(t, SoapGen.ComplexType):
            if t.name == 'Void':
                if val is None or val == '':  # should always be true
                    return None
            if t.name.endswith('List'):
                if val is None or val == '':
                    return []
                return [self._process_return(x, t.elems[0].etype) for x in val.item]
            if val is None or val == '':
                val = {}
            name2elem = dict((e.name, e) for e in t.elems)
            val2 = dict(val)
            val2.update((k, None) for k in name2elem if k not in val)
            ret = {}
            for k, v in val2.items():
                k = str(k)
                tt = name2elem[k]
                if v is None and tt.optional:
                    ret[k] = None
                elif tt.occurs is not None and tt.occurs != (0, 1):
                    ret[k] = [self._process_return(x, tt.etype) for x in v]
                else:
                    ret[k] = self._process_return(v, tt.etype)
            return ret

        # fallback, cannot use type (should not happen)
        return dict((x[0], self._process_return(x[1], None)) for x in val)

    def __dir__(self):
        return self.methods.keys()


def parse_intf(cl):
    """Create a SoapGen.Interface from a Suds client"""

    resolver = cl.factory.resolver
    tns = cl.wsdl.tns[1]
    m = re.match(r'http://soap\.anevia\.com/([^/]+)/', tns)
    if m is not None:
        intf_name = m.group(1)
        binding_name = 'Soap%sBinding' % intf_name.capitalize()
    else:
        # non-versionned WSDL
        m = re.match(r'http://([^.]+)\.soap\.anevia\.com', tns)
        if m is None:
            raise ValueError("not an Anevia SOAP interface")
        intf_name = m.group(1)
        binding_name = 'SoapInterfaceSOAP'

    # methods
    binding = None
    for k, v in cl.wsdl.bindings.items():
        if k[0] == binding_name:
            binding = v
            break
    if binding is None:
        raise KeyError("SOAP binding not found")

    methods = []
    for name in binding.operations:
        rettype = resolver.find('%sResponse' % name).children()[0][0].type[0]
        if rettype == 'Void':
            rettype = None
        m = SoapGen.Method(name, [parse_intf_element(el, SoapGen.Parameter) for el, _ in resolver.find(name).children()], rettype)
        methods.append(m)

    # types
    # skip types for method input/output parameters
    method_types = set(s for s in binding.operations)
    method_types |= set('%sResponse' % s for s in binding.operations)
    schema = None
    for el in cl.wsdl.types[0][0].children:
        if el['targetNamespace'] == tns:
            schema = el
            break
    if schema is None:
        raise KeyError("SOAP types not found")

    types = []
    for eltype in schema.children:
        if eltype.name != 'complexType':
            continue
        name = eltype['name']
        if name in method_types:
            continue
        t = SoapGen.ComplexType(name, [parse_intf_element(el, SoapGen.Element) for el, _ in resolver.find(name).children()])
        types.append(t)

    # finally, build the interface
    return SoapGen.Interface(intf_name, types=types, methods=methods)


def parse_intf_element(el, cls):
    if el.min is None and el.max is None:
        occurs = None
    else:
        if el.min is None:
            omin = 0
        else:
            omin = int(el.min)
        if el.max is None:
            omax = 1
        elif el.max == 'unbounded':
            omax = None
        else:
            omax = int(el.max)
        occurs = (omin, omax)
    return cls(el.name, el.type[0], optional=el.nillable, occurs=occurs)
