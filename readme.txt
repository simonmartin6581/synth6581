Revision History:

June 2nd 2021 - First release 
June 5th 2021 - Uppdated to run on Python 3.7

Description:

Three programs are available here:

synth6581.py 

This is an electronic musical instrument - it is a polyphonic multitimbral synthesizer that can handle up to 8 audio channels.
It requires a MOS6581 IC wired to a Raspberry Pi according to the schematics. It is configured to use a KeyLab88 keyboard for input.
Code can be easily modified to work with other keyboards and also other single chip synthesizers

SID_multi_player.py

Plays C64 songs on one or more SID boards
Does not require a MIDI keyboard. Just a SID or two, or six.

SID_multi_player_keys.py

Plays C64 songs on one or more SID boards
Knobs and sliders on a Keylab88 have been assigned to control delay, volume and pitch

To compile the C library for the sid_driver.py file to use, type:

gcc -Wall -pthread -shared -o sid_lib.so sid_lib.c -lpigpio 

Longer documentation will be available soon. The source code is extensively commented.
