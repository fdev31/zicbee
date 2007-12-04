def init():
    globals().update(
            dict(songs=Database('songs'), args=sys.argv[2:])
            )

def do_reset():
    songs.destroy()
    print "Database cleared!"

def do_help():
        print "Welcome to ZicDB!".center(80)
        print """
reset
    Erases the Database (every previous scan is lost!)

scan <directory> [directory...]
    Scan directories for files and add them to the database

search <match command>

  Match commands composition:
    VAL OPERATOR VAL
    VAL can be @<tag> or #string# or integer (ie. 13)
    OPERATOR can be 'in' '==' '<' and so on...

    @<tag>    Access a tag value
    #blah#    Declare the string "blah" (used for matching)
    @L        Suffix for tags value, convert tag to lowercase

  Possible tags:
\t- %s

  Exemple:
  %% %s search '#shak# in @filename@L and track == 2'

  Note:
    << ' >> symbol is used here to prevent the shell from interpreting
    special characters (@, ==, etc...)
    """%('\n\t- '.join(valid_tags), sys.argv[0])

def do_search():
    condition = ' '.join(args).replace('#', "'").replace('@L', '.lower()').replace('@', '') or 'True'
    duration = 0
    start_t = time()

    fields = list(valid_tags)
    fields.remove('filename')
    fields = tuple(fields)

    for res in songs.search([], condition):
        print '%s :\n '%res.filename,'| '.join('%s: %s'%(f, getattr(res, f)) for f in fields if f[0] != '_' and getattr(res, f))
        duration += res.length
    print "Found in %s for a total of %s!"%(
            duration_tidy(time()-start_t),
            duration_tidy(duration)
            )

def do_scan():
    import itertools

    newline_iterator = itertools.cycle(x == 10 for x in xrange(11))
    orig_nb = len(songs)
    start_t = time()

    for path in args:
        for status_char in songs.merge(path):
            print status_char,
            if newline_iterator.next():
                print ''
            sys.stdout.flush()

    elapsed = time() - start_t
    print "Processed %d (+ %d) songs in %s (%.2f/s.)"%(
            len(songs),
            len(songs)-orig_nb,
            duration_tidy(elapsed),
            len(songs)/elapsed)


### INTERNAL ###

import os, sys
from time import time
from zicdb.dbe import Database, valid_tags

def duration_tidy(orig):
    minutes, seconds = divmod(orig, 60)
    return '%d min %02ds.'%(minutes, seconds)
    if minutes > 60:
        hours = int(minutes/60)
        minutes -= hours*60
        if hours > 24:
            days = int(hours/24)
            hours -= days*24
            return '%d days, %d:%d.%ds.'%(days, hours, minutes, seconds)
        return '%d:%d.%ds.'%(hours, minutes, seconds)
    return '%d.%02ds.'%(minutes, seconds)

