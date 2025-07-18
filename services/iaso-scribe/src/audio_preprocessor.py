"""
Audio Preprocessing Pipeline for IasoScribe
Handles audio normalization, noise reduction, and format conversion
"""

import os
import logging
import tempfile
import hashlib
from typing import Union, Optional, Tuple
from pathlib import Path

import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import normalize
import webrtcvad
import httpx
from scipy import signal

logger = logging.getLogger(__name__)

class AudioPreprocessor:
    """
    Preprocess audio for optimal medical transcription
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize audio preprocessor
        
        Args:
            cache_dir: Directory for caching processed audio
        """
        self.cache_dir = cache_dir or tempfile.gettempdir()
        Path(self.cache_dir).mkdir(exist_ok=True)
        
        # Initialize VAD
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(2)  # Moderate aggressiveness
        
        # Audio parameters
        self.target_sample_rate = 16000  # Optimal for Whisper
        self.target_channels = 1  # Mono
        self.target_bit_depth = 16
        
        # Medical audio specific settings
        self.noise_reduction_strength = 0.8  # Higher for medical consultations
        self.normalization_headroom = -3.0  # dB
        
        logger.info("Audio preprocessor initialized")
    
    def process(
        self, 
        audio_input: Union[str, np.ndarray], 
        denoise: bool = True,
        normalize_audio: bool = True,
        remove_silence: bool = False,
        enhance_speech: bool = True
    ) -> str:
        """
        Process audio file for optimal transcription
        
        Args:
            audio_input: Path to audio file or numpy array
            denoise: Apply noise reduction
            normalize_audio: Normalize audio levels
            remove_silence: Remove silent segments
            enhance_speech: Apply speech enhancement
            
        Returns:
            Path to processed audio file
        """
        # Load audio
        if isinstance(audio_input, str):
            audio, sr = self._load_audio(audio_input)
        else:
            audio = audio_input
            sr = self.target_sample_rate
        
        # Check cache
        cache_key = self._get_cache_key(audio, denoise, normalize_audio, remove_silence, enhance_speech)
        cached_path = os.path.join(self.cache_dir, f"{cache_key}.wav")
        if os.path.exists(cached_path):
            logger.info(f"Using cached processed audio: {cached_path}")
            return cached_path
        
        # Convert to mono if needed
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        # Resample to target sample rate
        if sr != self.target_sample_rate:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=self.target_sample_rate)
            sr = self.target_sample_rate
        
        # Apply processing pipeline
        if enhance_speech:
            audio = self._enhance_speech(audio, sr)
        
        if denoise:
            audio = self._reduce_noise(audio, sr)
        
        if remove_silence:
            audio = self._remove_silence(audio, sr)
        
        if normalize_audio:
            audio = self._normalize_audio(audio)
        
        # Apply medical audio optimizations
        audio = self._optimize_for_medical(audio, sr)
        
        # Save processed audio
        output_path = os.path.join(self.cache_dir, f"processed_{cache_key}.wav")
        sf.write(output_path, audio, sr, subtype='PCM_16')
        
        logger.info(f"Processed audio saved to: {output_path}")
        return output_path
    
    def _load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Load audio file with format detection
        """
        try:
            # Try librosa first (handles most formats)
            audio, sr = librosa.load(file_path, sr=None, mono=False)
            return audio, sr
        except Exception as e:
            logger.warning(f"Librosa failed, trying pydub: {e}")
            
            # Fallback to pydub for more formats
            audio_segment = AudioSegment.from_file(file_path)
            
            # Convert to numpy array
            samples = np.array(audio_segment.get_array_of_samples())
            
            # Handle stereo
            if audio_segment.channels == 2:
                samples = samples.reshape((-1, 2))
            
            # Normalize to [-1, 1]
            samples = samples.astype(np.float32) / (2**15)
            
            return samples, audio_segment.frame_rate
    
    def _enhance_speech(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Enhance speech frequencies for medical dialogue
        """
        # Apply bandpass filter to focus on speech frequencies (80Hz - 8kHz)
        nyquist = sr / 2
        low_freq = 80 / nyquist
        high_freq = min(8000 / nyquist, 0.99)
        
        # Design bandpass filter
        b, a = signal.butter(5, [low_freq, high_freq], btype='band')
        filtered = signal.filtfilt(b, a, audio)
        
        # Boost mid-frequencies where medical terms are clearest (1-4 kHz)
        mid_low = 1000 / nyquist
        mid_high = min(4000 / nyquist, 0.99)
        b_mid, a_mid = signal.butter(2, [mid_low, mid_high], btype='band')
        mid_boost = signal.filtfilt(b_mid, a_mid, audio) * 0.3
        
        # Combine original with boosted frequencies
        enhanced = filtered + mid_boost
        
        # Prevent clipping
        max_val = np.max(np.abs(enhanced))
        if max_val > 0.95:
            enhanced = enhanced * 0.95 / max_val
        
        return enhanced
    
    def _reduce_noise(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Reduce background noise common in medical settings
        """
        # Estimate noise from first 0.5 seconds (usually silence)
        noise_sample_length = int(0.5 * sr)
        if len(audio) > noise_sample_length:
            noise_sample = audio[:noise_sample_length]
        else:
            noise_sample = audio
        
        # Compute noise profile using spectral subtraction
        noise_fft = np.fft.rfft(noise_sample)
        noise_profile = np.abs(noise_fft)
        
        # Apply spectral subtraction
        window_size = 2048
        hop_length = window_size // 4
        
        # Process in windows
        denoised = np.zeros_like(audio)
        for i in range(0, len(audio) - window_size, hop_length):
            window = audio[i:i + window_size]
            
            # Apply window function
            windowed = window * np.hanning(window_size)
            
            # FFT
            spectrum = np.fft.rfft(windowed)
            magnitude = np.abs(spectrum)
            phase = np.angle(spectrum)
            
            # Spectral subtraction
            magnitude_denoised = magnitude - self.noise_reduction_strength * noise_profile[:len(magnitude)]
            magnitude_denoised = np.maximum(magnitude_denoised, 0.1 * magnitude)  # Keep some signal
            
            # Reconstruct
            spectrum_denoised = magnitude_denoised * np.exp(1j * phase)
            window_denoised = np.fft.irfft(spectrum_denoised)
            
            # Overlap-add
            denoised[i:i + window_size] += window_denoised[:window_size]
        
        # Normalize overlap regions
        for i in range(hop_length, len(denoised) - window_size, hop_length):
            denoised[i:i + hop_length] /= 4
        
        return denoised
    
    def _remove_silence(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Remove silence using WebRTC VAD
        """
        # Convert to 16-bit PCM for VAD
        audio_16bit = (audio * 32767).astype(np.int16)
        
        # VAD works on 10, 20, or 30 ms frames
        frame_duration_ms = 20
        frame_length = int(sr * frame_duration_ms / 1000)
        
        # Pad audio to be divisible by frame length
        num_padding = frame_length - len(audio_16bit) % frame_length
        audio_padded = np.pad(audio_16bit, (0, num_padding), mode='constant')
        
        # Apply VAD
        voiced_frames = []
        for i in range(0, len(audio_padded), frame_length):
            frame = audio_padded[i:i + frame_length]
            if len(frame) == frame_length:
                is_speech = self.vad.is_speech(frame.tobytes(), sr)
                if is_speech:
                    voiced_frames.append(frame)
        
        # Concatenate voiced frames
        if voiced_frames:
            voiced_audio = np.concatenate(voiced_frames)
            # Convert back to float
            return voiced_audio.astype(np.float32) / 32767.0
        else:
            # Return original if no speech detected
            return audio
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio levels for consistent transcription
        """
        # Calculate RMS
        rms = np.sqrt(np.mean(audio**2))
        
        # Target RMS for speech (approximately -20 dB)
        target_rms = 0.1
        
        if rms > 0:
            # Calculate scaling factor
            scaling_factor = target_rms / rms
            
            # Apply scaling with headroom
            max_scaling = 10.0  # Prevent excessive amplification
            scaling_factor = min(scaling_factor, max_scaling)
            
            normalized = audio * scaling_factor
            
            # Peak limiting
            peak = np.max(np.abs(normalized))
            if peak > 0.95:
                normalized = normalized * 0.95 / peak
            
            return normalized
        
        return audio
    
    def _optimize_for_medical(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Apply medical audio specific optimizations
        """
        # Remove very low frequencies (below 50Hz) - often HVAC noise in medical facilities
        nyquist = sr / 2
        low_cutoff = 50 / nyquist
        b, a = signal.butter(4, low_cutoff, btype='high')
        audio = signal.filtfilt(b, a, audio)
        
        # Apply gentle compression to make quiet medical terms more audible
        # This helps with medical professionals who speak softly
        audio = self._apply_compression(audio, threshold=0.3, ratio=2.0)
        
        # De-emphasis to reduce sibilance (helpful for terms ending in -sis, -tic)
        pre_emphasis_factor = 0.97
        audio = np.append(audio[0], audio[1:] - pre_emphasis_factor * audio[:-1])
        
        return audio
    
    def _apply_compression(self, audio: np.ndarray, threshold: float = 0.5, ratio: float = 4.0) -> np.ndarray:
        """
        Apply dynamic range compression
        """
        # Simple compression
        mask = np.abs(audio) > threshold
        compressed = audio.copy()
        compressed[mask] = threshold + (audio[mask] - threshold) / ratio
        
        return compressed
    
    def download_audio(self, url: str) -> str:
        """
        Download audio from URL
        """
        # Create filename from URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()
        file_ext = url.split('.')[-1].split('?')[0]  # Handle URLs with parameters
        
        # Validate extension
        valid_extensions = ['wav', 'mp3', 'mp4', 'm4a', 'ogg', 'flac', 'webm']
        if file_ext.lower() not in valid_extensions:
            file_ext = 'wav'  # Default
        
        output_path = os.path.join(self.cache_dir, f"download_{url_hash}.{file_ext}")
        
        # Check if already downloaded
        if os.path.exists(output_path):
            logger.info(f"Using cached download: {output_path}")
            return output_path
        
        # Download file
        logger.info(f"Downloading audio from: {url}")
        
        with httpx.Client(follow_redirects=True, timeout=300.0) as client:
            response = client.get(url)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
        
        logger.info(f"Downloaded audio to: {output_path}")
        return output_path
    
    def _get_cache_key(self, audio: np.ndarray, *args) -> str:
        """
        Generate cache key for processed audio
        """
        # Use audio stats and processing parameters
        audio_hash = hashlib.md5(audio.tobytes()).hexdigest()[:8]
        param_str = '_'.join(str(arg) for arg in args)
        return f"{audio_hash}_{param_str}"
    
    def get_audio_info(self, file_path: str) -> dict:
        """
        Get audio file information
        """
        audio, sr = self._load_audio(file_path)
        
        duration = len(audio) / sr
        if len(audio.shape) > 1:
            channels = audio.shape[1]
        else:
            channels = 1
        
        return {
            "duration_seconds": duration,
            "sample_rate": sr,
            "channels": channels,
            "format": file_path.split('.')[-1],
            "file_size_mb": os.path.getsize(file_path) / (1024 * 1024)
        }
    
    def cleanup_cache(self, max_age_hours: int = 24):
        """
        Clean up old cached files
        """
        import time
        current_time = time.time()
        
        for file_path in Path(self.cache_dir).glob("processed_*"):
            file_age_hours = (current_time - file_path.stat().st_mtime) / 3600
            if file_age_hours > max_age_hours:
                file_path.unlink()
                logger.info(f"Deleted old cache file: {file_path}")