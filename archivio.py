import csv
import json
from pathlib import Path

import database
from modelli import da_dizionario
from scenari import scenario_da_dizionario

CARTELLA = Path(__file__).parent
FILE_DATI = CARTELLA / "dati.json"
CARTELLA_USCITA = CARTELLA / "esportazioni"


def percorso_uscita(nome_file):
    CARTELLA_USCITA.mkdir(exist_ok=True)
    return CARTELLA_USCITA / nome_file


def salva_json(attivita, lista_scenari, percorso=FILE_DATI):
    contenuto = {
        "attivita": [a.a_dizionario() for a in attivita],
        "scenari": [s.a_dizionario() for s in lista_scenari],
    }
    try:
        with open(percorso, "w", encoding="utf-8") as f:
            json.dump(contenuto, f, indent=2, ensure_ascii=False)
        return True
    except OSError as err:
        print(f"Errore nel salvataggio di {percorso}: {err}")
        return False


def carica_json(percorso=FILE_DATI):
    percorso = Path(percorso)
    if not percorso.exists():
        return [], []
    try:
        with open(percorso, encoding="utf-8") as f:
            contenuto = json.load(f)
        attivita = [da_dizionario(d) for d in contenuto.get("attivita", [])]
        lista_scenari = [scenario_da_dizionario(d)
                         for d in contenuto.get("scenari", [])]
        return attivita, lista_scenari
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as err:
        print(f"Impossibile leggere {percorso.name}: {err}")
        return [], []


def esporta_da_database(percorso=FILE_DATI):
    return salva_json(database.leggi_attivita(), database.leggi_scenari(), percorso)


def importa_in_database(percorso=FILE_DATI):
    attivita, lista_scenari = carica_json(percorso)
    esistenti = {a.nome: a.id for a in database.leggi_attivita()}
    nuove = set()
    n_attivita = 0
    for a in attivita:
        if a.nome in esistenti:
            continue
        if database.inserisci_attivita(a):
            esistenti[a.nome] = a.id
            nuove.add(a.nome)
            n_attivita += 1
    n_scenari = 0
    for s in lista_scenari:
        if s.nome_attivita in nuove:
            s.attivita_id = esistenti[s.nome_attivita]
            if database.inserisci_scenario(s):
                n_scenari += 1
    return n_attivita, n_scenari


def esporta_risultati_csv(attivita, percorso):
    intestazione = ["Attivita", "Tipo", "Costi totali", "Ricavi",
                    "Margine", "Margine %", "Prezzo minimo"]
    try:
        with open(percorso, "w", newline="", encoding="utf-8-sig") as f:
            scrittore = csv.writer(f, delimiter=";")
            scrittore.writerow(intestazione)
            for a in attivita:
                minimo = a.prezzo_minimo()
                scrittore.writerow([
                    a.nome, a.tipo, f"{a.costi_totali():.2f}",
                    f"{a.ricavi():.2f}", f"{a.margine():.2f}",
                    f"{a.margine_percentuale():.1f}",
                    "" if minimo is None else f"{minimo:.2f}"])
        return True
    except OSError as err:
        print(f"Errore nell'esportazione: {err}")
        return False


def esporta_confronto_csv(righe, percorso):
    intestazione = ["Scenario", "Prezzo EUR/kg", "Kg", "Costi", "Ricavi",
                    "Margine", "Margine %", "Differenza dalla base"]
    try:
        with open(percorso, "w", newline="", encoding="utf-8-sig") as f:
            scrittore = csv.writer(f, delimiter=";")
            scrittore.writerow(intestazione)
            for r in righe:
                scrittore.writerow([
                    r["nome"], f"{r['prezzo_kg']:.2f}", f"{r['kg']:.1f}",
                    f"{r['costi']:.2f}", f"{r['ricavi']:.2f}",
                    f"{r['margine']:.2f}", f"{r['margine_pct']:.1f}",
                    f"{r['diff_base']:.2f}"])
        return True
    except OSError as err:
        print(f"Errore nell'esportazione: {err}")
        return False
