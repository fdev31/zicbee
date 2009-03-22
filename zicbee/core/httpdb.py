# vim: et ts=4 sw=4
from __future__ import with_statement

__all__ = ['web_db_index', 'WEB_FIELDS', 'render']

import os
import web
from threading import RLock
from time import time
from zicbee.core import zshell
from zicbee.core.zutils import compact_int, jdump, parse_line, uncompact_int
from zicbee.core.config import config

WEB_FIELDS = 'artist album title length score tags'.split() + ['__id__']

web.config.debug = True if config.debug and str(config.debug).lower() in ('on', 'yes') else False
web.internalerror = web.debugerror

# Set default headers & go to templates directory
web.ctx.headers = [('Content-Type', 'text/html; charset=utf-8'), ('Expires', 'Thu, 01 Dec 1994 16:00:00 GMT')]
from pkg_resources import resource_filename
render = web.template.render(resource_filename('zicbee.ui.web', 'templates'))

# DB part

DbSimpleSearchForm = web.form.Form(
        web.form.Hidden('id'),
        web.form.Textbox('pattern'),
        web.form.Checkbox('m3u'),
        )

def refresh_db():
    zshell.songs.commit()
    zshell.songs._create()
    zshell.songs.cleanup()

class web_db_index:

    _db_lock = RLock()

    def tag(self, song, tag):

        song_id = uncompact_int(song)
        try:
            tag = unicode(tag)
            with self._db_lock:
                SEP=u','
                _t = zshell.songs[song_id].tags
                tag_set = set( _t.strip(SEP).split(SEP) ) if _t else set()
                for single_tag in tag.split(','):
                    tag_set.add(single_tag.strip())
                new_tag = ''.join((SEP,SEP.join(tag_set),SEP))
                zshell.songs[song_id].update(tags=new_tag)
        except Exception, e:
            web.debug('E!%s'%e)
        finally:
            refresh_db()

    def rate(self, song, rating):
        web.debug('rate: song=%s rating=%s'%(song,rating))
        try:
            with self._db_lock:
                song_id = uncompact_int(song)
                zshell.songs[song_id].update(score=int(rating))
        finally:
            refresh_db()

    def multirate(self, ratings_list):
        web.debug('rate: ratings_list=%s'%ratings_list)
        try:
            ratings = [rating.split('=') for rating in ratings_list.split(',')]
            with self._db_lock:
                for song, rating in ratings:
                        song_id = uncompact_int(song)
                        zshell.songs[song_id].update(score=int(rating))
        finally:
            refresh_db()

    def GET(self, name):
        hd = web.webapi.ctx.homedomain
        t0 = time()
        af = DbSimpleSearchForm()
        if name.startswith('rate/'):
            self.rate(*name.split('/', 3)[1:])
            return
        if name.startswith('multirate/'):
            self.multirate(name.split('/', 2)[1])
            return
        elif name.startswith('kill'):
            zshell.songs.close()
            raise SystemExit()
        elif name.startswith('tag'):
            self.tag(*name.split('/', 3)[1:])
            return
        elif af.validates():
            try:
                af.fill()
                song_id = af['id'].value
                if song_id:
                    song_id = uncompact_int(song_id)
                    if name.startswith("get"):
                        filename = zshell.songs[song_id].filename
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
                        song = zshell.songs[song_id]
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

        if pattern is None:
            res = None
        else:
            pat, vars = parse_line(pattern)
            urlencode = web.http.urlencode
            ci = compact_int
            web.debug('searching %s %s...'%(pat, vars))

            res = ([hd+'/db/get/%s?id=%s'%('song.'+ r.filename.rsplit('.', 1)[-1].lower(), ci(int(r.__id__))), r]
                    for r in zshell.songs.search(list(WEB_FIELDS)+['filename'], pat, **vars)
                    )
        t_sel = time()

        if format == 'm3u':
            yield unicode(render.m3u(web.http.url, res))
        elif format == 'plain':
            yield unicode(render.plain(af, web.http.url, res))
        elif format == 'json':
            some_db = zshell.songs.databases.itervalues().next()['handle']
            # try to pre-compute useful things
            field_decoder = zip( WEB_FIELDS,
                    (some_db.f_decode[some_db.fields[fname]] for fname in WEB_FIELDS)
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
                web.debug("ERR:", e)
        else:
            yield unicode(render.index(af, res))
