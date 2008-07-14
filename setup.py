#!/usr/bin/env python
import os
import sys
try:
	import setuptools
except ImportError:
	from ez_setup import use_setuptools
	use_setuptools()
from setuptools import setup, find_packages

VERSION='0.6-alpha'

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



# also supported:
#            'simplejson>=1.7.3',

requirements = [ 'buzhug>=0.9', 'mutagen>=1.13' ]

if os.name in ('nt', 'ce'):
    requirements.append( 'demjson>=1.1' )
else:
    requirements.append( 'python-cjson>=1.0.5' )

setup (
        name='zicbee',
        version=VERSION,
        author='Fabien Devaux',
        author_email='fdev31@gmail.com',
        long_description='A simple Music database engine',
        keywords='database music tags metadata management',
        packages = find_packages(),
        package_data = {
            'zicbee': ['ui/web/web_templates/*.html', 'ui/web/static/*.css', 'ui/web/static/*.css', 'ui/web/static/MochoKit/*.js', 'ui/gtk/*.glade'],
            },

        entry_points = {
            "console_scripts": [
                'zicdb = zicbee.core:startup',
                'zicgui = zicbee.ui.gtk.player:main [player]'
                ],
            "setuptools.installation" : [
                'eggsecutable = zicbee.core:startup'
                ]
            },

        install_requires = requirements,

        extras_require = dict(
            player='pyglet>=1.1beta1',
            server='web.py>=0.22',
            ),

        dependency_links = [
            'eggs',
            'http://code.google.com/p/pyglet/downloads/list',
            ],
        )

