import torch
import torchaudio
from pydub import AudioSegment
import io
import numpy as np

class AudioProcessor:
    def __init__(self):
        self.model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                           model='silero_vad',
                                           force_reload=False,
                                           onnx=False)
        (self.get_speech_timestamps,
         self.save_audio,
         self.read_audio,
         self.VADIterator,
         self.collect_chunks) = utils

    def load_audio(self, file_bytes):
        """Loads audio from bytes into a Pydub AudioSegment."""
        return AudioSegment.from_file(io.BytesIO(file_bytes))

    def _convert_to_tensor(self, audio_segment):
        """Converts Pydub AudioSegment to torch tensor for Silero VAD."""
        # Resample to 16000Hz as required by Silero
        audio_16k = audio_segment.set_frame_rate(16000).set_channels(1)
        
        # Convert to numpy array of float32
        samples = np.array(audio_16k.get_array_of_samples()).astype(np.float32)
        
        # Normalize to [-1, 1]
        if audio_segment.sample_width == 2: # 16-bit
            samples /= 32768.0
        elif audio_segment.sample_width == 4: # 32-bit
            samples /= 2147483648.0
            
        return torch.from_numpy(samples)

    def process_audio(self, file_bytes, padding_ms=150, crossfade_ms=50):
        """
        Main processing function:
        1. Load audio
        2. Detect speech
        3. Pad timestamps
        4. Slice and stitch with crossfade
        """
        original_audio = self.load_audio(file_bytes)
        
        # Prepare for VAD
        wav_tensor = self._convert_to_tensor(original_audio)
        
        # Get speech timestamps
        # min_speech_duration_ms: ignore short noises
        # min_silence_duration_ms: merge close segments
        speech_timestamps = self.get_speech_timestamps(
            wav_tensor,
            self.model,
            sampling_rate=16000,
            min_speech_duration_ms=250,
            min_silence_duration_ms=100
        )
        
        if not speech_timestamps:
            return original_audio # No speech detected, return original? Or empty?
            
        # Create a new empty AudioSegment
        processed_audio = AudioSegment.empty()
        
        # Iterate and stitch
        # We need to map 16k timestamps back to original audio time
        # Silero returns samples indices at 16000Hz
        
        for i, ts in enumerate(speech_timestamps):
            start_sample = ts['start']
            end_sample = ts['end']
            
            # Convert samples to milliseconds
            start_ms = (start_sample / 16000) * 1000
            end_ms = (end_sample / 16000) * 1000
            
            # Apply padding
            start_ms = max(0, start_ms - padding_ms)
            end_ms = min(len(original_audio), end_ms + padding_ms)
            
            # Extract segment
            segment = original_audio[start_ms:end_ms]
            
            # Stitch
            if i == 0:
                processed_audio += segment
            else:
                # Crossfade
                processed_audio = processed_audio.append(segment, crossfade=crossfade_ms)
                
        return processed_audio
