import unittest

from src.core.participant_tracker import ParticipantTracker


def make_participant(
    nome: str,
    cognome: str,
    squadra: str = "ROSSI",
    participant_id: str | None = None,
) -> dict:
    nome_completo = f"{nome} {cognome}"
    participant = {
        "nome": nome,
        "cognome": cognome,
        "squadra": squadra,
        "nome_completo": nome_completo,
        "search_name": nome_completo.lower(),
    }

    if participant_id is not None:
        participant["id"] = participant_id

    return participant


class ParticipantTrackerTests(unittest.TestCase):

    def setUp(self):
        self.mario = make_participant(
            "Mario",
            "Rossi",
        )
        self.luca = make_participant(
            "Luca",
            "Bianchi",
            squadra="BLU",
        )
        self.giulia = make_participant(
            "Giulia",
            "Verdi",
            squadra="GIALLI",
        )
        self.tracker = ParticipantTracker(
            [self.mario, self.luca, self.giulia]
        )

    def test_initial_counters_and_history(self):
        self.assertEqual(self.tracker.total_count, 3)
        self.assertEqual(self.tracker.processed_count, 0)
        self.assertEqual(self.tracker.remaining_count, 3)
        self.assertEqual(
            self.tracker.get_processed_participants(),
            [],
        )
        self.assertIsNone(
            self.tracker.get_last_processed()
        )

    def test_mark_processed_updates_history_and_counters(self):
        self.assertTrue(
            self.tracker.mark_processed(self.mario)
        )

        self.assertTrue(
            self.tracker.is_processed(self.mario)
        )
        self.assertEqual(self.tracker.processed_count, 1)
        self.assertEqual(self.tracker.remaining_count, 2)
        self.assertEqual(
            self.tracker.get_processed_participants(),
            [self.mario],
        )
        self.assertIs(
            self.tracker.get_last_processed(),
            self.mario,
        )

    def test_double_assignment_is_blocked(self):
        self.assertTrue(
            self.tracker.mark_processed(self.mario)
        )
        self.assertFalse(
            self.tracker.mark_processed(self.mario)
        )

        self.assertEqual(self.tracker.processed_count, 1)
        self.assertEqual(self.tracker.remaining_count, 2)
        self.assertEqual(
            self.tracker.get_processed_participants(),
            [self.mario],
        )

    def test_reset_participant_makes_them_available_again(self):
        self.tracker.mark_processed(self.mario)

        self.assertTrue(
            self.tracker.reset_participant(self.mario)
        )
        self.assertFalse(
            self.tracker.is_processed(self.mario)
        )
        self.assertEqual(self.tracker.processed_count, 0)
        self.assertEqual(self.tracker.remaining_count, 3)
        self.assertEqual(
            self.tracker.get_processed_participants(),
            [],
        )
        self.assertTrue(
            self.tracker.mark_processed(self.mario)
        )

    def test_reset_unprocessed_participant_changes_nothing(self):
        self.assertFalse(
            self.tracker.reset_participant(self.mario)
        )
        self.assertEqual(self.tracker.processed_count, 0)
        self.assertEqual(self.tracker.remaining_count, 3)

    def test_undo_last_restores_only_latest_participant(self):
        self.tracker.mark_processed(self.mario)
        self.tracker.mark_processed(self.luca)

        undone = self.tracker.undo_last()

        self.assertIs(undone, self.luca)
        self.assertTrue(
            self.tracker.is_processed(self.mario)
        )
        self.assertFalse(
            self.tracker.is_processed(self.luca)
        )
        self.assertEqual(self.tracker.processed_count, 1)
        self.assertEqual(self.tracker.remaining_count, 2)
        self.assertEqual(
            self.tracker.get_processed_participants(),
            [self.mario],
        )

    def test_undo_on_empty_history_changes_nothing(self):
        self.assertIsNone(self.tracker.undo_last())
        self.assertEqual(self.tracker.processed_count, 0)
        self.assertEqual(self.tracker.remaining_count, 3)

    def test_reset_removes_participant_from_middle_of_history(self):
        self.tracker.mark_processed(self.mario)
        self.tracker.mark_processed(self.luca)
        self.tracker.mark_processed(self.giulia)

        self.assertTrue(
            self.tracker.reset_participant(self.luca)
        )

        self.assertEqual(
            self.tracker.get_processed_participants(),
            [self.mario, self.giulia],
        )
        self.assertIs(
            self.tracker.get_last_processed(),
            self.giulia,
        )
        self.assertEqual(self.tracker.processed_count, 2)
        self.assertEqual(self.tracker.remaining_count, 1)

    def test_reset_all_clears_session(self):
        self.tracker.mark_processed(self.mario)
        self.tracker.mark_processed(self.luca)

        self.tracker.reset_all()

        self.assertEqual(self.tracker.processed_count, 0)
        self.assertEqual(self.tracker.remaining_count, 3)
        self.assertEqual(
            self.tracker.get_processed_participants(),
            [],
        )

    def test_returned_history_cannot_mutate_internal_history(self):
        self.tracker.mark_processed(self.mario)

        history = self.tracker.get_processed_participants()
        history.clear()

        self.assertEqual(self.tracker.processed_count, 1)
        self.assertEqual(
            self.tracker.get_processed_participants(),
            [self.mario],
        )

    def test_optional_ids_distinguish_equal_names(self):
        first_luca = make_participant(
            "Luca",
            "Rossi",
            squadra="DRAGHI",
            participant_id="1",
        )
        second_luca = make_participant(
            "Luca",
            "Rossi",
            squadra="LUPI",
            participant_id="2",
        )
        tracker = ParticipantTracker(
            [first_luca, second_luca]
        )

        self.assertTrue(tracker.mark_processed(first_luca))
        self.assertTrue(tracker.mark_processed(second_luca))
        self.assertEqual(tracker.processed_count, 2)
        self.assertEqual(tracker.remaining_count, 0)

    def test_invalid_participant_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "search_name",
        ):
            self.tracker.mark_processed(
                {"nome_completo": "Dato incompleto"}
            )

    def test_complete_required_event_sequence(self):
        self.assertTrue(self.tracker.mark_processed(self.mario))
        self.assertEqual(self.tracker.processed_count, 1)

        self.assertFalse(self.tracker.mark_processed(self.mario))
        self.assertEqual(self.tracker.processed_count, 1)

        self.assertTrue(self.tracker.reset_participant(self.mario))
        self.assertFalse(self.tracker.is_processed(self.mario))

        self.assertTrue(self.tracker.mark_processed(self.mario))
        self.assertTrue(self.tracker.mark_processed(self.luca))
        self.assertEqual(self.tracker.processed_count, 2)

        self.assertIs(self.tracker.undo_last(), self.luca)
        self.assertFalse(self.tracker.is_processed(self.luca))
        self.assertTrue(self.tracker.is_processed(self.mario))
        self.assertEqual(self.tracker.processed_count, 1)
        self.assertEqual(self.tracker.remaining_count, 2)


if __name__ == "__main__":
    unittest.main()
