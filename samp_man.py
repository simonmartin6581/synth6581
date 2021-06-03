######## Manages the C64 music playback samples ###############

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

class samp_man():
    def __init__(self,sd):
        # these five variables hold the sample info
        self.sd = sd
        self.samp = {} # the poke list for the samp
        self.length = {} # samp length
        self.loop = {} # where to loop back to (no loop if equal to length)
        self.note_orig = {} # play middle C to hear the original
        self.voice_orig = {} # what voices the samp recommends
        self.release = {} # value to override the samp release when gates are off
        self.frate = {}
        
        #These hold the channel status
        self.chan_samp =  [0]*8 # the samp on the channel
        self.poke_index = [0]*8 # where it is in the samp
        self.step_count = [0]*8
        self.vol_adj =    [1]*8
        self.samp_vol =   [0]*8
        self.f_now = [[0,0,0]]*8 # need to know what the samp freq is, not just the sid freq
        
    def cut_samp(self, orig, name, start_val, end_val, loop_val, note_orig, voice_orig, release_val, frate):
        if end_val<start_val:
            print ("Cannot save due to end_val %d and start_val %d" % (end_val, start_val))
            return False
        if loop_val<start_val:
            print ("Cannot save due to loop_val %d and start_val %d" % (loop_val, start_val))
            return False     
        if loop_val>end_val:
            print ("Cannot save due to loop_val %d and end_val %d" % (loop_val, end_val))
            return False
        self.samp[name]=self.samp[orig][start_val:end_val]
        self.length[name] = end_val-start_val
        self.loop[name] = loop_val-start_val
        self.note_orig[name] = note_orig
        self.voice_orig[name] = voice_orig
        self.release[name] = release_val
        self.frate[name] = frate
        return True
        
    def save_samp(self, name, file_name, folder = ""):
        if len(folder):
            file_name = folder+'/'+file_name
        print ("Saving:",file_name)
        with open (file_name+".dat", 'wb') as fp:
            pickle.dump(self.samp[name],fp)
            pickle.dump(self.length[name],fp)
            pickle.dump(self.loop[name],fp)
            pickle.dump(self.note_orig[name],fp)
            pickle.dump(self.voice_orig[name],fp)
            pickle.dump(self.release[name],fp)
            pickle.dump(self.frate[name],fp)
        fp.close
        return True
        
    def load_song(self, name, folder = ""):
        file_name = name +'.dat'
        if folder:
            file_name = folder+'/'+file_name
        print ("Loading:",name)
        with open (file_name, 'rb') as fp:
            self.samp[name]=pickle.load(fp)
            self.length[name] = len(self.samp[name])
            self.loop[name] = 0
            self.note_orig[name] = 60
            self.voice_orig[name] = [1,1,1]
            self.release[name] = 8
            self.frate[name] = 1
        fp.close

    def load_samp(self, name, folder = ""):
        file_name = name +'.dat'
        if folder:
            file_name = folder+'/'+file_name
        print ("Loading:",name)
        with open (file_name, 'rb') as fp:
            self.samp[name]=pickle.load(fp)
            self.length[name] = pickle.load(fp)
            self.loop[name] = pickle.load(fp)
            self.note_orig[name] = pickle.load(fp)
            print ("nominal note:",self.note_orig[name])
            self.voice_orig[name] = pickle.load(fp)
            self.release[name] = pickle.load(fp)
            self.frate[name] = pickle.load(fp)
        fp.close

    def start_samp(self, c, name):
        self.poke_index[c] = 0
        self.chan_samp[c] = name

    def mute_channel(self, c):
        for addr in range(0,21,7):
            self.sd.write_sid(c,addr+0,0)
            self.sd.write_sid(c,addr+1,0)            
            self.sd.write_sid(c,addr+4,self.sd.get_sid(c, addr+4)&254)
            
    def gates_off(self,c, release):
        for addr in range(0,21,7):
            self.sd.write_sid(c,addr+4,self.sd.get_sid(c, addr+4)&254)
            sr = self.sd.get_sid(c, addr+6)

            get_rel = sr & 15
            if get_rel<release:
                self.sd.write_sid(c,addr+6,(sr&240)+get_rel)
            else:
                self.sd.write_sid(c,addr+6,(sr&240)+release)
            self.sd.write_sid(c,addr+5,0)
            
    def reset_channel(self, c):
        for addr in range(23):
            self.sd.write_sid(c,addr,0)
        self.sd.write_sid(c,24,31)

    def adjust_volume(self, c, adj):
        self.vol_adj[c] = adj
        vol_reg = self.sd.get_sid(c,24)
        current_vol = vol_reg & 15
        current_filt = vol_reg & 240
        desired_vol = int(self.vol_adj[c] * self.samp_vol[c] )
        if current_vol != desired_vol:
            self.sd.write_sid(c, 24, current_filt + desired_vol)
        
    def play_next_samp(self, c, note, gate, view = False): # note of zero prevents pitch shift
        lc = int(self.step_count[c])
        self.step_count[c] += self.frate[self.chan_samp[c]]
        if lc == int(self.step_count[c]):
            return False
                
        Done = False
        while not Done:
            poke = self.samp[self.chan_samp[c]][int(self.poke_index[c] )]
            self.poke_index[c] += 1
            
            if self.poke_index[c] >=self.length[self.chan_samp[c]]: # end of samp reached
                if self.loop[self.chan_samp[c]] >= 0:
                    self.poke_index[c] = self.loop[self.chan_samp[c]] # loop it round
                if self.loop[self.chan_samp[c]] == self.length[self.chan_samp[c]]:
                    self.poke_index[c] = self.length[self.chan_samp[c]]-1 # no looping so just stop the samp moving
                    self.gates_off(c,self.release[self.chan_samp[c]])
                    return True
            addr = poke[0] - 54272
            data = poke[1]
            vc = int(addr/7)
            if vc<3:
                vc_addr = addr - vc * 7
            else:
                vc_addr = None        

            if vc_addr == 0 and note: # modifying freq Lo
                self.f_now[c][vc] = int(self.f_now[c][vc] & 65280) + data                   
                ndata = pitch_shift(self.note_orig[self.chan_samp[c]], self.f_now[c][vc], note)
                data = ndata&255
                if self.voice_orig[self.chan_samp[c]][vc]: # don't adjust this register if the channel is off 
                    self.sd.write_sid(c, addr+1, ndata >> 8) # need to update freq registers in pai
            if vc_addr == 1 and note: # modifying freq Hi
                self.f_now[c][vc] = int(data * 256 + (self.f_now[c][vc] & 255))
                ndata = pitch_shift(self.note_orig[self.chan_samp[c]], self.f_now[c][vc], note)
                data = ndata >> 8
                if self.voice_orig[self.chan_samp[c]][vc]:
                    self.sd.write_sid(c, addr-1, ndata & 255) # need to update freq registers in pairs
            if vc_addr == 4 and not gate: # gating sound
                data = data & 254
            if vc_addr == 6 and not gate:
                if data & 15 > self.release[self.chan_samp[c]]:
                    data = (data&240) + self.release[self.chan_samp[c]] # make sure the poke does not stretch the release
            if addr == 24:
                self.samp_vol[c] = data & 15
                data  = int(data & 240) + int(self.vol_adj[c] * (data & 15)) # If a silent sample changes the filter mode, it causes clicks
            if addr < 25:
                if vc>2 or self.voice_orig[self.chan_samp[c]][vc]:
                    self.sd.write_sid(c, addr, data) #pwm setting lo
            else:
                Done = True
        if not gate:
            self.gates_off(c,self.release[self.chan_samp[c]])
        if view:
            self.sd.print_sid(c, self.poke_index[c]-1)
        return False

def note_to_freq(note):
    return 261.63*(1.05946309436**(note-60))

def pitch_shift(note_original, f_now, note): # f_now
    f_note = note_to_freq(note)
    f_original = note_to_freq(note_original)
    shift = f_note / f_original
    return int(f_now * shift)

