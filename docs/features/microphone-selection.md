# Gestione e selezione del microfono

## Obiettivo

Permettere all'operatore di scegliere esplicitamente il dispositivo di input,
verificarne il segnale e riutilizzare la scelta agli avvii successivi senza
dipendere soltanto dal microfono predefinito di Windows.

## Comportamento implementato

- enumera tramite `sounddevice` esclusivamente i dispositivi con canali input;
- mostra nome, host API e ID di ogni dispositivo;
- mantiene visibili le varianti MME, DirectSound, WASAPI e WDM-KS;
- offre una voce per il dispositivo predefinito di sistema;
- salva l'ID selezionato in `config/settings.json`;
- usa immediatamente il nuovo dispositivo nelle registrazioni successive;
- ripristina la selezione salvata all'avvio;
- usa il default se il dispositivo salvato non è più disponibile;
- disabilita `ASCOLTA` quando non esistono dispositivi input;
- aggiorna la lista dopo connessioni o disconnessioni USB;
- esegue il test microfono per due secondi in un `QThread` separato;
- mostra peak, RMS e una valutazione comprensibile del segnale;
- impedisce cambio, refresh e test durante ascolto, thinking e reveal;
- mantiene invariato lo stato pubblico durante il test tecnico.

## Componenti coinvolti

```text
main.py
config/settings.json
src/config/settings_loader.py
src/audio/audio_device_manager.py
src/audio/microphone.py
src/audio/microphone_test_worker.py
src/audio/voice_recognition_worker.py
src/ui/operator_window.py
tests/test_audio_device_manager.py
tests/test_microphone_settings.py
tests/test_microphone_test_worker.py
tests/test_settings_loader.py
```

## Configurazione

```json
{
  "microphone_device": null
}
```

`null` utilizza l'input predefinito. Un intero maggiore o uguale a zero indica
l'ID PortAudio del dispositivo selezionato. Il salvataggio aggiorna il JSON in
modo atomico e conserva tutte le altre impostazioni.

Gli ID non vengono sostituiti con i nomi perché dispositivi diversi possono
avere lo stesso nome, soprattutto tra host API Windows differenti.

## Test del segnale

Le soglie sono indicative e servono come controllo operativo rapido:

- `RMS < 0.001`: nessun segnale rilevato;
- `0.001 <= RMS < 0.005`: segnale molto basso;
- `RMS >= 0.005`: microfono OK.

La registrazione di test è bloccante soltanto nel worker secondario e non nel
thread principale Qt. L'audio non viene salvato né riprodotto.

## Errori e fallback

Device inesistenti, scollegati, senza canali input o errori PortAudio vengono
convertiti in messaggi leggibili. Dopo un errore la console torna utilizzabile
e consente di aggiornare i dispositivi o selezionarne un altro.

Se il device salvato manca all'avvio, la console mostra un avviso, seleziona il
default e salva `null`. Se non esiste un default ma sono disponibili altri
input, seleziona il primo device enumerato.

## Test automatici eseguiti

- filtro dei soli dispositivi input;
- campi ID, canali, sample rate e host API;
- device predefinito e ID inesistente;
- errore di enumerazione PortAudio;
- passaggio dell'ID selezionato a `sounddevice.rec`;
- device mancante e device senza input;
- persistenza dell'ID e conservazione delle altre settings;
- validazione di ID negativi, booleani e nomi stringa;
- soglie RMS e peak del test microfono;
- regressione di settings, tracking, repository e matcher;
- costruzione offscreen della console con dispositivi reali enumerati.

## Verifiche manuali ancora richieste

Prima del commit devono essere provati dall'utente:

1. selezione e ripristino del device dopo riavvio;
2. test microfono parlando normalmente;
3. pipeline `ASCOLTA` fino al reveal;
4. scollegamento fisico di un device selezionato;
5. refresh dopo collegamento o scollegamento USB.

## Limiti attuali

Gli ID PortAudio possono cambiare se Windows modifica l'ordine dei dispositivi;
in quel caso viene applicato il fallback. I duplicati tra host API vengono
mostrati intenzionalmente. Le soglie RMS non sostituiscono una calibrazione
professionale e possono essere adattate in una fase successiva.

## Recovery runtime

La gestione errori centralizzata mantiene attiva la ricerca manuale se un device
non è più disponibile, se PortAudio fallisce o se un worker termina in errore.
La console torna utilizzabile e consente di aggiornare o cambiare microfono. I
dettagli sono descritti in `docs/features/error-handling.md`.
