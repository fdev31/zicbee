# vim: et ts=4 sw=4

import os
import sys
import web
from pkg_resources import resource_filename
from time import time
from zicbee.core.zshell import songs
from zicbee.core.zutils import compact_int, jdump, parse_line, uncompact_int, DEBUG

web.internalerror = web.debugerror

# Set default headers & go to templates directory
web.ctx.headers = [('Content-Type', 'text/html; charset=utf-8')]
render = web.template.render(resource_filename('zicbee.ui.web', 'web_templates'))

from zicbee.player.playerlogic import  PlayerCtl
from zicbee.player.events import DelayedAction, IterableAction
import gobject
from thread import start_new_thread
    # Allow glib calls (notifier)
#    start_new_thread(gobject.MainLoop().run, tuple())

#except ImportError, e:
#    sys.stderr.write("Failed loading player! %s\n"%e)
#    PlayerCtl = lambda *args: None

# Prepare some web stuff
urls = (
        '/player/(.*)', 'webplayer',
        '/(.*)', 'index',
        )

SimpleSearchForm = web.form.Form(
        web.form.Hidden('id'),
        web.form.Hidden('host', value='localhost'),
        web.form.Textbox('pattern'),
        web.form.Checkbox('m3u'),
        )



class webplayer:
    player = PlayerCtl()

    GET = web.autodelegate('REQ_')
    lastlog = []

    def REQ_main(self):
        af = SimpleSearchForm(True)
        af.fill()
        yield render.player(
                af,
                self.player.selected,
                self.player.infos,
                )

    REQ_ = REQ_main # default page

    def REQ_search(self):
        yield
        web.debug('SEARCH')
        i = web.input('pattern')
        if i.get('pattern'):
            it = self.player.fetch_playlist(i.host or 'localhost', pattern=i.pattern)
            it.next()
            IterableAction(it).start(0.01)
            DelayedAction(self.player.select, 1).start(1)
        web.redirect('/player/main')

    def REQ_infos(self):
        i = web.input()
        format = i.get('fmt', 'txt')

        if format == 'txt':
            yield 'current track: %s\n'%self.player._cur_song_pos
            yield 'current position: %s\n'%self.player._position
            yield 'playlist size: %s\n'%len(self.player.playlist)
            for k, v in self.player.selected.iteritems():
                yield '%s: %s\n'%(k, v)
        elif format == 'json':
            _d = self.player.selected.copy()
            _d['pls_position'] = self.player._cur_song_pos
            _d['song_position'] = self.player._position
            _d['pls_size'] = len(self.player.playlist)
            yield jdump(_d)

    def REQ_lastlog(self):
        return '\n'.join(self.lastlog)

    def REQ_playlist(self):
        i = web.input()
        pls = self.player.playlist

        start = int(i.get('start', 0))

        format = i.get('fmt', 'txt')

        if i.get('res'):
            end = start + int(i.res)
        else:
            end = len(pls)

        window_iterator = (pls[i] for i in xrange(start, end))

        if format == 'txt':
            for elt in window_iterator:
                yield str(list(elt))
        elif format == 'json':
            yield jdump(list(window_iterator))

    def REQ_shuffle(self):
        yield
        self.player.shuffle()

    def REQ_pause(self):
        yield
        self.player.pause()

    def REQ_prev(self):
        yield
        self.player.select(-1)

    def REQ_next(self):
        yield
        self.player.select(1)

class index:
    def GET(self, name):
        t0 = time()
        af = SimpleSearchForm()
        if af.validates():
            try:
                af.fill()
                song_id = af['id'].value
                if song_id:
                    song_id = uncompact_int(song_id)
                    if name.startswith("get"):
                        filename = songs[song_id].filename
                        web.header('Content-Type', 'application/x-audio')
                        web.header('Content-Disposition',
                                'attachment; filename:%s'%filename.rsplit('/', 1)[-1], unique=True)

                        CHUNK=1024
                        in_fd = file(filename)
                        web.header('Content-Length', str( os.fstat(in_fd.fileno()).st_size ) )
                        yield

                        while True:
                            data = in_fd.read(CHUNK)
                            if not data: break
                            y = (yield data)
                        return
                    else:
                        song = songs[song_id]
                        for f in song.fields:
                            yield "<b>%s</b>: %s<br/>"%(f, getattr(song, f))
                        return
            except GeneratorExit:
                raise
            except Exception, e:
                web.debug(e)

        if af['m3u'].value:
            web.header('Content-Type', 'audio/x-mpegurl')
            format = 'm3u'
        elif web.input().get('plain'):
            format = 'plain'
        elif web.input().get('json'):
            format = 'json'
        else:
            web.header('Content-Type', 'text/html; charset=utf-8')
            format = 'html'

        pattern = af['pattern'].value
        fields = tuple('artist album title length __id__'.split())

        if pattern is None:
            res = None
        else:
            pat, vars = parse_line(pattern)
            web.debug(pattern, pat, vars)
            home = web.ctx['homedomain']+'/get?'
            urlencode = web.http.urlencode
            ci = compact_int
            res = (['/get/%s?id=%s'%('song'+r.filename[-4:], ci(int(r.__id__))), r]
                    for r in songs.search(list(fields)+['filename'], pat, **vars)
                    )
        t_sel = time()

        if format == 'm3u':
            yield render.playlist(web.http.url, res)
        elif format == 'plain':
            yield render.plain(af, web.http.url, res)
        elif format == 'json':
            # try to pre-compute useful things
            field_decoder = zip( fields,
                    (songs.db.f_decode[songs.db.fields[fname]] for fname in fields)
                    )
            yield

            infos_iterator = ( [r[0]] + [d(r[1][r[1].fields.index(f)]) for f, d in field_decoder]
                    for r in res )
            try:
                # TODO: optimise this (jdump by 100 size blocks)
                for r in infos_iterator:
                    yield jdump(r)
                    yield '\n'
                web.debug('handled in %.2fs (%.2f for select)'%(time() - t0, t_sel - t0))
            except Exception, e:
                web.debug(e)
        else:
            yield render.index(af, res)


def do_serve():
    # UGLY !
    os.chdir( resource_filename('zicbee.ui.web', 'static')[:-6] )
    sys.argv = ['zicdb', '0.0.0.0:9090']
    try:
        start_new_thread(web.run, (urls, globals()))
        gobject.MainLoop().run()
    except:
        DEBUG()
        print 'kill', os.getpid()
#        print os.kill(os.getpid(), 9)

