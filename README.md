# ERA-5 Reanalysis Product retriever

The `reanalysis_getter` is a wrapper of the [CDS API][1]. The package is still
in a _bare bones_ stage, but it is able to translate multiple requests to the
CDS API and retrieve the desired data, either waiting in the CDS user queue, or
downloading the data directly (after waiting for the data to be processed). 

## Configuration and How-to Install

A `environment.yml` file is added to the repo to generate the development
environment. You can install [Miniconda][3] and run `conda env create -f
environment.yml`. After that, you can activate the environment and start using
the `conda activate reanalysis_env`. 

Following the API configuration, a `~/.cdsapirc` file with API credentials must
be created before doing any request. See the API [documentation][2] for more
details on how to get your user credentials. 

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


## TODO

 - [x] Run with the CDS API.
 - [ ] Add SQLite for storing requested data (API has no way to check data from
   Python]
 - [ ] Integrate with `xarray` and `iris` to extract data to n-arrays. 
 - [ ] Integrate to Luigi/Airflow (?) pipeline 

[1]: https://cds.climate.copernicus.eu/cdsapp#!/home
[2]: https://cds.climate.copernicus.eu/api-how-to
[3]: https://docs.conda.io/en/latest/miniconda.html
