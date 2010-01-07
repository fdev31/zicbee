# vim: et ts=4 sw=4

def serve():
    startup('serve')

def setup_db(db_name, args):
    import zicbee.core.zshell as zshell
    zshell.init(args, db_name)

def parse_cmd(action='help', *arguments):
    db_name = None
    arguments = list(arguments)

    if action == 'use':
        db_name = arguments[0]
        action = arguments[1]
        del arguments[:2] # Remove "<db name> <action>"

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

    return db_name, arguments, action, params, kparams

def execute_cmd(action, *params, **kparams):
    try:
        import zicbee.core.commands as cmds
        commands_dict = dict((i[3:], getattr(cmds, i)) for i in dir(cmds) if i.startswith('do_'))
        commands_dict.get(action, cmds.do_help)(*params, **kparams)
    except KeyboardInterrupt:
        print "Abort!"

def shell():
    startup('shell')

def startup(*args):
    import os
    import sys
    db_name = None
    if not args:
        arguments = sys.argv[2:]
        if len(sys.argv) > 1:
            action = sys.argv[1]
        else:
            action = 'help'
        # feature: you can use aliases like zicdb-bigdrive to automatically use "bigdrive" db
        if '-' in os.path.basename(sys.argv[0]):
            db_name = sys.argv[0].rsplit('-', 1)[1]
    else:
        action = args[0]
        arguments = args[1:]

    cmd_db_name, arguments, action, params, kparams = parse_cmd(action, *arguments)
    setup_db(db_name or cmd_db_name, arguments)
    execute_cmd(action, *params, **kparams)

