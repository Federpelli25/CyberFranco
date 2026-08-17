import unittest

from tests.test_sorting_controller_tracking import (
    AppState,
    SortingControllerTrackingTests,
)


class SortingRecoveryTests(SortingControllerTrackingTests):

    def test_listening_failure_recovers_to_idle(self):
        self.controller._start_listening()
        self.controller.recover_to_idle("ERRORE MICROFONO")

        self.assertEqual(self.state_manager.state, AppState.IDLE)
        self.assertFalse(self.operator.processing)
        self.assertEqual(self.operator.errors, ["ERRORE MICROFONO"])

    def test_thinking_failure_clears_participant(self):
        self.controller.start_sorting(self.mario)
        self.controller.recover_to_idle("ERRORE DISPLAY PUBBLICO")

        self.assertEqual(self.state_manager.state, AppState.IDLE)
        self.assertIsNone(self.controller.current_participant)
        self.assertFalse(self.tracker.is_processed(self.mario))

    def test_stale_thinking_callback_is_ignored(self):
        self.controller.start_sorting(self.mario)
        stale_token = self.controller._flow_token
        self.controller.recover_to_idle()
        self.controller._start_reveal(stale_token)

        self.assertEqual(self.public.revealed_teams, [])
        self.assertEqual(self.state_manager.state, AppState.IDLE)


if __name__ == "__main__":
    unittest.main()
