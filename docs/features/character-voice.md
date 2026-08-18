# Voce locale del personaggio

## Obiettivo

La feature aggiunge una voce completamente offline al personaggio digitale:
una clip casuale durante `THINKING` e un annuncio associato alla squadra reale
durante `REVEAL`. Il sorting e le animazioni continuano anche in assenza di
audio.

## Architettura e file

`src/audio/character_audio_manager.py` incapsula `QMediaPlayer`,
`QAudioOutput` e `QMediaDevices`. Espone playback, stop, stato, segnali e
selezione dell'uscita. `SortingController` richiede le clip di stato e forza lo
stop nei recovery. `OperatorWindow` ospita i controlli esclusivamente nella
pagina IMPOSTAZIONI. `FaceWidget` anima bocca e mesh quando riceve TALKING.

Una sola clip può essere attiva: una nuova richiesta ferma quella precedente.
Una clip THINKING non viene scelta due volte consecutivamente quando esistono
alternative. `AWAITING_CONFIRMATION` resta silenzioso e non avvia loop vocali.

## Asset e mapping squadre

Sono supportati `.wav` e `.mp3`; su Windows è consigliato WAV PCM. Le cartelle
sono:

- `assets/audio/thinking/`;
- `assets/audio/awaiting/`;
- `assets/audio/reveal/`;
- `assets/audio/system/` per TEST AUDIO.

`config/teams.json` associa qualsiasi nome normalizzato della squadra al
percorso locale `audio`. Il `TeamConfigLoader` condiviso risolve dinamicamente
la configurazione: non esistono elenchi di squadre o colori hardcodati nel
manager audio. Per sostituire le voci basta copiare i file e aggiornare il
mapping; nessun download viene eseguito dall'applicazione.

## Settings e dispositivi

`config/settings.json` contiene `character_audio.enabled`, `volume` da 0 a 1 e
`output_device_id`. L'identificatore Qt del device è salvato in forma
esadecimale, più stabile di un indice numerico ma non garantito tra driver o
riconnessioni HDMI. Se non è più disponibile viene selezionata l'uscita
predefinita e mostrato un warning. Il refresh è automatico tramite Qt quando
supportato e sempre disponibile tramite il pulsante dedicato.

Durante il playback il comando ASCOLTA è disabilitato per evitare che il
microfono acquisisca la voce dagli speaker. TEST AUDIO usa il device scelto e
diventa STOP AUDIO durante la riproduzione.

## Errori e fallback

File mancanti, mapping assenti, codec non supportati, errori del player e
uscite scollegate vengono registrati. TALKING viene sempre disattivato su stop,
fine o errore; reveal, tracking e sessione non vengono bloccati. Se non sono
presenti asset definitivi il funzionamento è intenzionalmente silenzioso.

## Test

I test automatici coprono manager, start/stop, segnali, volume, disabled mode,
file mancanti, selezione casuale senza ripetizione, mapping squadra, policy no
overlap, sincronizzazione TALKING, recovery e protezione microfono. Non usano
hardware audio reale.

Le verifiche manuali ancora necessarie sono: codec e volume su Windows,
selezione tra uscite fisiche, persistenza dopo riavvio, hot-plug HDMI, annunci
di più squadre, dieci cicli consecutivi e successivo utilizzo del microfono.

## Limiti

Non sono inclusi file vocali definitivi. Non sono presenti TTS, streaming,
cloning vocale, mixer multicanale o lip-sync a fonemi/visemi. La bocca usa una
pulsazione visiva semplice sincronizzata allo stato di playback.
# Sincronizzazione reveal avanzato

La clip della squadra parte al segnale `TEAM_APPEAR`, dopo il flash e insieme
alla comparsa di nome e logo. Una clip assente non modifica i timing visuali.
