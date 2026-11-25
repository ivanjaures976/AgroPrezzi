import copy
import statistics

from modelli import Coltura, Allevamento


class Scenario:
    def __init__(self, nome, prezzo_kg=None, resa_kg_m2=None,
                 percentuale_persi=None, attivita_id=None,
                 nome_attivita=None, id_db=None):
        if not nome.strip():
            raise ValueError("Il nome dello scenario non puo' essere vuoto.")
        if prezzo_kg is not None and prezzo_kg < 0:
            raise ValueError("Il prezzo non puo' essere negativo.")
        if resa_kg_m2 is not None and resa_kg_m2 < 0:
            raise ValueError("La resa non puo' essere negativa.")
        if percentuale_persi is not None and not 0 <= percentuale_persi <= 100:
            raise ValueError("La percentuale di animali persi va da 0 a 100.")
        self.id = id_db
        self.nome = nome.strip()
        self.prezzo_kg = prezzo_kg
        self.resa_kg_m2 = resa_kg_m2
        self.percentuale_persi = percentuale_persi
        self.attivita_id = attivita_id
        self.nome_attivita = nome_attivita

    def applica(self, attivita):
        copia = copy.deepcopy(attivita)
        if self.prezzo_kg is not None:
            copia.prezzo_kg = self.prezzo_kg
        if self.resa_kg_m2 is not None and isinstance(copia, Coltura):
            copia.resa_kg_m2 = self.resa_kg_m2
        if self.percentuale_persi is not None and isinstance(copia, Allevamento):
            copia.percentuale_persi = self.percentuale_persi
        return copia

    def descrizione(self):
        parti = []
        if self.prezzo_kg is not None:
            parti.append(f"prezzo {self.prezzo_kg:.2f} EUR/kg")
        if self.resa_kg_m2 is not None:
            parti.append(f"resa {self.resa_kg_m2:g} kg/m2")
        if self.percentuale_persi is not None:
            parti.append(f"persi {self.percentuale_persi:g}%")
        return ", ".join(parti) if parti else "nessuna modifica"

    def a_dizionario(self):
        return {"nome": self.nome, "nome_attivita": self.nome_attivita,
                "prezzo_kg": self.prezzo_kg, "resa_kg_m2": self.resa_kg_m2,
                "percentuale_persi": self.percentuale_persi}


def scenario_da_dizionario(d):
    return Scenario(d["nome"], d.get("prezzo_kg"), d.get("resa_kg_m2"),
                    d.get("percentuale_persi"),
                    nome_attivita=d.get("nome_attivita"))


def calcola_riga(nome, attivita):
    return {"nome": nome, "prezzo_kg": attivita.prezzo_kg,
            "kg": attivita.kg_venduti(), "costi": attivita.costi_totali(),
            "ricavi": attivita.ricavi(), "margine": attivita.margine(),
            "margine_pct": attivita.margine_percentuale(),
            "prezzo_minimo": attivita.prezzo_minimo()}


def confronta(attivita, lista_scenari):
    righe = [calcola_riga("Base", attivita)]
    for s in lista_scenari:
        righe.append(calcola_riga(s.nome, s.applica(attivita)))
    margine_base = righe[0]["margine"]
    for r in righe:
        r["diff_base"] = r["margine"] - margine_base
    return righe


def statistiche(righe):
    margini = [r["margine"] for r in righe]
    migliore = righe[0]
    peggiore = righe[0]
    in_perdita = []
    for r in righe:
        if r["margine"] > migliore["margine"]:
            migliore = r
        if r["margine"] < peggiore["margine"]:
            peggiore = r
        if r["margine"] < 0:
            in_perdita.append(r["nome"])
    deviazione = statistics.pstdev(margini) if len(margini) > 1 else 0.0
    return {"migliore": migliore["nome"], "margine_migliore": migliore["margine"],
            "peggiore": peggiore["nome"], "margine_peggiore": peggiore["margine"],
            "media": statistics.mean(margini), "deviazione": deviazione,
            "intervallo": migliore["margine"] - peggiore["margine"],
            "in_perdita": in_perdita}


def tabella_testo(righe):
    testo = (f"{'Scenario':<16}{'Prezzo':>8}{'Kg':>9}{'Costi':>10}"
             f"{'Ricavi':>10}{'Margine':>10}{'%':>7}{'vs base':>10}\n")
    testo += "-" * 80 + "\n"
    for r in righe:
        testo += (f"{r['nome'][:15]:<16}{r['prezzo_kg']:>8.2f}{r['kg']:>9.1f}"
                  f"{r['costi']:>10.2f}{r['ricavi']:>10.2f}{r['margine']:>10.2f}"
                  f"{r['margine_pct']:>7.1f}{r['diff_base']:>+10.2f}\n")
    return testo


def statistiche_testo(s):
    testo = (f"Scenario migliore: {s['migliore']} ({s['margine_migliore']:.2f} EUR)\n"
             f"Scenario peggiore: {s['peggiore']} ({s['margine_peggiore']:.2f} EUR)\n"
             f"Margine medio: {s['media']:.2f} EUR | "
             f"Deviazione standard: {s['deviazione']:.2f} EUR\n"
             f"Differenza tra migliore e peggiore: {s['intervallo']:.2f} EUR\n")
    if s["in_perdita"]:
        testo += "IN PERDITA: " + ", ".join(s["in_perdita"]) + "\n"
    else:
        testo += "Nessuno scenario in perdita.\n"
    return testo
