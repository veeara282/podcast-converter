use clap::Parser;

/// Converts podcast audio to video
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    /// input audio or video file (if a video file is provided, only the audio track will be used)
    audio: String,

    /// output video file
    #[arg(short, long)]
    output: String,

    /// the desired video frame rate in Hz
    #[arg(short, long, default_value_t = 30)]
    frame_rate: u16,

    /// video width in pixels
    #[arg(short, long, default_value_t = 1080)]
    width: u16,

    /// video height in pixels
    #[arg(short='y', long, default_value_t = 1080)]
    height: u16,
}

fn main() {
    let args = Args::parse();

    println!("Audio file: {}", args.audio);
    println!("Frame rate: {}", args.frame_rate);
    println!("Dimensions: {} x {}", args.width, args.height);
    println!("Video will be written to: {}", args.output);
}
