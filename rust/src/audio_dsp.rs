pub use mel_spec::wgpu::{WgpuError, WgpuMelSpectrogram};

use crate::audio_input::DecodedAudio;

pub fn mel_spectrogram_wgpu(
    audio: &DecodedAudio,
    frame_rate: u32,
    window_length: f32,
    n_bins: u32,
) -> Result<WgpuMelSpectrogram, WgpuError> {
    // Compute hop length from desired frame rate
    let hop_size = (audio.sample_rate() / frame_rate) as usize;

    // Compute window length in samples from function param (window length in seconds)
    let window_length_samples = ((audio.sample_rate() as f32) * window_length).round() as usize;

    WgpuMelSpectrogram::new(
        window_length_samples,
        hop_size,
        audio.sample_rate() as f64,
        n_bins as usize,
    )
}
