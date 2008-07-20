# vim: et ts=4 sw=4
from __future__ import with_statement

import web
from pkg_resources import resource_filename
from zicbee.core.zutils import jdump, jload # json in/out
import thread
from threading import RLock
from . import mp # player
import random # shuffle
import urllib # get playlist
from time import sleep # background thread

web.internalerror = web.debugerror

# Set default headers & go to templates directory
web.ctx.headers = [('Content-Type', 'text/html; charset=utf-8'), ('Expires', 'Thu, 01 Dec 1994 16:00:00 GMT')]
render = web.template.render(resource_filename('zicbee.ui.web', 'web_templates'))

SimpleSearchForm = web.form.Form(
        web.form.Hidden('id'),
        web.form.Textbox('host', description='Search host', value='localhost'),
        web.form.Textbox('pattern', description='Search pattern'),
        web.form.Textbox('tempname', description='Temporary name'),
        )

class PlayerCtl(object):
    """ The player interface, this should lead to a constant code, with an interchangeable backend
    See self.player.* for the needed interface.
    """
    def __init__(self):
        self._cur_song_pos = -1
        self.playlist = []
        self.views = []
        self.player = mp.MPlayer()
        self.position = None
        self._lock = RLock()
        self._paused = False
        thread.start_new_thread(self._main_loop, tuple())
        self._named_playlists = dict()

    def _main_loop(self):
        while True:
            if not self._paused and len(self.playlist):
                try:
                    try:
                        with self._lock:
                            self.position = int(self.player.prop_stream_pos/10000)
                    except:
                        self.position = None

                    web.debug('pos: %s'%self.position)

                    if self.position is None:
                        i = self.select(1)
                        while True:
                            try:
                                with self._lock:
                                    i.next()
                            except StopIteration:
                                break
                except Exception, e:
                    web.debug('E: %s'%e)
                except:
                    web.debug('E: ???')
            sleep(1)

    def select(self, sense):
        """ Selects a song, according to the given offset
        ex.: self.select(1) # selects the next track
        self.select(-1) # selects the previous track
        self.select(0) # no-op
        """
        with self._lock:
            pos = self._cur_song_pos
            self._cur_song_pos += sense
            web.debug(self.infos, self.selected)

            if self._cur_song_pos > len(self.playlist):
                self._cur_song_pos = -1
            elif self._cur_song_pos < -1:
                self._cur_song_pos = -1

            song_name = "zsong.zic"
            dl_it = self._download_zic(self.selected_uri, song_name)
            dl_it.next()
            web.debug('select: %d'%self._cur_song_pos)
            if pos != self._cur_song_pos:
                web.debug("Loadfile %d/%s : %s !!"%(self._cur_song_pos, len(self.playlist), song_name))
                self.player.loadfile(song_name)
            self._paused = False
        return dl_it

    def shuffle(self):
        """ Shuffle the playlist, and selects the first track
        if the playlist is empty, do nothing
        """
        if len(self.playlist) == 0:
            return
        with self._lock:
            random.shuffle(self.playlist)
            self._cur_song_pos = 0

    def seek(self, val):
        """ Seek according to given value
        """
        with self._lock:
            self.player.seek(val)

    def pause(self):
        """ (Un)Pause the player
        """
        with self._lock:
            self.player.pause()
            self._paused = not self._paused

    def delete_playlist(self, name):
        """ Delete the given named playlist (by name) """
        del self._named_playlists[name]

    def delete_entry(self, position):
        """ delete the song at the given position """
        del self.playlist[position]

    def move_entry(self, pos1, pos2):
        """ Swap two entries in the current playlist """
        p = self.playlist
        p[pos1], p[pos2] = p[pos2], p[pos1]

    def playlist_change(self, operation, pls_name):
        """ copy or append a named playlist to the active one
        """
        if operation == 'copy':
            self.playlist = self._named_playlists[pls_name]
            self._cur_song_pos = 0
        if operation == 'append':
            self.playlist.extend(self._named_playlists[pls_name])

    def fetch_playlist(self, hostname=None, temp=False, **kw):
        """
        Fetch a playlist from a given hostname,
        can take any keyword, will be passed with the remote command
        some useful keywords:
            pattern: a search string
            db: the database name (default is ok in general)
        if the temp keyword is given,
        a temporary playlist will be created with the given name
        (the main one is not affected)
        returns an iterator
        """
        hostname = hostname.strip()
        if not hostname:
            hostname = '127.0.0.1'

        if ':' not in hostname:
            hostname += ':9090'

        with self._lock:
            self.hostname = hostname

            uri = 'http://%s/search/?json=1&%s'%(hostname, urllib.urlencode(kw))
            site = urllib.urlopen(uri)

            if temp:
                self._named_playlists[temp] = []
                add = self._named_playlists[temp]
            else:
                self.playlist[:] = []
                add = self.playlist.append

        total = 0
        done = False

        while True:
            for n in xrange(50):
                line = site.readline()
                if not line:
                    break
                r = jload(line)
                total += r[4]
#                r[0] = 'http://%s%s'%(hostname, r[0])
                with self._lock:
                    add(r)
                self.signal_view('update_total', total)

            yield
            if not line:
                break

        if temp:
            self._total_length = total
        else:
            # reset song position
            with self._lock:
                self._cur_song_pos = 0
                self._tmp_total_length = total

    def _download_zic(self, uri, fname):
        if getattr(self, '_download_stream', None):
            self._download_stream.close()

        fd = file(fname, 'wb')
        self._download_stream = fd

        site = urllib.urlopen(uri)
        total = float(site.info().getheader('Content-Length'))
        total_length = float(self.selected['length'])
        achieved = 0

        data = site.read(2**17)
        fd.write(data) # read ~130k (a few seconds in general)
        achieved += len(data)
        self._running = True
        yield site.fileno()
#        web.debug('downloading %d'%achieved)

        try:
            BUF_SZ = 2**14 # 16k micro chunks
            while True:
                data = site.read(BUF_SZ)
                progress = total_length * (achieved / total)
#                self.signal_view('download_progress', progress)
                if not data:
                    break
                achieved += len(data)
                web.debug('downloading %s from %s (%f)'%(uri, self, progress))
                fd.write(data)
                yield
            fd.close()
        except Exception, e:
            web.debug('ERROR %s %s'%(repr(e), dir(e)))
        finally:
            if fd is self._download_stream:
                self._download_stream = None

    def signal_view(self, name, *args, **kw):
        web.debug('signaling %s %s %s'%(name, args, kw))
        for view in self.views:
            web.debug(' -> to view %s'%view)
            try:
                getattr(view, 'SIG_'+name)(*args, **kw)
            except:
                DEBUG()

    def _get_infos(self, l):
        try:
            return dict(album = l[1],
                        length = float(l[4]),
                        title = l[3],
                        __id__ = l[5],
                        artist = l[1])
        except:
            return None

    def _get_selected(self):
        pos = self._cur_song_pos
        if 0 <= pos <= len(self.playlist):
            return self._get_infos(self.playlist[pos])

    selected = property(_get_selected)

    @property
    def selected_uri(self):
        try:
            with self._lock:
                if self._cur_song_pos < 0:
                    raise Exception()
                txt =  'http://%s/search%s'%(self.hostname, self.playlist[self._cur_song_pos][0])
            return txt
        except:
            return None

    @property
    def infos(self):
        return dict(
                current = self._cur_song_pos,
                total = len(self.playlist),
                running = self._cur_song_pos >= 0,
                )

class webplayer:
    player = PlayerCtl()

    GET = web.autodelegate('REQ_')
    lastlog = []

    def REQ_main(self):
        af = SimpleSearchForm(True)
        af.fill()
        web.debug(self.player.selected, self.player.infos)
        yield render.player(
                af,
                self.player.selected,
                self.player.infos,
                )

    REQ_ = REQ_main # default page

    def REQ_search(self):
        it = None
        try:
            i = web.input('pattern')
            if i['pattern']:
                it = self.player.fetch_playlist(i.host, pattern=i.pattern, temp=i['tempname'].strip() or False)
            else:
                it = self.player.fetch_playlist(i.host, i['tempname'].strip() or False)
            it.next()

        except (IndexError, KeyError):
            it = None
        finally:
            yield web.redirect('/')

        if it:
            for x in it:
                yield

    def REQ_delete(self, position):
        # WARNING: not tested
        self.player.delete_entry(position)

    def REQ_move(self, pos1, pos2):
        self.player.move_entry(pos1, pos2)

    def REQ_append(self, name):
        self.player.playlist_change('append', name)

    def REQ_copy(self, name):
        self.player.playlist_change('copy', name)

    def REQ_infos(self):
        i = web.input()
        format = i.get('fmt', 'txt')

        if format == 'txt':
            yield 'current track: %s\n'%self.player._cur_song_pos
            yield 'current position: %s\n'%self.player.position
            yield 'playlist size: %s\n'%len(self.player.playlist)
            for k, v in self.player.selected.iteritems():
                yield '%s: %s\n'%(k, v)
        elif format == 'json':
            try:
                _d = self.player.selected.copy()
            except AttributeError:
                _d = dict()
            _d['pls_position'] = self.player._cur_song_pos
            _d['song_position'] = self.player.position
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
        return self.player.shuffle()

    def REQ_pause(self):
        return self.player.pause()

    def REQ_prev(self):
        return self.player.select(-1)

    def REQ_next(self):
        return self.player.select(1)

    def REQ_seek(self, val):
        val = val[1:]
        web.debug('VAL=%s'%val)
#        self.player.seek(int(val))

