#!/usr/bin/env python
from setuptools import setup, find_packages
VERSION='0.1'

setup (
        name='zicdb',
        version=VERSION,
        author='Fabien Devaux',
        author_email='fdev31@gmail.com',
        long_description='A simple Music database engine',
        keywords='database music tags metadata management',
        packages = find_packages(),

        entry_points = {
            "console_scripts": [
                'zicdb = zicdb:startup'
                ],
            "setuptools.installation" : [
                'eggsecutable = zicdb:startup'
                ]
            },

        install_requires = [
#            'buzhug>=0.9',
#            'mutagen>=1.13',
            ],

        dependency_links = [
            'http://box.gnux.info/fab/eggs'
            ],
        )

