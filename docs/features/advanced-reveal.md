# Reveal avanzato

## Obiettivo

Il reveal pubblico presenta la squadra con una sequenza scenica fluida e
interamente offline, mantenendo separata la scelta della squadra dalla resa
grafica.

## Comportamento implementato

`RevealController` orchestra le fasi `PRE_REVEAL`, `FLASH_IN`, `TEAM_APPEAR`,
`HOLD` e `FADE_OUT` tramite timer Qt non bloccanti. La faccia viene
intensificata nel pre-reveal, segue un flash breve nel colore secondario della
squadra e infine compaiono logo, nome e sfondo. La chiusura riporta il display
in IDLE ed emette il segnale che autorizza tracking e salvataggio sessione.

`TeamReveal` usa un background con crop cover quando disponibile. Senza
background disegna un gradiente dai colori configurati; senza logo mantiene il
nome grande e centrato. Una trama leggera di particelle deterministiche aggiunge
profondità senza loop ad alto FPS o dipendenze esterne.

Il pulsante `ANTEPRIMA REVEAL` nella sezione SQUADRE E ASSET avvia la stessa
presentazione solo quando l'applicazione è inattiva. La preview non imposta un
partecipante, non aggiorna il tracker e non salva la sessione.

## Componenti coinvolti

- `src/ui/reveal_controller.py`: sequenza, timing e generation token;
- `src/ui/team_reveal.py`: rendering scalabile e fallback;
- `src/ui/public_window.py`: integrazione con faccia e display pubblico;
- `src/core/sorting_controller.py`: audio all'apparizione e completamento;
- `src/ui/operator_window.py`: comando di preview;
- `src/config/settings_loader.py` e `config/settings.json`: timing.

## Configurazione

La sezione `reveal` espone `pre_reveal_ms`, `flash_ms`, `appear_ms`, `hold_ms`
e `fade_ms`. I valori predefiniti sono 500, 180, 500, 2200 e 500 ms, per una
durata complessiva di circa 3,9 secondi. Tutti devono essere interi non negativi.

## Audio, errori e fallback

L'annuncio locale parte quando la fase `TEAM_APPEAR` rende visibile la squadra;
l'assenza della clip non rallenta il flusso. Errori di rendering vengono
registrati e degradano a una presentazione statica. Ogni nuovo reveal o recovery
invalida le callback precedenti tramite generation token.

## Test

I test automatici coprono ordine delle fasi, completamento singolo, callback
stale, assenza degli asset, squadra non configurata, intensità e integrazione
con tracking/sessione già coperta dai test del controller applicativo.

## Limiti e verifiche manuali

Le particelle sono decorative e non animate continuamente. Restano da verificare
su hardware reale centratura e leggibilità a 1280x720 e 1920x1080, fullscreen su
monitor secondario, quattro squadre, asset mancanti e dieci cicli consecutivi.
