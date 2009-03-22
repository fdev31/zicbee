# vim: et ts=4 sw=4
import os
import sys
from zicbee.db import Database

DEFAULT_NAME='songs'

def init(args=None, db_name=None):
    try:
        db
    except NameError:
        pass
    else:
        print "db cleanup"
        db.cleanup() # XXX: Ugly !
        db.close()

    db_name = db_name or os.environ.get('ZDB', DEFAULT_NAME)
    print "opening %s..."%db_name
    db = Database(db_name)
    globals().update( dict(songs=db, args=args) )
    db.cleanup() # XXX: Ugly !

