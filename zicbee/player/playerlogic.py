from __future__ import with_statement
#
# Player Interface
#
# PROPERTIES
# selected: current track as dict(album, length, title, __id__, artist)
# infos: playlist status as dict(current, total, running)
# playlist: actual playlist (iterable)
#
# METHODS
# fetch_playlist(host, **uri_params): get playlist from a given pattern
# select(offset): changes the current song into the playlist
# shuffle(): shuffles the playlist
# pause(): pauses the player (toggle)
#

__all__ = ['PlayerCtl']

import gobject
import itertools
import random
import urllib
from cgi import escape
from gtk import ListStore
from zicbee.core.config import config
from zicbee.core.zutils import duration_tidy, jload, DEBUG
from zicbee.player.events import DelayedAction, IterableAction
from zicbee.player.soundplayer import SoundPlayer
from zicbee.core.debug import log
from threading import RLock

# XXX: TODO: rewrite using a metaclasse (util package ?)
def PlayerCtl(*args, **kw):
    if _PlayerCtl._playerctl_singleton_ is None:
        _PlayerCtl._playerctl_singleton_ = _PlayerCtl(*args, **kw)
    return _PlayerCtl._playerctl_singleton_

class _PlayerCtl(object):

    _playerctl_singleton_ = None

    def __init__(self):
        self._lock = RLock()
        self.player = SoundPlayer()
        self.views = []
        self._cur_song_pos = -1
        self._error_count = itertools.count()
        self._running = False
        self._position = None
        self._song_dl = None
        self.hostname = None

        IterableAction(self._tick_generator()).start(0.5, prio=gobject.PRIORITY_HIGH)

        self._play_timeout = DelayedAction(self._play_now, _delay=1)
        self.play = self._play_timeout.start
        self._seek_action = DelayedAction(self._seek_now)
        self._volume_action = DelayedAction(lambda v: self.player.volume(v), _delay=0.2)
        self.playlist = ListStore(str, str, str, str, int, int)

    def __repr__(self):
        return '<PlayerCtl %srunning - %s%s>'%(
                '' if self._running else 'not ',
                self._position,
                '- downloading' if self._song_dl else '')

    def __del__(self):
        self.player.quit()

    def _reset_stream(self):
        with self._lock:
            log.debug('reset stream...')
            if getattr(self, '_stream', False):
                try:
                    self._stream.flush()
                except ValueError:
                    pass
                self._stream.close()
            self._stream = file(config.streaming_file, 'wb')
            log.debug('new stream: %s', self._stream)

    def _new_error(self):
        with self._lock:
            log.debug('new error')
            cnt = self._error_count.next()
            if cnt >= 2:
                try:
                    self.select(1)
                except IndexError:
                    self.signal_view('status_changed', 'stopped')
                    self._running = False

    def _tick_generator(self):
#                or self._volume_action.running \
        while True:
            try:
                if not self.player.running \
                or self._play_timeout.running \
                or not self.playlist \
                or self._seek_action.running:
                    log.debug('no tick %s', self)
                    # Do nothing if paused or actualy changing the song
                    continue
                if self._running:
                    with self._lock:
                        log.debug('tick %s', self)
                        if self.player.finished: # End of track
                            raise Exception('player starved')
                        self._position = self.player.get_time_pos()
                        if self._position is None:
                            raise Exception('no position')
                        else:
                            self.signal_view('progress', float(self._position))
            except Exception, e:
                self._new_error()
            else:
                self._error_count = itertools.count()
            finally:
                yield True

    def signal_view(self, name, *args, **kw):
        log.info('signaling %s %s %s', name, args, kw)
        for view in self.views:
            log.info(' -> to view %s', view)
            try:
                getattr(view, 'SIG_'+name)(*args, **kw)
            except:
                DEBUG()

    def _play_now(self):
        selected = self.selected
        log.debug('play now %s on %s', selected, self)
        assert selected is not None

        def _download_zic(uri, fd):
            site = urllib.urlopen(uri)
            total = float(site.info().getheader('Content-Length'))
            total_length = float(selected['length'])
            achieved = 0

            data = site.read(2**17)
            fd.write(data) # read ~130k
            achieved += len(data)
            self._running = True
            yield site.fileno()

            try:
                BUF_SZ = 2**14 # 16k micro chunks
                while True:
                    data = site.read(BUF_SZ)
                    self.signal_view('download_progress', total_length * (achieved / total))
                    if not data:
                        break
                    achieved += len(data)
                    log.debug('downloading %s from %s', uri, self)
                    fd.write(data)
                    yield
                fd.close()
            finally:
                self._song_dl = None

        uri = self.selected_uri
        self.signal_view('song_uri', uri)
        idx = uri.index('id=')
        if self._song_dl:
            self._song_dl.stop()

        self._reset_stream()
        it = _download_zic(uri, self._stream)
#        self.signal_view('update_total', self._total_length)
        fd = it.next() # Start the download (try to not starve the soundcard)
        self._song_dl = IterableAction(it).start_on_fd(fd)
        try:
            self.player.loadfile(config.streaming_file)
        except:
            log.debug('not running anymore !!')
            self._running = False
            DEBUG()
            self.select(1)
        return False

    def _seek_now(self, val):
        with self._lock:
            log.info('seeking %s', val)
            self.player.seek(int(val), 2)

    def seek(self, val):
        with self._lock:
            self._seek_action.args = (val, )
            self._seek_action.start(0.2)

    def shuffle(self):
        with self._lock:
            log.info('shuffle')
            pos_list = range(len(self.playlist))
            random.shuffle(pos_list)
            self.playlist.reorder(pos_list)
            self._cur_song_pos = -1

    def pause(self):
        with self._lock:
            log.info('pause')
            self.player.pause()

    def select(self, sense):
        with self._lock:
            log.debug('SELECT @%s'% self)
            self._cur_song_pos += sense
            self._play_selected()

    def _play_selected(self, which=None):
        with self._lock:
            log.info('playing selected (%s)', which)
            info_list = ['', '']
            try:
                self._error_count = itertools.count()
                if which is not None:
                    self._cur_song_pos = which
                try:
                    m_d = self._get_selected()
                except IndexError:
                    return
                if m_d is None:
                    return

                self.signal_view('download_progress', 0)
                self.signal_view('progress', 0.0)
                if 'length' in m_d:
                    length = m_d['length']
                    self.signal_view('song_length', length)
                    info_list[1] = duration_tidy(length)
                else:
                    info_list[1] = ''

                self.play()

                title_artist = escape('%s\n%s'%(
                        m_d.get('title', 'Untitled'),
                        m_d.get('artist', 'Anonymous')
                        ))

                # FIXME: don't put XML in here
                if m_d.get('album'):
                    meta = '<span weight="bold">%s</span> - %s'%( title_artist, escape(m_d.get('album')) )
                else:
                    meta = '<span weight="bold">%s</span>'%(title_artist)

                info_list[0] = meta
                self.signal_view('update_infos', info_list)
                self.signal_view('select', self._cur_song_pos)
            except:
                DEBUG()
                self._running = False

    def fetch_playlist(self, hostname, **kw):
        """
        arguments:
            hostname: database host
            pattern: str must be passed
        """
        log.info('fetching playlist %s from %s', kw, hostname)
        if not hostname:
            hostname = '127.0.0.1'

        if ':' not in hostname:
            hostname += ':9090'
        self.hostname = hostname
        uri = 'http://%s/?json=1&%s'%(hostname, urllib.urlencode(kw))
        site = urllib.urlopen(uri)
        with self._lock:
            self.playlist.clear()
        add = self.playlist.append
        total = 0
        done = False
        try:
            while not done:
                for n in xrange(100):
                    line = site.readline()
                    if not line:
                        done = True
                        break
                    r = jload(line)
                    total += r[4]
                    with self._lock:
                        add(r)
                self.signal_view('update_total', total)
                yield True
        finally:
            self._total_length = total

    def _get_selected(self):
        pos = self._cur_song_pos
        if pos >= 0 and len(self.playlist) > 0:
            l = self.playlist[pos]
            return dict(album = l[1],
                        length = float(l[4]),
                        title = l[3],
                        __id__ = l[5],
                        artist = l[1])
        else:
            return None

    selected = property(_get_selected)

    selected_uri = property(lambda self: 'http://' + self.hostname + self.playlist[self._cur_song_pos][0] if self._cur_song_pos >= 0 else None)

    @property
    def infos(self):
        with self._lock:
            return dict(
                    current = self._cur_song_pos,
                    total = len(self.playlist),
                    running = self._running,
                    )

