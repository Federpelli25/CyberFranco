# Squadre e asset configurabili

## Obiettivo

Le squadre possono avere qualsiasi nome e non dipendono da colori predefiniti.
`config/teams.json` è la fonte autorevole per nome visualizzato, slug, logo,
background, colori e audio reveal.

## Configurazione

Ogni proprietà è associata a una chiave normalizzata, uguale al valore usato
nel file partecipanti senza differenze di maiuscole o spazi superflui:

```json
{
  "FENICI": {
    "slug": "fenici",
    "display_name": "Fenici",
    "logo": "assets/teams/fenici/logo.png",
    "background": "assets/teams/fenici/background.png",
    "primary_color": "#D97706",
    "secondary_color": "#FBBF24",
    "audio": "assets/audio/reveal/fenici.wav"
  }
}
```

Lo slug deve contenere lettere minuscole, numeri e trattini ed essere univoco.
I colori devono essere esadecimali `#RRGGBB`: sono attributi grafici e non
identificano la squadra.

## Componenti

`src/config/team_config_loader.py` carica e valida la configurazione, normalizza
le chiavi, risolve i percorsi e produce fallback. `PublicWindow` riceve una
configurazione completa, precarica i pixmap e usa il display name. Il manager
audio usa lo stesso loader per l'annuncio. `OperatorWindow` offre stato,
anteprima e reload senza modificare tracker, sessione o stato evento.

## Asset e fallback

Il logo PNG è l'asset principale. Il background è opzionale: quando manca il
reveal genera un gradiente da `primary_color` e `secondary_color`. Logo, audio
e colori non validi producono warning leggibili e fallback. Una squadra Excel
non configurata usa nome originale e stile neutro; il reveal continua.

La cache grafica viene invalidata e ricostruita premendo RICARICA
CONFIGURAZIONE E ASSET. Non serve riavviare l'applicazione.

## Aggiungere una squadra

1. aggiungere una voce a `config/teams.json`;
2. creare `assets/teams/<slug>/`;
3. inserire `logo.png`;
4. aggiungere facoltativamente `background.png`;
5. inserire l'audio reveal e configurarne il percorso;
6. usare la stessa chiave squadra nel file Excel;
7. premere RICARICA CONFIGURAZIONE E ASSET.

## Test e limiti

I test automatici coprono nomi arbitrari, slug, asset opzionali, colori,
duplicati, squadre sconosciute, fallback, cache, reload, preview e reveal.
Sono ancora necessarie verifiche manuali con PNG e WAV definitivi alle
risoluzioni 1280x720 e 1920x1080.

La GUI non crea o modifica strutturalmente le squadre e non scarica asset. Non
sono supportati video background, database o editor grafici completi.
