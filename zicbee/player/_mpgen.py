#!/usr/bin/env python2.5
import os
import select
import subprocess

class_code = """# Access MPlayer from python
import os
import select
import subprocess
from zicbee.core.debug import debug_enabled as DEBUG

class MPlayer(object):
    ''' A class to access a slave mplayer process
    you may also want to use command(name, args*) directly

    Exemples:
        mp.command('loadfile', '/desktop/funny.mp3')
        mp.command('pause')
        mp.command('quit')

    Or:
        mp.loadfile('/desktop/funny.mp3')
        mp.pause()
        mp.quit()
    '''

    exe_name = 'mplayer' if os.sep == '/' else 'mplayer.exe'

    def __init__(self, cache=128):
        self._spawn(cache)

    def wait(self):
        self._mplayer.wait()

    def _spawn(self, cache):
        self._mplayer = subprocess.Popen(
                [self.exe_name, '-cache', '%s'cache, '-slave', '-quiet', '-idle'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=1)
        self._cache = cache
        self._readlines()

    def set_cache(cache):
        if cache != self._cache:
            self._spawn(cache)

    def __del__(self):
        self._mplayer.stdin.write('quit\\n')

    def _readlines(self, timeout=0.4):
        ret = []
        while any(select.select([self._mplayer.stdout.fileno()], [], [], timeout)):
            ret.append( self._mplayer.stdout.readline() )
        return ret

    def _get_meta(self):
        try:
            meta = self.prop_metadata.split(',')
        except AttributeError:
            return None
        else:
            return dict(zip(meta[::2], meta[1::2]))

    meta = property(_get_meta, doc="Get metadatas as a dict"); del _get_meta

    def command(self, name, *args):
        ''' Very basic interface
        Sends command 'name' to process, with given args
        '''
        ret = self._readlines(0.01) # Flush
        if DEBUG:
            print "FLUSH LINES:", ret
        cmd = '%s%s%s\\n'%(name,
                ' ' if args else '',
                ' '.join(repr(a) for a in args)
                )
        if DEBUG:
            print "CMD:", cmd
        try:
            self._mplayer.stdin.write(cmd)
        except IOError:
            self._spawn()
            self._mplayer.stdin.write(cmd)

        if name == 'quit':
            return
        ret = self._readlines()
        if DEBUG:
            print "READ LINES:", ret

        if not ret:
            return None
        else:
            ret = ret[-1]

        if ret.startswith('ANS'):
            val = ret.split('=', 1)[1].rstrip()
            try:
                return eval(val)
            except:
                return val
        return ret

"""

exe_name = 'mplayer' if os.sep == '/' else 'mplayer.exe'
mplayer = subprocess.Popen([exe_name, '-input', 'cmdlist'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)

def args_pprint(txt):
    lc = txt.lower()
    if lc[0] == '[':
        return '%s=None'%lc[1:-1]
    return lc

_slave_txt = None
def _find_doc_for(name):
    global _slave_txt
    if _slave_txt is None:
        import urllib
        uri = 'slave.txt' if os.path.isfile('slave.txt') else 'http://www.mplayerhq.hu/DOCS/tech/slave.txt'
        _slave_txt = urllib.urlopen(uri).readlines()

    actual_doc = None
    for line in _slave_txt:
        if actual_doc:
            if line.strip():
                actual_doc += line
            else:
                break
        elif line.endswith('properties:\n'):
                break
        elif line.startswith(name):
            actual_doc = line

    return actual_doc

while True:
    line = mplayer.stdout.readline()
    if not line:
        break
    if line[0].isupper():
        continue
    args = line.split()
    cmd_name = args.pop(0)
    arguments = ', '.join(args_pprint(a) for a in args)
    doc = _find_doc_for(cmd_name) or '%s(%s)'%(cmd_name, arguments)
    minargc = len([a for a in args if a[0] != '['])
    func_str = '''    def %(name)s(self, *args):
        """ %(doc)s
        """
        if %(condition)s:
            raise TypeError('%(name)s takes %(argc)d arguments (%%d given)'%%len(args))
        return self.command('%(name)s', *args)\n\n'''%dict(
            doc = doc,
            condition = ('len(args) != %d'%len(args)) if len(args) == minargc else ('not (%d <= len(args) <= %d)'%(minargc, len(args))),
            argc = len(args),
            name = cmd_name,
            )
    class_code += func_str

_not_properties = True
name = None
for line in _slave_txt:
    if _not_properties:
        if line.startswith('==================='):
            _not_properties = False
            class_code += '#Properties\n'
    else:
        if line[0].isalpha():
            if name is not None and name[-1] != '*':
                class_code += """
    prop_%(name)s = property(
        lambda self: self.get_property("%(name)s"),
        %(setter)s,
        doc = %(doc)s)
        """%dict(
                name = name,
                doc = ("'''%s'''"%('\n'.join(comments))) if any(comments) else 'None',
                setter = 'None' if ro else 'lambda self, val: self.set_property("%s", val)'%name
                )

            ridx = line.rindex('X')
            idx = line.index('X')
            try:
                name, p_type, limits = line[:idx].split(None, 2)
            except ValueError: # No limits
                name, p_type = line[:idx].split(None)
                limits = None
            permissions = len(line[idx:ridx+1])
            comments = [line[ridx+1:].strip()]

            ro = permissions < 2
        elif name is not None:
            comments.append(line.strip())

print class_code
