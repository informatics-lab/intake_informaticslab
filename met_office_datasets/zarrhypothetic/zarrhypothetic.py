import json
from collections import namedtuple
from collections.abc import MutableMapping
from functools import partial
from itertools import product

import numpy as np
import xarray as xr
import zarr

FlagsProxy = namedtuple("FlagsProxy", ("c_contiguous",))
FlagsProxy.__new__.__defaults__ = (True,)

# values would ordinarily be an np array, so would contain dtype,
# shape etc - we dummy this just to have access to the is_c_contiguous flag
ValuesProxy = namedtuple("ValuesProxy", ("flags",))
ValuesProxy.__new__.__defaults__ = (FlagsProxy(),)

# data proxy to access chunksize
DataProxy = namedtuple("DataProxy", ("chunksize",))
DataProxy.__new__.__defaults__ = (None,)

# constructor signature not the same, but gives access to the attributes
# that we need
VariableProxy = namedtuple(
    "VariableProxy", ("dims", "shape", "dtype", "values", "data", "attrs")
)
VariableProxy.__new__.__defaults__ = (ValuesProxy(), DataProxy(), {})


class HypotheticZarrStore(MutableMapping):
    # For now define only the MutableMapping methods which are
    # overridden for zarr.storage.DirectoryStore
    # Could also implement:
    #     # mixins from base class
    #     def __contains__(self, item):
    #     def items(self):
    #     def values(self):
    #     def get(self, key, default=None):
    #     def __ne__(self, other):
    #     # added through mixin
    #     def pop(self, key, default=None):
    #     def popitem(self, kv):
    #     def update(self, **kwargs):
    #     def setdefault(self, key, default=None):
    METADATA_KEY = ".zmetadata"
    META_KEYS = [
        zarr.storage.array_meta_key,
        zarr.storage.attrs_key,
    ]
    ROOT_KEYS = [
        zarr.storage.group_meta_key,
        zarr.storage.attrs_key,
        METADATA_KEY,
    ]

    def __init__(
        self,
        dims,
        coord_vars,
        data_vars,
        chunks,
        loader_function,
        attrs=None,
        dtypes=None,
    ):
        # dims is a list/tuple of strs
        # coord vars is a dictionary of variables
        # datavars is a list of strs (assume all have the same dims -> same shape)
        # chunks is a dict describing chunks in a file (if missing, assume value is 1)
        # loader_function goes from coord values to data (via file)
        #   func assumed to return np array

        # optional:
        # attrs is a dict of global attrs for whole dataset
        # dtypes is a dict containing strings which specify the numpy dtype
        # of the data in the array - if not specified, float32 assumed

        # guard clause
        assert all(map(lambda dim: dim in coord_vars, dims))
        self.dims = dims
        self.attrs = attrs if attrs else {}
        self.chunks = chunks
        self.loader_function = loader_function

        # converting coord (data) arrays to dask arrays
        # to have access to number of chunks (put whole array in one chunk)
        self.coord_vars = {
            name: coord.copy().chunk() for name, coord in coord_vars.items()
        }
        if dtypes is None:
            dtypes = {}
        # need to do this after dims, chunks, coord_vars defined
        self.data_vars = {
            name: self._create_var_proxy(dtypes.get(name, "float32"))
            for name in data_vars
        }

    @property
    def vars(self):
        return dict(self.coord_vars, **self.data_vars)

    def _create_var_proxy(self, dtype, attrs=None, c_contiguous=True):
        if attrs is None:
            attrs = {}
        # dtype is a str passed into np.dtype()
        # calc: all data_vars have the same dims => same shape
        shape = tuple(map(lambda dim: len(self.coord_vars[dim]), self.dims))

        # get from dict, assume chunk of 1 if not present
        chunksize = self._chunksize(self.chunks, self.dims)
        # fake values to give acess to c_contiguous flag
        data = DataProxy(chunksize)
        values = ValuesProxy(FlagsProxy(c_contiguous))
        return VariableProxy(
            dims=self.dims,
            shape=shape,
            dtype=np.dtype(dtype),
            data=data,
            values=values,
            attrs=attrs,
        )

    @staticmethod
    def _chunksize(chunks, dims):
        return tuple(chunks.get(dim, 1) for dim in dims)

    @staticmethod
    def _num_chunks(var):
        return tuple(s // c for s, c in zip(var.shape, var.data.chunksize))

    @staticmethod
    def _var_mem_order(var):
        return "C" if var.values.flags.c_contiguous else "F"

    def _zgroup_dict(self):
        return json.dumps({"zarr_format": 2})

    def _zattrs_dict(self, variable=None):
        if variable is None:
            return json.dumps(self.attrs)
        else:
            return json.dumps(
                dict({"_ARRAY_DIMENSIONS": variable.dims}, **variable.attrs)
            )

    def _zarray_dict(self, variable):
        return json.dumps(
            {
                "chunks": variable.data.chunksize,
                "compressor": None,
                "dtype": variable.dtype.str,
                "fill_value": None,
                "filters": None,
                "order": self._var_mem_order(variable),
                "shape": variable.shape,
                "zarr_format": 2,
            }
        )

    def _zmetadata_dict(self):
        # if called from __getitem__, recursive (depth=2) and converts back and forth
        # between strings and dicts using json lib - should not be too slow though
        metadata = {}
        for key in filter(lambda key: key != self.METADATA_KEY, self.ROOT_KEYS):
            metadata[key] = json.loads(self[key].decode())
        for var in self.vars:
            for key in self.META_KEYS:
                key = f"{var}/{key}"
                # convert back from bytestring to regular string
                metadata[key] = json.loads(self[key].decode())
        return json.dumps({"metadata": metadata, "zarr_consolidated_format": 1})

    def _get_dim_values(self, chunk_idxs, dims):
        chunksize = self._chunksize(self.chunks, dims)
        # move to data index space rather than chunk indexing..
        data_idxs = list(map(lambda x: x[0] * x[1], zip(chunk_idxs, chunksize)))
        values = []
        for dim, idx in zip(dims, data_idxs):
            val = self.coord_vars[dim].values[idx]
            values.append(val.item())
        mapping = dict(zip(dims, values))
        return mapping

    def __getitem__(self, item):
        key = item.split("/")
        if len(key) == 1:
            var_name = None
            key = key[0]
        elif len(key) == 2:
            var_name, key = key
        else:
            raise KeyError(f"Invalid key: {item}")
        # mapping from keys to metadata returning methods
        accessor_mapping = {
            zarr.storage.array_meta_key: self._zarray_dict,
            zarr.storage.attrs_key: self._zattrs_dict,
            zarr.storage.group_meta_key: self._zgroup_dict,
            self.METADATA_KEY: self._zmetadata_dict,
        }
        # getting metadata:
        if key in accessor_mapping:
            accessor = accessor_mapping[key]
            if var_name is not None:
                accessor = partial(accessor, self.vars[var_name])
            return accessor().encode()
        # getting coords (stored in object):
        var = self.vars[var_name]
        if var_name in self.coord_vars:
            data = var.values
        else:
            # getting data (from elsewhere):
            accessor = self.loader_function
            # returning data - key are chunk indices
            chunk_idxs = tuple(int(x) for x in key.split("."))
            # access_values are the starting values for that chunk in all dims
            # as well as the variable name (first part of the key)
            access_values = self._get_dim_values(chunk_idxs, var.dims)
            access_values["variable_name"] = var_name
            data = accessor(access_values)
            if not isinstance(data, np.ndarray) and data is not None:
                raise TypeError("Loader function should return a numpy.ndarray or None")
            if data is None:
                data = np.full(
                    shape=var.data.chunksize,
                    fill_value=np.nan,
                    dtype=var.dtype,
                    order=self._var_mem_order(var),
                )
            # could potentially do some checking that shape and dtype are as expected if loaded
        return data.tobytes(order=self._var_mem_order(var))

    def __setitem__(self, item, value):
        raise NotImplementedError("Read-only access provided.")

    def __delitem__(self, item):
        raise NotImplementedError("Read-only access provided.")

    def __iter__(self):
        return self.keys()

    def __len__(self):
        # slow, could be calculated...
        # for now use zarr.storage.DirectoryStore implementation
        return sum(1 for _ in self.keys())

    def keys(self):
        for key in self.ROOT_KEYS:
            yield key

        for name, var in self.vars.items():
            for key in self.META_KEYS:
                yield f"{name}/{key}"
            num_chunks = self._num_chunks(var)
            chunk_iters = [range(x) for x in num_chunks]
            # slow, likely not to be used often
            # could calculate faster (at the cost of more memory)
            # by using np.meshgrid for cartesian products etc.
            for chunk_idx in product(*chunk_iters):
                chunk_idx = ".".join(str(x) for x in chunk_idx)
                yield f"{name}/{chunk_idx}"

    @staticmethod
    def _xarray_variables_equal(var1, var2):
        return (
            var1.dims == var2.dims
            and var1.attrs == var2.attrs
            and np.array_equal(var1.values, var2.values)
        )

    def __eq__(self, other):
        # only do some basic checking here.. could do more
        # could speed up by exiting early if any evaluates to False
        correct_type = isinstance(other, HypotheticZarrStore)
        dims_same = self.dims == other.dims
        data_vars_same = self.data_vars == other.data_vars
        coord_var_keys_same = self.coord_vars.keys() == other.coord_vars.keys()
        coord_var_values_same = all(
            [
                self._xarray_variables_equal(self_var, other_var)
                for self_var, other_var in zip(
                    self.coord_vars.values(), other.coord_vars.values()
                )
            ]
        )
        coord_vars_same = coord_var_keys_same and coord_var_values_same
        return correct_type and dims_same and data_vars_same and coord_vars_same

    def clear(self):
        raise NotImplementedError("Read-only access provided.")


class HypotheticZarrCloner(HypotheticZarrStore):
    def __init__(self, target, *args, **kwargs):
        if not isinstance(target, MutableMapping):
            raise ValueError("Target must be a MutableMapping")
        self.target = target
        super().__init__(*args, **kwargs)

    # keeps chunking exactly the same
    def __getitem__(self, item):
        try:
            return self.target[item]
        except KeyError:
            value = super().__getitem__(item)
            self.target[item] = value
            return value
