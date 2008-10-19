# vim: et ts=4 sw=4
import os
import sys
from zicbee.db import Database

DEFAULT_NAME='songs'

def init(args=None):
    clean_args = args or sys.argv[2:]
    db = Database(os.environ.get('ZDB', DEFAULT_NAME))
    globals().update( dict(songs=db, args=clean_args) )
    db.db.cleanup() # XXX: Ugly !
