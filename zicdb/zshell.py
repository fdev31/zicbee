# vim: et ts=4 sw=4
import os
import sys
from zicdb.dbe import Database

DEFAULT_NAME='songs'

def init(args=None):
    clean_args = args or sys.argv[2:]
    globals().update(
            dict(songs=Database(os.environ.get('ZDB', DEFAULT_NAME)),
                args=clean_args)
            )
