
######## manages the operation of each channel ###############

# Copyright 2021 Simon Martin <simon.martin.cam.uk@hotmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice (including the next
# paragraph) shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


#
# See http://ssvb.github.io/
# for more details.
#

from audio_constants import *
 
class chan_man:
    def __init__(self):
        self.upper_samp = 0
        self.arpeg_samp = 0      
        
        self.key_status = [OSC_RESET] * MAXCHANS
        self.samp = [0] * MAXCHANS #
        self.source = [0] * MAXCHANS
        self.key_down_age = [0] * MAXCHANS
        self.note = [0.0] * MAXCHANS
        self.velocity = [0.0] * MAXCHANS
        self.pedal_down = False
        self.note_count = 0
        self.chan_seq = [0] * MAXCHANS

        self.vel_curve = [] 
        val = 0.1
        for i in range(256):
            if i<45:
                val = 0.1
            else:
                val += 0.03
            if val > 1:
                val = 1.0
            self.vel_curve.append(val)
            
        self.note_curve = []
        val = 1.2
        for i in range(256):
            self.note_curve.append(val)
            val *= 0.999

    def add_note(self, note, velocity, source, samp): #key_status, note, velocity, source, sm
        free = None
        for c in GOOD_CHANNELS:
            if self.key_status[c] == OSC_RESET:
                free = c

        if free == None: # none in reset so find longest released
            free, full = self.find_oldest_chan(source)

        if free is not None: 
            self.note[free] = note
            self.velocity[free] = self.vel_curve[velocity] * self.note_curve[note]
            self.key_status[free] = OSC_KEYDOWN
            self.source[free] = source
            self.samp[free] = samp
        else:
            return CHANNELS[0]

        return free

    def release_note(self, note, source): # this is not elegant without adding ,samp):
        for c in CHANNELS:
            if note == self.note[c] and source == self.source[c] and self.key_status[c] < OSC_RELEASE: # find a pressed down key. 
                self.key_status[c] = OSC_RELEASE
                return
        return
    
    def release_source(self, source): 
        for c in CHANNELS:
            if source == self.source[c]: # find all of this source
                self.key_status[c] = OSC_RELEASE
                return
        return
    
    def release_all(self): # note, key_status
        for c in CHANNELS: 
            self.key_status[c] = OSC_RELEASE
            self.note[c] = 0
     
    def advance_key_status(self, c, reset):
        if reset:
           self.key_status[c] = OSC_RESET
           self.note[c] = 0
           
        if self.key_status[c] == OSC_CONTINUE:
            self.key_down_age[c] += 1 # start counting how long the key is pressed in case you need to release it
        if self.key_status[c] == OSC_KEYDOWN or self.key_status[c] == OSC_NEWFREQ:
            self.key_status[c] = OSC_CONTINUE
            self.key_down_age[c] = 0
        if self.key_status[c] >= OSC_RELEASE:
            self.key_status[c] += 1

 
    def find_oldest_chan(self, source): 
        max_release = OSC_RELEASE
        release = -1
        
        # top priority it osc_reset next is released key of your source
        for c in GOOD_CHANNELS:
            if self.key_status[c] == OSC_RESET:
                    return c, False
            if self.key_status[c] >= max_release:
                if self.source[c] == 0 or self.source[c] == source: # look for a released key of your source
                    max_release = self.key_status[c]
                    release = c
        if release >= 0:
            return release, False
        
        # next priority is released key of other source
        for c in GOOD_CHANNELS: 
            if self.key_status[c] >= max_release:
                max_release = self.key_status[c]
                release = c
        if release >= 0:
            return release, False
        
        #self.show_status()
        #next priority is a bad sid channel of your source
        for c in BAD_CHANNELS:
            if self.key_status[c] == OSC_RESET:
                    return c, False
            if self.key_status[c] >= max_release:
                if self.source[c] == 0 or self.source[c] == source: # look for a released key of your source
                    max_release = self.key_status[c]
                    release = c
        if release >= 0:
            return release, False

        # find the oldest pressed note of your source
        max_key_down_age = 0
        for c in BAD_CHANNELS:
            if self.key_status[c] == OSC_CONTINUE: # find a pressed down key.
                if self.source[c] == 0 or self.source[c] == source:                
                    if self.key_down_age[c] > max_key_down_age:
                        max_key_down_age = self.key_down_age[c]
                        release = c
        if release >= 0:
            return release, True
        
        # failing all that, just find the oldest note of any source
        max_key_down_age = 0
        for c in CHANNELS:
            if self.key_status[c] == OSC_CONTINUE: # find a pressed down key.              
                if self.key_down_age[c] > max_key_down_age:
                    max_key_down_age = self.key_down_age[c]
                    release = c    
        return release, True

    def transition_note(self, note, new_note, source): # note, source,
        for c in CHANNELS:
            if note == self.note[c] and source == self.source[c] and self.key_status[c] <= OSC_CONTINUE:
                self.note[c] = new_note
                return
        print ("could not find note:", note, self.note)
            
    def show_status(self):
        print
        print ("GOOD_CHANNELS")
        print ("c, self.key_status[c], self.note[c], self.source[c], self.key_down_age[c],self.velocity[c],self.chan_seq[c]")
        for c in GOOD_CHANNELS:
            print (c, self.key_status[c], self.note[c],self.source[c], self.key_down_age[c],self.velocity[c],self.chan_seq[c])
        print ("BAD_CHANNELS")
        for c in BAD_CHANNELS:
            print (c, self.key_status[c], self.note[c],self.source[c], self.key_down_age[c],self.velocity[c],self.chan_seq[c])
        print
        self.init_params("init")

# class arpeg:    
