use std::path::Path;
use symphonia::core::audio::AudioSpec;
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
    pub samples: Vec<f32>,
    pub audio_spec: AudioSpec,
}

impl DecodedAudio {
    pub fn sample_rate(&self) -> u32 {
        self.audio_spec.rate()
    }

    pub fn channel_count(&self) -> usize {
        self.audio_spec.channels().count()
    }
}

#[derive(Debug, thiserror::Error)]
pub enum AudioTrackError {
    #[error("failed to open input file: {0}")]
    Io(#[from] std::io::Error),
    #[error("no decodable audio track found in file")]
    NoAudioTrack,
    #[error(transparent)]
    Symphonia(#[from] symphonia::core::errors::Error),
    #[error("audio spec is inconsistent between frames in this track")]
    AudioSpecChanged,
    #[error("empty audio track")]
    EmptyAudioTrack,
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
pub fn decode_audio_track(audio_track: &mut AudioTrack) -> Result<DecodedAudio, AudioTrackError> {
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

    let mut decoder = symphonia::default::get_codecs()
        .make_audio_decoder(&codec_params, &AudioDecoderOptions::default())?;

    let mut combined_samples: Vec<f32> = Vec::new();

    let mut maybe_audio_spec: Option<AudioSpec> = None;

    while let Some(packet) = audio_track.format.next_packet()? {
        if packet.track_id != track_id {
            continue;
        }

        let decoded = decoder.decode(&packet)?;

        let cur_spec: &AudioSpec = decoded.spec();

        // decoded.spec() shouldn't change between frames in the same file, but handle it
        // in case it does
        match &maybe_audio_spec {
            Some(prev_spec) if prev_spec != cur_spec => {
                return Err(AudioTrackError::AudioSpecChanged);
            }
            None => maybe_audio_spec = Some(cur_spec.clone()), // clone happens exactly once
            _ => {}
        }

        let mut packet_samples: Vec<f32> = Vec::new();
        decoded.copy_to_vec_interleaved(&mut packet_samples);

        combined_samples.extend(packet_samples);
    }

    match maybe_audio_spec {
        Some(spec) => Ok(DecodedAudio {
            samples: combined_samples,
            audio_spec: spec,
        }),
        None => Err(AudioTrackError::EmptyAudioTrack),
    }
}
