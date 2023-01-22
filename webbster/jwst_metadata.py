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
    """Stores information about a filter on JWST and its transmission
    characteristics (used when automatically choosing colors)."""

    name: str
    instrument: str
    wavelength: float
    bandwidth: float
    is_pupil: bool = False

    def get_filter_name(self):
        """Returns a filter name in the format `INSTRUMENT-FILTER` where
        `INSTRUMENT` is the name of the instrument and `FILTER` is the actual
        name of the filter (e.g. `NIRCAM-F090W`)."""
        return self.instrument + "-" + self.name


class WebbFilters:
    """Stores information about the filters on the filter wheels of NIRCAM and
    MIRI."""

    FILTERS = {
        # Source: https://jwst-docs.stsci.edu/jwst-near-infrared-camera/nircam-instrumentation/nircam-filters#NIRCamFilters-Filterlists
        "NIRCAM": MetadataContainer(
            [
                WebbFilter("F070W", "NIRCAM", 0.704, 0.128, False),
                WebbFilter("F090W", "NIRCAM", 0.901, 0.194, False),
                WebbFilter("F115W", "NIRCAM", 1.154, 0.225, False),
                WebbFilter("F140M", "NIRCAM", 1.404, 0.142, False),
                WebbFilter("F150W", "NIRCAM", 1.501, 0.318, False),
                WebbFilter("F162M", "NIRCAM", 1.626, 0.168, True),
                WebbFilter("F164N", "NIRCAM", 1.644, 0.020, True),
                WebbFilter("F150W2", "NIRCAM", 1.671, 1.227, False),
                WebbFilter("F182M", "NIRCAM", 1.845, 0.238, False),
                WebbFilter("F187N", "NIRCAM", 1.874, 0.024, False),
                WebbFilter("F200W", "NIRCAM", 1.990, 0.461, False),
                WebbFilter("F210M", "NIRCAM", 2.093, 0.205, False),
                WebbFilter("F212N", "NIRCAM", 2.120, 0.027, False),
                WebbFilter("F250M", "NIRCAM", 2.503, 0.181, False),
                WebbFilter("F277W", "NIRCAM", 2.786, 0.672, False),
                WebbFilter("F300M", "NIRCAM", 2.996, 0.318, False),
                WebbFilter("F322W2", "NIRCAM", 3.247, 1.339, False),
                WebbFilter("F323N", "NIRCAM", 3.237, 0.038, True),
                WebbFilter("F335M", "NIRCAM", 3.365, 0.347, False),
                WebbFilter("F356W", "NIRCAM", 3.563, 0.787, False),
                WebbFilter("F360M", "NIRCAM", 3.621, 0.372, False),
                WebbFilter("F405N", "NIRCAM", 4.055, 0.046, True),
                WebbFilter("F410M", "NIRCAM", 4.092, 0.436, False),
                WebbFilter("F430M", "NIRCAM", 4.280, 0.228, False),
                WebbFilter("F444W", "NIRCAM", 4.421, 1.024, False),
                WebbFilter("F460M", "NIRCAM", 4.624, 0.228, False),
                WebbFilter("F466N", "NIRCAM", 4.654, 0.054, True),
                WebbFilter("F470N", "NIRCAM", 4.707, 0.051, True),
                WebbFilter("F480M", "NIRCAM", 4.834, 0.303, False),
            ]
        ),
        # Source: https://jwst-docs.stsci.edu/jwst-mid-infrared-instrument/miri-instrumentation/miri-filters-and-dispersers#MIRIFiltersandDispersers-Imagingfilters
        "MIRI": MetadataContainer(
            [
                WebbFilter("F560W", "MIRI", 5.6, 1.2),
                WebbFilter("F770W", "MIRI", 7.7, 2.2),
                WebbFilter("F1000W", "MIRI", 10.0, 2.0),
                WebbFilter("F1130W", "MIRI", 11.3, 0.7),
                WebbFilter("F1280W", "MIRI", 12.8, 2.4),
                WebbFilter("F1500W", "MIRI", 15.0, 3.0),
                WebbFilter("F1800W", "MIRI", 18.0, 3.0),
                WebbFilter("F2100W", "MIRI", 21.0, 5.0),
                WebbFilter("F2550W", "MIRI", 25.5, 4.0),
                WebbFilter("F2550WR", "MIRI", 25.5, 4.0),
                WebbFilter("FND", "MIRI", 13, 10),
            ]
        ),
    }
