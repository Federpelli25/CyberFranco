# Display pubblico, fullscreen e multi-monitor

## Obiettivo

La feature separa la console operatore dall'esperienza pubblica e permette di
posizionare `PublicWindow` su qualsiasi schermo rilevato da Qt, in finestra o in
fullscreen, senza assumere coordinate o orientamenti specifici.

## Selezione monitor

La sezione **DISPLAY PUBBLICO** della console mostra nome Qt, risoluzione e
indicazione del monitor principale. La combo, il pulsante `AGGIORNA MONITOR`, il
toggle fullscreen e `APRI / RIPOSIZIONA DISPLAY` operano a runtime.

`src/ui/display_manager.py` legge `QGuiApplication.screens()`, espone geometria,
indice, nome e monitor principale, e risolve la selezione salvata. Qt rimane la
fonte di verità anche quando un monitor si trova a sinistra, sopra o sotto il
principale.

## Configurazione e persistenza

La feature riutilizza `config/settings.json`:

```json
{
  "public_display_monitor": 1,
  "public_display_fullscreen": false
}
```

Le modifiche manuali vengono salvate atomicamente dal `SettingsLoader`. L'indice
Qt non è un identificatore assolutamente stabile tra modifiche hardware: il nome
dello schermo viene usato dal manager quando fornito direttamente, ma il formato
settings corrente conserva l'indice per compatibilità con le fasi precedenti.

## Fullscreen e modalità sviluppo

In fullscreen viene prima assegnato lo schermo alla finestra e poi chiamato
`showFullScreen()`. Con fullscreen disattivato la finestra è normale e occupa la
geometria del monitor selezionato, così può essere ridimensionata durante i test.
La console operatore viene posizionata sul monitor principale e resta una finestra
separata.

Il contenuto scenico include ora `FaceWidget`, guidato dagli stati applicativi e
scalabile senza coordinate legate a uno specifico monitor. Durante il reveal la
faccia esegue una breve reazione e lascia poi spazio al layer squadra esistente.
Asset faccia mancanti degradano sul fallback vettoriale Qt.

La shortcut di emergenza `Ctrl+Shift+F`, attiva nella console operatore, disattiva
soltanto il fullscreen della finestra pubblica. Funziona anche durante un reveal.

## Fallback e hot-plug

Con un solo monitor l'app resta utilizzabile e mostra un warning che consiglia la
modalità finestra. Se l'indice salvato non esiste, il display pubblico usa il
monitor principale senza sovrascrivere la preferenza: ricollegando il monitor,
la selezione originaria può essere ripristinata.

I segnali Qt `screenAdded` e `screenRemoved` aggiornano automaticamente la combo.
Se lo schermo pubblico scompare, la finestra viene spostata subito sul primary,
anche durante una fase occupata. Errori di posizionamento vengono loggati e la
finestra torna in modalità normale.

I cambi manuali sono disabilitati durante `THINKING` e `REVEAL`; il contenuto
grafico corrente non viene ricreato e il normale flusso reveal resta invariato.

## Componenti coinvolti

- `src/ui/display_manager.py` — enumerazione, descrizione e fallback schermi;
- `src/ui/operator_window.py` — controlli, persistenza, hot-plug e shortcut;
- `src/ui/public_window.py` — posizionamento e fullscreen;
- `src/ui/face_widget.py` — volto, animazioni e fallback grafico;
- `src/config/settings_loader.py` — salvataggio preferenze;
- `main.py` — condivisione manager e collegamento tra le due finestre;
- `tests/test_display_manager.py` — test mockati e offscreen.

## Gestione errori

Assenza o rimozione di monitor non chiudono l'app. Il fallback usa il primary e
viene registrato nel log. Il display pubblico continua a mostrare esclusivamente
contenuti scenici: nessun dato Excel, controllo operatore, trascrizione o dettaglio
tecnico viene trasferito alla finestra pubblica.

## Test automatici

I test verificano elenco schermi, geometrie anche negative, primary, indice e nome
validi, fallback per indice assente, assenza totale di schermi, formattazione,
salvataggio settings e applicazione di geometria/fullscreen alla `PublicWindow`.

## Test manuali consigliati

1. Avviare con un solo monitor e verificare warning e modalità finestra.
2. Collegare un secondo monitor, selezionarlo e provare finestra/fullscreen.
3. Disporre il secondario a sinistra, destra e sopra nelle impostazioni di Windows.
4. Riavviare e verificare il ripristino delle preferenze.
5. Scollegare il monitor pubblico durante IDLE e durante un reveal.
6. Verificare `Ctrl+Shift+F` e l'intero flusso ASCOLTA → REVEAL → IDLE.

## Limiti

Nome e ordine restituiti da Qt dipendono dal sistema operativo e dai driver. Il
fallback è affidabile, ma la persistenza assoluta dell'identità fisica di uno
schermo non è garantita. Il comportamento reale di fullscreen e taskbar deve
essere verificato sulla macchina Windows usata durante l'evento.

Dal redesign amministratore selezione monitor, fullscreen e riposizionamento
sono raccolti nella pagina IMPOSTAZIONI; l'header e le altre pagine non alterano
la finestra pubblica.
