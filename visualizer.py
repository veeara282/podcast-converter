import logging

import numpy as np
import skia
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


def draw_frame(spectrograms: Tensor, t: int) -> np.ndarray:
    surface = skia.Surface(1080, 1080)
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
        n_mels = spectrograms.size(1)
        bar_width = 12
        gap_width = 4
        leftmost = 27
        for i in range(n_mels):
            db = spectrograms[0, i, t]
            bar_height = max(0, db + 80) * 8
            x_left = leftmost + i * (bar_width + gap_width)
            x_right = x_left + bar_width
            y_bottom = 960
            y_top = y_bottom - bar_height
            rect = skia.Rect.MakeLTRB(x_left, y_top, x_right, y_bottom)
            canvas.drawRect(rect, paint)

    return surface.makeImageSnapshot().toarray()


def draw_frames(spectrograms: Tensor):
    # Use a generator to draw frames so we can stream them to the video encoder.
    n_frames = spectrograms.size(2)
    for t in range(n_frames):
        logger.debug(f"Drawing frame {t} of {n_frames}...")
        yield draw_frame(spectrograms, t)
