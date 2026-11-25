# AgroPrezzi

Calcolatore di costi, ricavi e margine per piccole attività agricole
(colture e allevamenti). Prova finale – Programmazione Python, ITS ICT Piemonte.

## Requisiti
- Python 3.10 o superiore (Ubuntu/Linux)
- `tkinter` per la GUI: `sudo apt install python3-tk`
- `reportlab` per i PDF: `pip install reportlab`
- sqlite3, json, csv: già inclusi in Python

## Avvio
    python3 main.py          # interfaccia testuale (TUI)
    python3 main.py --gui    # interfaccia grafica (tkinter)

## Utenti
Le credenziali non sono nel repository. Al primo avvio il programma chiede
di creare gli utenti da terminale. In alternativa si può usare la variabile
d'ambiente AGROPREZZI_UTENTI="utente1:password1,utente2:password2".

## File
| File | Compito |
|------|---------|
| main.py | avvio: prepara database e utenti, sceglie TUI o GUI |
| tui.py | menu numerico da terminale |
| gui.py | interfaccia grafica tkinter |
| modelli.py | classi Attivita, Coltura, Allevamento |
| scenari.py | classe Scenario, confronto e statistiche |
| database.py | sqlite3: tabelle, CRUD, commit/rollback |
| utenti.py | creazione utenti al primo avvio, password con hash |
| archivio.py | file JSON ed esportazione CSV |
| stampa.py | PDF con reportlab |

## Dati
- Il database è `agroprezzi.db` (creato al primo avvio).
- Alla chiusura tutti i dati vengono copiati in `dati.json`.
- Se il database è vuoto e `dati.json` esiste, i dati si caricano da lì.
  Per provare il programma con dati di esempio: `cp dati_esempio.json dati.json`
  (poi cancella `agroprezzi.db` se esiste già).
- CSV e PDF finiscono nella cartella `esportazioni/`.
