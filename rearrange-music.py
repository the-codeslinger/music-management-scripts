import os
import taglib
import argparse
import shutil
import string
import unicodedata

ARTIST_TAG = "ARTIST"
ALBUM_TAG = "ALBUM"
TITLE_TAG = "TITLE"
DATE_TAG = "DATE"
GENRE_TAG = "GENRE"
TNUM_TAG = "TRACKNUMBER"

SUPPORTED_TAGS = [ARTIST_TAG, ALBUM_TAG, TITLE_TAG, DATE_TAG, GENRE_TAG, TNUM_TAG]
VALID_FNAME_CHARS = "-_() %s%s" % (string.ascii_letters, string.digits)
CHAR_LIMIT = 255

# Thx to https://gist.github.com/wassname/1393c4a57cfcbf03641dbc31886123b8 for this method.
def clean_filename(filename, whitelist=VALID_FNAME_CHARS):
    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()
    
    # keep only whitelisted chars
    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
    if len(cleaned_filename)>CHAR_LIMIT:
        print("Warning, filename truncated because it was over {}. Filenames may no longer be unique".format(CHAR_LIMIT))
    return cleaned_filename[:CHAR_LIMIT] 

def is_hidden(name):
    return name[0] == "."

def make_placeholder(tag):
    return "{%s}" % tag

def concat_with_sep(path, other):
    pathcopy = path
    if not path.endswith(os.sep):
        pathcopy = path + os.sep
    return pathcopy + other

def read_tags(file):
    song = taglib.File(file)
    tags = {}
    
    for suptag in SUPPORTED_TAGS:
        if song.tags[suptag]:
            value = song.tags[suptag][0]

            # Always use two-digit tracknumbers. Also take care of something like '1/10' 
            # and only use the first number.
            if suptag == TNUM_TAG:
                slashpos = value.find("/")
                if -1 != slashpos:
                    value = value[:slashpos]
                value = "{:02d}".format(int(value))

            # Flatten the lists of values that are contained per tag into a single value.
            # Easier to use and all I need.
            tags[make_placeholder(suptag)] = value
    return tags

def move_file(srcfile, destpath, fname):
    if not os.path.exists(destpath):
        os.makedirs(destpath)
    
    destfile = concat_with_sep(destpath, fname)
    if not os.path.exists(destfile):
        print("Move '%s' to '%s'" % (os.path.basename(srcfile), destfile))
        shutil.move(srcfile, destfile)
    else:
        print("File already exists '%s'" % destfile)
        os.remove(srcfile)

def dest_fname(src, dest, file, format):
    newpath = format.upper()
    srcfile = concat_with_sep(src, file)

    tags = read_tags(srcfile)
    # Replace all placeholders with values.
    for tag in tags:
        if tag in newpath:
            newpath = newpath.replace(tag, clean_filename(tags[tag]))
    
    # Extract the file name so we have it separately. We also need to attach the extension.
    _, ext = os.path.splitext(srcfile)
    destfname = ''

    fnamestart = newpath.rfind(os.sep)
    if -1 == fnamestart:
        destfname = newpath + ext
        newpath = ''
    else:
        destfname = newpath[fnamestart + 1:] +  ext
        newpath = newpath[0:fnamestart]
    
    return (concat_with_sep(dest, newpath), destfname)

def scan_src_and_move_files(src, dest, format):
    for subdir, _, files in os.walk(src):
        for file in files:
            if not is_hidden(file):
                path, fname = dest_fname(subdir, dest, file, format)
                move_file(concat_with_sep(subdir, file), path, fname)

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--src", required=True, help="Source folder to scan for music files")
parser.add_argument("-d", "--dest", required=True, help="Destination root under which to create structure")
parser.add_argument("-f", "--format", required=True, help="""Describes the relative path at the destination. 
    Supported tags: {artist}, {album}, {title}, {genre}, {date}, {tracknumber}. 
    The last item of the format string will be the file's name.
    Tracknumber is always with a leading zero.
""")
args = parser.parse_args()

if not os.path.isdir(args.src):
    print("ERROR: Source must be a directory")
    exit(1)
else:
    scan_src_and_move_files(args.src, args.dest, args.format)
