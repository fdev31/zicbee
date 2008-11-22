# -*- coding: utf-8 -*-

# ZicDBBar (from SearchBar) for quodlibet 2.0
# - Copy this file to quodlibet/browsers/zicdb.py
# - Change ZICDB_HOST
# - Change your ~/.quodlibet/config to match zicdb rating:
# [settings]
# ratings = 10


import os
import random

from time import time
import gtk
import gobject
import urllib
from zicbee.player.events import DelayedAction, IterableAction
from zicbee.core.zutils import compact_int, jdump, jload, parse_line

from quodlibet import config
from quodlibet import const
from quodlibet import qltk

from quodlibet.browsers.search import EmptyBar, Limit
from quodlibet.browsers.iradio import ParseM3U, IRFile
from quodlibet.formats.remote import RemoteFile
from quodlibet.parse import Query
from quodlibet.qltk.cbes import ComboBoxEntrySave
from quodlibet.qltk.completion import LibraryTagCompletion
from quodlibet.qltk.songlist import SongList
from quodlibet.qltk.x import Tooltips
from logging import getLogger
log = getLogger(__name__)

QUERIES = os.path.join(const.USERDIR, "lists", "zqueries")
ZICDB_HOST = 'chenapan:9090'

class ZDBFile(RemoteFile):
    multisong = True
    can_add = False

    format = "Radio Station"

    __CAN_CHANGE = "title artist grouping".split()

    def __init__(self, values):
        if 'http' in values[0]:
            RemoteFile.__init__(self, values[0])
            RemoteFile.__setitem__(self, "artist", values[1])
            RemoteFile.__setitem__(self, "album", values[2])
            RemoteFile.__setitem__(self, "title", values[3])
            RemoteFile.__setitem__(self, "~#length", values[4])
            RemoteFile.__setitem__(self, "~#rating", values[5]/10.0 if values[5] else 0.5)
        else:
            RemoteFile.__init__(self, values)
        self._set_rating_action = DelayedAction(self._set_rating)

    def _set_rating(self):
        uri = self['~uri']
        score = self['~#rating']
        score = int(score*10) #quodlibet uses 1.0 as max, zicdb uses 10
        sid = (uri.rsplit('=', 1)[1])
        rate_uri = uri[:uri.index('/db/')+3] + '/rate/%s/%s'%(sid, score)
        urllib.urlopen(rate_uri)

    def __setitem__(self, key, value):
        if key == "~#rating":
            #print '~ new_rate=%s old_rate=%s'%(value, self[key])
            if key not in self or value != self[key]:
                self._set_rating_action.start(0.2)
        RemoteFile.__setitem__(self, key, value)

    def write(self): pass
    def can_change(self, k=None):
        if k is None: return self.__CAN_CHANGE
        else: return k in self.__CAN_CHANGE

# Like EmptyBar, but the user can also enter a query manually. This
# is QL's default browser. EmptyBar handles all the GObject stuff.
class ZicDBBar(EmptyBar):

    name = _("ZicDB Search")
    accelerated_name = _("_ZicDB Search")
    priority = 1
    in_menu = True

    def __init__(self, library, player):
        super(ZicDBBar, self).__init__(library, player)

        self.__save = bool(player)
        self.set_spacing(12)

        self.__limit = Limit()
        self.pack_start(self.__limit, expand=False)

        hb2 = gtk.HBox(spacing=3)
        l = gtk.Label(_("_Search:"))
        l.connect('mnemonic-activate', self.__mnemonic_activate)
        tips = Tooltips(self)
        combo = ComboBoxEntrySave(QUERIES, model="searchbar", count=8)
        combo.child.set_completion(LibraryTagCompletion(library.librarian))
        l.set_mnemonic_widget(combo.child)
        l.set_use_underline(True)
        clear = qltk.ClearButton(self, tips)

        search = gtk.Button()
        hb = gtk.HBox(spacing=3)
        hb.pack_start(gtk.image_new_from_stock(
            gtk.STOCK_FIND, gtk.ICON_SIZE_MENU), expand=False)
        hb.pack_start(gtk.Label(_("Search")))
        search.add(hb)
        tips.set_tip(search, _("Search your library"))
        search.connect_object('clicked', self.__text_parse, combo.child)
        combo.child.connect('activate', self.__text_parse)
        combo.child.connect('changed', self.__test_filter)
        combo.child.connect('realize', lambda w: w.grab_focus())
        combo.child.connect('populate-popup', self.__menu, self.__limit)
        hb2.pack_start(l, expand=False)
        hb3 = gtk.HBox()
        hb3.pack_start(combo)
        hb3.pack_start(clear, expand=False)
        hb3.pack_start(search, expand=False)
        hb2.pack_start(hb3)
        self.pack_start(hb2)
        self.show_all()
        self.__combo = combo
        self.__limit.hide()

    def __mnemonic_activate(self, label, group_cycling):
        # If our mnemonic widget already has the focus, switch to
        # the song list instead. (#254)
        widget = label.get_mnemonic_widget()
        if widget.is_focus():
            qltk.get_top_parent(widget).songlist.grab_focus()
            return True

    def __menu(self, entry, menu, hb):
        sep = gtk.SeparatorMenuItem()
        menu.prepend(sep)
        item = gtk.CheckMenuItem(_("_Limit Results"))
        menu.prepend(item)
        item.set_active(hb.get_property('visible'))
        item.connect('toggled', self.__showhide_limit, hb)
        item.show(); sep.show()

    def __showhide_limit(self, button, hb):
        if button.get_active(): hb.show()
        else: hb.hide()

    def activate(self):
        # 'artist album title length score tags'
        start = time()
        if self._text is not None:
            log.info('START: %s self._text=%s', start, self._text)
            uri = 'http://%s/db/?json=1&%s'%(ZICDB_HOST, urllib.urlencode({'pattern': self._text}))
            log.debug('uri=%s', uri)
            try:
                site = urllib.urlopen(uri)
            except Exception, e:
                log.error('Connect to %s failed: %s', ZICDB_HOST, e)
                yield False
            log.info('site=%s %ss', site, time()-start)
            songs = []
            m3u = []
            while True:
                for n in xrange(50):
                    line = site.readline()
                    if not line:
                        break
                    #m3u.append(line)
                    track = jload(line)
                    songs.append(ZDBFile(track))
                log.info('loop %ss', time()-start)
                yield
                if not line:
                    break
            #songs = ParseM3U(m3u)
            if songs:
                self.__combo.prepend_text(self._text)
                log.debug('combo done')
                if self.__limit.get_property('visible'):
                    songs = self.__limit.limit(songs)
                self.emit('songs-selected', songs, None)
                if self.__save: self.save()
                self.__combo.write(QUERIES)
            log.info('END %ss for %s songs', time()-start, len(songs))

    def set_text(self, text):
        log.debug('text=%s',text)
        self.__combo.child.set_text(text)
        if isinstance(text, str): text = text.decode('utf-8')
        self._text = text

    def __text_parse(self, entry):
        log.debug('entry=%s',entry)
        text = entry.get_text()
        if Query.is_parsable(text):
            log.debug('is parsable=')
            self._text = text.decode('utf-8')
            gobject.timeout_add(1000, self.activate)
            it = self.activate()
            it.next()
            IterableAction(it).start(0.001, prio=gobject.PRIORITY_DEFAULT_IDLE)
            #self.activate()

    def __test_filter(self, textbox):
        if not config.getboolean('browsers', 'color'):
            textbox.modify_text(gtk.STATE_NORMAL, None)
            return
        text = textbox.get_text().decode('utf-8')
        log.debug('text=%s',text)
        color = Query.is_valid_color(text)
        if color and textbox.get_property('sensitive'):
            textbox.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse(color))

browsers = [ZicDBBar]
