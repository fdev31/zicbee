from __future__ import with_statement
import ao
from pyglet.media import avbin
from Queue import Queue
from threading import Thread, Lock
from time import sleep, time

class SoundFeeder(Thread):
    def __init__(self, play_fn, filename):
        Thread.__init__(self)
        self.running = False
        self._fn = play_fn
        self._lock = Lock()
        self.filename = filename
        self.setDaemon(True)
        self.paused = False

    def run(self):
        self._src = avbin.AVbinSource(self.filename)
        self.seek = self._src._seek
        self.running = True
        lock = self._lock

        while self.running:
            if self.paused:
                sleep(0.2)
            else:
                try:
                    data = self._src._get_audio_data(65000)
                    assert data is not None
                except:
                    self.stop()
                else:
                    self._fn(data.data)

    def __del__(self):
        self.stop()

    def stop(self):
        self.running = False

class SoundPlayer(object):
    def __init__(self, backend=0):
        self._audio_out = ao.AudioDevice(backend)
        self._feeder = None

    running = property(lambda self: self._feeder.running if self._feeder else False)

    def stop(self):
        self._running = False

    def loadfile(self, filename, autoplay=True):
        if self._feeder:
            self._feeder.stop()
            self._feeder.join()

        self._feeder = SoundFeeder(self._audio_out.play, filename)

        if autoplay:
            print "Starting..."
            self._feeder.start()

    def volume(self, *args):
        print "Volume not managed yet"
        return 0

    prop_volume = property(volume)

    def get_time_pos(self):
        if self._feeder:
            return self._feeder._src._packet.timestamp/1000000.0
        else:
            return 0

    def seek(self, pos, t):
        self._feeder.seek(pos)

    def pause(self):
        if self._feeder.paused:
            self._feeder.paused = False
        else:
            self._feeder.paused = True

