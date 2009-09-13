ZicBee
++++++

Read this if you want to experience a new approach of song accesibility. This suite is not designed to be full featured, it's just a very handy pipe to transfer songs and playlists, optionally able to play things itself (using mplayer executable for now).

Features
========

* Still fast even on big playlists and libraries (OK with 30k entries on a netbook)
* Nice syntax for queries, accessible to any user, *search* and *play* takes the same parameters so you just replace the command name when you are happy with the output
* Daemon/Network oriented (not unlike mpd)
    * Access songs on remote computers
    * Close the client, songs will continue playing
    * Open as many clients as you want at any moment
    * You can mix songs from several computers on the same playlist
* Pure Python (it should run on any computer, mac, etc...)
* HTTP everywhere (you can use the web browser on your phone to control the playback or do a query on your library, try "http://host:9090/compact" HTTP address for minimal embedded devices support)
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
  * zicbee (server / admin utilities / db tools)
  * zicbee-wasp (client, much faster than zicbee)
  * zicbee-mplayer (mplayer bindings, allow zicbee to play music)
  * zicbee-quodlibet (plugin that turns quodlibet into a zicbee client)

Install
=======

Install it on your system::

 easy_install zicbee

Alternatively, you may try using `hives <http://zicbee.gnux.info/hive/>`_, a self-contained package, for linux only for now...

Scan your songs (you can reproduce this step several times)::

 zicdb scan <a directory with many songs>

Start the server (you may want to do this uppon your session startup)::

 zicserve

Quickstart
==========

Connect to the www interface::

 firefox http://localhost:9090/

Read help::

 zicdb help

Install the client and run it::

 easy_install zicbee-wasp
 wasp

alternatively you can run the client embedded in zicdb (both commands are equivalent)::

 zicbee
 `or`
 zicdb shell

Play songs from another computer here, after doing some search, zap first song & show playlist::

 wasp search artist: black
 wasp set db_host 192.168.0.40
 wasp set player_host localhost
 wasp search artist: black
 wasp play artist: black sab
 wasp next
 wasp show

Note that you have to remove "wasp" from the lines below if you are typing in zicdb shell or in wasp shell (run it giving no parameter to wasp).

Dependencies
============
  The software and all the dependencies are available in pure python without native code requirement,
  it should run on any OS. Wherever many packages answers that requirement, then evaluate speed and simplicity.

  * A JSON implementation (python-cjson, simplejson, demjson or builtin if using python >= 2.6)
  * mutagen (song metadatas handling)
  * buzhug (database)
  * web.py (minimalistic www providing library)

  You will also need *mplayer* executable if you want your server to play music by itself.
  Note that it's not required to play music easily, since you can generate m3u output that will open
  in your favorite music player.
  

Changelog
=========

0.9
...

 * allow easy player backends integration (packages splitting via entry-points)
    * there is a single backend so far (mplayer)
    * made server not an optional feature for zicbee (since now we have a proper independent shell and most people was confused with it)
    * see Developers section
 * minimal www interface (for low power machines, don't expect too much)
    * use /basic on any server with a player, it's quite rought now
 * Integrate automatic playlists with `*AUTO*` keyword
    * minimalistic last.fm support (no account needed, only works with "artist" keyword)
    * modulable tolerence giving a digit (ex: `*AUTO 15*`)
    * "artist: wax tailor or artist: birdy nam nam `*AUTO*`" automatically generates a playlist of similar artists
 * Split code into 3 projects to clarify parts
 * stored playlists (including position)
    * use "#" to act on current playlist
    * use "pls: <playlist name>" to WRITE a playlist
    * use "playlist: <playlist name>" to LOAD a playlist
    * prefix playlist name with "+" to append results to playlist
    * prefix playlist name with ">" to insert results into playlist just after the current song
    * inc. playlist resume
 * cleaner javascript/cookies/sessions (prepare theme support)
 * improve shell completion (abbreviations done, maybe "set" command to come)
    * text interface
 * rating/tag fully working (intensive tests on distributed configurations) [TBD: UnitTests]
 * satisfying duplicates detection [WIP]

0.8
..............

 * add support for FLAC
 * interactive shell support with completion and history
    * see "zicdb shell" or "zicbee" commands
 * integrate/complete tagging & scoring support
 * add support for multiple DBs at once
    * (ie. have separate databases for your mp3 player & your local drive)
    * see "use" command for usage
 * complete admin commands (see "set" command)

0.7
..............

 * add play, pause, next, prev, list
 * add cleaner configuration:: more unified (prepare themes handling)
    * ensure default host is well given

0.7-rc1 (first public release)
..............................

 * site launch
 * fixes egg/root installation (temporary file created)

