mod audio_input;

use clap::Parser;

/// Converts podcast audio to video
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    /// input audio or video file (if a video file is provided, only the audio track will be used)
    audio: String,

    /// output video file
    #[arg(short, long)]
    output: Option<String>,

    /// the desired video frame rate in Hz
    #[arg(short, long, default_value_t = 30)]
    frame_rate: u16,

    /// video width in pixels
    #[arg(short, long, default_value_t = 1080)]
    width: u16,

    /// video height in pixels
    #[arg(short = 'y', long, default_value_t = 1080)]
    height: u16,
}

fn main() -> Result<(), audio_input::AudioTrackError> {
    let args = Args::parse();

    println!("Audio file: {}", args.audio);
    println!("Frame rate: {}", args.frame_rate);
    println!("Dimensions: {} x {}", args.width, args.height);
    println!(
        "Video will be written to: {}",
        args.output.unwrap_or("[none]".to_string())
    );

    let mut audio_track = audio_input::read_audio_track(args.audio)?;
    let samples = audio_input::decode_audio_track(&mut audio_track)?;

    println!("Number of samples decoded: {}", samples.samples.len());
    if let Some(sample_rate) = samples.sample_rate {
        println!("Sample rate: {} Hz", sample_rate);
    } else {
        println!("Sample rate unknown");
    }
    if let Some(channels) = samples.channels {
        println!("Number of channels: {}", channels.count());
    }
    Ok(())
}
