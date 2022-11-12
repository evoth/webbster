from dataclasses import dataclass, fields


class MetadataContainer:
    """Simple way to get either a list or dictionary of dataclass objects."""

    def __init__(self, dataclass_list: list):
        """Populate both the `list` and `dict` fields using a list of dataclass
        objects.

        The `list` field will by identical to the input, and the `dict` field
        will be a dict where the key is the first field of the dataclass object,
        and the value is the actual object."""
        self.list = dataclass_list
        self.dict = {getattr(obj, fields(obj)[0].name): obj for obj in dataclass_list}


@dataclass()
class WebbFilter:
    """Stores information about a filter on JWST."""

    name: str
    wavelength: float
    bandwidth: float
    is_pupil: bool


class WebbFilters:
    """Stores information about the filters on the filter wheel of NIRCAM.

    Source: https://jwst-docs.stsci.edu/jwst-near-infrared-camera/nircam-instrumentation/nircam-filters#NIRCamFilters-Filterlists"""

    NIRCAM_FILTERS = MetadataContainer(
        [
            WebbFilter("F070W", 0.704, 0.132, False),
            WebbFilter("F090W", 0.902, 0.194, False),
            WebbFilter("F115W", 1.154, 0.225, False),
            WebbFilter("F140M", 1.405, 0.142, False),
            WebbFilter("F150W", 1.501, 0.318, False),
            WebbFilter("F162M", 1.627, 0.168, True),
            WebbFilter("F164N", 1.645, 0.02, True),
            WebbFilter("F150W2", 1.659, 1.175, False),
            WebbFilter("F182M", 1.845, 0.237, False),
            WebbFilter("F187N", 1.874, 0.024, False),
            WebbFilter("F200W", 1.989, 0.457, False),
            WebbFilter("F210M", 2.095, 0.206, False),
            WebbFilter("F212N", 2.121, 0.027, False),
            WebbFilter("F250M", 2.503, 0.18, False),
            WebbFilter("F277W", 2.762, 0.683, False),
            WebbFilter("F300M", 2.989, 0.315, False),
            WebbFilter("F322W2", 3.232, 1.356, False),
            WebbFilter("F323N", 3.237, 0.038, True),
            WebbFilter("F335M", 3.362, 0.352, False),
            WebbFilter("F360M", 3.624, 0.37, False),
            WebbFilter("F356W", 3.568, 0.781, False),
            WebbFilter("F405N", 4.052, 0.045, True),
            WebbFilter("F410M", 4.082, 0.438, False),
            WebbFilter("F430M", 4.281, 0.228, False),
            WebbFilter("F444W", 4.408, 1.029, False),
            WebbFilter("F460M", 4.63, 0.229, False),
            WebbFilter("F466N", 4.654, 0.054, True),
            WebbFilter("F470N", 4.708, 0.051, True),
            WebbFilter("F480M", 4.874, 0.3, False),
        ]
    )
