from time import time
import sys
from zicbee.db import valid_tags
from zicbee.core import zshell
from zicbee_lib.formats import duration_tidy, jload
from zicbee.core.parser import parse_line
from zicbee_lib.config import config
from zicbee_lib.debug import log, DEBUG

def do_search(out=None, edit_mode=False):
    """ Search for song, display results.
    out can be "m3u" or "null", defaults to human-readable
    """

    duration = 0
    start_t = time()

    fields = list(valid_tags)
    fields.remove('filename')
    fields = tuple(fields)

    if callable(out):
        song_output = out
    elif out == 'm3u':
        print "#EXTM3U"
        def song_output(song):
            print u"#EXTINF:%d,%s - %s\n%s"%(song.length, song.artist, song.title, song.filename)
    elif out == 'null':
        def song_output(song): pass
    else:
        def song_output(song):
            txt = '%s :\n%s [%s, score: %s, tags: %s]'%(song.filename,
                    '%s - %s - %s'%(song.artist, song.album, song.title),
                    duration_tidy(song.length), song.score, song.tags,
                    )
            print txt.decode('utf8').encode('utf8')

    pat, kw = parse_line(' '.join(zshell.args))

    if edit_mode:
        search_fn = zshell.songs.u_search
    else:
        search_fn = zshell.songs.search

    num = 0
    for num, res in enumerate(search_fn(None, pat, **kw)):
        song_output(res)
        duration += res.length

    sys.stderr.write("# %d results in %s for a total of %s!\n"%(
            num,
            duration_tidy(time()-start_t),
            duration_tidy(duration)
            ))


