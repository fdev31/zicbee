# vim: et ts=4 sw=4

import os
import sys
import web
from pkg_resources import resource_filename
from time import time
from zicbee.core.zshell import songs
from zicbee.core.zutils import compact_int, jdump, parse_line, uncompact_int
from zicbee.core.zutils import DEBUG

web.internalerror = web.debugerror

# Set default headers & go to templates directory
web.ctx.headers = [('Content-Type', 'text/html; charset=utf-8')]
render = web.template.render(resource_filename('zicbee.ui.web', 'web_templates'))

SimpleSearchForm = web.form.Form(
        web.form.Hidden('id'),
        web.form.Textbox('pattern'),
        web.form.Checkbox('m3u'),
        )

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
            urlencode = web.http.urlencode
            ci = compact_int
            res = (['/search/get/%s?id=%s'%('song'+r.filename[-4:], ci(int(r.__id__))), r]
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


def do_serve(play=None):
    # UGLY !
    # Prepare some web stuff
    urls = None
    if play:
        from zicbee.player.webplayer import webplayer
        globals().update({'webplayer': webplayer})
        p = os.path.dirname(resource_filename('zicbee.ui.web', 'static'))
        os.chdir( p )
        urls = ('/player/(.*)', 'webplayer',
                '/(.*)', 'index')
    else:
        urls = ('/(.*)', 'index',)
    sys.argv = ['zicdb', '0.0.0.0:9090']
    try:
        print __file__
        web.run(urls, globals())
    except:
        DEBUG()
        #print 'kill', os.getpid()
        print os.kill(os.getpid(), 9)

