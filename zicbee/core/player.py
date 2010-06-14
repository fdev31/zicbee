from __future__ import with_statement

__all__ = ['PlayerCtl']

import os
import gc
import thread
import urllib
import atexit
import itertools
from functools import partial
from time import sleep
from Queue import Queue, Empty
from zicbee.utils import notify
from zicbee.core.httpdb import web
from threading import RLock, Thread, Event
from zicbee.core.parser import extract_props
from zicbee_lib.resources import get_players
from zicbee.core.playlist import EndOfPlaylist, Playlist
from zicbee_lib.config import config, media_config, DB_DIR
from zicbee_lib.debug import log, DEBUG
from zicbee_lib.formats import jload
from zicbee_lib.debug import nop

try:
    from cPickle import Pickler, Unpickler
except ImportError:
    from Pickle import Pickler, Unpickler

from hashlib import md5

def get_type_from_uri(uri):
    if uri:
        try:
            return uri.rsplit('song.', 1)[1].split('?', 1)[0]
        except IndexError:
            return 'dunno'
            return uri.rsplit('.', 1)[1]
    return 'mp3'

def uri2fname(uri):
    return "%s.%s.%s"%(config.streaming_file, md5(uri).hexdigest(), str(get_type_from_uri(uri)))

class Downloader(Thread):
    q = Queue(3)
    next = None
    preloaded = []

    def __init__(self):
        Thread.__init__(self)
        self.aborted = False
        atexit.register(self.stop)

    def run(self):
        self.running = True
        stream = None
        fd = None
        cs = None

        while self.running:
            got_one = False
            while True:
                try:
                    uri, ic, cs, cb = self.q.get_nowait()
                    got_one = True
                except Empty:
                    break

            if got_one: # we have something to download
                if stream:
                    web.debug('Closing incomplete download %s'%preload_name)
                    fd.close()
                    stream.close()
                    self._abort(preload_name)
                preload_name = uri2fname(uri)
                self.preloaded.append(preload_name)
                fd = file(preload_name, 'w')
                stream = urllib.urlopen(uri)
                fd.write(stream.read(ic))
                fd.flush()
                cb()
            elif stream:
                d = stream.read(cs)
                if not d:
                    web.debug('download: EOF')
                    stream.close()
                    stream = None
                    fd.close()
                else:
                    fd.write(d)
            else:
                gc.collect()
                sleep(1) # wait some idle time
                if self.next: # preload asked, set the right descriptors
                    next = self.next
                    self.next = None
                    preload_name = uri2fname(next)
                    self.preloaded.append(preload_name)
                    fd = file(preload_name, 'w')
                    stream = urllib.urlopen(next)

    def _abort(self, name):
        web.debug("RM %s"% name)
        self.preloaded.remove(name)
        os.unlink(name)

    def get(self, uri, i_chunk=None, chunk=None):
        MAX_PRELOADS = 5
        filename = uri2fname(uri)
        web.debug('GET %s => %s'%(uri, filename))

        if len(self.preloaded) > MAX_PRELOADS:
            rm = self.preloaded.pop(0)
            try:
                web.debug("RM %s"% rm)
                os.unlink(rm)
            except OSError:
                pass
        if filename not in self.preloaded:
            # ask for a download and wait for the initial_chunk to be completed
            e = Event()
            self.q.put( (uri, i_chunk, chunk, e.set) )
            e.wait()
        return filename

    def stop(self):
        self.running = False
        for rm in self.preloaded:
            try:
                os.unlink(rm)
            except OSError:
                pass

class PlayerCtl(object):
    """ The player interface, this should lead to a constant code, with an interchangeable backend
    See documentation for the `zicbee.player`_ entry_point for the needed interface.
    """
    downloader = Downloader()

    def __init__(self):
        self.playlist = Playlist()
        self.downloader.start()
        self.views = []
        players = []
        preferences = [n.strip() for n in config.players]
        web.debug('player preferences: %s'%(', '.join(preferences)))
        for player_plugin in get_players():
            if player_plugin.name in preferences:
                players.insert(preferences.index(player_plugin.name), player_plugin)
            else:
                players.append(player_plugin)
        web.debug('available players: %s'%players)
        for player_plugin in players:
            try:
                self.player = player_plugin.load()()
            except Exception, e:
                web.debug('failed loading %s: %s'%(player_plugin.name, e))
            else:
                break # plugin loaded
        else:
            DEBUG()
            raise RuntimeError("No backend could be loaded!")

        self.position = None
        self._lock = RLock()
        self._paused = False
        thread.start_new_thread(self._main_loop, tuple())
        self._load_playlists()

    def close(self):
        self.downloader.stop()
        self.player.quit()

    def __repr__(self):
        return '<Player[%d] playing %s (views=%d)>'%(len(self.playlist), self.selected, len(self.views))

    def _main_loop(self):
        errors = dict(count=0)

        while True:
            if not self._paused and len(self.playlist):
                try:
                    try:
                        with self._lock:
                            p = self.player.position
                            if p is None:
                                errors['count'] = 10
                                self.position = None
                            else:
                                self.position = int(p)
                    except IOError, e:
                        web.debug('E: %s'%e)
                        self.position = None
                        # restart player
                        # self.player.respawn()
                    except:
                        DEBUG()
                        self.position = None

#                    web.debug('pos: %s, errors: %s'%(self.position, errors))

                    if self.position is None:
                        web.debug('NO POSITION %s'%errors)
                        if errors['count'] > 2:
                            errors['count'] = 0
                            i = self.select(1)
                        else:
                            errors['count'] += 1
                except Exception, e:
                    DEBUG(False)
            sleep(1)

    #@classmethod
    def _download_zic(self, uri, sync=False):
        d = media_config[get_type_from_uri(uri)]
        return self.downloader.get(uri, -1 if sync else d['init_chunk_size'], d['chunk_size'])

    def select(self, sense):
        """ Selects a song, according to the given offset
        ex.: self.select(1) # selects the next track
        self.select(-1) # selects the previous track
        self.select(0) # no-op
        """
        with self._lock:
            old_pos = self.playlist.pos
            try:
                self.playlist.move(sense)
            except EndOfPlaylist:
                if not config.loop:
                    self.pause()
            song_name = config.streaming_file
            if len(self.playlist) and self.playlist.pos < 0:
                self.playlist.pos = 0
            sel = self.selected
            uri = sel['uri']
            web.debug('download: %s'%uri)
            if uri.count('/db/get') != 1 or uri.count('id=') != 1:
                # something strange (LIVE mode)
                song_name = uri
                streaming = True
            else: # zicbee
                sync = bool(sel.get('cursed'))
                song_name = self._download_zic(sel['uri'], sync) # threaded
                streaming = False

            sibling = self.sibling
            if sibling and not sibling.get('cursed'):
                self.downloader.next = sibling['uri']

            web.debug('select: %d (previous=%s)'%(sel['pls_position'], old_pos))
            if old_pos != sel['pls_position']:
                sleep(0.3) # FIXME: wait for things to settle... :(((
                web.debug("Loadfile %d/%s : %s !!"%(sel['pls_position'], sel['pls_size'], song_name))
                cache = media_config[self.selected_type].get('player_cache')
                if cache:
                    self.player.set_cache(cache)
            web.debug('LOADING: %s'%song_name)
            self.player.load(song_name)
            description="""<b>%(title)s</b>
<i>%(album)s</i>"""%sel
            notify(sel.get('artist', 'Play'), description, icon='info') # generic notification
            self._paused = False
            if streaming:
                sleep(1.5) # FIXME: wait for things to settle... :(((
        return

    def volume(self, val):
        self.player.volume(val)

    def tag(self, tag):
        ci = self.selected['id']
        uri = 'http://%s/db/tag/%s/%s'%(self.hostname, ci, tag)
        urllib.urlopen(uri)

    def rate(self, score):
        web.debug('DEBUG: %s'%self.selected)
        ci = self.selected['id']
        uri = 'http://%s/db/rate/%s/%s'%(self.hostname, ci, score)
        web.debug('URI: %s'%uri)
        urllib.urlopen(uri)

    def shuffle(self):
        """ Shuffle the playlist, and selects the first track
        if the playlist is empty, do nothing
        """

        with self._lock:
            self.playlist.shuffle()
            notify('Shuffled', timeout=200, icon='shuffle')

    def seek(self, val):
        """ Seek according to given value
        """
        with self._lock:
            self.player.seek(val)
            notify('Seeking %s'%val, timeout=200, icon='next')

    def clear(self):
        """ Clear the current playlist and stop the player
        """
        with self._lock:
            self.playlist.clear()
            self._load_playlists()
            self.position = None
            self.player.respawn()
            self._paused = False

    def pause(self):
        """ (Un)Pause the player
        """
        with self._lock:
            self.player.pause()
            self._paused = not self._paused
        if self._paused:
            notify('Pause', timeout=300, icon='pause')
        else:
            notify('Play', timeout=300, icon='play')

    def delete_entry(self, position):
        """ delete the song at the given position """
        del self.playlist[position]

    def move_entry(self, pos1, pos2):
        """ Move an entry to a given playlist position"""
        p = self.playlist
        to_move = p[pos1]
        del p[pos1]
        p.inject(to_move, pos2)

    def swap_entry(self, pos1, pos2):
        """ Swap two entries in the current playlist """
        p = self.playlist
        p[pos1], p[pos2] = p[pos2], p[pos1]

    def playlist_change(self, operation, pls_name):
        """ copy or append a named playlist to the active one
        """
        pls = self._named_playlists[pls_name]
        if operation == 'copy':
            from copy import copy
            self.playlist = copy(pls)
            if config.autoshuffle:
                self.shuffle()
            self.select(0)
        elif operation == 'append':
            self.playlist.extend(pls)
        elif operation == 'inject':
            self.playlist.inject(pls, self.playlist.pos)
        self.running = True

    def delete_playlist(self, name):
        """ Delete the given named playlist (by name) """
        del self._named_playlists[name]
        self._save_playlists()

    def save(self, name):
        from copy import copy
        self._named_playlists[web.input()['name']] = copy(self.playlist)
        self._save_playlists()

    def fetch_playlist(self, hostname=None, playlist=False, **kw):
        """
        Fetch a playlist from a given hostname,
        can take any keyword, will be passed with the remote command
        kw should contain "pattern" parameter
        you can pass a playlist name to save the search
        a temporary playlist will be created with the given name
        (the main one is not affected)
        """
        self.running = False # do not disturb !
        web.debug('fetch_pl: h=%s tmp=%s %s'%(hostname, playlist, kw))

        # sanitise hostname
        hostname = hostname.strip()
        if not hostname:
            hostname = '127.0.0.1'
        if ':' not in hostname:
            hostname = "%s:%s"%(hostname, config.default_port)

        # set playlist name
        (new_pattern , props) = extract_props(kw['pattern'], ('pls',))
        if new_pattern:
            kw['pattern'] = new_pattern

        props = dict(props)
        if props:
            playlist = props['pls']

        with self._lock:
            self.hostname = hostname
            notify('Requesting', kw.get('pattern'))
            params = '&%s'%urllib.urlencode(kw) if kw else ''
            uri = 'http://%s/db/?fmt=json%s'%(hostname, params)
            site = urllib.urlopen(uri)

            # convert outpout playlist parameter
            append = False
            if playlist and playlist[0] in '>+':
                if playlist[0] == '>':
                    append = True
                else: # +
                    try:
                        append = self.playlist.pos + 1
                    except TypeError:
                        append = True
                playlist = playlist[1:].strip()

            elif not playlist:
                playlist = '#'

            if playlist == '#':
                out_pls = self.playlist
            else:
                out_pls = self._named_playlists[playlist] = Playlist()

            web.debug('fetch_pl: out_pls=%s kw=%s uri=%s'%(out_pls, kw, uri))

            # set up the output
            if not append:
                out_pls.replace([])

            if append and not isinstance(append, bool):
                def add_coroutine(offset):
                    n = offset
                    _injct = out_pls.inject
                    while True:
                        val = yield
                        _injct(val, n)
                        n = n+1
                iterator = add_coroutine(append)
                iterator.next()
                add = iterator.send
            else:
                add = out_pls.append

        total = 0

        while True:
            for n in xrange(50):
                line = site.readline()
                if not line:
                    break
                try:
                    r = jload(line)
                except:
                    DEBUG()
                    web.debug("Can't load json description: %s"%line)
                    break
                total += r[4]
#                web.debug('r=%s'%r)
                with self._lock:
                    add(r)
                self.signal_view('update_total', total)

            yield ''

            if not line:
                del add
                break

        if out_pls is self.playlist:
            if config.autoshuffle and not append:
                self.shuffle()
        else:
            self._save_playlists()


    def _save_playlists(self):
        try:
            save_file = file(os.path.join(DB_DIR, 'playlists.pk'), 'w')
            p = Pickler(save_file)
            p.dump(self._named_playlists)
        except Exception, e:
            web.debug('ERROR: save_playlists: %s'%repr(e))
        else:
            web.debug('playlists saved: %s'%self._named_playlists.keys())

    def _load_playlists(self):
        self._named_playlists = dict()
        db_path = os.path.join(DB_DIR, 'playlists.pk')
        try:
            save_file = file(db_path, 'r')
            p = Unpickler(save_file)
            self._named_playlists = p.load()
        except IOError, e:
            self._named_playlists['radios'] = Playlist((
                ['http://broadcast.infomaniak.net:80/radionova-high.mp3',
                    u'Misc artists', u'No album', 'Radio Nova', 1000,
                    None, None, 0],
                ['http://vipicecast.yacast.net:80/virginradio',
                    u'Misc artists', u'No album', 'Virgin Radio', 1000,
                    None, None, 0],
                ['http://vipicecast.yacast.net:80/vra_webradio03',
                    u'Misc artists', u'No album', 'Virgin Radio 70', 1000,
                    None, None, 0],
                ['http://streaming.rtbf.be:8000/2128xrtbf',
                    u'Misc artists', u'No album', 'Virgin Radio 70', 1000,
                    None, None, 0],
                ['http://ogg.frequence3.net:19000/frequence3.ogg',
                    u'Misc artists', u'No album', 'Radio Frequence3', 1000,
                    None, None, 0],
                ['http://mp3.live.tv-radio.com/lemouv/all/lemouvhautdebit.mp3',
                    u'Misc artists', u'No album', 'Radio Le Mouv\'', 1000,
                    None, None, 0],
                ['http://mp3.live.tv-radio.com/francemusique/all/francemusiquehautdebit.mp3',
                    u'Misc artists', u'No album', 'Radio France Musique', 1000,
                    None, None, 0],
                ))
            self._save_playlists()
        except Exception, e:
            web.debug('Unable to load playlist. Corrupted file ? (%s)'%repr(e))
            DEBUG()
        else:
            web.debug('playlists loaded: %s'%self._named_playlists.keys())

    def signal_view(self, name, *args, **kw):
#        web.debug('signaling %s %s %s'%(name, args, kw))
        for view in self.views:
            web.debug(' -> to view %s'%view)
            try:
                getattr(view, 'SIG_'+name)(*args, **kw)
            except:
                DEBUG()

    @property
    def selected(self):
        return self.playlist.selected_dict or None

    @property
    def sibling(self):
        return self.playlist.sibling


    @property
    def selected_type(self):
        # http://localhost:9090/db/get/song.mp3?id=5 -> mp3
        return get_type_from_uri(self.selected.get('uri'))

