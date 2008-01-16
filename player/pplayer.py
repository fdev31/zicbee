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

class PPlayer(object):

    def __init__(self):
        self.player = mp.MPlayer()
        self.playlist = []
        self.player.cur_song = -1
        gobject.timeout_add(1666, self._tick_generator().next)
        self._running = False
        self._paused = False

        self._wtree = gtk.glade.XML('pplayer.glade')

        self.win = self._wtree.get_widget('main_window')
        self.pat = self._wtree.get_widget('pattern_entry')
        self.info_lbl = self._wtree.get_widget('info_label')
        self.cursor = self._wtree.get_widget('cursor')
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
            if self._paused:
                yield True
                continue
            try:
                if self._running:
                    pos = self.player.get_time_pos()
                    if pos is None:
                        try:
                            self.play_next(None)
                        except IndexError:
                            self._running = False
                            self.info_lbl.set_text('Not Playing.')
                    else:
                        meta = '\n'.join('%s: %s'%(k, v) for k, v in self.player.meta.iteritems())
                        if not meta:
                            song = urllib.unquote_plus(self.playlist[self.player.cur_song])
                            meta = song.rsplit('/', 1)[-1]
                        self.info_lbl.set_text(meta)
                        total = self.player.get_time_length()
#                        print pos, total
                        if total and total > 0:
                            pos = total / pos
                        else:
                            pos %= 100
#                        print repr(pos)
                        self.cursor.set_value(float(pos))
            except Exception, e:
                traceback.print_exc()
            finally:
                yield True

    def validate_pattern(self, w):
        params = {'pattern':w.get_text()}
        uri = 'http://gunter.static.wyplay.int:9090/?plain=1&' + urllib.urlencode(params)
        self.playlist = [l.strip() for l in urllib.urlopen(uri).readlines()]
        random.shuffle(self.playlist)
        self.player.cur_song = 0
        self._play_selected()
        self._running = True


    def toggle_pause(self, w):
        self.player.pause()
        self._paused = not self._paused

    def play_prev(self, w):
        self.player.cur_song -= 1
        if self.player.cur_song < 0:
            raise IndexError()
        self._play_selected()

    def play_next(self, w):
        self.player.cur_song += 1
        self._play_selected()

    def _play_selected(self):
        self.player.loadfile(self.selected)

    selected = property(lambda self: self.playlist[self.player.cur_song] if self.player.cur_song != -1 else None)

if __name__ == '__main__':
    pp = PPlayer()
    gtk.main()
    pp.player.quit()

