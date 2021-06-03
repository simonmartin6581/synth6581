######## Main program for MOS6581 synthesizer ###############

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
patch_folder = "synth_patches"
patch_name = "init"

sample_folder = "synth_samples"
 
samp_names = [  'wiz3_1c', 'wiz3_2f', 'wiz3_3b','wiz6_stabb', 'wiz6_popb','bad_guy_lead', 'bad_guy_bass', 'bad_guy_3_ghoul', 'mega_lead', 'mega1_arp','mont1b','mont2b',
                 'com1b', 'com2b', 'cyb1', 'cyb_bass', 'cyb_backing', 'zoid_riff', 'zoid_all',  'zoid_drums','cobra_bleep', 'cobra_bassline','cobra_bass',
                'thrust_drone','rat_sync','thr2','thr_bass'] #'wiz3_3',

#samp_names = [ 'cyb1', 'com1b', 'com2b'] # limited samples for fast load

pad_list = [['bad_guy_bass', 31],['bad_guy_lead', 55],['bad_guy_3_ghoul', 58],['cobra_bassline', 33],
            ['wiz6_popb', 75],['cobra_bleep',67],['cobra_bleep', 71],['cobra_bleep', 69],
            ['zoid_all', 76],['wiz6_stabb', 69],['com1b', 79],['cyb_bass', 39],
            ['_special','next_upper'],['_special','next_lower'],['_special','reset_upper'],['_special','reset_lower']]

params = {'Pedal' : [[0,1,'lin'], 64],
        
        'Param1' : [[0, 30, 'lin'], 18],
        'Param2' : [[0, 30, 'lin'], 19] ,
        'Param3' : [[0, 30, 'lin'], 16],
        'Param4' : [[0, 2047, 'lin'], 17],

        'Cutoff' : [[-32, 64, 'lin'], 74],

        'Resonance' : [[0, 15, 'lin'], 71],

        'FiltA' : [[0.2,0.998,'decay'], 73],
        'FiltD' : [[0.2,0.998,'decay'], 75],
        'FiltS' : [[0,1.,'lin'], 79],
        'FiltR' : [[0.2,0.998,'decay'], 72],
                
        'AmpA' : [[0, 15, 'lin'], 80],
        'AmpD' : [[0, 15, 'lin'], 81],
        'AmpS' : [[0, 15, 'lin'], 82],
        'AmpR' : [[0, 15, 'lin'], 83],
        'AmpL' : [[-64, 64, 'lin'], 85],

        'LFORate' : [[0.05,200,'exp'], 76],
        'LFOAmt' : [[0.0001,8,'exp'], 77],
        
        'Chorus' : [[1., 1.01, 'exp'], 93],
        
        'Volume' : [[0, 15, 'lin'], 7],
        'Pitch' : [[-12.0 - (24.0/128), 12.0, 'lin'], 0],
        'Modulation' : [[80, 3000, 'exp'], 1],

        'Prog1' : [[0, 6, 'menu'], 22],
        'Prog2' : [[0, 6, 'menu'], 23],
        'Prog3' : [[0, 6, 'menu'], 24],
        'Prog4' : [[0, 7, 'menu'], 25],
        'Prog5' : [[0, 7, 'menu'], 26],
        'Prog6' : [[0, 1, 'menu'], 27],
        'Prog7' : [[0, 4, 'menu'], 28],
        'Prog8' : [[0, 7, 'menu'], 29],
        'Prog9' : [[0, 3, 'menu'], 30],
        'Prog10' : [[0, 3, 'menu'], 31],
        'Loop' : [[0, 1, 'menu'], 55],
        
        'DelayAmt' : [[0, 1024, 'lin'] ,91] }

vc_on = [0,1,2] # All three voices active
refresh_time = 0.005 # refesh rate

fps = 1.0/refresh_time
from audio_constants import *
import sid_driver

sd = sid_driver.sid()
sd.reset_sid() # called early to silence the SID chips when restarting

import key_man # collects MIDI events and processes them
import level_man # converts midi knobs to actual useable levels
import chan_man # manages which channel is doing what
import samp_man # stores and plays SID samples to a synth channel
import dsp # this is for software generated dynamic level generation e.g. LFOs and envelopes

import time
import sys

print ("loading pygame")
import pygame.midi # this code uses pygame midi feature
import pygame.event
print ("loaded")

INVF = 16.777216 / 256 # This is the SID conversion factor from frequency to register value

pedal_down = 0 # This functionality has not been implemented yet

from signal import signal, SIGINT

def end_prog(signal_received, frame):
    sd.reset_sid()
    sd.all_sid(24,0)
    pygame.quit() # I can't work out how to prevent the bad pointer exception when I quit pygame
    patch_name = raw_input("Enter patch name to save or Enter to exit...")
    if patch_name:
        print ("Saving...", patch_name)
        sid.lvls.save_patch(patch_folder, patch_name)
    sys.exit()

signal(SIGINT, end_prog) # This is the interupt handler to ensure ctrl-c closes down gracefully(-ish)
  
class sid_synth:
    def __init__(self,patch_folder, patch_name, sample_folder, samp_names):
        
        sd.tone_change = False
        
        self.last_event_time = time.clock()

        self.adsr_mode = 0 # Whether 
        self.synth_levels = {} # When events arrive they update this dictionary of parameters. 
        self.adsr = {'a':[0,0,0], 'd':[0,0,0], 's':[0,0,0], 'r':[0,0,0]} # SID envelope generator params
        self.fmul = [1,1,1] # frequency multiplier for each frequency
        self.pwm = 2047 # this needs to be 3 voice #tofix

        self.cm = chan_man.chan_man() # create a channel manager to control the channels

        self.samp_names = samp_names

        self.sm = samp_manager.samp_man(sd) # initialises the sample manager
        for name in samp_names:
            self.sm.load_samp(name, sample_folder) # loads the SID samples to memory
       
# MARKER - CREATE MODULES
        self.adsrf = []
        self.lfoa = []
        self.lfob = []

        for chan in range(MAXCHANS): # create modules for the synth architecture to use
            self.adsrf.append(dsp.adsr())
            self.lfoa.append(dsp.lfo())        
            self.lfob.append(dsp.lfo())
        return
    
    def update_synth(self, event_list, level_list): # called cyclicly to process the event list and update the synth paramters
        if time.clock() - self.last_event_time > 1000:
            print ("timed out")
            end_prog()

        for event in event_list:
            event_type,note,velocity, source, samp = event
            if event_type in ['key_down','pad_down']:
                self.cm.add_note(note, velocity,source,samp)
            if event_type in ['key_up','pad_up']:
                self.cm.release_note(note,source)
                
            if event_type == 'transition':
                self.cm.transition_note(note,velocity, source)
               
        for level in level_list:
            level_type,knob,val = level
            if level_type == 'knob_turn':
                self.knob_to_synth(knob, val)
                self.synth_levels[knob] = val

            if level_type == 'adsr':
                self.adsr[knob] = val 

        for c in CHANNELS:
            reset = self.update_chan(c, self.cm.key_status[c], self.cm.note[c], self.cm.samp[c]) # A channel may decide that it has completed the note
            self.cm.advance_key_status(c, reset) # deal with key ages for future channel selection
        
        return

    def update_chan(self, c, key_status, note, samp): # chooses sample or synth activity and deals with timeouts
        reset = False
        if samp:
            if key_status == OSC_KEYDOWN:
                self.sm.chan_samp[c] = samp
                self.sm.start_samp(c,samp)

            gate = key_status >= OSC_KEYDOWN and key_status <= OSC_CONTINUE
            note = note+self.synth_levels['Pitch']
            if key_status != OSC_RESET:
                reset = self.sm.play_next_samp(c, note, gate)
            else:
                self.sm.mute_channel(c)
            if key_status > RELEASE_LENGTHS[int(self.sm.release[self.sm.chan_samp[c]])] * fps:
                reset = True
        else:
            self.update_synth_chan(c, key_status, note)
            if key_status > 5 * fps:
                reset = True
                note = 0

        return reset
    
    def update_synth_chan(self,c, key_status, note): # updates the synth with the latest levels        
 
        levels = self.synth_levels # just for shorthand and read only
 
        sd.update_adsr(c, self.adsr)
        
        self.lfoa_lev=self.lfoa[c].next_frame(0,-1,1,levels['Prog8'],0.5,levels['LFORate'],True, key_status)
        
        fm = levels['AmpL'] * self.adsrf[c].next_frame(levels['FiltA'],levels['FiltD'],levels['FiltS'],levels['FiltR'], key_status)
        
        # extra envelopes and lfos can be added here
        #self.lfob_lev=self.lfob[c].next_frame(0,-levels['DelayAmt'],levels['DelayAmt'],SINE,0.5,levels['LFORate'],True, key_status)

        sd.set_pwm (c,self.pwm + self.lfoa_lev * levels['DelayAmt'])

        flfo = note_to_freq(note) * self.lfoa_lev * levels['LFOAmt']

        if key_status:
            if levels['Prog7'] == 0 or levels['Prog7'] == 4:
                freq = note_to_freq(note+levels['Pitch'])+flfo 
                sd.set_freq(c,0,freq*self.fmul[0])
                sd.set_freq(c,1,freq*self.fmul[1] * levels['Chorus'])
                sd.set_freq(c,2,freq*self.fmul[2] * levels['Chorus'])
                cut_off = note_to_freq(note + levels['Cutoff'] )
                sd.set_filter(c, cut_off, levels['Resonance'] , levels['Prog4'], levels['Prog5'], levels['Volume'])

            if levels['Prog7'] == 1:
                freq = note_to_freq(note+levels['Pitch']+fm)+flfo 
                sd.set_freq(c,0,freq*self.fmul[0])
                sd.set_freq(c,1,freq*self.fmul[1] * levels['Chorus'])
                sd.set_freq(c,2,freq*self.fmul[2] * levels['Chorus'])
                cut_off = note_to_freq(note + levels['Cutoff'] )
                sd.set_filter(c, cut_off, levels['Resonance'] , levels['Prog4'], levels['Prog5'], levels['Volume'])
                
            if levels['Prog7'] == 2:
                freq = note_to_freq(note+levels['Pitch'])
                sd.set_freq(c,0,freq*self.fmul[0])
                sd.set_freq(c,1,freq*self.fmul[1] * levels['Chorus'])
                freq = note_to_freq(note+levels['Pitch'] +fm)
                sd.set_freq(c,2,(freq*self.fmul[2]) * levels['Chorus'])
                cut_off = note_to_freq(note + levels['Cutoff'] + self.lfoa_lev * levels['LFOAmt']*10)
                sd.set_filter(c, cut_off, levels['Resonance'] , levels['Prog4'], levels['Prog5'], levels['Volume'])

            if levels['Prog7'] == 3:
                freq = note_to_freq(note+levels['Pitch'])
                sd.set_freq(c,0,freq*self.fmul[0])
                sd.set_freq(c,1,freq*self.fmul[1] * levels['Chorus'])
                freq = note_to_freq(note+levels['Pitch'] +fm ) +flfo
                sd.set_freq(c,2,(freq*self.fmul[2] + flfo) * levels['Chorus'])
                cut_off = note_to_freq(note + levels['Cutoff'] )
                sd.set_filter(c, cut_off, levels['Resonance'] , levels['Prog4'], levels['Prog5'], levels['Volume'])
                
            if levels['Prog7'] == 4: # filter uses envelope
                cut_off = note_to_freq(note + levels['Cutoff'] + fm)
                sd.set_filter(c, cut_off, levels['Resonance'] , levels['Prog4'], levels['Prog5'], levels['Volume'])
            
        if key_status == OSC_KEYDOWN or (key_status == OSC_CONTINUE and self.tone_change):
            self.tone_change = False
            for vc in range(3):
                sd.note_down(c,vc,self.cm.velocity[c] )

        if key_status == OSC_RELEASE or key_status == OSC_RESET:
            for vc in range(3):              
                sd.note_up(c,vc)
        return
    
    def knob_to_synth(self,knob_name, level): # adsr_mode, levels, knob_names, tone_change, tone, ring_sync, knob, fmul, release_all

        if knob_name == '':
            return
        if knob_name in ['AmpA','AmpD','AmpS','AmpR']:
            if self.adsr_mode == 0:
                vc = [0,1,2]
            else:
                vc = [self.adsr_mode - 1]
            for v in vc:
                self.adsr[{'AmpA' : 'a', 'AmpD' : 'd', 'AmpS' : 's', 'AmpR' : 'r'}[knob_name]][v] = int(level)

        if knob_name == 'Param4':   
            val = int(level)
            self.pwm = val # all three voices get the same pwm value. This could be changed in future
            
        if knob_name == 'Volume':   
            val = int(level)

        if knob_name in 'Prog1,Prog2,Prog3':
            vc = {'Prog1':0,'Prog2':1, 'Prog3':2}[knob_name]
            self.tone_change = True
            print ("Adjust waveform of voice "+ str(vc))
            tone, ring = menu_to_tone(level)
            sd.set_tone(vc, tone)
            sd.set_ring(vc, ring)
            
        if knob_name == 'Prog4' :
            print( "Filter on = " + str(level))
            
        if knob_name == 'Prog5':
            print ("Filter mode = "+ str(level))
            
        if knob_name == 'Prog6':
            self.tone_change = True
            if int(level):
                sd.set_sync(2,1)
                print ("Oscillator 3 syncronised to Osc 2")
            else:
                sd.set_sync(2,0)
                print ("Sync off")
                
        if knob_name == 'Prog7' :    
            print (["ADSRF off",
                    "ADSRF assigned to all oscillator frequencies",
                    "ADSRF assigned to Osc 3 and LFO assigned to filter",
                    "ADSRF assigned to Osc 3 and LFO to OSC 3 only",
                    "ADSRF assigned to filter"][level])                 

        if knob_name == 'Prog9' :  
            print (["All ADSRs adjusted","Voice 0 ADSR adjust","Voice 1 ADSR adjust","Voice 2 ADSR adjust"][level])
            self.adsr_mode = level
                
        if knob_name == 'Prog8' :
            print (OSC_NAMES[level])
            
        if knob_name == 'Prog10' :   
            print (["Single","Dual","Note Arpeggio","Modulation Arpeggio"][level])
            self.cm.release_all()

        if knob_name in ['Param1', 'Param2', 'Param3']:
            vc = {'Param1' : 0, 'Param2' : 1, 'Param3' : 2}[knob_name]
            if int(level) > 20:
                self.fmul[vc] = int(level) - 20
            else:
                self.fmul[vc] = 1./(22 - int(level))
            if int(level) < 2:
                self.fmul[vc] = 0
            print ("VC1:"+str(self.fmul[0])[0:5]+" VC2:"+ str(self.fmul[1])[0:5]+ " +VC3:"+str(self.fmul[2])[0:5])
    
    
def menu_to_tone(val):
    tones = ["None", "Triangle", "Saw", "Pulse", "Pulse/Tri", "Noise", "Ring Triangle"]
    print (tones[val])
    ring = 0
    if val > 2:# this code removes tone 3 that doesnt work
        val +=1
    if val > 6: # Ring oscillator on
        val = 1
        ring = 1
    if val > 5: # this code removes tone 7 that doesnt work
        val = 8
    return val, ring

def print_time(seconds):
    print ("Time to complete")
    ms = seconds * 1000
    s, ms = divmod(ms, 1000)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    print ("%d:%02d:%02d:%03d" % (h, m, s, ms))

def note_to_freq(note):
    return 261.63*(1.05946309436**(note-60))
        
##################################################        
# Main program starts here
##################################################
    
sid = sid_synth(patch_folder, patch_name, sample_folder, samp_names) # declare a synth called SID

sd.set_control_mode('') # User options NEG, BLOCK, HALF, VELOCITY - could be part of a patch saving in a future version

lvls = level_man.levels(params) # create a level manager class for this synth
level_list = lvls.load_patch(patch_folder, patch_name) # this will produce a long list of level events to process

sid.update_synth([], level_list) # this initialises those level events

km = key_man.keys('KeyLab', samp_names) # Set up the midi keyboard

km.set_up_lower_keys(21, 48, 24, 0) 
km.set_up_upper_keys(21, 109, 0, 0)
km.set_up_pads(pad_list)

onoff = lvls.levels['Loop']

last_frame_time = time.clock()
    
while True:
    event_list, knob_list = km.get_midi_events() # get midi input of keys and knobs

    level_list = lvls.modify_level_list(knob_list) # this rescales the knobs and smooths out sliders

    event_list, special_list = km.modify_pad_events(event_list)
        
    if special_list: # specials are defined in pad_list by naming them as _special
        for special in special_list:
            if special == 'next_upper':
                km.upper_samp = km.pick_next_samp(km.upper_samp)
                print 'Upper:', km.upper_samp
            if special == 'next_lower':
                km.lower_samp = km.pick_next_samp(km.lower_samp)
                print 'Arpeg:', km.lower_samp
            if special == 'reset_upper':
                km.upper_samp = 0       
            if special == 'reset_lower':
                km.lower_samp = 0

    km.arp_tempo = lvls.levels['Modulation']
    
    if lvls.levels['Prog10'] == 3:
        event_list = km.modify_arpeg_events(event_list) # process any arpeggio related key presses
        km.update_arpeg_modulate(event_list)
    if lvls.levels['Prog10'] == 2:
        event_list = km.modify_arpeg_events(event_list) # process any arpeggio related key presses
        km.update_arpeg_notes(event_list)
    if lvls.levels['Prog10'] == 1:
        event_list = km.modify_lower_events(event_list) # process any arpeggio related key presses

    event_list = km.modify_upper_events(event_list) # this is applied last so that the lower events can take prioirty
                                                    # this then mops up the events left over - this way lower and upper keys can overlap
    km.check_unmodified_events(event_list) # warns if loop messed up the event modification process
    
    # events are now ready to go to the synth
    sid.update_synth(event_list, level_list)   
    if lvls.levels['Loop'] != onoff:
        end_prog()
    
    last_frame_time += refresh_time
    while (time.clock()<last_frame_time):
        pass 
end_prog(0,0)
# MARKER - END PROGRAM


