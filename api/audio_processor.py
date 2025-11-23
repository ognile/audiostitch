import onnxruntime
import numpy as np
from pydub import AudioSegment
import io
import os

class AudioProcessor:
    def __init__(self):
        # Load ONNX model
        model_path = os.path.join(os.path.dirname(__file__), "silero_vad.onnx")
        self.session = onnxruntime.InferenceSession(model_path)
        self.reset_state()

    def reset_state(self):
        # Initialize state (h, c) for LSTM
        # Shape: (2, 1, 64) for Silero VAD v4/v5
        self._h = np.zeros((2, 1, 64)).astype('float32')
        self._c = np.zeros((2, 1, 64)).astype('float32')
        self._state = np.zeros((2, 1, 128)).astype('float32') # For v5? Let's check inputs.
        
        # Actually, let's inspect the model inputs to be sure, but standard Silero VAD ONNX usually takes:
        # input: (batch, time)
        # state: (2, batch, 128)
        # sr: (batch)
        
        self._state = np.zeros((2, 1, 128)).astype('float32')

    def load_audio(self, file_bytes):
        """Loads audio from bytes into a Pydub AudioSegment."""
        return AudioSegment.from_file(io.BytesIO(file_bytes))

    def _get_audio_array(self, audio_segment):
        """Converts Pydub AudioSegment to float32 numpy array at 16k."""
        # Resample to 16000Hz
        audio_16k = audio_segment.set_frame_rate(16000).set_channels(1)
        
        # Convert to numpy
        samples = np.array(audio_16k.get_array_of_samples()).astype(np.float32)
        
        # Normalize
        if audio_segment.sample_width == 2:
            samples /= 32768.0
        elif audio_segment.sample_width == 4:
            samples /= 2147483648.0
            
        return samples

    def get_speech_timestamps(self, audio, threshold=0.5, min_speech_duration_ms=250, min_silence_duration_ms=100):
        """
        Simplified VAD logic using ONNX model.
        """
        self.reset_state()
        
        sampling_rate = 16000
        # Window size: 512 samples (32ms) is standard for Silero
        window_size_samples = 512
        
        speech_probs = []
        
        # Iterate over audio in chunks
        for i in range(0, len(audio), window_size_samples):
            chunk = audio[i:i+window_size_samples]
            
            if len(chunk) < window_size_samples:
                # Pad last chunk
                chunk = np.pad(chunk, (0, window_size_samples - len(chunk)))
            
            # Prepare inputs
            input_tensor = chunk.reshape(1, -1) # (1, 512)
            sr_tensor = np.array([sampling_rate], dtype=np.int64)
            
            # Run inference
            ort_inputs = {
                'input': input_tensor, 
                'state': self._state, 
                'sr': sr_tensor
            }
            ort_outs = self.session.run(None, ort_inputs)
            
            output = ort_outs[0] # (1, 1) probability
            self._state = ort_outs[1] # Update state
            
            speech_probs.append(output.item())

        # Post-processing to get timestamps
        triggered = False
        speeches = []
        current_speech = {}
        
        # Convert ms to chunks
        min_speech_chunks = int(min_speech_duration_ms / 32)
        min_silence_chunks = int(min_silence_duration_ms / 32)
        
        temp_end = 0
        prev_end = 0
        
        for i, prob in enumerate(speech_probs):
            if prob >= threshold and temp_end:
                temp_end = 0
                
            if prob >= threshold and not triggered:
                triggered = True
                current_speech['start'] = i * window_size_samples
                
            if prob < threshold - 0.15 and triggered: # Hysteresis
                if not temp_end:
                    temp_end = i * window_size_samples
                
                # Check if silence is long enough
                if (i * window_size_samples) - temp_end >= min_silence_duration_ms * 16: # *16 because samples = ms * 16
                     current_speech['end'] = temp_end
                     
                     # Check duration
                     if (current_speech['end'] - current_speech['start']) >= min_speech_duration_ms * 16:
                         speeches.append(current_speech)
                     
                     current_speech = {}
                     triggered = False
                     temp_end = 0
        
        # Handle last speech
        if triggered:
            current_speech['end'] = len(audio)
            if (current_speech['end'] - current_speech['start']) >= min_speech_duration_ms * 16:
                speeches.append(current_speech)
                
        return speeches

    def process_audio(self, file_bytes, padding_ms=150, crossfade_ms=50):
        original_audio = self.load_audio(file_bytes)
        audio_array = self._get_audio_array(original_audio)
        
        timestamps = self.get_speech_timestamps(audio_array)
        
        if not timestamps:
            return original_audio
            
        processed_audio = AudioSegment.empty()
        
        for i, ts in enumerate(timestamps):
            start_sample = ts['start']
            end_sample = ts['end']
            
            start_ms = (start_sample / 16000) * 1000
            end_ms = (end_sample / 16000) * 1000
            
            start_ms = max(0, start_ms - padding_ms)
            end_ms = min(len(original_audio), end_ms + padding_ms)
            
            segment = original_audio[start_ms:end_ms]
            
            if i == 0:
                processed_audio += segment
            else:
                processed_audio = processed_audio.append(segment, crossfade=crossfade_ms)
                
        return processed_audio
