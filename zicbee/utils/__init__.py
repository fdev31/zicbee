import zicbee_lib as zl

def notify(title=None, description=None, icon=None, timeout=None):
    zl.debug.log.info("[%s] %s: %s"%(icon, title, description))

try:
    if not zl.config.config.notify:
        raise ValueError('notify disabled in user settings')
    from .notify import notify
except ValueError, e:
    zl.debug.log.warning("Not loading notification: %s", e.args[0])
except Exception, e:
    zl.debug.log.error("Can't load notify framework! %s"%e)
    zl.debug.DEBUG(False)

