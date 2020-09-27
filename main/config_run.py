from datetime import datetime
from src.requester import request_wrapper
from dateutil.relativedelta import relativedelta
from src.utils import datetime_range

if __name__ == '__main__':

    dates_ranges = datetime_range(start=datetime(1990, 12, 1),
                                  end=datetime(2018, 12, 1),
                                  delta={'years': 1})

    for init_date in dates_ranges:
        request_wrapper(file_name = None, 
                        path='/project2/geos39650/jet_stream/cdsapi_requested_files/',
                        start_date = init_date,
                        end_date = init_date + relativedelta(months=3),
                        variables_of_interest = '2m_temperature', # See ERA-5 documentation for more on this
                        subday_frequency = 12, #every 12 hours
                        pressure_levels = ['sfc']
                       )
