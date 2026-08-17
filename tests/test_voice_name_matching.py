import time

from src.audio.microphone import (
    MicrophoneRecorder,
)
from src.audio.speech_to_text import (
    SpeechToText,
)
from src.data.participant_repository import (
    ParticipantRepository,
)
from src.recognition.name_matcher import (
    NameMatcher,
)


print(
    "=" * 60
)

print(
    "CYBERFRANCO - TEST RICONOSCIMENTO COMPLETO"
)

print(
    "=" * 60
)

repository = ParticipantRepository(
    "data/partecipanti_example.xlsx"
)

participants = repository.load()

matcher = NameMatcher(
    participants
)

print()
print(
    f"Partecipanti caricati: "
    f"{len(participants)}"
)

hotwords = ", ".join(
    participant["nome_completo"]
    for participant in participants
)

recorder = MicrophoneRecorder(
    sample_rate=16000,
    channels=1,
)

speech_to_text = SpeechToText(
    model_size="small",
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

    time.sleep(
        1
    )

print()
print(
    "PARLA ORA"
)

audio = recorder.record(
    duration_seconds=4.0
)

print()
print(
    "Trascrizione..."
)

transcription = (
    speech_to_text.transcribe(
        audio,
        hotwords=hotwords,
    )
)

print()
print(
    "=" * 60
)

print(
    "TESTO RICONOSCIUTO"
)

print(
    "=" * 60
)

if not transcription:
    print(
        "Nessun testo riconosciuto."
    )

    raise SystemExit(
        1
    )

print(
    transcription
)

print()
print(
    "Ricerca partecipante..."
)

result = matcher.resolve(
    transcription
)

print()
print(
    "=" * 60
)

print(
    "RISULTATO MATCHING"
)

print(
    "=" * 60
)

print(
    f"Stato: "
    f"{result['status']}"
)

best_match = result[
    "best_match"
]

if best_match is None:
    print(
        "Nessun partecipante trovato."
    )

    raise SystemExit(
        1
    )

participant = best_match[
    "participant"
]

score = best_match[
    "score"
]

print(
    f"Nome riconosciuto: "
    f"{participant['nome_completo']}"
)

print(
    f"Affidabilità: "
    f"{score}%"
)

print(
    f"Squadra: "
    f"{participant['squadra']}"
)

if (
    result["status"]
    == NameMatcher.STATUS_AMBIGUOUS
):
    print()
    print(
        "ATTENZIONE: "
        "riconoscimento ambiguo."
    )

    print(
        "Possibili alternative:"
    )

    for match in result[
        "results"
    ]:
        candidate = match[
            "participant"
        ]

        print(
            f"- "
            f"{candidate['nome_completo']} "
            f"({match['score']}%)"
        )

print()
print(
    "=" * 60
)