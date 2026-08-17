# Whisper completamente offline

## Obiettivo

Eliminare la dipendenza dalla cache Hugging Face dell'utente e impedire
qualsiasi download implicito durante l'esecuzione normale di CyberFranco.

Il modello viene preparato prima dell'evento e caricato esclusivamente da una
directory locale controllata dal progetto.

## Configurazione

Il modello predefinito è configurato in `config/settings.json`:

```json
{
  "whisper_model": "small",
  "whisper_model_path": "models/faster-whisper-small",
  "whisper_device": "cpu",
  "whisper_compute_type": "int8",
  "language": "it"
}
```

`whisper_model` viene utilizzato esclusivamente dallo script di preparazione.
L'applicazione normale usa soltanto `whisper_model_path`, risolto rispetto alla
radice del progetto e non rispetto alla directory corrente del terminale.

La directory `models/` è esclusa da Git.

## Preparazione del modello

Con Internet disponibile e virtual environment attivo, eseguire dalla radice
del progetto:

```powershell
python scripts/download_whisper_model.py
```

Lo script usa la funzione ufficiale `faster_whisper.utils.download_model`, già
disponibile nelle dipendenze installate, e salva il modello in:

```text
models/faster-whisper-small/
```

È possibile specificare valori diversi:

```powershell
python scripts/download_whisper_model.py --model small --output D:\modelli\whisper-small
```

In questo caso aggiornare anche `whisper_model_path` nelle settings.

Lo script è separato e non viene mai chiamato da `main.py`.

## Validazione locale

Prima di costruire `WhisperModel`, l'app verifica che il percorso:

- esista;
- sia una directory;
- contenga `model.bin`;
- contenga `config.json`;
- contenga `tokenizer.json`.

`tokenizer.json` è obbligatorio perché la sua assenza potrebbe indurre
`faster-whisper` a recuperare un tokenizer online. Il costruttore riceve inoltre
`local_files_only=True` come ulteriore protezione.

`preprocessor_config.json` è opzionale. Nell'implementazione ufficiale di
`faster-whisper 1.2.1`, `_get_feature_kwargs()` restituisce una configurazione
vuota quando il file manca e `FeatureExtractor` utilizza i propri valori
predefiniti. La sua assenza non rende quindi incompleto un modello locale.

Non esiste alcun fallback a `WhisperModel("small")`.

## Modello mancante o non valido

Se il modello manca o non è caricabile:

- l'applicazione resta aperta;
- `ASCOLTA` rimane disabilitato;
- la console mostra percorso ed errore;
- ricerca manuale, participant tracking e reveal restano disponibili;
- non viene effettuato alcun tentativo di download.

## Componenti coinvolti

```text
config/settings.json
src/config/settings_loader.py
src/audio/speech_to_text.py
src/ui/operator_window.py
scripts/download_whisper_model.py
tests/test_speech_to_text_model_path.py
tests/test_whisper_missing_gui.py
tests/test_settings_loader.py
```

## Test automatici

La suite non accede a Internet e usa directory temporanee e mock per verificare:

- path inesistente;
- path che non è una directory;
- modello incompleto;
- modello valido senza `preprocessor_config.json`;
- modello completo;
- passaggio dell'esatto percorso assoluto a `WhisperModel`;
- uso di `local_files_only=True`;
- assenza di chiamate a Whisper quando il path manca;
- conversione degli errori CTranslate2 in messaggi leggibili;
- lettura e risoluzione della setting `whisper_model_path`;
- GUI utilizzabile manualmente con modello assente.

## Verifica offline manuale

1. Preparare il modello con Internet disponibile.
2. Avviare l'app e verificare una trascrizione completa.
3. Chiudere l'app.
4. Disattivare Wi-Fi, Ethernet, VPN e tethering.
5. Avviare nuovamente `python main.py`.
6. Premere `ASCOLTA`, pronunciare un partecipante valido e arrivare al reveal.

Per una verifica più forte, rinominare temporaneamente la cache Hugging Face
lasciando intatto il modello locale e ripetere il test offline.

## Test manuale del modello mancante

1. Chiudere l'app.
2. Rinominare `models/faster-whisper-small` aggiungendo `_DISABLED`.
3. Avviare l'app.
4. Verificare il messaggio e `ASCOLTA` disabilitato.
5. Cercare manualmente un partecipante ed eseguire il reveal.
6. Ripristinare il nome originale della directory.

## Limiti attuali

Il download iniziale richiede Internet ed è intenzionalmente manuale. Il modello
non viene incluso nel repository. Il caricamento avviene ancora nel thread GUI
all'avvio e può richiedere alcuni secondi, ma viene eseguito una sola volta e la
stessa istanza viene riutilizzata per tutte le trascrizioni.

## Recovery runtime

Gli errori CTranslate2 durante una trascrizione sono convertiti in un errore
applicativo, terminano il worker e riportano il flusso a `IDLE`; la ricerca
manuale resta disponibile. Vedere `docs/features/error-handling.md`.
