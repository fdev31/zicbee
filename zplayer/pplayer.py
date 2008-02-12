#!/usr/bin/env python

try:
    import pygtk
    pygtk.require("2.0")
finally:
    try:
        import gtk
        import gtk.glade
    except:
        raise SystemExit("Can't load gtk+")

import gobject
import sys
from .events import DelayedAction, IterableAction
from .playerlogic import PlayerCtl
from pkg_resources import resource_filename
from zicdb.zutils import duration_tidy, DEBUG

class PPlayer(object):

    def __init__(self, player_ctl):
        self.player_ctl = player_ctl

        self._old_size = (4, 4)
        self._actual_infos = ''

        self._wtree = gtk.glade.XML(resource_filename('zplayer', 'pplayer.glade'))

        self.win = self._wtree.get_widget('main_window')
        self.list_w = self._wtree.get_widget('songlist_tv')

        self.list_w.set_model(self.player_ctl.playlist)
        for i, name in enumerate(('Artist', 'Album', 'Title')):
            col = gtk.TreeViewColumn(name, gtk.CellRendererText(), text=i+1)
            col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            col.set_fixed_width(120)
            col.set_resizable(True)
            self.list_w.append_column( col )

        self.pat = self._wtree.get_widget('pattern_entry')
        self.pat.grab_focus()
        self.info_lbl = self._wtree.get_widget('info_label')
        self.time_lbl = self._wtree.get_widget('elapsed_time')
        # position
        self.cursor = self._wtree.get_widget('cursor')
        self.cursor.set_range(0, 100)
        self.cursor.set_show_fill_level(True)
        self.cursor.set_fill_level(0)
        # uri
        self._song_uri_lbl = self._wtree.get_widget('song_uri')
        # volume
#        self.volume_w = self._wtree.get_widget('volume')
#        self.volume_w.set_value(100)

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
        if txt is None:
            self._pop_status()
        else:
            self.status_w.push(self.status_w_ctx, txt)

    def _pop_status(self):
        self.status_w.pop(self.status_w_ctx)

#    def change_volume(self, w, value):
#        value *= 100
#        if not (0 <= value <= 100):
#            return False
#        self._volume_action.args[0] = int(value)
#        self._volume_action.start(0.1)

    def absolute_seek(self, w, type, val):
        #     |      Seek to some place in the movie.
        #     |          0 is a relative seek of +/- <value> seconds (default).
        #     |          1 is a seek to <value> % in the movie.
        #     |          2 is a seek to an absolute position of <value> seconds.
        self.player_ctl.seek(val)

    hostname = property(lambda self: self.hostname_w.get_text() if ':' in self.hostname_w.get_text() else self.hostname_w.get_text()+':9090')

    def validate_pattern(self, w):
        try:
            it = self.player_ctl.fetch_playlist(self.hostname, pattern=self.pat.get_text())
            it.next()
            IterableAction(it).start(0.001, prio=gobject.PRIORITY_DEFAULT_IDLE)
        except:
            DEBUG()
            self._pop_status()
            self._push_status('Connection to %s failed'%self.hostname)
        else:
            self._pop_status()
            self._push_status('Connected' if len(self.player_ctl.playlist) else 'Empty')

        DelayedAction(self.player_ctl._play_selected, 0).start(0.5)

    def shuffle_playlist(self, w):
        self.player_ctl.shuffle()

    def toggle_pause(self, w):
        self.player_ctl.pause()

    def play_prev(self, w):
        try:
            self.player_ctl.select(-1)
        except IndexError:
            pass
        else:
            self._push_status('seeking...')

    def play_next(self, *args):
        try:
            self.player_ctl.select(1)
        except IndexError:
            pass
        else:
            self._push_status('seeking...')

    def toggle_playlist(self, expander):
        DelayedAction(self.win.resize, *self._old_size).start(0.3)
        self._old_size = self.win.get_size()

    def force_change_song(self, treeview, path, treeview_col):
        self.player_ctl._play_selected(path[0])

    def SIG_update_infos(self, infos):
        # XXX: refactor this
        self.info_lbl.set_markup('\n'.join(infos))

    def SIG_update_total(self, total):
        self._actual_infos = duration_tidy(total)
        self._pop_status()
        self._push_status('%d songs | %s'%(len(self.player_ctl.playlist), self._actual_infos))

    def SIG_status_changed(self, status):
        if status == 'stopped':
            self.info_lbl.set_text('Not Playing.')

    def SIG_progress(self, val):
        self.cursor.set_value(val)
        self.time_lbl.set_text(duration_tidy(val))

    def SIG_download_progress(self, val):
        self.cursor.set_fill_level(val)

    def SIG_song_length(self, length):
        self.cursor.set_range(0, length)

    def SIG_song_uri(self, uri):
        self._song_uri_lbl.set_text(uri)

    def SIG_select(self, pos):
        self.list_w.set_cursor( (pos, 0) )


def main():
    player_ctl = PlayerCtl()
    pp = PPlayer(player_ctl)
    player_ctl.views.append(pp)
    gtk.main()
    player_ctl.player.quit()

if __name__ == '__main__':
    main()
