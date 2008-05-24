from __future__ import with_statement

import pyglet
import pyglet.media.avbin # ensure avbin is installed
pyglet.options['audio'] = ('alsa', 'directsound', 'openal', 'silent')
from thread import start_new_thread
from time import sleep

from zicbee.core.zutils import DEBUG

#_eventdispatcher = pyglet.app.run
#start_new_thread(_eventdispatcher, tuple())

class SoundPlayer(object):
    def __init__(self):
        self._player = None
        self._source = None
        self.__initialized = False

    def __setup(self):
        start_new_thread(pyglet.app.run, tuple())
        self.__initialized = True

    def loadfile(self, filename, autoplay=True):
        if self._player:
            try:
                self._player.stop()
            except ValueError:
                pass # Stream not in play list
        try:
            self._source = pyglet.media.load(filename)
        except:
            DEBUG()
        else:
            if autoplay:
                self._player = self._source.play()

        if not self.__initialized:
            self.__setup()

    running = property(lambda self: self._player and self._player.playing)
    finished = property(lambda self: not bool(self._player._sources))

    def stop(self):
        self._player.stop()

    def volume(self, val):
        self._player.volume = val /100.0

    prop_volume = property(volume)

    def get_time_pos(self):
        return (self._source and self._source._packet.timestamp/1000000.0) or 0

    def seek(self, pos, t):
        self._source._seek(pos)

    def pause(self):
        if self._player.playing:
            self._player.pause()
        else:
            self._player.play()

    def quit(self):
        if self._player:
            self._player.stop()

