# vim: et ts=4 sw=4
import itertools
import os
import sys
from time import time
from zicdb.zshell import songs
from zicdb.zutils import jdump, parse_line, compact_int, uncompact_int

def do_serve():
    import web
    import urllib

    from pkg_resources import resource_filename
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
                    song_id = uncompact_int(artist_form['id'].value)
                    if name.startswith("get") and song_id:
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
                            yield data
                        return
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
            if pattern is None:
                res = None
            else:
                pat, vars = parse_line(pattern)
                web.debug(pattern, pat, vars)
                home = web.ctx['homedomain']+'/get?'
                urlencode = web.http.urlencode
                ci = compact_int
                res = (['/get/%s?id=%s'%(r.filename.rsplit('/', 1)[-1], ci(int(r.__id__))), r]
                        for r in songs.search(None, pat, **vars))
            t_sel = time()

            if format == 'm3u':
                yield render.playlist(web.http.url, res)
            elif format == 'plain':
                yield render.plain(web.http.url, res)
            elif format == 'json':
# Experimental code:
#                from itertools import izip
#                lbls = ('genre', 'artist', 'album', 'title', 'length')
#                idxs = (3, 4, 5, 6, 8)
#                fields = ('__id__', '__version__', 'filename', 'genre', 'artist', 'album', 'title', 'track', 'length')
#                dict_list = [
#                        (s0, dict(izip(lbls, s1._get_val_iter(*idxs))))
#                        for (s0, s1) in res]
#                dict_list = [
#                        ( dict( (f, getattr(s[1], f))
#                            for f in s[1].fields if (f == '__id__' or f[0] not in 'f_'))
#                            )
                        # /tuple(uri, dict)
#                        for s in res]

#                web.webug(dict_list[1])
                dict_list = [
                        (r[0], dict( (f, getattr(r[1], f) )
                            for f in r[1].fields
                            if (f == '__id__' or f[0] not in 'f_')) )
                        for r in res ]
                web.debug('handled in %.2fs (%.2f for select)'%(time() - t0, t_sel - t0))
                web.debug(dict_list[:10])
                try:
                    yield render.json(dict_list)
                    web.debug('rendered')
                except Exception, e:
                    web.debug(e)
            else:
                yield render.index(artist_form, res)


    # UGLY !
    sys.argv = ['zicdb', '9090']
    web.run(urls, locals())

