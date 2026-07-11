import os

# Import this to resolve FFmpeg DLLs, since Python on Windows does not load DLLs
# automatically. Must come before the torchcodec import.
import resolve_ffmpeg

resolve_ffmpeg.add_dll_paths()

from torch import nn
from torchaudio import transforms as tfs
from torchcodec.decoders import AudioDecoder

# pipeline = nn.Sequential(
#     # Convert to mel scale (perceptual frequency bins)
#     tfs.MelSpectrogram(8192),
#     tfs.AmplitudeToDB(),
# )


def read_audio(source):
    if os.path.exists(source):
        print(f"Reading audio from source: {source}")
        decoder = AudioDecoder(source)
        audio = decoder.get_all_samples()
        print(f"Duration: {audio.duration_seconds} seconds")
        print(f"Sample rate: {audio.sample_rate} Hz")
        num_channels = audio.data.size(0)
        if num_channels == 1:
            print("Mono audio detected (number of channels: 1)")
        elif num_channels == 2:
            print("Stereo audio detected (number of channels: 2)")
        else:
            print(f"Number of channels: {audio.data.size(0)}")
        return audio
    else:
        raise FileNotFoundError(source)
