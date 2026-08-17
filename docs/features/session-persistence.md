# Persistenza della sessione

## Obiettivo

CyberFranco salva localmente lo storico dei partecipanti completati e lo
ripristina dopo chiusure, crash o riavvii, senza modificare il file Excel e senza
usare database o servizi online.

## Configurazione e percorso

Le impostazioni sono centralizzate in `config/settings.json`:

```json
{
  "session_file": "data/session.json",
  "session_persistence_enabled": true
}
```

Con la persistenza disabilitata il tracker torna a funzionare solo in memoria.
`data/session*.json` è escluso da Git perché contiene nomi di partecipanti.

## Formato versione 1

La sessione contiene `version`, `created_at`, `updated_at`,
`participants_file`, `participants_fingerprint` e lo storico `processed`. Ogni
entry processata salva soltanto chiave interna, nome, squadra e `processed_at`.
I timestamp sono ISO 8601 con timezone. Non vengono salvati audio, trascrizioni,
punteggi fuzzy o configurazioni hardware.

## Scrittura atomica

`SessionRepository` serializza prima `session.json.tmp`, esegue flush e `fsync`,
quindi sostituisce la sessione con `os.replace()`. Se la scrittura fallisce il
temporaneo viene rimosso, l'azione resta nello stato in memoria e l'operatore
vede `SESSIONE NON SALVATA` per poter riprovare.

## Restore

All'avvio vengono caricati prima i partecipanti e poi la sessione. Il tracker
ricostruisce insieme stato, ordine cronologico e timestamp. Il salvataggio di
una nuova assegnazione avviene soltanto dopo la conclusione del reveal; undo e
reset vengono persistiti subito dopo l'aggiornamento in memoria.

## Fingerprint e mismatch

Il fingerprint SHA-256 deriva dalle coppie ordinate e normalizzate
`search_name + squadra`. Se non coincide, lo storico vecchio non viene caricato
e il sorting resta bloccato. La sessione su disco non viene sovrascritta finché
l'operatore non conferma **NUOVO EVENTO**.

## Nuovo evento

Il pulsante è separato dai comandi di ascolto, visivamente distinto,
disabilitato durante `THINKING/REVEAL` e protetto da `QMessageBox`. La conferma
azzera tracker e storico persistito senza modificare Excel.

## Sessione corrotta

JSON malformato, schema incompleto, timestamp senza timezone, entry duplicate o
versione sconosciuta producono un errore controllato. Il file viene preservato
come `session.corrupted.<timestamp>.json`; l'app crea una sessione vuota e mostra
un warning. Un errore di lettura non recuperabile abilita la modalità in memoria.

## Componenti coinvolti

- `src/data/session_repository.py` — schema, validazione e I/O atomico;
- `src/core/participant_tracker.py` — import/export dello stato;
- `src/core/sorting_controller.py` — coordinamento dei salvataggi;
- `main.py` — restore, fingerprint, mismatch e corruzione;
- `src/ui/operator_window.py` — conferma del nuovo evento;
- `src/config/settings_loader.py` — configurazione;
- `tests/test_session_repository.py` e `tests/test_session_persistence.py`.

## Test automatici

I test usano directory temporanee e coprono file assente, sessione vuota,
save/load, replace atomico, JSON corrotto, quarantena, versione, timestamp,
fingerprint, restore tracker, reveal, undo, reset, nuovo evento, mismatch e
fallimento di scrittura.

## Test manuali consigliati

1. Processare due partecipanti, riavviare e verificare contatori e ordine.
2. Eseguire undo e reset, riavviare e verificare lo stato.
3. Confermare NUOVO EVENTO e verificare il reset dopo il riavvio.
4. Terminare forzatamente l'app dopo un reveal completato e riaprire.
5. Modificare temporaneamente l'Excel e verificare il mismatch.
6. Corrompere una copia di `session.json` e verificare warning e backup.

## Limiti

Non sono previsti migrazioni oltre la versione 1, sincronizzazione tra PC,
backup remoto o recovery di modifiche rimaste solo in memoria dopo un errore di
scrittura. La persistenza resta locale al computer dell'evento.

Le informazioni di sessione e il comando NUOVO EVENTO sono ora isolati nella
pagina SESSIONE della console amministratore.
