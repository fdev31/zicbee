# vim: et ts=4 sw=4

from zicdb.dbe import Database, DB_DIR
from zicdb.zshell import args, songs, DEFAULT_NAME

from .search import do_search
from .scan import do_scan
from .help import do_help
from .serve import do_serve
from .get import do_get

def do_list():
    from os import listdir
    from os.path import isfile, join

    for i in listdir(DB_DIR):
        if isfile(join(DB_DIR, i, '__info__')) and isfile(join(DB_DIR, i, 'album')):
            txt = "%s # %d records"%(i, len(Database(i)))
            if i == DEFAULT_NAME:
                txt += ' [default]'
            print txt

def do_shell():
    import pdb; pdb.set_trace()

def do_bundle():
    if len(args) != 1:
        raise SystemExit("Need filename name as agment !")
    songs.dump_archive(args[0])

def do_reset():
    songs.destroy()
    print "Database cleared!"


def do_hash():
    for i in songs.get_hash_iterator():
        print "%8d / %s"%i

def do_find_dups(wpt=None):
    """
    wpt == wrong positive threshold (ceil to not reach)
    """

    import itertools
    hash_dict = dict()

    cnt = itertools.count()

    if wpt is None:
        wpt = min(1000, len(songs)/60) # take untaged/corrupted data into account

    for num, footprint in songs.get_hash_iterator():
        if footprint not in hash_dict:
            hash_dict[footprint] = [num]
        else:
            hash_dict[footprint].append(num)

    for m in (matches for num, matches in hash_dict.iteritems() if 1 < len(matches) < wpt):
        print "#", cnt.next()
        for num in m:
            print "%d: %s"%(num, songs[num].filename)

