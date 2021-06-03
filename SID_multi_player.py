######## Main program for MOS6581 multiplayer ###############

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

sample_folder = "song_samples"

songs = [['Billie_Jean' , 50], ['Beat_It', 100], ['Bad_guy',100], ['Commando',50], ['Wiz3L',180], ['Wiz6L',200], ['Paperboy', 50], ['Ocean_loader_3',50],
         ['Thrust',50], ['Cobra',50],['Lazy_jones',50],['Cybernoid',50]] # columns of 8

song_num =  0# select which song to play

vols =   [ 1.00,  1.0,  0.50,  0.50,  0.50,  0.30] # attenuation on each channel. max = 1.0 - good for Oxygene 4
delays = [ 0   ,  1   , 0   ,  0   ,100   ,500   ] # delays in milliseconds
pitches =[60.00, 60.02,48.02, 35.98, 60.05, 60.07] # 60 is 1x frequency, 72 is 2x frequency, 79.02 is 3x frequency

vols =   [ 1.00,  1.0,  0.50,  0.50,  0.50,  0.90] # attenuation on each channel. max = 1.0 - good for Wiz 6L
delays = [ 0   ,  1   , 0   ,  0   ,100   ,250   ] # delays in milliseconds
pitches =[60.00, 60.02,48.02, 35.98, 60.05, 60.07] # 60 is 1x frequency, 72 is 2x frequency, 79.02 is 3x frequency

vols =   [ 0.5 ,  0.5 ,  0.50,  0.50,  0.25,  0.25] # attenuation on each channel. max = 1.0 - good for Cybernoid
delays = [ 0   , 60   ,  0   ,  0   ,  0   ,240   ] # delays in milliseconds
pitches =[60.00, 60.02, 71.98, 47.98, 60.05, 60.07] # 60 is 1x frequency, 72 is 2x frequency, 79.02 is 3x frequency


vc_on = [1,1,1] # select which voices to play
CHANNELS = [0,1,2,3,4,5] # select which channels are enabled

#from sid_driver import *
#from samp_manager import *
import sid_driver 
import samp_man 
import time
import sys
from signal import signal, SIGINT

def end_prog(signal_received, frame):
    print ("Exiting...")
    sd.reset_sid()
    sys.exit(0)

samp_1 = songs[song_num][0]

song = True
fps = songs[song_num][1]
if song and fps:
    refresh_time = 1.0/fps
else:
    fps = 200
    refresh_time = 1.0/fps # universal speed for samples

dels = []
for delay in delays:
    dels.append(int(delay * 0.001 * fps))    

MAXCHANS = 8

sd = sid_driver.sid()
sd.reset_sid()

sm = samp_manager.samp_man(sd)
if song:
    sm.load_song(samp_1, sample_folder) # defaults to all voices on, note = 60 and frate = 1
else:
    sm.load_samp(samp_1, sample_folder)

sm.voice_orig[samp_1] = vc_on

for c in CHANNELS:
    sm.start_samp(c, samp_1)
    sm.adjust_volume(c, vols[c])

steps = [0] * MAXCHANS
last_frame_time = time.clock()

signal(SIGINT, end_prog) # This is the interupt handler to ensure ctrl-c  stops the music

for i in range(fps*1000): # provide a 1000 second time out
    for c in CHANNELS:
        while steps[c] + dels[c] < i:
            sm.play_next_samp(c,pitches[c],1,c==0)
            steps[c]+=1
            
    last_frame_time += refresh_time
    while (time.clock()<last_frame_time):
        pass # insert bitcoin mining code here

end_prog()
