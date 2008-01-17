#!/usr/bin/env python
# http://www.micahcarrick.com/12-24-2007/gtk-glade-tutorial-part-1.html

import sys
try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk
    import gtk.glade
except:
    sys.exit(1)

import mp
import gobject
import urllib
import random
import traceback

#from ..zshell import duration_tidy
from zicdb.zshell import duration_tidy

class PPlayer(object):

    def __init__(self):
        self.player = mp.MPlayer()
        self.playlist = []
        self.player.cur_song = -1
        gobject.timeout_add(1666, self._tick_generator().next)
        self._running = False
        self._paused = False
        self._position = None
        self._play_timeout = None

        self._wtree = gtk.glade.XML('pplayer.glade')

        self.win = self._wtree.get_widget('main_window')
        self.pat = self._wtree.get_widget('pattern_entry')
        self.info_lbl = self._wtree.get_widget('info_label')
        self.cursor = self._wtree.get_widget('cursor')
        self.hostname_w = self._wtree.get_widget('hostname')
        self.cursor.set_range(0, 100)

        handlers = dict( (prop, getattr(self, prop))
            for prop in dir(self)
            if prop[0] != '_' and callable(getattr(self, prop))
            )
        self._wtree.signal_autoconnect(handlers)
        self.win.connect('destroy', gtk.main_quit)
        self.win.show()

    def _tick_generator(self):
        while True:
            if self._paused or self._play_timeout is not None:
                yield True
                continue
            try:
                if self._running:
                    self._position = self.player.get_time_pos()
                    if self._position is None:
                        try:
                            self.play_next(None)
                        except IndexError:
                            self._running = False
                            self.info_lbl.set_text('Not Playing.')
                    else:
                        self.cursor.set_value(self._position)
            except Exception, e:
                traceback.print_exc()
            finally:
                yield True

    def absolute_seek(self, w, value):
        #     |      Seek to some place in the movie.
        #     |          0 is a relative seek of +/- <value> seconds (default).
        #     |          1 is a seek to <value> % in the movie.
        #     |          2 is a seek to an absolute position of <value> seconds.
        print "seek not supported right now :("
#        if 0 <= value <= 100:
#            print "VALUE", value
#            self.player.seek('%d'%value, 1)
#        diff = value - self._position
#        print "DIFF", diff

    def validate_pattern(self, w):
        params = {'pattern':self.pat.get_text()}
        hostname = self.hostname_w.get_text()
        if ':' not in hostname:
            hostname += ':9090'
        uri = 'http://%s/?json=1&%s'%(hostname, urllib.urlencode(params))
        try:
            from cjson import decode as jload
        except ImportError:
            from simplejson import loads as jload

        self.playlist = jload(urllib.urlopen(uri).read())
        self.player.cur_song = 0
        self._play_selected()
        self._running = True

    def shuffle_playlist(self, w):
        print "Mixing", len(self.playlist), "elements."
        random.shuffle(self.playlist)
        self.player.cur_song = -1

    def toggle_pause(self, w):
        self.player.pause()
        self._paused = not self._paused

    def play_prev(self, w):
        if self.player.cur_song <= 0:
            return
        self.player.cur_song -= 1
        if self.player.cur_song < 0:
            raise IndexError()
        self._play_selected()

    def play_next(self, w):
        self.player.cur_song += 1
        self._play_selected()

    def _play_now(self):
        self.player.loadfile(str(self.selected_uri))
        self._play_timeout = None
        return False

    def _play_selected(self):
        m_d = self.selected
        self.cursor.set_range(0, m_d['length'])
        if m_d.get('album'):
            meta = '%s\n%s - %s'%(
                    m_d.get('title', 'Untitled'),
                    m_d.get('artist', 'Anonymous'), m_d.get('album'))
        else:
            meta = '%s\n%s'%(
                    m_d.get('title', 'Untitled'),
                    m_d.get('artist', 'Anonymous'))
        if 'length' in m_d:
            meta += '\n%s'%duration_tidy(m_d['length'])

        self.info_lbl.set_text(meta)

        if self._play_timeout is not None:
            gobject.source_remove(self._play_timeout)

        self._play_timeout = gobject.timeout_add(600, self._play_now)


    selected = property(lambda self: self.playlist[self.player.cur_song][1] if self.player.cur_song != -1 else None)

    selected_uri = property(lambda self: self.playlist[self.player.cur_song][0] if self.player.cur_song != -1 else None)

if __name__ == '__main__':
    pp = PPlayer()
    gtk.main()
    pp.player.quit()

