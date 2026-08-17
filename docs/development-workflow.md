# Workflow di sviluppo

Le regole operative complete sono definite in `dev-guides/README.md` e devono
essere lette prima di modificare il progetto.

Ogni feature richiede:

- un branch dedicato `feature/nome-feature`, creato da `Dev` aggiornato;
- codice e test della feature;
- un documento in `docs/features/nome-feature.md`;
- test rilevanti superati;
- commit e push del feature branch;
- merge del branch in `Dev`;
- push di `Dev` dopo il merge.

`main` non viene modificato automaticamente e contiene soltanto versioni
stabili verificate.
