# music-management-scripts

A bunch of Python scripts to perform a few management tasks on the files of a local digital music library

## Requirements

* Python 3
* [pytaglib](https://pypi.org/project/pytaglib/)
* [libtaglib](https://taglib.org) (required by pytaglib)

## General

Every script supports `-h` and `--help` that will print a list of arguments. They are self-explanatory.

## Show a file's tags

Supports single files or a recursive directory scan.

    python3 list-music-tags.py --src /somewhere/on/your/drive

The output will look like this for every file.

    ***************************************
    TAGS OF '06 Another fallen brother.m4a'
    ***************************************
    ALBUM       = Valkyrja
    ARTIST      = Týr
    DATE        = 2013
    ENCODEDBY   = Nero AAC codec / 1.5.1.0
    GENRE       = Pagan Metal
    TITLE       = Another fallen brother
    TRACKNUMBER = 6
    Unsupported tag elements: ----:com.apple.iTunes:cdec; ----:com.apple.iTunes:iTunSMPB; covr

## Modify a file's tags

Supports single files or a recursive directory scan.

    python3 modify-music-tag.py --src /somewhere/on/your/drive --artist Wolfheart --genre "Melodic Death Metal"

Supported tags are:

* Artist
* Album
* Title
* Genre
* Date
* Tracknumber

## Rearrange music files

Only works with a directory. Reads every file's tags and moves them to a new location based on a naming scheme.

    python3 rearrange-music.py --src /somewhere/on/your/drive --dest /somewhere/else --format "{genre}/{artist}/{date} - {album}/{tracknumber} - {title}"

This will move all the files to `/somewhere/else` and create a folder structure that starts with the song's genre directly followed by the artist. The album will contain the year, both tags separated by a hyphen. Lasty the tracknumber and the song't title will be the file's name. The tracknumber will contain a leading zero to ensure a proper ordering at all times.