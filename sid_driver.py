######## drives the C library that controls the SID chips ###############

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

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
import numpy.ctypeslib as ctl
import ctypes
import math

MAXCHANS = 8
INVF = 16.777216 / 256

class sid:
    def __init__(self):
        
        DIO = [8,9,10,11,12,13,14,15]
        AIO = [16, 17, 18, 19, 20]
        CSIO = [21,22,23,24,25,26,27,7]
        RW = 3
        SID_RESET = 2
        
        GPIO.setwarnings(False)
        GPIO.setup(4, GPIO.IN) #CLK
        GPIO.setup(DIO, GPIO.OUT) # d0
        GPIO.setup(CSIO, GPIO.OUT) # cs0
        GPIO.setup(7, GPIO.OUT) # cs7
        GPIO.setup(3, GPIO.OUT) # rw
        GPIO.setup(2, GPIO.OUT) # res
        GPIO.setup(AIO, GPIO.OUT) # a0
        
        # I hate this code. I don't know why pigpio does not set the I/O up properly
        # Only this python code does it and only if sudo is typed when running python
        
        self.print_count = 0
        
        libname = 'sid_lib.so'
        libdir = './'
        lib=ctl.load_library(libname, libdir)

        self.py_write_sid = lib.write_sid
        self.py_write_sid.argtypes = [ctypes.c_int]

        self.py_read_sid = lib.read_sid
        self.py_read_sid.argtypes = [ctypes.c_int]
        
        self.py_init_sid = lib.init_sid
        self.py_init_sid.argtypes = []

        self.py_reset_sid = lib.reset_sid
        self.py_reset_sid.argtypes = []
        
        self.registers = [[0] * 25] * MAXCHANS
        
        self.control = ''
        self.filt_mode = 0
        self.tone = [1,1,1]
        self.ring = [0,0,0]
        self.sync = [0,0,0]
        
    def reset_sid(self): # Pulls the reset pin and clears the registers
        self.py_init_sid()
        self.py_reset_sid()
        for ch in range(8):
            for addr in range(25):
                self.py_write_sid(ch, addr, 0)
            
    def mute_sid(self):
        for ch in range(MAXCHANS):
            self.py_write_sid(ch, 24, 0)
            
    def unmute_sid(self):
         for ch in range(MAXCHANS):
            self.py_write_sid(ch,24, self.registers[ch][24])
            
    def write_sid(self,ch, addr, data):
        if ch >= MAXCHANS:
            print ("bad channel in write_sid:", ch)
            return
        if addr > 24:
            print ("bad address in write_sid:", addr)
            return
        self.py_write_sid(ch, addr, data)
        self.registers[ch][addr] = data
        
    def read_sid(self,ch,addr):
        if ch >= MAXCHANS:
            print ("bad channel in read_sid:", ch)
            return
        if addr > 24:
            print ("bad address in read_sid:", addr)
            return
        return self.py_read_sid(ch, addr)
    
    def get_sid(self,ch,addr):
        if ch >= MAXCHANS:
            print ("bad channel in get_sid:", ch)
            return
        if addr > 24:
            print ("bad address in get_sid:", addr)
            return
        data = int(self.registers[ch][addr])
        return data
         
    def set_pwm(self,c,val):
        val = int(val)
        if val < 25:
            val = 25
        if val > 4070:
            val = 4070
        for vc in [0,7,14]:
            self.write_sid(c, vc+2, val&255)
            self.write_sid(c, vc+3, int(val / 256))


    def update_adsr(self,c,adsr):
        self.adsr = adsr
        for vc in range(3):
            val = int(adsr['a'][vc])*16+int(adsr['d'][vc])
            if self.get_sid(c, vc*7+5) != val:
                self.write_sid(c, vc*7+5, val)    
            val = int(adsr['s'][vc])*16+int(adsr['r'][vc])
            if self.get_sid(c, vc*7+6) != val:
                self.write_sid(c, vc*7+6, val)

    def all_sid(self,reg,val):
        for ch in range(MAXCHANS):
            if reg < 7:
                for vc in [0,7,14]:
                    self.write_sid(ch, vc+reg, int(val))
            else:
                self.write_sid(ch, reg, int(val))

    def set_filter(self,ch, cut_off, res, filt_on, filt_mode, vol):
        self.filt_mode = filt_mode
        #filtco = int((5000*cut_off)/(1035+cut_off))
        #filtco = int(cut_off * INVF * 0.5)
        #filtco = int(468.1662*2.71828**(0.0001*cut_off))
        filtco = int(cut_off*.5)

        if filtco > 2047:
            filtco = 2047
        self.write_sid(ch, 22, int(filtco*0.125))
        self.write_sid(ch, 21, filtco & 7)
            
        self.write_sid(ch, 23, filt_on + int(res) * 16) # Attack/dec
        self.write_sid(ch, 24, int(vol + filt_mode * 16))
    
    def set_control_mode(self,control):
        self.control = control
    
    def set_freq(self,ch, voice,freq):
        if voice > 2:
            print ("Incorrect voice in set_freq", voice)
            return

        if 'NEG' in self.control:            
            if freq < 0:
                freq = - freq

        if 'BLOCK' in self.control:
            if freq > 3906: # maximum allowed frequency in a SID
                freq = 0
            if freq < 0:
                freq = 0

        if 'HALF' in self.control:
            while freq > 3906: # maximum allowed frequency in a SID
                freq = freq * 0.5
            
        vc = voice * 7
        f = freq * INVF
        hi_byte = int(f)
        lo_byte = int((f - hi_byte) * 256)
        
        self.write_sid(ch, vc , lo_byte)
        self.write_sid(ch, vc + 1 , hi_byte)

    def set_tone(self, vc, tone): 
        self.tone[vc] = tone
        
    def set_ring(self, vc, ring):
        self.ring[vc] = ring
        
    def set_sync(self, vc, sync):
        self.sync[vc] = sync
        
    def set_volume(self,ch, vol):
        self.write_sid(ch, 24, vol + self.filt_mode * 16)
        self.current_vol = vol
       
    def note_down(self, ch, vc, velocity): #tone, ring_sync, adrs_*, 
        if 'VELOCITY' not in self.control or velocity > 1:
            velocity = 1
        #print("note down", ch, vc, self.adsr_a,vc, self.adsr_d,vc, self.adsr_s,vc, self.adsr_r)
        self.write_sid(ch, vc*7 + 4, self.tone[vc]*16+self.ring[vc] *4 +self.sync[vc]*2)
        val = int(self.adsr['a'][vc])*16+int(self.adsr['d'][vc])
        self.write_sid(ch, vc*7+5, val)    
        val = int(self.adsr['s'][vc]*velocity)*16+int(self.adsr['r'][vc])
        self.write_sid(ch, vc*7+6, val)
        self.write_sid(ch, vc*7 + 4, self.tone[vc] * 16 + self.ring[vc] * 4 + self.sync[vc] * 2 + 1)
        
    def note_up(self, ch, vc):#tone, ring_sync, 
        #print("note up", ch, vc, self.tone[vc]+self.ringsync[vc] )
        self.write_sid(ch, vc*7 + 4, self.tone[vc] * 16 + self.ring[vc] * 4 + self.sync[vc] * 2 )           
       
    def print_sid(self, ch, t):
        self.print_count += 1                                                                            
        if ch >= MAXCHANS:
            print ("bad channel in get_sid:", ch)
            return
        line = ["CH",hexc(ch,1)," "]
        x = self.registers[ch]
        for vc in range(3):
            v = vc*7
            line += [
            freq_to_note((x[1+v]*256+x[0+v])/INVF/256),
            ' PW', hexc(x[3+v],1), hexc(x[2+v]>>4,1),
            ' G', hexc(x[4+v]&1,1),
            ' ADSR', hexc(x[5+v],2), hexc(x[6+v],2),
            ' CR', hexc(x[4+v]&0xFE,2),
            ' F', hexc(x[23]&(1<<vc),1),
            ' ']
            
        line += [
        ' CUT',
        hexc(x[22],2),
        ' RES',
        hexc(x[23]>>4,1),
        ' V',
        hexc(x[24],2), ' ',
        str(t)]
        out = ''
        for c in line:
            out += c
        print (out)
        
def freq_to_note(freq):
    if freq <= 0:
        return "---"
    note = (math.log(freq / 261.63) / math.log (1.059463)) + 60
    num_text=''#str(note)
    notes_text = ["C-","C#","D-","D#","E-","F-","F#","G-","G#","A-","A#","B-"]
    note_text = notes_text[int(note+0.5)%12]
    if note > 12:
        octave = str(int(note/12)-1)
    else:
        octave = "S"
    return num_text+note_text+octave

def hexc(h,c):
    chars = '0123456789ABCDEF'
    out_hex = ''
    for i in range(c):
        out_hex = chars[int(h)&15] + out_hex
        h = h / 16
    return out_hex
