# Controls the sliders and knobs on the a MIDI keyboard and converts them to useable settings 

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

import pickle
import math

class levels:
    def __init__(self, params): 
            
        self.params = params
        self.knob_names = {}
        for param in params:
            self.knob_names[params[param][1] ] = param

        self.current_knob_name = ''
        self.knob_levels = {}
        self.levels = {}
        
        for knob_name in self.params:
            self.knob_levels[knob_name] = 0
            self.levels[knob_name] = 0
        self.lev_steady = True
        
    def load_patch(self, patch_folder, patch_name):
        self.lev_steady = True
        self.current_knob_name = ''
        self.target_level = 0
        self.knob_levels = {}
        self.levels = {}
        knob_list = []
        level_list = []
        
        for knob_name in self.params:
            self.knob_levels[knob_name] = 0
            self.levels[knob_name] = 0

        try:
            file_name = patch_folder + "/knob_list_" + patch_name + '.dat'
            print ("loading ", file_name)
            with open (file_name, 'rb') as fp:
                [kls,self.adsr_a,self.adsr_d,self.adsr_s,self.adsr_r] = pickle.load(fp)

                fp.close()
                #self.knob_levels = pickle.load(fp)
        except:
            s = "failed to load knob_list_" + patch_name + ".dat"
            print (s)
            print ("loading knob_list.dat instead")
            with open (patch_folder + "/knob_list_init.dat", 'rb') as fp:
                [kls,self.adsr_a,self.adsr_d,self.adsr_s,self.adsr_r] = pickle.load(fp)             
                #self.knob_levels = pickle.load(fp)
                fp.close()

        print (self.knob_names)
        for i in range(len(kls)): # this code needs to not be dependent on MIDI knob numbers
            if i in self.knob_names:
                #print (i, self.knob_levels[self.knob_names[i]], kls[i])
                #self.knob_levels[self.knob_names[i]] = kls[i]
                #self.set_level(self.knob_names[i],kls[i])
                knob_list.append(['knob_turn',i, kls[i]])
        
        #self.adsr = {'a':self.adsr_a, 'd':self.adsr_d, 's':self.adsr_s, 'r':self.adsr_r} # hack to fix save mode
        for knob in knob_list:
            knob_name = self.knob_names[knob[1]]
            new_level = self.set_level(knob_name, knob[2])
            level_list.append(['knob_turn', knob_name, new_level])
                              
        level_list.append(['adsr','a', self.adsr_a])
        level_list.append(['adsr','d', self.adsr_d])
        level_list.append(['adsr','s', self.adsr_s])
        level_list.append(['adsr','r', self.adsr_r])
                #self.adsr_mode = -1 # temporarily prevents the adsr being written to by knob_to_synth which cant deal with different values for each voice 
        self.show_levels()
        return level_list

    
    def save_patch(self, sid, patch_folder, patch_name):
        print ("Saving...", patch_name)
        print (self.knob_levels)
        kls = [0]*256
        for i in range(256):
            if i in self.knob_names:
                kls[i] = self.knob_levels[self.knob_names[i]]
        print (kls)
        print (sid.adsr['a'],sid.adsr['d'],sid.adsr['s'],sid.adsr['r'])
        with open(patch_folder +'/knob_list_' + patch_name + '.dat', 'wb') as fp:
            pickle.dump([kls,sid.adsr['a'],sid.adsr['d'],sid.adsr['s'],sid.adsr['r']], fp)
        fp.close()    

    def new_load_patch(self, patch_folder, patch_name):
        self.lev_steady = True
        self.current_knob_name = ''
        self.target_level = 0
        self.knob_levels = {}
        self.levels = {}
        knob_list = []
        level_list = []
        
        for knob_name in self.params:
            self.knob_levels[knob_name] = 0
            self.levels[knob_name] = 0

        try:
            file_name = patch_folder + "/knob_list_" + patch_name + '.dat'
            print ("loading ", file_name)
            with open (file_name, 'rb') as fp:
                [self.knob_levels,self.adsr_a,self.adsr_d,self.adsr_s,self.adsr_r] = pickle.load(fp)

                fp.close()
                #self.knob_levels = pickle.load(fp)
        except:
            s = "failed to load knob_list_" + patch_name + ".dat"
            print (s)
            print ("loading knob_list.dat instead")
            with open (patch_folder + "/knob_list_init.dat", 'rb') as fp:
                [self.levels,self.adsr_a,self.adsr_d,self.adsr_s,self.adsr_r] = pickle.load(fp)             
                #self.knob_levels = pickle.load(fp)
                fp.close()
        
        #self.adsr = {'a':self.adsr_a, 'd':self.adsr_d, 's':self.adsr_s, 'r':self.adsr_r} # hack to fix save mode
        for knob_name in self.levels:
            level_list.append(['knob_turn', knob_name, self.level[knob_name]])
                              
        level_list.append(['adsr','a', self.adsr_a])
        level_list.append(['adsr','d', self.adsr_d])
        level_list.append(['adsr','s', self.adsr_s])
        level_list.append(['adsr','r', self.adsr_r])
                #self.adsr_mode = -1 # temporarily prevents the adsr being written to by knob_to_synth which cant deal with different values for each voice 
        self.show_levels()
        return level_list
    

    def new_save_patch(self, patch_folder, patch_name):
        print ("Saving...", patch_name)
        print (self.knob_levels)
        with open(patch_folder +'/knob_list_' + patch_name + '.dat', 'wb') as fp:
            pickle.dump([self.knob_levels,sid.adsr['a'],self.adsr['d'],self.adsr['s'],self.adsr['r']], fp)
        fp.close()
        #pickle.dump(cb.synth.menu_levels, fp)
    #pygame.midi.Input.close

    def modify_level_list(self, knob_list): # takes the list of knob numbers and vals and updates self.levels, returns the levels for the synth to interpret
        level_list = []
        for knob_item in knob_list:
            level_type,knob_num,knob_level = knob_item
            if knob_num in self.knob_names:
                knob_name = self.knob_names[knob_num]
                if level_type == 'knob_turn':
                    level = self.new_level(knob_name, knob_level)
                    if self.params[knob_name][0][2] in 'menu count list' and knob_level == 0:
                        pass # this is to remove the button release event which has no value
                    else:
                        level_list += [[level_type,knob_name,level]] # this is what normally happens
        knob_name, level = self.manage_levels()
        if knob_name:
            level_list += [['knob_turn',knob_name,level]]
        return level_list

    def manage_levels(self): # Makes smooth transitions for a knob under user control

        if self.lev_steady == True or self.current_knob_name == '':
            return '',0
        knob_name = self.current_knob_name
        #print 'ml ',knob
        #if self.knob_names[knob] == 'Volume':
        #    print (self.knob_levels[knob], self.target_level)
        #    self.knob_levels[knob] = self.target_level # Smoothly adjusting the volume on a SID is not a thing...
        step = self.target_level - self.knob_levels[knob_name]
        step_size = abs(step)
        if step_size > 10:
            self.knob_levels[knob_name] += step * 0.5
        if step_size > 0.1 :
            self.knob_levels[knob_name] += step * 0.1
        else: 
            self.knob_levels[knob_name] = self.target_level
        if step_size < 0.01:
            self.knob_levels[knob_name] = self.target_level
            self.lev_steady = True
        else:
            self.set_level(knob_name, self.knob_levels[knob_name])
        return knob_name, self.levels[knob_name]

    def new_level(self, knob_name, knob_level): # fader, params, lev_steady, knob_levels, current_knob, target_level, set_level
        fader = self.params[knob_name][0][2]
        
        if fader in 'menu count list':
            self.lev_steady = True
            if knob_level == 127: # if a button was pressed
                self.knob_levels[knob_name] = int(self.knob_levels[knob_name]  + 1)
                self.set_level(knob_name, self.knob_levels[knob_name])
            return self.levels[knob_name]
        
        self.lev_steady = False
        if knob_name != self.current_knob_name:
            if self.current_knob_name:
                new_level = self.set_level(self.current_knob_name, self.target_level)
                #print 'n', new_level, self.current_knob_name, self.target_level, self.levels[self.current_knob_name]
            self.current_knob_name = knob_name
            self.target_level = knob_level
        else:
            self.target_level = knob_level
        return self.levels[knob_name]

            
    def set_level(self, knob_name, knob_level):  # knob_levels, pedal_down, params, fader, levels, does knob_to_synth
        self.knob_levels[knob_name] = knob_level
        lo_level, hi_level, fader = self.params[knob_name][0]

        if fader == 'lin':
            new_level = float(lo_level) + float(knob_level) * float((hi_level - lo_level)) / 127.

        if fader == 'decay':
            decay = 1. - (0.93 ** float(knob_level))
            new_level = float(lo_level) + decay * float(hi_level - lo_level)
        if fader in 'menu count': #and  knob_level == 127:
            self.knob_levels[knob_name] = knob_level # knob_level is incremented by scan_key->new_level->set_level
            if self.knob_levels[knob_name] > hi_level:
                self.knob_levels[knob_name] = 0
            new_level = self.knob_levels[knob_name] #Fixes the need to turn this knob level into a level because level is not saved

            if hi_level == 1:
                print (self.knob_levels[knob_name] == 1)
            else:
                if fader == 'count':
                    print (new_level)
                else:
                    pass# (OSC_NAMES[int(new_level)],new_level)
        if fader == 'list' : #and  knob_level == 127:
            if self.knob_levels[knob_name] > len(lo_level):
                self.knob_levels[knob_name] = 0
            elif hi_level > 0 and self.knob_levels[knob_name] > hi_level:
                self.knob_levels[knob_name] = 0
            new_level = lo_level[self.knob_levels[knob_name]] #Fixes the need to turn this knob level into a level because level is not saved
            print ("set list", self.knob_levels[knob_name] , new_level, knob_name, knob_level, param)
        if fader == 'freq':
            new_level =  (1.0594631 ** (float(knob_level) * lo_level)) * hi_level
        if fader == 'exp':
            log_ratio = math.log10(hi_level / (lo_level + 0.000001))
            new_level =  (10 ** (float(knob_level) / 127 * log_ratio)) * lo_level

        self.levels[knob_name] = new_level
        return new_level

    def show_levels(self):
        for name in self.params:
            if name != '':
                print (name, self.knob_levels[name], self.levels[name])
