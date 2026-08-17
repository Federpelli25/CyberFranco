import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from faster_whisper.utils import download_model

from src.audio.speech_to_text import SpeechToText
from src.config.settings_loader import SettingsLoader


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scarica il modello faster-whisper nella directory "
            "locale configurata per CyberFranco."
        )
    )
    parser.add_argument(
        "--model",
        help="Nome del modello faster-whisper da preparare.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Directory locale di destinazione.",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    settings = SettingsLoader(PROJECT_ROOT).load()
    model_name = arguments.model or settings.whisper_model
    output_path = (
        arguments.output.expanduser().resolve()
        if arguments.output is not None
        else settings.resolve_whisper_model_path()
    )

    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Preparazione modello faster-whisper '{model_name}'...")
    print(f"Destinazione: {output_path}")
    print("Questa operazione richiede una connessione Internet.")

    try:
        downloaded_path = download_model(
            model_name,
            output_dir=str(output_path),
            local_files_only=False,
        )
        validated_path = SpeechToText.validate_model_path(
            downloaded_path
        )
    except Exception as exc:
        print(f"Preparazione modello fallita: {exc}")
        return 1

    print("Modello preparato correttamente.")
    print(f"Percorso finale: {validated_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
