# Guide di sviluppo CyberFranco

Questa directory contiene le regole e i quality gate del progetto.
Il suo contenuto deve essere letto prima di sviluppare o modificare una
funzionalità.

## Documentazione obbligatoria delle feature

Ogni nuova feature o modifica funzionale deve essere accompagnata da un file
Markdown dedicato nella directory:

```text
docs/features/
```

Il documento deve essere creato o aggiornato nello stesso sviluppo del codice.
Una feature priva della relativa documentazione non è considerata completata.

Il nome del file deve essere descrittivo, in formato kebab-case:

```text
docs/features/nome-feature.md
```

Esempi:

```text
docs/features/participant-tracking.md
docs/features/centralized-settings.md
docs/features/microphone-selection.md
```

## Contenuto minimo

Ogni documento deve indicare almeno:

1. obiettivo della feature;
2. comportamento implementato;
3. componenti e file coinvolti;
4. configurazione o dati utilizzati;
5. gestione degli errori e fallback;
6. test eseguiti;
7. limiti attuali ed eventuali sviluppi successivi.

Il documento deve descrivere ciò che è realmente implementato. Non deve
presentare funzionalità future come già disponibili.

## Aggiornamenti successivi

Se una feature esistente viene modificata, il relativo documento deve essere
aggiornato nello stesso intervento. Se la modifica introduce un sottosistema
autonomo, è preferibile creare un nuovo documento e collegarlo a quello
esistente.

## Quality gate

Prima di considerare concluso uno sviluppo verificare che:

- il documento della feature esista;
- il documento corrisponda al comportamento effettivo del codice;
- file e configurazioni coinvolti siano elencati;
- test automatici e verifiche manuali siano riportati;
- limiti e dipendenze hardware siano dichiarati;
- la documentazione non contenga dati personali reali.
