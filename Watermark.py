# Watermark.py
#
# Convert image(s) to a specified output along with a randomly placed
# watermark image.
#
# With 3 samples images (sample1.jpg, sample2.jpg, sample3.jpg), will
# create a directory structure at destination:
#
# Images/
#   sample1.jpg
#   sample2.jpg
#   sample3.jpg
#   Thumbs/
#     sample1.jpg
#     sample2.jpg
#     sample3.jpg
#   Resizes/
#     sample1.jpg
#     sample2.jpg
#     sample3.jpg
#
# Derek Wong (http://www.goingthewongway.com)

import sys
import argparse
import os
import glob
import re
import string
import random
import ConfigParser

config = ConfigParser.ConfigParser()
config.readfp(open('env.cfg'))
source_default = config.get('locations', 'source')
destination_default = config.get('locations', 'target')
watermark_default = config.get('locations', 'watermark_file')
size_default = config.get('output_info', 'output_default_size')
resize_default = config.get('output_info', 'resize_default_size')
thumb_default = config.get('output_info', 'thumb_default_size')
append_default = config.get('output_info', 'append_default')
filetypes_config = config.get('locations', 'filetypes')
filetypes_default = []
for filetype in re.split(',', filetypes_config):
    filetypes_default.append(filetype.strip())
output_filename_default = config.get('output_info', 'default_name')
thumbnail_directory = config.get('locations', 'target_thumbnail')
resize_directory = config.get('locations', 'target_resizes')

def split_filename(filename):
    basename = os.path.basename(filename).split('.')[0]
    try:
        extension = '.%s' % os.path.basename(filename).split('.')[1]
    except IndexError:
        extension = '.JPG'
    return basename, extension

def watermark_image(source_path, destination_path, watermark_path,
                    output_size, debug, append, filename, create_thumb,
                    thumb_size, create_resize, resize_size):
    # Pseudo:
    #   Convert to output size
    #   If creating thumbs, create thumb
    #   Composite overlay with original to a new image
    #     using a random location for the watermark

    if os.path.isdir(source_path):
        return
    
    if debug:
        print("source: %s\ndest: %s\nwm: %s\noutput: %s" %
              (source_path, destination_path, watermark_path, output_size))

    delimiter_position = string.find(output_size, 'x')
    horizontal = int(output_size[0:delimiter_position])
    vertical = int(output_size[delimiter_position+1:len(output_size)])
    gravity = ['NorthWest', 'North', 'NorthEast', 'West', 'East', 'SouthWest',
               'South', 'SouthEast']
    geometry = ['+%s+%s' % (horizontal/7, vertical/8),
                '+%s+%s' % (horizontal/7.5, vertical/11),
                '+%s+%s' % (horizontal/20, vertical/10),
                '+%s+%s' % (horizontal/14, vertical/13),
                '+%s+%s' % (horizontal/8, vertical/6),
                '+%s+%s' % (horizontal/16, vertical/10)]

    # Directory provided does not exist
    try:
        os.mkdir(os.path.dirname(destination_path))
        if debug: print('mkdir')
    except OSError:
        pass
        
    # Create thumbnail directory
    if create_thumb:
        thumb_destination_path = ('%s/%s/' % (os.path.dirname(destination_path),
                                              thumbnail_directory))
        try:
            os.mkdir(thumb_destination_path)
            if debug: print('mkdir %s' % thumb_destination_path)
        except OSError:
            pass

    # Create resize directory
    if create_resize:
        resize_destination_path = ('%s/%s/' % (os.path.dirname(destination_path),
                                               resize_directory))
        try:
            os.mkdir(resize_destination_path)
            if debug: print('mkdir %s' % resize_destination_path)
        except OSError:
            pass
    
    # Retrieve filename since none is provided
    basename, extension = split_filename(filename if filename is not None
                                         else source_path)
    if os.path.isdir(destination_path):
        if debug: print('No filename given')
        out_file = '%s%s%s' % (basename, append, extension)
        if create_thumb:
            thumb_destination_path += '%s' % out_file
            if debug: print('Thumb: %s' % thumb_destination_path)
        if create_resize:
            resize_destination_path += '%s' % out_file
            if debug: print('Resize: %s' % resize_destination_path)
        destination_path += '%s' % out_file
        if debug: print('New destination: %s' % destination_path)
    # Use a unique filename rather than overwriting an existing file
    elif os.path.isfile(destination_path):
        if debug: print('Already exists, resolve new filename')
        basename, extension = split_filename(destination_path)
        directory = os.path.dirname(destination_path)
        dest = destination_path
        counter = 1
        while os.path.exists(dest):
            unique_name = '%s%s%s' % (basename, counter, extension)
            dest = "%s/%s" % (directory, unique_name)
            counter += 1
        destination_path = dest
        if debug: print('Unique filename: %s' % destination_path)
        if create_thumb:
            thumb_destination_path = ('%s/%s' %
                                      (thumb_destination_path, unique_name))
            if debug: print('thumb dest: %s' % thumb_destination_path)
        if create_resize:
            resize_destination_path = ('%s/%s' %
                                      (resize_destination_path, unique_name))
            if debug: print('resize dest: %s' % resize_destination_path)
        
    cmd = ("convert -quality 70%% -auto-orient \"%s\" -resize %s \"%s\"" %
           (source_path, output_size, destination_path))
    if debug:
        print(cmd)
    else:
        os.system(cmd)

    # Create thumbnail without watermark
    if create_thumb:
        cmd = ("convert -quality 80%% \"%s\" -resize %s \"%s\"" %
               (destination_path, thumb_size, thumb_destination_path))
        if debug:
            print(cmd)
        else:
            os.system(cmd)

    # Create resize without watermark
    if create_resize:
        cmd = ("convert -quality 80%% \"%s\" -resize %s \"%s\"" %
               (destination_path, resize_size, resize_destination_path))
        if debug:
            print(cmd)
        else:
            os.system(cmd)
        
    # Composite overlay to create watermarked full large size image
    cmd = ("convert \"%s\" -fill grey50 miff:- | "
           "composite -dissolve 20 -geometry %s -gravity %s - \"%s\" \"%s\"" %
           (watermark_path,
            geometry[random.randint(0, len(geometry)-1)],
            gravity[random.randint(0, len(gravity)-1)],
            destination_path,
            destination_path))
    if debug:
        print(cmd)
    else:
        os.system(cmd)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.set_defaults(source=source_default,
                        destination=destination_default,
                        watermark=watermark_default,
                        thumbs=False,
                        size=size_default,
                        thumbs_size=thumb_default,
                        resizes=False,
                        resizes_size=resize_default,
                        debug=False,
                        append=append_default,
                        output_filename=output_filename_default,
                        filetypes=filetypes_default)
    parser.add_argument('-src', '-in',
                        dest='source', help='Source directory or file')
    parser.add_argument('-dst', '-out',
                        dest='destination',
                        help='Destination directory or file')
    parser.add_argument('-size', dest='size',
                        help='Output size (e.g., 640x480)')
    parser.add_argument('-w', '-wm', '--watermark',
                        dest='watermark', help='Watermark image')
    parser.add_argument('-d', '--debug', dest='debug', help='Print commands',
                        action='store_true')
    parser.add_argument('-app', '--append', dest='append',
                        help='Append to the end of the source filename; '
                        'only used if destination is a directory')
    parser.add_argument('-f', '--output-filename', dest='output_filename',
                        help='Output file using this filename as a base name')
    parser.add_argument('--types', dest='filetypes',
                        help='Filetypes to look for in the input filenames')
    parser.add_argument('-t', '--thumbs', dest='thumbs',
                        help='Create thumbnails', action='store_true')
    parser.add_argument('-tsize', dest='thumbs_size',
                        help='Thumbnail size (e.g., 60x40)')
    parser.add_argument('-r', '--resizes', dest='resizes',
                        help='Create resizes', action='store_true')
    parser.add_argument('-rsize', dest='resizes_size',
                        help='Resizes size (e.g., 200x400)')
    args = vars(parser.parse_args())
    source = args['source']
    destination = args['destination']
    size = args['size']
    thumbs_size = args['thumbs_size']
    thumbs = args['thumbs']
    resize_size = args['resizes_size']
    resizes = args['resizes']
    watermark = args['watermark']
    debug = args['debug']
    append = args['append']
    output_filename = args['output_filename']
    filetypes = args['filetypes']

    if os.path.isfile(source):
        if debug: print('FILE')
        watermark_image(source, destination, watermark, size, debug, append,
                        output_filename, thumbs, thumbs_size, resizes,
                        resize_size)
    elif os.path.isdir(source):
        if debug: print('DIRECTORY')
        for t in filetypes:
            if debug: print('processing filetype %s' %t)
            for f in glob.glob(os.path.dirname(source + '/') + '/*.' + t):
                if debug: print('processing %s' % f)
                watermark_image(f, destination + '/',
                                watermark, size, debug, append,
                                output_filename, thumbs, thumbs_size, resizes,
                                resize_size)
