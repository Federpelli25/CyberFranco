# Faccia digitale e stati visivi

## Obiettivo

La finestra pubblica mostra un personaggio digitale che reagisce agli stati
`IDLE`, `LISTENING`, `THINKING`, `AWAITING_CONFIRMATION` e `REVEAL`, senza
esporre dati tecnici o amministrativi. Il sistema è completamente offline e non
aggiunge dipendenze grafiche esterne.

## Architettura

`FaceWidget` è un `QWidget` autonomo che riceve lo stato visuale, precarica gli
asset disponibili, disegna il fallback e possiede timer e animazioni. Non decide
le transizioni applicative. `SortingController` collega il segnale
`StateManager.state_changed` alla `PublicWindow`, che delega alla faccia e
continua a gestire separatamente il reveal della squadra.

Il cambio di stato incrementa un generation token, ferma timer e animazioni
precedenti e avvia soltanto le risorse necessarie al nuovo stato. Il passaggio
da `THINKING` ad `AWAITING_CONFIRMATION` è l'eccezione intenzionale: conserva
animazione e generation per evitare flash o reset visivi.

## Design del personaggio

Il fallback è concentrato esclusivamente sul volto e non disegna capelli,
orecchie, collo, busto o spalle. Il rendering Qt costruisce un avatar umanoide
olografico con silhouette del viso, sopracciglia, naso e bocca definiti da linee
luminose. Gli occhi sono landmark ad alto contrasto composti da profilo a
mandorla, iride wireframe, raggi e pupilla puntiforme.

L'interno del volto è una point cloud organizzata in righe curve. I nodi sono
collegati orizzontalmente, verticalmente e in diagonale per formare una mesh
triangolata che segue la sagoma della testa. Una fase animata applica piccoli
spostamenti sinusoidali ai punti; particelle orbitanti completano la silhouette
senza ricorrere a numeri binari o texture esterne. Palette, contorni e aura usano
esclusivamente ciano, turchese, azzurro, viola freddo e bianco.

## Stati e animazioni

- `IDLE`: espressione neutra, leggero sorriso, mesh lenta, poche particelle,
  movimento verticale e blink casuale tra 3 e 6,5 secondi;
- `LISTENING`: testa inclinata, occhi molto più aperti, sopracciglia sollevate,
  bocca aperta e glow azzurro pulsante;
- `THINKING`: mesh e particelle più attive, oltre a quattro pose realmente
  diverse che combinano inclinazione, sguardo, occhi, sopracciglia e bocca;
- `AWAITING_CONFIRMATION`: mantiene il movimento thinking ma lo rallenta e
  assume una posa sospesa, quasi soddisfatta, con accento turchese;
- `REVEAL`: volto più definito, massima densità dinamica, occhi e sopracciglia
  aperti, sorriso luminoso, flash e zoom prima che compaia la squadra.

Le animazioni usano esclusivamente `QTimer`, `QPropertyAnimation` e
`QSequentialAnimationGroup`; non esistono loop ad alto FPS o attese bloccanti.
L'API `set_talking(bool)` è predisposta ma non collegata ad audio o TTS.

## Asset e fallback

Gli asset opzionali vanno in `assets/face/` con questi nomi:

```text
idle.png
blink.png
listening.png
thinking_01.png
thinking_02.png
reveal.png
```

I PNG vengono caricati una sola volta all'avvio e scalati con
`Qt.KeepAspectRatio`. File assenti o non validi producono un warning e vengono
sostituiti dal volto vettoriale disegnato con `QPainter`. Il fallback usa forme
geometriche, glow e colori di stato; non richiede placeholder binari. Per
sostituirlo basta aggiungere i PNG nella cartella, senza modificare il codice.

## PublicWindow e performance

La faccia occupa lo spazio elastico della composizione esistente e scala con la
finestra a 1280×720, 1920×1080 e fullscreen. All'inizio del reveal resta visibile
per 220 ms, poi lascia spazio a logo e nome squadra. Un token separato impedisce
a una transizione reveal ritardata di riapparire dopo un recovery o cambio stato.

In IDLE sono attivi soltanto una proprietà animata lentamente e un timer
single-shot per il blink. Gli asset non vengono riletti per frame. Alla chiusura
del widget tutti i timer e le animazioni vengono fermati.

## Componenti coinvolti

- `src/ui/face_widget.py` — rendering, asset, fallback e animazioni;
- `src/ui/public_window.py` — composizione e passaggio faccia/reveal;
- `src/core/sorting_controller.py` — collegamento allo stato autorevole;
- `tests/test_face_widget.py` — asset, fallback, scaling e cleanup;
- `tests/test_face_state_transitions.py` — transizioni e callback stale;
- `docs/features/public-display.md` — integrazione con il display pubblico.

## Errori e fallback

Un asset mancante non interrompe l'app. Stati sconosciuti vengono ignorati con
warning. Le callback ritardate controllano il generation token prima di
modificare la UI. Il reveal squadra e la business logic restano indipendenti da
eventuali problemi grafici della faccia.

## Test automatici

I test Qt offscreen coprono stato iniziale, fallback senza cartella asset,
preload PNG, aspect ratio, sequenza IDLE → LISTENING → THINKING, continuità
AWAITING_CONFIRMATION, transizione REVEAL, stop delle vecchie animazioni,
callback stale, cleanup timer, attività mesh per stato, differenza della posa
LISTENING, quattro pose THINKING distinte e dieci cicli completi.

## Verifiche manuali consigliate

1. Lasciare IDLE attivo per 30–60 secondi e osservare blink e movimento.
2. Provare LISTENING, THINKING, nome ambiguo e reveal completo.
3. Eseguire almeno dieci cicli verificando fluidità e consumo CPU.
4. Provare finestra e fullscreen a 1280×720 e 1920×1080 sul monitor pubblico.
5. Aggiungere o rinominare temporaneamente `assets/face` e verificare il fallback.

## Limiti

Non sono implementati TTS, lip sync, rendering 3D o reveal avanzato. Il volto
vettoriale è un placeholder sostituibile e la resa finale va verificata sul
proiettore o monitor utilizzato durante l'evento.
