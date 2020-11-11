# pywavchopper
Chops large wav files into chunks based on loudness level drops (silence gets cut out). Performs good on large files.
Might be useful for chopping band rehearsal into songs or interviews into chunks.

# Functions
- Read a single .wav file from source_dir
- Split wav file into chunks with configurable loudness and threshold parameters. Chunks' metadata gets displayed so the user can decide whether the parameters are ok.
- Export all (or specified single) chunk as wav or mp3 into target_dir/format/ e.g. /2020-07-08/mp3/
- For mp3 the tags are assigned

# Parameters
- Default settings are controlled via .ini file (see default.ini as example) but can be changed during runtime
- .ini Filename can be given as parameter from command-line, thus it is possible to create different .ini files to different use cases (e.g. different loudness scenarios or different bands)

# Example

```
python3 pywavchopper.py m0.ini
Source wav filename (within /Users/alec/Music Production/Projects/m0/Rehearsals/source folder)? 2020-07-
28.wav
==============================================================================================================
Analyzing File /Users/alec/Music Production/Projects/m0/Rehearsals/source/2020-06-23-1.wav
Length: 01:08:34
Average Loudness: -21 dBFS
Silence Threshold (default: -40 dBFS): [Enter]
Minimal Chunk Length (default: 60000 ms): [Enter]
Loudness Peak (default: 20 dBFS): [Enter]
==============================================================================================================
Building Chunks
01_chunk: 00:00:00-00:06:27 (06:27)
02_chunk: 00:08:19-00:13:56 (05:37)
03_chunk: 00:18:40-00:21:05 (02:25)
04_chunk: 00:21:07-00:23:55 (02:48)
05_chunk: 00:26:48-00:32:25 (05:37)
06_chunk: 00:37:37-00:42:54 (05:17)
07_chunk: 00:51:03-00:56:38 (05:35)
08_chunk: 01:02:12-01:07:19 (05:07)
==============================================================================================================
Export? (default: Yes): [Enter]
Single Chunk (provide #, 0 for all)? (default: 0): [Enter]
Export Format (default: mp3): wav
==============================================================================================================
Exporting to /Users/alec/Music Production/Projects/m0/Rehearsals/chopped/2020-06-23-1/wav/
01_chunk.wav
02_chunk.wav
03_chunk.wav
04_chunk.wav
05_chunk.wav
06_chunk.wav
07_chunk.wav
08_chunk.wav
==============================================================================================================
Export again? (default: Yes): [Enter]
Single Chunk (provide #, 0 for all)? (default: 0): 5
Export Format (default: mp3): mp3
Export Codec (default: mp3): [Enter]
==============================================================================================================
Exporting to /Users/alec/Music Production/Projects/m0/Rehearsals/chopped/2020-06-23-1/mp3/
05_chunk.mp3
==============================================================================================================
Export again? (default: Yes): N
Process one more file? (default: Yes): N
```

# Dependencies
- pydub
- Exporting to mp3 requires ffmpeg
