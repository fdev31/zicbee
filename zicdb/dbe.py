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
        self._db_dir = os.path.join(DB_DIR, name)
        self._init()
        self._open()

    def _init(self):
        self.db = buzhug.Base(self._db_dir)
        self.search = self.db.select
        self.destroy = self.db.destroy

    def _open(self, db=None):
        if db is None:
            db = self.db
        db.create(
                ('filename', str),
                ('genre', unicode),
                ('artist', unicode),
                ('album', unicode),
                ('title', unicode),
                ('track', int),
                ('length', int),
                mode='open'
                )

    def __len__(self):
        return len(self.db)

    def dump_archive(self, filename):
        self.db.cleanup()
        from tarfile import TarFile
        tar = TarFile.open(filename, 'w:bz2')
        prefix_sz = len(self._db_dir)

        for root, dirs, files in os.walk(self._db_dir):
            short_root = root[prefix_sz:]
            for fname in files:
                fd = file(os.path.join(root, fname))
                ti = tar.gettarinfo(arcname=os.path.join(short_root, fname), fileobj=fd)
                tar.addfile(ti, fileobj=fd)
        tar.close()

    def merge(self, directory=None, archive=None, no_dups=True):
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
                                yield '0'
                            self.db.insert(**data)

        if  archive is not None:
            from tarfile import TarFile
            from tempfile import mkdtemp
            from shutil import rmtree
            tar = TarFile.open(archive)
            tmp = mkdtemp()
            try:
                # Extract archive to disk
                buf_size = 2**16
                for ti in tar.getmembers():
                    out_fname = os.path.join(tmp, ti.name)
                    in_fd = tar.extractfile(ti)
                    out_fd = file(out_fname, 'w')
                    while True:
                        data = in_fd.read(buf_size)
                        if not data:
                            break
                        out_fd.write(data)

                    out_fd.close()

                # Do the buzhug part
                tmp_db = buzhug.Base(tmp)
                self._open(tmp_db)

                for alien_entry in tmp_db:
                    if alien_entry not in self.db:
                        entry_dict = dict( (f,unicode(getattr(alien_entry,f), 'utf8')) for f in alien_entry.fields if f[0] != '_')
                        print alien_entry
                        print entry_dict
                        if no_dups and self.db.select(artist=entry_dict['artist']):
                            continue
                        self.db.insert(**entry_dict)
            finally:
                rmtree(tmp, ignore_errors=True)

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

