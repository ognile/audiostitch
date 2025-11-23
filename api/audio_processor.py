import onnxruntime
import numpy as np
from pydub import AudioSegment
import io
import os
import urllib.request

class AudioProcessor:
    def __init__(self):
        # Download model to /tmp (only writable dir on Vercel)
        model_path = "/tmp/silero_vad.onnx"
        
        if not os.path.exists(model_path):
            print("Downloading Silero VAD model...")
            url = "https://github.com/snakers4/silero-vad/raw/master/files/silero_vad.onnx"
            urllib.request.urlretrieve(url, model_path)
        
        self.session = onnxruntime.InferenceSession(model_path)
        self._state = np.zeros((2, 1, 128)).astype('float32')

    def _convert_to_tensor(self, audio_segment):
        """Convert AudioSegment to numpy array for ONNX."""
        audio_16k = audio_segment.set_frame_rate(16000).set_channels(1)
        samples = np.array(audio_16k.get_array_of_samples()).astype(np.float32)
        
        if audio_segment.sample_width == 2:
            samples /= 32768.0
        elif audio_segment.sample_width == 4:
            samples /= 2147483648.0
            
        return samples

    def get_speech_timestamps(self, wav_array, sampling_rate=16000):
        """Detect speech using ONNX model."""
        self._state = np.zeros((2, 1, 128)).astype('float32')
        window_size = 512
        speech_probs = []
        
        for i in range(0, len(wav_array), window_size):
            chunk = wav_array[i:i+window_size]
            if len(chunk) < window_size:
                chunk = np.pad(chunk, (0, window_size - len(chunk)))
            
            ort_inputs = {
                'input': chunk.reshape(1, -1),
                'state': self._state,
                'sr': np.array([sampling_rate], dtype=np.int64)
            }
            output, self._state = self.session.run(None, ort_inputs)
            speech_probs.append(output.item())
        
        # Simple thresholding to get speech segments
        threshold = 0.5
        min_speech_samples = 250 * 16  # 250ms in samples
        min_silence_samples = 100 * 16  # 100ms in samples
        
        speeches = []
        in_speech = False
        speech_start = 0
        
        for i, prob in enumerate(speech_probs):
            sample_idx = i * window_size
            
            if prob >= threshold and not in_speech:
                speech_start = sample_idx
                in_speech = True
            elif prob < threshold and in_speech:
                speech_len = sample_idx - speech_start
                if speech_len >= min_speech_samples:
                    speeches.append({'start': speech_start, 'end': sample_idx})
                in_speech = False
        
        # Handle last segment
        if in_speech:
            speeches.append({'start': speech_start, 'end': len(wav_array)})
        
        return speeches

    def process_audio(self, file_bytes, padding_ms=150, crossfade_ms=50):
        # Load audio
        original_audio = AudioSegment.from_file(io.BytesIO(file_bytes))
        
        # Convert to array for VAD
        wav_array = self._convert_to_tensor(original_audio)
        
        # Get speech timestamps
        timestamps = self.get_speech_timestamps(wav_array)
        
        if not timestamps:
            return original_audio
        
        # Stitch segments with crossfade
        processed_audio = AudioSegment.empty()
        
        for i, ts in enumerate(timestamps):
            # Convert samples to ms
            start_ms = (ts['start'] / 16000) * 1000
            end_ms = (ts['end'] / 16000) * 1000
            
            # Add padding
            start_ms = max(0, start_ms - padding_ms)
            end_ms = min(len(original_audio), end_ms + padding_ms)
            
            segment = original_audio[start_ms:end_ms]
            
            if i == 0:
                processed_audio = segment
            else:
                processed_audio = processed_audio.append(segment, crossfade=crossfade_ms)
        
        return processed_audio
