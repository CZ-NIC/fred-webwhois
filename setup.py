#!/usr/bin/python
# -*- coding: utf-8 -*-
from distutils.command.build import build

from setuptools import find_packages, setup
from setuptools.command.sdist import sdist


class custom_build(build):

    sub_commands = [('compile_catalog', lambda x: True)] + build.sub_commands


class custom_sdist(sdist):

    def run(self):
        self.run_command('compile_catalog')
        # sdist is an old style class so super cannot be used.
        sdist.run(self)


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
      setup_requires=['Babel >=2.3'],
      install_requires=['django', 'idna', 'fred-pylogger', 'fred-pyfco', 'django-app-settings>=0.3'],
      cmdclass={'build': custom_build, 'sdist': custom_sdist})
