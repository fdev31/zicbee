# vim: et ts=4 sw=4
from zicbee.core.config import config
from zicbee.core.debug import DEBUG

def do_serve(pure=False):
    """ Create a ZicDB instance
    parameters:
        pure (default: False): just start DB serving, no player
    """
    # chdir to serve files at the right place
    import os, sys
    from pkg_resources import resource_filename

    p = os.path.dirname(resource_filename('zicbee.ui.web', 'static'))
    os.chdir( p )

    import web
    from zicbee.core.httpdb import web_db_index

    pid = 0 # if not forking, still execute children commands
    do_detach = False # do not try to detach by default

    if config.fork:
        try:
            pid = os.fork()
            do_detach = True # fork succeded, try to detach
        except Exception, e:
            print "Can't fork: %s."%e

    if pid == 0:

        if do_detach:
            os.setsid()

        if not pure:
            # let's do webplayer
            try:
                from zicbee_player.webplayer import webplayer
            except (ImportError, RuntimeError):
                web.debug("Can't load webplayer, falling-back to pure db mode")
                DEBUG()
                pure = True

        sys.argv = ['zicdb', '0.0.0.0:%s'%(config.default_port)]
        try:
            print "%s listening on:"%('Song browser' if pure else 'Song browser and player')
            if pure:
                urls = ('/db/(.*)', 'web_db_index',
                        '/(.*)', 'web_db_index')
            else:
                urls = ('/db/(.*)', 'web_db_index',
                        '/(.*)', 'webplayer')
            app = web.application(urls, locals())
            app.run()
        except:
            DEBUG()
            print os.kill(os.getpid(), 9)
            #print 'kill', os.getpid()


