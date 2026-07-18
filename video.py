import logging
import time
from typing import Generator

# Import this to resolve FFmpeg DLLs, since Python on Windows does not load DLLs
# automatically. Must come before the torchcodec import.
import resolve_ffmpeg

resolve_ffmpeg.add_dll_paths()

import numpy as np
import torch
from torchcodec import AudioSamples
from torchcodec.encoders import Encoder
from tqdm import tqdm

logger = logging.getLogger()


def np_to_torchcodec_format(frame: np.ndarray) -> torch.Tensor:
    """Converts an image exported from Skia into the format expected by the torchcodec Encoder.

    Parameters:
    frame: an np.ndarray of size (w, h, c)

    Returns: a torch.Tensor of size (1, c, w, h)
    """
    # Transpose (w, h, c) -> (c, w, h), then add new dimension
    # Also drop alpha channel (comes first)
    reshaped = np.transpose(frame, (2, 0, 1))[np.newaxis, 1:4, ...]
    return torch.from_numpy(reshaped)


def export_video(
    dest: str,
    audio: AudioSamples,
    video_frames: Generator[np.ndarray],
    frame_rate: int = 30,
    n_frames: int = 1000,
    width: int = 1080,
    height: int = 1080,
):
    encoder = Encoder()
    video_stream = encoder.add_video(width=width, height=height, frame_rate=frame_rate)
    audio_stream = encoder.add_audio(
        sample_rate=audio.sample_rate,
        num_channels=audio.data.size(0),
        # If WebM file type is selected, FFmpeg will use the Opus audio codec.
        # Since Opus requires specific sample rates (48000, 24000, etc.), input audio
        # with an arbitrary sample rate (e.g. 44100 Hz) must be upsampled to 48000 Hz.
        # TorchCodec throws a RuntimeError instead of doing this automatically.
        out_sample_rate=48000 if dest.endswith(".webm") else None,
    )
    with encoder.open_file(dest):
        audio_stream.add_samples(audio.data)
        for frame in tqdm(video_frames, desc="Drawing frames", total=n_frames):
            logger.debug(
                f"Generated frame: ndarray of shape={frame.shape}, dtype={frame.dtype}"
            )
            t0 = time.perf_counter()
            tensor_frame = np_to_torchcodec_format(frame)
            logger.debug(f"convert: {time.perf_counter()-t0:.4f}s")
            t0 = time.perf_counter()
            video_stream.add_frames(tensor_frame)
            logger.debug(f"encode: {time.perf_counter()-t0:.4f}s")
        logger.info("Loop finished, awaiting generator cleanup...")
    logger.info("encoder.open_file() context exited, muxing complete.")
