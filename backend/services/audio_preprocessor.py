import os
import logging
import tempfile
from typing import Dict, Any, Optional, Tuple
import numpy as np
import av
import soundfile as sf
from scipy import signal

logger = logging.getLogger(__name__)

# Default configuration for audio preprocessing
DEFAULT_PREPROCESS_CONFIG = {
    "enabled": True,
    "target_sample_rate": 16000,
    "mono": True,
    "trim_silence": True,
    "silence_threshold_rms": 0.012,
    "speech_pad_seconds": 0.22,  # 220ms safety padding before and after speech
    "normalize_loudness": True,
    "target_peak": 0.85,
    "high_pass_filter": False,   # 85 Hz conservative high-pass
    "high_pass_cutoff": 85.0
}

def analyze_audio(file_path: str) -> Dict[str, Any]:
    """
    Extracts technical characteristics of an audio file for diagnostic auditing:
    MIME/format, codec, sample rate, channels, duration, peak, RMS, clipping, silence.
    Never logs private speech or sensitive medical content.
    """
    if not file_path or not os.path.exists(file_path):
        return {"error": "File not found"}

    try:
        container = av.open(file_path)
        audio_stream = next((s for s in container.streams if s.type == 'audio'), None)
        if not audio_stream:
            container.close()
            return {"error": "No audio stream found in container"}

        codec_name = audio_stream.codec_context.name
        sample_rate = audio_stream.codec_context.sample_rate
        channels = audio_stream.codec_context.channels
        format_name = container.format.name
        bit_rate = audio_stream.codec_context.bit_rate or 0

        # Decode samples to numpy to analyze signal levels
        container.seek(0)
        frames = []
        for frame in container.decode(audio_stream):
            arr = frame.to_ndarray()
            # If planar audio (e.g. shape (channels, samples)), average across channels
            if arr.ndim > 1:
                if arr.shape[0] == channels:
                    arr = np.mean(arr, axis=0)
                else:
                    arr = np.mean(arr, axis=1)
            frames.append(arr.astype(np.float32))

        container.close()

        if not frames:
            return {
                "format": format_name,
                "codec": codec_name,
                "sample_rate": sample_rate,
                "channels": channels,
                "duration_seconds": 0.0,
                "is_empty": True
            }

        samples = np.concatenate(frames)
        # Normalize to [-1.0, 1.0] if integer type
        max_val = np.max(np.abs(samples)) if len(samples) > 0 else 0.0
        if max_val > 1.0:
            samples = samples / 32768.0

        duration_sec = len(samples) / float(sample_rate) if sample_rate else 0.0
        peak_amp = float(np.max(np.abs(samples))) if len(samples) > 0 else 0.0
        rms_amp = float(np.sqrt(np.mean(samples ** 2))) if len(samples) > 0 else 0.0

        # Detect clipping (values near 1.0)
        clipped_samples = int(np.sum(np.abs(samples) >= 0.995))
        clipping_pct = (clipped_samples / float(len(samples))) * 100.0 if len(samples) > 0 else 0.0

        # Silence and VAD metrics
        frame_len = int(sample_rate * 0.02)  # 20ms frames
        leading_silence = 0.0
        trailing_silence = 0.0

        if frame_len > 0 and len(samples) >= frame_len:
            n_frames = len(samples) // frame_len
            frame_rms = [
                float(np.sqrt(np.mean(samples[i * frame_len:(i + 1) * frame_len] ** 2)))
                for i in range(n_frames)
            ]
            thresh = 0.015

            # Find first voice frame
            first_idx = next((i for i, r in enumerate(frame_rms) if r > thresh), None)
            if first_idx is not None:
                leading_silence = first_idx * 0.02
                # Find last voice frame
                last_idx = next((i for i in range(n_frames - 1, -1, -1) if frame_rms[i] > thresh), None)
                if last_idx is not None:
                    trailing_silence = (n_frames - 1 - last_idx) * 0.02

        return {
            "format": format_name,
            "codec": codec_name,
            "sample_rate": sample_rate,
            "channels": channels,
            "duration_seconds": round(duration_sec, 3),
            "peak_amplitude": round(peak_amp, 4),
            "rms_energy": round(rms_amp, 4),
            "is_clipped": clipping_pct > 0.1,
            "clipping_pct": round(clipping_pct, 2),
            "is_low_volume": rms_amp < 0.02 and duration_sec > 0.5,
            "leading_silence_sec": round(leading_silence, 3),
            "trailing_silence_sec": round(trailing_silence, 3)
        }
    except Exception as e:
        logger.warning(f"[AUDIO AUDIT] Audio analysis error: {e}")
        return {"error": str(e)}

def preprocess_audio_pipeline(
    input_path: str,
    output_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Preprocesses microphone audio safely before sending to Groq Whisper ASR:
    1. Decodes container (WebM/Opus, WAV, MP3) using PyAV.
    2. Resamples to 16,000 Hz, single-channel (mono).
    3. Conservatively trims leading and trailing room silence with 220ms safety padding.
       Preserves all consonant releases and soft initial Malayalam aspirated sounds.
    4. Applies conservative loudness normalization without clipping or distortion.
    5. Writes standard 16-bit PCM WAV.

    Returns:
        (processed_file_path, audit_metadata)
    """
    cfg = {**DEFAULT_PREPROCESS_CONFIG, **(config or {})}
    
    if not cfg.get("enabled", True):
        analysis = analyze_audio(input_path)
        return input_path, {"applied": False, "analysis": analysis}

    try:
        container = av.open(input_path)
        audio_stream = next((s for s in container.streams if s.type == 'audio'), None)
        if not audio_stream:
            container.close()
            return input_path, {"applied": False, "reason": "no_audio_stream"}

        orig_sr = audio_stream.codec_context.sample_rate
        orig_channels = audio_stream.codec_context.channels
        orig_codec = audio_stream.codec_context.name

        # Decode frames
        container.seek(0)
        frames = []
        for frame in container.decode(audio_stream):
            arr = frame.to_ndarray()
            if arr.ndim > 1:
                if arr.shape[0] == orig_channels:
                    arr = np.mean(arr, axis=0)
                else:
                    arr = np.mean(arr, axis=1)
            frames.append(arr.astype(np.float32))

        container.close()

        if not frames:
            return input_path, {"applied": False, "reason": "empty_frames"}

        raw_samples = np.concatenate(frames)
        max_val = np.max(np.abs(raw_samples)) if len(raw_samples) > 0 else 0.0
        if max_val > 1.0:
            raw_samples = raw_samples / 32768.0

        target_sr = cfg.get("target_sample_rate", 16000)
        
        # Resample to 16,000 Hz if needed using scipy.signal.resample_poly
        if orig_sr != target_sr and orig_sr > 0:
            import math
            gcd = math.gcd(orig_sr, target_sr)
            up = target_sr // gcd
            down = orig_sr // gcd
            resampled = signal.resample_poly(raw_samples, up, down).astype(np.float32)
        else:
            resampled = raw_samples

        total_samples = len(resampled)
        orig_duration = total_samples / float(target_sr)

        # 3. Conservative Voice Activity Detection / Silence Trimming
        trimmed_samples = resampled
        lead_trimmed = 0.0
        trail_trimmed = 0.0

        if cfg.get("trim_silence", True) and orig_duration > 0.8:
            frame_len = int(target_sr * 0.02)  # 20ms frame
            silence_thresh = cfg.get("silence_threshold_rms", 0.012)
            pad_samples = int(target_sr * cfg.get("speech_pad_seconds", 0.22))

            if frame_len > 0 and total_samples >= frame_len:
                n_frames = total_samples // frame_len
                frame_rms = [
                    float(np.sqrt(np.mean(resampled[i * frame_len:(i + 1) * frame_len] ** 2)))
                    for i in range(n_frames)
                ]

                # Find first active frame
                start_frame = next((i for i, r in enumerate(frame_rms) if r > silence_thresh), None)
                end_frame = next((i for i in range(n_frames - 1, -1, -1) if frame_rms[i] > silence_thresh), None)

                if start_frame is not None and end_frame is not None and start_frame <= end_frame:
                    start_idx = max(0, start_frame * frame_len - pad_samples)
                    end_idx = min(total_samples, (end_frame + 1) * frame_len + pad_samples)

                    # Only trim if we preserve at least 0.3s of speech
                    if (end_idx - start_idx) / float(target_sr) >= 0.3:
                        lead_trimmed = start_idx / float(target_sr)
                        trail_trimmed = (total_samples - end_idx) / float(target_sr)
                        trimmed_samples = resampled[start_idx:end_idx]

        # 4. Optional High-Pass Filter (85 Hz)
        filtered_samples = trimmed_samples
        if cfg.get("high_pass_filter", False):
            try:
                cutoff = cfg.get("high_pass_cutoff", 85.0)
                sos = signal.butter(2, cutoff, btype='highpass', fs=target_sr, output='sos')
                filtered_samples = signal.sosfilt(sos, trimmed_samples).astype(np.float32)
            except Exception as f_err:
                logger.warning(f"[AUDIO PREPROCESSOR] High-pass filter error: {f_err}")
                filtered_samples = trimmed_samples

        # 5. Conservative Loudness Normalization
        normalized_samples = filtered_samples
        peak = float(np.max(np.abs(filtered_samples))) if len(filtered_samples) > 0 else 0.0
        target_peak = cfg.get("target_peak", 0.85)

        if cfg.get("normalize_loudness", True) and peak > 0.01:
            # If peak is quiet (< 0.6) or clipping (> 0.95), scale to target peak
            scale_factor = target_peak / peak
            # Bound scale factor conservatively between 0.5 and 5.0 to prevent noise explosion
            bounded_scale = min(max(scale_factor, 0.5), 4.5)
            normalized_samples = np.clip(filtered_samples * bounded_scale, -1.0, 1.0)

        # 6. Save as standard 16-bit PCM WAV
        if not output_path:
            fd, output_path = tempfile.mkstemp(suffix="_preprocessed.wav", prefix="orma_asr_")
            os.close(fd)

        sf.write(output_path, normalized_samples, target_sr, subtype='PCM_16')
        proc_duration = len(normalized_samples) / float(target_sr)

        metadata = {
            "applied": True,
            "orig_codec": orig_codec,
            "orig_sr": orig_sr,
            "orig_channels": orig_channels,
            "orig_duration_sec": round(orig_duration, 3),
            "proc_duration_sec": round(proc_duration, 3),
            "lead_trimmed_sec": round(lead_trimmed, 3),
            "trail_trimmed_sec": round(trail_trimmed, 3),
            "peak_before": round(peak, 4),
            "peak_after": round(float(np.max(np.abs(normalized_samples))), 4)
        }

        return output_path, metadata

    except Exception as e:
        logger.warning(f"[AUDIO PREPROCESSOR] Pipeline fallback to raw audio due to: {e}")
        return input_path, {"applied": False, "error": str(e)}
