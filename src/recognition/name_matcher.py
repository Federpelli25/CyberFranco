from rapidfuzz import fuzz, process


class NameMatcher:
    STATUS_MATCH = "match"
    STATUS_AMBIGUOUS = "ambiguous"
    STATUS_NOT_FOUND = "not_found"

    def __init__(self, participants: list[dict]):
        self.participants = participants

        self.search_map = {
            participant["search_name"]: participant
            for participant in participants
        }

        self.choices = list(self.search_map.keys())

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:

        normalized_query = self._normalize(query)

        if not normalized_query:
            return []

        prefix_matches = self._prefix_search(
            normalized_query,
            limit=limit,
        )

        fuzzy_matches = process.extract(
            normalized_query,
            self.choices,
            scorer=fuzz.WRatio,
            limit=limit * 2,
        )

        results = prefix_matches.copy()

        already_added = {
            match["participant"]["search_name"]
            for match in results
        }

        for matched_name, score, _ in fuzzy_matches:
            if matched_name in already_added:
                continue

            participant = self.search_map[
                matched_name
            ]

            results.append(
                {
                    "participant": participant,
                    "score": round(score, 2),
                    "match_type": "fuzzy",
                }
            )

            already_added.add(
                matched_name
            )

            if len(results) >= limit:
                break

        return results[:limit]

    def resolve(
        self,
        query: str,
        automatic_threshold: float = 97.0,
        ambiguity_margin: float = 7.0,
    ) -> dict:

        normalized_query = self._normalize(
            query
        )

        if not normalized_query:
            return self._not_found_result(
                query
            )

        exact_participant = self.search_map.get(
            normalized_query
        )

        if exact_participant:
            exact_match = {
                "participant": exact_participant,
                "score": 100.0,
                "match_type": "exact",
            }

            return {
                "status": self.STATUS_MATCH,
                "query": query,
                "best_match": exact_match,
                "results": [exact_match],
            }

        results = self.search(
            query,
            limit=5,
        )

        if not results:
            return self._not_found_result(
                query
            )

        best = results[0]

        if best["score"] < automatic_threshold:
            return {
                "status": self.STATUS_AMBIGUOUS,
                "query": query,
                "best_match": best,
                "results": results,
            }

        if len(results) > 1:
            second = results[1]

            difference = (
                best["score"]
                - second["score"]
            )

            if difference < ambiguity_margin:
                return {
                    "status": self.STATUS_AMBIGUOUS,
                    "query": query,
                    "best_match": best,
                    "results": results,
                }

        return {
            "status": self.STATUS_MATCH,
            "query": query,
            "best_match": best,
            "results": results,
        }

    def _prefix_search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:

        query_words = query.split()

        matches = []

        for participant in self.participants:
            nome = (
                participant["nome"]
                .lower()
            )

            cognome = (
                participant["cognome"]
                .lower()
            )

            score = (
                self._calculate_prefix_score(
                    query_words,
                    nome,
                    cognome,
                )
            )

            if score is None:
                continue

            matches.append(
                {
                    "participant": participant,
                    "score": score,
                    "match_type": "prefix",
                }
            )

        matches.sort(
            key=lambda item: (
                -item["score"],
                item["participant"][
                    "nome_completo"
                ],
            )
        )

        return matches[:limit]

    @staticmethod
    def _calculate_prefix_score(
        query_words: list[str],
        nome: str,
        cognome: str,
    ) -> float | None:

        if len(query_words) == 1:
            query = query_words[0]

            if nome.startswith(query):
                return 100.0

            if cognome.startswith(query):
                return 98.0

            return None

        first_query = query_words[0]
        second_query = query_words[1]

        if (
            nome.startswith(first_query)
            and cognome.startswith(second_query)
        ):
            return 100.0

        if (
            cognome.startswith(first_query)
            and nome.startswith(second_query)
        ):
            return 99.0

        return None

    def _not_found_result(
        self,
        query: str,
    ) -> dict:

        return {
            "status": self.STATUS_NOT_FOUND,
            "query": query,
            "best_match": None,
            "results": [],
        }

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:

        return " ".join(
            value
            .strip()
            .lower()
            .split()
        )