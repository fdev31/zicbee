from zicbee.core.debug import log
try:
    from .notify import notify
except Exception, e:
    log.error("Can't load notify framework! %s"%e)
    DEBUG()
    def notify(title, description, icon, timeout):
        log.info("[%s] %s: %s"%(icon, title, description))

