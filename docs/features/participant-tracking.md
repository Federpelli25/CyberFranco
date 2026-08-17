# Participant tracking

## Obiettivo

Gestire in memoria lo stato dei partecipanti durante un evento, impedendo
assegnazioni duplicate e mantenendo contatori e storico coerenti.

## Comportamento implementato

- registra un partecipante come completato soltanto alla fine del reveal;
- mantiene lo storico ordinato dei partecipanti completati;
- espone i contatori totali, completati e rimanenti;
- impedisce di completare due volte lo stesso partecipante;
- permette di annullare l'ultima assegnazione;
- permette di resettare uno specifico partecipante;
- impedisce undo e reset durante gli stati `THINKING` e `REVEAL`;
- aggiorna elenco e contatori nella console operatore;
- mantiene lo stato esclusivamente in memoria e non modifica l'Excel.

La chiave interna usa la colonna opzionale `ID`, quando disponibile. In sua
assenza utilizza `search_name`.

## Componenti coinvolti

```text
main.py
src/core/participant_tracker.py
src/core/sorting_controller.py
src/ui/operator_window.py
src/data/participant_repository.py
tests/test_participant_tracker.py
tests/test_sorting_controller_tracking.py
```

## Errori e fallback

Un partecipante privo sia di `ID` sia di `search_name` viene rifiutato con un
errore esplicito. Il reset di un partecipante non completato non modifica lo
stato e produce un messaggio per l'operatore.

## Test

Sono presenti test automatici per:

- contatori e stato iniziale;
- completamento e storico;
- doppia assegnazione;
- reset singolo e globale;
- undo con storico vuoto e popolato;
- reset di un elemento intermedio dello storico;
- protezione dello storico interno;
- omonimi distinti tramite `ID`;
- completamento soltanto dopo il reveal;
- blocco di undo e reset durante l'elaborazione;
- sequenza completa Mario/Luca definita nella roadmap.

## Limiti attuali

Gli omonimi sono distinti correttamente dal tracker soltanto quando l'Excel
fornisce un `ID` univoco.

## Persistenza

Con `session_persistence_enabled` attivo, stato e ordine cronologico vengono
salvati dopo reveal, undo e reset e ripristinati al riavvio. Il formato e le
strategie di recovery sono descritti in `docs/features/session-persistence.md`.
