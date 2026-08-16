use std::path::Path;
use symphonia::core::audio::GenericAudioBufferRef;
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


/// Decodes the audio track identified by the struct `audio_track`.
pub fn decode_audio_track(audio_track: AudioTrack) -> Result<(), AudioTrackError> {
    let AudioTrack { mut format, track_id } = audio_track;

    let codec_params = format
        .tracks()
        .iter()
        .find(|t| t.id == track_id)
        .and_then(|t| t.codec_params.as_ref())
        .and_then(|cp| match cp {
            CodecParameters::Audio(audio) => Some(audio),
            _ => None,
        })
        .ok_or(AudioTrackError::NoAudioTrack)?;

    let mut decoder = symphonia::default::get_codecs()
        .make_audio_decoder(codec_params, &AudioDecoderOptions::default())?;

    while let Some(packet) = format.next_packet()? {
        if packet.track_id != track_id {
            continue;
        }
        let _decoded: GenericAudioBufferRef<'_> = decoder.decode(&packet)?;
        // decoded.spec() / decoded.capacity() are available here — see caveat below.
    }
    Ok(())
}
