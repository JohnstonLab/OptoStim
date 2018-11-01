# OptoStim
Software for design and control of optogenetic experiments

OptoStim is GUI driven software to facilitate targeted patterned illumination of neurons expressing optogenetic actuators. 
Using a digital-micromirror-device (DMD), OptoSim provides single photon patterned illumination to neurons 
identified with either 2-photon and/or epifluorescence microscopy. Alignment of the DMD and image planes is achieved 
with homography matrices automatically calculated from user defined points. Optical stimulation points can be selected 
from images read directly from micromanager supported cameras or from images imported from 2-photon microscopy. 
Using a low cost A/D board (Labjack), OptoStim can easily integrate with electrophysiology or 2-photon imaging experiments, 
where it can act as the "master" controlling the timing of all events or act as a "slave" waiting for signals from 
other equipment. In the protocol design, stimulus points can be incremented linearly or randomly with each loop of 
multiple trial experiments and all settings and experimental protocols can be saved and loaded via JSON files. 
OptoStim can also stream and display data from Arduino microcontrollers to display/monitor behavioural or 
physiological parameters. OptoSim can also utilise inputs from microcontrollers to control closed-loop experiments.


![alt text](https://github.com/JohnstonLab/OptoStim/blob/master/optostim/OptoStimLogo.jpeg?raw=true)
