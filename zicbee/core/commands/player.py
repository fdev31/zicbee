__all__ = [
    'do_play', 'do_pause',
    'do_next', 'do_prev', 'do_shuffle',
    'do_infos', 'do_playlist',
    'do_tag', 'do_rate',
]

import urllib
from zicbee.core.zshell import args
from zicbee.core.config import config
from .search import do_search

def do_play(dbhost=config.db_host, phost=config.player_host):
    """ Play the specified pattern, same syntax as "search". """
    play_uri = 'http://%s/search?id=&host=%s&pattern=%s'%(phost, dbhost, urllib.quote(u' '.join(args)))
    urllib.urlopen(play_uri).read()

def do_infos(host=config.player_host):
    """ Show informations about currently playing song """
    play_uri = 'http://%s/infos?fmt=txt'%(host)
    site = urllib.urlopen(play_uri)
    while True:
        l = site.readline()
        if not l:
            break
        print l,

def do_playlist(host=config.player_host):
    """ Show current playing list """
    play_uri = 'http://%s/playlist?fmt=txt'%(host)
    site = urllib.urlopen(play_uri)
    while True:
        l = site.readline()
        if not l:
            break
        print l,

def do_pause(host=config.player_host):
    """ Toggle pause on player """
    play_uri = 'http://%s/pause'%(host)
    urllib.urlopen(play_uri).read()

def do_shuffle(host=config.player_host):
    """ Shuffles the playing list (results in a random playlist) """
    play_uri = 'http://%s/shuffle'%(host)
    urllib.urlopen(play_uri).read()

def do_next(host=config.player_host):
    """ Switch to next track """
    play_uri = 'http://%s/next'%(host)
    urllib.urlopen(play_uri).read()

def do_prev(host=config.player_host):
    """ Switch to previous track """
    play_uri = 'http://%s/prev'%(host)
    urllib.urlopen(play_uri).read()

def do_tag(tag, host=config.player_host):
    """ Tag selected pattern with specified rating.
    options:
        tag
        host=<db_host>
        + same pattern as "search"
    ex:
        tag::jazz,funny artist: richard cheese
        tag::rock artist: noir d
    Note multi-tagging is allowed by using "," separator (NO BLANK!)
(EXPERIMENTAL)
    """
    def song_rater(song):
        uri = song[0]
        sid = (song[0].rsplit('=', 1)[1])
        rate_uri = uri[:uri.index('/db/')+3] + '/tag/%s/%s'%(sid, tag)
        urllib.urlopen(rate_uri)

    do_search(out=song_rater, host=host, edit_mode=True)

def do_rate(rate=1, host=config.db_host):
    """ Rate selected pattern with specified rating.
    options:
        rate=1
        host=<db_host>
        + same pattern as "search"
    ex:
        rate::3:guntah.myhost.com artist: Brassens
        rate::0 title: Very bad song artist: very bad artist
(EXPERIMENTAL) """
    def song_rater(song):
        uri = song[0]
        sid = (song[0].rsplit('=', 1)[1])
        rate_uri = uri[:uri.index('/db/')+3] + '/rate/%s/%s'%(sid, rate)
        urllib.urlopen(rate_uri)

    do_search(out=song_rater, host=host, edit_mode=True)

