# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from setuptools import setup, find_packages
import sys, os
import os.path as op

HERE = op.dirname(__file__)
README = open(op.join(HERE, 'README')).READ()

setup(name='drslib',
      version=version,
      description="A library for extracting analytics from the ESGF system",
      long_description=README,
,
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Stephen Pascoe',
      author_email='Stephen.Pascoe@stfc.ac.uk',
      #url='',
      #download_url='',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'test']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
      ],
      #tests_require=['NoseXUnit'],
      entry_points= {
        'console_scripts': [],
        },
      test_suite='nose.collector',
      )
