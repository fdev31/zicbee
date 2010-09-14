__all__ = ['Databae', 'valid_tags']
# vim: ts=4 sw=4 et

import os
import buzhug
from itertools import chain
from zicbee_lib.config import DB_DIR, media_config
import re
import time

try:
    required_buzhug = [1, 5]
    assert [int(d) for d in buzhug.version.split('.')] >= required_buzhug
except AssertionError:
    raise SystemExit('Wrong buzhug installed, please install at least version %s'%('.'.join(required_buzhug)))


valid_ext = media_config.keys()

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

track_re = re.compile('.*?(\d+)')

filters_dict = dict(
        track = ('TRCK', 'tracknumber', u'WM/Track', "WM/TrackNumber" 'trkn'),
        title = ('Title', 'TITLE', 'TIT1', 'TIT2', '\xa9nam'),
        artist = ('Author', 'author', 'AUTHOR', 'TPE1', '\xa9ART', '\xa9aART', 'WM/Composer', 'WM/Writer', 'TCOM', 'TOPE', 'album artist'),
        album = (u'WM/AlbumTitle', 'TALB', 'debut album', '\xa9alb'),
        genre = ('\xa9gen', u'WM/Genre'),
        # disc = ('disknumber', "WM/PartOfSet"),
        # rating = ('Rating',),
        )


def checkdb(base_fn):
    return base_fn
    def _mkdec(somefn):
        def _auto_db_check(self, *args, **kw):
            if self.databases is not None:
                self._create()
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
        self.databases = dict()
        self.db_name = name
        for name in name.split(','):
            p = os.path.join(DB_DIR, name)
            h = self._create(p)
            self.databases[name] = dict(
                    path = p,
                    handle = h,
                    )

    def add_error(self, message):
        f = getattr(self, '_error_fd', None)
        if not f:
            f = self._error_fd = open( os.path.join(DB_DIR, 'scan.log'), 'a+')
            self._error_fd.write("-- Errors scanning %s on %s --\n"%(self.db_name, time.asctime()))
        f.write(message+'\n')

    @property
    def artists(self):
        return set(r.artist for r in self.search(['artist']))

    @property
    def albums(self):
        return set(r.album for r in self.search(['album']))

    @property
    def genres(self):
        return set(r.genre for r in self.search(['genre']))

    def _create(self, db_name=None):
        if isinstance(db_name, basestring):
            databases = [ buzhug.Base(db_name) ]
        elif isinstance(db_name, buzhug.Base):
            databases = [ db_name ]
        else:
            for name, db in self._dbs_iter():
                self.databases[name] = buzhug.Base(db_name)
            databases = self.databases.values()

        kw = dict(mode='open')

        for db in databases:
            db.create(*self.DB_SCHEME, **kw)
        if databases is not self.databases and len(databases) == 1:
            return databases[0]
        return databases

    def _dbs_iter(self):
        return self.databases.iteritems()

    def close(self):
        for name, db in self._dbs_iter():
            db['handle'].close()

    def destroy(self):
        for name, db in self._dbs_iter():
            db['handle'].destroy()

    def commit(self):
        for name, db in self._dbs_iter():
            db['handle'].commit()

    def cleanup(self):
        for name, db in self._dbs_iter():
            db['handle'].cleanup()

    def update(self, record, **kw):
        for name, db in self._dbs_iter():
            db['handle'].update(record, **kw)

    @checkdb
    def __getitem__(self, item):
        for name, db in self._dbs_iter():
            db = db['handle']
            try:
                return db[item]
            except:
                continue

    @checkdb
    def __len__(self):
        return sum(len(db['handle']) for name, db in self._dbs_iter())

    @checkdb
    def search(self, *args, **kw):
        return chain( *(db['handle'].select(*args, **kw) for name, db in self._dbs_iter()) )

    @checkdb
    def u_search(self, *args, **kw):
        return chain( db['handle'].select_for_update(*args, **kw) for name, db in self._dbs_iter() )

    @checkdb
    def dump_archive(self, filename):
        """ dump a bz2 archive from this database """
        use_suffixes = len(self.databases) > 1
        self.cleanup()
        from tarfile import TarFile

        for name, db in self._dbs_iter():
            tar = TarFile.open('%s%s'%(filename, '_%s'%name if use_suffixes else ''), 'w:bz2')
            prefix_sz = len(db['path'])

            for root, dirs, files in os.walk(db['path']):
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
    def merge(self, db_name, directory=None, archive=None, no_dups=True, update=False):
        """ Merge informations from files in specified directory or archive """
        # TODO: handle no_dups to show merge of tags while adding new

        try:
            EasyID3
        except NameError:
            from mutagen import File
            from mutagen.mp3 import MP3
            from mutagen.easyid3 import EasyID3

        us_prefix = None

        print "Building data sets..."
        db_filenames = {}
        for name, db in self._dbs_iter():
            db = db['handle']
            db_filenames.update( (i.filename, i) for i in db if i.filename.startswith(directory) )

        db = self.databases[db_name]['handle']

        # Directory handling
        filenames = []
        if directory is not None and not us_prefix:
            for root, dirs, files in os.walk(directory):
                for fname in files:
                    if fname.rsplit('.', 1)[-1].lower() in valid_ext:
                        filenames.append( os.path.join(root, fname) )

        filenames = set(filenames)
        db_set = set(db_filenames.iterkeys())

        # remove old files
        print "\nRemoving..."
        for removed in db_set.difference(filenames):
            db.delete(db_filenames[removed])

        # add new files
        print "\nAdding..."
        for fullpath in filenames.difference(db_set):
            tags = None

            try:
                tags = File(fullpath)
            except Exception, e:
                print 'Error reading %s: %s'%(fullpath, e)
                yield "E"
                continue

            if tags:
                # Do it before tags is changed !
                length = int(tags.info.length+0.5)
                if isinstance(tags, MP3):
                    tags = EasyID3(fullpath)
                tags = dict(tags)
            else:
                length = 0

                name = unicode(fname, 'utf-8', 'replace')
                album = unicode(os.path.split(root)[-1], 'utf-8', 'replace')
                tags = {'title': name, 'album': album, 'artist': name}

            data = filter_dict(tags)
            data['filename'] = fullpath
            data['length'] = length
            if data.get('title') and data.get('artist'):
                yield '.'
            else:
                yield '0'
            try:
                db.insert(**data)
            except:
                import pdb; pdb.set_trace()

        if update:
            # Update tags
            print "\nUpdating..."
            for fullpath in filenames.intersection(db_set):
                tags = None

                try:
                    tags = File(fullpath)
                except Exception, e:
                    self.add_error("%s | %s | %r"%(db_name, fullpath, e))
                    yield "E"
                    continue

                if tags:
                    # Do it before tags is changed !
                    length = int(tags.info.length+0.5)
                    if isinstance(tags, MP3):
                        tags = EasyID3(fullpath)
                    tags = dict(tags)
                else:
                    length = 0

                    name = unicode(fname, 'utf-8', 'replace')
                    album = unicode(os.path.split(root)[-1], 'utf-8', 'replace')
                    tags = {'title': name, 'album': album, 'artist': name}

                data = filter_dict(tags)

                data['filename'] = fullpath
                data['length'] = length
                if data.get('title') and data.get('artist'):
                    yield '.'
                else:
                    yield '0'
                try:
                    song = db_filenames[fullpath]
                    #if any(data[k] != getattr(song, k) for k in data.keys()): # Looks useless
                    db.update(song, **data)
                except:
                    import pdb; pdb.set_trace()

        print "\nCleaning up..."
        self.cleanup()
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
                tmp_db = self._create(tmp)

                for alien_entry in tmp_db:
                    if alien_entry not in db:
                        entry_dict = dict()
                        for f in alien_entry.fields:
                            if f[0] == '_':
                                continue
                            val = getattr(alien_entry, f)
                            if isinstance(val, str) and f != 'filename':
                                val = unicode(val)
                            entry_dict[f] = val
                        db.insert(**entry_dict)
                        yield '.'
            finally:
                rmtree(tmp, ignore_errors=True)

        db.commit()

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

    for k in ('genre', 'artist', 'album', 'title'):
        d = data.get(k)
        if d is None:
            data[k] = u''
        elif not isinstance(d, unicode):
            data[k] = unicode(d)
        data[k] = data[k].split('\n')[0].replace(os.path.sep, '_').strip()

    if data.get('genre') == u'12':
        data['genre'] = u''


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
            if not iksinstance(track_val, int):
                track_val = int( track_re.match(track_val).groups()[0] )
        except:
            print "Unable to get track for", repr(track_val)
            data['track'] = None
        else:
            try:
                data['track'] = int(track_val.strip())
            except:
                data['track'] = None
        if not data['title'] and data['track']:
            data['title'] = unicode(track_val)

    return data

