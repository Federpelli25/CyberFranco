import logging

from rapidfuzz import fuzz, process


logger = logging.getLogger(__name__)


class NameMatcher:
    STATUS_MATCH = "match"
    STATUS_AMBIGUOUS = "ambiguous"
    STATUS_NOT_FOUND = "not_found"

    def __init__(self, participants: list[dict]):
        self.participants = participants

        self.search_map: dict[str, list[dict]] = {}
        for participant in participants:
            self.search_map.setdefault(participant["search_name"], []).append(
                participant
            )

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
            str(match["participant"]["id"])
            for match in results
        }

        for matched_name, score, _ in fuzzy_matches:
            if matched_name in already_added:
                continue

            for participant in self.search_map[matched_name]:
                participant_id = str(participant["id"])
                if participant_id in already_added:
                    continue
                results.append({
                    "participant": participant,
                    "score": round(score, 2),
                    "match_type": "fuzzy",
                })
                already_added.add(participant_id)
                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break

        return results[:limit]

    def resolve(
        self,
        query: str,
        automatic_threshold: float = 97.0,
        ambiguity_margin: float = 7.0,
    ) -> dict:

        logger.debug("Match query: %r", query)
        normalized_query = self._normalize(
            query
        )

        if not normalized_query:
            logger.warning("Match status: not_found; empty query")
            return self._not_found_result(
                query
            )

        exact_participants = self.search_map.get(
            normalized_query
        )

        if exact_participants:
            exact_matches = [{
                "participant": participant,
                "score": 100.0,
                "match_type": "exact",
            } for participant in exact_participants]
            if len(exact_matches) > 1:
                logger.warning(
                    "Ambiguous exact-name duplicate: name=%s ids=%s",
                    normalized_query,
                    [item["participant"]["id"] for item in exact_matches],
                )
                return {
                    "status": self.STATUS_AMBIGUOUS,
                    "query": query,
                    "best_match": exact_matches[0],
                    "results": exact_matches,
                    "reason": "duplicate_exact_name",
                }

            logger.info(
                "Match status: match; participant_id=%s; score=100.0",
                exact_participants[0]["id"],
            )
            return {
                "status": self.STATUS_MATCH,
                "query": query,
                "best_match": exact_matches[0],
                "results": exact_matches,
            }

        results = self.search(
            query,
            limit=5,
        )

        if not results:
            logger.warning("Match status: not_found")
            return self._not_found_result(
                query
            )

        best = results[0]

        if best["score"] < automatic_threshold:
            logger.warning(
                "Match status: ambiguous; best=%s; score=%.2f",
                best["participant"]["search_name"],
                best["score"],
            )
            logger.debug("Ambiguous candidates: %s", results)
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
                logger.warning(
                    "Match status: ambiguous; best=%s; score=%.2f",
                    best["participant"]["search_name"],
                    best["score"],
                )
                logger.debug("Ambiguous candidates: %s", results)
                return {
                    "status": self.STATUS_AMBIGUOUS,
                    "query": query,
                    "best_match": best,
                    "results": results,
                }

        logger.info(
            "Match status: match; candidate=%s; score=%.2f",
            best["participant"]["search_name"],
            best["score"],
        )
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
