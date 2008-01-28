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
    if '::' in action:
        params = action.split('::')
        action = params.pop(0)
        kparams = dict()
        for p in params:
            if '=' in p:
                k, v = p.split('=', 1)
                kparams[k] = v
                params.remove(p)
    else:
        kparams = dict()
        params = tuple()

    try:
        import zicdb.commands as cmds
        commands_dict = dict((i[3:], getattr(cmds, i)) for i in dir(cmds) if i.startswith('do_'))
        commands_dict.get(action, cmds.do_help)(*params, **kparams)
#        print dir(cmds)
#        exec('cmds.do_%s(*params, **kparams)'%action, commands_dict)
#        getattr(cmds, 'do_'+action, cmds.do_help)(*params, **kparams)
    except KeyboardInterrupt:
        print "Abort!"

