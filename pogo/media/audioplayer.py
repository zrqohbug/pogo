# -*- coding: utf-8 -*-
#
# Copyright (c) 2007  François Ingelrest (Francois.Ingelrest@gmail.com)
# Copyright (c) 2012  Jendrik Seipp (jendrikseipp@web.de)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

from gi.repository import Gst


class AudioPlayer:
    def __init__(self, callbackEnded):
        """ Constructor """
        self.player = None
        self.rgEnabled = False
        self.eqzLevels = None
        self.equalizer = None
        self.eqzEnabled = False
        self.callbackEnded = callbackEnded

    def __getPlayer(self):
        """ Construct and return the GStreamer player """
        if not self.player:
            self.__constructPlayer()

        return self.player

    def __constructPlayer(self):
        """ Create the GStreamer pipeline """
        self.player = Gst.ElementFactory.make('playbin', 'player')
        self.player.connect('about-to-finish', self.__onAboutToFinish)

        # No video
        self.player.set_property('video-sink', Gst.ElementFactory.make('fakesink', 'fakesink'))

        # Change the audio sink to our own bin, so that an equalizer/replay gain element can be added later on if needed
        self.audiobin = Gst.Bin.new('audiobin')
        self.audiosink = Gst.ElementFactory.make('autoaudiosink', 'audiosink')

        self.audiobin.add(self.audiosink)
        self.audiobin.add_pad(Gst.GhostPad.new('sink', self.audiosink.get_static_pad('sink')))
        self.player.set_property('audio-sink', self.audiobin)

        # Monitor messages generated by the player
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.__onGstMessage)

        # Add equalizer?
        if self.eqzEnabled:
            self.equalizer = Gst.ElementFactory.make('equalizer-10bands', 'equalizer')
            self.audiobin.add(self.equalizer)
            self.audiobin.get_static_pad('sink').set_target(self.equalizer.get_static_pad('sink'))
            self.equalizer.link_filtered(self.audiosink)

            if self.eqzLevels is not None:
                self.setEqualizerLvls(self.eqzLevels)

        # Add replay gain?
        if self.rgEnabled:
            replaygain = Gst.ElementFactory.make('rgvolume', 'replaygain')

            self.audiobin.add(replaygain)
            self.audiobin.get_static_pad('sink').set_target(replaygain.get_static_pad('sink'))

            if self.equalizer is None:
                replaygain.link_filtered(self.audiosink)
            else:
                replaygain.link_filtered(self.equalizer)

    def enableEqualizer(self):
        """ Add an equalizer to the audio chain """
        self.eqzEnabled = True

    def enableReplayGain(self):
        """ Add/Enable a replay gain element """
        self.rgEnabled = True

    def setEqualizerLvls(self, lvls):
        """
        Set the level of the 10-bands of the equalizer (levels must be a
        list/tuple with 10 values lying between -24 and +12).
        """
        if len(lvls) == 10:
            self.eqzLevels = lvls

            if self.equalizer is not None:
                self.equalizer.set_property('band0', lvls[0])
                self.equalizer.set_property('band1', lvls[1])
                self.equalizer.set_property('band2', lvls[2])
                self.equalizer.set_property('band3', lvls[3])
                self.equalizer.set_property('band4', lvls[4])
                self.equalizer.set_property('band5', lvls[5])
                self.equalizer.set_property('band6', lvls[6])
                self.equalizer.set_property('band7', lvls[7])
                self.equalizer.set_property('band8', lvls[8])
                self.equalizer.set_property('band9', lvls[9])

    def __onAboutToFinish(self, _islast):
        """ End of the track """
        self.callbackEnded(False)

    def __onGstMessage(self, bus, msg):
        """ A new message generated by the player """
        if msg.type == Gst.MessageType.EOS:
            self.callbackEnded(False)
        elif msg.type == Gst.MessageType.ERROR:
            self.stop()
            # It seems that the pipeline may not be able to play again
            # any valid stream when an error occurs.
            # We thus create a new one, even if that's quite a ugly solution.
            self.__constructPlayer()
            self.callbackEnded(True)

        return True

    def setNextURI(self, uri):
        """ Set the next URI """
        self.__getPlayer().set_property('uri', uri.replace('%', '%25').replace('#', '%23'))

    def isPaused(self):
        """ Return whether the player is paused """
        return self.__getPlayer().get_state(timeout=Gst.CLOCK_TIME_NONE).state == Gst.State.PAUSED

    def isPlaying(self):
        """ Return whether the player is paused """
        return self.__getPlayer().get_state(timeout=Gst.CLOCK_TIME_NONE).state == Gst.State.PLAYING

    def setURI(self, uri):
        """ Play the given URI """
        self.__getPlayer().set_property('uri', uri.replace('%', '%25').replace('#', '%23'))

    def play(self):
        """ Play """
        self.__getPlayer().set_state(Gst.State.PLAYING)

    def pause(self):
        """ Pause """
        self.__getPlayer().set_state(Gst.State.PAUSED)

    def stop(self):
        """ Stop playing """
        self.__getPlayer().set_state(Gst.State.NULL)

    def seek(self, where):
        """ Jump to the given location """
        self.__getPlayer().seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, where)

    def getPosition(self):
        """ Return the current position """
        return self.__getPlayer().query_position(Gst.Format.TIME).cur

    def getDuration(self):
        """ Return the duration of the current stream """
        return self.__getPlayer().query_duration(Gst.Format.TIME).duration