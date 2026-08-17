import unittest

from PySide6.QtGui import QShortcut

from tests.operator_workflow_support import (
    close_operator_window,
    create_operator_window,
)


class OperatorNavigationTests(unittest.TestCase):

    def setUp(self):
        self.app, self.window, self.temporary, self.patches = (
            create_operator_window()
        )

    def tearDown(self):
        close_operator_window(self.window, self.temporary, self.patches)

    def test_event_page_is_opened_initially(self):
        self.assertEqual(self.window.current_page_name, "event")
        self.assertIs(
            self.window.page_stack.currentWidget(),
            self.window.event_page,
        )
        self.assertTrue(self.window.navigation_buttons["event"].isChecked())

    def test_navigation_reaches_all_persistent_pages(self):
        page_ids = {name: id(page) for name, page in self.window.pages.items()}
        for name in ("participants", "settings", "session", "event"):
            self.window.show_page(name)
            self.assertIs(
                self.window.page_stack.currentWidget(),
                self.window.pages[name],
            )
        self.assertEqual(
            page_ids,
            {name: id(page) for name, page in self.window.pages.items()},
        )

    def test_page_change_does_not_reset_event_state(self):
        self.window.search_input.setText("Mario")
        self.window.transcription_label.setText("Voce riconosciuta: Mario")
        self.window.show_page("settings")
        self.window.show_page("event")
        self.assertEqual(self.window.search_input.text(), "Mario")
        self.assertEqual(
            self.window.transcription_label.text(),
            "Voce riconosciuta: Mario",
        )

    def test_header_state_remains_visible_across_pages(self):
        self.window.update_global_state("REVEAL")
        self.window.show_page("session")
        self.assertEqual(self.window.header_state_label.text(), "REVEAL")
        self.assertTrue(self.window.header_state_label.isVisible())

    def test_no_space_listen_shortcut_exists(self):
        shortcuts = self.window.findChildren(QShortcut)
        keys = {shortcut.key().toString().casefold() for shortcut in shortcuts}
        self.assertNotIn("space", keys)


if __name__ == "__main__":
    unittest.main()
