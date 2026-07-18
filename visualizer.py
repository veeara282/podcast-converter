import contextlib
import logging
import sys

import glfw
import numpy as np
import skia
import torch
from torch import Tensor

logger = logging.getLogger()

"""
Code adapted from https://skia-python.github.io/skia-python/tutorial/canvas.html#gpu

skia-python docs: Copyright (c) 2020, Kota Yamaguchi
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


@contextlib.contextmanager
def glfw_context(width: int = 1080, height: int = 1080):
    if not glfw.init():
        raise RuntimeError("glfw.init() failed")
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
    glfw.window_hint(glfw.STENCIL_BITS, 8)
    # see https://www.glfw.org/faq#macos
    if sys.platform.startswith("darwin"):
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    window = glfw.create_window(width, height, "", None, None)
    glfw.make_context_current(window)
    yield window
    logger.info("glfw_context: about to call glfw.terminate()...")
    glfw.terminate()
    logger.info("glfw_context: glfw.terminate() returned.")

def draw_background(surface: skia.Surface) -> None:
    with surface as canvas:
        paint_bg = skia.Paint(
            Color=skia.ColorBLUE,
            Style=skia.Paint.kFill_Style,
        )
        rect_bg = skia.Rect.MakeIWH(surface.width(), surface.height())
        canvas.drawRect(rect_bg, paint_bg)


def draw_frame(
    bar_heights: Tensor,
    t: int,
    width: int = 1080,
    height: int = 1080,
    surface: skia.Surface = None,
) -> np.ndarray:
    # The calling function may pass in a Surface for GPU rendering. If it does not, we
    # create a Surface on the CPU.
    if surface is None:
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
    with glfw_context():
        # Create an OpenGL surface and reuse it to draw each frame
        context = skia.GrDirectContext.MakeGL()
        info = skia.ImageInfo.MakeN32Premul(width, height)
        surface = skia.Surface.MakeRenderTarget(context, skia.Budgeted.kYes, info)
        if surface is None:
            logger.warning("Failed to create OpenGL rendering surface. Falling back to CPU rendering.")
        for t in range(n_frames):
            logger.debug(f"Drawing frame {t} of {n_frames}...")
            frame = draw_frame(bar_heights, t, width=width, height=height, surface=surface)
            context.flushAndSubmit()
            glfw.poll_events()
            yield frame
        # Release Skia's GPU-backed objects now, while the GL context is still
        # current — glfw.terminate() (below, on with-exit) invalidates the context,
        # and Skia's destructors need a live context to release GPU resources cleanly.
        del surface
        del context
    # glfw.terminate() runs here, with no dangling GPU objects left to clean up
