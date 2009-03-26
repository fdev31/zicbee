# vim: et ts=4 sw=4
import itertools
import os
import sys
from time import time
from zicbee.core import zshell
from zicbee.core.debug import DEBUG
from zicbee.core.zutils import duration_tidy, clean_path

def do_scan():
    """ Scan a directory for songs (fill Database)
    See "help" for a more complete documentation
    """
    if not zshell.args:
        sys.exit('At least one argument must be specified!')

    newline_iterator = itertools.cycle(x == 20 for x in xrange(21))
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

    def _scan(**kw):
        print ', '.join(':'.join((k,v)) for k,v in kw.iteritems())
        try:
            for status_char in zshell.songs.merge(**kw):
                print status_char,
                if newline_iterator.next():
                    print ''
                sys.stdout.flush()
        except Exception, e:
            DEBUG()

    for path in archives:
        _scan(archive=path, db_name=zshell.DEFAULT_NAME)

    for path in directories:
        _scan(directory=path, db_name=zshell.DEFAULT_NAME)

    elapsed = time() - start_t
    delta = len(zshell.songs)-orig_nb
    print "\nProcessed %d (%s%d) songs in %s (%.2f/s.)"%(
            len(zshell.songs),
            '-' if delta < 0 else '+',
            delta,
            duration_tidy(elapsed),
            len(zshell.songs)/elapsed)


