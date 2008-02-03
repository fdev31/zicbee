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

import gobject
import itertools
import mp
import random
import traceback
import urllib
from cgi import escape
from pkg_resources import resource_filename
from zicdb.zutils import duration_tidy, jload

def DEBUG():
    traceback.print_stack()
    traceback.print_exc()

class DelayedAction(object):
    def __init__(self, fn, *args, **kw):
        self.fn = fn
        self.args = list(args)
        self.kw = kw
        self.running = None
        self._delay = 1

    def _run(self):
        try:
            self.fn(*self.args, **self.kw)
            self.running = None
        except Exception, e:
            DEBUG()
        return False

    def start(self, delay):
        """ start action after 'delay' seconds. """
        self.stop()
        self.running = gobject.timeout_add(int(delay*1000), self._run)

    def stop(self):
        if self.running is not None:
            gobject.source_remove(self.running)
        self.running = None

class IterableAction(object):
    def __init__(self, it):
        self.it = it
        self.running = None
        self._delay = 1

    def _run(self):
        if self.running is None:
            return False
        try:
            self.it.next()
        except StopIteration:
            self.running = None
        else:
            return True
        return False

    def start(self, delay=0):
        """ start action after 'delay' seconds. """
        self.stop()
        self.running = gobject.timeout_add(int(delay*1000), self._run)

    def stop(self):
        if self.running is not None:
            gobject.source_remove(self.running)
        self.running = None

class PPlayer(object):

    def __init__(self):
        self.player = mp.MPlayer()
        self._error_count = itertools.count()
        self._old_size = (4, 4)
        self._cur_song_pos = -1
        self._info_list = ['', '']
        gobject.timeout_add(1666, self._tick_generator().next)
        self._running = False
        self._paused = False
        self._position = None
        self._actual_infos = ''
        self._play_timeout = DelayedAction(self._play_now)
        self._seek_action = DelayedAction(self._seek_now)

        self._wtree = gtk.glade.XML(resource_filename('zplayer', 'pplayer.glade'))

        self.win = self._wtree.get_widget('main_window')
        self.list_w = self._wtree.get_widget('songlist_tv')
        self.list_store = gtk.ListStore(str, str, str, str, int, int)
        self.list_w.set_model(self.list_store)
        for i, name in enumerate(('Artist', 'Album', 'Title')):
            col = gtk.TreeViewColumn(name, gtk.CellRendererText(), text=i+1)
            col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            col.set_fixed_width(120)
            col.set_resizable(True)
            self.list_w.append_column( col )

        self.pat = self._wtree.get_widget('pattern_entry')
        self.pat.grab_focus()
        self.info_lbl = self._wtree.get_widget('info_label')
        # position
        self.cursor = self._wtree.get_widget('cursor')
        self.cursor.set_range(0, 100)
        # uri
        self._song_uri = self._wtree.get_widget('song_uri')
        # volume
        self.volume_w = self._wtree.get_widget('volume')
        self.volume_w.set_value(100)
        self._volume_action = DelayedAction(lambda v: self.player.volume(v, 1), 0.5)

        self.hostname_w = self._wtree.get_widget('hostname')
        if len(sys.argv) == 2:
            self.hostname_w.set_text(sys.argv[1])

        self.status_w = self._wtree.get_widget('statusbar')
        self.status_w_ctx = self.status_w.get_context_id('player')
        self._push_status('idle')

        handlers = dict( (prop, getattr(self, prop))
            for prop in dir(self)
            if prop[0] != '_' and callable(getattr(self, prop))
            )
        self._wtree.signal_autoconnect(handlers)
        self.win.connect('destroy', gtk.main_quit)
        self.win.set_geometry_hints(self.win, 386, 176)
        self.win.show()
        self._old_size = self.win.get_size()

    def _push_status(self, txt):
        self.status_w.push(self.status_w_ctx, txt)

    def _pop_status(self):
        self.status_w.pop(self.status_w_ctx)

    def _new_error(self):
        cnt = self._error_count.next()
        if cnt >= 2:
            try:
                self.play_next(None)
            except IndexError:
                self._running = False
                self.info_lbl.set_text('Not Playing.')

    def _tick_generator(self):
        while True:
            try:
                if self._paused \
                or self._play_timeout.running \
                or self._volume_action.running \
                or not self.list_store \
                or self._seek_action.running:
                    # Do nothing if paused or actualy changing the song
                    yield True
                    continue
                if self._running:
                    self._position = self.player.get_time_pos()
                    if self._position is None:
                        self.cursor.set_value(self.selected['length'])
                        raise Exception()
                    else:
                        self.cursor.set_value(float(self._position))
                        cur_pos = duration_tidy(self._position)
                        if self._info_list[1]:
                            cut_vals = self._info_list[1].split('/')
                            cur_pos = '%s / %s'%(cur_pos, cut_vals[-1].strip())
                        self._info_list[1] = cur_pos
                        self._update_infos()
            except Exception, e:
                self._new_error()
                DEBUG()
            else:
                self._error_count = itertools.count()
            finally:
                yield True

    def change_volume(self, w, value):
        value *= 100
        if not (0 <= value <= 100):
            return False
        self._volume_action.args[0] = int(value)
        self._volume_action.start(0.1)

    def _seek_now(self, val):
        if 0 <= val <= 100:
            self.player.seek('%d'%val, 1)

    def absolute_seek(self, w, type, val):
        #     |      Seek to some place in the movie.
        #     |          0 is a relative seek of +/- <value> seconds (default).
        #     |          1 is a seek to <value> % in the movie.
        #     |          2 is a seek to an absolute position of <value> seconds.
        self._seek_action.args = (val,)
        self._seek_action.start(0.2)

    hostname = property(lambda self: self.hostname_w.get_text() if ':' in self.hostname_w.get_text() else self.hostname_w.get_text()+':9090')

    def validate_pattern(self, w):
        params = {'pattern':self.pat.get_text()}
        hostname = self.hostname
        uri = 'http://%s/?json=1&%s'%(hostname, urllib.urlencode(params))

        self._pop_status()
        self._paused = True
        try:
            def _fill_it():
                site = urllib.urlopen(uri)
                self.list_store.clear()
                yield
                add = self.list_store.append
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
                        yield True
                except Exception, e:
                    DEBUG()
                finally:
                    self._actual_infos = duration_tidy(total)
                    self._paused = False
            IterableAction(_fill_it()).start(0.1)
        except:
            DEBUG()
            self._push_status('Connect to %s failed'%hostname)
        else:
            self._push_status('Connected' if len(self.list_store) else 'Empty')
        self._cur_song_pos = 0
        try:
            DelayedAction(self._play_selected).start(0.4)
        except:
            return
        else:
            self._running = True

    def shuffle_playlist(self, w):
        print "Mixing", len(self.list_store), "elements."
        pos_list = range(len(self.list_store))
        random.shuffle(pos_list)
        self.list_store.reorder(pos_list)
        self._cur_song_pos = -1

    def toggle_pause(self, w):
        self.player.pause()
        self._paused = not self._paused

    def play_prev(self, w):
        if self._cur_song_pos <= 0:
            return
        self._cur_song_pos -= 1
        if self._cur_song_pos < 0:
            raise IndexError()
        try:
            self._play_selected()
        except:
            pass
        else:
            if not self._play_timeout.running:
                self._push_status('seeking...')

    def play_next(self, *args):
        if self._cur_song_pos > len(self.list_store):
            return
        self._cur_song_pos += 1
        try:
            self._play_selected()
        except:
            pass
        else:
            if not self._play_timeout.running:
                self._push_status('seeking...')

    def _play_now(self):
        self._pop_status()
        uri = self.selected_uri
        self._song_uri.set_text(uri)
        idx = uri.index('id=')
        self._push_status(self._actual_infos + ' over %d songs'%len(self.list_store))
        self.player.loadfile(str(uri))
        def _set_volume():
            vol = self.player.prop_volume
            if vol:
                self.volume_w.set_value(float(vol)/100.0)
        DelayedAction(_set_volume).start(0.5)
        return False

    def toggle_playlist(self, expander):
        DelayedAction(self.win.resize, *self._old_size).start(0.3)
        self._old_size = self.win.get_size()

    def force_change_song(self, treeview, path, treeview_col):
        self._cur_song_pos = path[0]
        self._play_selected()

    def _play_selected(self):
        self._error_count = itertools.count()
        try:
            m_d = self.selected
        except IndexError:
            return

        self.cursor.set_value(0.0)
        if 'length' in m_d:
            length = m_d['length']
            self.cursor.set_range(0, length)
            self.cursor.set_fill_level(length)
            self._info_list[1] = duration_tidy(length)
        else:
            self._info_list[1] = ''
        self._play_timeout.start(1)

        title_artist = escape('%s\n%s'%(
                m_d.get('title', 'Untitled'),
                m_d.get('artist', 'Anonymous')
                ))

        if m_d.get('album'):
            meta = '<span weight="bold">%s</span> - %s'%( title_artist, escape(m_d.get('album')) )
        else:
            meta = '<span weight="bold">%s</span>'%(title_artist)

        self._info_list[0] = meta

        self._update_infos()
        self.list_w.set_cursor( (self._cur_song_pos, 0) )

    def _update_infos(self):
        self.info_lbl.set_markup('\n'.join(self._info_list))

    def _get_selected(self):
        if self._cur_song_pos >= 0 and len(self.list_store) > 0:
            l = self.list_store[self._cur_song_pos]
            return dict(album = l[1],
                        length = float(l[4]),
                        title = l[3],
                        __id__ = l[5],
                        artist = l[1])
        else:
            return None

    selected = property(_get_selected)

    selected_uri = property(lambda self: 'http://' + self.hostname + self.list_store[self._cur_song_pos][0] if self._cur_song_pos >= 0 else None)

def main():
    pp = PPlayer()
    gtk.main()
    pp.player.quit()

if __name__ == '__main__':
    main()
