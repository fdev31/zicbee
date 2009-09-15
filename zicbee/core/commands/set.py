# vim: et ts=4 sw=4
from zicbee.core import zshell
from zicbee.core.config import config, defaults_dict

def do_set():
    """ set a config variable to the given value
    list all variables and values if no argument is given"""

    if not zshell.args:
        # dumps *
        values = defaults_dict.keys()
#        print "[DEFAULT]"

        not_found = []
        for param in values:
            try:
                print "%s = %s"%(param, getattr(config, param))
            except:
                not_found.append(param)

        if not_found:
            print "unavaible: %s"%(', '.join(not_found))

    elif zshell.args and len(zshell.args) < 4:
        # (re)set a value

        if len(zshell.args) == 2 or (len(zshell.args) == 3 and zshell.args[1] == '='):
            # set a value
            if zshell.args[1] == '=':
                del zshell.args[1]
            setattr(config, zshell.args[0], zshell.args[1])
        elif len(zshell.args) == 1:
            # reset (blank) a value
            setattr(config, zshell.args[0], '')

    else:
        print """Takes exactly 2 arguments: set <variable> <value>, takes no param to list variables.
        giving no arguments will print every variable
        a single parameter will be reset (blanked) """
