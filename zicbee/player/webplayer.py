# vim: et ts=4 sw=4

import web
from pkg_resources import resource_filename
from zicbee.core.zutils import jdump, jload
from . import mp

web.internalerror = web.debugerror

# Set default headers & go to templates directory
web.ctx.headers = [('Content-Type', 'text/html; charset=utf-8'), ('Expires', 'Thu, 01 Dec 1994 16:00:00 GMT')]
render = web.template.render(resource_filename('zicbee.ui.web', 'web_templates'))

SimpleSearchForm = web.form.Form(
        web.form.Hidden('id'),
        web.form.Hidden('host', value='localhost'),
        web.form.Textbox('pattern'),
        web.form.Checkbox('m3u'),
        )

import urllib

class PlayerCtl(object):
    def __init__(self):
        self._cur_song_pos = -1
        web.debug('X'*1000)
        self.playlist = []
        self.views = []
        self.player = mp.MPlayer()

    def select(self, sense):
        pos = self._cur_song_pos
        self._cur_song_pos += sense
        web.debug(self.infos, self.selected)

        if self._cur_song_pos > len(self.playlist):
            self._cur_song_pos = -1
        elif self._cur_song_pos < -1:
            self._cur_song_pos = -1

        web.debug('select: %d'%self._cur_song_pos)
        if pos != self._cur_song_pos:
            web.debug("Loadfile %d/%s : %s !!"%(self._cur_song_pos, len(self.playlist), self.selected_uri))
            self.player.loadfile(self.selected_uri)

    def fetch_playlist(self, hostname=None, temp=False, **kw):
        """ Takes a hostname & some kw (likely to be "pattern")
        returns an iterator
        """
        if not hostname:
            hostname = '127.0.0.1'

        if ':' not in hostname:
            hostname += ':9090'

        self.hostname = hostname

        uri = 'http://%s/search/?json=1&%s'%(hostname, urllib.urlencode(kw))
        site = urllib.urlopen(uri)

        if temp:
            self._tmp_playlist = []
            add = self._tmp_playlist
        else:
            self.playlist[:] = []
            add = self.playlist.append

        total = 0
        done = False

        while True:
            line = site.readline()
            if not line:
                break
            r = jload(line)
            total += r[4]
#            r[0] = 'http://%s%s'%(hostname, r[0])
            add(r)
            self.signal_view('update_total', total)
            yield

        self._total_length = total

        # reset song position
        self._cur_song_pos = 0

    def signal_view(self, name, *args, **kw):
        web.debug('signaling %s %s %s'%(name, args, kw))
        for view in self.views:
            web.debug(' -> to view %s'%view)
            try:
                getattr(view, 'SIG_'+name)(*args, **kw)
            except:
                DEBUG()

    def _get_selected(self):
        pos = self._cur_song_pos
        try:
            if pos >= 0 and len(self.playlist) > 0:
                l = self.playlist[pos]
                return dict(album = l[1],
                            length = float(l[4]),
                            title = l[3],
                            meta = self.player.prop_stream_pos,
                            __id__ = l[5],
                            artist = l[1])
        except:
            return None

    selected = property(_get_selected)

    @property
    def position(self):
        return self.player.prop_stream_pos

    @property
    def selected_uri(self):
        try:
            if self._cur_song_pos < 0:
                raise Exception()
            return 'http://%s/search%s'%(self.hostname, self.playlist[self._cur_song_pos][0])
        except:
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
        af = SimpleSearchForm(True)
        af.fill()
        web.debug(self.player.selected, self.player.infos)
        yield render.player(
                af,
                self.player.selected,
                self.player.infos,
                )

    REQ_ = REQ_main # default page

    def REQ_search(self):
        try:
            i = web.input('pattern')
            if i['pattern']:
                it = self.player.fetch_playlist(i.host or 'localhost', pattern=i.pattern)
                it.next()
                web.debug('song pos', self.player._cur_song_pos)
                self.player.select(1)
                web.debug('new song pos', self.player._cur_song_pos)
        except (IndexError, KeyError):
            it = None
        finally:
            yield web.redirect('/')

        if it:
            for x in it:
                yield

    def REQ_infos(self):
        i = web.input()
        format = i.get('fmt', 'txt')

        if format == 'txt':
            yield 'current track: %s\n'%self.player._cur_song_pos
            yield 'current position: %s\n'%self.player.position
            yield 'playlist size: %s\n'%len(self.player.playlist)
            for k, v in self.player.selected.iteritems():
                yield '%s: %s\n'%(k, v)
        elif format == 'json':
            _d = self.player.selected.copy()
            _d['pls_position'] = self.player._cur_song_pos
            _d['song_position'] = self.player.position
            _d['pls_size'] = len(self.player.playlist)
            yield jdump(_d)

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

        window_iterator = (pls[i] for i in xrange(start, end))

        if format == 'txt':
            for elt in window_iterator:
                yield str(list(elt))
        elif format == 'json':
            yield jdump(list(window_iterator))

    def REQ_shuffle(self):
        self.player.shuffle()

    def REQ_pause(self):
        self.player.pause()

    def REQ_prev(self):
        self.player.select(-1)

    def REQ_next(self):
        self.player.select(1)


