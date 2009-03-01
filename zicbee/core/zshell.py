# vim: et ts=4 sw=4
import os
import sys
from zicbee.db import Database

DEFAULT_NAME='songs'

def init(args=None, db_name=None):
    clean_args = args or sys.argv[2:]
    try:
        db
    except NameError:
        pass
    else:
        db.cleanup() # XXX: Ugly !
        db.close()

    db = Database(db_name or os.environ.get('ZDB', DEFAULT_NAME))
    globals().update( dict(songs=db, args=clean_args) )
    db.db.cleanup() # XXX: Ugly !

