######## LFO and Envelope controls - a subset of a larger library ##

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

import random
import wave

#import matplotlib.pyplot as plt
import numpy as np
#import audio_output_constants
#from array import array
from audio_constants import *
#from wave_table_gen import *
import time
#import scipy.signal as sp
import pickle
import copy

pedal_down = 0 # pedals are hacked out

TABLE_SIZE = 65536.0
FRAME_SIZE = 128

#half_sine_phase = np.append(np.arange(int(TABLE_SIZE * 0.1666666),TABLE_SIZE * 0.5,1),np.arange(0, int(TABLE_SIZE * 0.1666666),1))
half_sine_phase = list(range(int(TABLE_SIZE * 0.1666666),int(TABLE_SIZE))) + list(range(int(TABLE_SIZE * 0.1666666)))
half_cos_phase = list(range(int(TABLE_SIZE * 0.5))) + list(range(int(TABLE_SIZE * 1.5),int(TABLE_SIZE * 2)))

#print half_sine_phase
rand_table = np.random.random(int(TABLE_SIZE)).astype(np.float32) * 2 - 1

noise_sine = [np.sin(2*np.pi*i/TABLE_SIZE) for i in range(int(TABLE_SIZE))] + rand_table * 0.01

sign_sine = np.sign(noise_sine)
compressed_sine = [abs(i) ** 0.5 for i in noise_sine] * sign_sine

wave_table = np.array([[np.sin(2*np.pi*i/TABLE_SIZE) for i in range(int(TABLE_SIZE))],
                      [(np.sin(np.pi*i/TABLE_SIZE) * 2 - 1) for i in half_sine_phase],
                      [(np.sin(np.pi*i/TABLE_SIZE)) for i in half_cos_phase],
                      compressed_sine,
                      ]).astype(np.float32)

cos_delay_table = np.array([np.cos(2*np.pi*i/TABLE_SIZE) * 0.5 - 0.5 for i in range(int(TABLE_SIZE))])



    
class lfo:
    def __init__(self):
        self.noise_rate = 256. / TABLE_SIZE
        self.step = 0.0
        self.wave_shape = None
        self.wv_shape = 0

    def next_frame(self, start, lower, upper, wave_type, wave_shape, freq, continuous, key_status):
        self.start = start
        self.middle = (upper + lower) * 0.5
        self.scale = (upper - lower) * 0.5
        self.freq = freq
        self.continuous = continuous
        self.wave_type = wave_type
        if self.wave_shape != wave_shape:
            self.wave_shape = wave_shape
            self.wv_shape = np.float32(np.uint16(wave_shape * TABLE_SIZE))
            if self.wv_shape == 0:
                self.wv_shape += 1
            if self.wv_shape == TABLE_SIZE - 1:
                self.wv_shape -= 1
            self.noise_rate = 265. / TABLE_SIZE
            self.up_slope = 2. / (self.wv_shape)
            self.down_slope = 2. / (65536 - self.wv_shape)
        
        if key_status == OSC_KEYDOWN and not self.continuous:
            self.step = self.start

        if self.wave_type == MUTED:
            return self.start

        next_frame = self.step + self.freq * FRAME_SIZE

        int_phase = np.uint16(self.step)

        if self.wave_type < NOISE:
            sample = wave_table[self.wave_type][int_phase]

        if self.wave_type == NOISE:
            next_frame = self.step + self.freq * self.noise_rate
            int_phase = np.uint16(self.step)
            sample = rand_table[int_phase]

        if self.wave_type == PULSE:
            if int_phase > self.wv_shape:
                sample = float(wave_shape)
                #print "+-1", int_phase, self.wave_shape
            else:
                sample = float(wave_shape) - 1
                #print "-1", int_phase, self.wave_shape
                
        if self.wave_type == TRIANGLE:
            int_phase = np.float32(np.uint16(self.step)) - self.wv_shape
            #print int_phase, self.up_slope, self.down_slope, self.wave_shape, self.step
            if int_phase < 0:
                sample = 1. + self.up_slope * int_phase
            else:
                sample = 1. - self.down_slope * int_phase

        if self.wave_type == SINE_COS:
            sample = wave_table[SINE][int_phase] * wave_shape + wave_table[HALF_COS][int_phase] * (1.0 - wave_shape)

        if self.wave_type == TRUE_NOISE:
            sample = np.random.normal(0, 0.25, 1)

        self.step = next_frame
        while self.step > 65536:
            self.step -= 65536
        while self.step < 0:
            self.step += 65536
        return sample * self.scale + self.middle

class adsr():
    def __init__(self): # a,d are in ms. s is a level, r is a decay per ms, self.r is a decay per frame
        self.step = 0
        self.level = 0
        self.attack = 1
        self.decay = 2
        self.state = 0

        #print self.r, r, (1000.0 * FRAME_SIZE / fs)

    def next_frame(self, a, d, s, r, key_status):
        global pedal_down
        
        if key_status == OSC_KEYDOWN:
            self.state = self.attack
        if key_status >= OSC_RELEASE:
            if not pedal_down:
                self.state = 0

        last_lev = self.level

        if key_status == OSC_RESET:
            self.state = 0
            self.level = 0
            return self.level

        if self.state == self.attack:
            next_lev = 1.1-((1.1-last_lev) * a)
            if next_lev > 1:
                self.state = self.decay
                next_lev = 1
        elif self.state == self.decay:
                next_lev = s + (last_lev - s) * d
        else:
            next_lev = last_lev * r
        self.level = next_lev
        return self.level

class wadsr():
    def __init__(self): # a,d are in ms. s is a level, r is a decay per ms, self.r is a decay per frame
        self.step = 0
        self.level = 0
        self.attack = 1
        self.decay = 2
        self.state = 0
        self.steptime = 1000 * FRAME_SIZE / fs #this is the time in ms between each frame

        #print self.r, r, (1000.0 * FRAME_SIZE / fs)

    def next_frame(self, w, a, d, s, r, key_status):
        global pedal_down
    
        if key_status == OSC_KEYDOWN:
            self.state = self.attack
            self.step = 0
        if key_status >= OSC_RELEASE:
            if not pedal_down:
                self.state = 0

        last_lev = self.level[FRAME_SIZE - 1]
        self.step += self.steptime

        if self.state == self.attack:
            if self.step > w:
                next_lev = 1.1-((1.1-last_lev) * a)
                if next_lev > 1:
                    self.state = self.decay
                    next_lev = 1
            else:
                self.level = 0
                return self.level
        elif self.state == self.decay:
            next_lev = s + (last_lev - s) * d
        else:
            next_lev = last_lev * r
        self.level = next_lev
        return self.level
