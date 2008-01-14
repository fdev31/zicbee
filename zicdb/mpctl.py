from select import select
import subprocess

class MPlayer(object):
    def __init__(self):
        self._mplayer = subprocess.Popen(
                ['mplayer', '-slave', '-quiet', '-idle'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=1)
        self._readlines()

    def _readlines(self):
        ret = []
        while any(select([self._mplayer.stdout.fileno()], [], [], 0.6)):
#            if self._mplayer.poll():
#                raise SystemExit()
            ret.append( self._mplayer.stdout.readline() )
        return ret

    def _command(self, name, *args):
        cmd = '%s%s%s\n'%(name,
                ' ' if args else '',
                ' '.join(str(a) for a in args)
                )
        self._mplayer.stdin.write(cmd)
        if name == 'quit':
            return
        return self._readlines()

def init():
    mplayer = subprocess.Popen(['mplayer', '-input', 'cmdlist'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    while True:
        line = mplayer.stdout.readline()
        if not line:
            break
        if line[0].isupper():
            continue
        args = line.split()
        cmd_name = args.pop(0)
        func_str = '''def _mp_func(self, *args):
        """%(doc)s"""
        if not (%(minargc)d <= len(args) <= %(argc)d):
            raise TypeError('%(name)s takes %(argc)d arguments (%%d given)'%%len(args))
        ret = self._command('%(name)s', *args)
        if not ret:
            return None
        if ret[0].startswith('ANS'):
            val = ret[0].split('=', 1)[1].rstrip()
            try:
                return eval(val)
            except:
                return val
        return ret'''%dict(
                doc = '%s(%s)'%(cmd_name, ', '.join(args)),
                minargc = len([a for a in args if a[0] != '[']),
                argc = len(args),
                name = cmd_name,
                )
        exec(func_str)

        setattr(MPlayer, cmd_name, _mp_func)

if __name__ == '__main__':
    import sys
    init()
    try:
        mp = MPlayer()
        import readline
        readline.parse_and_bind('tab: complete')
        import rlcompleter
        mp.loadfile(sys.argv[1])
        raw_input('Run this with python -i to get interactive shell.\nPress any key to quit.')
    finally:
        mp.quit()

