# Settings centralizzati

## Obiettivo

Rimuovere dal codice i principali parametri operativi e caricarli da un unico
file JSON validato all'avvio.

## Comportamento implementato

Il file `config/settings.json` configura:

- file Excel reale e file di esempio;
- modello, device e compute type Whisper;
- percorso locale del modello Whisper;
- lingua di trascrizione;
- durata della registrazione;
- durata della fase di thinking;
- dispositivo microfono;
- monitor della finestra pubblica;
- modalità fullscreen della finestra pubblica;
- livello, file e rotazione del logging locale.

Il loader applica valori predefiniti alle proprietà omesse, valida i valori e
risolve i percorsi relativi rispetto alla radice del progetto. Il file Excel
reale ha priorità; se non esiste viene utilizzato il file di esempio.

L'indice del monitor è zero-based: `0` indica il monitor principale e `1` il
secondo monitor. Se l'indice non è disponibile, viene usato il monitor
principale.

## Componenti coinvolti

```text
config/settings.json
src/config/__init__.py
src/config/settings_loader.py
main.py
src/audio/microphone.py
src/audio/voice_recognition_worker.py
src/core/sorting_controller.py
src/ui/operator_window.py
src/ui/public_window.py
tests/test_settings_loader.py
tests/test_microphone_settings.py
```

## Errori e fallback

Il loader produce messaggi leggibili per:

- file di configurazione assente o non leggibile;
- JSON malformato, con riga e colonna;
- valori mancanti sostituiti dai default;
- tipi o intervalli non validi;
- entrambi i file Excel assenti.

Gli errori di configurazione iniziali vengono mostrati tramite una finestra di
dialogo invece di lasciare soltanto un traceback.

## Test

Sono presenti test automatici per:

- caricamento dei default e degli override;
- risoluzione dei percorsi dalla radice del progetto;
- priorità dell'Excel reale e fallback sull'esempio;
- JSON malformato e file assente;
- durata, microfono, monitor e fullscreen non validi;
- passaggio del dispositivo configurato a `sounddevice`.
- risoluzione del modello Whisper dalla radice del progetto.

## Limiti attuali

La configurazione generale viene letta all'avvio. La selezione del microfono è
invece salvata e applicata immediatamente dalla console operatore. Il
caricamento del modello Whisper avviene ancora durante la costruzione della
console operatore.

### Aggiornamento display pubblico

Le preferenze di monitor pubblico e fullscreen, come la selezione microfono,
vengono salvate e applicate immediatamente dalla console operatore tramite lo
stesso `SettingsLoader`.
