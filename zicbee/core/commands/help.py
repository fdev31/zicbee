# vim: et ts=4 sw=4
from zicbee.db import valid_tags

def do_help():
        """ Show a nifty help about most used commands """
        print "Welcome to ZicDB!".center(80)
        print """
use
    Not a command by itself, used to specify active database (default: songs)
    Exemple:
    %% %(prog)s use lisa search artist: dire st

serve[::pure]
    Runs a user-accessible www server on port 8080

  pure:
    don't allow player functionality access

list
    List available Databases.

reset
    Erases the Database (every previous scan is lost!)

bundle <filename>
    Create a bundle (compressed archive) of the database

scan <directory|archive> [directory|archive...]
    Scan directories/archive for files and add them to the database

get[::host][::out] <match command>
  host:
    the host to connect to

  out:
    the output directory

  Example:
    %% %(prog)s get::out=/tmp/download::host=gunter.biz artist: black
    %% %(prog)s get::gunter.biz artist: black

search[::out] <match command>

  out:
    specifies the output format (for now: m3u or null or default)

--- Match commands composition: ---

    field: value [ [or|and] field2: value2 ]...
    for length, value may be preceded by "<" or ">"
    if field name starts with a capital, the search is case-sensitive

  Possible fields:
\t- %(tags)s

  Exemple:
  %% %(prog)s search filename: shak length > 3*60

fullhelp
    List all available commands (with associated help if available)
    """%dict(
            tags = '\n\t- '.join(valid_tags),
            prog = "zicdb")

