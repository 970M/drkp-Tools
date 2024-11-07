import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
import os
import glob
import base64

"""

Generate WSDL and other files from Python descriptions.

Example:

    #!/usr/bin/env python3
    from SoapGen import *

    intf = Interface('sample-intf',
        types = (
            ComplexType('SomeObject', (
                Element('field', 'string'),
                Element('value', 'string', optional=True),
            )),
            ComplexType('StringList', (
                Element('item', 'string', occurs=(0,None)),
            )),
        ),
        methods = (
            Method('List_objects', (), 'StringList'),
            Method('Create_object', (
                Parameter('name', 'string'),
                Parameter('stuff', 'string'),
                Parameter('options', 'Map', True),
            ), 'string'),
            Method('Do_something', (
                Parameter('id', 'string'),
            ), 'int', False),
            Method('Return_nothing', (), None),
        ),
    )

    generate_api_files(intf)

"""

# python3 compatibility
import sys
if sys.version_info > (3, 0):
    long = int
    basestring = str


# Retrieve debian version from changelog, if available
# If debian module is not available (e.g. on lenny), provide a rough
# alternative.
try:
    from debian.changelog import Changelog

    def _get_changelog_version(f):
        return str(Changelog(open(f), 1).version)
except ImportError:
    import subprocess

    def _get_changelog_version(f):
        changes = subprocess.check_output(['dpkg-parsechangelog', '--file', f]).decode('utf-8')
        return re.search('^Version: *(.*)$', changes, re.M).group(1)

def get_changelog_version(f):
    if os.path.isfile(f):
        return _get_changelog_version(f)
    else:
        return None


class Element:
    """
    Basic type element (XMLSchema:element)

    Attributes:
      name -- element name
      etype -- element type name or ComplexType
      optional -- nillable
      occurs -- (min,max) pair or None, max is None if unbounded

    """

    def __init__(self, name, etype, **kw):
        self.name = name
        self.etype = etype
        self.optional = kw.get('optional', False)
        self.occurs = kw.get('occurs', None)
        # check occurs range
        if self.occurs is not None:
            if self.occurs == '*':
                self.occurs = (0, None)
            elif self.occurs == '+':
                self.occurs = (1, None)
            assert len(self.occurs) == 2, "occurs parameter must be a pair, '*' or '+'"
            assert self.occurs[1] is None or self.occurs[1] > self.occurs[0], "invalid occurs range"
            if self.occurs[0] == 0:
                self.optional = True

    def to_xml(self):
        e = ET.Element('xsd:element')
        e.attrib['name'] = self.name
        if isinstance(self.etype, basestring):
            e.attrib['type'] = type_with_ns(self.etype)
        else:
            assert isinstance(self.etype, ComplexType), "invalid element type"
            e.append(self.etype.to_xml())

        if self.optional:
            e.attrib['nillable'] = 'true'
        if self.occurs is not None:
            e.attrib['minOccurs'] = str(self.occurs[0])
            e.attrib['maxOccurs'] = str(self.occurs[1]) if self.occurs[1] is not None else 'unbounded'
        return e

    def check_type(self, intf, v, single=False):
        """Check python's value type against the element's type.
        Return a reformatted value.
        """
        if v is None:
            assert self.optional, "None value for non optional element '%s'" % self.name
            return None

        elif self.etype == 'Map':
            assert isinstance(v, dict), "invalid value for '%s'" % self.name
            return v

        elif not single and self.occurs is not None:
            if self.occurs == (0, 1) and type(v) not in (tuple, list):
                v = [v]
            assert type(v) in (tuple, list), "invalid value for '%s'" % self.name
            return tuple(self.check_type(intf, x, True) for x in v)

        elif self.etype in XMLSCHEMA_TYPES:
            t = XMLSCHEMA_TYPES[self.etype]
            if isinstance(t, type):
                assert isinstance(v, t), "invalid type for element '%s'" % self.name
            else:
                v = t[0](v)
            return v

        # fallback
        if self.etype in intf.types:
            return intf.types[self.etype].check_type(intf, v)

        raise ValueError("unknown type: '%s'" % self.etype)


class ComplexType:
    """
    SOAP complex type (XMLSchema:complexType)

    Attributes:
      name -- type name (may be None)
      elems -- tuple of Element objects

    """

    def __init__(self, name, elems):
        self.name = name
        assert all(isinstance(x, Element) for x in elems), "invalid elements"
        self.elems = elems

    def to_xml(self):
        eret = ET.Element('xsd:complexType')
        if self.name is not None:
            eret.attrib['name'] = self.name
        if len(self.elems):
            e = ET.SubElement(eret, 'xsd:sequence')
            for x in self.elems:
                e.append(x.to_xml())
        return eret

    def check_type(self, intf, v):
        """Check python's value type against the element's type.
        v can be a list/tuple or a dict.
        Return a dict.
        """
        if isinstance(v, dict):
            vv = tuple(v.get(e.name) for e in self.elems)
        else:
            assert len(v) <= len(self.elems), "too much arguments for  type '%s'" % self.name
            vv = tuple(v) + (None,) * (len(self.elems) - len(v))
        return dict((e.name, e.check_type(intf, x)) for e, x in zip(self.elems, vv))


# Namespace alias for the local namespace.
NS_ALIAS = 'tns'

# Standard types, defined in XMLSchema.
# Value is a type or a (encode method, decode method) pair
XMLSCHEMA_TYPES = {
  'string': (''.join, ''.join),  # deal with bot str and unicode
  'int': int,
  'long': long,
  'float': float,
  'boolean': bool,
  'base64Binary': (lambda v: base64.b64encode(v).decode(), base64.b64decode),
  'dateTime': ''.join,
}

APACHE_NS_URI = 'http://xml.apache.org/xml-soap'
APACHE_NS_ALIAS = 'aps'

# Types declared in the Apache namespace.
APACHE_TYPES = (
ComplexType('MapItem', (
    Element('key', 'string'),
    Element('value', 'string', optional=True),
)),
ComplexType('Map', (
    Element('item', 'MapItem', occurs=(0, None)),
)),
)
APACHE_TYPES = dict((t.name, t) for t in APACHE_TYPES)


def type_with_ns(t):
    """Return an XML type attribute (with namespace) from a type name."""
    if t in XMLSCHEMA_TYPES:
        ns = 'xsd'
    elif t in APACHE_TYPES:
        ns = APACHE_NS_ALIAS
    elif ':' not in t:
        ns = NS_ALIAS
    else:
        return t
    return "%s:%s" % (ns, t)


class Interface:
    """
    Gather declarations of a WSDL file.

    Attributes:
      namespace
      types -- custom (complex) types, as a dict
      methods

    """

    def __init__(self, ns, types=[], methods=[]):
        """Build a Interface."""

        self.namespace = ns
        assert all(isinstance(x, ComplexType) for x in types), "invalid types"
        self.types = dict((t.name, t) for t in types)
        if 'Void' not in self.types:
            self.types['Void'] = ComplexType('Void', ())
        assert all(isinstance(x, Method) for x in methods), "invalid methods"
        self.methods = list(methods)
        self.check_element_types()

    def check_element_types(self):
        """Check that element types exist"""

        all_elems = []
        for t in self.types.values():
            all_elems.extend(t.elems)
        for m in self.methods:
            all_elems.extend(m.type_in.elems)
            all_elems.extend(m.type_out.elems)
        all_elems = set(all_elems)

        defined_types = set(XMLSCHEMA_TYPES) | set(APACHE_TYPES) | set(self.types)

        for e in all_elems:
            if isinstance(e.etype, basestring) and ':' not in e.etype and e.etype not in defined_types:
                raise ValueError("undefined type: %s" % e.etype)

    def to_wsdl(self, version=None):
        """Return an WSDL tree."""

        assert self.namespace is not None, "namespace not defined"
        if version is None:
            intf_name = "SoapInterface"
            ns_uri = "http://%s.soap.anevia.com" % self.namespace
            location = ''
            binding = service = intf_name + 'SOAP'
            porttype = intf_name
        else:
            # versionned manifests use a different namings
            intf_name = "Soap%s" % self.namespace.capitalize()
            ns_uri = "http://soap.anevia.com/%s/%s/" % (self.namespace, version)
            location = "/soap-%s/%s/" % (self.namespace, version)
            binding = intf_name + 'Binding'
            service = intf_name + 'Service'
            porttype = intf_name + 'PortType'

        root = ET.Element('wsdl:definitions', {
          'xmlns:soap': 'http://schemas.xmlsoap.org/wsdl/soap/',
          'xmlns:%s' % APACHE_NS_ALIAS : APACHE_NS_URI,
          'xmlns:%s' % NS_ALIAS : ns_uri,
          'xmlns:wsdl': 'http://schemas.xmlsoap.org/wsdl/',
          'xmlns:xsd': 'http://www.w3.org/2001/XMLSchema',
          'name': intf_name,
          'targetNamespace': ns_uri,
        })

        # type declarations
        etypes = ET.SubElement(root, 'wsdl:types')

        # apache types
        eschema = ET.SubElement(etypes, 'xsd:schema', {'targetNamespace': APACHE_NS_URI})
        for t in APACHE_TYPES.values():
            eschema.append(t.to_xml())

        # custom types
        eschema = ET.SubElement(etypes, 'xsd:schema', {'targetNamespace': ns_uri})
        ET.SubElement(eschema, 'xsd:import', {'namespace': APACHE_NS_URI})
        for t in self.types.values():
            eschema.append(t.to_xml())
        # method types
        for m in self.methods:
            e = ET.SubElement(eschema, 'xsd:element', {'name': m.name})
            e.append(m.type_in.to_xml())
            e = ET.SubElement(eschema, 'xsd:element', {'name': '%sResponse' % m.name})
            e.append(m.type_out.to_xml())

        # messages (method Input/Output)
        for m in self.methods:
            e = ET.SubElement(root, 'wsdl:message', {'name': '%sInput' % m.name})
            ET.SubElement(e, 'wsdl:part', {
              'element': '%s:%s' % (NS_ALIAS, m.name),
              'name': 'parameters',
            })
            e = ET.SubElement(root, 'wsdl:message', {'name': '%sOutput' % m.name})
            ET.SubElement(e, 'wsdl:part', {
              'element': '%s:%sResponse' % (NS_ALIAS, m.name),
              'name': 'parameters',
            })

        # port types
        eports = ET.SubElement(root, 'wsdl:portType', {'name': porttype})
        e = ET.SubElement(eports, 'jaxws:bindings', {'xmlns:jaxws': 'http://java.sun.com/xml/ns/jaxws'})
        ET.SubElement(e, 'jaxws:enableWrapperStyle').text = 'false'
        for m in self.methods:
            e = ET.SubElement(eports, 'wsdl:operation', {'name': m.name})
            ET.SubElement(e, 'wsdl:input', {
              'message': '%s:%sInput' % (NS_ALIAS, m.name)
            })
            ET.SubElement(e, 'wsdl:output', {
              'message': '%s:%sOutput' % (NS_ALIAS, m.name)
            })

        # binding
        ebinding = ET.SubElement(root, 'wsdl:binding', {
          'name': binding,
          'type': '%s:%s' % (NS_ALIAS, porttype),
        })
        ET.SubElement(ebinding, 'soap:binding', {
          'style': 'document',
          'transport': 'http://schemas.xmlsoap.org/soap/http',
        })
        for m in self.methods:
            eop = ET.SubElement(ebinding, 'wsdl:operation', {'name': m.name})
            ET.SubElement(eop, 'soap:operation', {
              'soapAction': '%s/%s' % (intf_name, m.name),
            })
            e = ET.SubElement(eop, 'wsdl:input')
            ET.SubElement(e, 'soap:body', {'use': 'literal'})
            e = ET.SubElement(eop, 'wsdl:output')
            ET.SubElement(e, 'soap:body', {'use': 'literal'})

        # service
        eservice = ET.SubElement(root, 'wsdl:service', {'name': service})
        e = ET.SubElement(eservice, 'wsdl:port', {
          'binding': '%s:%s' % (NS_ALIAS, binding),
          'name': service,
        })
        ET.SubElement(e, 'soap:address', {
          'location': location,
        })

        return root

    def write_file(self, f=None, pretty=True, version=None):
        """Generate a WSDL, apply PHP replacements and write it to a file."""
        root = self.to_wsdl(version)
        s = ET.tostring(root)
        if pretty:
            s = minidom.parseString(s).toprettyxml(indent='  ', encoding='UTF-8')

        if f is None:
            f = 'soap.wsdl' # default filename
        if isinstance(f, basestring):
            d = os.path.normpath(os.path.dirname(f))
            if not os.path.isdir(d):
                os.makedirs(d)
            f = open(f, 'wb')
        f.write(s)


class Parameter(Element):
    """
    Method input parameter.
    """
    def __init__(self, name, stype, optional=False, **kw):
        Element.__init__(self, name, stype, optional=optional, **kw)

class Response(Element):
    """
    Method returned parameter.
    """
    def __init__(self, stype, optional=True):
        Element.__init__(self, 'return', stype, optional=optional)


class Method:
    """
    SOAP interface method.

    Attributes:
      name -- method name
      type_in -- input (complex) type
      type_out -- output (complex) type

    """

    def __init__(self, name, args, tret, optret=True):
        self.name = name
        assert all(isinstance(x, Parameter) for x in args), "invalid arguments"
        if tret is None:
            tret = 'Void'
            optret = True
        self.type_in = ComplexType(None, tuple(args))
        self.type_out = ComplexType(None, (
          Response(tret, optret),
          Element('status_code', 'int', optional=False),
          Element('status_message', 'string', optional=False),
        ))

    def return_type(self):
        return self.type_out.elems[0].etype


# Generated file templates, indexed by filename
templates = {}

templates['build-server.sh'] = """\
#!/bin/bash
soap_name="%(ns)s"
exec "`dirname $0`/common/build.sh" -n $soap_name "$@"
"""

templates['src/index.php'] = """\
<?php

$path = @trim($_SERVER['PATH_INFO'], '/');
$wsdl = './wsdl/soap' . ($path ? ".$path" : '') . '.wsdl';
if(strpos($path, '/') !== false || !file_exists($wsdl)) {
  http_response_code(404);
  header('Content-Type: text/plain');
  exit();
}

set_include_path(get_include_path().PATH_SEPARATOR.'common');
ini_set('soap.wsdl_cache_limit',   1);
ini_set('soap.wsdl_cache_enabled', 0);

require_once('Soap%(Ns)s.inc.php');

$server = new SoapServer($wsdl, array('send_errors' => AnvSoapInterface::$debug));
$server->setClass('Soap%(Ns)s');
$server->handle();

?>
"""

templates['src/version.txt'] = "%(ns)s %(v)s"


# Symlinks to common files
common_symlinks = [
    ('../common/doc', 'doc/common'),
    ('../common/src', 'src/common'),
    ('../common/wsdl/index.php', 'src/wsdl/index.php'),
]


def generate_api_files(intf, outdir='.'):
    """Generate all files for an API project."""
    if not outdir:
        outdir = '.'
    if not os.path.isdir(outdir):
        raise ValueError("invalid output directory: %s" % outdir)

    intf.write_file(os.path.join(outdir, 'src/wsdl/soap.wsdl'))

    # get debian version from changelog, if available
    # use changelog from out directory
    version = get_changelog_version(os.path.join(outdir, 'debian/changelog'))
    # remove existing versionned WSDL files
    for f in glob.glob(os.path.join(outdir, 'src/wsdl/soap.*.wsdl')):
        os.unlink(f)

    if version is not None:
        # generate the "branch" WSDL
        branch = re.match(r'^\d+\.\d+', version).group(0)
        intf.write_file(os.path.join(outdir, 'src/wsdl/soap.%s.wsdl' % branch), version=branch)
        # generate symlinks
        for v in ('latest', version):
            os.symlink('soap.%s.wsdl' % branch, os.path.join(outdir, 'src/wsdl/soap.%s.wsdl' % v))

    fmtd = {
        'ns': intf.namespace,
        'Ns': intf.namespace.capitalize(),
        'v': 'unknown' if version is None else version,
    }

    for name, tpl in templates.items():
        name = os.path.join(outdir, name)
        d = os.path.normpath(os.path.dirname(name))
        if not os.path.isdir(d):
            os.makedirs(d)
        open(name, 'wb').write((tpl % fmtd).encode('utf8'))
        if name.endswith('.sh'):
            os.chmod(name, 0o755)

    for sl in common_symlinks:
        if isinstance(sl, basestring):
            source, linkname = sl, sl
        else:
            source, linkname = sl
        linkname = os.path.join(outdir, linkname)
        if not os.path.lexists(linkname):
            os.symlink(source, linkname)
