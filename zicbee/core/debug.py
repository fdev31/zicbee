import os
import logging
log = logging.getLogger()

default_handler = logging.StreamHandler()
log.addHandler(default_handler)

if int(os.environ.get('DEBUG', 0)):
    log.setLevel(logging.NOTSET)

default_formatter = logging.Formatter('%(relativeCreated)d %(module)s %(funcName)s:%(lineno)s %(message)s\n')
default_handler.setFormatter( default_formatter )

