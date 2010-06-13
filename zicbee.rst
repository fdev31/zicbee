
ZicBee
++++++

To know more, visit `the website <http://zicbee.gnux.info/>`_.

Install
=======

You can either get an `"all in one" ZIP file on the website <http://zicbee.gnux.info/files/>`_ or install using something like easy_install, here is an example::

 easy_install zicbee

If you want to enable playback, install some player glue (pick one)::

 easy_install zicbee-mplayer
 easy_install zicbee-vlc

If you know Python language, you may want to download a fresh copy of `the workshop <http://zicbee.gnux.info/hg/zicbee-workshop/archive/tip.zip>`_, a collection of scripts to ease sources handling (fetching, building, distributing), also consider installing `Mercurial <http://mercurial.selenic.com/wiki/>`_.


Features
========

* Still **fast** even on big playlists and libraries (OK with 30k entries on a netbook)
* **Nice syntax** for queries, accessible to any user, *search* and *play* takes the same parameters so you just replace the command name when you are happy with the output
* Daemon/Network oriented (not unlike mpd)
    * Access songs on remote computers
    * Close the client, songs will continue playing
    * Open as many clients as you want at any moment
    * You can mix songs from several computers on the same playlist
* Pure **Python** (it should run on any computer, mac, etc...)
* **HTTP everywhere** (you can use the web browser on your phone to control the playback or do a query on your library, try "http://host:9090/basic" HTTP address for minimal embedded devices support)
* Always growing set of features:
    * nice playlist handling
    * real shuffle (not random)
    * last fm support (auto-generation of playlist based on small request)
    * song downloading
    * blind test mode (very minimalistic btw, see *guess* command)
    * duplicates detection (alpha quality)

    And much more... try *help* parameter to get an idea ! :)

Including projects
==================
  * zicbee (server (zicserve) / admin utilities (zicdb) / lightweight client (wasp))
  * zicbee-lib (base library for zicbee)
  * zicbee-mplayer (mplayer bindings, allow zicbee to play music)
  * zicbee-vlc (vlc bindings, allow zicbee to play music)
  * zicbee-gst (GStreamer bindings, allow zicbee to play music)
  * zicbee-quodlibet (plugin that turns quodlibet into a zicbee client)

Quickstart
==========

Start the server (you may want to do this uppon your session startup)::

 zicserve

Scan your songs (you can reproduce this step several times)::

 zicdb scan <a directory with many songs>

Connect to the www interface::

 firefox http://localhost:9090/

Read help::

 zicdb help

Fire up the client::

 wasp

Play songs from another computer here, after doing some search, zap first song & show playlist::

 wasp search artist: black
  => search artist containing "black" in their name
 wasp set
  => show all configuration variables
 wasp set db_host 192.168.0.40
  => changes the host to take songs from
 wasp set player_host localhost
  => tells zicbee to play song on THIS computer
 wasp search artist: black
  => search again (on the new db_host)
 wasp play artist: black sab
  => play black sabbath's music 
 wasp next
  => skip current song
 wasp show
  => Shows the next entries in the playlist
 wasp help
  => I think you *must* read it at least once...


Dependencies
============

The software and all the dependencies are available in pure python without native code requirement,
it should run on any OS. Wherever many packages answers that requirement, then evaluate speed and simplicity.

  * A JSON implementation (python-cjson, simplejson, demjson or builtin if using python >= 2.6)
  * mutagen (song metadatas handling)
  * buzhug (database)
  * web.py (minimalistic www providing library)

Additional dependencies may be required if you want playback (libvlc in case of zicbee-vlc and mplayer executable for zicbee-mplayer).
`Notice it's not required to play music easily, since you can generate m3u output that will open in your favorite music player.`
  

Changelog
=========

0.9
...

 * shiny new client (wasp), comes with many new features (grep, append, inject, get...)
    * **grep** can be used as parameter for ``move`` and ``delete`` commands. (use after using grep command)
    * ``move`` and ``delete`` also support slices passing (ex.: ``move 1:3``, ``delete 2:10``)
    * ``set`` can now unset a variable :P
 * improve shell completion
    * abbreviations everywhere
    * better completion
 * Support for live streaming, try "play <your favorite mp3 stream>"
 * autoshuffle mode (can be disabled of course)
 * new "random" command, plays some artist or album randomly
 * stfu won't have unexpected results, it *kills* the player_host
 * visual notification for player (can be disabled, unset "notify" variable)
 * satisfying duplicates detection [WIP]
 * more flexible commands (handles short commands)
 * allow easy player backends integration (packages splitting via entry-points)
    * there is two available backends so far (mplayer and vlc)
    * see Developers section
 * minimal www interface (for low power machines, don't expect too much)
    * use /basic on any server with a player, it's quite rought now
 * Integrate automatic playlists with ``*AUTO*`` keyword
    * minimalistic last.fm support (no account needed, only works with "artist" keyword)
    * modulable tolerence giving a digit (ex: ``*AUTO 15*``)
    * "``artist: wax tailor or artist: birdy nam nam *AUTO*``" automatically generates a playlist of similar artists
 * Split project for clarity
 * stored playlists (including position)
    * related wasp commands: load, save, append, inject
    * inc. playlist resume
    * you can alternatively use "pls:" option in play:
        * use "``#``" to act on current playlist
        * use "``pls: <playlist name>``" to WRITE a playlist
        * prefix playlist name with "``>``" to append results to playlist
        * prefix playlist name with "``+``" to insert results into playlist just after the current song
 * cleaner javascript/cookies/sessions (prepare theme support)
 * Tons of bugfixes!
 * known bugs: volume command is not very functional yet

0.8
...

 * add support for FLAC
 * interactive shell support with completion and history
    * see "zicdb shell" or "zicbee" commands
 * integrate/complete tagging & scoring support
 * add support for multiple DBs at once
    * (ie. have separate databases for your mp3 player & your local drive)
    * see "use" command for usage
 * complete admin commands (see "set" command)

0.7
...

 * add play, pause, next, prev, list
 * add cleaner configuration:: more unified (prepare themes handling)
    * ensure default host is well given

0.7-rc1 (first public release)
..............................

 * site launch
 * fixes egg/root installation (temporary file created)

