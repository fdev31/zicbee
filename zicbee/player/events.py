import gobject
gobject.threads_init()

from zicbee.core.zutils import DEBUG
from zicbee.core.debug import log

class DelayedAction(object):
    def __init__(self, fn, *args, **kw):
        """ You may pass _prio & _delay as keyword arguments
        """
        self.fn = fn
        self.running = None

        self._prio = kw.get('_prio', gobject.PRIORITY_DEFAULT_IDLE)
        try:
            del kw['_prio']
        except KeyError:
            pass

        self._delay = int(kw.get('_delay', 1) * 1000)
        try:
            del kw['_delay']
        except KeyError:
            pass

        self.args = tuple(args)
        self.kw = kw

    def _run(self, *args):
        try:
            self.fn(*self.args, **self.kw)
            self.running = None
        except Exception, e:
            DEBUG()
        return False

    def start(self, delay=None, prio=None, args=None, kwargs=None):
        """ (Re)Start the action
        if delay and/or prio are not specified, last used are used
        """
        """ start action after 'delay' seconds. """

        if delay is not None:
            self._delay = int(delay * 1000)

        if prio is not None:
            self._prio = prio

        if args is not None:
            self.args = args

        if kwargs is not None:
            self.kwargs = kwargs

        self.stop()
        self.running = gobject.timeout_add(self._delay, self._run,
                priority=self._prio)

    def stop(self):
        """ Stop the action if running """
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
        except:
            DEBUG()
            log.error('STOPPING %r!', self)
        else:
            return True
        return False

    def __repr__(self):
        return "<IterableAction %s %srunning/%s>"%(self.it, '' if self.running else 'not ', self._delay)

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

