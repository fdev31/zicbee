# vim: et ts=4 sw=4

from zicbee.db import Database, DB_DIR
from zicbee.core.zshell import args, songs, DEFAULT_NAME

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

do_shell.__doc__ = 'Spawns a shell'

def do_bundle():
    if len(args) != 1:
        raise SystemExit("Need filename name as agment !")
    songs.dump_archive(args[0])

do_bundle.__doc__ = 'Dump an archive (at given filename)'

def do_reset():
    songs.destroy()
    print "Database cleared!"

do_reset.__doc__ = 'Destroys the database'


def do_hash():
    for i in songs.get_hash_iterator():
        print "%8d / %s"%i

do_hash.__doc__ = """ Returns a list of id / hash lines """

def do_find_dups(wpt=None, ar=None):

    import itertools
    import heapq
    from os.path import dirname

    hash_dict = dict()

    cnt = itertools.count()
    total_cnt = itertools.count()

    if wpt is None:
        wpt = min(1000, len(songs)/60) # take untaged/corrupted data into account

    for num, footprint in songs.get_hash_iterator():
        if footprint not in hash_dict:
            hash_dict[footprint] = [num]
        else:
            hash_dict[footprint].append(num)

    if ar:
        for m in (matches for num, matches in hash_dict.iteritems() if 1 < len(matches) < wpt):
            h = []
            for num in m:
                song = songs[num]
                heapq.heappush(h,
                        (len(song.filename), song))

            for nb, other in h:
                if other != h[-1][1]:
                    print "rm '%s'"%(other.filename.replace("'", r"\'"))
                else:
                    print "# kept %s"%other.filename
    else:
        for m in (matches for num, matches in hash_dict.iteritems() if 1 < len(matches) < wpt):
            print "#", cnt.next()
            for num in m:
                total_cnt.next()
                print "%d: %s"%(num, songs[num].filename)
        print total_cnt.next()-cnt.next()-1, "# songs to be removed..."


do_find_dups.__doc__ = """
Find duplicates
Parameters:
    wpt: wrong positive threshold (ceil to not reach), default == auto
    ar: auto remove (ask for directory delection), the smallest directory always win
    """

def do_listallcmds():
    g = globals()
    undoc = []
    for cmd in (g[name] for name in g.keys() if name[:3] == 'do_'):
        if cmd.__doc__:
            print "%s:\n%s\n"%(cmd.func_name[3:], ('\n'.join('   %s'%l for l in cmd.__doc__.split('\n') if l.strip())))
        else:
            undoc.append(cmd.func_name[3:])
    print "undocumented:", ', '.join(undoc)

do_listallcmds.__doc__ = """ The developper's help (WIP functions also) """

