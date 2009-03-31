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
from time import time
from zicbee.core.zutils import compact_int, jdump, jload, parse_line
from zicbee.core.zutils import uncompact_int
from zicbee.core.debug import DEBUG
from zicbee.core.config import config, media_config
from zicbee.core.httpdb import WEB_FIELDS, render, web

SimpleSearchForm = web.form.Form(
        web.form.Hidden('id'),
        web.form.Textbox('host', description='Search host', value='localhost'),
        web.form.Textbox('pattern', description='Search pattern'),
#        web.form.Textbox('tempname', description='Temporary name'),
        )

TagForm = web.form.Form(web.form.Textbox('tag', description='Set tag'))
ScoreForm = web.form.Form(web.form.Dropdown('score', range(11), description='Set rate'))

def dump_data_as_text(d, format):
    if format == "json":
        yield jdump(d)
    else:
        # text output
        if isinstance(d, dict):
            for k, v in d.iteritems():
                yield '%s: %s\n'%(k, v)
        else:
            # assume iterable
            for elt in d:
                yield "%r\n"%elt

class PlayerCtl(object):
    """ The player interface, this should lead to a constant code, with an interchangeable backend
    See self.player.* for the needed interface.
    """
    def __init__(self):
        self._cur_song_pos = -1
        self.playlist = []
        self.views = []
        try:
            from . import mp # mplayer backend
            self.player = mp.MPlayer()
        except:
            # TODO: add different backends!
            # (maybe adapt mp interface to be more generic)
            DEBUG()
            raise RuntimeError("No backend could be loaded!")
        self.position = None
        self._lock = RLock()
        self._paused = False
        thread.start_new_thread(self._main_loop, tuple())
        self._named_playlists = dict()

    def close(self):
        try:
            self.player.quit()
        except Exception, e:
            print "E: %s"%e
        finally:
            self.player.wait()

    def __repr__(self):
        return '<Player[%d] playing %s (views=%d)>'%(len(self.playlist), self.selected, len(self.views))

    def _main_loop(self):
        errors = dict(count=0)

        while True:
            if not self._paused and len(self.playlist):
                try:
                    try:
                        with self._lock:
                            self.position = int(self.player.prop_stream_pos/10000)
                    except IOError, e:
                        web.debug('E: %s'%e)
                        self.position = None
                        # restart player
                        self.player.wait()
                        self.player = mp.MPlayer()
                    except:
                        self.position = None

                    web.debug('pos: %s, errors: %s'%(self.position, errors))

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
                    web.debug('E: %s'%e)
                except:
                    web.debug('E: ???')
            sleep(1)

    def select(self, sense):
        """ Selects a song, according to the given offset
        ex.: self.select(1) # selects the next track
        self.select(-1) # selects the previous track
        self.select(0) # no-op
        """

        with self._lock:
            pos = self._cur_song_pos
            self._cur_song_pos += sense
            web.debug(self.infos, self.selected)

            if self._cur_song_pos > len(self.playlist):
                self._cur_song_pos = -1
            elif self._cur_song_pos < -1:
                self._cur_song_pos = -1

            song_name = config.streaming_file
            web.debug('download: %s'%self.selected_uri)
            dl_it = self._download_zic(self.selected_uri, song_name)
            dl_it.next()
            web.debug('select: %d'%self._cur_song_pos)
            if pos != self._cur_song_pos:
                web.debug("Loadfile %d/%s : %s !!"%(self._cur_song_pos, len(self.playlist), song_name))
                cache = media_config[self.selected_type]['player_cache']
                self.player.set_cache(cache)
                self.player.loadfile(song_name)
            self._paused = False
        return dl_it

    def volume(self, val):
        self.player.volume(val, 'abs')

    def tag(self, tag):
        ci = compact_int(self.selected['__id__'])
        uri = 'http://%s/db/tag/%s/%s'%(self.hostname, ci, tag)
        urllib.urlopen(uri)

    def rate(self, score):
        web.debug('DEBUG: %s'%self.selected)
        ci = compact_int(self.selected['__id__'])
        uri = 'http://%s/db/rate/%s/%s'%(self.hostname, ci, score)
        web.debug('URI: %s'%uri)
        urllib.urlopen(uri)

    def shuffle(self):
        """ Shuffle the playlist, and selects the first track
        if the playlist is empty, do nothing
        """
        if len(self.playlist) == 0:
            return
        with self._lock:
            pos = self._cur_song_pos
            current = None
            if (0 <= pos < len(self.playlist)):
                current = self.playlist.pop(pos)
            random.shuffle(self.playlist)
            if current:
                self.playlist.insert(0, current)
                self._cur_song_pos = 0
            else:
                self._cur_song_pos = -1

    def seek(self, val):
        """ Seek according to given value
        """
        with self._lock:
            self.player.seek(val)

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
        """ Swap two entries in the current playlist """
        p = self.playlist
        p[pos1], p[pos2] = p[pos2], p[pos1]

    def playlist_change(self, operation, pls_name):
        """ copy or append a named playlist to the active one
        """
        if operation == 'copy':
            self.playlist = self._named_playlists[pls_name]
            self._cur_song_pos = 0
        if operation == 'append':
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
        web.debug('fetch_pl: h=%s tmp=%s'%(hostname, temp))
        hostname = hostname.strip()
        if not hostname:
            hostname = '127.0.0.1'

        if ':' not in hostname:
            hostname = "%s:%s"%(hostname, config.default_port)
        new_song_pos = -1

        with self._lock:
            self.hostname = hostname

            uri = 'http://%s/db/?json=1&%s'%(hostname, urllib.urlencode(kw))
            site = urllib.urlopen(uri)
            web.debug('fetch_pl: kw=%s uri=%s'%(kw, uri))
            if temp:
                # TODO: temporary playlist support
                self._named_playlists[temp] = []
                add = self._named_playlists[temp]
            else:
                current = self.playlist[self._cur_song_pos] if self.selected else None
                self.playlist[:] = []
                add = self.playlist.append
                if current:
                    new_song_pos = 0
                    add(current)

        total = 0
        done = False

        while True:
            for n in xrange(50):
                line = site.readline()
                if not line:
                    break
                try:
                    r = jload(line)
                except:
                    web.debug("Can't load json description: %s"%line)
                    break
                total += r[4]
                web.debug('r=%s'%r)
                with self._lock:
                    add(r)
                self.signal_view('update_total', total)

            yield
            if not line:
                break

        if temp:
            self._total_length = total
        else:
            # reset song position
            with self._lock:
                self._cur_song_pos = new_song_pos
                self._tmp_total_length = total

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
#        web.debug('downloading %d'%achieved)

        try:
            buf_sz = media_config[self.selected_type]['chunk_size'] # 16k micro chunks
            while True:
                data = site.read(buf_sz)
                progress = total_length * (achieved / total)
#                self.signal_view('download_progress', progress)
                if not data:
                    break
                achieved += len(data)
#                web.debug('downloading %s from %s (%.1f%%)'%(uri, self, progress))
                fd.write(data)
                yield
            fd.close()
        except Exception, e:
            web.debug('ERROR %s %s'%(repr(e), dir(e)))
        finally:
            if fd is self._download_stream:
                self._download_stream = None

    def signal_view(self, name, *args, **kw):
        web.debug('signaling %s %s %s'%(name, args, kw))
        for view in self.views:
            web.debug(' -> to view %s'%view)
            try:
                getattr(view, 'SIG_'+name)(*args, **kw)
            except:
                DEBUG()

    def _get_infos(self, l):
        try:
            d = dict(zip(['uri']+WEB_FIELDS, l))
            d['length'] = int(d['length'])
            d['score'] = d['score'] or 0.0
            d['tags'] = d['tags'] or u''
            return d
        except Exception, e:
            web.debug('_get_infos ERR: %s'%e)
            return None

    @property
    def selected(self):
        pos = self._cur_song_pos
        if not (0 <= pos < len(self.playlist)):
            return None
        else:
            return self._get_infos(self.playlist[pos])

    @property
    def selected_type(self):
        # http://localhost:9090/db/get/song.mp3?id=5 -> mp3
        try:
            return self.selected_uri.rsplit('song.', 1)[1].split('?', 1)[0]
        except:
            return 'mp3'

    @property
    def selected_uri(self):
        try:
            with self._lock:
                if self._cur_song_pos < 0:
                    raise Exception()
                txt =  self.playlist[self._cur_song_pos][0]
            return txt
        except Exception, e:
            web.debug("selected_uri ERR: %s"%e)
            return None

    @property
    def infos(self):
        return dict(
                current = self._cur_song_pos,
                total = len(self.playlist),
                running = self._cur_song_pos >= 0,
                )

class webplayer:
    player = PlayerCtl()

    GET = web.autodelegate('REQ_')
    lastlog = []

    def REQ_main(self):
        cook_jar = web.cookies(host='localhost', pattern='')
        cook_jar['pattern'] = urllib.unquote(cook_jar['pattern'])
        af = SimpleSearchForm(True)
        sf = ScoreForm(True)
        tf = TagForm(True)
        af.fill(cook_jar)
        yield unicode(render.player(af, sf, tf))

    REQ_ = REQ_main # default page

    def REQ_close(self):
        self.player.close()

    def REQ_search(self):
        it = None
        try:
            i = web.input()
            if i.get('pattern'):
                it = self.player.fetch_playlist(i.get('host', 'localhost'), pattern=i.pattern, temp=i.get('tempname', '').strip() or False)
            else:
                it = self.player.fetch_playlist(i.get('host', 'localhost'), i.get('tempname', '').strip() or False)
            it.next()

        except (IndexError, KeyError):
            it = None
        finally:
            return itertools.chain(it, [web.redirect('/')])

    def REQ_delete(self):
        i = web.input()
        self.player.delete_entry(int(i['idx']))
        return web.redirect('/')

    def REQ_move(self):
        i = web.input()
        self.player.move_entry(int(i['i1']), int(i['i2']))
        return web.redirect('/')

    def REQ_append(self):
        self.player.playlist_change('append', web.input()['name'])
        return web.redirect('/')

    def REQ_copy(self):
        self.player.playlist_change('copy', web.input()['name'])
        return web.redirect('/')

    def REQ_volume(self):
        i = web.input()
        val = i.get('val')
        if val is not None:
            self.player.volume(val)

    def REQ_infos(self):
        i = web.input()
        format = i.get('fmt', 'txt')

        try:
            _d = self.player.selected.copy()
            _d['uri'] = self.player.playlist[self.player._cur_song_pos][0]
        except AttributeError:
            _d = dict()
        _d['pls_position'] = self.player._cur_song_pos
        _d['song_position'] = self.player.position
        _d['pls_size'] = len(self.player.playlist)
        _d['paused'] = self.player._paused

        try:
            _d['id'] = compact_int(_d.pop('__id__'))
        except KeyError:
            pass

        return dump_data_as_text(_d, format)

    def REQ_lastlog(self):
        return '\n'.join(self.lastlog)

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
        return self.player.shuffle()

    def REQ_pause(self):
        return self.player.pause()

    def REQ_prev(self):
        return self.player.select(-1)

    def REQ_next(self):
        return self.player.select(1)

    def REQ_tag(self, tag):
        return self.player.tag(unicode(tag.lstrip('/')))

    def REQ_rate(self, score):
        return self.player.rate(score.lstrip('/'))

    def REQ_seek(self, val):
        val = val[1:]
        web.debug('VAL=%s'%val)
#        self.player.seek(int(val))

