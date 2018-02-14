#!/usr/bin/python
# -*- coding: utf-8 -*-
from distutils.command.build import build
from setuptools import find_packages, setup


class custom_build(build):

    def has_i18n_files(self):
        return bool(self.distribution.i18n_files)

    sub_commands = [('build_i18n', has_i18n_files)] + build.sub_commands


setup(name='fred-webwhois',
      version='1.11.0',
      description='NIC.CZ Fred Web Whois',
      author='Zdeněk Böhm, CZ.NIC',
      author_email='zdenek.bohm@nic.cz',
      url='http://fred.nic.cz/',
      license='GNU GPL',
      platforms=['posix'],
      long_description='CZ.NIC Fred Web Whois',
      packages=find_packages(),
      include_package_data=True,
      setup_requires='setuptools_i18n',
      install_requires=['django', 'idna', 'fred-pylogger', 'fred-pyfco', 'django-app-settings>=0.3'],
      i18n_files=['webwhois/locale/cs/LC_MESSAGES/django.po'],
      cmdclass={'build': custom_build})
