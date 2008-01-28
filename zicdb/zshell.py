# vim: et ts=4 sw=4
import itertools
from zicdb.zutils import duration_tidy, parse_line, jdump

DEFAULT_NAME='songs'

def init(args=None):
    clean_args = args or sys.argv[2:]
    globals().update(
            dict(songs=Database(os.environ.get('ZDB', DEFAULT_NAME)),
                args=clean_args)
            )
    sys.argv = sys.argv[2:]

### INTERNAL ###

import os, sys
from time import time
from zicdb.dbe import Database, valid_tags, DB_DIR

