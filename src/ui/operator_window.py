from pathlib import Path

from PySide6.QtCore import (
    Qt,
    Signal,
    QThread,
)
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
)

from src.audio.speech_to_text import (
    SpeechToText,
)
from src.audio.voice_recognition_worker import (
    VoiceRecognitionWorker,
)
from src.data.participant_repository import (
    ParticipantRepository,
)
from src.recognition.name_matcher import (
    NameMatcher,
)


class OperatorWindow(QMainWindow):

    participant_confirmed = Signal(dict)

    listening_started = Signal()
    listening_ambiguous = Signal()
    listening_failed = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "CyberFranco - Operator Console"
        )

        self.resize(
            900,
            700,
        )

        self.repository = ParticipantRepository(
            Path(
                "data/partecipanti_example.xlsx"
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
            for participant in self.participants
        )

        self.selected_participant = None

        self.processing = False
        self.voice_processing = False

        self.voice_thread = None
        self.voice_worker = None

        self._build_ui()
        self._connect_events()

        self._load_speech_model()

    def _load_speech_model(self):
        self.process_label.setText(
            "STATO: CARICAMENTO WHISPER"
        )

        self.listen_button.setEnabled(
            False
        )

        self.speech_to_text = SpeechToText(
            model_size="small",
            device="cpu",
            compute_type="int8",
            language="it",
        )

        self.process_label.setText(
            "STATO: PRONTO"
        )

        self.listen_button.setEnabled(
            True
        )

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

        self.status_label = QLabel(
            f"Partecipanti caricati: "
            f"{len(self.participants)}"
        )

        self.status_label.setAlignment(
            Qt.AlignCenter
        )

        self.process_label = QLabel(
            "STATO: PRONTO"
        )

        self.process_label.setAlignment(
            Qt.AlignCenter
        )

        self.process_label.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #28a745;
                padding: 8px;
            }
            """
        )

        self.transcription_label = QLabel(
            "Voce riconosciuta: -"
        )

        self.transcription_label.setAlignment(
            Qt.AlignCenter
        )

        self.transcription_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                padding: 8px;
            }
            """
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

        self.results_list.setStyleSheet(
            """
            QListWidget {
                font-size: 20px;
            }

            QListWidget::item {
                padding: 10px;
            }
            """
        )

        self.selection_label = QLabel(
            "Nessun partecipante selezionato"
        )

        self.selection_label.setAlignment(
            Qt.AlignCenter
        )

        self.selection_label.setStyleSheet(
            """
            font-size: 22px;
            font-weight: bold;
            padding: 15px;
            """
        )

        button_layout = QHBoxLayout()

        self.confirm_button = QPushButton(
            "Conferma"
        )

        self.confirm_button.setEnabled(
            False
        )

        self.confirm_button.setStyleSheet(
            """
            QPushButton {
                font-size: 20px;
                padding: 12px 30px;
            }
            """
        )

        self.clear_button = QPushButton(
            "Pulisci"
        )

        self.clear_button.setStyleSheet(
            """
            QPushButton {
                font-size: 20px;
                padding: 12px 30px;
            }
            """
        )

        button_layout.addWidget(
            self.clear_button
        )

        button_layout.addWidget(
            self.confirm_button
        )

        main_layout.addWidget(
            title
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

    def _connect_events(self):
        self.listen_button.clicked.connect(
            self._start_voice_recognition
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

    def _start_voice_recognition(self):
        if self.processing:
            return

        if self.voice_processing:
            return

        self.voice_processing = True

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
                duration_seconds=4.0,
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

        self.voice_thread.start()

    def _voice_recognition_completed(
        self,
        transcription: str,
    ):
        self.voice_processing = False

        if not transcription:
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

            self.selected_participant = (
                participant
            )

            self.selection_label.setText(
                f"{participant['nome_completo']} "
                f"({best_match['score']}%)"
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

            self.process_label.setText(
                "STATO: SCELTA PARTECIPANTE"
            )

            self.listening_ambiguous.emit()

            self._enable_manual_controls()

            return

        self.selection_label.setText(
            "Nessun partecipante trovato"
        )

        self.search_input.setText(
            transcription
        )

        self.listening_failed.emit()

        self._enable_manual_controls()

    def _voice_recognition_failed(
        self,
        error_message: str,
    ):
        self.voice_processing = False

        print(
            f"Errore riconoscimento vocale: "
            f"{error_message}"
        )

        self.transcription_label.setText(
            "Errore durante il riconoscimento vocale"
        )

        self.listening_failed.emit()

        self._enable_manual_controls()

    def _enable_manual_controls(self):
        if self.processing:
            return

        self.listen_button.setEnabled(
            True
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

        if self.selected_participant:
            self.confirm_button.setEnabled(
                True
            )

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
                f"{participant['nome_completo']} "
                f"({score}%)"
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

    def _update_results(
        self,
        text,
    ):
        if self.processing:
            return

        if self.voice_processing:
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
                participant[
                    "nome_completo"
                ]
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
        if self.processing:
            return

        if self.voice_processing:
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
            participant[
                "nome_completo"
            ]
        )

        self.confirm_button.setEnabled(
            True
        )

    def _confirm_item(
        self,
        item,
    ):
        if self.processing:
            return

        if self.voice_processing:
            return

        self.selected_participant = (
            item.data(
                Qt.UserRole
            )
        )

        self._confirm_selection()

    def _confirm_or_select_first(self):
        if self.processing:
            return

        if self.voice_processing:
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
        if self.processing:
            return

        if self.voice_processing:
            return

        if not self.selected_participant:
            return

        participant = (
            self.selected_participant
        )

        print(
            f"SELEZIONATO: "
            f"{participant['nome_completo']} "
            f"-> "
            f"{participant['squadra']}"
        )

        self.participant_confirmed.emit(
            participant
        )

    def set_processing(
        self,
        processing: bool,
    ):
        self.processing = processing

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
            not processing
        )

        if processing:
            self.confirm_button.setEnabled(
                False
            )

            if self.selected_participant:
                self.selection_label.setText(
                    f"In elaborazione: "
                    f"{self.selected_participant['nome_completo']}"
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

        self.listen_button.setEnabled(
            True
        )

        self.search_input.setFocus()

    def _clear_search(self):
        if self.processing:
            return

        if self.voice_processing:
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

        self.confirm_button.setEnabled(
            False
        )

        self.search_input.setFocus()