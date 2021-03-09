## Totalmix Command Line Tools
The tools in this repository are meant as supplement for RMEs Totalmix for controlling RME Interfaces over osc. They are especially useful when setting parameter for many channels e.g. activate the loopback function on a range of channels. 

Basic functions for toggling mute, loopback etc. were implemented. Future features will include functions for setting diagonal routing or other volume configurations and creating fadergroups via snapshot files.

In order to work properly the tool has to fetch the complete channel layout and channel gains. For that all channels have to be visible for the controller. So unhide all in the channel layout menu of totalmix.

`python ps-totalmixCli.py -f`
 
The fetched data is written into a json-file and must only refetched if the layout changes. (un-/hiding channels, change channel names or change stereo settings). A layer must not contain two or more channel with the same name. This might lead to confusing behavior because the channelnames were also used as orientation.


For activating e.g. loopback on output channel 3 to 10 and 12 to 18 you can write

`python ps-totalmixCli.py set output.3:10,12:18 loopback 1`

for further information see help

`python ps-totalmixCli.py -h`