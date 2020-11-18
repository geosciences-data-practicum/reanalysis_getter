# Infrastructure helpers

## 1. Use `dask` in `SLURM` jobs without notebooks

We process each model separately using `dask`. Due to the sheer size of some of
the models, we divide computation by time. The user can choose their time window
of preference or use the 5-year default. `runner.py` has a
command-line-interface (CLI) that reads a dataset, divide it using time, process
and save the data into a user-defined location. We can use some of `dask` tools
to make this process faster.

```bash
(base) [ivanhigueram@midway2-login1 infrastructure]$ $SCRATCH/reanalysis_env/bin/python runner.py --help
Usage: runner.py [OPTIONS]

  Calculate all methods from paper for a specified model by years

  Since we are memory constrained, this function takes the jetstream.Model
  object and allow to run the methods pipeline for a user defined group of
  years. The time_step allow us to define the width of the year window.

  Arguments:  - product_path: str path to raw model in NetCDF format. -
  save_path: str path to save output data from modeling - start_year: int
  start year. 2015 is set as default following GCM models - end_year: int
  end year. 2100 is set as default following GCM models - time_step: int
  Define a step to divide years. 5 is the default value.

  Returns:  None. Save to path directly.

Options:
  --product_path TEXT   Path to model data
  --save_path TEXT      Path to save output
  --time_step INTEGER   Number of years per file
  --start_year INTEGER  Start year
  --end_year INTEGER    End year
  --log_level TEXT
  --help                Show this message and exit.
```

All out methods are based on `xarray` and `Dask`. This allow us to use the power
of `dask.distributed` to lazy load massive datasets, divide them, and process
data. Distributted computing in `dask` has two parts: first, a scheduler that
centralizes computation and  assign tasks to each node/worker. Second, `dasks` 
uses workers that process each chunk of the data (in the case of our datasets, 
each chunk is defined as a time unit, like days). 

We have two scripts, one per each element of the process describe above. The
script `launch-dask.sh` orchestrates the creration of the scheduler, and a
user-defined number of workers: 

```bash
./launch-dask.sh <path_to_climate_model> <path_to_save_folder> <number-of-workers>
```

This will spawn one job per worker, but additionally, a job that runs the
scheduler. The jobid will be printed:

```bash
Launching dask scheduler
6100956
Launching dask workers ()
Submitted batch job 6100957
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
           6100956   broadwl dask-jet ivanhigu PD       0:00      1 (None)
6100956 broadwl dask-jet ivanhigu PD 0:00 1 (None)
6100956 broadwl dask-jet ivanhigu CF 0:01 1 midway2-0116
6100956 broadwl dask-jet ivanhigu R 0:02 1 midway2-0116
Launching model in workers
2020-10-12 00:04:56,276 - runner.py - INFO - Initializing t prime calculation
2020-10-12 00:04:56,277 - runner.py - INFO - Start processing -- 2015-12-01 to 2020-03-01
```

## 2. `load_stuff.sh`: exploring data with jupyter notebooks

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
