"""Eccezioni applicative note e leggibili di CyberFranco."""


class CyberFrancoError(Exception):
    """Classe base per gli errori previsti dell'applicazione."""


class ConfigurationError(CyberFrancoError):
    """Configurazione mancante, illeggibile o non valida."""


class ParticipantDataError(CyberFrancoError):
    """Elenco partecipanti mancante, ambiguo o non leggibile."""


class AudioDeviceError(CyberFrancoError):
    """Dispositivo audio assente o non interrogabile."""


class SpeechModelError(CyberFrancoError):
    """Modello Whisper locale assente, incompleto o non caricabile."""


class SpeechRecognitionError(CyberFrancoError):
    """Registrazione o trascrizione fallita durante l'uso."""


class AssetError(CyberFrancoError):
    """Risorsa grafica non valida; normalmente degradabile."""


class SessionError(CyberFrancoError):
    """Errore di lettura o scrittura della sessione locale."""


class SessionValidationError(SessionError):
    """Sessione corrotta, incompleta o con versione non supportata."""
