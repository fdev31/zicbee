#!/usr/bin/env python
from setuptools import setup, find_packages
VERSION='0.2'

setup (
        name='zicdb',
        version=VERSION,
        author='Fabien Devaux',
        author_email='fdev31@gmail.com',
        long_description='A simple Music database engine',
        keywords='database music tags metadata management',
        packages = find_packages(),
        package_data = {
            'zicdb': ['web_templates/*.html', 'static/*'],
            'zplayer': ['*.glade'],
            },

        entry_points = {
            "console_scripts": [
                'zicdb = zicdb:startup',
                'zicgui = zplayer.pplayer:main'
                ],
            "setuptools.installation" : [
                'eggsecutable = zicdb:startup'
                ]
            },

        install_requires = [
            'buzhug>=0.9',
            'mutagen>=1.13',
            'web.py>=0.22',
            'python-cjson>=1.0.5',
#            'simplejson>=1.7.3',
#            'demjson>=1.1',
            ],

        dependency_links = [
            'eggs',
#            'http://box.gnux.info/fab/eggs'
            ],
        )

