from src.audio.microphone import MicrophoneRecorder


recorder = MicrophoneRecorder()

print("Tra poco registra.")
print("Pronuncia il tuo nome e cognome.")

audio = recorder.record(
    duration_seconds=3.0
)

print()
print("TEST COMPLETATO")
print(f"Campioni registrati: {len(audio)}")
print(f"Valore minimo: {audio.min()}")
print(f"Valore massimo: {audio.max()}")