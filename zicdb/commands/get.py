__all__ = ['do_get']

import os
import sys
import urllib
from itertools import cycle, chain
from subprocess import Popen, PIPE
from .search import do_search

def DownloadGenerator(uri):
    uri, filename = uri
    if os.path.exists(filename):
        return
    yield

    site = urllib.urlopen(uri)
    out_file = file(filename, 'w')
    BUF_SZ = 2**14
    total_size = int(site.info().getheader('Content-Length'))
    actual_size = 0
    progress_p = 0

    while True:
        data = site.read(BUF_SZ)
        if not data:
            out_file.close()
            break
        out_file.write(data)
        actual_size += len(data)
        percent = total_size/actual_size
        if percent != progress_p:
            yield percent

            progress_p = percent
        else:
            yield '.'

class Downloader(object):
    def __init__(self, nb_dl=2):
        self._nb_dl = nb_dl

    def run(self, uri_list):
        downloaders = [] # Generators to handle
        in_queue = [] # List of "TODO" uris


        def manage_ui():
            write_out = sys.stdout.write
            counter = cycle(xrange(1, self._nb_dl + 1))
            to_write = None

            from weakref import WeakKeyDictionary
            percent_memory = WeakKeyDictionary()

            yield

            nb_downloaders = len(downloaders)
            nb_downloads = 0

            activity_str = None

            while True:
                dl, to_write = (yield)
                if to_write is None:
                    break
                # Tuple: (last_non_null, current)

                if isinstance(to_write, int):
                    percent_memory[dl] = to_write
#                    actual[0] = to_write

                actual_count = counter.next()

                num_change = len(downloaders) != nb_downloaders

                if num_change:
                    nb_downloaders = len(downloaders)
                    counter = cycle(xrange(1, nb_downloaders + 1))
                    nb_downloads += 1

                if num_change or actual_count == nb_downloaders:
                    sumup = ', '.join('%3d%%'%(val if int(val)<=100 else 0)
                            for val in percent_memory.itervalues())
                    write_out(' [ %s ] %d               \r'%(sumup, nb_downloads/2))
                    # FIXME: I don't know why I must divide nb_downloads !

                sys.stdout.flush()

        ui_manager = manage_ui()
        ui_manager.next() # Start the UI manager

        def _download():
            for dl in downloaders:
                try:
                    ret = dl.next()
                except StopIteration:
                    ret = '-'
                    downloaders.remove(dl)

                ui_manager.send((dl, ret))

        for uri in chain( uri_list, in_queue ):
            if len(downloaders) < self._nb_dl:
                try:
                    dg = DownloadGenerator(uri)
                    dg.next() # start the pump
                    downloaders.append( dg )
                except StopIteration:
                    pass
            else:
                in_queue.append(uri) # Later please !
                # iterate
                _download()

        while True:
            _download()
            if len(downloaders) <= 0:
                break

        print "                         \nEnjoy ;)"

def do_get(host='localhost', out='/tmp'):
    if ':' not in host:
        host += ':9090'

    uri_list = []
    def _p(*args):
        args = args[0]
        filename = os.path.join(out, ' - '.join(a for a in args[1:4] if a) + args[0].split('?', 1)[0][-4:])
        uri = 'http://%s%s'%(host, args[0])
        uri_list.append((uri, filename))
    do_search(out=_p, host=host)
    Downloader().run(uri_list)

