### Description  

This script draws processes/threads tree from strace output.
Work with strace v5.15 and above. Set of arguments to right parse output further:
`strace -o <strace_output_file> -ttt -Y -f -e trace=execve,clone,exit <command>`  
`./strace-visualizer.py -i <strace_output_file> [-o <image.png>]`  

![example](examples/example1.png)

### Install  
1) Install python3 and python3-pip in your system.  
2) Install virtualenv package also:  
`pip3 install virtualenv`  
`source ~/.profile`  
(note for Ubuntu 21.10)  
Installation package virtualenv with `sudo apt install python3-virtualenv` was cause of error:  
> "ModuleNotFoundError: No module named 'virtualenv'"  
3) Create virtualenv project:  
`virtualenv -p python3 <dir_name> `  
4) `source <dir_name>/bin/activate`  
5) Install the python-requirements:  
`pip3 install Pillow`  

#### Requirements
- python3 
- python3-pip

### Running
Activation python virtual environment must be performed before running script:  
`source <virtualenv_dir>/bin/activate`  

`./strace-visualizer.py -i <strace_output> [-o <image.png>]`  

Type `deactivate` if you need to exit from virtualenv
