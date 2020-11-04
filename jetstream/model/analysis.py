from jetstream.model.template import Template

class Analysis(Template):
    """ Methods template for reanalysis data
    """

    temp_var = 't2m'

    def cut(self, array_obj):
        """ Wrapper function to slice xarray using a dictionary

        Args:
        xr_array (xr.DataArray or xr.Dataset)

        returns: xr.Dataset or xr.Dataarray
        """

        valid_keys = {
            key: self.subset_dict[key] for key in self.subset_dict
            if key in array_obj.coords
        }

        xr_data = array_obj.sel(valid_keys)

        return xr_data.squeeze()


