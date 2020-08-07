# pywavchopper
# Usage: python3 pywavchopper.py myconfig.ini

import sys
import configparser
import os
from pydub import AudioSegment

# Initialize global vars
chunks = []
chunks_metadata = []
sound = None
source = None

def convert_ms(ms):
    ss=int((ms/1000)%60)
    mm=int((ms/(1000*60))%60)
    hh=int((ms/(1000*60*60))%24)
    return ss, mm, hh

def build_chunks(silence_threshold = -40 # Everything below is considered silence
               , chunk_min_length = 60000 # 1 Min, Minimal length of chunk that is considered for export
               , loudness_peak = 20 # Change in loudness in dBFS that would mean start/end of a chunk
               , fadeinout = 2000 # 2 Sec, Time to add at the beginning and end of chunk
               ):
    global chunks
    global chunks_metadata
    chunks = []
    chunks_metadata = []
    analysis_step = 1000 # 2 Sec, in which steps to analyse source audio
    prev_step_loudness = -100
    curr_step_loudness = -100
    chunk_start = 0
    chunk_end = 0
    z = 0

    # Move through source sound, measure loudness of every step and compare it to the previous one
    for i, step in enumerate(sound[::analysis_step]):
       prev_step_loudness = curr_step_loudness
       curr_step_loudness = step.dBFS

       # Consider everything that is quiter then threshold as silent
       if(curr_step_loudness < silence_threshold):
           curr_step_loudness = -100

       # Consider changes in loudness that are are higher than loudness_peak as start/end events
       if(abs(abs(curr_step_loudness)-abs(prev_step_loudness)) > loudness_peak):
           if(prev_step_loudness < curr_step_loudness):
               chunk_start = int(i*analysis_step)
           else:
               chunk_end = int(i*analysis_step)

           # If current chunk is longer that defined minimal length then consider it
           if(chunk_end > chunk_start and chunk_end - chunk_start > chunk_min_length):
               chunks.append(sound[chunk_start-fadeinout:chunk_end+fadeinout])
               # Gather some metadata, just for display
               start_pos_ss, start_pos_mm, start_pos_hh = convert_ms(chunk_start)
               end_pos_ss, end_pos_mm, end_pos_hh = convert_ms(chunk_end)
               duration_ss, duration_mm, duration_hh = convert_ms(chunk_end-chunk_start)
               chunks_metadata.append("{0}_chunk".format(str(z+1).zfill(2)) + ": " + "{0}:{1}:{2}-{3}:{4}:{5} ({6}:{7})".format(str(start_pos_hh).zfill(2), str(start_pos_mm).zfill(2), str(start_pos_ss).zfill(2), str(end_pos_hh).zfill(2), str(end_pos_mm).zfill(2), str(end_pos_ss).zfill(2), str(duration_mm).zfill(2), str(duration_ss).zfill(2)))
               print(chunks_metadata[z])
               z += 1

def export_chunks(export_dir, export_chunk_nr = 0, export_format = "mp3", export_codec = "mp3", export_tags = {}, export_bitrate = "256k"):
    global source
    global params_log

    print("Exporting to " + export_dir + "/")
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    log = open(export_dir + "/chop.log", "w")
    log.write("Chopping Source File " + source + "\n=======================================\n")
    log.write(params_log + "\n=======================================\n")
    for i, chunk in enumerate(chunks):
        # Export only in case all chunks need to be exported or current chunk is the one to be expoted
        if export_chunk_nr == 0 or (export_chunk_nr != 0 and export_chunk_nr == i+1):
            log.write(chunks_metadata[i] + "\n")
            print("{0}_chunk.{1}".format(str(i+1).zfill(2), export_format))
            export_file = export_dir + "/{0}_chunk.{1}".format(str(i+1).zfill(2), export_format)
            if(export_codec == "mp3"):
                chunk.export(export_file, format=export_format, codec=export_codec, tags=export_tags, bitrate=export_bitrate)
            else:
                chunk.export(export_file, format=export_format, tags=export_tags)
    log.close

def export(target_dir, source, export_chunk_nr, default_export_format, export_tags, export_bitrate):
    export_format = input("Export Format (default: {0}): ".format(default_export_format)) or default_export_format
    if(export_format != "wav"):
        export_codec = input("Export Codec (default: mp3): ") or "mp3"
    else:
        export_codec = "wav"
    print("==============================================================================================================")
    export_chunks(target_dir + "/" + source + "/" + export_format, export_chunk_nr, export_format, export_codec, export_tags, export_bitrate)

def retry():
    retry = input('Process one more file? (default: Yes): ') or "Yes"
    if(retry in ("Yes", "Y", "Yeah", "y", "yes")):
        main()

def load_config(config_file):

    config = configparser.ConfigParser()

    if(not os.path.isfile(config_file)):
        print("Config file not found " + config_file)
        exit()

    config.read(config_file)

    # Get configs
    source_dir = config['path'].get('source_dir', 'source/')
    target_dir = config['path'].get('target_dir', 'chopped/')
    source_file = config['path'].get('source_file','nonexistingfile.wav')
    export_tags = {'artist': config['export'].get('tag_artist', 'Unknown Artist'), 'album': config['export'].get('tag_album', 'Unknown Album') }
    export_bitrate = config['export'].get('bitrate', "192k") or "192k"
    export_format = config['export'].get('format', 'wav')
    default_silence_threshold = config['sound'].get('silence_threshold', -41)
    default_chunk_min_length =  config['sound'].get('chunk_min_length', 60001)
    default_loudness_peak =  config['sound'].get('loudness_peak', 21)
    dafault_fade_in_out = config['sound'].get('fade_in_out', 2001)

    return source_dir, target_dir, source_file, export_tags, export_bitrate, export_format, default_silence_threshold, default_chunk_min_length, default_loudness_peak, dafault_fade_in_out


def main():
    global source
    global sound
    global params_log

    if(len(sys.argv) > 1):
        config_file = sys.argv[1] or 'default.ini'
    else:
        print("No config file provided as parameter, trying default.ini")
        config_file = 'default.ini'

    source_dir, target_dir, source_file, export_tags, export_bitrate, export_format, default_silence_threshold, default_chunk_min_length, default_loudness_peak, dafault_fade_in_out = load_config(config_file)
    do_export = True

    sourcefile = input('Source Filename (within ' + source_dir + ' folder)? ') or source_file or "nonexistingfile.wav"
    source_filename = source_dir + "/" + sourcefile

    if(os.path.isfile(source_filename)):
        print("==============================================================================================================")
        print("Processing file " + source_filename)
        source, source_file_extension = os.path.splitext(sourcefile)
        sound = AudioSegment.from_file(source_filename, format="wav")

        len_ss, len_mm, len_hh = convert_ms(len(sound))
        print("Length: {0}:{1}:{2}".format(str(len_hh).zfill(2), str(len_mm).zfill(2), str(len_ss).zfill(2)))
        print("Average Loudness: " + str(int(sound.dBFS)) + " dBFS")

        silence_threshold = input("Silence Threshold (default: {0} dBFS): ".format(default_silence_threshold)) or default_silence_threshold
        chunk_min_length = input("Minimal Chunk Length (default: {0} ms): ".format(default_chunk_min_length)) or default_chunk_min_length
        loudness_peak = input("Loudness Peak (default: {0} dBFS): ".format(default_loudness_peak)) or default_loudness_peak

        params_log = "Silence Threshold: " + str(silence_threshold) + "\nMinimal Chunk Length: " + str(chunk_min_length) + "\nLoudness Peak: " + str(loudness_peak)
        print("==============================================================================================================")
        print("Building Chunks")
        build_chunks(float(silence_threshold), float(chunk_min_length), float(loudness_peak))
        print("==============================================================================================================")
        if(len(chunks) > 0):
            do_export = (input('Export? (default: Yes): ') or "Yes") in ("Yes", "Y", "Yeah", "y", "yes")
            export_tags['album'] = export_tags['album'].format(source)
            while do_export:
                export_chunk_nr = int(input('Single Chunk (provide #, 0 for all)? (default: 0): ') or "0")
                export(target_dir, source, export_chunk_nr, export_format, export_tags, export_bitrate)
                print("==============================================================================================================")
                do_export = (input('Export again? (default: Yes): ') or "Yes") in ("Yes", "Y", "Yeah", "y", "yes")
            else:
                retry()
        else:
            print("No chunks found")
            retry()
    else:
        print("File not found " + source_filename)
        retry()

if __name__ == "__main__":
    main()
