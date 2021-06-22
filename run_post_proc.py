from jetstream.post_proc import run_demeaning, SingleModelPostProcessor
import os
from dask.distributed import Client, LocalCluster

data_product = 'climate_model'# 'reanalysis'#  'historical' #
var_of_interest = 't_prime' #'t_ref', 'tas' 'eff_lat' #

if data_product == 'reanalysis':
    list_of_models = ["ds_1979_2021_lat_20_1D_renamed",
                      "ds_1950_1979_lat_20_1D_rename"]
    path_data = '/project2/moyer/jetstream/era5_processed_data/'
    path_postproc = '/project2/moyer/jetstream/era5_processed_data/post_processing_output/'

elif data_product == 'climate_model':
    path_data = '/project2/moyer/jetstream/cmip6_complete_gcms/'
    path_postproc = '/project2/moyer/jetstream/cmip6_complete_gcms/post_processing_output/'
    list_of_models = [#'GFDL-ESM4_ssp585_tas_daily',
            'MPI-ESM1-2-HR_ssp585_tas_daily',
#            'CESM2-WACCM_ssp585_tas_daily',
#            'IPSL-CM6A-LR_ssp585_tas_daily',
#            'UKESM1-0-LL_ssp585_tas_daily'#os.listdir(path_data)
    ]
elif data_product == 'historical':
    path_data = '/project2/moyer/jetstream/cmip6_processed_data/'
    path_postproc = '/project2/moyer/jetstream/cmip6_processed_data/post_processing_output/'
    list_of_models = ['CESM2-WACCM_hist_tas_daily',
            'GFDL-ESM4_hist_tas_daily',
            'IPSL-CM6A-LR_hist_tas_daily',
            'MPI-ESM1-2-HR_hist_tas_daily',
            'MRI-ESM2-0_hist_tas_daily'
            ]
else:
    raise NotImplementedError

for model in list_of_models:
    if var_of_interest in ['t_ref', 'tas']:
        label='t_prime'
    else:
        label=var_of_interest

    path_processed = f'{path_data}{model}/{model}_{label}*.nc4'

    if data_product == 'reanalysis':
        shortname = 'era5'+model[2:12]
    elif data_product == 'climate_model':
        shortname = model.split('-')[0]
    elif data_product == 'historical':
        shortname = model.split('-')[0] + '_hist'

    print('creating class for ', shortname)
    single = run_demeaning(path_processed,
                           shortname,
                           path_postproc,
                           var_of_interest,
                           decade=True
                           )

#    single = SingleModelPostProcessor(
#            path_to_input_files=path_processed,
#            diagnostic_var=var_of_interest,
#            season='DJF'
#            )
    single.diagnostic_plot(demean=True,
            path_to_save=f'{path_postproc}/diagnostic_plots/{shortname}_{var_of_interest}_demean')
