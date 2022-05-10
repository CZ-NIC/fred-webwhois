#!/usr/bin/python3
"""Setup script for webwhois."""
import os
from distutils.command.build import build

from setuptools import setup


def run_npm(build) -> bool:
    return not bool(os.environ.get('SKIP_NPM', False))


class custom_build(build):
    sub_commands = [
        ('compile_catalog', None),
        ('npm_install', run_npm),
        ('npm_run', run_npm),
    ] + build.sub_commands


setup(cmdclass={'build': custom_build})
