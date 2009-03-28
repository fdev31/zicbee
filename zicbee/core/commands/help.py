# vim: et ts=4 sw=4
from zicbee.db import valid_tags
from zicbee.core import zshell
from zicbee.core.zutils import get_help_from_func

def do_help():
        """ Show a nifty help about most used commands """
        if zshell.args:
            from zicbee.core import commands
            not_found = []
            for arg in zshell.args:
                try:
                    cmd = getattr(commands, 'do_%s'%arg)
                except AttributeError:
                    cmd = None
                    not_found.append(arg)

                if cmd:
                    cmd_help, cmd_is_remote = get_help_from_func(cmd)
                    print cmd_help
            if not_found:
                print "Not found: %s"%(', '.join(not_found))
            return

        print "Welcome to ZicDB!".center(80)
        print """
use
    Not a command by itself, used to specify active database (default: songs)
    You can specify mutiple databases at once using ',' separator (without spaces)
    Exemple:
    %% %(prog)s use lisa serve
      > starts serving lisa's database
    %% %(prog)s use usb_drive reset
      > destroy usb_drive database
    %% %(prog)s use ipod bundle ipod_database_backup.zdb
      > backups the "ipod" database into "ipod_database_backup.zdb" file in current directory

    WARNING: using more than one database will most probably lead to song conflicts and won't be usable
      consider this feature very experimental, use only if you know what you are doing.

    NOTE: you can alternatively use the "ZDB" environment variable instead

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

play[::dbhost::phost] <match command>
    Set playlist to specified request and start playing if previously stopped

    dbhost:
      the computer owning the songs
    phost:
      the playback computer

search[::out::host] <match command>

  out:
    specifies the output format (for now: m3u or null or default)

--- Match commands composition: ---

    field: value [ [or|and] field2: value2 ]...
    for length, value may be preceded by "<" or ">"
    if field name starts with a capital, the search is case-sensitive

  Possible fields:
\t- id (compact style)
\t- %(tags)s

  Working Exemples:
  %% %(prog)s search filename: shak length: > 3*60
    > songs with "shak" in filename and of more than 3 min
  %% %(prog)s search artist: shak length: > 3*60 or artist: black
    > songs with "shak" or "black" in artist name and of more than 3 min
  %% %(prog)s search artist: shak length: > 3*60 and title: mo
    > songs with "shak" in artist name and of more than 3 min and with "mo" on the title
  %% %(prog)s search tags: jazz title: moon
    > songs tagged "jazz" and with titles containing "moon"
  %% %(prog)s search score: >2
    > songs with a score higher than 2
  %% %(prog)s search score: >2 score: <= 3 tags: rock length: <= 120
    > a quite dumb search ;) (the selected songs will have a score of 3, less than 2 min and tagged as "rock")

fullhelp
    List all available commands (with associated help if available)
    """%dict(
            tags = '\n\t- '.join(valid_tags),
            prog = "zicdb")

