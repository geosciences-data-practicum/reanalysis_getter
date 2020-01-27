
from datetime import datetime
from src.requester import request_wrapper
request_wrapper(file_name = None, 
                start_date = datetime(2007, 12 ,1),
                end_date = datetime(2008, 3, 1),
                variables_of_interest = [167.128], # See ERA-5 documentation for more on this
                subday_frequency = 12, #every 12 hours
                pressure_levels = 'sfc'
                )
