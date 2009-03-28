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

def do_play(dbhost=None, phost=None):
    """ Play the specified pattern, same syntax as "search". """

    if phost is None:
        phost = config.player_host

    if dbhost is None:
        dbhost = config.db_host
    play_uri = 'http://%s/search?id=&host=%s&pattern=%s'%(phost, dbhost, urllib.quote(u' '.join(args)))
    urllib.urlopen(play_uri).read()

def do_infos(host=None):
    """ Show informations about currently playing song """
    if host is None:
        host = config.player_host
    play_uri = 'http://%s/infos?fmt=txt'%(host)
    site = urllib.urlopen(play_uri)
    while True:
        l = site.readline()
        if not l:
            break
        print l,

def do_playlist(host=None):
    """ Show current playing list """
    if host is None:
        host = config.player_host
    play_uri = 'http://%s/playlist?fmt=txt'%(host)
    site = urllib.urlopen(play_uri)
    while True:
        l = site.readline()
        if not l:
            break
        print l,

def do_pause(host=None):
    """ Toggle pause on player """
    if host is None:
        host = config.player_host
    play_uri = 'http://%s/pause'%(host)
    urllib.urlopen(play_uri).read()

def do_shuffle(host=None):
    """ Shuffles the playing list (results in a random playlist) """
    if host is None:
        host = config.player_host
    play_uri = 'http://%s/shuffle'%(host)
    urllib.urlopen(play_uri).read()

def do_next(host=None):
    """ Switch to next track """
    if host is None:
        host = config.player_host
    play_uri = 'http://%s/next'%(host)
    urllib.urlopen(play_uri).read()

def do_prev(host=None):
    """ Switch to previous track """
    if host is None:
        host = config.player_host
    play_uri = 'http://%s/prev'%(host)
    urllib.urlopen(play_uri).read()

def do_tag(tag, host=None):
    """ Tag selected pattern with specified rating.
    options:
        tag
        host=<db_host>
        + same pattern as "search"
    ex:
        tag::jazz,funny artist: richard cheese
        tag::rock artist: noir d
    NOTE:
     - without a search pattern it will tag the currently playing song
     - multi-tagging is allowed by using "," separator (NO BLANK!)

    """

    def song_tagger(song):
        uri = song[0]
        sid = (song[0].rsplit('=', 1)[1])
        tag_uri = uri[:uri.index('/db/')+3] + '/tag/%s/%s'%(sid, tag)
        urllib.urlopen(tag_uri)

    if host is None:
        host = config.player_host

    if args:
        do_search(out=song_tagger, host=host, edit_mode=True)
    else:
        tag_uri = 'http://%s/tag/%s'%(host, tag)
        urllib.urlopen(tag_uri)

def do_rate(rate=1, host=None):
    """ Rate selected pattern with specified rating.
    options:
        rate=1
        host=<db_host if pattern given, else defaults to player host to tag current song>
        + same pattern as "search" (optionnal)
    ex:
        rate::3:guntah.myhost.com artist: Brassens
        rate::0 title: Very bad song artist: very bad artist
     NOTE: without a search pattern it will rate the currently playing song
        """

    def song_rater(song):
        uri = song[0]
        sid = (song[0].rsplit('=', 1)[1])
        rate_uri = uri[:uri.index('/db/')+3] + '/rate/%s/%s'%(sid, rate)
        urllib.urlopen(rate_uri)

    if args:
        do_search(out=song_rater, host=host or config.db_host, edit_mode=True)
    else:
        rate_uri = 'http://%s/rate/%s'%(host or config.player_host, rate)
        urllib.urlopen(rate_uri)


