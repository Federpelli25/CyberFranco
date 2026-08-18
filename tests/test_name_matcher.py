from src.data.participant_repository import ParticipantRepository
from src.recognition.name_matcher import NameMatcher
import unittest


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


class DuplicateNameMatcherTests(unittest.TestCase):

    def test_unique_exact_name_is_a_match(self):
        unique = [
            item for item in participants
            if item["search_name"] == "luca bianchi"
        ]
        result = NameMatcher(unique).resolve("Luca Bianchi")
        self.assertEqual(result["status"], NameMatcher.STATUS_MATCH)

    def test_duplicate_exact_name_is_ambiguous_at_score_100(self):
        duplicates = [
            item for item in participants
            if item["search_name"] == "mario rossi"
        ]
        result = NameMatcher(duplicates).resolve("Mario Rossi")
        self.assertEqual(result["status"], NameMatcher.STATUS_AMBIGUOUS)
        self.assertEqual(result["reason"], "duplicate_exact_name")
        self.assertEqual(len(result["results"]), 2)
        self.assertTrue(all(item["score"] == 100 for item in result["results"]))
