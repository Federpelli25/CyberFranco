# Asset delle squadre

Ogni squadra configurata in `config/teams.json` usa uno slug indipendente dal
nome visualizzato. Creare una cartella `assets/teams/<slug>/` e inserirvi:

- `logo.png` (asset principale, preferibilmente trasparente);
- `background.png` (opzionale).

Se il logo manca viene mostrato il nome con un fallback grafico. Se manca il
background viene generato un gradiente dai colori configurati.
