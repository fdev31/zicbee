# vim: et ts=4 sw=4
from __future__ import with_statement

__all__ = ['web_db_index', 'WEB_FIELDS', 'render']

import os
import web
import random
from threading import RLock
from time import time
from zicbee.core import zshell
from zicbee_lib.formats import compact_int, jdump, uncompact_int, dump_data_as_text
from zicbee.core.parser import parse_line
from zicbee_lib.config import config
from zicbee_lib.debug import DEBUG
from zicbee_lib import debug
from zicbee import __version__ as VERSION

WEB_FIELDS = 'artist album title length score tags __id__'.split()

web.internalerror = web.debugerror = web.debug = debug.log.debug

if debug.debug_enabled:
    web.config.debug = True
else:
    web.config.debug = None

def kill_server():
    zshell.songs.close()
    try:
        from zicbee.core.httpplayer import webplayer
        webplayer.player.close()
    except:
        pass

def allow_admin_mode():
    addr = web.ctx.env['REMOTE_ADDR']

    admins = config.allow_remote_admin
    allowed = ['127.0.0.1']
    if admins:
        if len(admins) == 1 and admins[0].lower() in ('yes', 'true', 'on'):
            return True
        allowed.extend(admins)
    return addr in allowed


# Set default headers & go to templates directory
web.ctx.headers = [('Content-Type', 'text/html; charset=utf-8'), ('Expires', 'Thu, 01 Dec 1994 16:00:00 GMT')]
from zicbee_lib.resources import resource_filename
try:
    render = web.template.render(resource_filename('zicbee.ui.web', 'templates'))
except Exception, e:
    DEBUG()
    class FakeRender(object):
        def __getattr__(self, name):
            return self
        def __call__(self, *args, **kw):
            return 'Unable to load templates'
    render = FakeRender()

# DB part

available_formats = [
        ('html', 'WWW Browser'),
        ('txt', 'Text'),
        ('json', 'JSON'),
        ('m3u', 'Playlist (m3u)'),
        ('zip', 'ZIP archive'),
        ]

DbSimpleSearchForm = web.form.Form(
        web.form.Hidden('id'),
        web.form.Textbox('pattern', description="Play pattern"),
        web.form.Dropdown('fmt', available_formats,
            value="html", description="Output"),
        )

import zipfile
#import cZipFile


class Zipper(list):
    """ Object used to handle zip files """
    def __init__(self, zipname):
        self.name = zipname

#    def extract(self, name=None, to_path=None, members=None, load=False):
#        name = name or self.name
#        zf = zipfile.ZipFile(name)
#        if load:
#            self[:] = [(x, '') for x in zf.namelist()]
#        zf.extractall(to_path, members)
#        zf.close()

    def saveSongs(self, as_name=None, prefix=''):
        name = as_name or self.name
        zf = zipfile.ZipFile(name, 'w', zipfile.ZIP_DEFLATED)
        for uri, song in self:
            fname = song.filename
            zf.write(fname, "/".join((song.artist, song.album, song.title))+"."+(fname.rsplit('.', 1)[-1]))
        zf.close()

#    def saveFiles(self, as_name=None, prefix=''):
#        name = as_name or self.name
#        zf = zipfile.ZipFile(name, 'w', zipfile.ZIP_DEFLATED)
#        for fname, dirname in self:
#            zf.write(fname, prefix+fname[len(dirname):])
#        zf.close()


def refresh_db():
    zshell.songs.commit()
    zshell.songs._create()
    zshell.songs.cleanup()

class web_db_index:

    _db_lock = RLock()

    def REQ_tag(self, song, tag):
        """ Tags a song
        tag/<song id>/<tag>

        Args:
            - song (int): song
            - tag (str): the tag you want to add to that song
        Returns:
            None
        """

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

    def REQ_rate(self, song, rating):
        """ Rate a song
        rate/<song id>/<rating>

        Args:
            - song (int): song
            - rating (int): the rate you want to give to that song
        Returns:
            None
        """
        web.debug('rate: song=%s rating=%s'%(song,rating))
        try:
            with self._db_lock:
                song_id = uncompact_int(song)
                zshell.songs[song_id].update(score=int(rating))
        finally:
            refresh_db()

    def REQ_multirate(self, ratings_list):
        """ Rate a list of songs
        multirate/[song id=rating]<,song id2=rating2><,song id3=rating3>...

        Args:
            - ratings_list: a list of tuples of the form::
                song=rating,song2=rating2,...
        Returns:
            None
        """
        web.debug('rate: ratings_list=%s'%ratings_list)
        try:
            ratings = [rating.split('=') for rating in ratings_list.split(',')]
            with self._db_lock:
                for song, rating in ratings:
                        song_id = uncompact_int(song)
                        zshell.songs[song_id].update(score=int(rating))
        finally:
            refresh_db()

    def REQ_version(self):
        """ Returns version of zicbee used on that instance

        Returns:
            None
        """
        yield VERSION

    def REQ_random(self):
        """ Returns a pattern with a random artist query
        If "what" parameter is specified, allow to change
        the random attribute, currently available:
         - artist
         - album
        """
        inp = web.input()
        what = inp.get('what', 'artist')
        if what.startswith('album'):
            what = ['album', list(zshell.songs.albums)]
        else:
            what = ['artist', list(zshell.songs.artists)]

        what[1] = random.choice(what[1])
        return 'pattern=%s:%s'%tuple(what)

    def REQ_artists(self):
        """ List all the artists

        Keywords:
            fmt (str, optional): output format

        Returns:
            A list of artists in desired format
        """
        inp = web.input()
        for d in dump_data_as_text(zshell.songs.artists, inp.get('fmt', 'txt')):
            yield d

    def REQ_albums(self):
        """ List all the albums

        Keywords:
            fmt (str, optional): output format

        Returns:
            A list of albums in desired format
        """
        inp = web.input()
        for d in dump_data_as_text(zshell.songs.albums, inp.get('fmt', 'txt')):
            yield d

    def REQ_genres(self):
        """ List all the genres

        Keywords:
            fmt (str, optional): output format

        Returns:
            A list of genres in desired format
        """
        inp = web.input()
        for d in dump_data_as_text(zshell.songs.genres, inp.get('fmt', 'txt')):
            yield d

    def REQ_set(self):
        if not allow_admin_mode():
            return "Not allowed"
        i = web.input()
        k = i.get('k')
        v = i.get('v')
        if v is not None:
            config[k] = v
        v = config[k]
        return "%s = %s"%(k, ', '.join(v) if isinstance(v, (list, tuple)) else v)

    def REQ_kill(self):
        """ Kills the application

        Returns:
            "Aaaah!"
        """
        if allow_admin_mode():
            kill_server()
            yield 'Aaaah!'
            raise SystemExit()

    def REQ_infos(self, song_id):
        """ Show infos about a song
        Either positional parameter or ``id`` keyword has to be given

        Keywords:
            fmt (str): output format
            id (str): id of the song
        Args:
            song_id (int): index of the song
        Returns:
            all the metadatas in desired format
        """


        af = DbSimpleSearchForm()
        if af.validates():
            af.fill()
            song_id = uncompact_int(af['id'].value)
            fmt = af['fmt'].value

        song = zshell.songs[song_id]
        d = dict( (f, getattr(song, f)) for f in song.fields ) if song else {}
        return dump_data_as_text(d, fmt)

    def REQ_get(self, *args):
        af = DbSimpleSearchForm()
        if af.validates():
            af.fill()
            song_id = uncompact_int(af['id'].value)
        filename = zshell.songs[song_id].filename
        web.header('Content-Type', 'application/x-audio')
        web.header('Content-Disposition',
                'attachment; filename:%s'%filename.rsplit('/', 1)[-1], unique=True)

        CHUNK=1024
        in_fd = file(filename)
        web.header('Content-Length', str( os.fstat(in_fd.fileno()).st_size ) )
        yield ''

        while True:
            data = in_fd.read(CHUNK)
            if not data: break
            y = (yield data)
        in_fd.close()
        return

    def GET(self, name):
        hd = web.webapi.ctx.homedomain
        inp = web.input()
        t0 = time()

        # XXX: move this to special commands, using dedicated Form()s
        # m3u flag has to move to "fmt"
        args = None
        song_id = None
        handler = None # special action handler executed before listing
        af = DbSimpleSearchForm()
        if af.validates():
            af.fill()
            song_id = af['id'].value

        if song_id:
            args = [song_id]

        if name:
            # Special actions (1rs level path)
            try:
                name, path = name.split('/', 1)
            except ValueError:
                name = name
                path = None
            try:
                handler = getattr(self, 'REQ_' + name)
            except AttributeError:
                handler = None

            if not args:
                if path:
                    args = path.split('/')
                else:
                    args = []

        if handler:
            # XXX: replace that with autodelegate as in httpplayer
            try:
                # execute the handler
                web.debug('%s: %r'%(handler, args))
                ret = handler(*args)
                if hasattr(ret, 'next'):
                    for chunk in ret:
                        yield chunk
                else:
                    yield ret
            except GeneratorExit:
                raise
            except Exception, e:
                DEBUG()

        else: # XXX: move that to a dedicated command ? (ex: .../db/q?pattern=... looks nice)
            # or use "index" ... (sounds good too !)
            format = af['fmt'].value or 'html'
            if format == 'm3u':
                web.header('Content-Type', 'audio/x-mpegurl')
            elif format == 'html':
                web.header('Content-Type', 'text/html; charset=utf-8')

            pattern = af['pattern'].value

            if pattern is None:
                res = xrange(0)
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
            elif format == 'zip':
                web.header('Content-Type', 'application/zip')
                import tempfile
                tmp_file = tempfile.NamedTemporaryFile()
                z = Zipper(tmp_file.name)
                z[:]= res
                z.saveSongs()
                tmp_file.seek(0)
                CZ = 2**18

                while True:
                    dat = tmp_file.read(CZ)
                    if not dat:
                        break
                    yield dat

                tmp_file.close()
                return
            elif not format or format == 'html':
                yield unicode(render.index(af, res, config.web_skin or 'default'))
            elif format in ('json', 'txt'):
                some_db = zshell.songs.databases.itervalues().next()['handle']
                # try to pre-compute useful things
                field_decoder = zip( WEB_FIELDS,
                        (some_db.f_decode[some_db.fields[fname]] for fname in WEB_FIELDS)
                        )
                yield ''

                infos_iterator = ( [r[0]] + [d(r[1][r[1].fields.index(f)]) for f, d in field_decoder]
                        for r in res )
                if format == 'json':
                    d = jdump
                else:
                    def d(line):
                        return ' | '.join(line[:4])

                try:
                    # TODO: optimise this (jdump by 100 size blocks)
                    for r in infos_iterator:
                        yield d(r)
                        yield '\n'
                    web.debug('handled in %.2fs (%.2f for select)'%(time() - t0, t_sel - t0))
                except Exception, e:
                    DEBUG()
                    web.debug("ERR: %s(%s)"% (type(e), e))
            else:
                # TODO: add support for zip output (returns a zip stream with all the songs)
                web.debug('unknown search mode')
                for r in res:
                    yield dump_data_as_text(r, format)

