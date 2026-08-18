# Console amministratore multi-pagina

## Obiettivo

La console operatore è stata trasformata da una schermata verticale unica in
un'interfaccia amministrativa con header fisso e quattro pagine persistenti. Il
redesign separa il flusso usato per ogni partecipante dalle impostazioni e dalle
azioni distruttive, senza cambiare business logic, worker o `PublicWindow`.

## Architettura

`OperatorWindow` resta una singola `QMainWindow`. Il central widget contiene:

- header fisso con nome, avanzamento, stato globale e navigazione;
- `QStackedWidget` con pagine create una sola volta;
- `QScrollArea` indipendente per ogni pagina.

Il cambio pagina modifica soltanto l'indice dello stack: ricerca, trascrizione,
selezione, worker e reveal non vengono ricreati o interrotti.

## Header e navigazione

I pulsanti sempre visibili sono **EVENTO**, **PARTECIPANTI**, **IMPOSTAZIONI** e
**SESSIONE**. Il pulsante corrente è evidenziato. L'header mostra da qualsiasi
pagina `completati / totale` e uno stato testuale colorato:

- PRONTO, verde;
- ASCOLTO, blu;
- DA CONFERMARE, arancio;
- ELABORAZIONE, ambra;
- REVEAL, viola;
- ERRORE, rosso.
- GIÀ PROCESSATO, verde petrolio.

Lo stato deriva dallo `StateManager`; il colore non sostituisce mai il testo.

## Pagina EVENTO

Contiene soltanto contatori operativi, messaggio di processo, `ASCOLTA`,
trascrizione, ricerca manuale, suggerimenti, partecipante/squadra selezionati e
i comandi PULISCI/CONFERMA. Un match sicuro prosegue senza conferma aggiuntiva.
Un match ambiguo mostra `RICONOSCIMENTO DA CONFERMARE`, seleziona il primo
candidato e sposta il focus sulla lista. Se l'ambiguità deriva da omonimi
esatti, il messaggio chiede esplicitamente di scegliere il partecipante corretto
e ogni candidato mostra ID e squadra.

Le interazioni da tastiera sono locali alla pagina:

- ENTER nel campo ricerca o sulla lista conferma il candidato;
- frecce su/giù usano la navigazione nativa della lista;
- ESC pulisce ricerca e selezione.

Non esiste alcuna shortcut `SPACE = ASCOLTA`. Rimane soltanto la shortcut di
emergenza display `Ctrl+Shift+F`, introdotta dalla feature multi-monitor.

## Pagina PARTECIPANTI

Mostra contatori, elenco completo e storico cronologico. L'elenco completo
indica `ID | Nome | Squadra | Stato` e può essere filtrato localmente per ID, nome,
cognome, nome completo o squadra. Undo e reset continuano a usare tracker e
persistenza esistenti.

## Pagina IMPOSTAZIONI

Contiene le sezioni tecniche già esistenti:

- microfono, refresh device e test audio;
- monitor pubblico, refresh, fullscreen e riposizionamento.

Le stesse istanze dei widget conservano selezione e collegamenti precedenti. Le
preferenze continuano a essere salvate dallo stesso `SettingsLoader`.

## Pagina SESSIONE

Mostra file partecipanti, percorso sessione, modalità attiva/in-memory, data di
creazione, ultimo aggiornamento, conteggio salvato e compatibilità. Il comando
NUOVO EVENTO è isolato in questa pagina, evidenziato come distruttivo e protetto
dal dialogo con i pulsanti espliciti Annulla/Nuovo evento.

## Stati critici

Durante THINKING e REVEAL la navigazione resta disponibile per consultare le
pagine, ma controlli audio, display, undo/reset e nuovo evento sono disabilitati.
Il reveal pubblico continua indipendentemente dalla pagina visualizzata. Al
termine il focus torna alla ricerca della pagina EVENTO quando utilizzabile.

## Design e responsive desktop

Lo stile usa fondo scuro, contrasto elevato, sezioni sobrie e spaziatura ampia.
L'header non scorre; ciascuna pagina gestisce il proprio overflow. La dimensione
iniziale è 1280x800, con minimo 960x640, per coprire l'uso previsto a 1280x720 e
1920x1080.

## Componenti coinvolti

- `src/ui/operator_window.py` — struttura, pagine, navigazione e focus;
- `src/core/sorting_controller.py` — sincronizzazione header e sessione;
- `main.py` — informazioni sessione iniziali;
- `tests/test_operator_navigation.py`;
- `tests/test_operator_workflow.py`;
- `tests/operator_workflow_support.py`.

## Errori e fallback

Gli errori continuano a usare i metodi centralizzati della console e il logging.
Un errore imposta l'indicatore globale rosso senza aprire nuove finestre per i
problemi recuperabili. La pagina impostazioni mantiene i fallback audio/display,
mentre la pagina sessione mostra lo stato di compatibilità esistente.

## Test automatici

I test offscreen verificano pagina iniziale, navigazione, persistenza dei widget,
header globale, collocazione dei controlli, storico, filtro, ENTER, ESC, focus
ambiguity, assenza di shortcut SPACE e blocco dei comandi amministrativi durante
gli stati critici. La suite di regressione copre inoltre audio, display, sessione,
tracking e state machine.

## Test manuali consigliati

1. Eseguire ASCOLTA → match → THINKING → REVEAL dalla pagina EVENTO.
2. Provare un nome ambiguo con frecce ed ENTER senza mouse.
3. Visitare tutte le pagine e verificare che ricerca/trascrizione non cambino.
4. Provare microfono, display e fullscreen dalla pagina IMPOSTAZIONI.
5. Verificare storico, filtro, undo e reset in PARTECIPANTI.
6. Verificare informazioni e NUOVO EVENTO in SESSIONE.
7. Cambiare pagina durante un reveal e provare finestre 1280x720/1920x1080.

## Limiti

Il redesign non introduce componenti UI esterni, nuove impostazioni vocali o
nuova logica di matching. Il layout e la leggibilità finale devono essere
validati sul display e con il ridimensionamento usati durante l'evento.

## Tema scuro e contrasto

La correzione visiva successiva centralizza palette e stylesheet in
`src/ui/operator_theme.py`. Sfondo, superfici, testo principale/secondario,
placeholder, selezione, focus, hover, checked e disabled hanno colori espliciti.
Label, group box, checkbox, input, combo, liste e relativi popup non dipendono
più dalla palette chiara del sistema operativo. Gli stati usano sempre testo
bianco oltre al colore distintivo; `GIÀ PROCESSATO` dispone di uno stato header
dedicato. Il tema riguarda soltanto la console e non modifica `PublicWindow`.
