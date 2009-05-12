import os
import sys
import zicbee.db

class TestBuzhug(object):
    TMP_DB_NAME = 'tmpdatabase'

    def setUp(self):
        import buzhug
        self._renew_db()
        assert len(self.db.db) == 0

    def _renew_db(self):

        try:
            self.db.close()
        except AttributeError:
            pass

        db = zicbee.db.Database(self.TMP_DB_NAME)
        db.destroy()
        self.db = zicbee.db.Database(self.TMP_DB_NAME)
        print dir(self.db)

    def _populate(self):
        import random
        size = 3
        db = self.db.databases[self.TMP_DB_NAME]['handle']

        for n_art in xrange(size):
            for n_alb in xrange(size):
                for n_title in xrange(size):
                    db.insert(
                            '/foo%d'%random.randint(0, 99999999999999999),
                            u'',
                            unicode('artist %d'%n_art),
                            unicode('album %d'%n_alb),
                            unicode('title %d'%n_title),
                            random.randint(0, 10),
                            random.randint(1, 1000),
                            None, None )

        assert len(db) == size**3

    def test_tags_corruption(self):
        self._populate()
        idx = len(self.db) - 2
        tags = u',jazz,rock,pop,'
        self.db[idx].update(tags=tags)
        elt = self.db[idx]
        print elt
        assert elt.tags == tags
        assert elt.score is None

