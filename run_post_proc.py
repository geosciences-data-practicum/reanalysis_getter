from jetstream.post_proc import run_demeaning, SingleModelPostProcessor
import os
from dask.distributed import Client, LocalCluster

data_product = 'reanalysis'# 'climate_model'
var_of_interest = 'eff_lat' #'t_prime' #'t_ref', 'tas'

if data_product == 'reanalysis':
    list_of_models = ["ds_1979_2021_lat_20_1D_renamed",
                      "ds_1950_1979_lat_20_1D_rename"]
    path_data = '/project2/moyer/jetstream/era5_processed_data/'
    path_postproc = '/project2/moyer/jetstream/era5_processed_data/post_processing_output/'

elif data_product == 'climate_model':
    path_data = '/project2/moyer/jetstream/cmip6_processed_data/'
    path_postproc = '/project2/moyer/jetstream/cmip6_processed_data/post_processing_output/'
    list_of_models = ['GFDL-ESM4_ssp585_tas_daily',
            'MPI-ESM1-2-HR_ssp585_tas_daily',
            'CESM2-WACCM_ssp585_tas_daily',
            'IPSL-CM6A-LR_ssp585_tas_daily',
            'UKESM1-0-LL_ssp585_tas_daily']#os.listdir(path_data)

else:
    raise NotImplementedError

# client = Client()

for model in list_of_models:
    if model in ['MRI-ESM2-0_hist_tas_daily', 'UKESM1-0-LL_ssp585_tas_daily',
            'post_processing_output']:
        continue

    if var_of_interest in ['t_ref', 'tas']:
        label='t_prime'
    else:
        label=var_of_interest
    if data_product == 'reanalysis':
        path_processed = f'{path_data}{model}/{model}_{label}*.nc4'
        shortname = 'era5'+model[2:12]
    elif data_product == 'climate_model':
        path_processed = f'{path_data}{model}/{model}_{label}*11*.nc4'
        shortname = model.split('-')[0]

    print('creating class for ', shortname)
    single = run_demeaning(path_processed,
                           shortname,
                           path_postproc,
                           var_of_interest,
                           decade=True
                           )
 #   single = SingleModelPostProcessor(
 #           path_to_input_files=path_processed,
 #           diagnostic_var=var_of_interest,
 #           season='DJF'
 #           )
 #   single.diagnostic_plot(demean=True,
 #           path_to_save=f'{path_postproc}/diagnostic_plots/{shortname}_{var_of_interest}_demean')
