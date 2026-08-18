import logging

from PySide6.QtCore import (
    Qt,
    Signal,
    QThread,
)
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QComboBox,
    QGroupBox,
    QCheckBox,
    QMessageBox,
    QStackedWidget,
    QButtonGroup,
    QScrollArea,
)

from src.audio.audio_device_manager import (
    AudioDeviceError,
    AudioDeviceManager,
)
from src.audio.microphone_test_worker import (
    MicrophoneTestWorker,
)
from src.audio.speech_to_text import (
    SpeechModelError,
    SpeechToText,
)
from src.audio.voice_recognition_worker import (
    VoiceRecognitionWorker,
)
from src.data.participant_repository import (
    ParticipantRepository,
)
from src.config.settings_loader import (
    AppSettings,
    SettingsError,
    SettingsLoader,
)
from src.recognition.name_matcher import (
    NameMatcher,
)
from src.ui.display_manager import DisplayManager
from src.ui.operator_theme import apply_operator_theme


logger = logging.getLogger(__name__)


class OperatorWindow(QMainWindow):

    participant_confirmed = Signal(dict)

    listening_started = Signal()
    listening_ambiguous = Signal()
    listening_failed = Signal()

    undo_last_requested = Signal()
    reset_participant_requested = Signal(dict)
    public_display_changed = Signal(int, bool)
    new_event_requested = Signal()

    def __init__(
        self,
        settings: AppSettings,
        settings_loader: SettingsLoader,
        display_manager: DisplayManager | None = None,
    ):
        super().__init__()

        self.settings = settings
        self.settings_loader = settings_loader
        self.display_manager = display_manager or DisplayManager()
        self.preferred_display_index = settings.public_display_monitor
        self.audio_device_manager = AudioDeviceManager()
        self.current_microphone_device = (
            settings.microphone_device
        )
        self.input_devices = []
        self.speech_ready = False

        self.setWindowTitle(
            "CyberFranco - Operator Console"
        )

        self.resize(
            1000,
            900,
        )

        self.repository = (
            ParticipantRepository(
                settings.resolve_participants_file()
            )
        )

        self.participants = (
            self.repository.load()
        )

        self.matcher = NameMatcher(
            self.participants
        )

        self.hotwords = ", ".join(
            participant["nome_completo"]
            for participant
            in self.participants
        )

        self.selected_participant = None
        self.selected_processed_participant = None
        self._processed_participant_keys = set()

        self.processing = False
        self.voice_processing = False
        self.microphone_test_processing = False

        self.voice_thread = None
        self.voice_worker = None
        self.microphone_test_thread = None
        self.microphone_test_worker = None

        self._build_ui()
        self._connect_events()

        self._refresh_displays(initial_load=True)
        application = self.display_manager.application
        if application is not None:
            application.screenAdded.connect(self._screen_configuration_changed)
            application.screenRemoved.connect(self._screen_configuration_changed)

        self._refresh_audio_devices(initial_load=True)
        self._load_speech_model()

    def _load_speech_model(self):
        self.process_label.setText(
            "STATO: CARICAMENTO WHISPER"
        )

        self.listen_button.setEnabled(
            False
        )

        try:
            self.speech_to_text = SpeechToText(
                model_path=(
                    self.settings
                    .resolve_whisper_model_path()
                ),
                device=self.settings.whisper_device,
                compute_type=(
                    self.settings.whisper_compute_type
                ),
                language=self.settings.language,
            )
        except SpeechModelError as exc:
            logger.warning("Whisper model unavailable: %s", exc)
            self.speech_to_text = None
            self.speech_ready = False
            self.process_label.setText(
                "STATO VOCALE: MODELLO WHISPER "
                "NON DISPONIBILE"
            )
            self.transcription_label.setText(str(exc))
            self.transcription_label.setWordWrap(True)
            self._update_audio_controls()
            return

        self.process_label.setText(
            "STATO: PRONTO"
        )
        self.speech_ready = True
        self._update_audio_controls()

    def _build_ui(self):
        central_widget = QWidget()

        self.setCentralWidget(
            central_widget
        )

        main_layout = QVBoxLayout(
            central_widget
        )

        title = QLabel(
            "CyberFranco"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            """
            font-size: 32px;
            font-weight: bold;
            padding: 15px;
            """
        )

        self.file_label = QLabel(
            "File partecipanti: "
            f"{self.repository.file_path.name}"
        )

        self.file_label.setAlignment(
            Qt.AlignCenter
        )

        self.status_label = QLabel("")

        self.status_label.setAlignment(
            Qt.AlignCenter
        )

        self.status_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 6px;
            }
            """
        )

        self.process_label = QLabel(
            "STATO: PRONTO"
        )

        self.process_label.setAlignment(
            Qt.AlignCenter
        )

        self.transcription_label = QLabel(
            "Voce riconosciuta: -"
        )

        self.transcription_label.setAlignment(
            Qt.AlignCenter
        )

        self.listen_button = QPushButton(
            "ASCOLTA"
        )

        self.listen_button.setStyleSheet(
            """
            QPushButton {
                font-size: 24px;
                font-weight: bold;
                padding: 15px;
            }
            """
        )

        microphone_group = QGroupBox(
            "MICROFONO"
        )
        microphone_layout = QVBoxLayout(
            microphone_group
        )

        self.microphone_combo = QComboBox()
        self.microphone_combo.setMinimumHeight(38)

        microphone_button_layout = QHBoxLayout()
        self.refresh_microphones_button = QPushButton(
            "AGGIORNA DISPOSITIVI"
        )
        self.test_microphone_button = QPushButton(
            "TEST MICROFONO"
        )
        microphone_button_layout.addWidget(
            self.refresh_microphones_button
        )
        microphone_button_layout.addWidget(
            self.test_microphone_button
        )

        self.active_microphone_label = QLabel(
            "Microfono attivo: caricamento..."
        )
        self.active_microphone_label.setWordWrap(True)

        self.microphone_test_label = QLabel(
            "Test microfono: non eseguito"
        )
        self.microphone_test_label.setWordWrap(True)

        microphone_layout.addWidget(
            self.microphone_combo
        )
        microphone_layout.addLayout(
            microphone_button_layout
        )
        microphone_layout.addWidget(
            self.active_microphone_label
        )
        microphone_layout.addWidget(
            self.microphone_test_label
        )

        display_group = QGroupBox("DISPLAY PUBBLICO")
        display_layout = QVBoxLayout(display_group)
        self.display_combo = QComboBox()
        self.display_combo.setMinimumHeight(38)
        self.refresh_displays_button = QPushButton("AGGIORNA MONITOR")
        self.public_display_fullscreen_checkbox = QCheckBox("Fullscreen")
        self.public_display_fullscreen_checkbox.setChecked(
            self.settings.public_display_fullscreen
        )
        self.apply_display_button = QPushButton(
            "APRI / RIPOSIZIONA DISPLAY"
        )
        self.display_status_label = QLabel("Rilevamento monitor...")
        self.display_status_label.setWordWrap(True)
        display_layout.addWidget(self.display_combo)
        display_layout.addWidget(self.refresh_displays_button)
        display_layout.addWidget(self.public_display_fullscreen_checkbox)
        display_layout.addWidget(self.apply_display_button)
        display_layout.addWidget(self.display_status_label)

        self.public_display_shortcut = QShortcut(
            QKeySequence("Ctrl+Shift+F"),
            self,
        )

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Scrivi nome o cognome..."
        )

        self.search_input.setStyleSheet(
            """
            QLineEdit {
                font-size: 22px;
                padding: 12px;
            }
            """
        )

        self.results_list = QListWidget()
        self.results_list.setMinimumHeight(220)

        self.selection_label = QLabel(
            "Nessun partecipante selezionato"
        )

        self.selection_label.setAlignment(
            Qt.AlignCenter
        )

        button_layout = QHBoxLayout()

        self.clear_button = QPushButton(
            "Pulisci"
        )

        self.confirm_button = QPushButton(
            "Conferma"
        )

        self.confirm_button.setEnabled(
            False
        )

        button_layout.addWidget(
            self.clear_button
        )

        button_layout.addWidget(
            self.confirm_button
        )

        processed_title = QLabel(
            "Partecipanti già passati"
        )

        processed_title.setAlignment(
            Qt.AlignCenter
        )

        processed_title.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: bold;
                padding-top: 15px;
            }
            """
        )

        self.processed_list = QListWidget()
        self.processed_list.setMinimumHeight(180)

        self.processed_list.setStyleSheet(
            """
            QListWidget {
                font-size: 18px;
            }

            QListWidget::item {
                padding: 8px;
            }
            """
        )

        tracking_button_layout = (
            QHBoxLayout()
        )

        self.undo_button = QPushButton(
            "ANNULLA ULTIMA"
        )

        self.undo_button.setEnabled(
            False
        )

        self.reset_selected_button = (
            QPushButton(
                "RESET SELEZIONATO"
            )
        )

        self.reset_selected_button.setEnabled(
            False
        )

        tracking_button_layout.addWidget(
            self.undo_button
        )

        tracking_button_layout.addWidget(
            self.reset_selected_button
        )

        self.new_event_button = QPushButton("NUOVO EVENTO")
        self.new_event_button.setStyleSheet(
            "QPushButton { color: #b00020; font-weight: bold; padding: 10px; }"
        )

        main_layout.addWidget(
            title
        )

        main_layout.addWidget(
            self.file_label
        )

        main_layout.addWidget(
            self.status_label
        )

        main_layout.addWidget(
            self.process_label
        )

        main_layout.addWidget(
            self.transcription_label
        )

        main_layout.addWidget(
            microphone_group
        )

        main_layout.addWidget(display_group)

        main_layout.addWidget(
            self.listen_button
        )

        main_layout.addWidget(
            self.search_input
        )

        main_layout.addWidget(
            self.results_list
        )

        main_layout.addWidget(
            self.selection_label
        )

        main_layout.addLayout(
            button_layout
        )

        main_layout.addWidget(
            processed_title
        )

        main_layout.addWidget(
            self.processed_list
        )

        main_layout.addLayout(
            tracking_button_layout
        )

        main_layout.addWidget(self.new_event_button)

        self._apply_multipage_layout(
            microphone_group,
            display_group,
        )

    def _apply_multipage_layout(self, microphone_group, display_group):
        for widget in (
            self.listen_button,
            self.search_input,
            self.processed_list,
            self.new_event_button,
        ):
            widget.setStyleSheet("")
        self.listen_button.setObjectName("primaryActionButton")
        self.new_event_button.setObjectName("dangerActionButton")
        self.process_label.setObjectName("operatorMessage")
        self.resize(1280, 800)
        self.setMinimumSize(960, 640)

        central_widget = QWidget()
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("adminHeader")
        header_layout = QVBoxLayout(header)
        header_top = QHBoxLayout()
        header_title = QLabel("CYBERFRANCO")
        header_title.setObjectName("headerTitle")
        self.header_state_label = QLabel("PRONTO")
        self.header_state_label.setObjectName("stateReady")
        self.header_progress_label = QLabel("0 / 0 completati")
        header_top.addWidget(header_title)
        header_top.addStretch()
        header_top.addWidget(self.header_progress_label)
        header_top.addWidget(self.header_state_label)

        navigation_layout = QHBoxLayout()
        self.navigation_group = QButtonGroup(self)
        self.navigation_group.setExclusive(True)
        self.navigation_buttons = {}
        for page_name, label in (
            ("event", "EVENTO"),
            ("participants", "PARTECIPANTI"),
            ("settings", "IMPOSTAZIONI"),
            ("session", "SESSIONE"),
        ):
            button = QPushButton(label)
            button.setCheckable(True)
            button.clicked.connect(
                lambda _checked=False, name=page_name: self.show_page(name)
            )
            self.navigation_group.addButton(button)
            self.navigation_buttons[page_name] = button
            navigation_layout.addWidget(button)

        header_layout.addLayout(header_top)
        header_layout.addLayout(navigation_layout)
        root_layout.addWidget(header)

        self.page_stack = QStackedWidget()
        root_layout.addWidget(self.page_stack, 1)

        self.event_page, event_layout = self._create_scroll_page("EVENTO")
        self.event_progress_label = QLabel("Completati: 0 / 0   •   Rimanenti: 0")
        self.event_progress_label.setObjectName("progressLabel")
        self.selected_team_label = QLabel("Squadra: -")
        self.selected_team_label.setAlignment(Qt.AlignCenter)
        event_buttons = QHBoxLayout()
        event_buttons.addWidget(self.clear_button)
        event_buttons.addWidget(self.confirm_button)
        event_layout.addWidget(self.event_progress_label)
        event_layout.addWidget(self.process_label)
        event_layout.addWidget(self.listen_button)
        event_layout.addWidget(QLabel("Trascrizione"))
        event_layout.addWidget(self.transcription_label)
        event_layout.addWidget(QLabel("Ricerca manuale"))
        event_layout.addWidget(self.search_input)
        event_layout.addWidget(QLabel("Suggerimenti"))
        event_layout.addWidget(self.results_list, 1)
        event_layout.addWidget(self.selection_label)
        event_layout.addWidget(self.selected_team_label)
        event_layout.addLayout(event_buttons)

        self.participants_page, participants_layout = self._create_scroll_page(
            "PARTECIPANTI"
        )
        self.participants_filter_input = QLineEdit()
        self.participants_filter_input.setPlaceholderText("Cerca partecipante...")
        self.all_participants_list = QListWidget()
        self.all_participants_list.setMinimumHeight(220)
        self.participants_message_label = QLabel("")
        tracking_buttons = QHBoxLayout()
        tracking_buttons.addWidget(self.undo_button)
        tracking_buttons.addWidget(self.reset_selected_button)
        participants_layout.addWidget(self.status_label)
        participants_layout.addWidget(QLabel("Elenco completo"))
        participants_layout.addWidget(self.participants_filter_input)
        participants_layout.addWidget(self.all_participants_list, 1)
        participants_layout.addWidget(QLabel("Storico completati"))
        participants_layout.addWidget(self.processed_list, 1)
        participants_layout.addLayout(tracking_buttons)
        participants_layout.addWidget(self.participants_message_label)

        self.settings_page, settings_layout = self._create_scroll_page(
            "IMPOSTAZIONI"
        )
        settings_layout.addWidget(microphone_group)
        settings_layout.addWidget(display_group)
        settings_layout.addStretch()

        self.session_page, session_layout = self._create_scroll_page(
            "SESSIONE EVENTO"
        )
        self.session_status_label = QLabel(
            "Persistenza: "
            + ("ATTIVA" if self.settings.session_persistence_enabled else "IN MEMORIA")
        )
        self.session_file_label = QLabel(
            f"File sessione: {self.settings.session_file}"
        )
        self.session_details_label = QLabel("Sessione non ancora inizializzata")
        self.session_details_label.setWordWrap(True)
        self.session_action_label = QLabel("")
        session_layout.addWidget(self.session_status_label)
        session_layout.addWidget(self.session_file_label)
        session_layout.addWidget(self.file_label)
        session_layout.addWidget(self.session_details_label)
        session_layout.addWidget(self.session_action_label)
        session_layout.addStretch()
        session_layout.addWidget(self.new_event_button)

        self.pages = {
            "event": self.event_page,
            "participants": self.participants_page,
            "settings": self.settings_page,
            "session": self.session_page,
        }
        for page in self.pages.values():
            self.page_stack.addWidget(page)

        self.event_escape_shortcut = QShortcut(
            QKeySequence(Qt.Key_Escape), self.event_page
        )
        self.event_escape_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self.event_escape_shortcut.activated.connect(self._clear_search)
        self.candidate_enter_shortcut = QShortcut(
            QKeySequence(Qt.Key_Return), self.results_list
        )
        self.candidate_enter_shortcut.setContext(Qt.WidgetShortcut)
        self.candidate_enter_shortcut.activated.connect(
            self._confirm_or_select_first
        )

        self.participants_filter_input.textChanged.connect(
            self._refresh_all_participants
        )
        self.setCentralWidget(central_widget)
        apply_operator_theme(self)
        self.show_page("event")
        self._refresh_all_participants()

    def _create_scroll_page(self, title_text: str):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(14)
        title = QLabel(title_text)
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        scroll.setWidget(content)
        return scroll, layout

    def show_page(self, page_name: str):
        page = self.pages.get(page_name)
        if page is None:
            return
        self.page_stack.setCurrentWidget(page)
        self.navigation_buttons[page_name].setChecked(True)
        self.current_page_name = page_name
        logger.debug("Operator page changed: %s", page_name)
        if page_name == "event" and not self.processing:
            self.search_input.setFocus()

    def _connect_events(self):
        self.listen_button.clicked.connect(
            self._start_voice_recognition
        )

        self.microphone_combo.currentIndexChanged.connect(
            self._microphone_selection_changed
        )

        self.refresh_microphones_button.clicked.connect(
            self._refresh_audio_devices
        )

        self.test_microphone_button.clicked.connect(
            self._start_microphone_test
        )

        self.display_combo.currentIndexChanged.connect(
            self._display_selection_changed
        )
        self.refresh_displays_button.clicked.connect(
            self._refresh_displays
        )
        self.public_display_fullscreen_checkbox.toggled.connect(
            self._display_fullscreen_changed
        )
        self.apply_display_button.clicked.connect(
            self._manual_apply_public_display
        )
        self.public_display_shortcut.activated.connect(
            self._emergency_exit_public_fullscreen
        )

        self.search_input.textChanged.connect(
            self._update_results
        )

        self.results_list.itemSelectionChanged.connect(
            self._select_current_result
        )

        self.results_list.itemDoubleClicked.connect(
            self._confirm_item
        )

        self.search_input.returnPressed.connect(
            self._confirm_or_select_first
        )

        self.confirm_button.clicked.connect(
            self._confirm_selection
        )

        self.clear_button.clicked.connect(
            self._clear_search
        )

        self.processed_list.itemSelectionChanged.connect(
            self._select_processed_participant
        )

        self.undo_button.clicked.connect(
            self.undo_last_requested.emit
        )

        self.reset_selected_button.clicked.connect(
            self._request_processed_reset
        )

        self.new_event_button.clicked.connect(
            self._confirm_new_event
        )

    def _refresh_displays(
        self,
        initial_load: bool = False,
        force: bool = False,
    ):
        if self.processing and not initial_load and not force:
            return

        requested = self.preferred_display_index
        screens = self.display_manager.list_screens()
        resolved = self.display_manager.resolve_screen(requested)

        self.display_combo.blockSignals(True)
        self.display_combo.clear()
        for screen in screens:
            self.display_combo.addItem(
                self.display_manager.format_screen(screen),
                screen["index"],
            )

        if resolved is None:
            self.display_status_label.setText("NESSUN MONITOR DISPONIBILE")
            self.display_combo.blockSignals(False)
            self._update_display_controls()
            return

        selected_index = self.display_combo.findData(resolved["index"])
        self.display_combo.setCurrentIndex(max(selected_index, 0))
        self.display_combo.blockSignals(False)

        if len(screens) == 1:
            self.show_warning("È DISPONIBILE UN SOLO MONITOR")
            self.display_status_label.setText(
                "È disponibile un solo monitor. Usa la modalità finestra "
                "per mantenere visibile la console."
            )
        else:
            self.display_status_label.setText(
                f"Monitor rilevati: {len(screens)}"
            )

        if resolved["index"] != requested:
            logger.warning("Public display fallback to primary screen")

        if not initial_load:
            self._apply_public_display(force=force, persist=False)
        self._update_display_controls()

    def _screen_configuration_changed(self, *_):
        logger.warning("Screen configuration changed")
        self._refresh_displays(initial_load=False, force=True)

    def _display_selection_changed(self, index: int):
        if index < 0 or self.processing:
            return
        self.preferred_display_index = int(self.display_combo.currentData())
        self._apply_public_display()

    def _display_fullscreen_changed(self, _checked: bool):
        if self.processing:
            return
        self._apply_public_display()

    def _manual_apply_public_display(self):
        self._apply_public_display()

    def _apply_public_display(
        self,
        force: bool = False,
        persist: bool = True,
    ):
        if (
            (self.processing and not force)
            or self.display_combo.currentIndex() < 0
        ):
            return
        screen_index = int(self.display_combo.currentData())
        fullscreen = self.public_display_fullscreen_checkbox.isChecked()
        if persist:
            self._save_public_display_settings()
        logger.info(
            "Public display selected: screen=%d fullscreen=%s",
            screen_index,
            fullscreen,
        )
        self.public_display_changed.emit(screen_index, fullscreen)

    def _save_public_display_settings(self):
        if self.display_combo.currentIndex() < 0:
            return
        try:
            self.settings_loader.save_public_display(
                self.preferred_display_index,
                self.public_display_fullscreen_checkbox.isChecked(),
            )
        except SettingsError as exc:
            logger.exception("Public display settings could not be saved")
            self.display_status_label.setText(
                f"Preferenza display non salvata: {exc}"
            )

    def _emergency_exit_public_fullscreen(self):
        logger.warning("Emergency public fullscreen exit requested")
        self.public_display_fullscreen_checkbox.blockSignals(True)
        self.public_display_fullscreen_checkbox.setChecked(False)
        self.public_display_fullscreen_checkbox.blockSignals(False)
        if self.display_combo.currentIndex() >= 0:
            screen_index = int(self.display_combo.currentData())
            self._save_public_display_settings()
            self.public_display_changed.emit(screen_index, False)

    def _update_display_controls(self):
        enabled = self.display_combo.count() > 0 and not self.processing
        self.display_combo.setEnabled(enabled)
        self.refresh_displays_button.setEnabled(not self.processing)
        self.public_display_fullscreen_checkbox.setEnabled(enabled)
        self.apply_display_button.setEnabled(enabled)

    def _refresh_audio_devices(
        self,
        initial_load: bool = False,
    ):
        if (
            self.processing
            or self.voice_processing
            or self.microphone_test_processing
        ):
            return

        requested_device = self.current_microphone_device

        try:
            devices = (
                self.audio_device_manager
                .list_input_devices()
            )
            default_device = (
                self.audio_device_manager
                .get_default_input_device()
            )
        except AudioDeviceError as exc:
            logger.exception("Audio device refresh failed")
            self.input_devices = []
            self.microphone_combo.clear()
            self.active_microphone_label.setText(
                "NESSUN MICROFONO DISPONIBILE"
            )
            self.microphone_test_label.setText(str(exc))
            self._update_audio_controls()
            return

        self.input_devices = devices
        self.microphone_combo.blockSignals(True)
        self.microphone_combo.clear()

        if not devices:
            self.current_microphone_device = None
            self.microphone_combo.addItem(
                "NESSUN MICROFONO DISPONIBILE",
                None,
            )
            self.active_microphone_label.setText(
                "NESSUN MICROFONO DISPONIBILE"
            )
            self.microphone_test_label.setText(
                "Collega un microfono e premi "
                "AGGIORNA DISPOSITIVI."
            )
            self.microphone_combo.blockSignals(False)
            self._update_audio_controls()
            return

        if default_device is not None:
            self.microphone_combo.addItem(
                "Predefinito di sistema — "
                + self.audio_device_manager.format_device_name(
                    default_device
                ),
                None,
            )

        for device in devices:
            label = self.audio_device_manager.format_device_name(
                device
            )
            self.microphone_combo.addItem(
                f"{label} — Device {device['id']}",
                device["id"],
            )

        selected_index = self._find_microphone_combo_index(
            requested_device
        )

        if requested_device is not None and selected_index < 0:
            self.current_microphone_device = None
            selected_index = self._find_microphone_combo_index(None)
            self.microphone_test_label.setText(
                "Il microfono salvato non è disponibile. "
                "È stato selezionato il dispositivo predefinito."
            )
            self._save_microphone_selection(None)

        if selected_index < 0:
            selected_index = 0
            self.current_microphone_device = (
                self.microphone_combo.itemData(0)
            )
            self._save_microphone_selection(
                self.current_microphone_device
            )

        self.microphone_combo.setCurrentIndex(selected_index)
        self.microphone_combo.blockSignals(False)
        self.current_microphone_device = (
            self.microphone_combo.currentData()
        )
        self._update_active_microphone_label()

        if not initial_load:
            self.microphone_test_label.setText(
                "Elenco dispositivi aggiornato."
            )

        self._update_audio_controls()

    def _find_microphone_combo_index(
        self,
        device_id: int | None,
    ) -> int:
        for index in range(self.microphone_combo.count()):
            if self.microphone_combo.itemData(index) == device_id:
                return index

        return -1

    def _microphone_selection_changed(self, index: int):
        if index < 0:
            return

        if (
            self.processing
            or self.voice_processing
            or self.microphone_test_processing
        ):
            return

        self.current_microphone_device = (
            self.microphone_combo.itemData(index)
        )
        self._save_microphone_selection(
            self.current_microphone_device
        )
        self._update_active_microphone_label()
        self.microphone_test_label.setText(
            "Microfono selezionato. Esegui un test prima "
            "dell'evento."
        )
        self._update_audio_controls()

    def _save_microphone_selection(
        self,
        device_id: int | None,
    ):
        try:
            self.settings_loader.save_microphone_device(
                device_id
            )
        except SettingsError as exc:
            logger.exception("Microphone selection could not be saved")
            self.microphone_test_label.setText(
                f"Scelta attiva ma non salvata: {exc}"
            )
            return

        logger.info("Selected microphone: device_id=%s", device_id)

    def _update_active_microphone_label(self):
        if self.current_microphone_device is None:
            try:
                device = (
                    self.audio_device_manager
                    .get_default_input_device()
                )
            except AudioDeviceError:
                device = None
        else:
            try:
                device = self.audio_device_manager.get_device(
                    self.current_microphone_device
                )
            except AudioDeviceError:
                device = None

        if device is None:
            self.active_microphone_label.setText(
                "NESSUN MICROFONO DISPONIBILE"
            )
            return

        label = self.audio_device_manager.format_device_name(
            device
        )
        mode = (
            "predefinito di sistema"
            if self.current_microphone_device is None
            else f"Device {device['id']}"
        )
        self.active_microphone_label.setText(
            f"Microfono attivo: {label}\n{mode}"
        )

    def _start_microphone_test(self):
        if (
            self.processing
            or self.voice_processing
            or self.microphone_test_processing
            or not self.input_devices
        ):
            return

        self.microphone_test_processing = True
        self.microphone_test_label.setText(
            "TEST MICROFONO IN CORSO... Parla normalmente."
        )
        self._update_audio_controls()

        self.microphone_test_thread = QThread()
        self.microphone_test_worker = MicrophoneTestWorker(
            microphone_device=self.current_microphone_device,
            duration_seconds=2.0,
        )
        self.microphone_test_worker.moveToThread(
            self.microphone_test_thread
        )
        self.microphone_test_thread.started.connect(
            self.microphone_test_worker.run
        )
        self.microphone_test_worker.completed.connect(
            self._microphone_test_completed
        )
        self.microphone_test_worker.failed.connect(
            self._microphone_test_failed
        )
        self.microphone_test_worker.completed.connect(
            self.microphone_test_thread.quit
        )
        self.microphone_test_worker.failed.connect(
            self.microphone_test_thread.quit
        )
        self.microphone_test_thread.finished.connect(
            self.microphone_test_worker.deleteLater
        )
        self.microphone_test_thread.finished.connect(
            self.microphone_test_thread.deleteLater
        )
        self.microphone_test_thread.finished.connect(
            self._microphone_test_thread_finished
        )
        self.microphone_test_thread.start()

    def _microphone_test_completed(self, result: dict):
        self.microphone_test_processing = False
        self.microphone_test_label.setText(
            f"{result['status']} — "
            f"Peak: {result['peak']:.3f} — "
            f"RMS: {result['rms']:.3f}"
        )
        self._update_audio_controls()

    def _microphone_test_failed(self, error_message: str):
        self.microphone_test_processing = False
        self.microphone_test_label.setText(
            "TEST MICROFONO FALLITO. "
            "Aggiorna i dispositivi e riprova."
        )
        self._update_audio_controls()

    def _microphone_test_thread_finished(self):
        if self.microphone_test_processing:
            logger.error("Microphone test thread ended without a result")
            self.microphone_test_processing = False
            self.microphone_test_label.setText("TEST MICROFONO FALLITO")
            self._update_audio_controls()
        self.microphone_test_worker = None
        self.microphone_test_thread = None

    def _update_audio_controls(self):
        busy = (
            self.processing
            or self.voice_processing
            or self.microphone_test_processing
        )
        has_microphone = bool(self.input_devices)

        self.microphone_combo.setEnabled(
            has_microphone and not busy
        )
        self.refresh_microphones_button.setEnabled(
            not busy
        )
        self.test_microphone_button.setEnabled(
            has_microphone and not busy
        )
        self.listen_button.setEnabled(
            has_microphone
            and self.speech_ready
            and not busy
        )

    def update_tracking_status(
        self,
        total: int,
        processed: int,
        remaining: int,
    ):
        self.status_label.setText(
            f"Totali: {total}   |   "
            f"Completati: {processed}   |   "
            f"Rimanenti: {remaining}"
        )
        self.event_progress_label.setText(
            f"Completati: {processed} / {total}   •   Rimanenti: {remaining}"
        )
        self.header_progress_label.setText(
            f"{processed} / {total} completati"
        )

        self.undo_button.setEnabled(
            processed > 0 and not self.processing
        )

    def update_processed_list(
        self,
        participants: list[dict],
    ):
        self.processed_list.clear()

        self.selected_processed_participant = None

        self.reset_selected_button.setEnabled(
            False
        )
        self._processed_participant_keys = {
            str(participant.get("id", "")).strip()
            for participant in participants
        }

        for participant in reversed(
            participants
        ):
            item = QListWidgetItem(
                f"ID {participant['id']} — {participant['nome_completo']} "
                f"→ {participant['squadra']}"
            )

            item.setData(
                Qt.UserRole,
                participant,
            )

            self.processed_list.addItem(
                item
            )
        self._refresh_all_participants()

    def _refresh_all_participants(self, *_):
        if not hasattr(self, "all_participants_list"):
            return
        query = self.participants_filter_input.text().strip().casefold()
        self.all_participants_list.clear()
        for participant in self.participants:
            searchable = " ".join((
                str(participant.get("nome", "")),
                str(participant.get("cognome", "")),
                str(participant.get("nome_completo", "")),
                str(participant.get("squadra", "")),
                str(participant.get("id", "")),
            )).casefold()
            if query and query not in searchable:
                continue
            completed = (
                str(participant.get("id", "")).strip()
                in self._processed_participant_keys
            )
            status = "COMPLETATO" if completed else "DA PROCESSARE"
            self.all_participants_list.addItem(
                f"{participant['id']} | {participant['nome_completo']} | "
                f"{participant['squadra']} | {status}"
            )

    def _select_processed_participant(
        self,
    ):
        item = (
            self.processed_list.currentItem()
        )

        if not item:
            self.selected_processed_participant = None

            self.reset_selected_button.setEnabled(
                False
            )

            return

        self.selected_processed_participant = (
            item.data(
                Qt.UserRole
            )
        )

        self.reset_selected_button.setEnabled(
            True
        )

    def _request_processed_reset(
        self,
    ):
        if not self.selected_processed_participant:
            return

        self.reset_participant_requested.emit(
            self.selected_processed_participant
        )

    def show_already_processed(
        self,
        participant: dict,
    ):
        self.set_processing(False)
        self.process_label.setText(
            "STATO: GIÀ ASSEGNATO"
        )

        self.selection_label.setText(
            f"{participant['nome_completo']} "
            "è già stato processato"
        )
        self.selected_team_label.setText(
            f"Squadra: {participant['squadra']}"
        )

        self.update_global_state("PROCESSED")

        self.search_input.setFocus()

    def show_tracking_message(
        self,
        message: str,
    ):
        self.process_label.setText(
            message
        )
        self.participants_message_label.setText(message)
        self.session_action_label.setText(message)

    def _confirm_new_event(self):
        if self.processing or self.voice_processing:
            return
        message_box = QMessageBox(self)
        message_box.setIcon(QMessageBox.Warning)
        message_box.setWindowTitle("Nuovo evento")
        message_box.setText(
            "Vuoi iniziare un nuovo evento?\n\n"
            "Tutti i partecipanti verranno marcati come non ancora "
            "processati.\nIl file Excel non verrà modificato."
        )
        cancel_button = message_box.addButton(
            "Annulla",
            QMessageBox.RejectRole,
        )
        confirm_button = message_box.addButton(
            "Nuovo evento",
            QMessageBox.DestructiveRole,
        )
        message_box.setDefaultButton(cancel_button)
        message_box.exec()
        if message_box.clickedButton() is confirm_button:
            self.new_event_requested.emit()

    def show_status(self, message: str):
        self.process_label.setText(message)

    def show_warning(self, message: str):
        logger.warning("Operator warning: %s", message)
        self.show_status(message)

    def show_error(self, message: str):
        logger.error("Operator error: %s", message)
        self.update_global_state("ERROR")
        self.show_status(message)

    def update_global_state(self, state):
        state_value = getattr(state, "value", state)
        states = {
            "IDLE": ("PRONTO", "stateReady"),
            "LISTENING": ("ASCOLTO", "stateListening"),
            "AWAITING_CONFIRMATION": ("DA CONFERMARE", "stateConfirm"),
            "THINKING": ("ELABORAZIONE", "stateProcessing"),
            "REVEAL": ("REVEAL", "stateReveal"),
            "ERROR": ("ERRORE", "stateError"),
            "PROCESSED": ("GIÀ PROCESSATO", "stateProcessed"),
        }
        text, object_name = states.get(
            str(state_value),
            (str(state_value), "stateReady"),
        )
        self.header_state_label.setText(text)
        self.header_state_label.setObjectName(object_name)
        self.header_state_label.style().unpolish(self.header_state_label)
        self.header_state_label.style().polish(self.header_state_label)

    def update_session_info(self, session: dict | None, blocked: bool = False):
        if not self.settings.session_persistence_enabled:
            self.session_status_label.setText("Persistenza: IN MEMORIA")
            self.session_details_label.setText("Nessun file sessione utilizzato.")
            return
        status = "NON COMPATIBILE" if blocked else "ATTIVA"
        self.session_status_label.setText(f"Persistenza: {status}")
        if session is None:
            self.session_details_label.setText("Sessione non disponibile.")
            return
        self.session_details_label.setText(
            f"Creata: {session.get('created_at', '-')}\n"
            f"Ultimo aggiornamento: {session.get('updated_at', '-')}\n"
            f"Completati salvati: {len(session.get('processed', []))}\n"
            f"Compatibilità: {'DA RISOLVERE' if blocked else 'VALIDA'}"
        )

    def _start_voice_recognition(self):
        if (
            self.processing
            or self.voice_processing
            or self.microphone_test_processing
        ):
            return

        if not self.input_devices:
            logger.warning("Listening unavailable: no microphone")
            self.process_label.setText(
                "NESSUN MICROFONO DISPONIBILE"
            )
            self._update_audio_controls()
            return

        if not self.speech_ready or self.speech_to_text is None:
            self.show_warning("MODELLO WHISPER NON DISPONIBILE")
            self._update_audio_controls()
            return

        if self.current_microphone_device is not None:
            try:
                device_available = (
                    self.audio_device_manager
                    .is_device_available(
                        self.current_microphone_device
                    )
                )
            except AudioDeviceError:
                logger.exception("Selected microphone availability check failed")
                device_available = False

            if not device_available:
                logger.warning(
                    "Configured microphone unavailable: device_id=%s",
                    self.current_microphone_device,
                )
                self.process_label.setText(
                    "Microfono non disponibile. "
                    "Seleziona un altro dispositivo."
                )
                self.microphone_test_label.setText(
                    "Il dispositivo selezionato è stato "
                    "scollegato. Premi AGGIORNA DISPOSITIVI."
                )
                self._update_audio_controls()
                return

        self.voice_processing = True
        logger.info(
            "Voice recognition started: device_id=%s",
            self.current_microphone_device,
        )
        self._update_audio_controls()

        self.transcription_label.setText(
            "Voce riconosciuta: ascolto..."
        )

        self.process_label.setText(
            "STATO: ASCOLTO"
        )

        self.listen_button.setEnabled(
            False
        )

        self.search_input.setEnabled(
            False
        )

        self.results_list.setEnabled(
            False
        )

        self.clear_button.setEnabled(
            False
        )

        self.confirm_button.setEnabled(
            False
        )

        self.listening_started.emit()

        self.voice_thread = QThread()

        self.voice_worker = (
            VoiceRecognitionWorker(
                speech_to_text=
                    self.speech_to_text,
                hotwords=
                    self.hotwords,
                duration_seconds=(
                    self.settings
                    .recording_duration_seconds
                ),
                microphone_device=(
                    self.current_microphone_device
                ),
            )
        )

        self.voice_worker.moveToThread(
            self.voice_thread
        )

        self.voice_thread.started.connect(
            self.voice_worker.run
        )

        self.voice_worker.completed.connect(
            self._voice_recognition_completed
        )

        self.voice_worker.failed.connect(
            self._voice_recognition_failed
        )

        self.voice_worker.completed.connect(
            self.voice_thread.quit
        )

        self.voice_worker.failed.connect(
            self.voice_thread.quit
        )

        self.voice_thread.finished.connect(
            self.voice_worker.deleteLater
        )

        self.voice_thread.finished.connect(
            self.voice_thread.deleteLater
        )
        self.voice_thread.finished.connect(
            self._voice_thread_finished
        )

        self.voice_thread.start()

    def _voice_thread_finished(self):
        if self.voice_processing:
            logger.error("Voice thread ended without a result")
            self.voice_processing = False
            self.show_error("ERRORE DI RICONOSCIMENTO")
            self.listening_failed.emit()
            self._enable_manual_controls()
        self.voice_worker = None
        self.voice_thread = None

    def _voice_recognition_completed(
        self,
        transcription: str,
    ):
        self.voice_processing = False

        if not transcription:
            logger.warning("Voice recognition completed without text")
            self.transcription_label.setText(
                "Voce riconosciuta: nessun testo"
            )

            self.listening_failed.emit()

            self._enable_manual_controls()
            return

        self.transcription_label.setText(
            f"Voce riconosciuta: "
            f"{transcription}"
        )

        result = self.matcher.resolve(
            transcription
        )

        if (
            result["status"]
            == NameMatcher.STATUS_MATCH
        ):
            best_match = result[
                "best_match"
            ]

            participant = best_match[
                "participant"
            ]
            logger.info(
                "Voice participant confirmed: %s",
                participant["nome_completo"],
            )

            self.selected_participant = (
                participant
            )

            self.selection_label.setText(
                f"{participant['nome_completo']} "
                f"({best_match['score']}%)"
            )
            self.selected_team_label.setText(
                f"Squadra: {participant['squadra']}"
            )

            self.participant_confirmed.emit(
                participant
            )

            return

        if (
            result["status"]
            == NameMatcher.STATUS_AMBIGUOUS
        ):
            self._show_voice_candidates(
                result["results"]
            )
            logger.warning("Voice match ambiguous")

            if result.get("reason") == "duplicate_exact_name":
                self.process_label.setText(
                    "PIÙ PARTECIPANTI CON LO STESSO NOME — "
                    "SELEZIONA QUELLO CORRETTO"
                )
            else:
                self.process_label.setText(
                    "RICONOSCIMENTO DA CONFERMARE"
                )

            self.listening_ambiguous.emit()

            self._enable_manual_controls()
            self.results_list.setFocus()

            return

        self.selection_label.setText(
            "Nessun partecipante trovato"
        )

        self.search_input.setText(
            transcription
        )

        self.listening_failed.emit()
        self.update_global_state("ERROR")

        self._enable_manual_controls()

    def _voice_recognition_failed(
        self,
        error_message: str,
    ):
        self.voice_processing = False

        logger.error(
            "Voice recognition failed: %s",
            error_message,
        )

        self.transcription_label.setText(
            "Microfono non disponibile. "
            "Seleziona un altro dispositivo."
        )

        self.process_label.setText(
            "ERRORE DI RICONOSCIMENTO"
        )

        self.listening_failed.emit()
        self.update_global_state("ERROR")

        self._enable_manual_controls()

    def closeEvent(self, event):
        """Chiude in modo controllato eventuali thread ancora attivi."""
        for thread in (self.voice_thread, self.microphone_test_thread):
            if thread is not None and thread.isRunning():
                thread.quit()
                thread.wait(3000)
        super().closeEvent(event)

    def _enable_manual_controls(self):
        if self.processing:
            return

        self.search_input.setEnabled(
            True
        )

        self.results_list.setEnabled(
            True
        )

        self.clear_button.setEnabled(
            True
        )

        if self.selected_participant:
            self.confirm_button.setEnabled(
                True
            )

        self._update_audio_controls()

        self.search_input.setFocus()

    def _show_voice_candidates(
        self,
        results: list[dict],
    ):
        self.results_list.clear()

        self.selected_participant = None

        for result in results:
            participant = result[
                "participant"
            ]

            score = result[
                "score"
            ]

            item = QListWidgetItem(
                f"{participant['nome_completo']} — ID {participant['id']} — "
                f"Squadra {participant['squadra']} ({score}%)"
            )

            item.setData(
                Qt.UserRole,
                participant,
            )

            self.results_list.addItem(
                item
            )

        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(
                0
            )
            self.results_list.setFocus()

    def _update_results(
        self,
        text,
    ):
        if (
            self.processing
            or self.voice_processing
        ):
            return

        self.results_list.clear()

        self.selected_participant = None

        self.confirm_button.setEnabled(
            False
        )

        query = text.strip()

        if not query:
            self.selection_label.setText(
                "Nessun partecipante selezionato"
            )
            self.selected_team_label.setText("Squadra: -")
            return

        results = self.matcher.search(
            query,
            limit=8,
        )

        for result in results:
            participant = result[
                "participant"
            ]

            item = QListWidgetItem(
                f"{participant['nome_completo']} — ID {participant['id']} — "
                f"Squadra {participant['squadra']}"
            )

            item.setData(
                Qt.UserRole,
                participant,
            )

            self.results_list.addItem(
                item
            )

        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(
                0
            )

    def _select_current_result(self):
        if (
            self.processing
            or self.voice_processing
        ):
            return

        item = (
            self.results_list.currentItem()
        )

        if not item:
            self.selected_participant = None

            self.confirm_button.setEnabled(
                False
            )

            return

        participant = item.data(
            Qt.UserRole
        )

        self.selected_participant = (
            participant
        )

        self.selection_label.setText(
            participant["nome_completo"]
        )
        self.selected_team_label.setText(
            f"Squadra: {participant['squadra']}"
        )

        self.confirm_button.setEnabled(
            True
        )

    def _confirm_item(
        self,
        item,
    ):
        if (
            self.processing
            or self.voice_processing
        ):
            return

        self.selected_participant = (
            item.data(
                Qt.UserRole
            )
        )

        self._confirm_selection()

    def _confirm_or_select_first(self):
        if (
            self.processing
            or self.voice_processing
        ):
            return

        if self.selected_participant:
            self._confirm_selection()
            return

        if self.results_list.count() == 0:
            return

        self.results_list.setCurrentRow(
            0
        )

        self._confirm_selection()

    def _confirm_selection(self):
        if (
            self.processing
            or self.voice_processing
            or not self.selected_participant
        ):
            return

        self.participant_confirmed.emit(
            self.selected_participant
        )

    def set_processing(
        self,
        processing: bool,
    ):
        self.processing = processing
        self._update_display_controls()
        self.new_event_button.setEnabled(not processing)
        self.undo_button.setEnabled(
            not processing and bool(self._processed_participant_keys)
        )
        self.reset_selected_button.setEnabled(
            not processing and self.selected_processed_participant is not None
        )

        self.search_input.setEnabled(
            not processing
        )

        self.results_list.setEnabled(
            not processing
        )

        self.clear_button.setEnabled(
            not processing
        )

        self.listen_button.setEnabled(
            False
        )

        self._update_audio_controls()

        if processing:
            self.confirm_button.setEnabled(
                False
            )

            self.process_label.setText(
                "STATO: ELABORAZIONE"
            )
        else:
            self.process_label.setText(
                "STATO: PRONTO"
            )

    def reset_for_next_participant(self):
        self.search_input.clear()
        self.results_list.clear()

        self.selected_participant = None

        self.transcription_label.setText(
            "Voce riconosciuta: -"
        )

        self.selection_label.setText(
            "Nessun partecipante selezionato"
        )
        self.selected_team_label.setText("Squadra: -")

        self.process_label.setText(
            "STATO: PRONTO"
        )

        self.confirm_button.setEnabled(
            False
        )

        self.search_input.setEnabled(
            True
        )

        self.results_list.setEnabled(
            True
        )

        self.clear_button.setEnabled(
            True
        )

        self._update_audio_controls()

        self.search_input.setFocus()

    def _clear_search(self):
        if (
            self.processing
            or self.voice_processing
        ):
            return

        self.search_input.clear()
        self.results_list.clear()

        self.selected_participant = None

        self.transcription_label.setText(
            "Voce riconosciuta: -"
        )

        self.selection_label.setText(
            "Nessun partecipante selezionato"
        )
        self.selected_team_label.setText("Squadra: -")

        self.confirm_button.setEnabled(
            False
        )

        self.search_input.setFocus()
