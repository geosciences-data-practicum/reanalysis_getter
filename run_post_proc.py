from jetstream.post_proc import SingleModelPostProcessor
import os

var_of_interest = 'eff_lat'
path_data = '/project2/moyer/jetsream/era5_processed_data/'
path_postproc = '/project2/moyer/jetsream/era5_processed_data/post_processing_output/diagnostic_plots/'
path_aggregate_postproc = '/project2/moyer/jetsream/postproc_aggregate'

for model in os.listdir(path_data):
	if model in ['MRI-ESM2-0_hist_tas_daily','UKESM1-0-LL_ssp585_tas_daily']: 
		continue
	path_processed = f'{path_data}{model}/{model}_{var_of_interest}*.nc4'
	print(path_processed)
	shortname='era5'
	#shortname = model.split('-')[0]
	print('creating class for ', shortname )
	single = SingleModelPostProcessor(path_to_files=path_processed,
                 path_to_save_files=path_postproc+shortname+var_of_interest,
                 diagnostic_var=var_of_interest,
                 season='DJF')

	single.diagnostic_plot(demean=False)


