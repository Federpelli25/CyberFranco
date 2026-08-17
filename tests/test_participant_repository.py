from src.data.participant_repository import ParticipantRepository


repository = ParticipantRepository("data/partecipanti_example.xlsx")

participants = repository.load()

print(f"Partecipanti caricati: {len(participants)}")

for participant in participants:
    print(
        f"{participant['nome_completo']} -> "
        f"{participant['squadra']}"
    )