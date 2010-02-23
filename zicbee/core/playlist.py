__all__ = ['Playlist', 'EndOfPlaylist']

import random # shuffle
import web
from zicbee.core.httpdb import web, WEB_FIELDS
from zicbee_lib.debug import DEBUG
from zicbee_lib.formats import compact_int

class EndOfPlaylist(Exception): pass

class Playlist(list):
    """ A playlist class
    """

    def __init__(self, *args):
        list.__init__(self, *args)
        self.pos = -1
        self.sense = 1

    def __delitem__(self, slc):
        """ Deletes an entry (int and slices are supported) """
        self.__update_position(slc)
        try:
            idx = int(slc)
        except TypeError:
            # slice
            idx = slc.start

        if idx < self.pos:
            self.pos -= 1

        return list.__delitem__(self, slc)

    def __setitem__(self, slc, val):
        self.__update_position(slc)
        return list.__setitem__(self, slc, val)

    def __update_position(self, start, stop=None):

        if stop is None:
            try:
                start = int(start)
            except TypeError:
                try:
                    stop = start[1]
                    start = start[0]
                except TypeError:
                    # slice
                    stop = start.stop
                    start = start.start
            else:
                stop = start

        if start < self.pos:
            # increment
            self.pos += 1
        else:
            if start < self.pos and stop < self.pos:
                # increment stop-start
                self.pos += stop-start
            elif start < self.pos < stop:
                # reset position to beginning of slice
                self.pos = 0 if self.playlist else -1

    def insert(self, idx, obj):
        """ Inserts an object at a position, behaves like `list.insert`.
        """
        self.__update_position(idx)
        list.insert(self, idx, obj)

    def inject(self, data, position=None):
        """ inject a song or a range of songs,
        keeps the position if possible """
        if hasattr(data, '__getitem__') and isinstance(data[0], basestring):
            data = [data]
        elif isinstance(data, slice):
            data = self[data]

        p = self.pos+1 if position is None else position

        self.__update_position(p)

        self[p:p] = data

    def extend(self, data, idx=None):
        """ See `list.extend` """
        if idx is None:
            idx = len(self)
        self.__update_position(idx, idx+len(data))
        list.extend(self, data)

    def replace(self, any_iterable):
        current = self.selected
        if current:
            self.pop(self.pos)
        self[:] = any_iterable
        if current:
            self.insert(0, current)
            self.pos = 0
        else:
            self.pos = -1

    def shuffle(self):
        if len(self) == 0:
            return
        current = self.selected
        if current:
            self.pop(self.pos)
        random.shuffle(self)
        if current:
            self.insert(0, current)
            self.pos = 0
        else:
            self.pos = -1

    def clear(self):
        self[:] = []
        self.pos = -1

    def _selected(self, p=None):
        if not p:
            p = self.pos

        if p == -1 or len(self) == 0:
            return None
        try:
            return self[p]
        except IndexError:
            DEBUG()

    selected = property(_selected)

    @property
    def sibling(self):
        return self._selected_dict(self.pos+self.sense)

    def _selected_dict(self, pos=None):
        sel = self._selected(pos)

        web.debug('SELECTED: %r'%sel)
        if not sel:
            return dict()

        d = dict(zip(['uri']+WEB_FIELDS, sel))

        try:
            d['length'] = int(d.get('length') or 0)
            d['score'] = int(d.get('score') or 0)
            d['tags'] = d.get('tags') or u''
            d['pls_position'] = self.pos
            d['pls_size'] = len(self)
        except ValueError, e:
            # !!corrupted data!!
            web.debug('data corruption: %s'%e)
            return dict()
        except Exception:
            DEBUG()
        try:
            d['id'] = compact_int(d.pop('__id__'))
        except KeyError:
            pass
        return d

    selected_dict = property(_selected_dict)

    def move(self, steps):
        self.pos += steps
        self.sense = steps
        if self.pos >= len(self):
            self.pos = -1
            raise EndOfPlaylist()
        elif self.pos < -1:
            self.pos = -1

