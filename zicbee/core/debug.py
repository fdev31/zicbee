__all__ = ['DEBUG', 'debug_enabled', 'log']
import os
import logging
import traceback
from logging import getLogger
from zicbee.core.config import config

log = getLogger('zicbee')

try:
    debug_enabled = (str(config.debug).lower()[:1] not in 'fn') if config.debug else False
    # disable if "false" or "no"
except:
    debug_enabled = False

# environment overrides
if not debug_enabled and os.environ.get('DEBUG'):
    debug_enabled = os.environ['DEBUG'] != '0'

def traced(fn):
    def _get_decorator(decorated):
        def _decorator(*args, **kw):
            try:
                return decorated(*args, **kw)
            except:
                import pdb; pdb.set_trace()
        return _decorator
    return _get_decorator(fn)

def DEBUG():
    traceback.print_stack()
    traceback.print_exc()


if debug_enabled:
    default_formatter = logging.Formatter('[%(threadName)s %(relativeCreated)d] %(module)s %(funcName)s:%(lineno)s %(message)s')
    try:
        LOGFILENAME='zicbee.log'
        file(LOGFILENAME, 'a').close()
    except Exception:
        LOGFILENAME=None

    handlers = [ logging.StreamHandler() ] # first is stderr
    if LOGFILENAME:
        handlers.append( logging.FileHandler(LOGFILENAME) )

    # add handlers
    for h in handlers:
        log.addHandler(h)
        h.setFormatter( default_formatter )

    try:
        val = int(os.environ.get('DEBUG', 1))*10
    except ValueError:
        val = logging.DEBUG

    log.setLevel(val)
else:
    globals()['DEBUG'] = lambda: None # NO-OP if not debugging
    log.setLevel(logging.FATAL)

