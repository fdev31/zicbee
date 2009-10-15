import os
import readline
from cmd import Cmd
from functools import partial
from zicbee_lib.commands import commands, execute
from zicbee_lib.config import config, DB_DIR
from zicbee_lib.debug import DEBUG


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
            try:
                completer = commands[cmd][2]['complete']
            except (IndexError, KeyError):
                pass # no completor
            else:
                setattr(self, 'complete_%s'%cmd, partial(complete_command, cmd, completer))
        Cmd.__init__(self)
        self.names = ['do_%s'%c for c in commands.keys()] + ['do_help']

    def onecmd(self, line):
        try:
            cmd, arg, line = self.parseline(line)
            if not line:
                return self.emptyline()
            if cmd is None:
                return self.default(line)
            self.lastcmd = line
            if cmd == '':
                ret = self.default(line)
            else:
                ret = execute(cmd,arg)
        except Exception, e:
            print "Err: %s"%e
            DEBUG()
        except KeyboardInterrupt:
            print "Interrupted!"
        else:
            print "."
            return ret

    def get_names(self):
        return self.names

    def do_EOF(self, line):
        try:
            readline.set_history_length(int(config['history_size']))
        except:
            pass

        readline.write_history_file(self._history)
        raise SystemExit()

    do_exit = do_quit = do_bye = do_EOF


