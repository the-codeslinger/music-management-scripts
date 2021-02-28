# music-management-scripts

A bunch of Python scripts to perform a few management tasks on the
files of a (my) local digital music library.

## Requirements

* Python 3
* [pytaglib](https://pypi.org/project/pytaglib/)
* [libtaglib](https://taglib.org) (required by pytaglib)
* [pathvalidate](https://pypi.org/project/pathvalidate/) (required by `create_toc.py`)
* [eyeD3](https://eyed3.readthedocs.io/en/latest/index.html) (required by `convert-music.py`)

## General

Every script supports `-h` and `--help` that will print a list of arguments.
They should be self-explanatory.

## Show a file's tags (list-music-tags.py)

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

## Modify a file's tags (modify-music-tag.py)

Supports single files or a recursive directory scan.

    python3 modify-music-tag.py --src /somewhere/on/your/drive --artist Wolfheart --genre "Melodic Death Metal"

Supported tags are:

* Artist
* Album
* Title
* Genre
* Date
* Tracknumber

## Rearrange music files (rearrange-music.py)

Only works with a directory. Reads every file's tags and moves them to
a new location based on a naming scheme.

    python3 rearrange-music.py --src /somewhere/on/your/drive --dest /somewhere/else --format "{genre}/{artist}/{date} - {album}/{tracknumber} - {title}"

This script will move all the files to `/somewhere/else` and create a
folder structure that starts with the song's genre directly followed
by the artist. The album will contain the year, both tags separated by
a hyphen. Lastly, the track number and the song's title will be the
file's name. The track number will contain a leading zero to ensure
proper ordering at all times.

## Create Table of Contents (create-toc.py)

This script reads the content of a folder full of audio files and
parses the metadata from the file names. The assumption is that all
files in the folder are part of the same album or compilation and
follow a consistent naming scheme. The artist's name and album title
(or the equivalent of a compilation) must be the same for every file.

The purpose is for each folder to contain a JSON file, the TOC, or
table of contents, that has the relevant metadata about an audio disc.
This way, the file names can be simplified and do not require any more
special encoding. This script helps to convert an encoded naming
scheme created by ripping an audio disc to a more modern way. This 
includes getting rid of encoded characters like `&47;` for `/`, `&58;` 
for `:`, `&63;` for `?`, and `&92;` for `\`.

The `ToC.json` looks like this.

```json
{
  "artist": "Wolfheart",
  "album": "Winterborn",
  "genre": "Melodic Death Metal",
  "year": "2013",
  "tracks": [
    {
      "track": "01",
      "title": "The hunt",
      "filename": {
        "long": "Wolfheart#Winterborn#2013#Melodic Death Metal#01#The hunt.wav",
        "short": "01-The_hunt.wav"
      }
    },
    {
      ...
    },
    ...
  ]
}
```

The original "long" filename is retained in case something goes wrong
during TOC creation while renaming from "long" to "short". This way,
all the information is still available.

The naming scheme can be configured using the `format` option in the
configuration file. The following types of tags are supported. Not all
values are required, but you cannot specify more tags than are
available in the filename.

* artist
* album
* year
* genre
* track
* title

This way, you can configure the parser to your naming scheme. The tag
delimiter can be provided with `delim`. The script only scans for a
specific file type that is identified by the file's extension. The
argument `type` configures this extension. Note: do **not** include
the dot, e.g. use `-t wav` instead of `.wav`. This value is also used
for renaming the files.

You can also specify a config file on the command line if the default
location in `<script-dir>/etc` does not suit you.

    python3 create-toc.py --config /opt/music-scripts/table-of-content.json

## Convert WAV to MP3 (convert-music.py)

Convert all files mentioned in a `ToC.json` file to compressed audio
as configured in the settings file (default
`<script-dir>/etc/convert-music.json`). The setting file can contain
multiple compressor configurations from which one must be selected on
the command line using the `--type` option.

The call to the converter's command line supports `%input%` and
`%output%` parameters that are replaced with the source WAV file and
the output MP3 file.

Although the configuration and script support multiple output formats,
writing metadata is currently limited to ID3, i.e. the only output
effectively supported is MP3. This is due to the fact that eyed3 is
used as a tagging library, not pytaglib. The latter does not support
cover art in Python scripts whereas eyed3 does for MP3 - which is good
enough for me.

You can also specify a config file on the command line if the default
location in `<script-dir>/etc` does not suit you.

    python3 convert-music.py --type mp3 --config /opt/music-scripts/converter.json

## Rename Files (file-renamer.py)

This little script reads the `ToC.json` file in every directory  and
renames the files based on the hard-coded rules in its `sanitize`
function. The `ToC.json` is updated accordingly. This script is not
part of any workflow and more or less serves as an additional utility
in case I change my mind regarding the file name format.

The only argument is the source path to scan and scanning is performed
recursively.

  python3 file-renamer --source /home/rlo/audio-discs

