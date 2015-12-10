#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

from freddist.core import setup
from freddist.util import find_data_files, find_packages, findall

PROJECT_NAME = 'fred-webwhois-site'


def main():
    srcdir = os.path.dirname(os.path.abspath(__file__))
    packages = find_packages(srcdir)

    package_data = {
        'webwhois_standalone': [os.path.join('templates', name)
                                for name in findall(os.path.join(srcdir, 'webwhois_standalone/templates'))],
    }

    data_files = [(os.path.join('share/ginger/static', dest), files)
                  for dest, files in find_data_files(srcdir, 'webwhois_standalone/static')]

    setup(name=PROJECT_NAME,
          description='NIC.CZ Fred Web Whois Standalone site',
          author='Zdeněk Böhm, CZ.NIC',
          author_email='zdenek.bohm@nic.cz',
          url='http://fred.nic.cz/',
          license='GNU GPL',
          platforms=['posix'],
          long_description='CZ.NIC Fred Web Whois Standalone site',
          packages=packages,
          package_data=package_data,
          i18n_files=['webwhois_standalone/locale/cs/LC_MESSAGES/django.po'],
          data_files=data_files
    )


if __name__ == '__main__':
    main()
