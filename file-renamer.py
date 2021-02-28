import os
import json
import codecs
import argparse
from pathvalidate import sanitize_filename

TOC_FILENAME = "ToC.json"

TRACK_TAG_NAME = 'track'
TITLE_TAG_NAME = 'title'

FILENAME_TAG_NAME = 'filename'
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

def read_toc(dir):
    with codecs.open(os.path.join(dir, TOC_FILENAME), "r", encoding="UTF-8") as f:
        return json.load(f)

def write_toc(dir, toc):
    with codecs.open(os.path.join(dir, TOC_FILENAME), "w", encoding="UTF-8") as f:
        json.dump(toc, f, indent=2, ensure_ascii=False)

def sanitize(value):
    value = value \
        .replace("\"", "") \
        .replace(FORWARD_SLASH_STRING, "") \
        .replace(COLON_STRING, "") \
        .replace(QUESTION_MARK_STRING, "") \
        .replace(BACKSLASH_STRING, "") \
        .replace(HASH_STRING, "") \
        .replace(SINGLE_QUOTE_STRING, "") \
        .replace(DOT_STRING, "") \
        .replace(COMMA_STRING, "") \
        .replace(EXLAMATION_MARK_STRING, "")
    return sanitize_filename(value)

def rename_file(dir, file, track_no, title):
    file_name = track_no + " - " + sanitize(title) + ".wav"
    os.rename(file, os.path.join(dir, file_name))
    return file_name

def read_dir(dir):
    if not os.path.exists(os.path.join(dir, TOC_FILENAME)):
        print(f"No ToC found in {dir}, skipping")
        return
    
    toc = read_toc(dir)
    for track in toc["tracks"]:
        source = os.path.join(dir, track[FILENAME_TAG_NAME][SHORT_FILENAME_TAG_NAME])
        assert os.path.exists(source), f"File not found {source}"

        track_no = track[TRACK_TAG_NAME]
        title = track[TITLE_TAG_NAME]

        new_name = rename_file(dir, source, track_no, title)
        track[FILENAME_TAG_NAME][SHORT_FILENAME_TAG_NAME] = new_name
    
    write_toc(dir, toc)

def read_recursive(dir):
    for subdir, _, _ in os.walk(dir):
        read_dir(subdir)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--source", 
        help="Folder to scan recursively")
    return parser.parse_args()

args = parse_args()
read_recursive(args.source)