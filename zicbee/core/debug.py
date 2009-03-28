__all__ = ['DEBUG', 'debug_enabled', 'log']
import os
import logging
import traceback
from logging import getLogger
from zicbee.core.config import config

log = getLogger('zicbee')

default_formatter = logging.Formatter('[%(threadName)s %(relativeCreated)d] %(module)s %(funcName)s:%(lineno)s %(message)s')

# add two handlers
for h in logging.FileHandler('/tmp/zicbee.log'), logging.StreamHandler():
    log.addHandler(h)
    h.setFormatter( default_formatter )

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

debug_enabled = ('DEBUG' in os.environ) or config.debug

if debug_enabled:
    try:
        val = logging.ERROR - int(os.environ.get('DEBUG', 1))*10
    except ValueError:
        val = logging.DEBUG

    log.setLevel(val)
else:
    globals()['DEBUG'] = lambda: None # NO-OP if not debugging

