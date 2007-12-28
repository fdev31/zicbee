# Syntax:
# vim: et ts=4 sw=4
# ./run.py search #shak# in '@filename@L' and #but# in '@filename@L'

def startup(action='help'):
    import os
    import sys
    import zicdb.zshell as zshell
    if len(sys.argv) > 1:
        action = sys.argv[1]

    if '-' in sys.argv[0]:
        os.environ['ZDB'] = sys.argv[0].split('-', 1)[1]
    if action == 'use':
        os.environ['ZDB'] = sys.argv[2]
        del sys.argv[1:3] # Remove "use <db>"
        action = sys.argv[1]

    zshell.init()
    try:
        getattr(zshell, 'do_'+action, zshell.do_help)()
    except:
        print "Abort!"

