#!/usr/bin/env python

import os
from distutils.core import setup

here = os.path.split(__file__)[0]
if not here: here = '.'

setup(name='Bincodes',
      version='1.0',
      packages=['bincodes'],
      package_dir={'bincodes':here},
      package_data={'bincodes':['bincodes.db']},
     )
