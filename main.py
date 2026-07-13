import argparse
import logging

# Show info/debug logs (temporary)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def parse_args():
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Converts podcast audio to video",
        epilog="Happy podcasting!",
    )
    parser.add_argument(
        "audio",
        help="input audio or video file (if a video file is provided, only the audio track will be used)",
    )
    parser.add_argument("-b", "--bg-image", help="background image file")
    parser.add_argument("-o", "--output", help="output video file")
    parser.add_argument(
        "--vc",
        "--video-codec",
        help="video encoding to use for the output",
        choices=["h264", "hevc", "vp9", "av1"],
        default="av1",
    )
    parser.add_argument(
        "--ac",
        "--audio-codec",
        help="audio encoding to use for the output",
        choices=["aac", "opus"],
        default="opus",
    )
    parser.add_argument(
        "-f",
        "--frame-rate",
        help="the desired video frame rate in Hz. Default: 30",
        type=int,
        default=30,
    )
    return parser.parse_args()


def main():
    args = parse_args()
    audio_file_path = args.audio
    image_file_path = args.bg_image
    logger.info(f"Audio file: {audio_file_path or '[none]'}")
    logger.info(f"Image file: {image_file_path or '[none]'}")
    output_file_path = args.output
    logger.info(f"Video will be written to: {output_file_path}")

    # Lazy import: module has a lot of dependencies (PyTorch and FFmpeg DLLs), so only
    # import when needed to avoid blocking argparse
    logger.info("Loading dependencies...")
    import audio

    audio_samples = audio.read_audio(audio_file_path)
    spectrograms = audio.generate_spectrograms(
        audio_samples, frame_rate=args.frame_rate
    )
    assert spectrograms is not None


if __name__ == "__main__":
    main()
