import gobject
gobject.threads_init()

from zicdb.zutils import DEBUG

class DelayedAction(object):
    def __init__(self, fn, *args, **kw):
        self.fn = fn
        self.args = list(args)
        self.kw = kw
        self.running = None
        self._delay = 1

    def _run(self, *args):
        try:
            self.fn(*self.args, **self.kw)
            self.running = None
        except Exception, e:
            DEBUG()
        return False

    def start(self, delay, prio=gobject.PRIORITY_DEFAULT_IDLE):
        """ start action after 'delay' seconds. """
        self.stop()
        self.running = gobject.timeout_add(int(delay*1000), self._run, priority=prio)

    def stop(self):
        if self.running is not None:
            gobject.source_remove(self.running)
        self.running = None

class IterableAction(object):
    def __init__(self, it):
        self.it = it
        self.running = None
        self._delay = 1

    def _run(self, *args):
        if self.running is None:
            return False
        try:
            self.it.next()
        except StopIteration:
            self.stop()
        else:
            return True
        return False

    def start(self, delay=0, prio=gobject.PRIORITY_DEFAULT_IDLE):
        """ start action after 'delay' seconds. """
        self.stop()
        self.running = gobject.timeout_add(int(delay*1000), self._run, priority=prio)
        return self

    def start_on_fd(self, fd, prio=gobject.PRIORITY_DEFAULT_IDLE):
        """ start action if 'fd' is readable. """
        self.stop()
        self.running = gobject.io_add_watch(fd, gobject.IO_IN, self._run, priority=prio)
        return self

    def stop(self):
        if self.running is not None:
            gobject.source_remove(self.running)
        self.running = None

