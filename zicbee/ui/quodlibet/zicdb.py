# -*- coding: utf-8 -*-

# ZicDBBar (from SearchBar) for quodlibet 2.0
# - Copy this file to quodlibet/browsers/zicdb.py
# - Change DEFAULT_ZICDB_HOST
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
from zicbee.core.debug import log

from quodlibet import config
from quodlibet import const
from quodlibet import qltk

from quodlibet.browsers.search import EmptyBar, Limit
#from quodlibet.browsers.iradio import ParseM3U
from quodlibet.formats.remote import RemoteFile
from quodlibet.parse import Query
from quodlibet.qltk.cbes import ComboBoxEntrySave
from quodlibet.qltk.completion import LibraryTagCompletion
from quodlibet.qltk.songlist import SongList
from quodlibet.qltk.x import Tooltips

ZDBQUERIES = os.path.join(const.USERDIR, "lists", "zdbqueries")
ZDBHOSTS = os.path.join(const.USERDIR, "lists", "zdbhosts")
DEFAULT_ZICDB_HOST = 'chenapan:9090'

class ZDBRater(list):
    """
    Rates several track in one request.
    Uses 1 Rater for each zdb host
    """
    def __init__(self, host):
        list.__init__(self)
        self._host = host
        self._set_rating_action = DelayedAction(self._set_rating)

    def _set_rating(self):
        uri =''
        count = 0
        while True:
            try:
                (song, rating) = self.pop(0)
            except IndexError:
                break
            rating = int(rating*10) #quodlibet uses 1.0 as max, zicdb uses 10
            uri += '%s=%s,'%(song, rating)
            count += 1
            if count >= 50:
                break
        rate_uri = '%s/db/multirate/%s'%(self._host, uri)
        log.debug('rate_uri=%s', rate_uri)
        urllib.urlopen(rate_uri)
        if len(self):
            self._set_rating_action.start(1)

    def append(self, song_rating):
        list.append(self, song_rating)
        self._set_rating_action.start(1)


class ZDBFile(RemoteFile):
    multisong = True
    can_add = False

    format = "ZicDB file"
    raters = dict()
    dirty_tags = ('private-id3v2-frame',)

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
        self._host = self['~uri'].split('/db/')[0]
        self._sid = self['~uri'].rsplit('=', 1)[1]
        if not self._host in ZDBFile.raters:
            log.debug('create new Rater for %s', self._host)
            ZDBFile.raters[self._host] = ZDBRater(self._host)

    def __setitem__(self, key, value):
        if key == "~#rating":
            log.debug('rate=: %s -> %s',self[key], value)
            if key not in self or value != self[key]:
                ZDBFile.raters[self._host].append((self._sid, value))
        if key not in self.dirty_tags:
            RemoteFile.__setitem__(self, key, value)

    def write(self): pass
    def can_change(self, k=None):
        if k is None: return self.__CAN_CHANGE
        else: return k in self.__CAN_CHANGE

class ZicDBBar(EmptyBar):

    name = _("ZicDB Search")
    accelerated_name = _("_ZicDB Search")
    priority = 1
    in_menu = True

    def __init__(self, library, player):
        super(ZicDBBar, self).__init__(library, player)
        self._host = None
        self.__save = bool(player)
        self.set_spacing(12)

        hb2 = gtk.HBox(spacing=3)

        self.__limit = Limit()
        self.pack_start(self.__limit, expand=False)


        l = gtk.Label(_("_Search:"))
        l.connect('mnemonic-activate', self.__mnemonic_activate)
        tips = Tooltips(self)
        combo = ComboBoxEntrySave(ZDBQUERIES, model="searchbar", count=20)
        combo.child.set_completion(LibraryTagCompletion(library.librarian))
        l.set_mnemonic_widget(combo.child)
        l.set_use_underline(True)

        host_l = gtk.Label(_("_Host:"))
        host_l.set_use_underline(True)
        host_combo = ComboBoxEntrySave(ZDBHOSTS, model="searchbar", count=10)

        clear = qltk.ClearButton(self, tips)

        search = gtk.Button()
        hb = gtk.HBox(spacing=3)
        hb.pack_start(gtk.image_new_from_stock(
            gtk.STOCK_FIND, gtk.ICON_SIZE_MENU), expand=False)
        hb.pack_start(gtk.Label(_("Search")))
        search.add(hb)
        tips.set_tip(search, _("Search your library"))
        search.connect_object('clicked', self.__text_parse, combo.child)
        host_combo.child.connect_object('activate', self.__text_parse, combo.child)
        host_combo.child.connect('changed', self.__get_host)
        host_combo.child.connect('realize', lambda w: w.grab_focus())
        host_combo.child.connect('populate-popup', self.__menu, self.__limit)
        combo.child.connect('activate', self.__text_parse)
        combo.child.connect('changed', self.__test_filter)
        combo.child.connect('realize', lambda w: w.grab_focus())
        combo.child.connect('populate-popup', self.__menu, self.__limit)
        hb2.pack_start(host_l, expand=False)
        hb2.pack_start(host_combo, expand=False)
        hb2.pack_start(l, expand=False)
        hb3 = gtk.HBox()
        hb3.pack_start(combo)
        hb3.pack_start(clear, expand=False)
        hb3.pack_start(search, expand=False)
        hb2.pack_start(hb3)
        self.pack_start(hb2)
        self.show_all()
        self.__combo = combo
        self.__host_combo = host_combo
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
        if self._text is not None:
            self._host = self._host or DEFAULT_ZICDB_HOST
            start = time()
            log.info('START: %s self._text=%s', start, self._text)
            uri = 'http://%s/db/?json=1&%s'%(self._host, urllib.urlencode({'pattern': self._text}))
            log.info('uri=%s', uri)
            try:
                site = urllib.urlopen(uri)
            except Exception, e:
                log.error('Connect to %s failed: %s', self._host, e)
                yield False
            else:
                log.info('site=%s %ss', site, time()-start)
                songs = []
                m3u = []
                while True:
                    #lstart = time()
                    for n in xrange(50):
                        line = site.readline()
                        if not line:
                            break
                        try:
                            track = jload(line)
                            songs.append(ZDBFile(track))
                        except Exception, e:
                            log.error('Error while fetching song %s: %s', line, e)
                    #log.debug('loop %ss', time()-lstart)
                    yield
                    if not line:
                        break
                log.debug('got songs from server: %ss for %s songs', time()-start, len(songs))
                if songs:
                    self.__combo.prepend_text(self._text)
                    if self.__limit.get_property('visible'):
                        songs = self.__limit.limit(songs)
                    log.debug('emitting songs-selected')
                    self.emit('songs-selected', songs, None)
                    log.debug('songs emmited: %ss for %s songs', time()-start, len(songs))
                    if self.__save: self.save()
                    self.__combo.write(ZDBQUERIES)
                    self.__host_combo.write(ZDBHOSTS)

    def set_text(self, text):
        log.debug('text=%s',text)
        self.__combo.child.set_text(text)
        if isinstance(text, str): text = text.decode('utf-8')
        self._text = text

    def __text_parse(self, entry):
        log.debug('entry=%s',entry)
        text = entry.get_text()
        if Query.is_parsable(text):
            self._text = text.decode('utf-8')
            gobject.timeout_add(500, self.activate)
            it = self.activate()
            it.next()
            IterableAction(it).start(0.001, prio=gobject.PRIORITY_DEFAULT_IDLE)

    def __test_filter(self, textbox):
        if not config.getboolean('browsers', 'color'):
            textbox.modify_text(gtk.STATE_NORMAL, None)
            return
        text = textbox.get_text().decode('utf-8')
        #log.debug('text=%s',text)
        color = Query.is_valid_color(text)
        if color and textbox.get_property('sensitive'):
            textbox.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse(color))

    def __get_host(self, textbox):
        text = textbox.get_text().decode('utf-8')
        #log.debug('host=%s',text)
        self._host = text

browsers = [ZicDBBar]
