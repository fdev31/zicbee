import os
import logging
from logging import getLogger as get_log
log = get_log()

default_handler = logging.StreamHandler()
log.addHandler(default_handler)

default_formatter = logging.Formatter('[%(threadName)s %(relativeCreated)d] %(module)s %(funcName)s:%(lineno)s %(message)s')
default_handler.setFormatter( default_formatter )

