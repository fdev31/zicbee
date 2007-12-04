# Syntax:
# vim: et ts=4 sw=4
# ./run.py search #shak# in '@filename@L' and #but# in '@filename@L'

def startup(action='help'):
    import sys
    import zicdb.zshell as zshell
    if len(sys.argv) > 1:
        action = sys.argv[1]

    zshell.init()
    getattr(zshell, 'do_'+action, zshell.do_help)()

