#!/bin/python
# Requirements: scipy, numpy. You might need to pip install these if you don't have them.
# After editing the below settings, run 'python convert-may-audio.py' or perhaps
# 'python3 convert-mat-audio.py', depending on your system
# Note that everything here assumes single-channel (mono) audio.

import scipy.io
import scipy.io.wavfile
import numpy as np
from pathlib import PurePath, Path
from glob import glob
import subprocess

########### User-editable settings ###########
# Search pattern for .mat files. Examples:
# * '/Users/cbrendel/blah/**/*.mat'  - all files in /Users/cbrendel/blah and its
#                                     subdirectories that end with a .mat extension
# * '/Users/cbrendel/matfiles/*.mat' - all files directly in /Users/cbrendel/matfiles
#                                      that end in .mat, but NOT in subdirectories
# * '/Users/cbrendel/testfile.mat'   - just one file located at this path
matPath = '/home/cbrendel/techproj/temp_help/karen/affected/**/*.mat'

# The location where new wav files will be saved. Examples:
# * '' (ie, blank)         - new files will be saved in the same directory that each .mat
#                            is loaded from (default).
# * '/Users/cbrendel/wavs' - all wav files will be saved in /Users/cbrendel/wavs
wavPath = ''

# Format of filenames for the exported wav files. {fileName} will be replaced with the
# name of the original file, minus the file extension.
# * '{fileName}.wav' turns 'JPN_P1_02.mat' -> 'JPN_P1_02.wav'
wavFnFormat = '{fileName}.wav'

# Force wav files to be exported at a particular bitrate. This shouldn't need to be
# changed. By default (None), the sample rate provided in the .mat file will be used.
# Otherwise, enter Hz as an integer (e.g. forceBitrate = 24000 will output all files at
# 24000Hz).
forceBitrate = None

## Compression ##
# Experimental. If set to True, attempt to use ffmpeg to compress the wav files.
# There might be minor loss in audio quality depending on your ffmpeg default settings,
# but typically enabled compression provides a good balance of audio quality and file
# size (1/4 of the size typically). You also will need to have ffmpeg installed.
compress = False

# If using compression, we need to specify the bit depth of the input. (I was too lazy to
# do this automatically). You shouldn't need to worry about this, assuming that the raw
# audio in the .mat files are all saved at the same bit depth. As far as I can tell, EMA
# exports audio at 64-bit bit depth, which is what the default value here means.
ffInputBitdepth = 'f64le'
####

########### End user-editable settings ###########

overwriteAll = False
remKeys = {'__header__', '__version__', '__globals__'}

for matFilename in glob(matPath, recursive=True):
    # Load mat file into memory and retrieve raw audio data
    mat = scipy.io.loadmat(matFilename)

    # Try to automatically load the correct record. Usually this matches the filename, but
    # this could easily break. I assume there's one record per .mat file
    recordLoc = mat.keys() - remKeys
    assert len(recordLoc) == 1, 'More than one record in {}; not sure what to do'\
                                .format(matFilename)
    record = mat[recordLoc.pop()]

    audio = None
    for field in record[0]:
        if field[0][0] == 'AUDIO':
            audio = np.squeeze(field[2])
            srate = forceBitrate or field[1][0][0]
            break
    assert audio is not None, 'Could not find AUDIO field in {}'.format(matFilename)

    matPath = PurePath(matFilename)
    wavFilename = PurePath('/').joinpath(wavPath or matPath.parent,
                                         wavFnFormat.format(fileName=matPath.stem))

    if Path(wavFilename).exists() and not overwriteAll:
        resp = input("{} already exists.\n Overwrite? ([N]o, [y]es, overwrite [a]ll, [q]uit): ".
                     format(wavFilename)).lower()[:1]
        if resp == 'y':
            pass
        elif resp == 'a':
            overwriteAll = True
        elif resp == 'q':
            break
        else:
            print("Skipped this file")
            continue

    if compress:
        subprocess.run(['ffmpeg',
                        '-loglevel', 'fatal',
                        '-y',
                        '-stdin',
                        '-f', ffInputBitdepth,
                        '-ar', str(srate),
                        '-ac', '1',
                        '-i', 'pipe:',
                        str(wavFilename)],
                       input=audio.tobytes(), stdout=None, stderr=subprocess.STDOUT)
    else:
        scipy.io.wavfile.write(str(wavFilename), srate, audio)

    print('Wrote {} to disk!'.format(wavFilename))
