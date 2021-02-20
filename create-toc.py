# Scan directories for audio files with a given extension and read the
# meta data from the file"s name to create a table of contents JSON
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
import codecs
import argparse
from pathvalidate import sanitize_filename

ARTIST_TAG_NAME = "artist"
ALBUM_TAG_NAME = "album"
GENRE_TAG_NAME = "genre"
YEAR_TAG_NAME = "year"
TRACK_TAG_NAME = "track"
TITLE_TAG_NAME = "title"
TRACK_LIST_NAME = "tracks"
FILENAME_TAG_NAME = "filename"
LONG_FILENAME_TAG_NAME = "long"
SHORT_FILENAME_TAG_NAME = "short"

FORWARD_SLASH_STRING = "/"
FORWARD_SLASH_CODE = "&47;"

COLON_STRING = ":"
COLON_CODE = "&58;"

QUESTION_MARK_STRING = "?"
QUESTION_MARK_CODE = "&63;"

BACKSLASH_STRING = "\\"
BACKSLASH_CODE = "&92;"

HASH_STRING = "#"
HASH_CODE = "&35;"

TOC_FILENAME = "ToC.json"

def is_hidden(name):
    return name[0] == "."

def get_artist(file_tags):
    return file_tags[ARTIST_TAG_NAME] if ARTIST_TAG_NAME in file_tags else ""

def get_album(file_tags):
    return file_tags[ALBUM_TAG_NAME] if ALBUM_TAG_NAME in file_tags else ""

def get_genre(file_tags):
    return file_tags[GENRE_TAG_NAME] if GENRE_TAG_NAME in file_tags else ""

def get_year(file_tags):
    return file_tags[YEAR_TAG_NAME] if YEAR_TAG_NAME in file_tags else ""

def get_track(file_tags):
    return file_tags[TRACK_TAG_NAME].zfill(2) if TRACK_TAG_NAME in file_tags else ""

def get_title(file_tags):
    return file_tags[TITLE_TAG_NAME] if TITLE_TAG_NAME in file_tags else ""

def replace_specials(value):
    return value \
        .replace(FORWARD_SLASH_CODE, FORWARD_SLASH_STRING) \
        .replace(COLON_CODE, COLON_STRING) \
        .replace(QUESTION_MARK_CODE, QUESTION_MARK_STRING) \
        .replace(BACKSLASH_CODE, BACKSLASH_STRING) \
        .replace(HASH_CODE, HASH_STRING)

def simple_filename(file_tags, type):
    track = get_track(file_tags)
    title = get_title(file_tags)

    filename = ""
    if track and title:
        filename = track + " - " + title + "." + type
    elif track and not title:
        filename = track + "." + type
    elif not track and title:
        filename = title + "." + type
    
    # Sanitize_filename removes my coded special characters.
    filename = filename \
        .replace("\"", "") \
        .replace(",", "") \
        .replace("!", "") \
        .replace(FORWARD_SLASH_STRING, "") \
        .replace(COLON_STRING, "") \
        .replace(QUESTION_MARK_STRING, "") \
        .replace(BACKSLASH_STRING, "") \
        .replace(HASH_STRING, "")

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
    
def read_tags(filename, config):
    format_list = config["format"]
    tag_list = filename.split(config["delim"])
    assert len(tag_list) <= len(format_list), f"Number tags in file {filename} larger than expected according to format"
    
    file_tags = {}
    for index, value in enumerate(tag_list):
        tag_name = format_list[index]
        file_tags[tag_name] = replace_specials(value)

    return file_tags

def write_toc_file(dir, record_metadata):
    with codecs.open(os.path.join(dir, TOC_FILENAME), "w", encoding="UTF-8") as json_file:
        json.dump(record_metadata, json_file, indent=2)

def rename_files(dir, record_metadata):
    for track_info in record_metadata[TRACK_LIST_NAME]:
        long_name = track_info[FILENAME_TAG_NAME][LONG_FILENAME_TAG_NAME]
        short_name = track_info[FILENAME_TAG_NAME][SHORT_FILENAME_TAG_NAME]
        os.rename(os.path.join(dir, long_name), os.path.join(dir, short_name))

def read_dir(subdir, config):
    print(subdir)
    if os.path.exists(os.path.join(subdir, TOC_FILENAME)):
        print(f"Folder {subdir} already contains ToC")
        return
    
    with os.scandir(subdir) as iter:
        record_metadata = {
            ARTIST_TAG_NAME: "",
            ALBUM_TAG_NAME: "",
            GENRE_TAG_NAME: "",
            YEAR_TAG_NAME: "",
            TRACK_LIST_NAME: []
        }
        
        for entry in iter:
            type = config["type"]
            if entry.is_file() and entry.name.endswith("." + type):
                file = entry.name
                file_no_ext = file[:-1 * (1 + len(type))]

                file_tags = read_tags(file_no_ext, config)
                file_tags[FILENAME_TAG_NAME] = {
                    LONG_FILENAME_TAG_NAME: entry.name,
                    SHORT_FILENAME_TAG_NAME: simple_filename(file_tags, type)
                }

                fill_record_metadata(record_metadata, file_tags)
                remove_redundant_tags(file_tags)

                record_metadata[TRACK_LIST_NAME].append(file_tags)
        
        if record_metadata[TRACK_LIST_NAME]:
            write_toc_file(subdir, record_metadata)
            rename_files(subdir, record_metadata)

def read_recursive(config):
    for subdir, _, _ in os.walk(config["source"]):
        read_dir(subdir, config)

def read_config(config_path):
    with codecs.open(config_path, "r", encoding="UTF-8") as f:
        return json.load(f)

def make_abs_config_path(config):
    config_path = config
    if not os.path.isabs(config):
        config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), config)
    return config_path

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", 
        help="""Optional configuration file. Defaults to {script-dir}/etc/create-toc.json""",
        default="etc/create-toc.json")
    return parser.parse_args()

args = parse_args()

config = read_config(make_abs_config_path(args.config))
if config["recurse"] is True:
    read_recursive(config)
else:
    read_dir(config["source"], config)