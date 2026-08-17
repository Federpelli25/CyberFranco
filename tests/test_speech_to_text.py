import time

from src.audio.microphone import MicrophoneRecorder
from src.audio.speech_to_text import SpeechToText
from src.data.participant_repository import ParticipantRepository


print("INIZIALIZZAZIONE")

repository = ParticipantRepository(
    "data/partecipanti_example.xlsx"
)

participants = repository.load()

print(
    f"Partecipanti disponibili: "
    f"{len(participants)}"
)

hotwords = ", ".join(
    participant["nome_completo"]
    for participant in participants
)

print()
print("Hotwords caricate:")
print(hotwords)

recorder = MicrophoneRecorder()

speech_to_text = SpeechToText(
    model_path="models/faster-whisper-small",
    device="cpu",
    compute_type="int8",
    language="it",
)

print()
print(
    "Preparati a pronunciare "
    "nome e cognome."
)

print()

for seconds in range(
    3,
    0,
    -1,
):
    print(
        f"Registrazione tra "
        f"{seconds}..."
    )

    time.sleep(1)

print()
print(
    "PARLA ORA: pronuncia "
    "nome e cognome."
)

audio = recorder.record(
    duration_seconds=4.0
)

print()
print(
    "Trascrizione in corso..."
)

text = speech_to_text.transcribe(
    audio,
    hotwords=hotwords,
)

print()
print("=" * 50)
print("TRASCRIZIONE")
print("=" * 50)

if text:
    print(text)
else:
    print(
        "Nessun testo riconosciuto."
    )

print("=" * 50)
