#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

from freddist.core import setup
from freddist.util import find_packages, findall

PROJECT_NAME = 'fred-webwhois'


def main():
    srcdir = os.path.dirname(os.path.abspath(__file__))
    packages = find_packages(srcdir)

    templates = [os.path.join('templates', name) for name in findall(os.path.join(srcdir, 'webwhois/templates'))]
    static = [os.path.join('static', name) for name in findall(os.path.join(srcdir, 'webwhois/static'))]
    package_data = {
        'webwhois': templates + static,
        'webwhois.tests': ['templates/*'],
    }

    setup(name=PROJECT_NAME,
          description='NIC.CZ Fred Web Whois',
          author='Zdeněk Böhm, CZ.NIC',
          author_email='zdenek.bohm@nic.cz',
          url='http://fred.nic.cz/',
          license='GNU GPL',
          platforms=['posix'],
          long_description='CZ.NIC Fred Web Whois',
          packages=packages,
          package_data=package_data,
          i18n_files=['webwhois/locale/cs/LC_MESSAGES/django.po'])


if __name__ == '__main__':
    main()
