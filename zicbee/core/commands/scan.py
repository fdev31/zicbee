# vim: et ts=4 sw=4
import itertools
import os
import sys
from time import time
from zicbee.core.zshell import args, songs
from zicbee.core.zutils import duration_tidy, clean_path

def do_scan():
    """ Scan a directory for songs (fill Database)
    See "help" for a more complete documentation
    """
    if not args:
        sys.exit('At least one argument must be specified!')

    newline_iterator = itertools.cycle(x == 20 for x in xrange(21))
    orig_nb = len(songs)
    start_t = time()

    archives = []
    directories = []

    for path in args:
        path = clean_path(path)
        if os.path.isdir(path):
            directories.append(path)
        else:
            archives.append(path)

    def _scan(**kw):
        print ', '.join(':'.join((k,v)) for k,v in kw.iteritems())
        try:
            for status_char in songs.merge(**kw):
                print status_char,
                if newline_iterator.next():
                    print ''
                sys.stdout.flush()
        except Exception, e:
            print "ERROR!", str(e)
            import traceback
            traceback.print_exc()

    for path in archives:
        _scan(archive=path)

    for path in directories:
        _scan(directory=path)

    elapsed = time() - start_t
    delta = len(songs)-orig_nb
    print "\nProcessed %d (%s%d) songs in %s (%.2f/s.)"%(
            len(songs),
            '-' if delta < 0 else '+',
            delta,
            duration_tidy(elapsed),
            len(songs)/elapsed)


