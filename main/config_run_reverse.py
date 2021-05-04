from datetime import datetime
from jetstream.requester import request_wrapper
from dateutil.relativedelta import relativedelta
from jetstream.utils import datetime_range

if __name__ == '__main__':

    dates_ranges = datetime_range(start=datetime(2010, 12, 1),
                                  end=datetime(2020, 3, 1),
                                  delta={'years': 1})

    for init_date in dates_ranges:
        request_wrapper(file_name = None, 
                        path='/project2/moyer/jetstream/era-5-data/',
                        start_date = init_date,
                        end_date = init_date + vedelta(months=4),
                        variables_of_interest = 'surface_pressure', # See ERA-5 documentation for more on this
                        subday_frequency = 'hourly', #every 12 hours,
                        #product='historical',
                        pressure_levels = ['sfc']
                       )
