import logging

import numpy as np
import skia
import torch
from torch import Tensor

logger = logging.getLogger()


def draw_background(surface: skia.Surface) -> None:
    with surface as canvas:
        paint_bg = skia.Paint(
            Color=skia.ColorBLUE,
            Style=skia.Paint.kFill_Style,
        )
        rect_bg = skia.Rect.MakeIWH(surface.width(), surface.height())
        canvas.drawRect(rect_bg, paint_bg)


def draw_frame(
    bar_heights: Tensor, t: int, width: int = 1080, height: int = 1080
) -> np.ndarray:
    surface = skia.Surface(width, height)
    # First draw the background
    draw_background(surface)

    # Then draw the visualizer bars
    with surface as canvas:
        paint = skia.Paint(
            Alphaf=0.6,
            AntiAlias=True,
            Color=skia.ColorWHITE,
            Style=skia.Paint.kFill_Style,
        )
        n_mels = bar_heights.size(1)
        bar_width = 12
        gap_width = 4
        leftmost = 27
        for i in range(n_mels):
            bar_height = bar_heights[0, i, t]
            x_left = leftmost + i * (bar_width + gap_width)
            x_right = x_left + bar_width
            y_bottom = 900
            y_top = y_bottom - bar_height
            rect = skia.Rect.MakeLTRB(x_left, y_top, x_right, y_bottom)
            canvas.drawRect(rect, paint)

    return surface.makeImageSnapshot().toarray()


def spectrograms_to_bar_heights(spectrograms: Tensor, max_height=720) -> Tensor:
    # No need to clip the dynamic range - AmplitudeToDB already clips it to [-100, 0] dB
    # Normalize the dynamic range [db_min, db_max] -> [0, 1].
    # Important because db_max can go above 0 dB.
    db_min, db_max = torch.aminmax(spectrograms)
    logger.info(f"Audio min/max dB: {db_min:.3f}, {db_max:.3f}")
    db_range = db_max - db_min
    normalized = (spectrograms - db_max) / db_range + 1
    # norm_min, norm_max = torch.aminmax(normalized)
    # logger.debug(f"Normalized min/max dB: {norm_min:.3f}, {norm_max:.3f}")
    return normalized * max_height


def draw_frames(spectrograms: Tensor, width: int = 1080, height: int = 1080):
    bar_heights = spectrograms_to_bar_heights(spectrograms)
    # Use a generator to draw frames so we can stream them to the video encoder.
    n_frames = spectrograms.size(2)
    for t in range(n_frames):
        logger.debug(f"Drawing frame {t} of {n_frames}...")
        yield draw_frame(bar_heights, t, width, height)
