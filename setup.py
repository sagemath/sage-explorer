#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import os, sys, platform
from glob import glob
from os.path import join as pjoin
from setuptools.command.test import test as TestCommand # for tests
from setuptools.command.sdist import sdist
from setuptools.command.build_py import build_py
from setuptools.command.egg_info import egg_info
#from subprocess import check_call

here = os.path.dirname(os.path.abspath(__file__))
node_root = os.path.join(here, 'js')
is_repo = os.path.exists(os.path.join(here, '.git'))

npm_path = os.pathsep.join([
    os.path.join(node_root, 'node_modules', '.bin'),
                os.environ.get('PATH', os.defpath),
])
from setupbase import (
    create_cmdclass, install_npm, ensure_targets,
    find_packages, combine_commands, ensure_python,
    get_version, HERE
)

from setuptools import setup


# The name of the project
name = 'new_sage_explorer'

# Ensure a valid python version
ensure_python('>=3.4')

# Get our version
version = get_version(pjoin(name, '_version.py'))

nb_path = pjoin(node_root, name, 'nbextension', 'static')
lab_path = pjoin(node_root, name, 'labextension')

# Get information from separate files (README, VERSION)
def readfile(filename):
    with open(filename,  encoding='utf-8') as f:
        return f.read()

# For the tests
class SageTest(TestCommand):
    def run_tests(self):
        errno = os.system("sage -t --force-lib sage_widget_adapters")
        if errno != 0:
            sys.exit(1)
        errno = os.system("sage -t --force-lib sage_combinat_widgets")
        if errno != 0:
            sys.exit(1)

def js_prerelease(command, strict=False):
    """decorator for building minified js/css prior to another command"""
    class DecoratedCommand(command):
        def run(self):
            jsdeps = self.distribution.get_command_obj('jsdeps')
            if not is_repo and all(os.path.exists(t) for t in jsdeps.targets):
                # sdist, nothing to do
                command.run(self)
                return

            try:
                self.distribution.run_command('jsdeps')
            except Exception as e:
                missing = [t for t in jsdeps.targets if not os.path.exists(t)]
                if strict or missing:
                    log.warn('rebuilding js and css failed')
                    if missing:
                        log.error('missing files: %s' % missing)
                    raise e
                else:
                    log.warn('rebuilding js and css failed (not a problem)')
                    log.warn(str(e))
            command.run(self)
            update_package_data(self.distribution)
    return DecoratedCommand

# Representative files that should exist after a successful build
jstargets = [
    pjoin(nb_path, 'index.js'),
    pjoin(node_root, 'lib', 'plugin.js'),
]

package_data_spec = {
    name: [
        'nbextension/static/*.*js*',
        'labextension/*.tgz'
    ]
}

data_files_spec = [
    ('share/jupyter/nbextensions/new_sage_explorer',
        nb_path, '*.js*'),
    ('share/jupyter/lab/extensions', lab_path, '*.tgz'),
    ('etc/jupyter/nbconfig/notebook.d' , HERE, 'new_sage_explorer.json')
]


cmdclass = create_cmdclass('jsdeps', package_data_spec=package_data_spec,
    data_files_spec=data_files_spec)
cmdclass['jsdeps'] = combine_commands(
    install_npm(node_root, build_cmd='build:all'),
    ensure_targets(jstargets),
)
cmdclass['test'] = SageTest


setup(
    name = name,
    version = version,
    description = 'Jupyter (new) explorer widget for SAGE objects',
    long_description = readfile("README.rst"),
    url='https://github.com/zerline/new-sage-explorer',
    author='Odile Bénassy, Nathan Carter, Nicolas M. Thiéry',
    author_email='odile.benassy@u-psud.fr',
    license='GPLv2+',
    classifiers=[
      # How mature is this project? Common values are
      #   3 - Alpha
      #   4 - Beta
      #   5 - Production/Stable
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Science/Research',
      'Topic :: Scientific/Engineering :: Mathematics',
      'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
      'Programming Language :: Python :: 2.7',
    ], # classifiers list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    package_data = {'new_sage_explorer': ['*.yml']},
    keywords = "SageMath widget explorer jupyter notebook",
    packages = ['new_sage_explorer'],
    cmdclass = cmdclass,
    install_requires = ['PyYAML', 'sage-combinat-widgets', 'sage-package', 'sphinx']
)
