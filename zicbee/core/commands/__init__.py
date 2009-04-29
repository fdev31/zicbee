# vim: et ts=4 sw=4

import itertools
import socket
from zicbee.core.config import config
from zicbee.core.debug import log
from zicbee.core.zutils import get_help_from_func

try:
    socket.setdefaulttimeout(int(config.socket_timeout)) # setsocket  timeout, for interactive cmds
except Exception, e:
    log.warning("unable to set socket timeout to '%s': %s.", config.socket_timeout, e)

from .misc_commands import do_kill, do_stfu, do_hash, do_reset, do_bundle, do_debug
from .set import do_set
from .list import do_list
from .find_dups import do_find_dups
from .serve import do_serve
from .shell import do_shell
from .search import do_search
from .scan import do_scan
from .help import do_help
from .get import do_get
from .player import (do_play, do_clear, do_pause,
        do_next, do_prev, do_shuffle,
        do_infos, do_playlist,
        do_tag, do_rate)

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

