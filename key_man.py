######## Manages the functions of keys and pads ###############

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

print ("loading pygame")
import pygame.midi
import pygame.event
print ("loaded")
import time

class keys:
    def __init__(self,midi_name, samp_names): #'KeyLab'
        
        self.arp_start_time = 0
        self.arp_seq = []
        self.new_arp_ready = False
        self.new_arp_seq = []
        self.arp_list = []
        self.arp_count = 0
        self.arp_tempo = 480
        self.arp_record = False
        self.arp_loop_length = 0
        self.arp_loop_time = self.arp_loop_length * 60 / self.arp_tempo
        self.arp2on = False
        self.last_note = 0
        
        self.upper_samp = 0
        self.lower_samp = 0
        self.samp_names = samp_names
        
        self.event_types = {144 : 'key_down', 128: 'key_up', 153:'pad_down', 137:'pad_up', 176: 'knob_turn', 224:'knob_turn', 169: 'pad_after', 208 : 'key_after'}
        pygame.midi.init()
        c = pygame.midi.get_count()
        print ("%s midi devices found" % c)
        for i in range(c):
            midi_dev = pygame.midi.get_device_info(i)
            print ("%s name: %s input: %s output: %s opened: %s" % (midi_dev))
            if midi_name in midi_dev[1].decode() and midi_dev[2]:
                device = i
        if device:
            print ("Setting device to %s" % device)
            self.midi_dev = pygame.midi.Input(device)
        else:
            self.midi_dev = 'undefined'
        print ("dev",self.midi_dev)
        return 

    def close_midi(self):
        self.midi_dev.close()

    def get_midi_events(self):
        event_list = []
        knob_list = []
        for midi_in in pygame.midi.Input.read(self.midi_dev,1):
            note = midi_in[0][1]
            m_in = midi_in[0][0]
            
            if m_in in self.event_types:
                event_type = self.event_types[m_in]
            else:
                print ("Event type not found in key_man.update_events", m_in)
                event_type = ''
                
            if event_type == 'knob_turn':
                knob_num = midi_in[0][1]
                #knob = self.lvls.knob_name(num) # this is not right
                knob_level = midi_in[0][2]
                knob_list += [[event_type, knob_num, knob_level]]

            if event_type in ['key_down','pad_down']:
                velocity = int(midi_in[0][2])
                event_list+=[[event_type, note, velocity, '', 0]]
                
            if event_type in ['key_up', 'pad_up']:
                event_list+=[[event_type, note, 0, '', 0]]
                
        return event_list, knob_list
        
    def set_up_lower_keys(self, low_note, high_note, note_shift, samp):
        self.low_lower_note = low_note
        self.high_lower_note = high_note
        self.lower_note_shift = note_shift
        self.lower_samp = samp

    def set_up_upper_keys(self, low_note, high_note, note_shift, samp):
        self.low_upper_note = low_note
        self.high_upper_note = high_note
        self.upper_note_shift = note_shift
        self.upper_samp = samp
        
    def set_up_pads(self, pad_list):
        self.pad_list = pad_list
        
    def pick_next_samp(self, samp): # samp_names
        if samp == 0:
            return self.samp_names[0]
        i = self.samp_names.index(samp)+1
        if i >= len(self.samp_names):
            return self.samp_names[0]
        return self.samp_names[i]
    
    def modify_upper_events(self, event_list):
        new_event_list = []
        for event in event_list:
            event_type,note,velocity, source, samp = event
            if event_type in ['key_down','key_up'] and note >= self.low_upper_note and note < self.high_upper_note:
                if source == '':
                    source = 'upper'
                    samp = self.upper_samp
            new_event_list += [[event_type,note,velocity, source, samp]]    

        return new_event_list
    
    def modify_lower_events(self, event_list):
        new_event_list = []
        for event in event_list:
            event_type,note,velocity, source, samp = event
            if event_type in ['key_down','key_up'] and note >= self.low_lower_note and note < self.high_lower_note:
                if source == '':
                    source = 'lower'
                    samp = self.lower_samp
            new_event_list += [[event_type,note,velocity, source, samp]]

        return new_event_list     
         
    def modify_pad_events(self,event_list):
        new_event_list = []
        special_list = []
        for event in event_list:
            event_type,note,velocity, source, samp = event
            if event_type in ['pad_down','pad_up']:
                if source == '':
                    source = 'pad'
                    samp = self.pad_list[note-40][0]
                    note = self.pad_list[note-40][1]
                if samp =='_special':        # ignore undefined pads
                    if event_type == 'pad_down': # special only activates on pad_down
                        special_list += [note]
                else:
                    new_event_list += [[event_type,note,velocity, source, samp]]
            else:
                new_event_list += [[event_type,note,velocity, source, samp]]
                
        return new_event_list, special_list
    
    def modify_arpeg_events(self, event_list):
        removed_events = []
        for event in event_list:
            event_type,note,velocity, source, samp = event
            if event_type == 'key_down' and note >= self.low_lower_note and note < self.high_lower_note:
                self.add_arpeg_note(note, velocity)
                removed_events.append(event)
                
            if event_type == 'key_up' and note >= self.low_lower_note and note < self.high_lower_note:
                self.release_arpeg_note (note)
                removed_events.append(event)
                
        for event in removed_events: # remove the original key presses
            event_list.remove(event)
            
        return event_list
    
    def check_unmodified_events(self, event_list, show_all=0):
        for event in event_list:
            event_type,note,velocity, source, samp = event
            if show_all:
                print (event)
            else:
                if source == '':
                    print ("warning undefined event:", event)
    
    def add_arpeg_note (self, note, velocity):
        
        note += self.lower_note_shift
        if self.arp_loop_time == 0:
            self.arp_loop_time = 500 # to fix
        if self.arp_count == 0:
            self.arp_start_time = time.clock() + 0.05# + self.arp_loop_time# + 0.05 # make it sample within 0.1 seconds
            self.arp_record = True
            self.arp_loop_length = 0
            self.new_arp_seq = []
        self.arp_count += 1  
        if self.arp_record == True:
            self.new_arp_seq.append([self.arp_loop_length, note,100,0.75,False]) 
            self.arp_loop_length += 1
            #self.new_arp_seq=[[1, 54, 100, 0.9, False], [1, 58, 100, 0.9, False], [2, 66, 100, 0.9, False]]
            self.new_arp_ready = True
        else:
            step_time = (time.clock() - self.arp_start_time)
            
            next_step = int(self.arp_loop_length * step_time / self.arp_loop_time)# position in note steps
            if next_step >= self.arp_loop_length:
                next_step = 0
                
            for x in range(self.arp_loop_length):                           # hunt for the next blank slot
                step, arp_note, velocity, note_length, status = self.new_arp_seq[next_step]
                if velocity == 0:
                    self.new_arp_seq[next_step] = [next_step, note,100,0.75,False] # Hack of arpegiator
                else:
                    next_step += 1
                    if next_step >= self.arp_loop_length:
                        next_step = 0
        
    def release_arpeg_note(self,note):
        
        note += self.lower_note_shift
        found = False            
        for x in range(self.arp_loop_length):
            step, arp_note, velocity, note_length, status = self.new_arp_seq[x]
            if arp_note == note:
                self.new_arp_seq[x]= [step,arp_note,0,note_length, status] # silence this note
                found = True

        self.arp_count -= 1 # keep a tally of how many notes are pressed (differnt to arp loop length)
            
        if found:
            self.new_arp_ready = True
   
    def update_arpeg_notes(self, event_list):
        step_time = (time.clock() - self.arp_start_time)

        if self.arp_loop_length == 0:
            return
        
        if self.arp_tempo == 0:
            self.arp_tempo = 500 # to fix

        self.arp_loop_time = self.arp_loop_length * 60.0 / self.arp_tempo

        if step_time > self.arp_loop_time or step_time < 0: # this is the moment it resets the next sequence
            if self.new_arp_ready: 
                for x in range(len(self.arp_seq)): # first release all notes
                    step, note, velocity, note_length, status = self.arp_seq[x]
                    if status == True:
                        event_data = ['key_up', note, 0, 'arpeg', self.lower_samp] # release note
                        event_list.append(event_data)                      
                self.arp_seq = self.new_arp_seq
                self.new_arp_ready = False
                 
        if self.arp_record == False:            #Dont go to beginning when recording
            while step_time > self.arp_loop_time:
                self.arp_start_time += self.arp_loop_time
                step_time -= self.arp_loop_time
        elif step_time > len(self.arp_seq) * 60 / self.arp_tempo:
                self.arp_record = False
            
        step_pos = self.arp_loop_length * step_time / self.arp_loop_time # position in note steps

        for x in range(len(self.arp_seq)):
            note_start, note, velocity, note_length, status = self.arp_seq[x] # hunt through arp_seq
            note_end = note_start + note_length                               # step is the note_start
            if note_end >= self.arp_loop_length:                        # should this be an while?
                note_end -= self.arp_loop_length

            if note_end > note_start: # This is the normal case when note_end is after note_start
                if step_pos > note_end or step_pos < note_start: # pos is outside of note
                    if status:              # if note is on
                        self.arp_seq[x][4] = False # switch of note
                        if velocity == 0:
                            self.arp_seq[x] = [0,0,0,0,0] # release_arpeg_note told us to delete this
                        event_data = ['key_up', note, 0, 'arpeg', self.lower_samp] # release note
                        event_list.append(event_data)  
                elif step_pos > note_start and step_pos < note_end: # a note is found
                    if not status:          # it is new too
                        self.arp_seq[x][4] = True
                        if velocity:
                            event_data = ['key_down', note, velocity, 'arpeg', self.lower_samp] # add note
                            event_list.append(event_data)

            else:               # different case if note_end is before note_start. It has wrapped
                if step_pos > note_end and step_pos < note_start: 
                    if status: # if note is on
                        self.arp_seq[x][4] = False
                        if velocity == 0:
                            self.arp_seq[x] = [0,0,0,0,0] # release_arpeg_note told us to delete this
                        event_data = ['key_up', note, 0, 'arpeg', self.lower_samp] # release note
                        event_list.append(event_data) 
                elif step_pos > note_start or step_pos < note_end: # test this first since note end is less than note start
                    if not status:  # it is new
                        self.arp_seq[x][4] = True
                        if velocity:
                            event_data = ['key_down', note, velocity, 'arpeg', self.lower_samp] # add note
                            event_list.append(event_data)
        #if event_list:
        #    print event_list
        return event_list
    

    def update_arpeg_modulate(self, event_list):

        step_time = (time.clock() - self.arp_start_time)
        if self.arp_loop_length == 0:
            return
        self.arp_loop_time = self.arp_loop_length * 60 / self.arp_tempo

        if step_time > self.arp_loop_time or step_time < 0: # this is the moment it resets the next sequence
            if self.new_arp_ready:
                any_on = False
                for x in range(len(self.new_arp_seq)): # first relelase all notes
                    step, note, velocity, note_length, status = self.new_arp_seq[x]
                    if velocity:
                        any_on = True
                    self.arp_seq = self.new_arp_seq
                self.new_arp_ready = False
                if any_on == False:
                    self.arp2on = False # No notes are down anymore
                    event_data = ['key_up', self.last_note, 0, 'arpeg', self.lower_samp] # add note
                    self.last_note = note
                    event_list.append(event_data)
                    self.arp_count = 0
                    
        if self.arp_record == False:            #Dont go to beginning when recording
            while step_time > self.arp_loop_time:
                self.arp_start_time += self.arp_loop_time
                step_time -= self.arp_loop_time
        elif step_time > len(self.arp_seq) * 60 / self.arp_tempo:
                self.arp_record = False
            
        step_pos = self.arp_loop_length * step_time / self.arp_loop_time # position in note steps

        for x in range(len(self.arp_seq)):
            note_start, note, velocity, note_length, status = self.arp_seq[x] # hunt through arp_seq
            note_end = note_start + note_length                               # step is the note_start
            if note_end >= self.arp_loop_length:                        # should this be an while?
                note_end -= self.arp_loop_length

            if note_end > note_start: # This is the normal case when note_end is after note_start
                if step_pos > note_end: # Note has ended
                    if status:              # if note is on
                        self.arp_seq[x][4] = False # switch off note
                elif step_pos > note_start: # a note is found
                    if not status:          # it is new too
                        self.arp_seq[x][4] = True
                        if self.arp2on == False:
                            if velocity:
                                event_data = ['key_down', note, velocity, 'arpeg', self.lower_samp] # add note
                                self.arp2on = True
                                self.last_note = note
                                event_list.append(event_data)
                        else:
                            if velocity:
                                event_data = ['transition', self.last_note, note, 'arpeg', self.lower_samp] # add note
                                self.last_note = note
                                event_list.append(event_data)
            else:               # different case if note_end is before note_start. It has wrapped
                if step_pos > note_start: # test this first since note end is less than note start
                    if not status:  # it is new
                        self.arp_seq[x][4] = True
                        if self.arp2on == False:
                            if velocity:
                                event_data = ['key_down', note, velocity, 'arpeg', self.lower_samp] # add note
                                self.arp2on = True
                                self.last_note = note
                                event_list.append(event_data)
                                self.arp2on = True
                        else:
                            if velocity:
                                event_data = ['transition', self.last_note, note, 'arpeg', self.lower_samp] # add note
                                self.last_note = note
                                event_list.append(event_data)
                elif step_pos > note_end:
                    if status: # if note is on
                        self.arp_seq[x][4] = False

        return event_list
    
    def adjust_arpeg_note_length(self, length): # arp_seq, 
        for i in range(len(self.arp_seq)):
            self.arp_seq[i][3] = length

