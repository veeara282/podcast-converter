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
        logger.info(f"Reading audio from source: {source}")
        decoder = AudioDecoder(source)
        audio = decoder.get_all_samples()
        logger.info(f"Duration: {audio.duration_seconds} seconds")
        logger.info(f"Sample rate: {audio.sample_rate} Hz")
        num_channels = audio.data.size(0)
        if num_channels == 1:
            logger.info("Mono audio detected (number of channels: 1)")
        elif num_channels == 2:
            logger.info("Stereo audio detected (number of channels: 2)")
        else:
            logger.info(f"Number of channels: {audio.data.size(0)}")
        return audio
    else:
        raise FileNotFoundError(source)


def spectrogram_pipeline(
    audio: AudioSamples,
    frame_rate: int = 30,
    window_length: float = 0.25,
    n_bins: int = 64,
) -> nn.Module:
    """
    Returns a nn.Sequential that converts the input audio data into a series of spectrograms
    binned by perceptual pitch (see MelSpectrogram).

    Parameters:
    audio (torchcodec.AudioSamples): an AudioSamples object
    frame_rate (int): the desired frame rate of the video to be generated. It is recommended that the audio sample rate be evenly divisible by the frame rate.
    window_length (float): the window length in seconds for the short-time Fourier transform used to generate the spectrograms.
    n_bins (int): the number of spectrogram bins to be generated. This corresponds to the number of bars in the visualizer.
    """

    # Compute hop length from desired frame rate
    hop_length = audio.sample_rate // frame_rate
    if audio.sample_rate % frame_rate != 0:
        logger.warning(
            f"Sample rate ({audio.sample_rate} Hz) is not evenly divisible by frame rate ({frame_rate} Hz). Video output may be misaligned with audio."
        )

    # Compute window length in samples from function param (window length in seconds)
    window_length_samples = round(audio.sample_rate * window_length)

    return nn.Sequential(
        # Convert to mel scale (perceptual frequency bins)
        tfs.MelSpectrogram(
            sample_rate=audio.sample_rate,
            n_fft=window_length_samples,  # same as win_length
            hop_length=hop_length,
            n_mels=n_bins,
        ),
        tfs.AmplitudeToDB(),
    )


def generate_spectrograms(
    audio: AudioSamples,
    frame_rate: int = 30,
    window_length: float = 0.25,
    n_bins: int = 64,
    merge_channels=True,
) -> torch.Tensor:
    if merge_channels:
        # If true, convert multi-channel audio to mono.
        # The shape of the input tensor is (num_channels, num_samples), so we average
        # along the first dimension.
        audio_data = torch.mean(audio.data, dim=0, keepdim=True)
    else:
        # Otherwise keep input data as-is
        audio_data = audio.data

    logger.info("Generating spectrograms...")
    pipeline = spectrogram_pipeline(audio, frame_rate, window_length, n_bins)
    return pipeline.forward(audio_data)
