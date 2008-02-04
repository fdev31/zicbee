# vim: et ts=4 sw=4

import os
import sys
from zicdb.dbe import Database, DB_DIR
from zicdb.zshell import args, songs, DEFAULT_NAME

from .search import do_search
from .scan import do_scan
from .help import do_help
from .serve import do_serve

def do_list():
    for i in os.listdir(DB_DIR):
        if os.path.isfile(os.path.join(DB_DIR, i, '__info__')):
            txt = "%s # %d records"%(i, len(Database(i)))
            if i == DEFAULT_NAME:
                txt += ' [default]'
            print txt

def do_shell():
    import pdb; pdb.set_trace()

def do_bundle():
    if len(args) != 1:
        sys.exit("Need filename name as agment !")
    songs.dump_archive(args[0])

def do_reset():
    songs.destroy()
    print "Database cleared!"

def do_get(host='localhost', out='/tmp'):
    if ':' not in host:
        host += ':9090'

    def _p(*args):
        args = args[0]
        filename = os.path.join(out, ' - '.join(a for a in args[1:4] if a) + args[0].split('?', 1)[0][-4:])
        uri = 'http://%s%s'%(host, args[0])
        print "wget -O %s %s"%(repr(str(filename)), repr(uri))

    do_search(out=_p, host=host)

