# vim: et ts=4 sw=4

import os
import sys
import web
from pkg_resources import resource_filename
from time import time
from zicdb.zshell import songs
from zicdb.zutils import compact_int, jdump, parse_line, uncompact_int, DEBUG

web.internalerror = web.debugerror

# Set default headers & go to templates directory
web.ctx.headers = [('Content-Type', 'text/html; charset=utf-8')]
render = web.template.render(resource_filename('zicdb', 'web_templates'))

try:
    from zplayer.playerlogic import  PlayerCtl
    from zplayer.events import DelayedAction, IterableAction
    import gobject
    from thread import start_new_thread
    # Allow glib calls (notifier)
    start_new_thread(gobject.MainLoop().run, tuple())
except ImportError:
    print "Failed loading player!"
    PlayerCtl = lambda *args: None

# Prepare some web stuff
urls = (
        '/player/(.*)', 'webplayer',
        '/(.*)', 'index',
        )

artist_form = web.form.Form(
        web.form.Hidden('id'),
        web.form.Textbox('pattern'),
        web.form.Checkbox('m3u'),
        )


class webplayer:
    player = PlayerCtl()

    GET = web.autodelegate('REQ_')
    lastlog = []

    def REQ_search(self):
        i = web.input()
        if i.get('pat'):
            it = self.player.fetch_playlist(i.host, pattern=i.pat)
            it.next()
            IterableAction(it).start(0.01)
            DelayedAction(self.player.select, 1).start(1)
        yield "OK"

    def REQ_infos(self):
        yield 'current track: %s\n'%self.player._cur_song_pos
        yield 'playlist size: %s\n'%len(self.player.playlist)
        yield '\n'.join('%s: %s'%(k, v) for k,v in self.player.selected.iteritems())

    def REQ_lastlog(self):
        return '\n'.join(self.lastlog)

    def REQ_playlist(self):
        for elt in self.player.playlist:
            yield str(list(elt))
            yield "\n"

    def REQ_shuffle(self):
        self.player.shuffle()

    def REQ_pause(self):
        self.player.pause()

    def REQ_prev(self):
        self.player.select(-1)

    def REQ_next(self):
        self.player.select(1)

class index:
    def GET(self, name):
        t0 = time()
        if artist_form.validates():
            try:
                artist_form.fill()
                song_id = artist_form['id'].value
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

        if artist_form['m3u'].value:
            web.header('Content-Type', 'audio/x-mpegurl')
            format = 'm3u'
        elif web.input().get('plain'):
            format = 'plain'
        elif web.input().get('json'):
            format = 'json'
        else:
            web.header('Content-Type', 'text/html; charset=utf-8')
            format = 'html'

        pattern = artist_form['pattern'].value
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
            yield render.plain(web.http.url, res)
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
            yield render.index(artist_form, res)


def do_serve():
    # UGLY !
    os.chdir( resource_filename('zicdb', 'static')[:-6] )
    sys.argv = ['zicdb', '9090']
    try:
        web.run(urls, globals())
    except:
        DEBUG()
        print 'kill', os.getpid()
        print os.kill(os.getpid(), 9)

