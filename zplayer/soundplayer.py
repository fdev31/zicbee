from __future__ import with_statement

import pyglet
pyglet.options['audio'] = ('alsa', 'directsound', 'openal', 'silent')
from pyglet import media
from thread import start_new_thread
from time import sleep

def _eventdispatcher():
    while True:
        media.dispatch_events()
        sleep(0.01)

start_new_thread(_eventdispatcher, tuple())

class SoundPlayer(object):
    def __init__(self):
        self._player = None
        self._source = None

    def loadfile(self, filename, autoplay=True):
        if self._player:
            self._player.stop()
        self._source = media.load(filename)

        if autoplay:
            self._player = self._source.play()

    running = property(lambda self: self._player and self._player.playing)
    starved = property(lambda self: not bool(self._player._next_audio_data))

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

