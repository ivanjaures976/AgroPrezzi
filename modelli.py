class Attivita:
    tipo = "attivita"

    def __init__(self, nome, prezzo_kg, costi=None):
        if not nome.strip():
            raise ValueError("Il nome non puo' essere vuoto.")
        if prezzo_kg < 0:
            raise ValueError("Il prezzo non puo' essere negativo.")
        self.id = None
        self.nome = nome.strip()
        self.prezzo_kg = prezzo_kg
        self.costi = costi if costi is not None else []

    def aggiungi_costo(self, nome, importo):
        if not nome.strip():
            raise ValueError("Il nome della voce non puo' essere vuoto.")
        if importo < 0:
            raise ValueError("L'importo non puo' essere negativo.")
        self.costi.append({"nome": nome.strip(), "importo": importo})

    def elimina_costo(self, indice):
        if not 0 <= indice < len(self.costi):
            raise IndexError("Voce di costo inesistente.")
        return self.costi.pop(indice)

    def costi_totali(self):
        return sum(c["importo"] for c in self.costi)

    def kg_venduti(self):
        raise NotImplementedError

    def ricavi(self):
        return self.kg_venduti() * self.prezzo_kg

    def margine(self):
        return self.ricavi() - self.costi_totali()

    def margine_percentuale(self):
        ricavi = self.ricavi()
        if ricavi == 0:
            return 0.0
        return self.margine() / ricavi * 100

    def prezzo_minimo(self):
        kg = self.kg_venduti()
        if kg == 0:
            return None
        return self.costi_totali() / kg

    def dettagli(self):
        return ""

    def riepilogo(self):
        righe = [f"Attivita': {self.nome} ({self.tipo})"]
        if self.dettagli():
            righe.append(self.dettagli())
        righe.append(f"Costi totali: {self.costi_totali():.2f} EUR")
        righe.append(f"Ricavi: {self.ricavi():.2f} EUR "
                     f"({self.kg_venduti():g} kg x {self.prezzo_kg:.2f} EUR/kg)")
        righe.append(f"Margine: {self.margine():.2f} EUR "
                     f"({self.margine_percentuale():.1f}%)")
        minimo = self.prezzo_minimo()
        if minimo is None:
            righe.append("Prezzo minimo: non calcolabile (produzione pari a zero)")
        else:
            righe.append(f"Prezzo minimo: {minimo:.2f} EUR/kg")
            if self.prezzo_kg < minimo:
                righe.append(f"ATTENZIONE: il prezzo attuale e' sotto "
                             f"{minimo:.2f} EUR/kg, si va in perdita.")
            else:
                righe.append(f"ATTENZIONE: se il prezzo scende sotto "
                             f"{minimo:.2f} EUR/kg si va in perdita.")
        return righe

    def a_dizionario(self):
        return {"tipo": self.tipo, "nome": self.nome,
                "prezzo_kg": self.prezzo_kg, "costi": self.costi}


class Coltura(Attivita):
    tipo = "coltura"

    def __init__(self, nome, superficie_m2, resa_kg_m2, prezzo_kg, costi=None):
        super().__init__(nome, prezzo_kg, costi)
        if superficie_m2 < 0 or resa_kg_m2 < 0:
            raise ValueError("Superficie e resa non possono essere negative.")
        self.superficie_m2 = superficie_m2
        self.resa_kg_m2 = resa_kg_m2

    def kg_venduti(self):
        return self.superficie_m2 * self.resa_kg_m2

    def dettagli(self):
        return (f"Superficie: {self.superficie_m2:g} m2 | "
                f"Resa: {self.resa_kg_m2:g} kg/m2")

    def a_dizionario(self):
        d = super().a_dizionario()
        d.update(superficie_m2=self.superficie_m2, resa_kg_m2=self.resa_kg_m2)
        return d


class Allevamento(Attivita):
    tipo = "allevamento"

    def __init__(self, nome, animali_iniziali, percentuale_persi,
                 peso_medio_kg, prezzo_kg, costi=None):
        super().__init__(nome, prezzo_kg, costi)
        if animali_iniziali < 0 or peso_medio_kg < 0:
            raise ValueError("Animali e peso non possono essere negativi.")
        if not 0 <= percentuale_persi <= 100:
            raise ValueError("La percentuale di animali persi va da 0 a 100.")
        self.animali_iniziali = animali_iniziali
        self.percentuale_persi = percentuale_persi
        self.peso_medio_kg = peso_medio_kg

    def animali_finali(self):
        return self.animali_iniziali * (1 - self.percentuale_persi / 100)

    def kg_venduti(self):
        return self.animali_finali() * self.peso_medio_kg

    def dettagli(self):
        return (f"Animali iniziali: {self.animali_iniziali:g} | "
                f"Persi: {self.percentuale_persi:g}% | "
                f"Peso medio: {self.peso_medio_kg:g} kg")

    def a_dizionario(self):
        d = super().a_dizionario()
        d.update(animali_iniziali=self.animali_iniziali,
                 percentuale_persi=self.percentuale_persi,
                 peso_medio_kg=self.peso_medio_kg)
        return d


def da_dizionario(d):
    if d["tipo"] == "coltura":
        return Coltura(d["nome"], d["superficie_m2"], d["resa_kg_m2"],
                       d["prezzo_kg"], d["costi"])
    if d["tipo"] == "allevamento":
        return Allevamento(d["nome"], d["animali_iniziali"],
                           d["percentuale_persi"], d["peso_medio_kg"],
                           d["prezzo_kg"], d["costi"])
    raise ValueError(f"Tipo sconosciuto: {d['tipo']}")
