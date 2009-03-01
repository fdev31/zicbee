# vim: et ts=4 sw=4

def serve():
    startup('serve')

def startup(action='help'):
    import os
    import sys
    import zicbee.core.zshell as zshell
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
        for p in list(params):
            if '=' in p:
                k, v = p.split('=', 1)
                kparams[k] = v
                params.remove(p)
    else:
        kparams = dict()
        params = tuple()

    try:
        import zicbee.core.commands as cmds
        commands_dict = dict((i[3:], getattr(cmds, i)) for i in dir(cmds) if i.startswith('do_'))
        commands_dict.get(action, cmds.do_help)(*params, **kparams)
    except KeyboardInterrupt:
        print "Abort!"

