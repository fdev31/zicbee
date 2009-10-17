#!/usr/bin/env python
import os
import sys
try:
	import setuptools
except ImportError:
	from ez_setup import use_setuptools
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

requirements = [ 'zicbee-lib>=0.5', 'buzhug>=1.5', 'mutagen>=1.14', 'web.py>=0.32' ]

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
        packages = find_packages(),
        zip_safe = False,
        package_data = {
            'zicbee': [
                'ui/web/templates/*.html',
                'ui/web/static/*.css',
                'ui/web/static/*.js',
                'ui/web/static/pics/*.*',
                'ui/web/static/pics/cmd/*.*',
                'ui/notify/*.png',
                ],
            },

        entry_points = {
            "console_scripts": [
                'zicdb = zicbee.core:startup',
                'zicserve = zicbee.core:serve',
                'wasp = zicbee.wasp:startup',
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
            'eggs',
            'http://zicbee.gnux.info/files/',
            'http://webpy.org/',
            'http://buzhug.sourceforge.net/',
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

if 'build' in sys.argv or 'install' in sys.argv or any(a for a in sys.argv if 'dist' in a):
    # test copied from zicbee/player/_mpgen.py [and mp.py]:
    exe_name = 'mplayer' if os.sep == '/' else 'mplayer.exe'
    import subprocess
    try:
        ret = subprocess.Popen([exe_name, '-really-quiet']).wait()
    except OSError:
        ret = 255
    if ret:
        dec = "*"*80
        print dec
        print dec
        print ''
        print "* WARNING !! mplayer seems not accessible, please install properly."
        print dec
        print "* YOU NEED MPLAYER IN YOUR PATH TO GET PLAYER FEATURES"
        print ''
        print dec
        print dec

