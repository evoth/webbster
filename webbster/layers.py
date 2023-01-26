from os.path import basename
from typing import Any, List, Tuple

import numpy as np
from PIL import Image
from skimage import color
from skimage.io import imread

from .fits import WebbsterFITS
from .jwst_metadata import WebbFilters, WebbFilter

# To prevent messages like "PIL.Image.DecompressionBombError:
# Image size (182222791 pixels) exceeds limit of 178956970 pixels,
# could be decompression bomb DOS attack."
Image.MAX_IMAGE_PIXELS = None


class WebbsterLayer:
    """Helps colorize a grayscale layer and get the required information such as
    hue and saturation from different formats."""

    def fromImageFile(
        image_file: str,
        hue: float = None,
        saturation: float = None,
        value: float = None,
        filter: WebbFilter = None,
    ) -> "WebbsterLayer":
        """Creates WebbsterLayer from an image file.

        If `filter` is provided, gets the colors for that filter. Otherwise,
        attempts to extract the filter name from the filename. Then, if `hue`
        and/or `saturation` are provided, uses those values instead. The `value`
        defaults to 1 unless otherwise specified."""

        # If no filter is provided, looks for the filter name in the filename in
        # the format "*_INSTRUMENT-FILTER.ext". If the name was auto generated
        # using the WebbsterFITS save_image() function, it should be in this
        # format.
        if not filter:
            try:
                instrument, filter_name = (
                    basename(image_file).upper().split(".")[0].split("_")[1].split("-")
                )
            except:
                instrument = None
                filter_name = None

            if (
                instrument
                and filter_name
                and instrument in WebbFilters.FILTERS
                and filter_name in WebbFilters.FILTERS[instrument].dict
            ):
                filter = WebbFilters.FILTERS[instrument].dict[filter_name]

        hue, saturation, value = WebbsterLayer.get_hsv(
            hue, saturation, value, filter, strict=True
        )
        return WebbsterLayer(
            imread(image_file), basename(image_file), hue, saturation, value, image_file
        )

    def fromFITS(
        fits: WebbsterFITS,
        hue: float = None,
        saturation: float = None,
        value: float = None,
        filter: WebbFilter = None,
    ) -> "WebbsterLayer":
        """Creates WebbsterLayer from a WebbsterFITS.

        First, defaults to hue and saturation from the filter of the
        WebbsterFITS. Then, if `filter` is provided, uses the colors for that
        filter. Last, if `hue` and/or `saturation` are provided, uses those
        values instead. The `value` defaults to 1 unless otherwise specified."""

        hue, saturation, value = WebbsterLayer.get_hsv(
            hue,
            saturation,
            value,
            filter or fits.filter,
        )
        return WebbsterLayer(fits.png_data, fits.name, hue, saturation, value)

    def __init__(
        self,
        image: Any,
        name: str,
        hue: float,
        saturation: float,
        value: float,
        filepath: str = None,
    ):
        """Creates WebbsterLayer from the given image data, name, and HSV."""

        self.gray_image = image
        self.name = name
        self.hue = hue
        self.saturation = saturation
        self.value = value
        if filepath:
            self.filepath = filepath

    def colorize(self):
        """
        Colorize the grayscale image and set color_image to new RGB image.
        """

        rgb = color.gray2rgb(self.gray_image)
        multiplier = np.array(
            [self.hue, self.saturation, self.value],
            dtype=np.float64,
        )
        multiplier = color.hsv2rgb(multiplier)
        self.color_image = (rgb * multiplier).astype(np.uint8)

    def get_hsv(
        hue: float = None,
        saturation: float = None,
        value: float = None,
        filter: WebbFilter = None,
        strict: bool = False,
    ) -> Tuple[float, float, float]:
        """Returns a tuple of (hue, saturation, value) based on the input.

        If `filter` is provided, gets the colors for the filter. Then, if `hue`
        and/or `saturation` are provided, uses those values instead. The `value`
        defaults to 1 unless otherwise specified. If `strict` is `True`, then it
        will raise an error if insufficient information is given to get both a
        hue and saturation."""

        new_hue = new_saturation = None

        if filter:
            new_hue, new_saturation = WebbsterLayer.get_filter_hue_saturation(filter)
        if hue is None:
            hue = new_hue
        if saturation is None:
            saturation = new_saturation

        if (hue is None or saturation is None) and strict:
            raise ValueError(
                "Must at least provide either filter or hue and saturation."
            )

        return (hue, saturation, 1 if value is None else value)

    def get_filter_hue_saturation(filter: WebbFilter) -> Tuple[float, float]:
        """
        Gets representative hue and saturation for a filter based on the
        filter's pivot wavelength and bandwidth. Returns a tuple of
        (hue, saturation).
        """

        # If there if no filter, this layer will be grayscale
        if not filter:
            return (0, 0)

        # Each filter is given a hue based on where its wavelength falls in
        # relation to the entire range of the filter's instrument, and a
        # saturation based on its bandwidth.
        instrument_filters = WebbFilters.FILTERS[filter.instrument].list
        all_bandwidths = [filter.bandwidth for filter in instrument_filters]
        bw_range = (min(all_bandwidths), max(all_bandwidths))
        all_wavelengths = [filter.wavelength for filter in instrument_filters]
        wl_range = (min(all_wavelengths), max(all_wavelengths))

        hue_range = (0, 240 / 360)
        saturation_range = (0, 1)

        # Get the proportion of the wavelength on the wavelength range
        wl_prop = (filter.wavelength - wl_range[0]) / (wl_range[1] - wl_range[0])
        # Adjust the proportion according to an S-curve to avoid too much green
        # (Curve doesn't behave very well at endpoints so we assume it's an
        # endpoint if we get an error)
        wl_prop_adj = wl_prop
        try:
            wl_prop_adj = 1 / (1 + (wl_prop / (1 - wl_prop)) ** -2)
        except:
            wl_prop_adj = round(wl_prop)
        # Convert adjusted proportion to hue based on desired range of hues
        # (Also, we invert it because wavelength is inversely proportional to
        #  hue)
        hue = hue_range[1] - wl_prop_adj * (hue_range[1] - hue_range[0])

        # Get the proportion of the bandwidth on the bandwidth range
        # (We map bandwidth to saturation because the wider the bandwidth, the
        # less "focused" the color will be)
        bw_prop = (filter.bandwidth - bw_range[0]) / (bw_range[1] - bw_range[0])
        saturation = saturation_range[1] - bw_prop * (
            saturation_range[1] - saturation_range[0]
        )

        return (hue, saturation)


def screen_blend(image1: Any, image2: Any):
    """
    Screen blend two RGB uint8 images.
    """

    return 255 - np.floor_divide(
        (255 - image1).astype(np.uint) * (255 - image2).astype(np.uint), 255
    ).astype(np.uint8)


def screen_blend_multiple(images: List, brightness: float = None):
    """
    Blends multiple images by iteratively blending each new image with the first
    image. Decreases the brightness of each image to compensate for the amount
    of layers, or multiplies them by `brightness` if provided.
    """

    # A bit arbitrary, but the point is that each layer should be darker when
    # there are more layers
    brightness = 1 - 0.05 * len(images) if brightness is None else brightness

    # TODO: fix how I'm adjusting the "brightness". This is just a quick fix.
    blended = images[0]
    for i in range(1, len(images)):
        multiplier = np.array([brightness, brightness, brightness], dtype=np.float64)
        new_image = (images[i] * multiplier).astype(np.uint8)
        blended = screen_blend(blended, new_image)
    return blended
