## -*- encoding: utf-8 -*-
import os
import sys
from setuptools import setup
from codecs import open # To open the README file with proper encoding
from setuptools.command.test import test as TestCommand # for tests

# The name of the project
name = 'sage-explorer'

# Ensure python>=3.6
if sys.version_info.major < 3 or sys.version_info.minor < 6:
    raise ValueError("Python version '%s.%s' unsupported" % (
        sys.version_info.major, sys.version_info.minor)
    )

# Get information from separate files (README, VERSION)
def readfile(filename):
    with open(filename,  encoding='utf-8') as f:
        return f.read()

# For the tests
class SageTest(TestCommand):
    def run_tests(self):
        errno = os.system("sage -t --force-lib sage_explorer")
        if errno != 0:
            sys.exit(1)

setup(
    name = name,
    version = readfile("VERSION"),
    description='Jupyter explorer widget for SAGE objects',
    long_description = readfile("README.rst"),
    url='https://github.com/sagemath/sage-explorer',
    author='Odile Bénassy, Nicolas M. Thiéry',
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
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.6',
      'Programming Language :: Python :: 3.7',
      'Framework :: Jupyter',
    ], # classifiers list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    package_data = {'sage_explorer': ['*.yml']},
    keywords = "SageMath widget explorer jupyter notebook",
    packages = ['sage_explorer'],
    cmdclass = {'test': SageTest}, # adding a special setup command for tests
    install_requires = ['PyYAML', 'cysignals', 'ipywidgets >= 7.5.0', 'ipyevents', 'sage-combinat-widgets'],
    extra_require = ['sage-package', 'sphinx']
)
