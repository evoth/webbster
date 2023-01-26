import argparse
import random
import time
from os import listdir
from os.path import abspath, join
from typing import Dict, Tuple

from skimage.io import imsave

from webbster.layers import WebbsterLayer, screen_blend_multiple


def parse_colors_file(colors_filepath: str) -> Dict[str, Tuple[float, float, float]]:
    """
    Parses a colors file (format as described below) and returns a dictionary
    with filepaths as keys and HSV tuples as values.

    The following is the format for each line of a colors file:

       "`FILEPATH`" (`HUE`, `SATURATION`, `VALUE`)

    where `FILEPATH` is the path to an image in the specified folder, and `HUE`,
    `SATURATION`, and `VALUE` are either a single number (e.g. `75`), or a range
    (e.g. `75-100`), where the latter will generate a random value on that range
    (inclusive). The ranges for `HUE`, `SATURATION`, and `VALUE` are [0-360],
    [0-100], and [0-100], respectively.

    The following is an example colors file::

       "layers/JW02731-F090W.png" (200-240, 87, 100)
       "layers/JW02731-F187N.png" (208, 50-100, 100)
       "layers/JW02731-F200W.png" (200, 67, 100)
       "layers/JW02731-F335M.png" (0-359, 0-100, 0-100)
       "layers/JW02731-F444W.png" (4, 24, 100)
       "layers/JW02731-F470N.png" (0, 98, 100)

    Any image present in the folder that is not referenced in the colors file
    will be colored as default from the filter name in the filename.
    """
    with open(colors_filepath, "r") as f:
        lines = f.readlines()

    image_colors = {}
    for line in lines:
        # Filename is after the first quote, before the second
        parts = line.strip().split('"')
        filename = parts[1]
        # To get hsv strings, we take away the parentheses, then split by commas
        # (removing whitespace at each step.)
        hsv_strings = [c.strip() for c in parts[2].strip()[1:-1].split(",")]
        hsv = []
        # If a component is in the format NUMBER_1-NUMBER_2, generate a random
        # int on that range. Otherwise, just convert it to an int.
        for component in hsv_strings:
            if "-" in component:
                lo, hi = (int(x.strip()) for x in component.split("-"))
                hsv.append(random.randint(lo, hi))
            else:
                hsv.append(int(component))
        image_colors[abspath(filename).upper()] = (
            hsv[0] / 360,
            hsv[1] / 100,
            hsv[2] / 100,
        )

    return image_colors


if __name__ == "__main__":
    # Set up command line arguments with argparse
    parser = argparse.ArgumentParser(
        description="""Converts a folder of grayscale layer images to a single 
        image, with the option to customize the color of each layer."""
    )
    parser.add_argument(
        "INPUT_FOLDER",
        help="a folder containing the grayscale layer images to compile",
    )
    parser.add_argument(
        "OUTPUT_IMAGE",
        help="the filepath of the output image (e.g. cosmic_cliffs.jpg)",
    )
    parser.add_argument(
        "COLORS_FILE",
        nargs="?",
        help=(
            "path to file with custom colors for each layer (see lines 15-38 "
            "of this file or https://github.com/evoth/webbster#colors-file-formatting "
            "for more info)"
        ),
    )
    parser.add_argument(
        "--export_colors_file",
        help=(
            "path to export the colors used for each layer (in the same format "
            "as COLORS_FILE)"
        ),
    )

    # Get values of arguments
    args = parser.parse_args()
    layers_folder = args.INPUT_FOLDER
    output_filepath = args.OUTPUT_IMAGE
    colors_filepath = args.COLORS_FILE
    export_colors_filepath = args.export_colors_file

    start_time = time.time()

    print(f"Loading image files.")

    # Gets image files in folder
    image_filepaths = [
        join(layers_folder, filename)
        for filename in listdir(layers_folder)
        if filename.split(".")[-1].lower() in ["jpg", "jpeg", "png"]
    ]

    # If a colors file is provided, attempt to use those colors for each image
    # in the folder. If the colors file does not contain one of the images, we
    # revert to attempting to extract the filter name from the filename and
    # using the color associated with that filter. The latter applies to every
    # image if no colors file is provided.
    if colors_filepath:
        print(f'Importing colors file at "{colors_filepath}".')
        custom_colors = parse_colors_file(colors_filepath)
    layers = []
    for image_filepath in image_filepaths:
        if colors_filepath and abspath(image_filepath).upper() in custom_colors:
            hsv = custom_colors[abspath(image_filepath).upper()]
            layers.append(WebbsterLayer.fromImageFile(image_filepath, *hsv))
        else:
            layers.append(WebbsterLayer.fromImageFile(image_filepath))

    print(f"Colorizing layers.")
    colors_used = []
    for layer in layers:
        hsv = [
            round(layer.hue * 360),
            round(layer.saturation * 100),
            round(layer.value * 100),
        ]
        colors_used.append(f'"{layer.filepath}" ({hsv[0]}, {hsv[1]}, {hsv[2]})')
        print(
            (f" > Colorizing {layer.name} with HSV ({hsv[0]}, " f"{hsv[1]}, {hsv[2]}).")
        )
        layer.colorize()

    # If export_colors_filepath was provided, export the colors we used
    if export_colors_filepath:
        with open(export_colors_filepath, "w") as f:
            print(f'Exporting colors file to "{export_colors_filepath}".')
            f.write("\n".join(colors_used))

    print(f"Blending layers.")
    blended_image = screen_blend_multiple([layer.color_image for layer in layers])

    print(f'Saving composited image to "{output_filepath}".')
    imsave(
        output_filepath,
        blended_image,
    )

    minutes, seconds = divmod(time.time() - start_time, 60)
    print(f"Done in {int(minutes)} minute(s), {round(seconds, 2)} second(s).")
