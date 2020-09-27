from jetstream.model.template import Template

class Model(Template):
    """ Methods template for GCM
    """

    temp_var = 'tas'

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


