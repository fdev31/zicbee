from zicbee_lib.debug import log, DEBUG

try:
    from .notify import notify
except Exception, e:
    log.error("Can't load notify framework! %s"%e)
    DEBUG()
    def notify(title, description, icon, timeout):
        log.info("[%s] %s: %s"%(icon, title, description))

