import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Converts podcast audio to video",
        epilog="Happy podcasting!",
    )
    parser.add_argument("--audio", help="input audio or video file (if a video file is provided, only the audio track will be used)")
    parser.add_argument("--bg", help="background image file")
    parser.add_argument("-o", "--output", help="output video file")
    parser.add_argument("--vc", "--video-codec",
                        help="video encoding to use for the output",
                        choices=["h264", "av1"],
                        default="av1")
    parser.add_argument("--ac", "--audio-codec",
                        help="audio encoding to use for the output",
                        choices=["aac", "opus"],
                        default="opus")
    return parser.parse_args()


def main():
    args = parse_args()


if __name__ == "__main__":
    main()
