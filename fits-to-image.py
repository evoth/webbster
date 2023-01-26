import argparse
import time
import warnings
from os import listdir
from os.path import join

from skimage.io import imsave

from webbster.fits import WebbsterFITS
from webbster.layers import WebbsterLayer, screen_blend_multiple

# Suppresses FITSFixedWarning from Astropy/WCSLIB, since JWST images set it off
# TODO: Only ignore that specific class of warning
warnings.simplefilter("ignore")

if __name__ == "__main__":
    # Set up command line arguments with argparse
    parser = argparse.ArgumentParser(
        description="""Converts a folder of FITS images to a single image. 
        Optionally exports a grayscale image for each layer."""
    )
    parser.add_argument(
        "INPUT_FOLDER",
        help="a folder containing the JWST .fits files to compile",
    )
    parser.add_argument(
        "OUTPUT_IMAGE",
        help="the filepath of the output image (e.g. cosmic_cliffs.jpg)",
    )
    parser.add_argument(
        "LAYERS_FOLDER",
        nargs="?",
        help="folder into which to export a grayscale image for each layer",
    )
    parser.add_argument(
        "-j",
        "--jpg_layers",
        action="store_const",
        const="jpg",
        default="png",
        help="when exporting layers, use .jpg extension instead of .png (may be faster and/or save storage)",
    )

    # Get values of arguments
    args = parser.parse_args()
    fits_folder = args.INPUT_FOLDER
    output_filepath = args.OUTPUT_IMAGE
    layers_folder = args.LAYERS_FOLDER
    layers_extension = args.jpg_layers

    start_time = time.time()

    # Gets fits files from directory and initialize fitsFilter objects for each
    print(f"Loading images from fits.")
    filters = [
        WebbsterFITS(join(fits_folder, filename))
        for filename in listdir(fits_folder)
        if filename[-5:].lower() == ".fits"
    ]

    # Find image with greatest resolution to use as reference for aligning other
    # images. Also, rename filters if there are duplicate filter names.
    max_res = 0
    ref_filter = filters[0]
    names = {}
    for filter in filters:
        print(f" > Checking resolution of {filter.name}.")
        if filter.res > max_res:
            max_res = filter.res
            ref_filter = filter

        if filter.name in names:
            names[filter.name] += 1
            filter.name = filter.name + "-" + str(names[filter.name])
        else:
            names[filter.name] = 1

    print(f" > Reference filter is {ref_filter.name}.")

    # Process and export each layer
    for filter in filters:
        print(f"Processing {filter.name}.")
        print(f" > Adjusting contrast of {filter.name}.")
        filter.adjust_contrast()
        if filter != ref_filter:
            print(f" > Reprojecting {filter.name}.")
            filter.reproject(ref_filter)
        if layers_folder:
            print(f" > Saving layer image for {filter.name}.")
            filter.save_image(layers_folder, extension=layers_extension)

    # Convert WebbsterFITS to WebbsterLayer
    layers = [WebbsterLayer.fromFITS(filter) for filter in filters]

    print(f"Colorizing layers.")
    for layer in layers:
        print(
            (
                f" > Colorizing {layer.name} with HSV ({round(layer.hue * 360)}, "
                f"{round(layer.saturation * 100)}, {round(layer.value * 100)})."
            )
        )
        layer.colorize()

    print(f"Blending layers.")
    blended_image = screen_blend_multiple([layer.color_image for layer in layers])

    print(f'Saving composited image to "{output_filepath}".')
    imsave(
        output_filepath,
        blended_image,
    )

    minutes, seconds = divmod(time.time() - start_time, 60)
    print(f"Done in {int(minutes)} minute(s), {round(seconds, 2)} second(s).")
