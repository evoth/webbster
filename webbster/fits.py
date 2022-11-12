from os.path import join

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from reproject import reproject_interp
from skimage import exposure
from skimage.io import imsave
from skimage.util import img_as_ubyte

from .jwst_metadata import WebbFilters


class WebbsterFITS:
    """Represents data from FITS file and helps perform image operations."""

    def __init__(self, filepath: str):
        """
        Opens the file at `filepath`, gets data from FITS HDUList object, and
        uses it to populate fields.
        """

        self.filepath = filepath
        self.hdul = fits.open(self.filepath)
        self.fits_filename = self.hdul[0].header["FILENAME"].upper()
        self.hdu = self.hdul[1]
        self.naxis1 = self.hdu.header["NAXIS1"]
        self.naxis2 = self.hdu.header["NAXIS2"]
        self.res = self.naxis1 * self.naxis2
        self.data = self.hdu.data
        self.filter_name = self.get_filter_name()
        self.name = self.filter_name or "NONE"

    def get_filter_name(self) -> str:
        """
        Gets filter name by searching for an instance of a filter name in fits
        filename. If there are multiple instances, prefers the one that is on
        the pupil wheel, or appears last.

        If no instance of a filter name is found, returns `None`.
        """

        # Chooses whichever filter appears last or is on the pupil ring, if
        # multiple appear.
        filter_index = -1
        filter_name = None

        for filter in WebbFilters.NIRCAM_FILTERS.list:
            index = self.fits_filename.find(filter.name)
            if index != -1 and (index > filter_index or filter.is_pupil):
                filter_index = index
                filter_name = filter.name

        return filter_name

    def adjust_contrast(self):
        """
        Stretches out the darker portions of the image so that we can see it.
        """

        # Rescale intensity (clip darkest and brightest areas)
        # TODO: more reliable way of stretching contrast
        lo, hi = np.percentile(self.data, (15, 99.85))
        self.data = exposure.rescale_intensity(self.data, in_range=(lo, hi))
        self.data = np.clip(self.data, 0.0, 1.0)
        # Adaptive histogram equalization
        self.data = exposure.equalize_adapthist(self.data, clip_limit=0.02)

    def reproject(self, ref_fits: "WebbsterFITS", max_pixels: int = 50_000_000):
        """
        Reprojects image to be aligned with `ref_fits` using WCS data.

        To save on memory usage, the image is reprojected in slices, which are
        each compressed to uint8 then joined back together. `max_pixels` is the
        maximum number of pixels allowed in a slice (1 pixel is about 8 bytes)
        """

        start_row = 0
        max_rows = max_pixels // ref_fits.naxis1
        # Empty array with the same width as output, to which slices will be
        # concatenated
        proj_data = np.empty((0, ref_fits.naxis1), dtype=np.uint8)
        # Repeat until we reach the bottom of image (the last slice will be the
        # shortest)
        while start_row < ref_fits.naxis2:
            if ref_fits.naxis2 - start_row > max_rows:
                end_row = start_row + max_rows
            else:
                end_row = ref_fits.naxis2
            # Slice the WCS of the reference image so that it will only project
            # to the slice
            ref_wcs = WCS(ref_fits.hdu.header)
            ref_wcs = ref_wcs[start_row:end_row, 0 : ref_fits.naxis1]
            slice_shape = (end_row - start_row, ref_fits.naxis1)
            # Reproject, and convert to uint8 to save memory
            proj_slice = img_as_ubyte(
                reproject_interp(
                    (self.data, self.hdu.header), ref_wcs, shape_out=slice_shape
                )[0]
            )
            # Concatenate new slice onto the end of our image
            proj_data = np.concatenate((proj_data, proj_slice))
            start_row = end_row
        # Full data
        self.data = proj_data

    def save_image(
        self, folder: str = None, filename: str = None, extension: str = "png"
    ) -> str:
        """
        Converts data to uint8 and optionally saves as image.

        If `folder` is specified, saves an image to that location, with either a
        generated name based on the filter name or `filename` if provided. If
        using a generated name, `extension` (default is `"png"`) will be used as
        the file extension. Returns the filepath of the resulting image if
        saved.
        """

        self.png_data = img_as_ubyte(self.data)
        self.png_data = np.flipud(self.png_data)
        if folder:
            filepath = join(
                folder,
                filename
                or f"{self.fits_filename.split('-')[0]}-{self.name}.{extension}",
            )
            imsave(filepath, self.png_data)
            return filepath
