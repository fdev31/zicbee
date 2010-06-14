# vim: et ts=4 sw=4
import os
from zicbee_lib.resources import set_proc_title
from zicbee.core.httpdb import kill_server
from zicbee_lib.config import config
from zicbee_lib.debug import DEBUG

def abort():
    kill_server()
    raise SystemExit()

def make_app(no_player=False, fork=None):
    import web
    import signal
    from zicbee_lib.debug import debug_enabled
    from zicbee_lib.resources import resource_filename
    from zicbee.core.httpdb import web_db_index

    # Handle ^C keystroke (try atexit if any problem...)
    signal.signal(signal.SIGINT, abort)

    if not no_player:
        # let's do webplayer
        try:
            from zicbee.core.httpplayer import webplayer
        except (ImportError, RuntimeError):
            print "Can't load webplayer, falling-back to pure db mode"
            DEBUG()
            no_player = True

    try:
        # chdir to serve files at the right place
        p = os.path.dirname(resource_filename('zicbee.ui.web', 'static'))
        os.chdir( p )
    except Exception:
        DEBUG()

    pid = 0 # if not forking, still execute children commands
    do_detach = False # do not try to detach by default

    if config.fork and not debug_enabled or fork is True:
        try:
            pid = os.fork()
            do_detach = True # fork succeded, try to detach
        except Exception, e:
            print "Can't fork: %s."%e

    if pid == 0:

        if do_detach:
            os.setsid()

        print "%s listening on:"%('Song browser' if no_player else 'Song browser and player'),
        if no_player:
            urls = ('/db/(.*)', 'web_db_index',
                    '/(.*)', 'web_db_index'
                    )
        else:
            urls = ('/db/(.*)', 'web_db_index',
                    '/(.*)', 'webplayer')

        app = web.application(urls, locals())
        return app

def do_serve(pure=False):
    """ Create a ZicDB instance
    parameters:
        pure (default: False): just start DB serving, no player
    """
    import socket
    import sys

    set_proc_title('zicserve')
    sys.argv = ['zicdb', '0.0.0.0:%s'%(config.default_port)]

    try:
        make_app(no_player=pure).run()
    except SystemExit:
        print "ciao!"
    except socket.error:
        print "Already running!"
        try:
            abort()
        finally:
            raise SystemExit()
    except:
        DEBUG()
        try:
            abort()
        finally:
            print os.kill(os.getpid(), 9)
        #print 'kill', os.getpid()

