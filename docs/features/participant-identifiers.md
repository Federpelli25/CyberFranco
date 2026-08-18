# Identificatori univoci dei partecipanti

## Obiettivo

Gestire più partecipanti con lo stesso nome senza confondere tracking,
assegnazioni o sessioni. L'ID Excel è la chiave primaria applicativa; il nome
normalizzato resta esclusivamente un dato di ricerca.

## Excel e modello dati

Le colonne obbligatorie sono `ID`, `Nome`, `Cognome` e `Squadra`. L'ID viene
letto come stringa e ripulito soltanto dagli spazi esterni: valori come `001`,
`A017` e `ROMA-023` sono validi e gli zeri iniziali vengono conservati se la
cella Excel è testuale. ID mancanti, vuoti o duplicati bloccano il caricamento.
Nomi uguali con ID diversi sono ammessi e producono un warning nel log.

Ogni partecipante contiene `id`, `nome`, `cognome`, `squadra`,
`nome_completo` e `search_name`. L'app non genera ID durante l'avvio.

`data/partecipanti_example.xlsx` contiene la colonna ID e due righe `Mario
Rossi`, rispettivamente `001` e `002`, assegnate a squadre diverse.

## Matching e flusso operatore

`NameMatcher` conserva tutte le righe associate allo stesso `search_name`. Un
exact match con più ID restituisce sempre `ambiguous`, anche con punteggio 100,
e la console mostra un messaggio specifico. Risultati vocali e manuali mostrano
nome, ID e squadra. La pagina PARTECIPANTI mostra `ID | Nome | Squadra | Stato`
e il filtro cerca anche per ID.

L'ID resta un dato amministrativo: `PublicWindow` riceve il partecipante
completo dal controller, ma continua a mostrare soltanto il reveal della
squadra.

## Tracking e sessione

Tracker, controllo "già processato", undo e reset usano esclusivamente l'ID.
La sessione è in versione 2 e ogni voce processata contiene
`participant_id`, `name`, `team` e `processed_at`. Il fingerprint SHA-256
include le righe ordinate `ID|search_name|squadra`.

Le sessioni versione 1 non vengono migrate per nome: con omonimi sarebbe
possibile associare lo storico alla persona sbagliata. Sono quindi rifiutate in
modo leggibile e preservate dal meccanismo di quarantena; l'operatore avvia un
nuovo evento in versione 2.

## Utility di transizione

`scripts/add_participant_ids.py` crea una copia di un Excel legacy e aggiunge
ID sequenziali con padding minimo a tre cifre:

```text
python scripts/add_participant_ids.py data/partecipanti.xlsx
```

Il nome predefinito è `partecipanti_con_id.xlsx`. L'originale non viene mai
sovrascritto; una destinazione esistente richiede `--force`.

## Componenti coinvolti

- `src/data/participant_repository.py` — validazione Excel e modello dati;
- `src/recognition/name_matcher.py` — duplicati ed ambiguity;
- `src/core/participant_tracker.py` — identità per ID;
- `src/core/sorting_controller.py` — trasporto e logging dell'ID;
- `src/data/session_repository.py` e `main.py` — sessione v2 e recovery;
- `src/ui/operator_window.py` — ID nella sola console amministratore;
- `scripts/add_participant_ids.py` — migrazione esplicita dell'Excel;
- `data/partecipanti_example.xlsx` — dataset dimostrativo.

## Errori e fallback

Un file privo della colonna ID mostra `FILE PARTECIPANTI NON VALIDO`. Un ID
duplicato mostra `ID PARTECIPANTE DUPLICATO`. Non esiste fallback a nome né
generazione silenziosa di ID. Una sessione legacy viene conservata e sostituita
da una sessione vuota v2.

## Test

I test automatici coprono ID testuali e con zeri iniziali, valori vuoti,
colonna assente, ID duplicati, nomi duplicati, exact match ambiguo al 100%,
tracking indipendente, restore per ID, fingerprint, ricerca/filtro UI, undo e
reset. Per il collaudo manuale usare i due Mario Rossi del file di esempio,
processare soltanto un ID, riavviare e verificare che l'altro resti disponibile.

## Limiti

Non sono previsti database, scanner, QR code o servizi cloud. Gli ID numerici
che devono mantenere zeri iniziali vanno memorizzati in Excel come testo.
