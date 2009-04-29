import heapq
import itertools
from zicbee.core import zshell

def do_find_dups(wpt=None, ar=None):
    """
    Find duplicates (WIP)
    Parameters:
        wpt: wrong positive threshold (ceil to not reach), default == auto
        ar: auto remove (ask for directory deletion), the smallest directory always wins
    """
    hash_dict = dict()

    cnt = itertools.count()
    total_cnt = itertools.count()

    if wpt is None:
        wpt = min(1000, len(zshell.songs)/60) # take untaged/corrupted data into account

    for num, footprint in zshell.songs.get_hash_iterator():
        if footprint not in hash_dict:
            hash_dict[footprint] = [num]
        else:
            hash_dict[footprint].append(num)

    if ar:
        print '#!/bin/sh'
        for m in (matches for num, matches in hash_dict.iteritems() if 1 < len(matches) < wpt):
            h = []
            cnt.next()
            for num in m:
                total_cnt.next()
                song = zshell.songs[num]
                heapq.heappush(h,
                        (len(song.filename), song))

            for nb, other in h:
                if other != h[-1][1]:
                    print "rm '%s'"%(other.filename.replace("'", r"\'"))
                else:
                    print "# kept %s"%other.filename
    else:
        for m in (matches for num, matches in hash_dict.iteritems() if 1 < len(matches) < wpt):
            print "#", cnt.next()
            for num in m:
                total_cnt.next()
                print "%d: %s"%(num, zshell.songs[num].filename)
    print "# %d songs are duplicates."%(total_cnt.next()-cnt.next())
