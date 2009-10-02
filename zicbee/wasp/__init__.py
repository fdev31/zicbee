import zicbee

def startup():
    import sys
    from .core import Shell, execute, best_match
    if len(sys.argv) > 1:
        execute(best_match(' '.join(sys.argv[1:])))
    else:
        s = Shell()
        s._prompt = 'wasp'
        user_happy = True
        while user_happy:
            try:
                s.cmdloop('Wasp %s!'%zicbee.__version__)
            except KeyboardInterrupt:
                if raw_input("Do you really want to exit (y/n) ? ").lower()[:1] == 'y':
                    user_happy = False


