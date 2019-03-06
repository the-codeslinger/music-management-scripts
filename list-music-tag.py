import os
import argparse
import subprocess

def is_hidden(name):
    return name[0] == "."
    
def print_tags(file):
    process = subprocess.Popen(["pyprinttags3", "-b", file])
    process.wait()

def read_dir(dir):
    for subdir, _, files in os.walk(dir):
        for file in files:
            if not is_hidden(file):
                print_tags(subdir + os.sep + file)

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--src", help="Folder or file to read")
args = parser.parse_args()

if os.path.isdir(args.src):
    read_dir(args.src)
else:
    print_tags(args.src)