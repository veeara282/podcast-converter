mod audio_dsp;
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

#[derive(Debug, thiserror::Error)]
enum ProgramError {
    #[error(transparent)]
    AudioTrackError(#[from] audio_input::AudioTrackError),
    #[error(transparent)]
    WgpuError(#[from] audio_dsp::WgpuError),
}

fn main() -> Result<(), ProgramError> {
    let args = Args::parse();

    println!("Audio file: {}", args.audio);
    println!("Frame rate: {}", args.frame_rate);
    println!("Dimensions: {} x {}", args.width, args.height);
    println!(
        "Video will be written to: {}",
        args.output.unwrap_or("[none]".to_string())
    );

    let mut audio_track = audio_input::read_audio_track(args.audio)?;
    let samples = audio_input::decode_audio_track(&mut audio_track, false)?;

    println!("Sample rate: {} Hz", samples.sample_rate());
    println!("Number of channels: {}", samples.channel_count());

    let num_samples = samples.samples.len();

    if samples.pre_mixed {
        println!("Number of samples decoded: {} (pre-mixed)", num_samples);
        println!(
            "Original number of samples: {}",
            num_samples * samples.channel_count()
        );
    } else {
        println!("Number of samples decoded: {}", num_samples);
    }

    let _mel_spec = audio_dsp::mel_spectrogram_wgpu(&samples, args.frame_rate as u32, 0.25, 64)?;

    Ok(())
}
