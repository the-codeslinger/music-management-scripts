import os
import json
import eyed3
import codecs
import argparse
import subprocess
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

FORWARD_SLASH_STRING = "/"
COLON_STRING = ":"
QUESTION_MARK_STRING = "?"
EXLAMATION_MARK_STRING = "!"
BACKSLASH_STRING = "\\"
HASH_STRING = "#"
SINGLE_QUOTE_STRING = "'"
DOT_STRING = "."
COMMA_STRING = ","

CONVERTER_INPUT = "%input%"
CONVERTER_OUTPUT = "%output%"

TOC_FILENAME = "ToC.json"

def is_hidden(name):
    return name[0] == "."

def sanitize(value):
    value = value \
        .replace("\"", "") \
        .replace(FORWARD_SLASH_STRING, "_") \
        .replace(COLON_STRING, "_") \
        .replace(QUESTION_MARK_STRING, "_") \
        .replace(BACKSLASH_STRING, "_") \
        .replace(HASH_STRING, "") \
        .replace(SINGLE_QUOTE_STRING, "") \
        .replace(DOT_STRING, "") \
        .replace(COMMA_STRING, "") \
        .replace(EXLAMATION_MARK_STRING, "")

    return sanitize_filename(value)

def make_destination_file_name(output_config, toc, track):
    out_path = output_config["path"]
    formatted_file_path = output_config["format"] \
        .replace(ARTIST_TAG_NAME, sanitize(toc[ARTIST_TAG_NAME])) \
        .replace(ALBUM_TAG_NAME, sanitize(toc[ALBUM_TAG_NAME])) \
        .replace(GENRE_TAG_NAME, sanitize(toc[GENRE_TAG_NAME])) \
        .replace(YEAR_TAG_NAME, sanitize(toc[YEAR_TAG_NAME])) \
        .replace(TRACK_TAG_NAME, sanitize(track[TRACK_TAG_NAME])) \
        .replace(TITLE_TAG_NAME, sanitize(track[TITLE_TAG_NAME]))
    return os.path.join(out_path, formatted_file_path + "." + output_config["type"])

def make_destination_folder(destination_filename):
    folder = os.path.dirname(destination_filename)
    os.makedirs(folder, exist_ok=True)

def convert_file(output_config, source, destination):
    converter_config = output_config["converter"]
    exec_config = [converter_config["bin"]]

    for arg in converter_config["args"]:
        if arg == CONVERTER_INPUT:
            exec_config.append(source)
        elif arg == CONVERTER_OUTPUT:
            exec_config.append(destination)
        else:
            exec_config.append(arg)

    subprocess.run(exec_config)

def write_mp3_tags(file, album_tags, file_tags, cover_art_filename):
    song = eyed3.load(file)

    if not song.tag:
        song.initTag()

    if album_tags[ARTIST_TAG_NAME]:
        song.tag.artist = album_tags[ARTIST_TAG_NAME]
    if album_tags[ALBUM_TAG_NAME]:
        song.tag.album = album_tags[ALBUM_TAG_NAME]
    if album_tags[GENRE_TAG_NAME]:
        song.tag.genre = album_tags[GENRE_TAG_NAME]
    if album_tags[YEAR_TAG_NAME]:
        song.tag.recording_date = album_tags[YEAR_TAG_NAME]
    if file_tags[TRACK_TAG_NAME]:
        song.tag.track_num = file_tags[TRACK_TAG_NAME]
    if file_tags[TITLE_TAG_NAME]:
        song.tag.title = file_tags[TITLE_TAG_NAME]

    if os.path.exists(cover_art_filename):
        with open(cover_art_filename, "rb") as cover_art:
            song.tag.images.set(3, cover_art.read(), "image/jpeg")
    else:
        print(f"{cover_art_filename} not found")

    song.tag.save(version=eyed3.id3.ID3_V2_3)

def read_dir(dir, input_type, output_config):
    with codecs.open(os.path.join(dir, TOC_FILENAME), "r", encoding="UTF-8") as f:
        cover_art_filename = os.path.join(dir, "Cover.jpg")
        toc = json.load(f)
        
        for track in toc["tracks"]:
            source = os.path.join(dir, track[FILENAME_TAG_NAME][SHORT_FILENAME_TAG_NAME])
            assert os.path.exists(source), f"File not found {source}"

            destination = make_destination_file_name(output_config, toc, track)
            make_destination_folder(destination)

            if not os.path.exists(destination):
                convert_file(output_config, source, destination)
                write_mp3_tags(destination, toc, track, cover_art_filename)

def read_recursive(input_config, output_config):
    root_path = input_config["path"]
    for subdir, _, _ in os.walk(root_path):
        if os.path.exists(os.path.join(subdir, TOC_FILENAME)):
            read_dir(subdir, input_config["type"], output_config)

def read_config(config_path):
    input_config = None
    output_config = None

    with codecs.open(config_path, "r", encoding="UTF-8") as f:
        data = json.load(f)
        input_config = data["input"]
        for out_type in data["output"]:
            if out_type["type"] == args.type:
                output_config = out_type

    assert input_config, f"Input configuration not found; check configuration '{config_path}'"
    assert output_config, f"Output configuration {args.type} not found; check configuration '{config_path}'"

    return input_config, output_config

def make_abs_config_path(config):
    config_path = config
    if not os.path.isabs(config):
        config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), config)
    return config_path

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", 
        help="""Optional configuration file. Defaults to {script-dir}/etc/convert-music.json""",
        default="etc/convert-music.json")
    parser.add_argument(
        "-t", "--type", 
        help="The output file type as configured in convert-music.json")
    return parser.parse_args()

args = parse_args()

input_config, output_config = read_config(make_abs_config_path(args.config))

eyed3.log.setLevel("ERROR")

if input_config["recurse"] is True:
    read_recursive(input_config, output_config)
else:
    read_dir(input_config["path"], input_config["type"], output_config)