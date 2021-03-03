from jetstream.post_proc import SingleModelPostProcessor, run_demeaning
import os
from dask.distributed import Client, LocalCluster

data_product = 'reanalysis' #climate_model
var_of_interest = 'eff_lat'

if data_product == 'reanalysis':
    list_of_models =["ds_1950_1979_lat_20_1D_rename","ds_1979_2021_lat_20_1D_renamed"]
    path_data = '/project2/moyer/jetstream/era5_processed_data/'
    path_postproc = '/project2/moyer/jetstream/era5_processed_data/post_processing_output/'

elif data_product == 'climate_model':
    path_data = '/project2/moyer/jetstream/cmip6_processed_data/'
    path_postproc = '/project2/moyer/jetstream/cmip6_processed_data/post_processing_output/'
    list_of_models = os.listdir(path_data)

else:
    raise NotImplementedError

client = Client()

for model in list_of_models:
    if model in ['MRI-ESM2-0_hist_tas_daily','UKESM1-0-LL_ssp585_tas_daily', 'post_processing_output']:
        continue

    if data_product == 'reanalysis':
        path_processed = f'{path_data}{model}/{model}_{var_of_interest}*.nc4'
        shortname = 'era5'+model[2:12]
    elif data_product == 'climate_model':
        path_processed = f'{path_data}{model}/{model}_{var_of_interest}*11*.nc4'
        shortname = model.split('-')[0]

    print('creating class for ', shortname )
    single=run_demeaning(path_processed,
            shortname,
            path_postproc,
            var_of_interest)
    single.diagnostic_plot(demean=False,
            path_to_save=f'{path_postproc}/diagnostic_plots/{shortname}_{var_of_interest}')
