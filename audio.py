import logging
import os

# Import this to resolve FFmpeg DLLs, since Python on Windows does not load DLLs
# automatically. Must come before the torchcodec import.
import resolve_ffmpeg

resolve_ffmpeg.add_dll_paths()

import torch
from torch import nn
from torchaudio import transforms as tfs
from torchcodec import AudioSamples
from torchcodec.decoders import AudioDecoder

logger = logging.getLogger()


def read_audio(source: str) -> AudioSamples:
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


def spectrogram_pipeline(audio: AudioSamples, frame_rate: int = 30) -> nn.Module:
    hop_length = audio.sample_rate // frame_rate
    if audio.sample_rate % frame_rate != 0:
        logger.warning(
            f"Sample rate ({audio.sample_rate} Hz) is not evenly divisible by frame rate ({frame_rate} Hz). Video output may be misaligned with audio."
        )
    return nn.Sequential(
        # Convert to mel scale (perceptual frequency bins)
        tfs.MelSpectrogram(
            sample_rate=audio.sample_rate, n_fft=hop_length * 4, hop_length=hop_length
        ),
        tfs.AmplitudeToDB(),
    )


def generate_spectrograms(
    audio: AudioSamples, frame_rate: int = 30, merge_channels=True
) -> torch.Tensor:
    if merge_channels:
        # If true, convert multi-channel audio to mono
        audio_data = torch.mean(audio.data, dim=0)
    else:
        # Otherwise keep input data as-is
        audio_data = audio.data

    pipeline = spectrogram_pipeline(audio, frame_rate)
    return pipeline.forward(audio_data)
