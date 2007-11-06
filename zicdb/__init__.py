# Syntax:
# vim: et ts=4 sw=4
# ./run.py search #shak# in '@filename@L' and #but# in '@filename@L'

import os
DB_DIR='~/.zicdb'

def filter_dict(data):
    try:
        data['track'] = data.pop('tracknumber')
    except KeyError: pass
    for k, v in data.items():
        if k not in ('genre', 'artist', 'album', 'title', 'track', 'filename', 'length'):
            del data[k]
        else:
            if isinstance(v, (list, tuple)):
                data[k] = v[0]
        track_val = data.get('track')
        if track_val is not None:
            if isinstance(track_val, (list, tuple)):
                track_val = track_val[0]
            data['track'] = int(track_val)

    for k in ('genre', 'artist', 'album', 'title'):
        if data.get(k) is None:
            data[k] = u''
    return data

def startup(action, *args):

    # Open DB
    import buzhug
    db_dir = os.path.expanduser(DB_DIR)
    try:
        os.mkdir(db_dir)
    except:
        pass
    finally:
        songs = buzhug.Base(os.path.join(db_dir, 'songs'))
        songs.create(
                ('filename', str),
                ('genre', unicode),
                ('artist', unicode),
                ('album', unicode),
                ('title', unicode),
                ('track', int),
                ('length', int),
                mode='open'
                )

    # Chose an action
    if action == 'scan':
        from mutagen import File
        from time import time
        import sys

        start_t = time()
        for path in args:
            for root, dirs, files in os.walk(path):
                for fname in files:
                    if fname[-4:].lower() in ('.ogg', '.mp3', '.mp4', '.aac', '.vqf', '.wmv', '.wma', '.m4a'):
                        fullpath = os.path.join(root, fname)
                        try:
                            tags = File(fullpath)
                        except Exception:
                            tags = None

                        if not tags:
                            print "E",
                            continue
                        data = filter_dict(dict(tags))
                        data['filename'] = fullpath
                        data['length'] = int(tags.info.length+0.5)
                        print ".",
                        songs.insert(**data)
                        sys.stdout.flush()
        elapsed = time() - start_t
        print "Done!"
        songs.commit()
        print "Processed %d songs in %.2fs. (%.2f/s.)"%( len(songs), elapsed, len(songs)/elapsed)

    elif action == 'search':
        condition = ' '.join(args).replace('#', "'").replace('@L', '.lower()').replace('@', 's.') or 'True'
        print "Condition", condition
        results = (s for s in songs if eval(condition))
        for res in results:
            print ' '.join('%s: %s'%(f, getattr(res, f)) for f in res.fields if f[0] != '_')
    elif action == 'reset':
        import shutil
        print "Database cleared!"
        shutil.rmtree(db_dir, ignore_errors=True)
    else:
        print "Actions: scan, search, reset"


