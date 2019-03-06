import os
import taglib
import argparse

def is_hidden(name):
    return name[0] == "."
    
def concat_with_sep(path, other):
    pathcopy = path
    if not path.endswith(os.sep):
        pathcopy = path + os.sep
    return pathcopy + other

def modify_tags(file, args):
    song = taglib.File(file)
    if args.artist:
        song.tags["ARTIST"] = [args.artist]
    if args.album:
        song.tags["ALBUM"] = [args.album]
    if args.title:
        song.tags["TITLE"] = [args.title]
    if args.genre:
        song.tags["GENRE"] = [args.genre]
    if args.date:
        song.tags["DATE"] = [args.date]
    if args.tracknumber:
        song.tags["TRACKNUMBER"] = [args.tracknumber]
    song.save()

def read_dir(dir, args):
    for subdir, _, files in os.walk(dir):
        for file in files:
            if not is_hidden(file):
                modify_tags(concat_with_sep(subdir, file), args)

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--src", help="Folder or file to read", required=True)
parser.add_argument("-a", "--artist")
parser.add_argument("-b", "--album")
parser.add_argument("-t", "--title")
parser.add_argument("-g", "--genre")
parser.add_argument("-d", "--date")
parser.add_argument("-n", "--tracknumber")
args = parser.parse_args()

if os.path.isdir(args.src):
    read_dir(args.src, args)
else:
    modify_tags(args.src, args)
