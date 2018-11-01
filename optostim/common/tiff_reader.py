from skimage.external import tifffile as tif

from pyjohnstonlab.thirdparty.scan_image_tiff_reader import ScanImageTiffReader


def read_tif(filename):
    data = tif.imread(filename)
    vol = ScanImageTiffReader(filename.encode())
    metadata = binary_to_dict(vol.metadata())

    descriptions = [binary_to_dict(vol.description(frame_number))
                    for frame_number in range(data.shape[0])]

    return metadata, data, descriptions


def binary_to_dict(binary_data):

    string = binary_data.decode('utf-8')
    info_list = string.split('\n')

    dict = {}

    for info in info_list:
        key_value_list = info.split('=')

        if len(key_value_list) == 2:
            dict[key_value_list[0].strip()] = key_value_list[1].strip()

    return dict



