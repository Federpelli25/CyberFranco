from src.data.participant_repository import ParticipantRepository
from src.recognition.name_matcher import NameMatcher


repository = ParticipantRepository(
    "data/partecipanti_example.xlsx"
)

participants = repository.load()

matcher = NameMatcher(participants)


def print_results(query: str):
    print()
    print("=" * 50)
    print(f'RICERCA: "{query}"')

    results = matcher.search(query)

    for index, result in enumerate(results, start=1):
        participant = result["participant"]

        print(
            f"{index}. "
            f"{participant['nome_completo']} "
            f"-> {participant['squadra']} "
            f"({result['score']}%) "
            f"[{result['match_type']}]"
        )


def test_resolve(query: str):
    print()
    print("-" * 50)
    print(f'RESOLVE: "{query}"')

    result = matcher.resolve(query)

    print(f"STATUS: {result['status']}")

    if result["best_match"]:
        participant = result["best_match"]["participant"]

        print(
            f"BEST MATCH: "
            f"{participant['nome_completo']} "
            f"({result['best_match']['score']}%)"
        )

    if result["status"] == NameMatcher.STATUS_AMBIGUOUS:
        print("Possibili candidati:")

        for match in result["results"]:
            participant = match["participant"]

            print(
                f"- {participant['nome_completo']} "
                f"({match['score']}%)"
            )


print_results("mar")
print_results("fede")
print_results("pel")
print_results("fede pel")
print_results("Mario Rosi")
print_results("Francesco De Luc")

test_resolve("Mario Rossi")
test_resolve("Mario Rosi")
test_resolve("fede")
test_resolve("Federico Pellegrini")
test_resolve("persona inesistente")