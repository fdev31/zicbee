# vim: et ts=4 sw=4
from __future__ import with_statement

import os
import random # shuffle
import thread
import urllib
import difflib
from time import sleep
from threading import RLock
import itertools
import pkg_resources
from time import time
from zicbee.core.zutils import compact_int, jdump, jload, dump_data_as_text
from zicbee.core.parser import extract_props
from zicbee.core.zutils import uncompact_int
from zicbee.core.debug import DEBUG, log, debug_enabled
from zicbee.core.config import config, media_config, DB_DIR
from zicbee.core.httpdb import WEB_FIELDS, render, web
try:
    from cPickle import Pickler, Unpickler
except ImportError:
    from Pickle import Pickler, Unpickler

SimpleSearchForm = web.form.Form(
        web.form.Hidden('id'),
        web.form.Textbox('host', description='Search host', value='localhost'),
        web.form.Textbox('pattern', description='Search pattern'),
#        web.form.Textbox('tempname', description='Temporary name'),
        )

TagForm = web.form.Form(web.form.Textbox('tag', description='Set tag'))
ScoreForm = web.form.Form(web.form.Dropdown('score', range(11), description='Set rate'))

class Playlist(list):

    def __init__(self, *args):
        list.__init__(self, *args)
        self.pos = -1

    def __delitem__(self, slc):
        self.__checkindex(slc)
        try:
            idx = int(slc)
        except TypeError:
            # slice
            idx = slc.start

        if idx < self.pos:
            self.pos -= 1

        return list.__delitem__(self, slc)

    def __setitem__(self, slc, val):
        self.__checkindex(slc)
        return list.__setitem__(self, slc, val)

    def __checkindex(self, start, stop=None):

        if stop is None:
            try:
                start = int(start)
            except TypeError:
                try:
                    stop = start[-1]
                    start = start[0]
                except TypeError:
                    # slice
                    stop = start.stop
                    start = start.start
            else:
                stop = start

        if start < self.pos:
            # increment
            self.pos += 1
        else:
            if start < self.pos and stop < self.pos:
                # increment stop-start
                self.pos += stop-start
            elif start < self.pos < stop:
                # reset position to beginning of slice
                self.pos = 0 if self.playlist else -1

    def insert(self, idx, obj):
        self.__checkindex(idx)
        list.insert(self, idx, obj)

    def inject(self, data, position=None):
        """ inject a song """
        if hasattr(data, '__getitem__') and isinstance(data[0], basestring):
            data = [data]
        p = self.pos+1 if position is None else position

        self.__checkindex(position)

        self[p:p] = data

    def shuffle(self):
        if len(self) == 0:
            return
        current = self.selected
        if current:
            self.pop(self.pos)
        random.shuffle(self)
        if current:
            self.insert(0, current)
            self.pos = 0
        else:
            self.pos = -1

    def clear(self):
        self[:] = []
        self.pos = -1

    @property
    def selected(self):
        if self.pos == -1 or len(self) == 0:
            return None
        try:
            return self[self.pos]
        except IndexError:
            DEBUG()
            self.pos = -1
            return None

    @property
    def selected_dict(self):
        sel = self.selected
        web.debug('SELECTED: %r'%sel)
        if not sel:
            return dict()

        d = dict(zip(['uri']+WEB_FIELDS, sel))

        try:
            d['length'] = int(d.get('length') or 0)
            d['score'] = int(d.get('score') or 0)
            d['tags'] = d.get('tags') or u''
            d['pls_position'] = self.pos
            d['pls_size'] = len(self)
        except ValueError, e:
            # !!corrupted data!!
            web.debug('data corruption: %s'%e)
            return dict()
        except Exception:
            DEBUG()
        try:
            d['id'] = compact_int(d.pop('__id__'))
        except KeyError:
            pass
        return d

    def move(self, steps):
        self.pos += steps
        if self.pos >= len(self):
            self.pos = -1
        elif self.pos < -1:
            self.pos = -1

class PlayerCtl(object):
    """ The player interface, this should lead to a constant code, with an interchangeable backend
    See documentation for the zicbee.player hook for the needed interface.
    """
    def __init__(self):
        self.playlist = Playlist()
        self.views = []
        for player_plugin in pkg_resources.iter_entry_points('zicbee.player'):
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
                            self.position = int(self.player.position)
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
                    DEBUG()
            sleep(1)

    def select(self, sense):
        """ Selects a song, according to the given offset
        ex.: self.select(1) # selects the next track
        self.select(-1) # selects the previous track
        self.select(0) # no-op
        """

        with self._lock:
            old_pos = self.playlist.pos
            self.playlist.move(sense)
            song_name = config.streaming_file
            sel = self.selected
            web.debug('download: %s'%sel['uri'])
            dl_it = self._download_zic(sel['uri'], song_name)
            dl_it.next()
            web.debug('select: %d (previous=%s)'%(sel['pls_position'], old_pos))
            if old_pos != sel['pls_position']:
                web.debug("Loadfile %d/%s : %s !!"%(sel['pls_position'], sel['pls_size'], song_name))
                cache = media_config[self.selected_type]['player_cache']
                self.player.set_cache(cache)
                self.player.load(song_name)
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

    def seek(self, val):
        """ Seek according to given value
        """
        with self._lock:
            self.player.seek(val)

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

    def delete_playlist(self, name):
        """ Delete the given named playlist (by name) """
        del self._named_playlists[name]

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
        if operation == 'copy':
            self.playlist = self._named_playlists[pls_name]
        elif operation == 'append':
            self.playlist.extend(self._named_playlists[pls_name])

    def fetch_playlist(self, hostname=None, temp=False, **kw):
        """
        Fetch a playlist from a given hostname,
        can take any keyword, will be passed with the remote command
        some useful keywords:
            pattern: a search string
            db: the database name (default is ok in general)
        if the temp keyword is given,
        a temporary playlist will be created with the given name
        (the main one is not affected)
        returns an iterator
        """
        web.debug('fetch_pl: h=%s tmp=%s %s'%(hostname, temp, kw))
        hostname = hostname.strip()
        if not hostname:
            hostname = '127.0.0.1'

        pattern = kw.get('pattern', None)
        playlist = pls = None
        if pattern:
            # try to find 'pls' (output) and 'playlist' (input) in pattern
            (new_pattern , props) = extract_props(pattern, ('playlist', 'pls'))
            if props:
                props = dict(props)
                playlist = props.get('playlist', None)
                pls = props.get('pls', None)
            if new_pattern:
                kw['pattern'] = new_pattern
            else:
                del kw['pattern']

        if ':' not in hostname:
            hostname = "%s:%s"%(hostname, config.default_port)

        to_be_inserted = []

        with self._lock:
            self.hostname = hostname
            params = '&%s'%urllib.urlencode(kw) if kw else ''
            uri = 'http://%s/db/?fmt=json%s'%(hostname, params)
            site = urllib.urlopen(uri)
            web.debug('fetch_pl: playlist=%s pls=%s kw=%s uri=%s'%(playlist, pls, kw, uri))

            append = False
            out_pls = self.playlist
            if pls:
                # we have an 'output' playlist
                if pls.startswith('+'):
                    pls = pls[1:]
                    append = True
                elif pls.startswith('>'):
                    pls = pls[1:]
                    if self.playlist.pos >= 0:
                        append = self.playlist.pos + 1 # insert just next
                if pls != '#':
                    # output playlist is not 'current playlist' 
                    if pls not in self._named_playlists:
                        self._named_playlists[pls] = Playlist()
                    out_pls = self._named_playlists[pls]
            add = out_pls.append
            ext = out_pls.extend
            current = self.playlist.selected
            if isinstance(append, int):
                add = to_be_inserted.append
                ext = to_be_inserted.extend

            if not append:
                out_pls[:] = []
                if current:
                    add(current)

        total = 0
        done = False
        if playlist:
            if playlist in self._named_playlists:
                ext(self._named_playlists[playlist])
            elif playlist == '#' and out_pls is not self.playlist:
                ext(self.playlist)

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
                break

        if out_pls is self.playlist:
            # reset song position
            with self._lock:
                if not self.playlist:
                    self.playlist.pos = out_pls.pos
                if to_be_inserted:
                    self.playlist.inject(to_be_inserted, position=append)

                if self.playlist.pos > 0 and not append:
                    self.playlist.pos = 0
                self._tmp_total_length = total
        else:
            self._save_playlists()

    def _download_zic(self, uri, fname):
        if getattr(self, '_download_stream', None):
            self._download_stream.close()

        fd = file(fname, 'wb')
        self._download_stream = fd

        site = urllib.urlopen(uri)
        total = float(site.info().getheader('Content-Length'))
        total_length = 100
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
                progress = total_length * (achieved / total)
#                self.signal_view('download_progress', progress)
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
            web.debug('ERROR: load_playlists: %s'%repr(e))
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
            return uri.rsplit('song.', 1)[1].split('?', 1)[0]
        return 'mp3'


class webplayer:
    player = PlayerCtl()

    GET = web.autodelegate('REQ_')

    def REQ_main(self):
        return self.render_main(render.player)

    def REQ_basic(self):
        return self.render_main(render.basicplayer)

    def render_main(self, rend):
        cook_jar = web.cookies(host='localhost', pattern='')
        cook_jar['pattern'] = urllib.unquote(cook_jar['pattern'])
        af = SimpleSearchForm(True)
        sf = ScoreForm(True)
        tf = TagForm(True)
        af.fill(cook_jar)
        yield unicode(rend(af, sf, tf, config.web_skin or 'default'))

    REQ_ = REQ_main # default page

    def REQ_close(self):
        self.player.close()

    def REQ_search(self):
        it = None
        try:
            i = web.input()
            tempname = i.get('tempname', '').strip() or False
            if i.get('pattern'):
                if i.pattern.startswith('http'):
                    try:
                        uri = i.pattern
                        hostname = uri.split("/", 3)[2]
                        song_id = uri.rsplit('=', 1)[1]
                        it = self.player.fetch_playlist(hostname, pattern=u'id: %s pls: >#'%song_id, temp=tempname)
                    except:
                        pls = self.player.playlist
                        pls.inject( [uri, u'injected uri', 1000, None, None, 1000] )
                else:
                    it = self.player.fetch_playlist(i.get('host', 'localhost'), pattern=i.pattern, temp=tempname)
            else:
                it = self.player.fetch_playlist(i.get('host', 'localhost'), pattern=u'', temp=tempname)
            it.next()

        except (IndexError, KeyError):
            DEBUG()
        finally:
            return it

    def REQ_delete(self):
        i = web.input()
        self.player.delete_entry(int(i['idx']))
        return ''


    def REQ_move(self):
        i = web.input()
        self.player.move_entry(int(i['s']), int(i['d']))
        return ''

    def REQ_swap(self):
        i = web.input()
        self.player.swap_entry(int(i['i1']), int(i['i2']))
        return ''

    def REQ_append(self):
        self.player.playlist_change('append', web.input()['name'])
        return ''

    def REQ_copy(self):
        self.player.playlist_change('copy', web.input()['name'])
        return ''

    def REQ_volume(self):
        i = web.input()
        val = i.get('val')
        if val is not None:
            self.player.volume(val)
        return ''

    def REQ_infos(self):
        format = web.input().get('fmt', 'txt')

        _d = self.player.selected or dict()
        # add player infos
        _d['song_position'] = self.player.position
        _d['paused'] = self.player._paused

        if format.startswith('htm'):
            web.header('Content-Type', 'text/html; charset=utf-8')
        return dump_data_as_text(_d, format)

    def REQ_playlist(self):
        i = web.input()
        pls = self.player.playlist

        start = int(i.get('start', 0))

        format = i.get('fmt', 'txt')

        if i.get('res'):
            end = start + int(i.res)
        else:
            end = len(pls)

        window_iterator = (pls[i] + [i] for i in xrange(start, min(len(pls), end)))

        return dump_data_as_text(window_iterator, format)

    def REQ_guess(self, guess):
        try:
            self.player.selected.iteritems
        except AttributeError:
            yield jdump(False)
            return

        artist = self.player.selected['artist']
        title = self.player.selected['title']
        if difflib.get_close_matches(guess, (artist, title)):
            yield jdump(True)
        else:
            yield jdump(False)

    def REQ_shuffle(self):
        return self.player.shuffle() or ''

    def REQ_clear(self):
        return self.player.clear() or ''

    def REQ_pause(self):
        return self.player.pause() or ''

    def REQ_prev(self):
        return self.player.select(-1) or ''

    def REQ_next(self):
        return self.player.select(1) or ''

    def REQ_tag(self, tag):
        return self.player.tag(unicode(tag.lstrip('/'))) or ''

    def REQ_rate(self, score):
        return self.player.rate(score.lstrip('/')) or ''

    def REQ_seek(self, val):
        val = val[1:]
        web.debug('VAL=%s'%val)
        self.player.seek(int(val))
        return ''

