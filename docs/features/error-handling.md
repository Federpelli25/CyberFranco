# Gestione errori e recovery

## Obiettivo

La feature mantiene CyberFranco utilizzabile quando una risorsa opzionale
fallisce e interrompe in modo leggibile l'avvio quando mancano dati essenziali.
Il dettaglio tecnico viene scritto nel log; l'operatore riceve messaggi brevi.

## Categorie di errore

`src/core/exceptions.py` definisce la base `CyberFrancoError` e le categorie
per configurazione, partecipanti, dispositivi audio, modello Whisper,
riconoscimento vocale e asset. Le classi già esposte dai moduli audio e settings
restano importabili, ma appartengono ora alla gerarchia comune.

## Errori bloccanti

- configurazione assente, JSON malformato o valori non validi;
- file partecipanti assente senza fallback di esempio;
- workbook illeggibile, vuoto o privo delle colonne richieste;
- righe parziali, elenco senza partecipanti validi o duplicati `nome + cognome`.

In questi casi lo startup mostra un `QMessageBox` leggibile e termina con codice
di errore. I dati ambigui non vengono corretti o ignorati automaticamente.

## Errori degradabili e manual mode

- senza microfono l'app resta aperta, consente refresh/selezione e mantiene la
  ricerca manuale;
- senza modello Whisper il pulsante `ASCOLTA` resta disabilitato, mentre ricerca
  e conferma manuali restano disponibili;
- un errore CTranslate2 durante la trascrizione termina il worker e restituisce
  il controllo all'operatore;
- asset squadra assenti o immagini logo non valide generano un warning e usano
  il reveal grafico neutro;
- un errore del display pubblico durante thinking/reveal viene intercettato dal
  controller e non blocca la console operatore.

## Strategia di recovery

`SortingController.recover_to_idle()` invalida il flusso corrente, elimina il
partecipante temporaneo, riporta lo state manager a `IDLE`, prova a ripristinare
il display pubblico e riabilita la console. Ogni sorting possiede un token: un
callback `QTimer.singleShot()` appartenente a un flusso annullato viene ignorato
e non può avviare un reveal obsoleto.

`VoiceRecognitionWorker` e `MicrophoneTestWorker` trasformano ogni eccezione in
un segnale `failed`. Entrambi i thread terminano su `completed` o `failed`; gli
handler `finished` rilasciano i riferimenti e applicano un recovery di sicurezza
se un thread termina senza risultato. La chiusura della finestra richiede inoltre
l'arresto controllato degli eventuali thread ancora attivi.

`main.py` installa un `sys.excepthook` per registrare stack trace non previsti e
mostrare un messaggio generico. Questo handler non sostituisce le gestioni locali
degli errori attesi.

## Componenti coinvolti

- `main.py` — startup controllato e handler globale;
- `src/core/exceptions.py` — gerarchia applicativa;
- `src/core/sorting_controller.py` — recovery e token anti-callback stale;
- `src/data/participant_repository.py` — validazione completa Excel;
- `src/config/settings_loader.py` — errore di configurazione comune;
- `src/audio/` — errori audio, modello, runtime e worker;
- `src/ui/operator_window.py` — messaggi e rilascio thread;
- `src/ui/public_window.py` — fallback degli asset.

## Test automatici

I test dedicati sono in `tests/test_error_handling.py` e
`tests/test_recovery.py`. Coprono file assente, colonne mancanti, righe
incomplete, duplicati, errore runtime Whisper, fallimento worker, recovery da
LISTENING e THINKING, callback stale e asset mancanti. Le suite esistenti
coprono inoltre settings malformati, device non disponibile e modello locale
mancante o incompleto.

## Test manuali consigliati

1. Scollegare il microfono selezionato e verificare ritorno a `IDLE`, controlli
   manuali attivi e refresh disponibile.
2. Rinominare temporaneamente la directory del modello e verificare il manual
   mode.
3. Usare una copia del workbook senza `Squadra` e verificare il popup bloccante.
4. Usare una squadra senza directory asset e completare un reveal fallback.
5. Simulare un errore worker e verificare che pulsanti e stato si sblocchino.

## Limiti

La feature gestisce il recovery runtime. Non salva la sessione su disco, non
ripristina una sessione dopo un riavvio e non introduce gestione multi-monitor.
La disponibilità effettiva di microfoni, driver PortAudio e monitor deve essere
verificata sulla macchina dell'evento.

Il recovery multi-monitor è ora implementato dalla feature `public-display`:
monitor rimossi o non disponibili causano un fallback runtime sul primary senza
interrompere il reveal o la console operatore.
