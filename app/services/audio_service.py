"""
Audio processing service
"""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple
from pydub import AudioSegment
from app.core.logging import get_logger
from app.config import settings
from app.exceptions import AudioProcessingError
from app.utils.file_utils import file_handler

logger = get_logger("audio_service")


class AudioProcessor:
    """Audio processing with async support"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def process_audio_file(self, file_path: str) -> Tuple[str, float]:
        """Process audio file and return path to processed WAV file and duration"""
        try:
            start_time = time.time()
            
            # Run audio processing in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Load and process audio
            audio, duration = await loop.run_in_executor(
                self.executor, self._process_audio_sync, file_path
            )
            
            # Export to WAV format
            wav_path = file_path + ".wav"
            await loop.run_in_executor(
                self.executor, audio.export, wav_path, "wav"
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Audio processed in {processing_time:.2f}s, duration: {duration:.2f}s")
            
            return wav_path, duration
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}", exc_info=True)
            raise AudioProcessingError(f"Failed to process audio: {str(e)}")
    
    def _process_audio_sync(self, file_path: str) -> Tuple[AudioSegment, float]:
        """Synchronous audio processing"""
        try:
            # Load audio file
            audio = AudioSegment.from_file(file_path)
            
            # Get original duration
            duration_seconds = len(audio) / 1000.0
            
            # Convert to required format
            audio = audio.set_channels(settings.channels)
            audio = audio.set_frame_rate(settings.sample_rate)
            
            # Normalize audio levels
            audio = self._normalize_audio(audio)
            
            return audio, duration_seconds
            
        except Exception as e:
            raise AudioProcessingError(f"Audio processing error: {str(e)}")
    
    def _normalize_audio(self, audio: AudioSegment) -> AudioSegment:
        """Normalize audio levels"""
        try:
            # Apply gain normalization
            target_dBFS = -20.0
            change_in_dBFS = target_dBFS - audio.dBFS
            
            # Limit gain changes to prevent distortion
            if change_in_dBFS > 10:
                change_in_dBFS = 10
            elif change_in_dBFS < -10:
                change_in_dBFS = -10
            
            normalized_audio = audio.apply_gain(change_in_dBFS)
            
            return normalized_audio
            
        except Exception as e:
            logger.warning(f"Audio normalization failed: {e}")
            return audio  # Return original if normalization fails
    
    def validate_audio_duration(self, duration: float) -> bool:
        """Validate audio duration"""
        max_duration = 300  # 5 minutes
        min_duration = 0.5  # 0.5 seconds
        
        return min_duration <= duration <= max_duration
    
    async def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)


# Global audio processor instance
audio_processor = AudioProcessor()