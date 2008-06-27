# vim: et ts=4 sw=4

import web
from pkg_resources import resource_filename
from zicbee.core.zutils import compact_int, jdump, parse_line, uncompact_int, DEBUG

web.internalerror = web.debugerror

# Set default headers & go to templates directory
web.ctx.headers = [('Content-Type', 'text/html; charset=utf-8')]
render = web.template.render(resource_filename('zicbee.ui.web', 'web_templates'))

from zicbee.player.playerlogic import  PlayerCtl

SimpleSearchForm = web.form.Form(
        web.form.Hidden('id'),
        web.form.Hidden('host', value='localhost'),
        web.form.Textbox('pattern'),
        web.form.Checkbox('m3u'),
        )

class webplayer:
    player = PlayerCtl()

    GET = web.autodelegate('REQ_')
    lastlog = []

    def REQ_main(self):
        af = SimpleSearchForm(True)
        af.fill()
        yield render.player(
                af,
                self.player.selected,
                self.player.infos,
                )

    REQ_ = REQ_main # default page

    def REQ_search(self):
        yield
        web.debug('SEARCH')
        i = web.input('pattern')
        if i.get('pattern'):
            it = self.player.fetch_playlist(i.host or 'localhost', pattern=i.pattern)
            it.next()
            self.player.select(1)
        else:
            it = None
        web.redirect('/player/main')
        if it:
            for x in it:
                yield x

    def REQ_infos(self):
        i = web.input()
        format = i.get('fmt', 'txt')

        if format == 'txt':
            yield 'current track: %s\n'%self.player._cur_song_pos
            yield 'current position: %s\n'%self.player._position
            yield 'playlist size: %s\n'%len(self.player.playlist)
            for k, v in self.player.selected.iteritems():
                yield '%s: %s\n'%(k, v)
        elif format == 'json':
            _d = self.player.selected.copy()
            _d['pls_position'] = self.player._cur_song_pos
            _d['song_position'] = self.player._position
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


