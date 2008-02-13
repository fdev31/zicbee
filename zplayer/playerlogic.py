__all__ = ['PlayerCtl']
import gobject
import itertools
import random
import urllib
from .events import DelayedAction, IterableAction
from .soundplayer import SoundPlayer
from cgi import escape
from gtk import ListStore
from zicdb.zutils import duration_tidy, jload, DEBUG

class PlayerCtl(object):
    def __init__(self):
        self.player = SoundPlayer('alsa')
        self.views = []
        self._cur_song_pos = -1
        self._error_count = itertools.count()
        self._running = False
        self._position = None
        self._song_dl = None
        self.hostname = None

        IterableAction(self._tick_generator()).start(0.5, prio=gobject.PRIORITY_HIGH_IDLE)

        self._play_timeout = DelayedAction(self._play_now)
        self._seek_action = DelayedAction(self._seek_now)
        self._volume_action = DelayedAction(lambda v: self.player.volume(v), 0.5)
        self.playlist = ListStore(str, str, str, str, int, int)

    def __del__(self):
        self.player.quit()

    def _new_error(self):
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
                    # Do nothing if paused or actualy changing the song
                    continue
                if self._running:
                    self._position = self.player.get_time_pos()
                    if self._position is None:
                        raise Exception()
                    else:
                        self.signal_view('progress', float(self._position))
            except Exception, e:
                self._new_error()
            else:
                self._error_count = itertools.count()
            finally:
                yield True

    def signal_view(self, name, *args, **kw):
        for view in self.views:
            try:
                getattr(view, 'SIG_'+name)(*args, **kw)
            except:
                DEBUG()

    def _play_now(self, selected):

        def _download_zic(uri, fname):
            site = urllib.urlopen(uri)
            fd = file(fname, 'w')
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
        it = _download_zic(uri, '/tmp/zsong')
#        self.signal_view('update_total', self._total_length)
        fd = it.next() # Start the download (try to not starve the soundcard)
        self._song_dl = IterableAction(it).start_on_fd(fd)
        self.player.loadfile('/tmp/zsong')
        return False

    def _seek_now(self, val):
        self.player.seek(int(val), 2)

    def seek(self, val):
        self._seek_action.args = (val, )
        self._seek_action.start(0.2)

    def shuffle(self):
        print "Mixing", len(self.playlist), "elements."
        pos_list = range(len(self.playlist))
        random.shuffle(pos_list)
        self.playlist.reorder(pos_list)
        self._cur_song_pos = -1

    def pause(self):
        self.player.pause()

    def select(self, sense):
        self._cur_song_pos += sense
        self._play_selected()

    def _play_selected(self, which=None):
        info_list = ['', '']
        try:
            self._error_count = itertools.count()
            if which is not None:
                self._cur_song_pos = which
            try:
                m_d = self._get_selected()
            except IndexError:
                return

            self.signal_view('download_progress', 0)
            self.signal_view('progress', 0.0)
            if 'length' in m_d:
                length = m_d['length']
                self.signal_view('song_length', length)
                info_list[1] = duration_tidy(length)
            else:
                info_list[1] = ''

            self._play_timeout.args = [m_d]
            self._play_timeout.start(1)

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
        self.hostname = hostname
        uri = 'http://%s/?json=1&%s'%(hostname, urllib.urlencode(kw))
        site = urllib.urlopen(uri)
        self.playlist.clear()
        yield
        add = self.playlist.append
        total = 0
        try:
            done = False
            while not done:
                for n in xrange(100):
                    line = site.readline()
                    if not line:
                        done = True
                        break
                    r = jload(line)
                    total += r[4]
                    add(r)
                self.signal_view('update_total', total)
                yield True
        except Exception, e:
            DEBUG()
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


