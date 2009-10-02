import os
import readline
from cmd import Cmd
from functools import partial
from zicbee_lib.config import config, DB_DIR
from zicbee_lib.commands import commands
from zicbee_lib.core import iter_webget
import urllib

def execute(name=None, line=None):
    if line is None:
        args = name.split()
        name = args.pop(0)
    else:
        args = line.split()

    if name == 'help':
        for cmd, infos in commands.iteritems():
            print "%s : %s"%(cmd, infos[1])
        print """
                 Syntax quick sheet
    Tags:
      * id (compact style) * genre * artist * album * title * track
      * filename * score * tags * length

    Playlists (only with play command):
        use "pls: <name>" to store the request as "<name>"
        add ">" prefix to name to append instead of replacing
        "+" prefix inserts just next
        "#" = special name to point "current" playlist

    Numerics (length, track, score) have rich operators, default is "==" for equality
        length: >= 60*5
        length: < 60*3+30
        length: >100
        score: 5
        """

        return

    try:
        pattern, doc = commands[name]
        extras = None
    except ValueError:
        pattern, doc, extras = commands[name]

    if callable(pattern):
        pattern = pattern(*args)
        if not pattern:
            return

    args = [urllib.quote(a) for a in args]

    if '%s' in pattern:
        expansion = tuple(args)
    else:
        expansion = dict(args = '%20'.join(args), db_host=config['db_host'], player_host=config['player_host'])
    try:
        uri = pattern%expansion
    except Exception, e:
        print "Invalid arguments: %s"%e
    else:
        if extras and extras.get('uri_hook'):
            extras['uri_hook'](uri)
        r = iter_webget(uri)
        if r:
            if extras and extras.get('display_modifier'):
                extras['display_modifier'](r)
            else:
                for line in r:
                    print line

def show_help(name):
    print commands[name][1]

def complete_command(name, completer, cur_var, line, s, e):
    ret = completer(cur_var, line.split())
    return [cur_var+h[e-s:] for h in ret if h.startswith(cur_var)]

class Shell(Cmd):
    prompt = "Wasp> "
    def __init__(self):
        self._history = os.path.join(DB_DIR, 'wasp_history.txt')
        self._last_line = None
        try:
            readline.read_history_file(self._history)
        except IOError:
            'First time you launch Wasp! type "help" to get a list of commands.'

        for cmd, infos in commands.iteritems():
            setattr(self, 'do_%s'%cmd, partial(execute, cmd))
            setattr(self, 'help_%s'%cmd, partial(show_help, cmd))
            try:
                completer = commands[cmd][2]['complete']
            except (IndexError, KeyError):
                pass
            else:
                setattr(self, 'complete_%s'%cmd, partial(complete_command, cmd, completer))
        Cmd.__init__(self)
        self.names = [n for n in dir(self) if n.startswith('do_') and callable(getattr(self, n))]

    def do_help(self, line):
        line = line.strip()
        if line:
            try:
                getattr(self, 'help_%s'%line)()
            except AttributeError:
                print "Bzz Bzz"
        else:
            execute("help")

    def onecmd(self, line):
        try:
            word = line.split(None, 1)[0]
        except IndexError: # empty string
            if self._last_line:
                return self.onecmd(self._last_line)
            return

        if word not in commands.keys():
            possible_keys = [k for k in commands.keys() if k.startswith(word)]
            if len(possible_keys) == 1:
                line = possible_keys[0] + line[len(word):]
            elif not hasattr(self, 'do_%s'%word):
                if possible_keys:
                    print "Ambiguity: %s"%(', '.join(possible_keys))
                else:
                    print "Unkown command: %r, try 'help'."%word
                return
        try:
            r = Cmd.onecmd(self, line)
            self._last_line = line
            return r
        except Exception, e:
            print "Err: %s"%e
        except KeyboardInterrupt:
            print "Interrupted!"

    def get_names(self):
        return self.names

    def do_EOF(self, line):
        readline.set_history_length(int(config['history_size']))
        readline.write_history_file(self._history)
        raise SystemExit()

    do_exit = do_quit = do_bye = do_EOF


