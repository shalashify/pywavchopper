# pywavchopper
# Usage: python3 pywavchopper.py myconfig.ini

import sys
import configparser
import os
from pydub import AudioSegment

# Initialize global vars
_chunks = []
_chunks_metadata = []
_sound = None
_source = None


def _convert_ms(_ms):
    _ss = int((_ms / 1000) % 60)
    _mm = int((_ms / (1000 * 60)) % 60)
    _hh = int((_ms / (1000 * 60 * 60)) % 24)
    return _ss, _mm, _hh


def _build_chunks(_silence_threshold=-40  # Everything below is considered silence
                 , _chunk_min_length=60000  # 1 Min, Minimal length of chunk that is considered for export
                 , _loudness_peak=20  # Change in loudness in dBFS that would mean start/end of a chunk
                 , _fadeinout=2000  # 2 Sec, time to add at the beginning and end of chunk
                 ):
    global _chunks
    global _chunks_metadata
    _chunks = []
    _chunks_metadata = []
    _analysis_step = 1000  # 2 Sec, in which steps to analyse source audio
    _prev_step_loudness = -100
    _curr_step_loudness = -100
    _chunk_start = 0
    _chunk_end = 0
    _z = 0

    # Move through source sound, measure loudness of every step and compare it
    # to the previous one
    for _i, _step in enumerate(_sound[::_analysis_step]):
        _prev_step_loudness = _curr_step_loudness
        _curr_step_loudness = _step.dBFS

        # Consider everything that is quiter then threshold as silent
        if(_curr_step_loudness < _silence_threshold):
            _curr_step_loudness = -100

        # Consider changes in loudness that are are higher than loudness_peak
        # as start/end events
        if(abs(abs(_curr_step_loudness) - abs(_prev_step_loudness)) > _loudness_peak):
            if(_prev_step_loudness < _curr_step_loudness):
                _chunk_start = int(_i * _analysis_step)
            else:
                _chunk_end = int(_i * _analysis_step)

            # If current chunk is longer that defined minimal length then
            # consider it
            if(_chunk_end > _chunk_start and _chunk_end - _chunk_start > _chunk_min_length):
                # Check that start / end position considering fade in / fade
                # out do not exceed file length
                _start_pos = (
                    _chunk_start -
                    _fadeinout) if (
                    _chunk_start -
                    _fadeinout >= 0) else _chunk_start
                _end_pos = (
                    _chunk_end +
                    _fadeinout) if (
                    _chunk_start +
                    _fadeinout < len(_sound)) else _chunk_end
                _chunks.append(_sound[_start_pos:_end_pos])
                # Gather some metadata, just for display
                _start_pos_ss, _start_pos_mm, _start_pos_hh = _convert_ms(
                    _chunk_start)
                _end_pos_ss, _end_pos_mm, _end_pos_hh = _convert_ms(_chunk_end)
                _duration_ss, _duration_mm, _duration_hh = _convert_ms( _chunk_end - _chunk_start)
                _chunks_metadata.append(
                    "{0}_chunk".format(
                        str(_z + 1).zfill(2)) + ": " + "{0}:{1}:{2}-{3}:{4}:{5} ({6}:{7})".format(
                        str(_start_pos_hh).zfill(2),
                        str(_start_pos_mm).zfill(2),
                        str(_start_pos_ss).zfill(2),
                        str(_end_pos_hh).zfill(2),
                        str(_end_pos_mm).zfill(2),
                        str(_end_pos_ss).zfill(2),
                        str(_duration_mm).zfill(2),
                        str(_duration_ss).zfill(2)))
                print(_chunks_metadata[_z])
                _z += 1


def _export_chunks(
        _export_dir,
        _export_chunk_nr=0,
        _export_format="mp3",
        _export_codec="mp3",
        _export_tags={},
        _export_bitrate="256k"):
    global _source
    global _params_log

    print("Exporting to " + _export_dir + "/")
    if not os.path.exists(_export_dir):
        os.makedirs(_export_dir)
    _log = open(_export_dir + "/chop.log", "w")
    _log.write("Chopping Source File " + _source +
              "\n=======================================\n")
    _log.write(_params_log + "\n=======================================\n")
    for _i, _chunk in enumerate(_chunks):
        # Export only in case all chunks need to be exported or current chunk
        # is the one to be expoted
        if _export_chunk_nr == 0 or (_export_chunk_nr != 0 and _export_chunk_nr == _i + 1):
            _log.write(_chunks_metadata[_i] + "\n")
            print("{0}_chunk.{1}".format(str(_i + 1).zfill(2), _export_format))
            _export_file = _export_dir + \
                "/{0}_chunk.{1}".format(str(_i + 1).zfill(2), _export_format)
            if(_export_codec == "mp3"):
                _chunk.export(
                    _export_file,
                    format=_export_format,
                    codec=_export_codec,
                    tags=_export_tags,
                    bitrate=_export_bitrate)
            else:
                _chunk.export(
                    _export_file,
                    format=_export_format,
                    tags=_export_tags)
    _log.close


def _export(
        _target_dir,
        _source,
        _export_chunk_nr,
        _default_export_format,
        _export_tags,
        _export_bitrate):
    _export_format = input("Export Format (default: {0}): ".format(
        _default_export_format)) or _default_export_format
    if(_export_format != "wav"):
        _export_codec = input("Export Codec (default: mp3): ") or "mp3"
    else:
        _export_codec = "wav"
    print("==============================================================================================================")
    _export_chunks(
        _target_dir +
        "/" +
        _source +
        "/" +
        _export_format,
        _export_chunk_nr,
        _export_format,
        _export_codec,
        _export_tags,
        _export_bitrate)


def _retry():
    _retry = input('Process one more file? (default: Yes): ') or "Yes"
    if(_retry in ("Yes", "Y", "Yeah", "y", "yes")):
        _main()


def _load_config(_config_file):

    _config = configparser.ConfigParser()

    if(not os.path.isfile(_config_file)):
        print("Config file not found " + _config_file)
        exit()

    _config.read(_config_file)

    # Get configs
    _source_dir = _config['path'].get('source_dir', 'source/')
    _target_dir = _config['path'].get('target_dir', 'chopped/')
    _source_file = _config['path'].get('source_file', 'nonexistingfile.wav')
    _export_tags = {
        'artist': _config['export'].get(
            'tag_artist',
            'Unknown Artist'),
        'album': _config['export'].get(
            'tag_album',
            'Unknown Album')}
    _export_bitrate = _config['export'].get('bitrate', "192k") or "192k"
    _export_format = _config['export'].get('format', 'wav')
    _default_silence_threshold = _config['sound'].get('silence_threshold', -41)
    _default_chunk_min_length = _config['sound'].get('chunk_min_length', 60001)
    _default_loudness_peak = _config['sound'].get('loudness_peak', 21)
    _dafault_fade_in_out = _config['sound'].get('fade_in_out', 2001)

    return _source_dir, _target_dir, _source_file, _export_tags, _export_bitrate, _export_format, _default_silence_threshold, _default_chunk_min_length, _default_loudness_peak, _dafault_fade_in_out


def _hello():
    #http://patorjk.com/software/taag/#p=display&f=Small%20Slant&t=pywavchopper
    _hello = """

                                   __
   ___  __ ___    _____ __  ______/ /  ___  ___  ___  ___ ____
  / _ \/ // / |/|/ / _ `/ |/ / __/ _ \/ _ \/ _ \/ _ \/ -_) __/
 / .__/\_, /|__,__/\_,_/|___/\__/_//_/\___/ .__/ .__/\__/_/
/_/   /___/                              /_/  /_/


    """
    print(_hello)


def _main():
    global _source
    global _sound
    global _params_log
    try:
        if(len(sys.argv) > 1):
            _config_file = sys.argv[1] or 'default.ini'
        else:
            print("No config file provided as parameter, trying default.ini")
            _config_file = 'default.ini'

        _source_dir, _target_dir, _source_file, _export_tags, _export_bitrate, _export_format, _default_silence_threshold, _default_chunk_min_length, _default_loudness_peak, _dafault_fade_in_out = _load_config(_config_file)
        _do_export = True

        _sourcefile = input('Source Filename (within ' + _source_dir + ' folder)? ') or _source_file or "nonexistingfile.wav"
        _source_filename = _source_dir + "/" + _sourcefile

        if(os.path.isfile(_source_filename)):
            print("==============================================================================================================")
            print("Analyzing File " + _source_filename)
            _source, _source_file_extension = os.path.splitext(_sourcefile)
            _sound = AudioSegment.from_file(_source_filename, format="wav")

            _len_ss, _len_mm, _len_hh = _convert_ms(len(_sound))
            print(
                "Length: {0}:{1}:{2}".format(
                    str(_len_hh).zfill(2),
                    str(_len_mm).zfill(2),
                    str(_len_ss).zfill(2)))
            print("Average Loudness: " + str(int(_sound.dBFS)) + " dBFS")

            _silence_threshold = input("Silence Threshold (default: {0} dBFS): ".format(
                _default_silence_threshold)) or _default_silence_threshold

            _chunk_min_length = input("Minimal Chunk Length (default: {0} ms): ".format(
                _default_chunk_min_length)) or _default_chunk_min_length

            _loudness_peak = input("Loudness Peak (default: {0} dBFS): ".format(
                _default_loudness_peak)) or _default_loudness_peak

            _params_log = "Silence Threshold: " + str(_silence_threshold) + "\nMinimal Chunk Length: " + str(
                _chunk_min_length) + "\nLoudness Peak: " + str(_loudness_peak)

            print("==============================================================================================================")
            print("Building Chunks")
            _build_chunks(
                float(_silence_threshold),
                float(_chunk_min_length),
                float(_loudness_peak))
            print("==============================================================================================================")
            if(len(_chunks) > 0):
                _do_export = (input('Export? (default: Yes): ') or "Yes") in ("Yes", "Y", "Yeah", "y", "yes")
                _export_tags['album'] = _export_tags['album'].format(_source)
                while _do_export:
                    _export_chunk_nr = int(input('Single Chunk (provide #, 0 for all)? (default: 0): ') or "0")
                    _export(
                        _target_dir,
                        _source,
                        _export_chunk_nr,
                        _export_format,
                        _export_tags,
                        _export_bitrate)
                    print("==============================================================================================================")
                    _do_export = (input('Export again? (default: Yes): ') or "Yes") in ("Yes", "Y", "Yeah", "y", "yes")
                else:
                    _retry()
            else:
                print("No chunks found")
                _retry()
        else:
            print("File not found " + _source_filename)
            _retry()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    _hello()
    _main()
