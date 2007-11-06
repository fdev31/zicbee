# Syntax:
# vim: et ts=4 sw=4
# ./run.py search #shak# in '@filename@L' and #but# in '@filename@L'

import os
DB_DIR = os.getenv('ZICDB_PATH') or '~/.zicdb'

valid_ext = ('.ogg','.mp3', '.mp4',
    '.aac', '.vqf', '.wmv', '.wma', '.m4a', 'asf'):

filters_dict = dict(
        track = ('TRCK', 'tracknumber'),
        title = ('Title', 'TITLE', 'TIT1', 'TIT2'),
        artist = ('Author', 'author', 'AUTHOR', 'TPE1'),
        )

valid_tags = (
        'genre',
        'artist',
        'album',
        'title',
        'track',
        'filename',
        'length')

def filter_dict(data):
    for good_tag, bad_tags in filters_dict.iteritems():
        for bad_tag in bad_tags:
            if good_tag in data:
                break
            if data.get(bad_tag) is not None:
                data[good_tag] = data[bad_tag]

    for k, v in data.items():
        if k not in valid_tags:
            del data[k]
        else:
            if isinstance(v, (list, tuple)):
                data[k] = v[0]
        track_val = data.get('track')
        if track_val is not None:
            if isinstance(track_val, (list, tuple)):
                track_val = track_val[0]
            if not isinstance(track_val, int):
                track_val = int(track_val.replace('-', '/').split('/')[0])
            data['track'] = track_val

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
        from mutagen.mp3 import MP3
        from mutagen.easyid3 import EasyID3
        from time import time
        import sys

        start_t = time()
        for path in args:
            for root, dirs, files in os.walk(path):
                for fname in files:
                    if fname[-4:].lower() in valid_ext:
                        fullpath = os.path.join(root, fname)
                        print fullpath
                        try:
                            tags = File(fullpath)
                        except Exception:
                            tags = None

                        if not tags:
                            print "E",
                            continue
                        # Do it before tags is changed !
                        length = int(tags.info.length+0.5)
                        if isinstance(tags, MP3):
                            tags = EasyID3(fullpath)
                        data = filter_dict(dict(tags))
                        data['filename'] = fullpath
                        data['length'] = length
                        if 'title' in data and 'artist' in data:
                            print '.',
                        else:
                            print '0',
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


