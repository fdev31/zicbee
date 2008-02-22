#!/usr/bin/env python
import os
import sys
try:
	import setuptools
except ImportError:
	from ez_setup import use_setuptools
	use_setuptools()
from setuptools import setup, find_packages

VERSION='0.4'

if 'install' in sys.argv:
    print """Warning:
You will need to install some parts manually:

pyglet      http://pyglet.org/
            (with avbin support: http://code.google.com/p/avbin/)

If it can't build, try to comment the line:
            'python-cjson>=1.0.5',

and uncomment one of those (recommended alternative: simplejson):
#            'simplejson>=1.7.3',
#            'demjson>=1.1',

Good luck !"""

requirements = [ 'buzhug>=0.9', 'mutagen>=1.13' ]

if os.name == 'posix':
    requirements.append('python-cjson>=1.0.5')
else:
    requirements.append('demjson>=1.1')

# if it fails, try:
#requirements[-1] = 'simplejson>=1.7.3'


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
                'zicgui = zplayer.pplayer:main [player]'
                ],
            "setuptools.installation" : [
                'eggsecutable = zicdb:startup'
                ]
            },

        install_requires = [
            'buzhug>=0.9',
            'mutagen>=1.13',
            ],

        extras_require = dict(
            player='pyglet>=1.0',
            server='web.py>=0.22',
            ),

        dependency_links = [
            'eggs',
            'http://code.google.com/p/pyglet/downloads/list',
            ],
        )

