# Access MPlayer from python
import os
import select
import subprocess
from zicbee.core.debug import debug_enabled as DEBUG

class MPlayer(object):
    ''' A class to access a slave mplayer process
    you may also want to use command(name, args*) directly

    Exemples:
        mp.command('loadfile', '/desktop/funny.mp3')
        mp.command('pause')
        mp.command('quit')

    Or:
        mp.loadfile('/desktop/funny.mp3')
        mp.pause()
        mp.quit()
    '''

    exe_name = 'mplayer' if os.sep == '/' else 'mplayer.exe'

    def __init__(self, cache=128):
        self._spawn(cache)

    def wait(self):
        self._mplayer.wait()

    def respawn(self):
        self._mplayer.stdin.write('quit\n')
        self._mplayer.wait()
        self._spawn(self._cache)

    def _spawn(self, cache):
        self._mplayer = subprocess.Popen(
                [self.exe_name, '-cache', '%s'%cache, '-slave', '-quiet', '-idle'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=1)
        self._cache = cache
        self._readlines()

    def set_cache(self, cache):
        if cache != self._cache:
            self._spawn(cache)

    def __del__(self):
        self._mplayer.stdin.write('quit\n')

    def _readlines(self, timeout=0.4):
        ret = []
        while any(select.select([self._mplayer.stdout.fileno()], [], [], timeout)):
            ret.append( self._mplayer.stdout.readline() )
        return ret

    def _get_meta(self):
        try:
            meta = self.prop_metadata.split(',')
        except AttributeError:
            return None
        else:
            return dict(zip(meta[::2], meta[1::2]))

    meta = property(_get_meta, doc="Get metadatas as a dict"); del _get_meta

    def command(self, name, *args):
        ''' Very basic interface
        Sends command 'name' to process, with given args
        '''
        ret = self._readlines(0.01) # Flush
        if DEBUG:
            print "FLUSH LINES:", ret
        cmd = '%s%s%s\n'%(name,
                ' ' if args else '',
                ' '.join(repr(a) for a in args)
                )
        if DEBUG:
            print "CMD:", cmd
        try:
            self._mplayer.stdin.write(cmd)
        except IOError:
            self._spawn()
            self._mplayer.stdin.write(cmd)

        if name == 'quit':
            return
        ret = self._readlines()
        if DEBUG:
            print "READ LINES:", ret

        if not ret:
            return None
        else:
            ret = ret[-1]

        if ret.startswith('ANS'):
            val = ret.split('=', 1)[1].rstrip()
            try:
                return eval(val)
            except:
                return val
        return ret

    def radio_step_channel(self, *args):
        """ radio_step_channel <-1|1>
    Step forwards (1) or backwards (-1) in channel list. Works only when the
    'channels' radio parameter was set.

        """
        if len(args) != 1:
            raise TypeError('radio_step_channel takes 1 arguments (%d given)'%len(args))
        return self.command('radio_step_channel', *args)

    def radio_set_channel(self, *args):
        """ radio_set_channel <channel>
    Switch to <channel>. The 'channels' radio parameter needs to be set.

        """
        if len(args) != 1:
            raise TypeError('radio_set_channel takes 1 arguments (%d given)'%len(args))
        return self.command('radio_set_channel', *args)

    def radio_set_freq(self, *args):
        """ radio_set_freq <frequency in MHz>
    Set the radio tuner frequency.

        """
        if len(args) != 1:
            raise TypeError('radio_set_freq takes 1 arguments (%d given)'%len(args))
        return self.command('radio_set_freq', *args)

    def radio_step_freq(self, *args):
        """ radio_step_freq <value>
    Tune frequency by the <value> (positive - up, negative - down). 

        """
        if len(args) != 1:
            raise TypeError('radio_step_freq takes 1 arguments (%d given)'%len(args))
        return self.command('radio_step_freq', *args)

    def seek(self, *args):
        """ seek <value> [type]
    Seek to some place in the movie.
        0 is a relative seek of +/- <value> seconds (default).
        1 is a seek to <value> % in the movie.
        2 is a seek to an absolute position of <value> seconds.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('seek takes 2 arguments (%d given)'%len(args))
        return self.command('seek', *args)

    def edl_mark(self, *args):
        """ edl_mark
    Write the current position into the EDL file.

        """
        if len(args) != 0:
            raise TypeError('edl_mark takes 0 arguments (%d given)'%len(args))
        return self.command('edl_mark', *args)

    def audio_delay(self, *args):
        """ audio_delay <value> [abs]
    Set/adjust the audio delay.
    If [abs] is not given or is zero, adjust the delay by <value> seconds.
    If [abs] is nonzero, set the delay to <value> seconds.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('audio_delay takes 2 arguments (%d given)'%len(args))
        return self.command('audio_delay', *args)

    def speed_incr(self, *args):
        """ speed_incr <value>
    Add <value> to the current playback speed.

        """
        if len(args) != 1:
            raise TypeError('speed_incr takes 1 arguments (%d given)'%len(args))
        return self.command('speed_incr', *args)

    def speed_mult(self, *args):
        """ speed_mult <value>
    Multiply the current speed by <value>.

        """
        if len(args) != 1:
            raise TypeError('speed_mult takes 1 arguments (%d given)'%len(args))
        return self.command('speed_mult', *args)

    def speed_set(self, *args):
        """ speed_set <value>
    Set the speed to <value>.

        """
        if len(args) != 1:
            raise TypeError('speed_set takes 1 arguments (%d given)'%len(args))
        return self.command('speed_set', *args)

    def quit(self, *args):
        """ quit [value]
    Quit MPlayer. The optional integer [value] is used as the return code
    for the mplayer process (default: 0).

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('quit takes 1 arguments (%d given)'%len(args))
        return self.command('quit', *args)

    def pause(self, *args):
        """ pause
    Pause/unpause the playback.

        """
        if len(args) != 0:
            raise TypeError('pause takes 0 arguments (%d given)'%len(args))
        return self.command('pause', *args)

    def frame_step(self, *args):
        """ frame_step
    Play one frame, then pause again.

        """
        if len(args) != 0:
            raise TypeError('frame_step takes 0 arguments (%d given)'%len(args))
        return self.command('frame_step', *args)

    def pt_step(self, *args):
        """ pt_step <value> [force]
    Go to the next/previous entry in the playtree. The sign of <value> tells
    the direction.  If no entry is available in the given direction it will do
    nothing unless [force] is non-zero.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('pt_step takes 2 arguments (%d given)'%len(args))
        return self.command('pt_step', *args)

    def pt_up_step(self, *args):
        """ pt_up_step <value> [force]
    Similar to pt_step but jumps to the next/previous entry in the parent list.
    Useful to break out of the inner loop in the playtree.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('pt_up_step takes 2 arguments (%d given)'%len(args))
        return self.command('pt_up_step', *args)

    def alt_src_step(self, *args):
        """ alt_src_step <value> (ASX playlist only)
    When more than one source is available it selects the next/previous one.

        """
        if len(args) != 1:
            raise TypeError('alt_src_step takes 1 arguments (%d given)'%len(args))
        return self.command('alt_src_step', *args)

    def loop(self, *args):
        """ loop <value> [abs]
    Adjust/set how many times the movie should be looped. -1 means no loop,
    and 0 forever.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('loop takes 2 arguments (%d given)'%len(args))
        return self.command('loop', *args)

    def sub_delay(self, *args):
        """ sub_delay <value> [abs]
    Adjust the subtitle delay by +/- <value> seconds or set it to <value>
    seconds when [abs] is nonzero.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('sub_delay takes 2 arguments (%d given)'%len(args))
        return self.command('sub_delay', *args)

    def sub_step(self, *args):
        """ sub_step <value>
    Step forward in the subtitle list by <value> steps or backwards if <value>
    is negative.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('sub_step takes 2 arguments (%d given)'%len(args))
        return self.command('sub_step', *args)

    def osd(self, *args):
        """ osd [level]
    Toggle OSD mode or set it to [level] when [level] >= 0.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('osd takes 1 arguments (%d given)'%len(args))
        return self.command('osd', *args)

    def osd_show_text(self, *args):
        """ osd_show_text <string> [duration] [level]
    Show <string> on the OSD.

        """
        if not (1 <= len(args) <= 3):
            raise TypeError('osd_show_text takes 3 arguments (%d given)'%len(args))
        return self.command('osd_show_text', *args)

    def osd_show_property_te(self, *args):
        """ osd_show_property_text <string> [duration] [level]
    Show an expanded property string on the OSD, see -playing-msg for a
    description of the available expansions. If [duration] is >= 0 the text
    is shown for [duration] ms. [level] sets the minimum OSD level needed
    for the message to be visible (default: 0 - always show).

        """
        if not (1 <= len(args) <= 3):
            raise TypeError('osd_show_property_te takes 3 arguments (%d given)'%len(args))
        return self.command('osd_show_property_te', *args)

    def volume(self, *args):
        """ volume <value> [abs]
    Increase/decrease volume or set it to <value> if [abs] is nonzero.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('volume takes 2 arguments (%d given)'%len(args))
        return self.command('volume', *args)

    def balance(self, *args):
        """ balance(float, integer=None)
        """
        if not (1 <= len(args) <= 2):
            raise TypeError('balance takes 2 arguments (%d given)'%len(args))
        return self.command('balance', *args)

    def use_master(self, *args):
        """ use_master
    Switch volume control between master and PCM.

        """
        if len(args) != 0:
            raise TypeError('use_master takes 0 arguments (%d given)'%len(args))
        return self.command('use_master', *args)

    def mute(self, *args):
        """ mute [value]
    Toggle sound output muting or set it to [value] when [value] >= 0
    (1 == on, 0 == off).

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('mute takes 1 arguments (%d given)'%len(args))
        return self.command('mute', *args)

    def contrast(self, *args):
        """ contrast(integer, integer=None)
        """
        if not (1 <= len(args) <= 2):
            raise TypeError('contrast takes 2 arguments (%d given)'%len(args))
        return self.command('contrast', *args)

    def gamma(self, *args):
        """ gamma(integer, integer=None)
        """
        if not (1 <= len(args) <= 2):
            raise TypeError('gamma takes 2 arguments (%d given)'%len(args))
        return self.command('gamma', *args)

    def brightness(self, *args):
        """ brightness(integer, integer=None)
        """
        if not (1 <= len(args) <= 2):
            raise TypeError('brightness takes 2 arguments (%d given)'%len(args))
        return self.command('brightness', *args)

    def hue(self, *args):
        """ hue(integer, integer=None)
        """
        if not (1 <= len(args) <= 2):
            raise TypeError('hue takes 2 arguments (%d given)'%len(args))
        return self.command('hue', *args)

    def saturation(self, *args):
        """ saturation(integer, integer=None)
        """
        if not (1 <= len(args) <= 2):
            raise TypeError('saturation takes 2 arguments (%d given)'%len(args))
        return self.command('saturation', *args)

    def frame_drop(self, *args):
        """ frame_drop [value]
    Toggle/set frame dropping mode.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('frame_drop takes 1 arguments (%d given)'%len(args))
        return self.command('frame_drop', *args)

    def sub_pos(self, *args):
        """ sub_pos <value> [abs]
    Adjust/set subtitle position.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('sub_pos takes 2 arguments (%d given)'%len(args))
        return self.command('sub_pos', *args)

    def sub_alignment(self, *args):
        """ sub_alignment [value]
    Toggle/set subtitle alignment.
        0 top alignment
        1 center alignment
        2 bottom alignment

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('sub_alignment takes 1 arguments (%d given)'%len(args))
        return self.command('sub_alignment', *args)

    def sub_visibility(self, *args):
        """ sub_visibility [value]
    Toggle/set subtitle visibility.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('sub_visibility takes 1 arguments (%d given)'%len(args))
        return self.command('sub_visibility', *args)

    def sub_load(self, *args):
        """ sub_load <subtitle_file>
    Loads subtitles from <subtitle_file>.

        """
        if len(args) != 1:
            raise TypeError('sub_load takes 1 arguments (%d given)'%len(args))
        return self.command('sub_load', *args)

    def sub_remove(self, *args):
        """ sub_remove [value]
    If the [value] argument is present and non-negative, removes the subtitle
    file with index [value]. If the argument is omitted or negative, removes
    all subtitle files.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('sub_remove takes 1 arguments (%d given)'%len(args))
        return self.command('sub_remove', *args)

    def vobsub_lang(self, *args):
        """ vobsub_lang
    This is a stub linked to sub_select for backwards compatibility.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('vobsub_lang takes 1 arguments (%d given)'%len(args))
        return self.command('vobsub_lang', *args)

    def sub_select(self, *args):
        """ sub_select [value]
    Display subtitle with index [value]. Turn subtitle display off if
    [value] is -1 or greater than the highest available subtitle index.
    Cycle through the available subtitles if [value] is omitted or less
    than -1. Supported subtitle sources are -sub options on the command
    line, VOBsubs, DVD subtitles, and Ogg and Matroska text streams.
    This command is mainly for cycling all subtitles, if you want to set
    a specific subtitle, use sub_file, sub_vob, or sub_demux.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('sub_select takes 1 arguments (%d given)'%len(args))
        return self.command('sub_select', *args)

    def sub_log(self, *args):
        """ sub_log
    Logs the current or last displayed subtitle together with filename
    and time information to ~/.mplayer/subtitle_log. Intended purpose
    is to allow convenient marking of bogus subtitles which need to be
    fixed while watching the movie.

        """
        if len(args) != 0:
            raise TypeError('sub_log takes 0 arguments (%d given)'%len(args))
        return self.command('sub_log', *args)

    def sub_scale(self, *args):
        """ sub_scale <value> [abs]
    Adjust the subtitle size by +/- <value> or set it to <value> when [abs]
    is nonzero.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('sub_scale takes 2 arguments (%d given)'%len(args))
        return self.command('sub_scale', *args)

    def get_percent_pos(self, *args):
        """ get_percent_pos
    Print out the current position in the file, as integer percentage [0-100).

        """
        if len(args) != 0:
            raise TypeError('get_percent_pos takes 0 arguments (%d given)'%len(args))
        return self.command('get_percent_pos', *args)

    def get_time_pos(self, *args):
        """ get_time_pos
    Print out the current position in the file in seconds, as float.

        """
        if len(args) != 0:
            raise TypeError('get_time_pos takes 0 arguments (%d given)'%len(args))
        return self.command('get_time_pos', *args)

    def get_time_length(self, *args):
        """ get_time_length
    Print out the length of the current file in seconds.

        """
        if len(args) != 0:
            raise TypeError('get_time_length takes 0 arguments (%d given)'%len(args))
        return self.command('get_time_length', *args)

    def get_file_name(self, *args):
        """ get_file_name
    Print out the name of the current file.

        """
        if len(args) != 0:
            raise TypeError('get_file_name takes 0 arguments (%d given)'%len(args))
        return self.command('get_file_name', *args)

    def get_video_codec(self, *args):
        """ get_video_codec
    Print out the video codec name of the current file.

        """
        if len(args) != 0:
            raise TypeError('get_video_codec takes 0 arguments (%d given)'%len(args))
        return self.command('get_video_codec', *args)

    def get_video_bitrate(self, *args):
        """ get_video_bitrate
    Print out the video bitrate of the current file.

        """
        if len(args) != 0:
            raise TypeError('get_video_bitrate takes 0 arguments (%d given)'%len(args))
        return self.command('get_video_bitrate', *args)

    def get_video_resolution(self, *args):
        """ get_video_resolution
    Print out the video resolution of the current file.

        """
        if len(args) != 0:
            raise TypeError('get_video_resolution takes 0 arguments (%d given)'%len(args))
        return self.command('get_video_resolution', *args)

    def get_audio_codec(self, *args):
        """ get_audio_codec
    Print out the audio codec name of the current file.

        """
        if len(args) != 0:
            raise TypeError('get_audio_codec takes 0 arguments (%d given)'%len(args))
        return self.command('get_audio_codec', *args)

    def get_audio_bitrate(self, *args):
        """ get_audio_bitrate
    Print out the audio bitrate of the current file.

        """
        if len(args) != 0:
            raise TypeError('get_audio_bitrate takes 0 arguments (%d given)'%len(args))
        return self.command('get_audio_bitrate', *args)

    def get_audio_samples(self, *args):
        """ get_audio_samples
    Print out the audio frequency and number of channels of the current file.

        """
        if len(args) != 0:
            raise TypeError('get_audio_samples takes 0 arguments (%d given)'%len(args))
        return self.command('get_audio_samples', *args)

    def get_meta_title(self, *args):
        """ get_meta_title
    Print out the 'Title' metadata of the current file.

        """
        if len(args) != 0:
            raise TypeError('get_meta_title takes 0 arguments (%d given)'%len(args))
        return self.command('get_meta_title', *args)

    def get_meta_artist(self, *args):
        """ get_meta_artist
    Print out the 'Artist' metadata of the current file.

        """
        if len(args) != 0:
            raise TypeError('get_meta_artist takes 0 arguments (%d given)'%len(args))
        return self.command('get_meta_artist', *args)

    def get_meta_album(self, *args):
        """ get_meta_album
    Print out the 'Album' metadata of the current file.

        """
        if len(args) != 0:
            raise TypeError('get_meta_album takes 0 arguments (%d given)'%len(args))
        return self.command('get_meta_album', *args)

    def get_meta_year(self, *args):
        """ get_meta_year
    Print out the 'Year' metadata of the current file.

        """
        if len(args) != 0:
            raise TypeError('get_meta_year takes 0 arguments (%d given)'%len(args))
        return self.command('get_meta_year', *args)

    def get_meta_comment(self, *args):
        """ get_meta_comment
    Print out the 'Comment' metadata of the current file.

        """
        if len(args) != 0:
            raise TypeError('get_meta_comment takes 0 arguments (%d given)'%len(args))
        return self.command('get_meta_comment', *args)

    def get_meta_track(self, *args):
        """ get_meta_track
    Print out the 'Track Number' metadata of the current file.

        """
        if len(args) != 0:
            raise TypeError('get_meta_track takes 0 arguments (%d given)'%len(args))
        return self.command('get_meta_track', *args)

    def get_meta_genre(self, *args):
        """ get_meta_genre
    Print out the 'Genre' metadata of the current file.

        """
        if len(args) != 0:
            raise TypeError('get_meta_genre takes 0 arguments (%d given)'%len(args))
        return self.command('get_meta_genre', *args)

    def switch_audio(self, *args):
        """ switch_audio [value] (currently MPEG*, AVI, Matroska and streams handled by libavformat)
    Switch to the audio track with the ID [value]. Cycle through the
    available tracks if [value] is omitted or negative.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('switch_audio takes 1 arguments (%d given)'%len(args))
        return self.command('switch_audio', *args)

    def tv_start_scan(self, *args):
        """ tv_start_scan
    Start automatic TV channel scanning.

        """
        if len(args) != 0:
            raise TypeError('tv_start_scan takes 0 arguments (%d given)'%len(args))
        return self.command('tv_start_scan', *args)

    def tv_step_channel(self, *args):
        """ tv_step_channel <channel>
    Select next/previous TV channel.

        """
        if len(args) != 1:
            raise TypeError('tv_step_channel takes 1 arguments (%d given)'%len(args))
        return self.command('tv_step_channel', *args)

    def tv_step_norm(self, *args):
        """ tv_step_norm
    Change TV norm.

        """
        if len(args) != 0:
            raise TypeError('tv_step_norm takes 0 arguments (%d given)'%len(args))
        return self.command('tv_step_norm', *args)

    def tv_step_chanlist(self, *args):
        """ tv_step_chanlist
    Change channel list.

        """
        if len(args) != 0:
            raise TypeError('tv_step_chanlist takes 0 arguments (%d given)'%len(args))
        return self.command('tv_step_chanlist', *args)

    def tv_set_channel(self, *args):
        """ tv_set_channel <channel>
    Set the current TV channel.

        """
        if len(args) != 1:
            raise TypeError('tv_set_channel takes 1 arguments (%d given)'%len(args))
        return self.command('tv_set_channel', *args)

    def tv_last_channel(self, *args):
        """ tv_last_channel
    Set the current TV channel to the last one.

        """
        if len(args) != 0:
            raise TypeError('tv_last_channel takes 0 arguments (%d given)'%len(args))
        return self.command('tv_last_channel', *args)

    def tv_set_freq(self, *args):
        """ tv_set_freq <frequency in MHz>
    Set the TV tuner frequency.

        """
        if len(args) != 1:
            raise TypeError('tv_set_freq takes 1 arguments (%d given)'%len(args))
        return self.command('tv_set_freq', *args)

    def tv_step_freq(self, *args):
        """ tv_step_freq <frequency offset in MHz>
    Set the TV tuner frequency relative to current value.

        """
        if len(args) != 1:
            raise TypeError('tv_step_freq takes 1 arguments (%d given)'%len(args))
        return self.command('tv_step_freq', *args)

    def tv_set_norm(self, *args):
        """ tv_set_norm <norm>
    Set the TV tuner norm (PAL, SECAM, NTSC, ...).

        """
        if len(args) != 1:
            raise TypeError('tv_set_norm takes 1 arguments (%d given)'%len(args))
        return self.command('tv_set_norm', *args)

    def tv_set_brightness(self, *args):
        """ tv_set_brightness <-100 - 100> [abs]
    Set TV tuner brightness or adjust it if [abs] is set to 0.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('tv_set_brightness takes 2 arguments (%d given)'%len(args))
        return self.command('tv_set_brightness', *args)

    def tv_set_contrast(self, *args):
        """ tv_set_contrast <-100 -100> [abs]
    Set TV tuner contrast or adjust it if [abs] is set to 0.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('tv_set_contrast takes 2 arguments (%d given)'%len(args))
        return self.command('tv_set_contrast', *args)

    def tv_set_hue(self, *args):
        """ tv_set_hue <-100 - 100> [abs]
    Set TV tuner hue or adjust it if [abs] is set to 0.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('tv_set_hue takes 2 arguments (%d given)'%len(args))
        return self.command('tv_set_hue', *args)

    def tv_set_saturation(self, *args):
        """ tv_set_saturation <-100 - 100> [abs]
    Set TV tuner saturation or adjust it if [abs] is set to 0.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('tv_set_saturation takes 2 arguments (%d given)'%len(args))
        return self.command('tv_set_saturation', *args)

    def forced_subs_only(self, *args):
        """ forced_subs_only [value]
    Toggle/set forced subtitles only.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('forced_subs_only takes 1 arguments (%d given)'%len(args))
        return self.command('forced_subs_only', *args)

    def dvb_set_channel(self, *args):
        """ dvb_set_channel <channel_number> <card_number>
    Set DVB channel.

        """
        if len(args) != 2:
            raise TypeError('dvb_set_channel takes 2 arguments (%d given)'%len(args))
        return self.command('dvb_set_channel', *args)

    def switch_ratio(self, *args):
        """ switch_ratio [value]
    Change aspect ratio at runtime. [value] is the new aspect ratio expressed
    as a float (e.g. 1.77778 for 16/9).
    There might be problems with some video filters.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('switch_ratio takes 1 arguments (%d given)'%len(args))
        return self.command('switch_ratio', *args)

    def vo_fullscreen(self, *args):
        """ vo_fullscreen [value]
    Toggle/set fullscreen mode.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('vo_fullscreen takes 1 arguments (%d given)'%len(args))
        return self.command('vo_fullscreen', *args)

    def vo_ontop(self, *args):
        """ vo_ontop [value]
    Toggle/set stay-on-top.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('vo_ontop takes 1 arguments (%d given)'%len(args))
        return self.command('vo_ontop', *args)

    def file_filter(self, *args):
        """ file_filter(integer)
        """
        if len(args) != 1:
            raise TypeError('file_filter takes 1 arguments (%d given)'%len(args))
        return self.command('file_filter', *args)

    def vo_rootwin(self, *args):
        """ vo_rootwin [value]
    Toggle/set playback on the root window.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('vo_rootwin takes 1 arguments (%d given)'%len(args))
        return self.command('vo_rootwin', *args)

    def vo_border(self, *args):
        """ vo_border [value]
    Toggle/set borderless display.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('vo_border takes 1 arguments (%d given)'%len(args))
        return self.command('vo_border', *args)

    def screenshot(self, *args):
        """ screenshot <value>
    Take a screenshot. Requires the screenshot filter to be loaded.
        0 Take a single screenshot.
        1 Start/stop taking screenshot of each frame.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('screenshot takes 1 arguments (%d given)'%len(args))
        return self.command('screenshot', *args)

    def panscan(self, *args):
        """ panscan <-1.0 - 1.0> | <0.0 - 1.0> <abs>
    Increase or decrease the pan-and-scan range by <value>, 1.0 is the maximum.
    Negative values decrease the pan-and-scan range.
    If <abs> is != 0, then the pan-and scan range is interpreted as an
    absolute range.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('panscan takes 2 arguments (%d given)'%len(args))
        return self.command('panscan', *args)

    def switch_vsync(self, *args):
        """ switch_vsync [value]
    Toggle vsync (1 == on, 0 == off). If [value] is not provided,
    vsync status is inverted.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('switch_vsync takes 1 arguments (%d given)'%len(args))
        return self.command('switch_vsync', *args)

    def loadfile(self, *args):
        """ loadfile <file|url> <append>
    Load the given file/URL, stopping playback of the current file/URL.
    If <append> is nonzero playback continues and the file/URL is
    appended to the current playlist instead.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('loadfile takes 2 arguments (%d given)'%len(args))
        return self.command('loadfile', *args)

    def loadlist(self, *args):
        """ loadlist <file> <append>
    Load the given playlist file, stopping playback of the current file.
    If <append> is nonzero playback continues and the playlist file is
    appended to the current playlist instead.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('loadlist takes 2 arguments (%d given)'%len(args))
        return self.command('loadlist', *args)

    def run(self, *args):
        """ run <value>
    Run <value> as shell command. In OSD menu console mode stdout and stdin
    are through the video output driver.

        """
        if len(args) != 1:
            raise TypeError('run takes 1 arguments (%d given)'%len(args))
        return self.command('run', *args)

    def change_rectangle(self, *args):
        """ change_rectangle <val1> <val2>
    Change the position of the rectangle filter rectangle.
        <val1>
            Must be one of the following:
                0 = width
                1 = height
                2 = x position
                3 = y position
        <val2>
            If <val1> is 0 or 1:
                Integer amount to add/subtract from the width/height.
                Positive values add to width/height and negative values
                subtract from it.
            If <val1> is 2 or 3:
                Relative integer amount by which to move the upper left
                rectangle corner. Positive values move the rectangle
                right/down and negative values move the rectangle left/up.

        """
        if len(args) != 2:
            raise TypeError('change_rectangle takes 2 arguments (%d given)'%len(args))
        return self.command('change_rectangle', *args)

    def teletext_add_dec(self, *args):
        """ teletext_add_dec(string)
        """
        if len(args) != 1:
            raise TypeError('teletext_add_dec takes 1 arguments (%d given)'%len(args))
        return self.command('teletext_add_dec', *args)

    def teletext_go_link(self, *args):
        """ teletext_go_link <1-6>
    Follow given link on current teletext page.

        """
        if len(args) != 1:
            raise TypeError('teletext_go_link takes 1 arguments (%d given)'%len(args))
        return self.command('teletext_go_link', *args)

    def menu(self, *args):
        """ menu <command>
    Execute an OSD menu command.
        up     Move cursor up.
        down   Move cursor down.
        ok     Accept selection.
        cancel Cancel selection.
        hide   Hide the OSD menu.

        """
        if len(args) != 1:
            raise TypeError('menu takes 1 arguments (%d given)'%len(args))
        return self.command('menu', *args)

    def set_menu(self, *args):
        """ set_menu <menu_name>
    Display the menu named <menu_name>.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('set_menu takes 2 arguments (%d given)'%len(args))
        return self.command('set_menu', *args)

    def help(self, *args):
        """ help
    Displays help text, currently empty.

        """
        if len(args) != 0:
            raise TypeError('help takes 0 arguments (%d given)'%len(args))
        return self.command('help', *args)

    def exit(self, *args):
        """ exit
    Exits from OSD menu console. Unlike 'quit', does not quit MPlayer.

        """
        if len(args) != 0:
            raise TypeError('exit takes 0 arguments (%d given)'%len(args))
        return self.command('exit', *args)

    def hide(self, *args):
        """ hide
    Hides the OSD menu console. Clicking a menu command unhides it. Other
    keybindings act as usual.

        """
        if not (0 <= len(args) <= 1):
            raise TypeError('hide takes 1 arguments (%d given)'%len(args))
        return self.command('hide', *args)

    def get_vo_fullscreen(self, *args):
        """ get_vo_fullscreen
    Print out fullscreen status (1 == fullscreened, 0 == windowed).

        """
        if len(args) != 0:
            raise TypeError('get_vo_fullscreen takes 0 arguments (%d given)'%len(args))
        return self.command('get_vo_fullscreen', *args)

    def get_sub_visibility(self, *args):
        """ get_sub_visibility
    Print out subtitle visibility (1 == on, 0 == off).

        """
        if len(args) != 0:
            raise TypeError('get_sub_visibility takes 0 arguments (%d given)'%len(args))
        return self.command('get_sub_visibility', *args)

    def key_down_event(self, *args):
        """ key_down_event <value>
    Inject <value> key code event into MPlayer.

        """
        if len(args) != 1:
            raise TypeError('key_down_event takes 1 arguments (%d given)'%len(args))
        return self.command('key_down_event', *args)

    def set_property(self, *args):
        """ set_property <property> <value>
    Set a property.

        """
        if len(args) != 2:
            raise TypeError('set_property takes 2 arguments (%d given)'%len(args))
        return self.command('set_property', *args)

    def get_property(self, *args):
        """ get_property <property>
    Print out the current value of a property.

        """
        if len(args) != 1:
            raise TypeError('get_property takes 1 arguments (%d given)'%len(args))
        return self.command('get_property', *args)

    def step_property(self, *args):
        """ step_property <property> [value] [direction]
    Change a property by value, or increase by a default if value is
    not given or zero. The direction is reversed if direction is less
    than zero.

        """
        if not (1 <= len(args) <= 3):
            raise TypeError('step_property takes 3 arguments (%d given)'%len(args))
        return self.command('step_property', *args)

    def seek_chapter(self, *args):
        """ seek_chapter <value> [type]
    Seek to the start of a chapter.
        0 is a relative seek of +/- <value> chapters (default).
        1 is a seek to chapter <value>.

        """
        if not (1 <= len(args) <= 2):
            raise TypeError('seek_chapter takes 2 arguments (%d given)'%len(args))
        return self.command('seek_chapter', *args)

    def set_mouse_pos(self, *args):
        """ set_mouse_pos <x> <y>
    Tells MPlayer the coordinates of the mouse in the window.
    This command doesn't move the mouse!

        """
        if len(args) != 2:
            raise TypeError('set_mouse_pos takes 2 arguments (%d given)'%len(args))
        return self.command('set_mouse_pos', *args)

#Properties

    prop_osdlevel = property(
        lambda self: self.get_property("osdlevel"),
        lambda self, val: self.set_property("osdlevel", val),
        doc = '''as -osdlevel''')
        
    prop_speed = property(
        lambda self: self.get_property("speed"),
        lambda self, val: self.set_property("speed", val),
        doc = '''as -speed''')
        
    prop_loop = property(
        lambda self: self.get_property("loop"),
        lambda self, val: self.set_property("loop", val),
        doc = '''as -loop''')
        
    prop_pause = property(
        lambda self: self.get_property("pause"),
        None,
        doc = '''1 if paused, use with pausing_keep_force''')
        
    prop_filename = property(
        lambda self: self.get_property("filename"),
        None,
        doc = '''file playing wo path''')
        
    prop_path = property(
        lambda self: self.get_property("path"),
        None,
        doc = '''file playing''')
        
    prop_demuxer = property(
        lambda self: self.get_property("demuxer"),
        None,
        doc = '''demuxer used''')
        
    prop_stream_pos = property(
        lambda self: self.get_property("stream_pos"),
        lambda self, val: self.set_property("stream_pos", val),
        doc = '''position in stream''')
        
    prop_stream_start = property(
        lambda self: self.get_property("stream_start"),
        None,
        doc = '''start pos in stream''')
        
    prop_stream_end = property(
        lambda self: self.get_property("stream_end"),
        None,
        doc = '''end pos in stream''')
        
    prop_stream_length = property(
        lambda self: self.get_property("stream_length"),
        None,
        doc = '''(end - start)''')
        
    prop_chapter = property(
        lambda self: self.get_property("chapter"),
        lambda self, val: self.set_property("chapter", val),
        doc = '''select chapter''')
        
    prop_chapters = property(
        lambda self: self.get_property("chapters"),
        None,
        doc = '''number of chapters''')
        
    prop_angle = property(
        lambda self: self.get_property("angle"),
        lambda self, val: self.set_property("angle", val),
        doc = '''select angle''')
        
    prop_length = property(
        lambda self: self.get_property("length"),
        None,
        doc = '''length of file in seconds''')
        
    prop_percent_pos = property(
        lambda self: self.get_property("percent_pos"),
        lambda self, val: self.set_property("percent_pos", val),
        doc = '''position in percent''')
        
    prop_time_pos = property(
        lambda self: self.get_property("time_pos"),
        lambda self, val: self.set_property("time_pos", val),
        doc = '''position in seconds''')
        
    prop_metadata = property(
        lambda self: self.get_property("metadata"),
        None,
        doc = '''list of metadata key/value''')
        
    prop_volume = property(
        lambda self: self.get_property("volume"),
        lambda self, val: self.set_property("volume", val),
        doc = '''change volume''')
        
    prop_balance = property(
        lambda self: self.get_property("balance"),
        lambda self, val: self.set_property("balance", val),
        doc = '''change audio balance''')
        
    prop_mute = property(
        lambda self: self.get_property("mute"),
        lambda self, val: self.set_property("mute", val),
        doc = None)
        
    prop_audio_delay = property(
        lambda self: self.get_property("audio_delay"),
        lambda self, val: self.set_property("audio_delay", val),
        doc = None)
        
    prop_audio_format = property(
        lambda self: self.get_property("audio_format"),
        None,
        doc = None)
        
    prop_audio_codec = property(
        lambda self: self.get_property("audio_codec"),
        None,
        doc = None)
        
    prop_audio_bitrate = property(
        lambda self: self.get_property("audio_bitrate"),
        None,
        doc = None)
        
    prop_samplerate = property(
        lambda self: self.get_property("samplerate"),
        None,
        doc = None)
        
    prop_channels = property(
        lambda self: self.get_property("channels"),
        None,
        doc = None)
        
    prop_switch_audio = property(
        lambda self: self.get_property("switch_audio"),
        lambda self, val: self.set_property("switch_audio", val),
        doc = '''select audio stream''')
        
    prop_switch_angle = property(
        lambda self: self.get_property("switch_angle"),
        lambda self, val: self.set_property("switch_angle", val),
        doc = '''select DVD angle''')
        
    prop_switch_title = property(
        lambda self: self.get_property("switch_title"),
        lambda self, val: self.set_property("switch_title", val),
        doc = '''select DVD title''')
        
    prop_fullscreen = property(
        lambda self: self.get_property("fullscreen"),
        lambda self, val: self.set_property("fullscreen", val),
        doc = None)
        
    prop_deinterlace = property(
        lambda self: self.get_property("deinterlace"),
        lambda self, val: self.set_property("deinterlace", val),
        doc = None)
        
    prop_ontop = property(
        lambda self: self.get_property("ontop"),
        lambda self, val: self.set_property("ontop", val),
        doc = None)
        
    prop_rootwin = property(
        lambda self: self.get_property("rootwin"),
        lambda self, val: self.set_property("rootwin", val),
        doc = None)
        
    prop_border = property(
        lambda self: self.get_property("border"),
        lambda self, val: self.set_property("border", val),
        doc = None)
        
    prop_framedropping = property(
        lambda self: self.get_property("framedropping"),
        lambda self, val: self.set_property("framedropping", val),
        doc = '''1 = soft, 2 = hard''')
        
    prop_gamma = property(
        lambda self: self.get_property("gamma"),
        lambda self, val: self.set_property("gamma", val),
        doc = None)
        
    prop_brightness = property(
        lambda self: self.get_property("brightness"),
        lambda self, val: self.set_property("brightness", val),
        doc = None)
        
    prop_contrast = property(
        lambda self: self.get_property("contrast"),
        lambda self, val: self.set_property("contrast", val),
        doc = None)
        
    prop_saturation = property(
        lambda self: self.get_property("saturation"),
        lambda self, val: self.set_property("saturation", val),
        doc = None)
        
    prop_hue = property(
        lambda self: self.get_property("hue"),
        lambda self, val: self.set_property("hue", val),
        doc = None)
        
    prop_panscan = property(
        lambda self: self.get_property("panscan"),
        lambda self, val: self.set_property("panscan", val),
        doc = None)
        
    prop_vsync = property(
        lambda self: self.get_property("vsync"),
        lambda self, val: self.set_property("vsync", val),
        doc = None)
        
    prop_video_format = property(
        lambda self: self.get_property("video_format"),
        None,
        doc = None)
        
    prop_video_codec = property(
        lambda self: self.get_property("video_codec"),
        None,
        doc = None)
        
    prop_video_bitrate = property(
        lambda self: self.get_property("video_bitrate"),
        None,
        doc = None)
        
    prop_width = property(
        lambda self: self.get_property("width"),
        None,
        doc = '''"display" width''')
        
    prop_height = property(
        lambda self: self.get_property("height"),
        None,
        doc = '''"display" height''')
        
    prop_fps = property(
        lambda self: self.get_property("fps"),
        None,
        doc = None)
        
    prop_aspect = property(
        lambda self: self.get_property("aspect"),
        None,
        doc = None)
        
    prop_switch_video = property(
        lambda self: self.get_property("switch_video"),
        lambda self, val: self.set_property("switch_video", val),
        doc = '''select video stream''')
        
    prop_switch_program = property(
        lambda self: self.get_property("switch_program"),
        lambda self, val: self.set_property("switch_program", val),
        doc = '''(see TAB default keybind)''')
        
    prop_sub = property(
        lambda self: self.get_property("sub"),
        lambda self, val: self.set_property("sub", val),
        doc = '''select subtitle stream''')
        
    prop_sub_source = property(
        lambda self: self.get_property("sub_source"),
        lambda self, val: self.set_property("sub_source", val),
        doc = '''select subtitle source''')
        
    prop_sub_file = property(
        lambda self: self.get_property("sub_file"),
        lambda self, val: self.set_property("sub_file", val),
        doc = '''select file subtitles''')
        
    prop_sub_vob = property(
        lambda self: self.get_property("sub_vob"),
        lambda self, val: self.set_property("sub_vob", val),
        doc = '''select vobsubs''')
        
    prop_sub_demux = property(
        lambda self: self.get_property("sub_demux"),
        lambda self, val: self.set_property("sub_demux", val),
        doc = '''select subs from demux''')
        
    prop_sub_delay = property(
        lambda self: self.get_property("sub_delay"),
        lambda self, val: self.set_property("sub_delay", val),
        doc = None)
        
    prop_sub_pos = property(
        lambda self: self.get_property("sub_pos"),
        lambda self, val: self.set_property("sub_pos", val),
        doc = '''subtitle position''')
        
    prop_sub_alignment = property(
        lambda self: self.get_property("sub_alignment"),
        lambda self, val: self.set_property("sub_alignment", val),
        doc = '''subtitle alignment''')
        
    prop_sub_visibility = property(
        lambda self: self.get_property("sub_visibility"),
        lambda self, val: self.set_property("sub_visibility", val),
        doc = '''show/hide subtitles''')
        
    prop_sub_forced_only = property(
        lambda self: self.get_property("sub_forced_only"),
        lambda self, val: self.set_property("sub_forced_only", val),
        doc = None)
        
    prop_sub_scale = property(
        lambda self: self.get_property("sub_scale"),
        lambda self, val: self.set_property("sub_scale", val),
        doc = '''subtitles font size''')
        
    prop_tv_brightness = property(
        lambda self: self.get_property("tv_brightness"),
        lambda self, val: self.set_property("tv_brightness", val),
        doc = None)
        
    prop_tv_contrast = property(
        lambda self: self.get_property("tv_contrast"),
        lambda self, val: self.set_property("tv_contrast", val),
        doc = None)
        
    prop_tv_saturation = property(
        lambda self: self.get_property("tv_saturation"),
        lambda self, val: self.set_property("tv_saturation", val),
        doc = None)
        
    prop_tv_hue = property(
        lambda self: self.get_property("tv_hue"),
        lambda self, val: self.set_property("tv_hue", val),
        doc = None)
        
    prop_teletext_page = property(
        lambda self: self.get_property("teletext_page"),
        lambda self, val: self.set_property("teletext_page", val),
        doc = None)
        
    prop_teletext_subpage = property(
        lambda self: self.get_property("teletext_subpage"),
        lambda self, val: self.set_property("teletext_subpage", val),
        doc = None)
        
    prop_teletext_mode = property(
        lambda self: self.get_property("teletext_mode"),
        lambda self, val: self.set_property("teletext_mode", val),
        doc = '''0 - off, 1 - on''')
        
    prop_teletext_format = property(
        lambda self: self.get_property("teletext_format"),
        lambda self, val: self.set_property("teletext_format", val),
        doc = '''0 - opaque,
1 - transparent,
2 - opaque inverted,
3 - transp. inv.''')
        
