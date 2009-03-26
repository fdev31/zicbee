# vim: et ts=4 sw=4
from zicbee.db import valid_tags

def do_help():
        """ Show a nifty help about most used commands """
        print "Welcome to ZicDB!".center(80)
        print """
use
    Not a command by itself, used to specify active database (default: songs)
    You can specify mutiple databases at once using ',' separator (without spaces)
    Exemple:
    %% %(prog)s use lisa search artist: dire st
    %% %(prog)s use usb_drive,songs search artist: dire st
    %% %(prog)s use songs,ipod search artist: dire st

    The first exemple is using only one db (not the default one of course),
    the next uses usb drive and fallbacks to default db
    the last one uses the ipod database as fallback for commands (like search)
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

search[::out] <match command>

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

