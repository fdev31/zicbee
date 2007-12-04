__all__ = ['Database', 'valid_tags']

import os
import buzhug

DB_DIR = os.path.expanduser(os.getenv('ZICDB_PATH') or '~/.zicdb')

try: # Ensure personal dir exists
    os.mkdir(DB_DIR)
except:
    pass

valid_ext = ('.ogg','.mp3', '.mp4',
    '.aac', '.vqf', '.wmv', '.wma', '.m4a', 'asf')

valid_tags = (
        'genre',
        'artist',
        'album',
        'title',
        'track',
        'filename',
        'length')

filters_dict = dict(
        track = ('TRCK', 'tracknumber'),
        title = ('Title', 'TITLE', 'TIT1', 'TIT2'),
        artist = ('Author', 'author', 'AUTHOR', 'TPE1'),
        )


class Database(object):
    def __init__(self, name):
        """ Open/Create a database """
        self.db = buzhug.Base(os.path.join(DB_DIR, name))
        self.db.create(
                ('filename', str),
                ('genre', unicode),
                ('artist', unicode),
                ('album', unicode),
                ('title', unicode),
                ('track', int),
                ('length', int),
                mode='open'
                )

        self.search = self.db.select
        self.destroy = self.db.destroy

    def __len__(self):
        return len(self.db)

    def merge(self, directory=None, no_dups=True):
        """ Merge informations from files in specified directory """

        try:
            EasyID3
        except NameError:
            from mutagen import File
            from mutagen.mp3 import MP3
            from mutagen.easyid3 import EasyID3

        if directory is not None:
            for root, dirs, files in os.walk(directory):
                for fname in files:
                    if fname[-4:].lower() in valid_ext:
                        fullpath = os.path.join(root, fname)
                        if no_dups and self.db.select(filename=fullpath):
                            yield 'I'
                        else:
                            try:
                                tags = File(fullpath)
                            except Exception:
                                tags = None

                            if not tags:
                                yield "E"
                                continue
                            # Do it before tags is changed !
                            length = int(tags.info.length+0.5)
                            if isinstance(tags, MP3):
                                tags = EasyID3(fullpath)
                            data = filter_dict(dict(tags))
                            data['filename'] = fullpath
                            data['length'] = length
                            if data.get('title') and data.get('artist'):
                                yield '.'
                            else:
                                yield '0',
                            self.db.insert(**data)
        self.db.commit()



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

    if data.get('genre') == u'12':
        data['genre'] = u''

    return data

