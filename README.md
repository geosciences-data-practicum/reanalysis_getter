# Jetstream - A replication library for the paper [insert paper name here]

This library contain the replication code for the paper **[paper name here]**.
Data adquisition, processing, and methods are included here. You can download 
either model or reanalysis data and calculate: `t_ref` and `t_prime`, and also
generate some derivative products, like anomalies and Hovmuller plots to explore
the movement of wind masees in the Northern Hemisphere

## Data adquisition

The `reanalysis_getter` is a wrapper of the [CDS API][1]. The package is still
in a _bare bones_ stage, but it is able to translate multiple requests to the
CDS API and retrieve the desired data, either waiting in the CDS user queue, or
downloading the data directly (after waiting for the data to be processed). 

### API Credentials

Following the API configuration, a `~/.cdsapirc` file with API credentials must
be created before doing any request. See the API [documentation][2] for more
details on how to get your user credentials.

## Data processing

We run our tests on two types of products: `reanalysis` (ERA-5), and several CIMP6
global climate models `model`. To process both, the user can use `jetstream.model.Analysis`
or `jetstream.model.Model` to either process reanalysis data or GCM data. Both classes
are abstract classes inherited from `jetstream.model.template` and adapted to capture 
all the particularities from each data set. 

This project is heavily reliant on both Dask and `xarray`, and uses the parallel powers 
from the latter to take big datasets and process the outlined methods in our paper.
Hence, there are some hardware requirements that are needed to fully replicate our methods
on a complete product, especially with daily data. 

Both classes are able to take a `dask.distributed.Client` object from the environment and
start calculation using the powers of embarassing distributed computing, onn both local and
remote environments. 

## Configuration and How-to Install

You can use: `python setup.py install --user` to install the modules of this library.
We recoment you to use a `virtualenv` to avoid conflicts with your local libraries, or
use any of the Dask Docker images. 

# Use case

Download sub-daily (each 3 hours )surface temperature (2-meter temperature)
between December 2007 and March 2008: 

```python
from datetime import datetime
from src.requester import request_wrapper
request_wrapper(file_name = None, 
                start_date = datetime(2007, 1 ,1),
                end_date = datetime(2008, 3, 1),
                variables_of_interest = [167.128] # See ERA-5 documentation for more on this
                subday_frequency = 3,
                pressure_levels = 'sfc'
                )
```

Data will be requested and a queue will start. Once data is processed remotely,
the download process will start. By default, data will be stored in the
`cdsapi_requested_files` directory. 


[1]: https://cds.climate.copernicus.eu/cdsapp#!/home
[2]: https://cds.climate.copernicus.eu/api-how-to
[3]: https://docs.conda.io/en/latest/miniconda.html
[4]: https://github.com/ecmwf/cfgrib
[5]: https://scitools.org.uk/iris/docs/latest/
