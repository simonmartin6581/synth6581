sample_folder = "synth_samples"

songs = [['Billie_Jean' , 50], ['Beat_It', 100], ['Bad_guy',100], ['Commando',50], ['Wiz3L',180], ['Wiz4L',200], ['Wiz5L',200], ['Wiz6L',200],
         ['Paperboy', 50], ['Ocean_loader_3',50], ['Oxygen_4', 50], ['Mission_impossible' , 50], ['1942',50], ['Thrust',50], ['Cobra',50],['Lazy_jones',50],
         ['Cybernoid',50]] # columns of 8

song_num =  4# select which song to play

#vols =   [ 1.00,  0.90,  0.80,  0.5 ,  0.20,  0.15] # attenuation on each channel. max = 1.0
#delays = [ 0   ,  0   ,  0   ,  1   ,150   ,500   ] # delays in milliseconds
#pitches =[60.00, 60.03, 48.01, 79.02, 60.01, 60.00] # 60 is 1x frequency, 72 is 2x frequency, 79.02 is 3x frequency


vols =   [ 1.00,  1.0,  0.50,  0.50,  0.50,  0.30] # attenuation on each channel. max = 1.0 - good for Oxygene 4
delays = [ 0   ,  1   , 0   ,  0   ,100   ,500   ] # delays in milliseconds
pitches =[60.00, 60.02,48.02, 35.98, 60.05, 60.07] # 60 is 1x frequency, 72 is 2x frequency, 79.02 is 3x frequency


vols =   [ 1.00,  1.0,  0.50,  0.50,  0.50,  0.90] # attenuation on each channel. max = 1.0 - good for Wiz 6L
delays = [ 0   ,  1   , 0   ,  0   ,100   ,250   ] # delays in milliseconds
pitches =[60.00, 60.02,48.02, 35.98, 60.05, 60.07] # 60 is 1x frequency, 72 is 2x frequency, 79.02 is 3x frequency

f = 120
vols =   [ 5.50,  0.5 ,  0.30,  0.20,  0.20,  0.10] # attenuation on each channel. max = 1.0 - good for 
delays = [20   , 20   , 20   ,  0   ,  f   ,2*f   ] # delays in milliseconds
pitches =[60.00, 60.02, 71.98, 47.98, 60.05,60.07] # 60 is 1x frequency, 72 is 2x frequency, 79.02 is 3x frequency




vols =   [ 0.5 ,  0.5 ,  0.50,  0.50,  0.25,  0.25] # attenuation on each channel. max = 1.0 - good for Cybernoid
delays = [ 0   , 60   ,  0   ,  0   ,  0   ,240   ] # delays in milliseconds
pitches =[60.00, 60.02, 71.98, 47.98, 60.05, 60.07] # 60 is 1x frequency, 72 is 2x frequency, 79.02 is 3x frequency


params = {'Pedal' : [[0,1,'lin'], 64],

        'FiltA' : [[36, 84, 'lin'], 73],
        'Param1' : [[36, 84, 'lin'], 18],
        'Param2' : [[36, 84, 'lin'], 19] ,
        'Param3' : [[36, 84, 'lin'], 16],
        'Param4' : [[36, 84, 'lin'], 17],
        'DelayAmt' : [[36, 84, 'lin'] ,91],

        'FiltD' : [[1, 1000, 'exp'], 75],          
        'Cutoff' : [[1, 1000, 'exp'], 74],
        'Resonance' : [[1, 1000, 'exp'], 71],
        'LFORate' : [[1, 1000, 'exp'], 76],
        'LFOAmt' : [[1, 1000, 'exp'], 77],
        'Chorus' : [[1, 1000, 'exp'], 93],

        
        'FiltS' : [[1, 1000, 'exp'], 79],

        'FiltR' : [[0, 1, 'lin'], 72],
        'AmpA' : [[0, 1, 'lin'], 80],
        'AmpD' : [[0, 1, 'lin'], 81],
        'AmpS' : [[0, 1, 'lin'], 82],
        'AmpR' : [[0, 1, 'lin'], 83],
        'AmpL' : [[0, 1, 'lin'], 85],


        
        'Volume' : [[0, 15, 'lin'], 7],
        'Pitch' : [[-12.0 - (24.0/128), 12.0, 'lin'], 0],
        'Modulation' : [[0, 1, 'lin'], 1],

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
        
}


sample_folder = "synth_samples"

vc_on = [0,1,2] # All three voices active
speed = 0.005 # refesh rate


vc_on = [1,1,1] # select which voices to play
CHANNELS = [0,1,2,3,4,5] # select which channels are enabled

#from sid_driver import *
#from samp_manager import *
import sid_driver

MAXCHANS = 8

sd = sid_driver.sid()
sd.reset_sid()


import time
import sys
import level_man
import key_man
import samp_man

print ("loading pygame")
import pygame.midi
import pygame.event
print ("loaded")

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



sd.set_control_mode('') # User options NEG, BLOCK, HALF, VELOCITY - should be part of a patch saving but not enough midi controls 
    
lvls = level_man.levels(params) # create a level manager class for this synth

km = key_man.keys('KeyLab') # Set up the midi keyboard

km.set_up_arpeg(21, 48, 12, 0) # define where on the keyboard the arpeggiator exists
km.set_up_lower_keys(0, 0, 0, 0) 
km.set_up_upper_keys(48, 109, 0, 0)

onoff = lvls.levels['Loop']

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

pitch_list = {'FiltA': 0,'Param1' : 1, 'Param2' : 2, 'Param3' : 3, 'Param4' : 4, 'DelayAmt' : 5}
volume_list = {'FiltR': 0, 'AmpA' : 1, 'AmpD' : 2, 'AmpS' : 3, 'AmpR' : 4, 'AmpL' : 5}
delay_list = {'FiltD': 0, 'Cutoff' : 1, 'Resonance' : 2, 'LFORate' : 3, 'LFOAmt' : 4, 'Chorus' : 5}

for knob_name in pitch_list:
    lvls.levels[knob_name] = 60
for knob_name in volume_list:
    lvls.levels[knob_name] = 0
for knob_name in delay_list:
    lvls.levels[knob_name] = 1
        
for i in range(fps*1000): # provide a 1000 second time out
    
    event_list, knob_list = km.get_midi_events() # get midi input

    level_list = lvls.modify_level_list(knob_list) # this rescales the knobs and smooths out sliders

    for knob_name in pitch_list:
        pitch = lvls.levels[knob_name]
        p = int(pitch /12)
        rem = (pitch - p * 12) / 20
        pitch = p * 12 + rem
        pitches[pitch_list[knob_name]] = int(100*pitch)*0.01

    for knob_name in volume_list:
        c = volume_list[knob_name]
        vols[c] = int(100*lvls.levels[knob_name])*0.01
        sm.adjust_volume(c, vols[c])

    for knob_name in delay_list:
        dels[delay_list[knob_name]] = int(100*lvls.levels[knob_name])*0.01
    if level_list:
        print ("vols   :",vols)
        print ("pitches:",pitches)
        print ("dels   :",dels)
        
    for c in CHANNELS:
        while steps[c] + dels[c] < i:
            sm.play_next_samp(c,pitches[c],1,0)
            steps[c]+=1 
    last_frame_time += refresh_time
    while (time.clock()<last_frame_time):
        pass # insert bitcoin mining code here


end_prog(0,0)
