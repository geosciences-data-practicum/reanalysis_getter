# Infrastructure helpers

RCC Cluster has a lot of tricks! Hopefully, Amanda's experience and this bash
files will help the user to navigate these with ease by using some simple
functions.

### `load_stuff.sh`: Jupyter notebook runner and environment manager

The `load_stuff.sh` command creates an environment using the library information
(located in the `env` folder in the root of the project), and has the option to
start a Jupyter Notebook directly from the bash while setting the IP socket to
your local machine. The function has a succinct help: 


```
[you@midway2-login1 reanalysis_getter]$ ./env/load_stuff.sh -h
______  _____  _____     ___                   _
| ___ \/  __ \/  __ \   |_  |                 | |
| |_/ /| /  \/| /  \/     | |_   _ _ __  _   _| |_ ___ _ __
|    / | |    | |         | | | | | '_ \| | | | __/ _ \ '__|
| |\ \ | \__/\| \__/\ /\__/ / |_| | |_) | |_| | ||  __/ |
\_| \_| \____/ \____/ \____/ \__,_| .__/ \__, |\__\___|_|
                                  | |     __/ |
                                  |_|    |___/
   __________             ______________
  |:""""""""i:           | ............ :
  |:        |:           | :          | :
  |: >boba  |:           | :          | :
  |:________!:           | :>@wwa.com | :
  |   .....  :---_____---| :__________! :
  |  '-----" :           |..............:
  | @        :"-__-_     |"""""""""""""":
  |..........:    _-"    |..............:
  /.::::::::.\   /\      /.::::::::.:::.\
 /____________\ (__)    /________________\
Usage: ./env/load_stuff.sh (-h | -i | -b | -r |)
OPTIONS:
   -h|--help                   Show this message
   -i|--info                   Show information about the environment
   -b|--build-conda-env        Build the conda reanalysis_env
   -r|--run-jupyter-env        Run Jupyter Notebook in the environment

EXAMPLES:
   Activate RCC Anaconda module and install conda env:
        $ ./load_stuff.sh -b
   Activaate and run a Jupyter notebook in local note:
        $ ./load_stuff.sh -r


```
