# Logging applicativo locale

## Obiettivo

Fornire diagnostica locale durante sviluppo ed evento senza servizi esterni,
database o trasmissione di dati. Il logging affianca i messaggi GUI e non ne
modifica il comportamento.

## Configurazione

Il sistema usa `logging` della libreria standard ed è configurato in
`config/settings.json`:

```json
{
  "logging": {
    "level": "INFO",
    "file": "logs/cyberfranco.log",
    "max_bytes": 5242880,
    "backup_count": 3
  }
}
```

Il percorso relativo viene risolto dalla radice del progetto. I livelli
accettati sono `DEBUG`, `INFO`, `WARNING`, `ERROR` e `CRITICAL`.

## File e rotazione

Il file predefinito è `logs/cyberfranco.log`. `RotatingFileHandler` limita ogni
file a 5 MB e conserva tre backup (`.1`, `.2`, `.3`). La directory `logs/` e i
file `*.log` sono esclusi da Git.

Il formato è:

```text
2026-08-17 15:30:22 | INFO | src.audio.speech_to_text | Whisper model loaded
```

## Comportamento e fallback

`src/core/logging_config.py` configura una sola coppia di handler condivisi:

- `StreamHandler` per la console;
- `RotatingFileHandler` per il file.

Richiami successivi sostituiscono gli handler CyberFranco esistenti invece di
duplicarli. Se directory o file non sono scrivibili, l'app continua con la sola
console e produce un warning. Il logging non è un requisito bloccante.

## Livelli ed eventi

- `DEBUG`: dispositivi audio, metriche peak/RMS, segmenti Whisper, candidati e
  score completi;
- `INFO`: avvio, partecipanti, microfono, modello, trascrizione, conferma,
  tracking e reveal;
- `WARNING`: device/modello indisponibile, testo vuoto, match ambiguo,
  partecipante duplicato e asset mancanti;
- `ERROR`: errori PortAudio/worker, modello invalido, Excel invalido e I/O.

Per abilitare il dettaglio diagnostico impostare `"level": "DEBUG"` e
riavviare l'app. Dopo la diagnosi è consigliato ripristinare `INFO`.

## Policy sui dati personali

Il progetto tratta nomi di minori. I log non contengono il file Excel completo,
audio o dati non necessari. Il nome completo è concentrato negli eventi chiave
di conferma e completamento; candidati e score sono disponibili solo a livello
`DEBUG`. I log devono essere conservati solo per il tempo necessario.

## Componenti coinvolti

```text
config/settings.json
src/core/logging_config.py
main.py
src/config/settings_loader.py
src/audio/
src/data/participant_repository.py
src/recognition/name_matcher.py
src/core/state_manager.py
src/core/sorting_controller.py
src/core/participant_tracker.py
src/ui/operator_window.py
src/ui/public_window.py
tests/test_logging_config.py
tests/test_settings_loader.py
```

## Test automatici

- creazione directory/file e scrittura;
- formatter con timestamp, livello, modulo e messaggio;
- assenza di handler duplicati;
- livello e rotazione configurati;
- fallback console su errore del file handler;
- default, override e validazione settings;
- regressione delle feature esistenti.

I test usano directory temporanee e non scrivono nei log reali.

## Test manuali richiesti

1. Avviare `python main.py` e verificare `logs/cyberfranco.log`.
2. Eseguire ascolto, matching e reveal e controllare gli eventi.
3. Provocare un match ambiguo e verificare `WARNING`.
4. Eseguire `TEST MICROFONO` e controllare peak/RMS.
5. Provocare un errore recuperabile e verificare GUI e log.

## Limiti attuali

Il logging è sincrono, adeguato al volume dell'evento. Non esistono invio cloud,
Sentry, database, salvataggio audio o coda dedicata. La rimozione dei vecchi
backup è gestita dalla rotazione configurata.
