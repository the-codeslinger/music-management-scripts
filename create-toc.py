# Scan directories for audio files with a given extension and read the
# meta data from the file's name to create a table of contents JSON
# file from that information. This file can later be used by 
# conversion tools/scripts.
# 
# Usage example:
#   python3 create-toc.py \
#       -s Music \
#       -d "#" \
#       -f "artist,album,year,genre,track,title" \
#       -r \
#       -t wav
# 
# See `python3 create-toc.py --help` for details.

import os
import json
import argparse
from pathvalidate import sanitize_filename

ARTIST_TAG_NAME = 'artist'
ALBUM_TAG_NAME = 'album'
GENRE_TAG_NAME = 'genre'
YEAR_TAG_NAME = 'year'
TRACK_TAG_NAME = 'track'
TITLE_TAG_NAME = 'title'
TRACK_LIST_NAME = 'tracks'
FILENAME_TAG_NAME = 'filename'
LONG_FILENAME_TAG_NAME = 'long'
SHORT_FILENAME_TAG_NAME = 'short'

FORWARD_SLASH_STRING = '/'
FORWARD_SLASH_CODE = '&47;'

COLON_STRING = ':'
COLON_CODE = '&58;'

QUESTION_MARK_STRING = '?'
QUESTION_MARK_CODE = '&63;'

BACKSLASH_STRING = '\\'
BACKSLASH_CODE = '&92;'

def is_hidden(name):
    return name[0] == "."

def get_artist(file_tags):
    return file_tags[ARTIST_TAG_NAME] if ARTIST_TAG_NAME in file_tags else ''

def get_album(file_tags):
    return file_tags[ALBUM_TAG_NAME] if ALBUM_TAG_NAME in file_tags else ''

def get_genre(file_tags):
    return file_tags[GENRE_TAG_NAME] if GENRE_TAG_NAME in file_tags else ''

def get_year(file_tags):
    return file_tags[YEAR_TAG_NAME] if YEAR_TAG_NAME in file_tags else ''

def get_track(file_tags):
    return file_tags[TRACK_TAG_NAME].zfill(2) if TRACK_TAG_NAME in file_tags else ''

def get_title(file_tags):
    return file_tags[TITLE_TAG_NAME] if TITLE_TAG_NAME in file_tags else ''

def replace_specials(title):
    return title \
        .replace(FORWARD_SLASH_CODE, FORWARD_SLASH_STRING) \
        .replace(COLON_CODE, COLON_STRING) \
        .replace(QUESTION_MARK_CODE, QUESTION_MARK_STRING) \
        .replace(BACKSLASH_CODE, BACKSLASH_STRING)

def simple_filename(file_tags, type):
    track = get_track(file_tags)
    title = get_title(file_tags)

    filename = ''
    if track and title:
        filename = track + "-" + title + "." + type
    elif track and not title:
        filename = track + "." + type
    elif not track and title:
        filename = title + "." + type
    
    # sanitize_filename removes my coded special characters; I prefer '_' instead
    filename = filename \
        .replace(' ', '_') \
        .replace('\'', '') \
        .replace(FORWARD_SLASH_STRING, '_') \
        .replace(COLON_STRING, '_') \
        .replace(QUESTION_MARK_STRING, '_') \
        .replace(BACKSLASH_STRING, '_')

    return sanitize_filename(filename)

def assert_and_fill_metadata(record_metadata, tag_name, tag_value):
    if not record_metadata[tag_name]:
        record_metadata[tag_name] = tag_value
    else:
        assert record_metadata[tag_name] == tag_value, f"File contains different {tag_name}"

def fill_record_metadata(record_metadata, file_tags):
    assert_and_fill_metadata(record_metadata, ARTIST_TAG_NAME, get_artist(file_tags))
    assert_and_fill_metadata(record_metadata, ALBUM_TAG_NAME, get_album(file_tags))
    assert_and_fill_metadata(record_metadata, GENRE_TAG_NAME, get_genre(file_tags))
    assert_and_fill_metadata(record_metadata, YEAR_TAG_NAME, get_year(file_tags))

def remove_redundant_tags(file_tags):
    file_tags.pop(ARTIST_TAG_NAME, None)
    file_tags.pop(ALBUM_TAG_NAME, None)
    file_tags.pop(GENRE_TAG_NAME, None)
    file_tags.pop(YEAR_TAG_NAME, None)
    
def read_tags(filename, format_list, delim):
    tag_list = filename.split(delim)
    assert len(tag_list) >= len(format_list), "Number tags in file smaller than expected according to format"
    
    file_tags = {}
    for index, value in enumerate(tag_list):
        tag_name = format_list[index]
        if tag_name == TITLE_TAG_NAME:
            file_tags[tag_name] = replace_specials(value)
        else:
            file_tags[tag_name] = value

    return file_tags

def write_toc_file(dir, record_metadata):
    with open(dir + os.sep + "ToC.json", "w") as json_file:
        json.dump(record_metadata, json_file, indent=2)

def rename_files(dir, record_metadata):
    for track_info in record_metadata[TRACK_LIST_NAME]:
        long_name = track_info[FILENAME_TAG_NAME][LONG_FILENAME_TAG_NAME]
        short_name = track_info[FILENAME_TAG_NAME][SHORT_FILENAME_TAG_NAME]
        os.rename(dir + os.sep + long_name, dir + os.sep + short_name)

def read_dir(dir, type, format_list, delim):
    with os.scandir(dir) as iter:
        record_metadata = {
            ARTIST_TAG_NAME: '',
            ALBUM_TAG_NAME: '',
            GENRE_TAG_NAME: '',
            YEAR_TAG_NAME: '',
            TRACK_LIST_NAME: []
        }
        
        for entry in iter:
            if entry.is_file() and entry.name.endswith("." + type):
                file = entry.name
                file_no_ext = file[:-1 * (1 + len(type))]

                file_tags = read_tags(file_no_ext, format_list, delim)
                file_tags[FILENAME_TAG_NAME] = {
                    LONG_FILENAME_TAG_NAME: entry.name,
                    SHORT_FILENAME_TAG_NAME: simple_filename(file_tags, type)
                }

                fill_record_metadata(record_metadata, file_tags)
                remove_redundant_tags(file_tags)

                record_metadata[TRACK_LIST_NAME].append(file_tags)
        
        if record_metadata[TRACK_LIST_NAME]:
            write_toc_file(dir, record_metadata)
            rename_files(dir, record_metadata)

def read_recursive(dir, type, format_list, delim):
    for subdir, _, _ in os.walk(dir):
        read_dir(subdir, type, format_list, delim)

def validate_format_list(format_list):
    pass

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--format", 
        help="""Format how filenames encode tags. Comma separated list of 
            'artist', 'album', 'year', 'genre', 'track', 'title'.""")
    parser.add_argument(
        "-d", "--delim", 
        help="Delimiter that separates tags in the filename.")
    parser.add_argument(
        "-s", "--source",
        help="Directory to scan for music files.")
    parser.add_argument(
        "-r", "--recurse", 
        action='store_true',
        help="Specify if directory shall be scanned recursively.")
    parser.add_argument(
        "-t", "--type", 
        help="Filename extension that specifies the audio files to look for.")
    return parser.parse_args()

args = parse_args()

format_list = args.format.split(",")
validate_format_list(format_list)

if args.recurse is True:
    read_recursive(args.source, args.type, format_list, args.delim)
else:
    read_dir(args.source, args.type, format_list, args.delim)