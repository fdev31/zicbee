from zicbee_lib.debug import log, DEBUG

try:
    from .notify import notify
except Exception, e:
    log.error("Can't load notify framework! %s"%e)
    DEBUG(False)
    def notify(title=None, description=None, icon=None, timeout=None):
        log.info("[%s] %s: %s"%(icon, title, description))

