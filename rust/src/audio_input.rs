use std::path::Path;
use symphonia::core::codecs::CodecParameters;
use symphonia::core::codecs::audio::AudioDecoderOptions;
use symphonia::core::formats::probe::Hint;
use symphonia::core::formats::{FormatOptions, FormatReader, TrackType};
use symphonia::core::io::MediaSourceStream;
use symphonia::core::meta::MetadataOptions;

pub struct AudioTrack {
    pub format: Box<dyn FormatReader>,
    pub track_id: u32,
}

#[derive(Debug, Clone)]
pub struct DecodedAudio {
    pub sample_rate: Option<u32>,
    pub channels: Option<symphonia::core::audio::Channels>,
    pub samples: Vec<f32>,
    // true if the track was mixed to mono during decoding
    pub pre_mixed: bool,
}

/// Mixes interleaved samples to mono by averaging every audio frame.
pub fn mix_samples_to_mono(
    samples: &[f32],
    channels: Option<&symphonia::core::audio::Channels>,
) -> Vec<f32> {
    let channel_count = channels.map_or(1, |channels| channels.count());

    if channel_count <= 1 {
        return samples.to_vec();
    }

    let frame_count = samples.len() / channel_count;
    let scale = 1.0 / channel_count as f32;
    let mut mono_samples = Vec::with_capacity(frame_count);

    for frame in samples.chunks_exact(channel_count) {
        mono_samples.push(frame.iter().sum::<f32>() * scale);
    }

    mono_samples
}

#[derive(Debug, thiserror::Error)]
pub enum AudioTrackError {
    #[error("failed to open input file: {0}")]
    Io(#[from] std::io::Error),
    #[error("no decodable audio track found in file")]
    NoAudioTrack,
    #[error(transparent)]
    Symphonia(#[from] symphonia::core::errors::Error),
}

/// Reads the audio track in the file specified by `path` without decoding it.
/// If `path` represents a video file, only the audio track is used.
pub fn read_audio_track(path: impl AsRef<Path>) -> Result<AudioTrack, AudioTrackError> {
    let src = std::fs::File::open(path).map_err(AudioTrackError::Io)?;
    let mss = MediaSourceStream::new(Box::new(src), Default::default());

    let format: Box<dyn FormatReader> = symphonia::default::get_probe().probe(
        &Hint::new(),
        mss,
        FormatOptions::default(),
        MetadataOptions::default(),
    )?;

    let track_id: u32 = format
        .default_track(TrackType::Audio)
        .ok_or(AudioTrackError::NoAudioTrack)?
        .id;

    Ok(AudioTrack { format, track_id })
}

/// Decodes the audio track identified by the struct `audio_track` and returns a single
/// interleaved audio stream.
pub fn decode_audio_track(
    audio_track: &mut AudioTrack,
    mix_to_mono: bool,
) -> Result<DecodedAudio, AudioTrackError> {
    let track_id = audio_track.track_id;

    let codec_params = audio_track
        .format
        .tracks()
        .iter()
        .find(|t| t.id == track_id)
        .and_then(|t| t.codec_params.as_ref())
        .and_then(|cp| match cp {
            CodecParameters::Audio(audio) => Some(audio.clone()),
            _ => None,
        })
        .ok_or(AudioTrackError::NoAudioTrack)?;

    let sample_rate = codec_params.sample_rate;
    let channels = codec_params.channels.clone();

    let mut decoder = symphonia::default::get_codecs()
        .make_audio_decoder(&codec_params, &AudioDecoderOptions::default())?;

    let mut combined_samples: Vec<f32> = Vec::new();

    while let Some(packet) = audio_track.format.next_packet()? {
        if packet.track_id != track_id {
            continue;
        }

        let decoded = decoder.decode(&packet)?;
        let mut packet_samples: Vec<f32> = Vec::new();
        decoded.copy_to_vec_interleaved(&mut packet_samples);

        if mix_to_mono {
            packet_samples = mix_samples_to_mono(&packet_samples, channels.as_ref());
        }

        combined_samples.extend(packet_samples);
    }

    Ok(DecodedAudio {
        sample_rate,
        channels,
        samples: combined_samples,
        pre_mixed: mix_to_mono,
    })
}
