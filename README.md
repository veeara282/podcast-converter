# podcast-converter

This is a program that generates a visualizer video from a given audio file, such as
music or podcasts.

## Usage and examples

Once the virtual environment and dependencies are installed (see below), run the
following command:

```bash
python ./main.py ./examples/Wikipedia_Chanukah.flac -f 30 -o wikipedia_chanukah.mp4
```

- First positional argument: the input file (e.g. `./examples/Wikipedia_Chanukah.flac`).
  Can be any file format supported by FFmpeg.
- `-f`: the frame rate in frames per second (hertz). A frame rate that evenly divides
  the audio sample rate is recommended. Common frame rates include 24, 30 and 60 fps.
- `-o`: the output video file. Can be any file format supported by FFmpeg.

A few freely licensed music and podcast files are provided in the `examples/` folder.
You can also use your own audio as long as you own the copyright or have permission to
do so.

## Installation

To install the dependencies and run this program in a virtual environment, run the
following commands from the _root_ of the repository:

```bash
uv venv
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
uv sync
```

This program uses [TorchCodec](https://meta-pytorch.org/torchcodec/stable/index.html),
which requires FFmpeg shared libraries to work (`.dll` on Windows, `.so` on macOS/Linux).
`uv` won't install the FFmpeg libraries automatically, and not all FFmpeg distributions
come with them (e.g. the WinGet FFmpeg distribution).

Thus, you'll need to download an FFmpeg build from [here](https://github.com/BtbN/FFmpeg-Builds/releases)
matching the Python interpreter's architecture - for example, if the Python is x86, the FFmpeg
build should also be x86, even if your computer is emulating x86 programs on ARM.
Make sure to download one of the ZIP archives with `shared` in its name, e.g.
`ffmpeg-n8.1-latest-win64-gpl-shared-8.1.zip`.

The ZIP will contain the following file structure:
```
└── ffmpeg-n8.1-latest-win64-gpl-shared-8.1/
    ├── bin/
    │   ├── avcodec-62.dll
    │   ├── avdevice-62.dll
    │   │   ...
    │   ├── ffmpeg.exe
    │   ├── ffplay.exe
    │   │   ...
    │   └── swscale-9.dll
    ├── doc
    ├── include
    ├── lib
    ├── presets
    └── LICENSE.txt
```

Extract the top-level directory into a known location (e.g. `C:\ffmpeg\ffmpeg-n8.1-latest-win64-gpl-shared-8.1`
if on Windows) and add the `bin` directory to your PATH (e.g. `C:\ffmpeg\ffmpeg-n8.1-latest-win64-gpl-shared-8.1\bin`).
When you run the program on Windows, the `resolve_ffmpeg` will automatically detect any
directory with the substring `ffmpeg` in its name and look for DLLs that match the names
of the FFmpeg shared libraries. This is necessary because Python >3.8 doesn't check the
PATH for DLLs to load (see https://github.com/python/cpython/issues/80266 for more info).
On Unix-like operating systems, Python will find the FFmpeg `.so` shared libraries
automatically.
