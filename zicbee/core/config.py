import os
import atexit
import ConfigParser

__all__ = ['DB_DIR', 'defaults_dict', 'config']

DB_DIR = os.path.expanduser(os.getenv('ZICDB_PATH') or '~/.zicdb')
try: # Ensure personal dir exists
    os.mkdir(DB_DIR)
except:
    pass

defaults_dict = {
        'streaming_file' : '/tmp/zsong',
        'download_dir' : '/tmp',
        'db_host' : 'localhost:9090',
        'player_host' : 'localhost:9090',
        'debug' : '',
        'default_search' : '',
        'web_skin' : '',
        }

config_filename = os.path.join(DB_DIR, 'config.ini')

class ConfigObj(object):

    _cfg = ConfigParser.ConfigParser(defaults_dict)

    def __init__(self):
        if os.path.exists(config_filename):
            self._cfg.read(config_filename)
        else:
            self._cfg.write(file(config_filename, 'w'))

    def __setattr__(self, name, val):
        return self._cfg.set('DEFAULT', name, val)

    def __getattr__(self, name):
        return self._cfg.get('DEFAULT', name)

# Ensure the file is written on drive
atexit.register(lambda: config._cfg.write(file(config_filename, 'w')))

config = ConfigObj()

if config.debug:
    import logging
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

