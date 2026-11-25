import tkinter as tk
from tkinter import messagebox

import archivio
import database
import scenari
import stampa
import utenti
from modelli import Coltura, Allevamento
from scenari import Scenario

CAMPI_ATTIVITA = {
    "coltura": [("nome", "Nome", str, True),
                ("superficie_m2", "Superficie (m2)", float, True),
                ("resa_kg_m2", "Resa (kg per m2)", float, True),
                ("prezzo_kg", "Prezzo (EUR/kg)", float, True)],
    "allevamento": [("nome", "Nome", str, True),
                    ("animali_iniziali", "Animali iniziali", int, True),
                    ("percentuale_persi", "Animali persi (%)", float, True),
                    ("peso_medio_kg", "Peso medio (kg)", float, True),
                    ("prezzo_kg", "Prezzo (EUR/kg)", float, True)],
}
CAMPI_SCENARIO = {
    "coltura": [("nome", "Nome scenario", str, True),
                ("prezzo_kg", "Prezzo (EUR/kg)", float, False),
                ("resa_kg_m2", "Resa (kg per m2)", float, False)],
    "allevamento": [("nome", "Nome scenario", str, True),
                    ("prezzo_kg", "Prezzo (EUR/kg)", float, False),
                    ("percentuale_persi", "Animali persi (%)", float, False)],
}


def converti(campi, testi):
    valori = {}
    for chiave, etichetta, tipo, obbligatorio in campi:
        testo = testi[chiave].strip().replace(",", ".")
        if testo == "":
            if obbligatorio:
                raise ValueError(f"Il campo '{etichetta}' e' obbligatorio.")
            valori[chiave] = None
            continue
        if tipo is str:
            valori[chiave] = testo
            continue
        try:
            valori[chiave] = tipo(testo)
        except ValueError:
            raise ValueError(f"Il campo '{etichetta}' non e' un numero valido.")
    return valori


def crea_oggetto(tipo, v, costi=None):
    if tipo == "coltura":
        return Coltura(v["nome"], v["superficie_m2"], v["resa_kg_m2"],
                       v["prezzo_kg"], costi)
    return Allevamento(v["nome"], v["animali_iniziali"], v["percentuale_persi"],
                       v["peso_medio_kg"], v["prezzo_kg"], costi)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("AgroPrezzi")
        self.elenco = []
        self.corrente = None
        self.scenari_corrente = []
        self.mostra_login()

    def mostra_login(self):
        self.frame_login = tk.Frame(self.root, padx=30, pady=30)
        self.frame_login.pack()
        tk.Label(self.frame_login, text="AgroPrezzi",
                 font=("Helvetica", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        tk.Label(self.frame_login, text="Utente:").grid(row=1, column=0, sticky="e")
        tk.Label(self.frame_login, text="Password:").grid(row=2, column=0, sticky="e")
        self.entry_utente = tk.Entry(self.frame_login)
        self.entry_utente.grid(row=1, column=1, pady=3)
        self.entry_password = tk.Entry(self.frame_login, show="*")
        self.entry_password.grid(row=2, column=1, pady=3)
        self.entry_password.bind("<Return>", self.accedi)
        tk.Button(self.frame_login, text="Accedi",
                  command=self.accedi).grid(row=3, column=0, columnspan=2, pady=10)
        self.entry_utente.focus()

    def accedi(self, evento=None):
        if utenti.accedi(self.entry_utente.get(), self.entry_password.get()):
            self.frame_login.destroy()
            self.costruisci_principale()
        else:
            messagebox.showerror("Accesso", "Utente o password errati.")

    def costruisci_principale(self):
        self.root.geometry("900x620")
        sinistra = tk.Frame(self.root, padx=8, pady=8)
        sinistra.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(sinistra, text="Attivita'", font=("Helvetica", 12, "bold")).pack()
        self.lista_attivita = tk.Listbox(sinistra, width=24, height=18,
                                         exportselection=False)
        self.lista_attivita.pack(fill=tk.Y, expand=True)
        self.lista_attivita.bind("<<ListboxSelect>>", self.seleziona_attivita)
        tk.Button(sinistra, text="Nuova coltura",
                  command=lambda: self.form_attivita("coltura")).pack(fill=tk.X, pady=1)
        tk.Button(sinistra, text="Nuovo allevamento",
                  command=lambda: self.form_attivita("allevamento")).pack(fill=tk.X, pady=1)
        tk.Button(sinistra, text="Modifica",
                  command=self.modifica_attivita).pack(fill=tk.X, pady=1)
        tk.Button(sinistra, text="Elimina",
                  command=self.elimina_attivita).pack(fill=tk.X, pady=1)

        destra = tk.Frame(self.root, padx=8, pady=8)
        destra.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(destra, text="Risultato del calcolo",
                 font=("Helvetica", 12, "bold")).pack(anchor="w")
        self.testo_risultato = tk.Text(destra, height=9, state="disabled")
        self.testo_risultato.pack(fill=tk.X)

        frame_costi = tk.Frame(destra)
        frame_costi.pack(fill=tk.X, pady=6)
        tk.Label(frame_costi, text="Voci di costo",
                 font=("Helvetica", 12, "bold")).grid(row=0, column=0, sticky="w")
        self.lista_costi = tk.Listbox(frame_costi, height=5, width=40,
                                      exportselection=False)
        self.lista_costi.grid(row=1, column=0, rowspan=3, padx=(0, 8))
        tk.Label(frame_costi, text="Nome:").grid(row=1, column=1, sticky="e")
        self.entry_costo_nome = tk.Entry(frame_costi, width=16)
        self.entry_costo_nome.grid(row=1, column=2)
        tk.Label(frame_costi, text="Importo:").grid(row=2, column=1, sticky="e")
        self.entry_costo_importo = tk.Entry(frame_costi, width=16)
        self.entry_costo_importo.grid(row=2, column=2)
        tk.Button(frame_costi, text="Aggiungi",
                  command=self.aggiungi_costo).grid(row=3, column=1)
        tk.Button(frame_costi, text="Elimina selezionata",
                  command=self.elimina_costo).grid(row=3, column=2)

        frame_scenari = tk.Frame(destra)
        frame_scenari.pack(fill=tk.X, pady=6)
        tk.Label(frame_scenari, text="Scenari",
                 font=("Helvetica", 12, "bold")).grid(row=0, column=0, sticky="w")
        self.lista_scenari = tk.Listbox(frame_scenari, height=5, width=40,
                                        exportselection=False)
        self.lista_scenari.grid(row=1, column=0, rowspan=3, padx=(0, 8))
        tk.Button(frame_scenari, text="Nuovo scenario",
                  command=self.nuovo_scenario).grid(row=1, column=1, sticky="ew")
        tk.Button(frame_scenari, text="Elimina scenario",
                  command=self.elimina_scenario).grid(row=2, column=1, sticky="ew")
        tk.Button(frame_scenari, text="Confronta scenari",
                  command=self.confronta_scenari).grid(row=3, column=1, sticky="ew")

        frame_export = tk.Frame(destra)
        frame_export.pack(fill=tk.X, pady=6)
        tk.Button(frame_export, text="CSV risultati",
                  command=self.esporta_csv).pack(side=tk.LEFT, padx=2)
        tk.Button(frame_export, text="Copia JSON",
                  command=self.esporta_json).pack(side=tk.LEFT, padx=2)
        tk.Button(frame_export, text="PDF scheda",
                  command=self.pdf_scheda).pack(side=tk.LEFT, padx=2)
        tk.Button(frame_export, text="Esci",
                  command=self.root.destroy).pack(side=tk.RIGHT, padx=2)

        self.aggiorna_elenco()

    def aggiorna_elenco(self, id_da_selezionare=None):
        self.elenco = database.leggi_attivita()
        self.lista_attivita.delete(0, tk.END)
        posizione = None
        for i, a in enumerate(self.elenco):
            self.lista_attivita.insert(tk.END, f"{a.nome} ({a.tipo})")
            if a.id == id_da_selezionare:
                posizione = i
        self.corrente = None
        if posizione is not None:
            self.lista_attivita.selection_set(posizione)
            self.corrente = self.elenco[posizione]
        self.aggiorna_dettaglio()

    def aggiorna_dettaglio(self):
        self.testo_risultato.config(state="normal")
        self.testo_risultato.delete("1.0", tk.END)
        self.lista_costi.delete(0, tk.END)
        self.lista_scenari.delete(0, tk.END)
        if self.corrente is None:
            self.testo_risultato.insert(tk.END, "Seleziona o crea un'attivita'.")
            self.scenari_corrente = []
        else:
            self.testo_risultato.insert(tk.END, "\n".join(self.corrente.riepilogo()))
            for c in self.corrente.costi:
                self.lista_costi.insert(tk.END, f"{c['nome']}: {c['importo']:.2f} EUR")
            self.scenari_corrente = database.leggi_scenari(self.corrente.id)
            for s in self.scenari_corrente:
                self.lista_scenari.insert(tk.END, f"{s.nome}: {s.descrizione()}")
        self.testo_risultato.config(state="disabled")

    def seleziona_attivita(self, evento=None):
        selezione = self.lista_attivita.curselection()
        if selezione:
            self.corrente = self.elenco[selezione[0]]
            self.aggiorna_dettaglio()

    def serve_attivita(self):
        if self.corrente is None:
            messagebox.showinfo("AgroPrezzi", "Seleziona prima un'attivita'.")
            return False
        return True

    def finestra_modulo(self, titolo, campi, valori, azione):
        finestra = tk.Toplevel(self.root)
        finestra.title(titolo)
        finestra.grab_set()
        entries = {}
        for riga, (chiave, etichetta, _, _) in enumerate(campi):
            tk.Label(finestra, text=etichetta).grid(row=riga, column=0,
                                                    sticky="e", padx=6, pady=3)
            entry = tk.Entry(finestra, width=26)
            entry.grid(row=riga, column=1, padx=6, pady=3)
            entry.insert(0, valori.get(chiave, ""))
            entries[chiave] = entry

        def conferma():
            testi = {chiave: e.get() for chiave, e in entries.items()}
            errore = azione(testi)
            if errore:
                messagebox.showerror("Dati non validi", errore, parent=finestra)
            else:
                finestra.destroy()

        tk.Button(finestra, text="OK", command=conferma).grid(
            row=len(campi), column=0, columnspan=2, pady=8)

    def form_attivita(self, tipo):
        def azione(testi):
            try:
                a = crea_oggetto(tipo, converti(CAMPI_ATTIVITA[tipo], testi))
            except ValueError as err:
                return str(err)
            if not database.inserisci_attivita(a):
                return "Salvataggio non riuscito: " + database.ultimo_errore
            self.aggiorna_elenco(a.id)
            return None
        self.finestra_modulo("Nuova " + tipo, CAMPI_ATTIVITA[tipo], {}, azione)

    def modifica_attivita(self):
        if not self.serve_attivita():
            return
        vecchia = self.corrente
        tipo = vecchia.tipo
        valori = {k: str(v) for k, v in vecchia.a_dizionario().items()
                  if k != "costi"}

        def azione(testi):
            try:
                nuova = crea_oggetto(tipo, converti(CAMPI_ATTIVITA[tipo], testi),
                                     vecchia.costi)
            except ValueError as err:
                return str(err)
            nuova.id = vecchia.id
            if not database.aggiorna_attivita(nuova):
                return "Salvataggio non riuscito: " + database.ultimo_errore
            self.aggiorna_elenco(nuova.id)
            return None
        self.finestra_modulo("Modifica " + vecchia.nome, CAMPI_ATTIVITA[tipo],
                             valori, azione)

    def elimina_attivita(self):
        if not self.serve_attivita():
            return
        if messagebox.askyesno("Elimina", f"Eliminare '{self.corrente.nome}' "
                               "con costi e scenari?"):
            if database.elimina_attivita(self.corrente.id):
                self.aggiorna_elenco()
            else:
                messagebox.showerror("Errore", database.ultimo_errore)

    def aggiungi_costo(self):
        if not self.serve_attivita():
            return
        try:
            importo = float(self.entry_costo_importo.get().strip().replace(",", "."))
            self.corrente.aggiungi_costo(self.entry_costo_nome.get(), importo)
        except ValueError as err:
            messagebox.showerror("Dati non validi",
                                 "Inserisci un nome e un importo valido (numero >= 0).")
            return
        if database.aggiorna_attivita(self.corrente):
            self.entry_costo_nome.delete(0, tk.END)
            self.entry_costo_importo.delete(0, tk.END)
            self.aggiorna_dettaglio()
        else:
            self.corrente.costi.pop()
            messagebox.showerror("Errore", database.ultimo_errore)

    def elimina_costo(self):
        if not self.serve_attivita():
            return
        selezione = self.lista_costi.curselection()
        if not selezione:
            messagebox.showinfo("AgroPrezzi", "Seleziona una voce di costo.")
            return
        voce = self.corrente.elimina_costo(selezione[0])
        if database.aggiorna_attivita(self.corrente):
            self.aggiorna_dettaglio()
        else:
            self.corrente.costi.insert(selezione[0], voce)
            messagebox.showerror("Errore", database.ultimo_errore)

    def nuovo_scenario(self):
        if not self.serve_attivita():
            return
        attivita = self.corrente
        campi = CAMPI_SCENARIO[attivita.tipo]

        def azione(testi):
            try:
                v = converti(campi, testi)
                s = Scenario(v["nome"], v.get("prezzo_kg"), v.get("resa_kg_m2"),
                             v.get("percentuale_persi"), attivita_id=attivita.id,
                             nome_attivita=attivita.nome)
            except ValueError as err:
                return str(err)
            if not database.inserisci_scenario(s):
                return "Salvataggio non riuscito: " + database.ultimo_errore
            self.aggiorna_dettaglio()
            return None
        self.finestra_modulo("Nuovo scenario (campi vuoti = invariati)",
                             campi, {}, azione)

    def elimina_scenario(self):
        if not self.serve_attivita():
            return
        selezione = self.lista_scenari.curselection()
        if not selezione:
            messagebox.showinfo("AgroPrezzi", "Seleziona uno scenario.")
            return
        s = self.scenari_corrente[selezione[0]]
        if database.elimina_scenario(s.id):
            self.aggiorna_dettaglio()
        else:
            messagebox.showerror("Errore", database.ultimo_errore)

    def confronta_scenari(self):
        if not self.serve_attivita():
            return
        if not self.scenari_corrente:
            messagebox.showinfo("AgroPrezzi", "Crea almeno uno scenario.")
            return
        attivita = self.corrente
        righe = scenari.confronta(attivita, self.scenari_corrente)
        finestra = tk.Toplevel(self.root)
        finestra.title(f"Confronto scenari - {attivita.nome}")
        testo = tk.Text(finestra, width=84, height=18, font=("Courier", 10))
        testo.pack(padx=8, pady=8)
        testo.insert(tk.END, scenari.tabella_testo(righe) + "\n")
        testo.insert(tk.END, scenari.statistiche_testo(scenari.statistiche(righe)))
        testo.config(state="disabled")

        def salva_pdf():
            percorso = archivio.percorso_uscita(f"confronto_{attivita.nome}.pdf")
            if stampa.pdf_confronto(attivita, righe, percorso):
                messagebox.showinfo("PDF", f"Creato:\n{percorso}", parent=finestra)
            else:
                messagebox.showerror("PDF", stampa.ultimo_errore, parent=finestra)

        def salva_csv():
            percorso = archivio.percorso_uscita(f"confronto_{attivita.nome}.csv")
            if archivio.esporta_confronto_csv(righe, percorso):
                messagebox.showinfo("CSV", f"Creato:\n{percorso}", parent=finestra)

        frame = tk.Frame(finestra)
        frame.pack(pady=(0, 8))
        tk.Button(frame, text="Stampa PDF", command=salva_pdf).pack(side=tk.LEFT, padx=4)
        tk.Button(frame, text="Esporta CSV", command=salva_csv).pack(side=tk.LEFT, padx=4)
        tk.Button(frame, text="Chiudi", command=finestra.destroy).pack(side=tk.LEFT, padx=4)

    def esporta_csv(self):
        percorso = archivio.percorso_uscita("risultati.csv")
        if archivio.esporta_risultati_csv(self.elenco, percorso):
            messagebox.showinfo("CSV", f"Creato:\n{percorso}")

    def esporta_json(self):
        if archivio.esporta_da_database():
            messagebox.showinfo("JSON", f"Creato:\n{archivio.FILE_DATI}")

    def pdf_scheda(self):
        if not self.serve_attivita():
            return
        percorso = archivio.percorso_uscita(f"scheda_{self.corrente.nome}.pdf")
        if stampa.pdf_attivita(self.corrente, percorso):
            messagebox.showinfo("PDF", f"Creato:\n{percorso}")
        else:
            messagebox.showerror("PDF", stampa.ultimo_errore)


def avvia():
    root = tk.Tk()
    App(root)
    root.mainloop()
