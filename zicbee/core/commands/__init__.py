# vim: et ts=4 sw=4

from zicbee.db import Database, DB_DIR
from zicbee.core.zshell import args, songs, DEFAULT_NAME
from zicbee.core.zutils import DEBUG
from zicbee.core.config import config
import urllib
import itertools

from .search import do_search
from .scan import do_scan
from .help import do_help
from .get import do_get
from .player import (do_play, do_pause,
        do_next, do_prev, do_shuffle,
        do_infos, do_playlist,
        do_tag, do_rate)


def do_kill(host=config.db_host):
    """ Kills the current db_host or any specified as argument """
    play_uri = 'http://%s/kill'%(host)
    try:
        urllib.urlopen(play_uri).read()
    except IOError:
        print "RIP."

def do_stfu(host=config.player_host):
    """ Kills the current player_host
    (in case db_host and player_host are the same, this command
    is equivalent to "kill")
    """
    play_uri = 'http://%s/kill'%(host)
    try:
        urllib.urlopen(play_uri).read()
    except IOError:
        print "RIP."

def do_serve(pure=False):
    """ Create a ZicDB instance
    parameters:
        pure (default: False): just start DB serving, no player
    """
    # chdir to serve files at the right place
    import os, sys
    from pkg_resources import resource_filename

    p = os.path.dirname(resource_filename('zicbee.ui.web', 'static'))
    os.chdir( p )

    # let's do webplayer
    import web
    from zicbee.player.webplayer import webplayer, web_db_index

    sys.argv = ['zicdb', '0.0.0.0:9090']
    try:
        import web.wsgiserver
        print "Running webplayer from", __file__
        if pure:
            urls = ('/db/(.*)', 'web_db_index',
                    '/(.*)', 'web_db_index')
        else:
            urls = ('/db/(.*)', 'web_db_index',
                    '/(.*)', 'webplayer')
        app = web.application(urls, locals())
        app.run()
    except:
        DEBUG()
        print os.kill(os.getpid(), 9)
        #print 'kill', os.getpid()

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

def do_shell():
    """ Start a PDB (dev/hackers only)"""
    import pdb; pdb.set_trace()

def do_bundle():
    """ Dump used database to specified archive (any filename) """
    if len(args) != 1:
        raise SystemExit("Need filename name as agment !")
    songs.dump_archive(args[0])

def do_reset():
    """ Destroy all songs on used database """
    songs.destroy()
    print "Database cleared!"


def do_hash():
    """ List all songs by id and hash (mostly to debug find_dups command) """
    for i in songs.get_hash_iterator():
        print "%8d / %s"%i

def do_find_dups(wpt=None, ar=None):
    """
    Find duplicates (WIP)
    Parameters:
        wpt: wrong positive threshold (ceil to not reach), default == auto
        ar: auto remove (ask for directory deletion), the smallest directory always wins
    """
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


def do_fullhelp():
    """ The Hacker's help (WIP functions included) """
    import inspect
    g = globals()
    undoc = []
    command_functions = [g[name] for name in g.keys() if name[:3] == 'do_']
    command_functions.sort()
    commands_display = []
    remote_commands_display = []
    for cmd in command_functions:
        if cmd.__doc__:
            arg_names, not_used, neither, dflt_values = inspect.getargspec(cmd)
            if dflt_values is None:
                dflt_values = []
            else:
                dflt_values = list(dflt_values)

            # Ensure they have the same length
            if len(dflt_values) < len(arg_names):
                dflt_values = [None] * (len(dflt_values) - len(arg_names))
                map(None, arg_names, dflt_values)

            doc = ':'.join('%s%s'%(arg_name, '%s'%('='+str(arg_val) if arg_val is not None else '')) for arg_name, arg_val in itertools.imap(None, arg_names, dflt_values))

            if any(h for h in arg_names if h.startswith('host') or h.endswith('host')):
                out = remote_commands_display
            else:
                out = commands_display

            out.append( "%s[::%s]"%(cmd.func_name[3:], doc) if len(doc) > 1 else cmd.func_name[3:] ) # title
            out.append( "%s\n"%( ('\n'.join('   %s'%l for l in cmd.__doc__.split('\n') if l.strip()))) ) # body
        else:
            undoc.append(cmd.func_name[3:])

    for cmd in itertools.chain( ['[REMOTE COMMANDS]\n'], remote_commands_display, ['[LOCAL COMMANDS]\n'], commands_display ):
        print cmd
    print "Not documented:", ', '.join(undoc)

