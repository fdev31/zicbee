__all__ = [
    'do_play', 'do_pause',
    'do_next', 'do_prev', 'do_shuffle',
    'do_infos', 'do_playlist',
    'do_tag', 'do_rate',
]

import urllib
from zicbee.core.zshell import args

def do_play(host='localhost:9090'):
    """ Play the specified pattern, same syntax as "search". """
    play_uri = 'http://%s/search?id=&host=%s&pattern=%s'%(host, host, urllib.quote(u' '.join(args)))
    urllib.urlopen(play_uri).read()

def do_infos(host='localhost:9090'):
    """ Show informations about currently playing song """
    play_uri = 'http://%s/infos?fmt=txt'%(host)
    site = urllib.urlopen(play_uri)
    while True:
        l = site.readline()
        if not l:
            break
        print l,

def do_playlist(host='localhost:9090'):
    """ Show current playing list """
    play_uri = 'http://%s/playlist?fmt=txt'%(host)
    site = urllib.urlopen(play_uri)
    while True:
        l = site.readline()
        if not l:
            break
        print l,

def do_pause(host='localhost:9090'):
    """ Toggle pause on player """
    play_uri = 'http://%s/pause'%(host)
    urllib.urlopen(play_uri).read()

def do_shuffle(host='localhost:9090'):
    """ Shuffles the playing list (results in a random playlist) """
    play_uri = 'http://%s/shuffle'%(host)
    urllib.urlopen(play_uri).read()

def do_next(host='localhost:9090'):
    """ Switch to next track """
    play_uri = 'http://%s/next'%(host)
    urllib.urlopen(play_uri).read()

def do_prev(host='localhost:9090'):
    """ Switch to previous track """
    play_uri = 'http://%s/prev'%(host)
    urllib.urlopen(play_uri).read()

def do_tag(tag, host='localhost:9090'):
    """ Tag current song with specified tag name (EXPERIMENTAL) """
    def song_rater(song):
        uri = song[0]
        sid = (song[0].rsplit('=', 1)[1])
        rate_uri = uri[:uri.index('/db/')+3] + '/tag/%s/%s'%(sid, tag)
        urllib.urlopen(rate_uri)

    do_search(out=song_rater, host=host, edit_mode=True)

def do_rate(rate=1, host='localhost:9090'):
    """ Rate current song with specified rating (EXPERIMENTAL) """
    def song_rater(song):
        uri = song[0]
        sid = (song[0].rsplit('=', 1)[1])
        rate_uri = uri[:uri.index('/db/')+3] + '/rate/%s/%s'%(sid, rate)
        urllib.urlopen(rate_uri)

    do_search(out=song_rater, host=host, edit_mode=True)

