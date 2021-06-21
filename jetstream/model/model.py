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

        if isinstance(xr_data.time.values[0], cftime._cftime.datetime):
            datetime_index = xr_data.indexes['time'].to_datetimeindex()
            xr_data['time'] = datetime_index

        if self.subset_dict is not None:
            xr_data = self.cut(xr_data)
            print('Cut data')

        if self.season is not None:
            xr_data = xr_data.where(xr_data.time.dt.season == self.season,
                                    drop=True)

        if self.rescale_longitude is True:
            xr_data = xr_data.assign_coords(lon=(((xr_data.lon + 180) % 360) -
                                                 180)).sortby('lon')

        return xr_data[self.DIMS + [self.temp_var]].squeeze()

    def cut(self, array_obj):
        """ Wrapper function to slice GCM using a dictionary

        Slice GCM with a user-defined dictionary and take only the first
        elements of member_id or nband, if exists

        Args:
        xr_array (xr.DataArray or xr.Dataset)

        returns: xr.Dataset or xr.Dataarray
        """

        valid_keys = {
            key: self.subset_dict[key]
            for key in self.subset_dict if key in array_obj.coords
        }

        other_coords = [
            x for x in list(array_obj.coords) if x not in self.DIMS
        ]

        xr_data = array_obj.sel(time=valid_keys['time'])
        xr_data = xr_data.drop(other_coords)

        if 'lat' in valid_keys.keys():
            xr_data = xr_data.where(xr_data.lat > valid_keys['lat'], drop=True)
        if 'lon' in valid_keys.keys():
            xr_data = xr_data.where(xr_data.lat > valid_keys['lat'], drop=True)

        return xr_data.squeeze()
