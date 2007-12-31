import itertools

DEFAULT_NAME='songs'

def init():
    globals().update(
            dict(songs=Database(os.environ.get('ZDB', DEFAULT_NAME)), args=sys.argv[2:])
            )

def do_list():
    for i in os.listdir(DB_DIR):
        if os.path.isfile(os.path.join(DB_DIR, i, '__info__')):
            txt = "%s # %d records"%(i, len(Database(i)))
            if i == DEFAULT_NAME:
                txt += ' [default]'
            print txt

def do_bundle():
    if len(args) != 1:
        sys.exit("Need filename name as agment !")
    songs.dump_archive(args[0])

def do_reset():
    songs.destroy()
    print "Database cleared!"

def do_help():
        print "Welcome to ZicDB!".center(80)
        print """

reset
    Erases the Database (every previous scan is lost!)

bundle <filename>
    Create a bundle (compressed archive) of the database

scan <directory|archive> [directory|archive...]
    Scan directories/archive for files and add them to the database

search[::out] <match command>

  out:
	specifies the output format (for now: m3u or null or default)

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

def do_search(out=None):
    condition = ' '.join(args).replace('#', "'").replace('@L', '.lower()').replace('@U', '.upper()').replace('@', '') or 'True'
    duration = 0
    start_t = time()

    fields = list(valid_tags)
    fields.remove('filename')
    fields = tuple(fields)

    if out == 'm3u':
        def song_output(song):
            print song.filename
    elif out == 'null':
        def song_output(song): pass
    else:
        def song_output(song):
            txt = '%s :\n%s '%(song.filename, '| '.join('%s: %s'%(f, getattr(song, f)) for f in fields if f[0] != '_' and getattr(song, f)))
            print txt.decode('utf8').encode('utf8')

    num = 0
    for num, res in enumerate(songs.search([], condition)):
        song_output(res)
        duration += res.length

    print "# %d results in %s for a total of %s!"%(
            num,
            duration_tidy(time()-start_t),
            duration_tidy(duration)
            )

def do_scan():
    if not args:
        sys.exit('At least one argument must be specified!')

    newline_iterator = itertools.cycle(x == 10 for x in xrange(11))
    orig_nb = len(songs)
    start_t = time()

    archives = []
    directories = []

    for path in args:
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


### INTERNAL ###

import os, sys
from time import time
from zicdb.dbe import Database, valid_tags, DB_DIR

_plur = lambda val: 's' if val > 1 else ''

def duration_tidy(orig):
    minutes, seconds = divmod(orig, 60)
    if minutes > 60:
        hours, minutes = divmod(minutes, 60)
        if hours > 24:
            days, hours = divmod(hours, 24)
            return '%d day%s, %d hour%s %d min %02.1fs.'%(days, _plur(days), hours, _plur(hours), minutes, seconds)
        else:
            return '%d hour%s %d min %02.1fs.'%(hours, 's' if hours>1 else '', minutes, seconds)
    else:
        return '%d min %02.1fs.'%(minutes, seconds)
    if minutes > 60:
        hours = int(minutes/60)
        minutes -= hours*60
        if hours > 24:
            days = int(hours/24)
            hours -= days*24
            return '%d days, %d:%d.%ds.'%(days, hours, minutes, seconds)
        return '%d:%d.%ds.'%(hours, minutes, seconds)
    return '%d.%02ds.'%(minutes, seconds)

