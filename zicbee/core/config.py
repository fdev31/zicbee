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


media_config = {
        'mp3' : {'player_cache': 128, 'init_chunk_size': 2**17, 'chunk_size': 2**14},
        'ogg' : {'player_cache': 128, 'init_chunk_size': 2**17, 'chunk_size': 2**14},
        'mp4' : {'player_cache': 128, 'init_chunk_size': 2**17, 'chunk_size': 2**14},
        'aac' : {'player_cache': 128, 'init_chunk_size': 2**17, 'chunk_size': 2**14},
        'vqf' : {'player_cache': 128, 'init_chunk_size': 2**17, 'chunk_size': 2**14},
        'wmv' : {'player_cache': 128, 'init_chunk_size': 2**17, 'chunk_size': 2**14},
        'wma' : {'player_cache': 128, 'init_chunk_size': 2**17, 'chunk_size': 2**14},
        'm4a' : {'player_cache': 128, 'init_chunk_size': 2**17, 'chunk_size': 2**14},
        'asf' : {'player_cache': 128, 'init_chunk_size': 2**17, 'chunk_size': 2**14},
        'oga' : {'player_cache': 128, 'init_chunk_size': 2**17, 'chunk_size': 2**14},
        'flac' : {'player_cache': 4096, 'init_chunk_size': 2**22, 'chunk_size': 2**20},
        }

if config.debug:
    import logging
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

