import math
import struct
import wave

# Audio parameters
sample_rate = 44100

def get_sine_wave(frequency, duration, amplitude=0.4):
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        # Apply a simple envelope (fade in and fade out) to prevent clicking sounds
        envelope = 1.0
        fade_samples = int(sample_rate * 0.05) # 50ms fade
        if i < fade_samples:
            envelope = i / fade_samples
        elif i > num_samples - fade_samples:
            envelope = (num_samples - i) / fade_samples
            
        t = i / sample_rate
        sample = amplitude * envelope * math.sin(2 * math.pi * frequency * t)
        samples.append(sample)
    return samples

# C major chord arpeggio melody
# Frequencies: C4 (261.63), E4 (329.63), G4 (392.00), C5 (523.25)
melody_notes = [
    (261.63, 0.4), # C4
    (329.63, 0.4), # E4
    (392.00, 0.4), # G4
    (523.25, 0.8), # C5
    (392.00, 0.4), # G4
    (329.63, 0.4), # E4
    (261.63, 1.2), # C4 (held longer)
]

all_samples = []
for freq, dur in melody_notes:
    all_samples.extend(get_sine_wave(freq, dur))

# Write the synthesized samples to a WAV file
wav_path = '/home/darian/.gemini/antigravity/scratch/melody.wav'
with wave.open(wav_path, 'wb') as wav_file:
    wav_file.setnchannels(1)      # Mono
    wav_file.setsampwidth(2)      # 16-bit
    wav_file.setframerate(sample_rate)
    for sample in all_samples:
        # Convert float sample [-1.0, 1.0] to signed 16-bit integer
        pcm_val = int(sample * 32767)
        wav_file.writeframesraw(struct.pack('<h', pcm_val))

print(f"Melody WAV generated successfully at {wav_path}!")
