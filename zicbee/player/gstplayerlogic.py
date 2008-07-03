import gobject
import itertools
import random
import urllib
from cgi import escape
from gtk import ListStore
from zicbee.core.config import config
from zicbee.core.zutils import duration_tidy, jload, DEBUG
from zicbee.player.events import DelayedAction, IterableAction
#from zicbee.player.soundplayer import SoundPlayer
from zicbee.core.debug import log
from threading import RLock
import pygst
pygst.require('0.10')
import gst

class PlayerCtl(object):
    def __init__(self):
        self.player = gst.element_factory_make("playbin", "my-playbin")
        fakesink = gst.element_factory_make("fakesink", "my-fakesink")
        self.player.set_property("video-sink", fakesink)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        self.views = []
        self._cur_song_pos = -1
        self._error_count = itertools.count()
        self._running = False
        self._position = None
        self._song_dl = None
        self.hostname = None
        self.playlist = ListStore(str, str, str, str, int, int)

    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
            self.select(1)

        elif t == gst.MESSAGE_ERROR:
            self.player.set_state(gst.STATE_NULL)
            err, debug = message.parse_error()
            print "Error: %s" % err, debug

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
                    add(r)
                self.signal_view('update_total', total)
                yield True
        finally:
            self._total_length = total

    def play(self):
        self.player.set_property('uri', self.selected_uri)
        self.player.set_state(gst.STATE_PLAYING)

    def select(self, offset):
        self._cur_song_pos += sense
        self.play()

    def shuffle(self):
        pos_list = range(len(self.playlist))
        random.shuffle(pos_list)
        self.playlist.reorder(pos_list)
        self._cur_song_pos = -1

    def pause(self):
        pass

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

