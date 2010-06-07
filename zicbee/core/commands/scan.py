# vim: et ts=4 sw=4
import itertools
import os
import sys
from time import time
from zicbee.core import zshell
from zicbee_lib.debug import DEBUG
from zicbee_lib.formats import duration_tidy, clean_path
from os.path import dirname

def _scan(update=False, **kw):
    newline_iterator = itertools.cycle(x == 20 for x in xrange(21))
    print ', '.join(':'.join((k,v)) for k,v in kw.iteritems())
    try:
        newlined=True
        for status_char in zshell.songs.merge(update=update,**kw):
            newlined=False
            print status_char,
            if newline_iterator.next():
                newlined=True
                print ''
            sys.stdout.flush()
        if not newlined:
            print ''
    except Exception, e:
        DEBUG()

def do_scan(up=False):
    """ Scan a directory for songs (fill Database)
    See "help" for a more complete documentation
    paramter:
      up: if True, updates tags of already scanned songs
    """
    if not zshell.args:
        sys.exit('At least one argument must be specified!')

    orig_nb = len(zshell.songs)
    start_t = time()

    archives = []
    directories = []

    for path in zshell.args:
        path = clean_path(path)
        if os.path.isdir(path):
            directories.append(path)
        else:
            archives.append(path)

    for path in archives:
        _scan(archive=path, db_name=zshell.songs.db_name)

    for path in directories:
        _scan(directory=path, db_name=zshell.songs.db_name, update=up)

    elapsed = time() - start_t
    delta = len(zshell.songs)-orig_nb
    print "\nProcessed %d (%s%d) songs in %s (%.2f/s.)"%(
            len(zshell.songs),
            '-' if delta < 0 else '+',
            abs(delta),
            duration_tidy(elapsed),
            len(zshell.songs)/elapsed)


