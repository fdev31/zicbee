# vim: et ts=4 sw=4
import os
from cmd import Cmd
from time import time as get_time
from zicbee.core import execute_cmd, parse_cmd, setup_db, zshell
from zicbee.core.config import config, DB_DIR
from zicbee.db import DB_DIR
import zicbee

def do_shell():
    """ Starts a shell allowing you any command. """
    shell = Shell()
    shell._prompt = 'ZicBee'
    shell.cmdloop('Welcome to zicbee-%s, press ENTER for help.'%zicbee.__version__)

class Shell(Cmd):
    def __init__(self, prompt='ZicBee'):
        Cmd.__init__(self)
        self._db_host = None
        self._player_host = None

        self.webget = zicbee.core.commands.misc_commands._webget

        self.history = dict(filename=None, value=[])
        if config.enable_history:
            try:
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

        self.commands = [name for name in dir(zicbee.core.commands) if name.startswith('do_') and callable(getattr(zicbee.core.commands, name))]
        self._prompt = prompt
        self._refresh_prompt()

    def _refresh_prompt(self):
        ph = self._player_host
        dh = self._db_host

        local_hostname = ('localhost:%s'%config.default_port)

        if (ph is None and dh is None and config.db_host == config.player_host == local_hostname) or \
                (ph == dh == local_hostname):
            self.prompt = '[local]\n%s> '%self._prompt
        else:
            if ph != config.player_host:
                try:
                    if config.player_host.startswith('localhost:'):
                        raise Exception()
                    version = self.webget(config.player_host+'/db/version')
                except Exception:
                    self._player_host = config.player_host
                else:
                    self._player_host = "%s (%s)"%(config.player_host, version.strip() if version else '??')

            if dh != config.db_host:
                try:
                    if config.db_host.startswith('localhost:'):
                        raise Exception()
                    version = self.webget(config.db_host+'/db/version')
                except Exception:
                    self._db_host = config.db_host
                else:
                    self._db_host = "%s (%s)"%(config.db_host, version.strip() if version else '??')

            self.prompt = "[%s > %s]\n%s> "%(self._db_host, self._player_host, self._prompt)

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
                candidates = [cmd[3:] for cmd in self.commands if cmd.startswith('do_'+action)]

                if len(candidates) == 1: # support abbreviated commands
                    action = candidates[0]

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

