use mel_spec::mel::BatchLogMelError;
use mel_spec::mel::downmix_interleaved;
pub use mel_spec::wgpu::{WgpuError, WgpuMelSpectrogram};

use crate::audio_input::DecodedAudio;

#[derive(Debug, thiserror::Error)]
pub enum DspError {
    #[error(transparent)]
    BatchLogMel(#[from] BatchLogMelError),
    #[error(transparent)]
    Wgpu(#[from] WgpuError),
}

/// Initializes a `WgpuMelSpectrogram` struct based on the parameters provided.
///
/// Arguments:
///
/// * `audio` - a `&DecodedAudio` struct with the audio to be processed.
///   `audio.sample_rate()` is passed to the `WgpuMelSpectrogram` constructor.
/// * `frame_rate`: the desired frame rate of the video to be generated. It is
///   recommended that the audio sample rate be evenly divisible by the frame rate.
/// * `window_length`: the window length in seconds for the short-time Fourier transform
///   (STFT) used to generate the spectrograms.
/// * `n_bins`: the number of spectrogram bins to be generated. This corresponds to the
///   number of bars in the visualizer.
pub fn mel_spectrogram_wgpu(
    audio: &DecodedAudio,
    frame_rate: u32,
    window_length: f32,
    n_bins: u32,
) -> Result<WgpuMelSpectrogram, DspError> {
    let sample_rate = audio.sample_rate();

    if sample_rate % frame_rate != 0 {
        println!(
            "Sample rate ({} Hz) is not evenly divisible by frame rate ({} Hz). Video output may be misaligned with audio.",
            sample_rate, frame_rate,
        )
    }

    // Compute hop length from desired frame rate
    let hop_size = (sample_rate / frame_rate) as usize;

    // Compute window length in samples from function param (window length in seconds)
    let window_length_samples = ((sample_rate as f32) * window_length).round() as usize;

    WgpuMelSpectrogram::new(
        window_length_samples,
        hop_size,
        sample_rate as f64,
        n_bins as usize,
    )
    .map_err(|e| DspError::Wgpu(e))
}

pub fn generate_spectrograms(
    audio: &DecodedAudio,
    frame_rate: u32,
    window_length: f32,
    n_bins: u32,
) -> Result<Vec<Vec<f32>>, DspError> {
    // Mix audio to mono - this won't work otherwise
    println!("Converting audio to mono for spectral analysis...");
    let audio_mono = downmix_interleaved(&audio.samples, audio.channel_count())?;

    let wgpu_mel_spec = mel_spectrogram_wgpu(audio, frame_rate, window_length, n_bins)?;

    println!("Generating spectrograms...");
    wgpu_mel_spec
        .compute_mel_spectrogram(&audio_mono)
        .map_err(|e| DspError::Wgpu(e))
}
