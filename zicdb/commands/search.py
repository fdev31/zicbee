from time import time
from zicdb.dbe import valid_tags
from zicdb.zshell import args, songs
from zicdb.zutils import duration_tidy, parse_line

def do_search(out=None):
    duration = 0
    start_t = time()

    fields = list(valid_tags)
    fields.remove('filename')
    fields = tuple(fields)

    if out == 'm3u':
        def song_output(song):
            print song.filename
    elif out == 'null':
        def song_output(song): pass
    else:
        def song_output(song):
            txt = '%s :\n%s '%(repr(song.filename), '| '.join('%s: %s'%(f, getattr(song, f)) for f in fields if f[0] != '_' and getattr(song, f)))
            print txt.decode('utf8').encode('utf8')

    num = 0
    pat, kw = parse_line(' '.join(args))
    for num, res in enumerate(songs.search(None, pat, **kw)):
        song_output(res)
        duration += res.length

    print "# %d results in %s for a total of %s!"%(
            num,
            duration_tidy(time()-start_t),
            duration_tidy(duration)
            )


