import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Converts podcast audio to video",
    )
    parser.add_argument("--audio", help="input audio or video file")
    parser.add_argument
    parser.add_argument("-o", "--output", help="output video file")
    return parser.parse_args()


def main():
    pass


if __name__ == "__main__":
    main()
