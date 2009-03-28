from time import time
import sys
from zicbee.db import valid_tags
from zicbee.core import zshell
from zicbee.core.zutils import duration_tidy, parse_line, jload
from zicbee.core.config import config
from zicbee.core.debug import log, DEBUG

def do_search(out=None, host=None, edit_mode=False):
    """ Search for song, display results.
    See "help" for a more complete documentation
    """
    if host is None:
        host = config.db_host

    if ':' not in host:
        host = "%s:%s"%(host, config.default_port)

    duration = 0
    start_t = time()

    fields = list(valid_tags)
    fields.remove('filename')
    fields = tuple(fields)

    if callable(out):
        song_output = out
    elif out == 'm3u':
        def song_output(song):
            print song[0]
    elif out == 'null':
        def song_output(song): pass
    else:
        def song_output(song):
            txt = '%s :\n%s [%s, score: %s, tags: %s]'%(song[0],
                    ' - '.join(str(i) for i in song[1:4]),
                    duration_tidy(song[4]), song[5], song[6],
                    )
            print txt.decode('utf8').encode('utf8')

    num = 0
    if host is not None:
        import urllib
        params = {'pattern':' '.join(zshell.args)}
        uri = 'http://%s/db/?json=1&%s'%(host, urllib.urlencode(params))
        site = urllib.urlopen(uri)
        while True:
            line = site.readline()
            if not line:
                break
            try:
                r = jload(line)
            except:
                DEBUG()
                for l in site.readlines():
                    log.error(l.rstrip())
                raise

            song_output(r)
            duration += r[4]
            num += 1
    else:
        pat, kw = parse_line(' '.join(zshell.args))

        if edit_mode:
            search_fn = zshell.songs.u_search
        else:
            search_fn = zshell.songs.search

        for num, res in enumerate(search_fn(None, pat, **kw)):
            song_output(res)
            duration += res.length

    sys.stderr.write("# %d results in %s for a total of %s!\n"%(
            num,
            duration_tidy(time()-start_t),
            duration_tidy(duration)
            ))


