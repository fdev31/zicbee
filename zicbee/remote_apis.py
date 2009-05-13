import sys
import urllib
import xml.etree.ElementTree as ET

class ASArtist(object):
    """ AudioScrobbler Artist object """

    def __init__(self, name):
        self.name = name.encode('utf8')
        self._base_url = 'http://ws.audioscrobbler.com/1.0/artist'

    def getSimilar(self):
        ret = []
        infos = urllib.urlopen(self._base_url+'/%s/similar.txt'%urllib.quote(self.name))
        while True:
            line = infos.readline()
            if not line: break
            if not line[0].isdigit(): break
            match, mbid, artist = line.strip().split(',',2)
            ret.append( (match,artist.decode('utf8')) )
        return ret

    def getTop(self):
        ret = []
        xmlpage = urllib.urlopen(self._base_url+'/%s/toptracks.xml'%urllib.quote(self.name)).read()
        xmlpage = ET.fromstring(xmlpage)
        return [i.text.decode('utf8') for i in xmlpage.getiterator('name')]

if __name__ == '__main__':
    print repr( ASArtist('Radiohead').getSimilar() )
    print repr( ASArtist('pink floyd').getTop() )

