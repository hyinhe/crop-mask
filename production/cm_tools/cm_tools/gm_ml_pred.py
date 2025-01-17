import logging
import fsspec
import joblib
import xarray as xr
from odc.stats.model import Task
from typing import Tuple, Dict, Optional, Any, Sequence
from odc.stats.plugins._registry import register
from odc.stats.plugins import StatsPluginInterface
from datacube.model import Dataset
from datacube.utils.geometry import GeoBox
from deafrica_tools.classification import predict_xr
from cm_tools.post_processing import post_processing
from cm_tools.feature_layer import gm_mads_two_seasons_prediction

_log = logging.getLogger(__name__)


class PredGMS2(StatsPluginInterface):
    """
    Prediction from GeoMAD
    """

    source_product = "gm_s2_semiannual"
    target_product = "crop_mask_<region>"

    def __init__(
        self,
        urls: Dict[str, Any],
        bands: Optional[Tuple] = None,
    ):
        # target band to be saved
        self.urls = urls
        self.bands = ("mask", "prob", "filtered")

    @property
    def measurements(self) -> Tuple[str, ...]:
        return self.bands

    def input_data(self, datasets: Sequence[Dataset], geobox: GeoBox) -> xr.Dataset:
        """
        Assemble the input data and do prediction here.

        """
        # create the features
        measurements = [
            "blue",
            "green",
            "red",
            "nir",
            "swir_1",
            "swir_2",
            "red_edge_1",
            "red_edge_2",
            "red_edge_3",
            "bcdev",
            "edev",
            "sdev",
        ]

        input_data = gm_mads_two_seasons_prediction(
            datasets, geobox, measurements, self.urls
        )

        if not input_data:
            return None
        # read in model
        model = joblib.load(self.urls["model"]).set_params(n_jobs=1)

        # ------Run predictions--------
        # step 1: select features
        # load the column names from the training data file to ensure
        # the bands are in the right order
        with fsspec.open(self.urls["td"], "r") as file:
            header = file.readline()
        column_names = header.split()[1:][1:]
        
        # reorder input data according to column names
        input_data = input_data[column_names]
        
        # step 2: prediction
        predicted = predict_xr(
            model=model,
            input_xr=input_data,
            clean=True,
            proba=True,
            return_input=True,
        )

        predicted["Predictions"] = predicted["Predictions"].astype("uint8")
        predicted["Probabilities"] = predicted["Probabilities"].astype("uint8")

        # rechunk on the way out
        return predicted.chunk({"x": -1, "y": -1})

    def reduce(self, xx: xr.Dataset) -> xr.Dataset:
        return post_processing(xx, self.urls)


register("pred-gm-s2", PredGMS2)
