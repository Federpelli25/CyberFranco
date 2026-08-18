import unittest

from PySide6.QtGui import QPalette

from tests.operator_workflow_support import (
    close_operator_window,
    create_operator_window,
)


class OperatorWorkflowTests(unittest.TestCase):

    def setUp(self):
        self.app, self.window, self.temporary, self.patches = (
            create_operator_window()
        )

    def tearDown(self):
        close_operator_window(self.window, self.temporary, self.patches)

    def test_technical_controls_are_on_settings_page(self):
        self.assertTrue(
            self.window.settings_page.isAncestorOf(self.window.microphone_combo)
        )
        self.assertTrue(
            self.window.settings_page.isAncestorOf(self.window.display_combo)
        )
        self.assertFalse(
            self.window.event_page.isAncestorOf(self.window.microphone_combo)
        )

    def test_session_and_tracking_controls_are_on_dedicated_pages(self):
        self.assertTrue(
            self.window.session_page.isAncestorOf(self.window.new_event_button)
        )
        self.assertTrue(
            self.window.participants_page.isAncestorOf(self.window.processed_list)
        )

    def test_history_and_complete_list_update(self):
        participant = self.window.participants[0]
        self.window.update_tracking_status(len(self.window.participants), 1,
                                           len(self.window.participants) - 1)
        self.window.update_processed_list([participant])
        self.assertEqual(self.window.processed_list.count(), 1)
        completed_rows = [
            self.window.all_participants_list.item(index).text()
            for index in range(self.window.all_participants_list.count())
        ]
        self.assertTrue(any("COMPLETATO" in row for row in completed_rows))
        self.assertIn("1 /", self.window.header_progress_label.text())

    def test_participant_filter_matches_team(self):
        team = self.window.participants[0]["squadra"]
        self.window.participants_filter_input.setText(team)
        self.assertGreater(self.window.all_participants_list.count(), 0)
        for index in range(self.window.all_participants_list.count()):
            self.assertIn(
                team.casefold(),
                self.window.all_participants_list.item(index).text().casefold(),
            )

    def test_participant_filter_and_rows_include_id(self):
        participant = self.window.participants[0]
        self.window.participants_filter_input.setText(participant["id"])
        self.assertGreater(self.window.all_participants_list.count(), 0)
        self.assertIn(
            participant["id"], self.window.all_participants_list.item(0).text()
        )

    def test_duplicate_manual_search_shows_distinct_ids(self):
        self.window.search_input.setText("Mario Rossi")
        rows = [
            self.window.results_list.item(index).text()
            for index in range(self.window.results_list.count())
        ]
        self.assertGreaterEqual(len(rows), 2)
        self.assertTrue(any("ID 001" in row for row in rows))
        self.assertTrue(any("ID 002" in row for row in rows))

    def test_enter_confirms_selected_candidate(self):
        participant = self.window.participants[0]
        self.window.search_input.setText(participant["nome_completo"])
        self.window.results_list.setCurrentRow(0)
        confirmed = []
        self.window.participant_confirmed.connect(confirmed.append)
        self.window.candidate_enter_shortcut.activated.emit()
        self.assertEqual(confirmed, [participant])

    def test_escape_clears_event_search(self):
        self.window.search_input.setText("Mario")
        self.window.event_escape_shortcut.activated.emit()
        self.assertEqual(self.window.search_input.text(), "")
        self.assertEqual(self.window.results_list.count(), 0)

    def test_ambiguity_selects_first_candidate_and_focuses_list(self):
        participant = self.window.participants[0]
        self.window._show_voice_candidates([
            {"participant": participant, "score": 80}
        ])
        self.app.processEvents()
        self.assertEqual(self.window.results_list.currentRow(), 0)
        self.assertTrue(self.window.results_list.hasFocus())

    def test_admin_controls_are_disabled_during_critical_flow(self):
        self.window.set_processing(True)
        self.assertFalse(self.window.new_event_button.isEnabled())
        self.assertFalse(self.window.microphone_combo.isEnabled())
        self.assertFalse(self.window.display_combo.isEnabled())
        self.assertFalse(self.window.undo_button.isEnabled())
        self.assertTrue(self.window.navigation_buttons["participants"].isEnabled())

    def test_dark_theme_explicitly_styles_contrast_states(self):
        style = self.window.styleSheet().casefold()
        self.assertEqual(
            self.window.palette().color(QPalette.WindowText).name(),
            "#f0f6fc",
        )
        for selector in (
            "qlineedit:focus",
            "placeholder-text-color",
            "qlistwidget::item:selected",
            "qpushbutton:disabled",
            "qwidget#adminheader qpushbutton:checked",
            "qcheckbox:disabled",
            "qgroupbox::title",
            "qlabel#stateprocessed",
            "qpushbutton#primaryactionbutton:disabled",
            "qpushbutton#dangeractionbutton:disabled",
        ):
            self.assertIn(selector, style)

    def test_already_processed_has_textual_header_state(self):
        participant = self.window.participants[0]
        self.window.show_already_processed(participant)
        self.assertEqual(
            self.window.header_state_label.text(),
            "GIÀ PROCESSATO",
        )
        self.assertEqual(
            self.window.header_state_label.objectName(),
            "stateProcessed",
        )
        self.assertIn("GIÀ ASSEGNATO", self.window.process_label.text())


if __name__ == "__main__":
    unittest.main()
