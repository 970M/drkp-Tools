#!/usr/bin/env python3

import os
import subprocess
from distutils.core import setup
from datetime import date

def get_debian_version():
    debian_dir = os.path.join(os.path.dirname(__file__), 'debian')
    if not os.path.isdir(debian_dir):
        return
    try:
        version = subprocess.check_output(['dpkg-parsechangelog', '-SVersion']).decode('utf-8').strip()
        if "~" in version:
            str_date_time = date.today().strftime("%Y%m%d.%H%M%S")
            version = version.replace("~", ".") + str_date_time
            return version
    except FileNotFoundError:
        # no dpkg-parsechangelog: assume CI build
        return os.environ.get('CI_COMMIT_TAG') or None
    except subprocess.CalledProcessError:
        return

setup(
    name='soap-common',
    version=get_debian_version() or 'unknown',
    description='Common tools for SOAP modules',
    url='https://gitlab.anevia.com/common/soap-common/',
    py_modules=['SoapClient', 'SoapGen'],
    scripts=['soapsh'],
    extras_require={
        ":python_version>='3'": ["suds-community"],
    },
)
