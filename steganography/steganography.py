# Copyright 2021 Gael Abadin
# Forked from https://github.com/subc/steganography
# ( MIT LICENSED on https://github.com/subc/steganography/blob/8ce5ed30ed087c85cdd1a378f8e5cc81154ebcc7/setup.py#L26 )

import sys
from PIL import Image
import random

DIST = 8


def normalize_pixel(rgb):
    """
    pixel color normalize
    :param rgb: list
    :return: (int, int, int)
    """
    if is_modify_pixel(rgb):
        seed = random.randint(0, 2)
        rgb[seed] = _normalize(rgb[seed])
    return tuple(rgb)


def modify_pixel(r, g, b):
    """
    pixel color modify
    :param r: int
    :param g: int
    :param b: int
    :return: (int, int, int)
    """
    return map(_modify, [r, g, b])


def is_modify_pixel(rgb):
    """
    :param rgb: list
    :return: bool
    """
    return rgb[0] % DIST == rgb[1] % DIST == rgb[2] % DIST == 1


def _modify(i):
    if i >= 128:
        for x in range(DIST + 1):
            if i % DIST == 1:
                return i
            i -= 1
    else:
        for x in range(DIST + 1):
            if i % DIST == 1:
                return i
            i += 1
    raise ValueError


def _normalize(i):
    if i >= 128:
        i -= 1
    else:
        i += 1
    return i


def hide_text(img, path, text, full_normalize=True):
    """
    hide text to image
    :param img: Image
    :param path: str
    :param text: str
    :param full_normalize: bool
    """
    text = str(text)
    if not full_normalize:
        text += '\0\0\0\0\0\1'

    # convert text to hex for write
    write_param = []
    _base = 0
    for _ in to_hex(text):
        write_param.append(int(_, 16) + _base)
        _base += 16

    # hide hex-text to image
    counter = 0
    writes_to_go = len(write_param)
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            if counter in write_param:
                r, g, b, a = img.getpixel((x, y))
                _r, _g, _b = normalize_pixel([r, g, b])
                _r, _g, _b = modify_pixel(_r, _g, _b)
                img.putpixel((x, y), (_r, _g, _b, a))
                if not full_normalize:
                    writes_to_go -= 1
                    if writes_to_go == 0:
                        break
            elif full_normalize:
                r, g, b, a = img.getpixel((x, y))
                _r, _g, _b = normalize_pixel([r, g, b])
                if (_r, _g, _b) != (r, g, b):
                    img.putpixel((x, y), (_r, _g, _b, a))
            counter += 1
        if writes_to_go == 0:
            break
    # save
    img.save(path, "PNG")


def to_hex(s):
    return s.encode().hex()


def to_str(s):
    return bytes.fromhex(s).decode('utf-8')


def read_text(path, full_normalize=True):
    """
    read secret text from image
    :param path: str
    :param full_normalize: bool
    :return: str
    """
    img = Image.open(path)
    counter = 0
    terminator_count = 0
    result = []
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = img.getpixel((x, y))
            if is_modify_pixel([r, g, b]):
                result.append(counter)
                if not full_normalize:
                    if counter == 0:
                        terminator_count += 1
                    elif counter == 1 and terminator_count >= 11:
                        break
                    else:
                        terminator_count = 0
            counter = (counter + 1) % 16
        if not full_normalize and counter == 1 and terminator_count >= 11:
            break
    if not full_normalize:
        result = result[:-12]
    return to_str(''.join([hex(_)[-1:] for _ in result]))


class Steganography(object):
    @classmethod
    def encode(cls, input_image_path, output_image_path, encode_text, full_normalize=True):
        """
        hide text to image
        :param input_image_path: str
        :param output_image_path: str
        :param encode_text: str
        :param full_normalize: bool
        """
        img = Image.open(input_image_path)
        if img.mode != "RGBA":
            img = img.convert('RGBA')
        hide_text(img, output_image_path, encode_text, full_normalize)

    @classmethod
    def decode(cls, image_path, full_normalize=True):
        """
        read secret text from image
        :param image_path: str
        :param full_normalize: bool
        :return: str
        """
        return read_text(image_path, full_normalize)


# Main program
def main():
    if len(sys.argv) == 5 and (sys.argv[1] == '-e' or sys.argv[1] == '-se'):
        # encode
        print("Start Encode")
        input_image_path = sys.argv[2]
        output_image_path = sys.argv[3]
        text = sys.argv[4]
        full_normalize = sys.argv[1] == '-e'
        Steganography.encode(input_image_path, output_image_path, text, full_normalize)
        print("Finish:{}".format(output_image_path))
        return
    if len(sys.argv) == 3 and (sys.argv[1] == '-d' or sys.argv[1] == '-sd'):
        # decode
        input_image_path = sys.argv[2]
        full_normalize = sys.argv[1] == '-d'
        print(Steganography.decode(input_image_path, full_normalize))
        return
    print_help_text()


def print_help_text():
    print("ERROR: not steganography command")
    print("--------------------------------")
    print("# encode example: hide text to image")
    print("steganography -e /tmp/image/input.jpg /tmp/image/output.jpg 'The quick brown fox jumps over the lazy dog.'")
    print("")
    print("# decode example: read secret text from image")
    print("steganography -d /tmp/image/output.jpg")
    print("")
    print("(For quick encode/decode using partial normalization, use -se/-sd instead)")
    print("")


if __name__ == "__main__":
    main()
