#!/usr/bin/env python
import os
import sys
try:
	import setuptools
except ImportError:
	from distribute_setup import use_setuptools
	use_setuptools()
from setuptools import setup, find_packages

sys.path.insert(0, '.')
import zicbee
VERSION=zicbee.__version__

if 'install' in sys.argv:
    print """Warning:
You will need to install some parts manually:

If it can't build, try to comment the line:
            'python-cjson>=1.0.5',

and uncomment one of those (recommended alternative: simplejson):
#            'simplejson>=1.7.3',
#            'demjson>=1.1',

Good luck !"""



# also supported:
#            'simplejson>=1.7.3',

requirements = [ 'zicbee-lib>=0.7.1', 'buzhug>=1.8', 'mutagen>=1.20', 'web.py>=0.34' ]

if sys.version_info[:2] < (2, 6):
    # add cjson dependency
    if os.name in ('nt', 'ce'):
        requirements.append( 'demjson>=1.1' )
    else:
        requirements.append( 'python-cjson>=1.0.5' )

DESCRIPTION=open('zicbee.rst').read()

setup (
        name='zicbee',
        version=VERSION,
        author='Fabien Devaux',
        author_email='fdev31@gmail.com',
        url = 'http://zicbee.gnux.info/',
        download_url='http://zicbee.gnux.info/hg/index.cgi/zicbee/archive/%s.tar.bz2'%VERSION,
        license='BSD',
        platform='all',
        description='A simple & powerful distributed Music database engine',
        long_description=DESCRIPTION,
        keywords = 'database music tags metadata management',
        include_package_data = True,
        packages = find_packages(),
        zip_safe = False,

        entry_points = {
            "console_scripts": [
                'zicdb = zicbee.core:startup',
                'zicserve = zicbee.core:serve',
                ],
            "setuptools.installation" : [
                'eggsecutable = zicbee.core:startup'
                ]
            },

        install_requires = requirements,

        extras_require = dict(
            player='zicbee-mplayer>=0.9',
            ),

        dependency_links = [
            'http://webpy.org/',
            'http://buzhug.sourceforge.net/',
            'http://webpy.org/static/',
            'http://code.google.com/p/quodlibet/downloads/list',
            ],
        classifiers = [
                'Development Status :: 4 - Beta',
                'Intended Audience :: Developers',
#                'Intended Audience :: End Users/Desktop',
                'Operating System :: OS Independent',
                'Operating System :: Microsoft :: Windows',
                'Operating System :: POSIX',
                'Programming Language :: Python',
                'Environment :: Console',
                'Environment :: No Input/Output (Daemon)',
                'Environment :: X11 Applications',
                'Natural Language :: English',
                'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
                'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
                'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
                'Topic :: Software Development',
                'Topic :: Software Development :: Libraries :: Python Modules',
                'Topic :: Multimedia :: Sound/Audio :: Players',
                'Topic :: Multimedia :: Sound/Audio :: Players :: MP3',
                'Topic :: Text Processing :: Markup',
                'Topic :: Utilities',
                ],

        )

