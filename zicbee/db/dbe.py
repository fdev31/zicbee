__all__ = ['Database', 'valid_tags']
# vim: ts=4 sw=4 et

import os
import buzhug
from zicbee.core.config import DB_DIR
from zicbee.core.config import media_config

#valid_ext = ('.ogg','.mp3', '.mp4',
#    '.aac', '.vqf', '.wmv', '.wma', '.m4a', '.asf', '.oga', '.flac')

valid_ext = ['.%s'%ext for ext in media_config.keys()]

valid_tags = (
        'genre',
        'artist',
        'album',
        'title',
        'track',
        'filename',
        'score',
        'tags',
        'length')

filters_dict = dict(
        track = ('TRCK', 'tracknumber', u'WM/Track', 'trkn'),
        title = ('Title', 'TITLE', 'TIT1', 'TIT2', '\xa9nam'),
        artist = ('Author', 'author', 'AUTHOR', 'TPE1', '\xa9ART', '\xa9aART', 'WM/Composer', 'WM/Writer', 'TCOM', 'TOPE', 'album artist'),
        album = (u'WM/AlbumTitle', 'TALB', 'debut album'),
        genre = ('\xa9gen', u'WM/Genre'),
        # disc = ('disknumber',),
        # rating = ('Rating',),
        )


def checkdb(base_fn):
    return base_fn
    def _mkdec(somefn):
        def _auto_db_check(self, *args, **kw):
            if self.db is None:
                self._init()
            return somefn(self, *args, **kw)
        return _auto_db_check

    return _mkdec(base_fn)


class Database(object):

    DB_SCHEME = (
                ('filename', str),
                ('genre', unicode),
                ('artist', unicode),
                ('album', unicode),
                ('title', unicode),
                ('track', int),
                ('length', int),
                ('score', int),
                ('tags', unicode),
                )

    def __init__(self, name):
        """ Open/Create a database """
        self._db_dir = os.path.join(DB_DIR, name)
        self._init()

    def _init(self):
        self.db = buzhug.Base(self._db_dir)
        self.destroy = self.db.destroy
        self.cleanup = self.db.cleanup
        self._open()

    @checkdb
    def __getitem__(self, item):
        return self.db[item]

    @checkdb
    def __len__(self):
        return len(self.db)

    @checkdb
    def search(self, *args, **kw):
        return self.db.select(*args, **kw)

    @checkdb
    def u_search(self, *args, **kw):
        return self.db.select_for_update(*args, **kw)

    @checkdb
    def _open(self, db=None):
        if db is None:
            db = self.db
        kw = dict(mode='open')
        db.create(*self.DB_SCHEME, **kw)

    @checkdb
    def dump_archive(self, filename):
        """ dump a bz2 archive from this database """
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

    def get_hash_iterator(self):
        """ Returns an (id, hash) tuple generator """
        for item in self.search():
            yield item.__id__, '%(artist)s:%(album)s:%(title)s'%dict(
                    (k, ''.join(c for c in getattr(item, k).lower() if c != ' '))
                    if isinstance(getattr(item, k), basestring)
                    else (k, getattr(item, k))
                    for k in item.fields)

    @checkdb
    def merge(self, directory=None, archive=None, no_dups=True):
        """ Merge informations from files in specified directory or archive """
        # TODO: add auto "no_dups" style after a len() check of the db

        try:
            EasyID3
        except NameError:
            from mutagen import File
            from mutagen.mp3 import MP3
            from mutagen.easyid3 import EasyID3

        us_prefix = None

        # Avoid duplicates
        if no_dups and len(self.db):

            # user specified prefix
            if directory is None:
                try:
                    print "Example filename %s"%(self.db[0].filename)
                except IndexError:
                    pass
                finally:
                    us_prefix = raw_input('Enter prefix to remove: ')
                    if us_prefix.strip():
                        directory = us_prefix

            # Remove every file starting with that directory
            old_len = len(self.db)
            for it in (i for i in self.db if i.filename.startswith(directory)):
                self.db.delete(it)
            print "Removed %d items"%( old_len - len(self.db) )
            self.db.cleanup()

        # Directory handling
        if directory is not None and not us_prefix:
            for root, dirs, files in os.walk(directory):
                for fname in files:
                    if '.' + fname.rsplit('.', 1)[-1].lower() in valid_ext:
                        fullpath = os.path.join(root, fname)

                        try:
                            tags = File(fullpath)
                        except Exception, e:
                            print 'Error reading %s: %s'%(fullpath, e)
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
                        try:
                            self.db.insert(**data)
                        except:
                            import pdb; pdb.set_trace()

        # Archive handling
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
                        entry_dict = dict()
                        for f in alien_entry.fields:
                            if f[0] == '_':
                                continue
                            val = getattr(alien_entry, f)
                            if isinstance(val, str) and f != 'filename':
                                val = unicode(val)
                            entry_dict[f] = val
                        self.db.insert(**entry_dict)
                        yield '.'
            finally:
                rmtree(tmp, ignore_errors=True)

        self.db.commit()

def filter_dict(data):
    """ Returns a filtered given data dict """
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
            while isinstance(v, (list, tuple)):
                try:
                    v = v[0]
                except IndexError:
                    v = None
            data[k] = v
    track_val = data.get('track')
    if track_val is not None:
        try:
            track_val = unicode(track_val).strip()
        except Exception, e:
            print e
            track_val = unicode(track_val.value)
        try:
            if isinstance(track_val, (list, tuple)):
                track_val = track_val[0]
            if not isinstance(track_val, int):
                track_val = int(track_val.replace('-', ' ').replace('/', ' ').split()[0])
        except:
            print "Unable to get track for", repr(track_val)
            data['track'] = None
        else:
            try:
                data['track'] = int(track_val.strip())
            except:
                data['track'] = None

    for k in ('genre', 'artist', 'album', 'title'):
        d = data.get(k)
        if d is None:
            data[k] = u''
        elif not isinstance(d, unicode):
            data[k] = unicode(d)

    if data.get('genre') == u'12':
        data['genre'] = u''

    return data

