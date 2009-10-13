from __future__ import with_statement

__all__ = ['PlayerCtl']

import os
import thread
import urllib
from threading import RLock
from time import sleep
from zicbee.core.httpdb import web
from zicbee.core.parser import extract_props
from zicbee_lib.resources import get_players
from zicbee.core.playlist import EndOfPlaylist, Playlist
from zicbee.utils import notify
from zicbee_lib.config import config, media_config, DB_DIR
from zicbee_lib.debug import log, DEBUG
from zicbee_lib.formats import jload
try:
    from cPickle import Pickler, Unpickler
except ImportError:
    from Pickle import Pickler, Unpickler

class PlayerCtl(object):
    """ The player interface, this should lead to a constant code, with an interchangeable backend
    See documentation for the zicbee.player hook for the needed interface.
    """
    def __init__(self):
        self.playlist = Playlist()
        self.views = []
        players = []
        preferences = [n.strip() for n in config.players.split(',')]
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
                        self.player.respawn()
                    except:
                        DEBUG()
                        self.position = None

#                    web.debug('pos: %s, errors: %s'%(self.position, errors))

                    if self.position is None:
                        if errors['count'] > 2:
                            errors['count'] = 0
                            i = self.select(1)
                            while True:
                                try:
                                    with self._lock:
                                        i.next()
                                except StopIteration:
                                    break
                        else:
                            errors['count'] += 1
                except Exception, e:
                    DEBUG(False)
            sleep(1)

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
            sel = self.selected
            uri = sel['uri']
            web.debug('download: %s'%uri)
            if uri.count('/db/get') != 1 or uri.count('id=') != 1: # something strange
                song_name = uri
                dl_it = (None for n in xrange(1))
            else: # zicbee
                dl_it = self._download_zic(sel['uri'], song_name)
                dl_it.next()
            web.debug('select: %d (previous=%s)'%(sel['pls_position'], old_pos))
            if old_pos != sel['pls_position']:
                web.debug("Loadfile %d/%s : %s !!"%(sel['pls_position'], sel['pls_size'], song_name))
                cache = media_config[self.selected_type].get('player_cache')
                if cache:
                    self.player.set_cache(cache)
                self.player.load(song_name)
                description="""Title:\t%(title)s
Album:\t%(album)s"""%sel
                notify(sel.get('artist', 'Play'), description)
            self._paused = False
        return dl_it

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
            notify('Shuffled', timeout=200)

    def seek(self, val):
        """ Seek according to given value
        """
        with self._lock:
            self.player.seek(val)
            notify('Seeking %s'%val, timeout=200)

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
            notify('Pause', timeout=300)
        else:
            notify('Play', timeout=300)

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
        returns an iterator
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
            notify('Play %(pattern)s'%kw)
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

    def _download_zic(self, uri, fname):
        if getattr(self, '_download_stream', None):
            self._download_stream.close()

        fd = file(fname, 'wb')
        self._download_stream = fd

        site = urllib.urlopen(uri)
        achieved = 0

        init_sz = media_config[self.selected_type]['init_chunk_size']
        data = site.read(init_sz)
        fd.write(data) # read ~130k (a few seconds in general)
        achieved += len(data)
        self._running = True
        yield site.fileno()

        try:
            buf_sz = media_config[self.selected_type]['chunk_size'] # 16k micro chunks
            while True:
                data = site.read(buf_sz)
                if not data:
                    break
                achieved += len(data)
                fd.write(data)
                yield ''
            fd.close()
        except Exception, e:
            web.debug('ERROR %s %s'%(repr(e), dir(e)))
        finally:
            if fd is self._download_stream:
                self._download_stream = None

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
        try:
            save_file = file(os.path.join(DB_DIR, 'playlists.pk'), 'r')
            p = Unpickler(save_file)
            self._named_playlists = p.load()
        except IOError, e:
            log.debug("Not loading playlists: %s"%e.args[1])
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
    def selected_type(self):
        # http://localhost:9090/db/get/song.mp3?id=5 -> mp3
        uri = self.selected.get('uri')
        if uri:
            try:
                return uri.rsplit('song.', 1)[1].split('?', 1)[0]
            except IndexError:
                return 'dunno'
                return uri.rsplit('.', 1)[1]
        return 'mp3'


