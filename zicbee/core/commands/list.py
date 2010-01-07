# vim: et ts=4 sw=4
from zicbee_lib.config import DB_DIR
from zicbee.core.zshell import DEFAULT_NAME
from zicbee.db import Database, DB_DIR

def do_list():
    """ List available databases (some can be specified with "use" argument) """
    from os import listdir
    from os.path import isfile, join

    for i in listdir(DB_DIR):
        if isfile(join(DB_DIR, i, '__info__')) and isfile(join(DB_DIR, i, 'album')):
            txt = "%s # %d records"%(i, len(Database(i)))
            if i == DEFAULT_NAME:
                txt += ' [default]'
            print txt

