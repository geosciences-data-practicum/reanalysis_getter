import cftime
import xarray as xr
from descriptors import cachedproperty
from distributed.client import _get_global_client
from jetstream.model.template import Template

class Model(Template):
    """ Methods template for GCM
    """

    temp_var = 'tas'

    @cachedproperty
    def data_array(self):
        """ Lazy load model/analysis data into memory. 
        """

        client = _get_global_client()

        xr_data = xr.open_mfdataset(self.path_to_files,
                                 chunks=self.chunks,
                                 parallel=True)

        if not all(x in list(xr_data.coords) for x in self.DIMS):
            xr_data = xr_data.rename({
                'latitude': 'lat',
                'longitude': 'lon',
            })

        if isinstance(xr_data.time.values[0], cftime._cftime.DatetimeNoLeap):
            datetime_index = xr_data.indexes['time'].to_datetimeindex()
            xr_data['time'] = datetime_index

        if self.subset_dict is not None:
            xr_data = self.cut(xr_data)
            print('Cut data')

        return xr_data

    def cut(self, array_obj):
        """ Wrapper function to slice GCM using a dictionary

        Slice GCM with a user-defined dictionary and take only the first
        elements of member_id or nband, if exists

        Args:
        xr_array (xr.DataArray or xr.Dataset)

        returns: xr.Dataset or xr.Dataarray
        """

        valid_keys = {
            key: self.subset_dict[key] for key in self.subset_dict
            if key in array_obj.coords
        }

        other_coords = [x for x in list(array_obj.coords) if x not in self.DIMS]

        xr_data = array_obj.sel(valid_keys)
        xr_data = xr_data.drop(other_coords)

        return xr_data.squeeze()


