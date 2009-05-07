# vim: et ts=4 sw=4
__all__ = ['do_kill', 'do_stfu', 'do_hash', 'do_reset', 'do_bundle', 'do_debug']

import urllib
from zicbee.core import zshell
from zicbee.core.config import config, defaults_dict, DB_DIR
from zicbee.core.zshell import DEFAULT_NAME
from zicbee.db import Database, DB_DIR

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

def _webget(uri):
    if not uri.startswith('http://'):
        uri = "http://" + uri.lstrip('/')
    try:
        return urllib.urlopen(uri).read()
    except IOError, e:
        print "webget(%s): %s"%(uri, e)

def do_stfu(host=None):
    """ Kills the current player_host
    (in case db_host and player_host are the same, this command
    is equivalent to "kill")
    """
    if host is None:
        host = config.player_host
    _webget('%s/close'%host)
    _webget('%s/db/kill'%host)

def do_kill(host=None):
    """ Kills the current db_host or any specified as argument """
    if host is None:
        host = config.db_host
    _webget('%s/close'%host)
    _webget('%s/db/kill'%host)

