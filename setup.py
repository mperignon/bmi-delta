#! /usr/bin/env python
from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages


setup(name='bmi-deltaRCM',
      version='0.1.0',
      author='Mariela Perignon',
      author_email='perignon@colorado.edu',
      description='BMI Delta RCM',
      long_description=open('README.md').read(),
      packages=find_packages(),
)
