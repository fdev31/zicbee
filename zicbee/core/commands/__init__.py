# vim: et ts=4 sw=4

from zicbee.db import Database, DB_DIR
from zicbee.core import zshell
from zicbee.core.zshell import DEFAULT_NAME
from zicbee.core.zutils import get_help_from_func
from zicbee.core.debug import DEBUG, log
from zicbee.core.config import config, DB_DIR, defaults_dict
from zicbee.core import parse_cmd, execute_cmd, setup_db # needed by shell command
import urllib
import itertools
from time import time as get_time
import socket

try:
    socket.setdefaulttimeout(int(config.socket_timeout)) # setsocket  timeout, for interactive cmds
except Exception, e:
    log.warning("unable to set socket timeout to '%s': %s.", config.socket_timeout, e)

from .search import do_search
from .scan import do_scan
from .help import do_help
from .get import do_get
from .player import (do_play, do_pause,
        do_next, do_prev, do_shuffle,
        do_infos, do_playlist,
        do_tag, do_rate)

from cmd import Cmd
class Shell(Cmd):
    def __init__(self, prompt='ZicBee'):
        Cmd.__init__(self)
        self.history = dict(filename=None, value=[])
        if config.enable_history:
            try:
                import os
                history_file = os.path.join(DB_DIR, 'shell_history.txt')
                self.history['filename'] = history_file
                self.history['value'] = [l.rstrip() for l in file(history_file).readlines()]
                import readline
                for hist in self.history['value']:
                    readline.add_history(hist)
            except Exception, e:
                print "No history loaded: %s"%e
                self.history['value'] = []
        else:
            self.history['value'] = []

        self.commands = [name for name, obj in globals().iteritems() if name.startswith('do_') and callable(obj)]
        self._prompt = prompt
        self._refresh_prompt()

    def _refresh_prompt(self):
        self.prompt = "[%s > %s]\n%s> "%(config.db_host, config.player_host, self._prompt)

    def get_names(self):
        return self.commands

    def onecmd(self, line):
        if not line:
            line = 'help'

        try:
            cmd, arg = line.split(None, 1)
        except:
            cmd = line
            arg = []
        else:
            arg = arg.split()
        self.lastcmd = line
        if cmd == '':
            return self.default(line)
        elif cmd in ('EOF', 'bye', 'exit', 'logout'):
            # save history & exit
            try:
                hist_fd = file(self.history['filename'], 'w')
                try:
                    hist_size = int(config.history_size)
                except ValueError:
                    hist_size = 100 # default value
                hist_fd.writelines("%s\n"%l for l in self.history['value'][-hist_size:])
            except Exception, e:
                print "Cannot save history file: %s."%(e)
            raise SystemExit('bye bye')
        else:
            db_name, new_args, action, p, kw = parse_cmd(line.split(None, 1)[0], *arg)
            if db_name:
                # re-init db & args
                setup_db(db_name, new_args)
            else:
                zshell.args[:] = new_args # remplace args with new args

            try:
                t0 = get_time()
                execute_cmd(action, *p, **kw)
                elapsed = get_time() - t0
                if elapsed > 0.4:
                    print "took %.1fs"%elapsed

            except Exception, e:
                print "ERROR: %s"%e
            except KeyboardInterrupt:
                print "Interrupted!"
            else:
                if not self.history['value'] or self.history['value'][-1] != line: # avoid consecutive clones
                    self.history['value'].append(line)

            self._refresh_prompt()

def do_shell():
    """ Starts a shell allowing you any command. """
    shell = Shell()
    shell._prompt = 'ZicBee'
    shell.cmdloop('Welcome to zicbee, press ENTER for help.')

def do_set():
    """ set a config variable to the given value
    list all variables and values if no argument is given"""

    if not zshell.args:
        # dumps *
        values = defaults_dict.keys()
#        print "[DEFAULT]"

        not_found = []
        for param in values:
            try:
                print "%s = %s"%(param, getattr(config, param))
            except:
                not_found.append(param)

        if not_found:
            print "unavaible: %s"%(', '.join(not_found))

    elif zshell.args and len(zshell.args) < 4:
        # (re)set a value

        if len(zshell.args) == 2 or (len(zshell.args) == 3 and zshell.args[1] == '='):
            # set a value
            if zshell.args[1] == '=':
                del zshell.args[1]
            setattr(config, zshell.args[0], zshell.args[1])
        elif len(zshell.args) == 1:
            # reset (blank) a value
            setattr(config, zshell.args[0], '')

    else:
        print """Takes exactly 2 arguments: set <variable> <value>, takes no param to list variables.
        giving no arguments will print every variable
        a single parameter will be reset (blanked) """

def do_kill(host=None):
    """ Kills the current db_host or any specified as argument """
    if host is None:
        host = config.db_host
    play_uri = 'http://%s/db/kill'%(host)
    try:
        urllib.urlopen(play_uri).read()
    except IOError:
        print "RIP."

def do_stfu(host=None):
    """ Kills the current player_host
    (in case db_host and player_host are the same, this command
    is equivalent to "kill")
    """
    if host is None:
        config.player_host
    play_uri = 'http://%s/close'%(host)
    try:
        urllib.urlopen(play_uri).read()
    except IOError:
        print "Silence."

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

    import web
    from zicbee.core.httpdb import web_db_index

    pid = 0 # if not forking, still execute children commands
    do_detach = False # do not try to detach by default

    if config.fork:
        try:
            pid = os.fork()
            do_detach = True # fork succeded, try to detach
        except Exception, e:
            print "Can't fork: %s."%e

    if pid == 0:

        if do_detach:
            os.setsid()

        if not pure:
            # let's do webplayer
            try:
                from zicbee.player.webplayer import webplayer
            except RuntimeError:
                web.debug("Can't load webplayer, falling-back to pure db mode")
                DEBUG()
                pure = True

        sys.argv = ['zicdb', '0.0.0.0:%s'%(config.default_port)]
        try:
            print "Running web%s from %s"%('db' if pure else 'player', __file__)
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

def do_debug():
    """ Start a PDB (dev/hackers only)"""
    import pdb; pdb.set_trace()

def do_bundle():
    """ Dump used database to specified archive (any filename) """
    if len(zshell.args) != 1:
        raise SystemExit("Need filename name as agment !")
    zshell.songs.dump_archive(zshell.args[0])

def do_reset():
    """ Destroy all songs on used database """
    zshell.songs.destroy()
    print "Database cleared!"


def do_hash():
    """ List all songs by id and hash (mostly to debug find_dups command) """
    for i in zshell.songs.get_hash_iterator():
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
        wpt = min(1000, len(zshell.songs)/60) # take untaged/corrupted data into account

    for num, footprint in zshell.songs.get_hash_iterator():
        if footprint not in hash_dict:
            hash_dict[footprint] = [num]
        else:
            hash_dict[footprint].append(num)

    if ar:
        for m in (matches for num, matches in hash_dict.iteritems() if 1 < len(matches) < wpt):
            h = []
            for num in m:
                song = zshell.songs[num]
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
                print "%d: %s"%(num, zshell.songs[num].filename)
        print total_cnt.next()-cnt.next()-1, "# songs to be removed..."


def do_fullhelp():
    """ The Hacker's help [read standard help before !!] (WIP functions included) """
    g = globals()
    undoc = []
    command_functions = [g[name] for name in g.keys() if name[:3] == 'do_']
    command_functions.sort()
    commands_display = []
    remote_commands_display = []
    for cmd in command_functions:
        cmd_help, cmd_is_remote = get_help_from_func(cmd)

        if cmd_is_remote:
            remote_commands_display.append(cmd_help)
        else:
            commands_display.append(cmd_help)

        if not '\n' in cmd_help:
            undoc.append(cmd.func_name[3:])

    for cmd in itertools.chain( ['[REMOTE COMMANDS]\n'], remote_commands_display, ['[LOCAL COMMANDS]\n'], commands_display ):
        print cmd
    print "Not documented:", ', '.join(undoc)

