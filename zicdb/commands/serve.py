# vim: et ts=4 sw=4

import os
import sys
import web
from pkg_resources import resource_filename
from time import time
from zicdb.zshell import songs
from zicdb.zutils import compact_int, jdump, parse_line, uncompact_int

render = web.template.render(resource_filename('zicdb', 'web_templates'))
web.template.Template.globals['jdump'] = jdump
os.chdir( resource_filename('zicdb', 'static')[:-6] )

urls = (
        '/(.*)', 'index',
        )

artist_form = web.form.Form(
        web.form.Hidden('id'),
        web.form.Textbox('pattern'),
        web.form.Checkbox('m3u'),
        )

class index:
    def GET(self, name):
        t0 = time()
        if artist_form.validates():
            try:
                artist_form.fill()
                song_id = artist_form['id'].value
                if name.startswith("get") and song_id:
                    song_id = uncompact_int(song_id)
                    filename = songs[song_id].filename
                    web.header('Content-Type', 'application/x-audio')
                    web.header('Content-Disposition',
                            'attachment; filename:%s'%filename.rsplit('/', 1)[-1], unique=True)

                    CHUNK=1024
                    in_fd = file(filename)
                    web.header('Content-Length', str( os.fstat(in_fd.fileno()).st_size ) )

                    while True:
                        data = in_fd.read(CHUNK)
                        if not data: break
                        y = (yield data)
                    return
            except GeneratorExit:
                raise
            except Exception, e:
                web.debug(e)

        if artist_form['m3u'].value:
            web.header('Content-Type', 'audio/x-mpegurl')
            format = 'm3u'
        elif web.input().get('plain'):
            web.header('Content-Type', 'text/plain')
            format = 'plain'
        elif web.input().get('json'):
            web.header('Content-Type', 'text/plain')
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
    sys.argv = ['zicdb', '9090']
    try:
        web.run(urls, globals())
    except:
        print 'kill', os.getpid()
        print os.kill(os.getpid(), 9)

