# vim: et ts=4 sw=4
from __future__ import with_statement

import difflib
import urllib
from zicbee.core.httpdb import render, web
from zicbee.core.player import PlayerCtl
from zicbee.utils import notify
from zicbee_lib.config import config
from zicbee_lib.debug import DEBUG
from zicbee_lib.formats import dump_data_as_text, jdump, get_index_or_slice

SimpleSearchForm = web.form.Form(
        web.form.Hidden('id'),
        web.form.Textbox('host', description='Search host', value='localhost'),
        web.form.Textbox('pattern', description='Search pattern'),
#        web.form.Textbox('tempname', description='Temporary name'),
        )

TagForm = web.form.Form(web.form.Textbox('tag', description='Set tag'))
ScoreForm = web.form.Form(web.form.Dropdown('score', range(11), description='Set rate'))

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
        it = ('' for i in xrange(1))
        try:

            i = web.input()
            tempname = False

            if i.get('pattern', '').startswith('http'):
                # http pattern
                try:
                    uri = i.pattern.split()[0]
                    hostname = uri.split("/", 3)[2]
                    song_id = uri.rsplit('=', 1)[1]
                    it = self.player.fetch_playlist(hostname, pattern=u'id: %s pls: +#'%song_id)
                except:
                    # hardcore injection
                    pls = self.player.playlist

                    pls.inject( [str(uri), u'No artist', u'No album', 'External stream', 1000, None, None, 0] )
            else:
                # standard pattern
                it = self.player.fetch_playlist(i.get('host', 'localhost'), pattern=i.pattern)
            it.next()

        except (IndexError, KeyError):
            DEBUG(False)
        except Exception, e:
            DEBUG()
        finally:
            return it

    def REQ_delete(self):
        i = web.input()
        try:
            i = get_index_or_slice(i['idx'])
        except ValueError:
            self.player.delete_playlist(i['idx'])
        else:
            self.player.delete_entry(i)

        return ''

    def REQ_move(self):
        i = web.input()
        start = get_index_or_slice(i['s'])
        self.player.move_entry(start, int(i['d']))
        return ''

    def REQ_swap(self):
        i = web.input()
        self.player.swap_entry(int(i['i1']), int(i['i2']))
        return ''

    def REQ_append(self):
        self.player.playlist_change('append', web.input()['name'])
        return ''

    def REQ_copy(self):
        try:
            self.player.playlist_change('copy', web.input()['name'])
            return ''
        except KeyError:
            return 'Not Found'

    def REQ_inject(self):
        try:
            self.player.playlist_change('inject', web.input()['name'])
            return ''
        except KeyError:
            return 'Not Found'

    def REQ_save(self):
        name = web.input()['name']
        self.player.save(name)
        return 'saved %s'%name

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

    def REQ_playlists(self):
        return '\n'.join(self.player._named_playlists.keys())

    def REQ_playlist(self):
        i = web.input()
        pls = self.player.playlist

        start = int(i.get('start', 0))

        format = i.get('fmt', 'txt')
        if start < 0:
            start = len(pls) + start

        if i.get('res'):
            r = int(i.res)
            if r > 0:
                end = start + r
            else:
                # compute from end
                end = len(pls) + r
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
        notify('Zap!', icon='media-previous', timeout=200)
        return self.player.select(-1) or ''

    def REQ_next(self):
        notify('Zap!', icon='media-next', timeout=200)
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

