import getpass

import archivio
import database
import scenari
import stampa
import utenti
from modelli import Coltura, Allevamento
from scenari import Scenario


def leggi_testo(messaggio):
    while True:
        testo = input(messaggio).strip()
        if testo:
            return testo
        print("Valore obbligatorio.")


def leggi_numero(messaggio, minimo=0, massimo=None, intero=False,
                 facoltativo=False):
    while True:
        testo = input(messaggio).strip().replace(",", ".")
        if facoltativo and testo == "":
            return None
        try:
            valore = int(testo) if intero else float(testo)
        except ValueError:
            print("Inserisci un numero valido.")
            continue
        if valore < minimo:
            print(f"Il valore deve essere almeno {minimo}.")
            continue
        if massimo is not None and valore > massimo:
            print(f"Il valore deve essere al massimo {massimo}.")
            continue
        return valore


def stampa_menu(titolo, voci):
    print(f"\n=========== {titolo} ===========")
    for numero, testo in voci:
        print(f" {numero}. {testo}")


def login():
    for _ in range(3):
        username = input("Utente: ")
        password = getpass.getpass("Password: ")
        if utenti.accedi(username, password):
            return username.strip()
        print("Credenziali errate.")
    return None


def scegli_attivita():
    elenco = database.leggi_attivita()
    if not elenco:
        print("Non ci sono attivita'. Creane una con l'opzione 1.")
        return None
    for numero, a in enumerate(elenco, start=1):
        print(f" {numero}. {a.nome} ({a.tipo})")
    scelta = leggi_numero("Numero attivita' (0 = annulla): ", 0, len(elenco), True)
    if scelta == 0:
        return None
    return elenco[scelta - 1]


def nuova_attivita():
    tipo = leggi_numero("Tipo: 1 = coltura, 2 = allevamento: ", 1, 2, True)
    nome = leggi_testo("Nome: ")
    try:
        if tipo == 1:
            superficie = leggi_numero("Superficie in m2: ")
            resa = leggi_numero("Resa in kg per m2: ")
            prezzo = leggi_numero("Prezzo di vendita in EUR/kg: ")
            a = Coltura(nome, superficie, resa, prezzo)
        else:
            animali = leggi_numero("Numero di animali iniziali: ", intero=True)
            persi = leggi_numero("Animali persi in %: ", 0, 100)
            peso = leggi_numero("Peso medio in kg: ")
            prezzo = leggi_numero("Prezzo di vendita in EUR/kg: ")
            a = Allevamento(nome, animali, persi, peso, prezzo)
    except ValueError as err:
        print(f"Dati non validi: {err}")
        return None
    if database.inserisci_attivita(a):
        print("Attivita' creata.")
        return a
    return None


def modifica_attivita(a):
    print("Premi Invio per lasciare il valore attuale.")
    prezzo = leggi_numero(f"Prezzo EUR/kg [{a.prezzo_kg:g}]: ", facoltativo=True)
    prezzo = a.prezzo_kg if prezzo is None else prezzo
    try:
        if isinstance(a, Coltura):
            sup = leggi_numero(f"Superficie m2 [{a.superficie_m2:g}]: ", facoltativo=True)
            resa = leggi_numero(f"Resa kg/m2 [{a.resa_kg_m2:g}]: ", facoltativo=True)
            nuova = Coltura(a.nome, a.superficie_m2 if sup is None else sup,
                            a.resa_kg_m2 if resa is None else resa, prezzo, a.costi)
        else:
            ani = leggi_numero(f"Animali iniziali [{a.animali_iniziali:g}]: ",
                               intero=True, facoltativo=True)
            persi = leggi_numero(f"Persi % [{a.percentuale_persi:g}]: ", 0, 100,
                                 facoltativo=True)
            peso = leggi_numero(f"Peso medio kg [{a.peso_medio_kg:g}]: ", facoltativo=True)
            nuova = Allevamento(a.nome,
                                a.animali_iniziali if ani is None else ani,
                                a.percentuale_persi if persi is None else persi,
                                a.peso_medio_kg if peso is None else peso,
                                prezzo, a.costi)
    except ValueError as err:
        print(f"Dati non validi: {err}")
        return a
    nuova.id = a.id
    if database.aggiorna_attivita(nuova):
        print("Attivita' aggiornata.")
        return nuova
    return a


def aggiungi_costo(a):
    nome = leggi_testo("Nome della voce di costo: ")
    importo = leggi_numero("Importo in EUR: ")
    try:
        a.aggiungi_costo(nome, importo)
    except ValueError as err:
        print(f"Dati non validi: {err}")
        return
    if database.aggiorna_attivita(a):
        print("Voce di costo aggiunta.")
    else:
        a.costi.pop()


def elimina_costo(a):
    if not a.costi:
        print("Non ci sono voci di costo.")
        return
    for numero, c in enumerate(a.costi, start=1):
        print(f" {numero}. {c['nome']}: {c['importo']:.2f} EUR")
    scelta = leggi_numero("Numero da eliminare (0 = annulla): ", 0, len(a.costi), True)
    if scelta == 0:
        return
    voce = a.elimina_costo(scelta - 1)
    if database.aggiorna_attivita(a):
        print("Voce eliminata.")
    else:
        a.costi.insert(scelta - 1, voce)


def elimina_attivita(a):
    conferma = input(f"Eliminare '{a.nome}' con costi e scenari? (s/n): ").strip().lower()
    if conferma == "s" and database.elimina_attivita(a.id):
        print("Attivita' eliminata.")
        return True
    return False


def scegli_scenario(a):
    elenco = database.leggi_scenari(a.id)
    if not elenco:
        print("Non ci sono scenari per questa attivita'.")
        return None
    for numero, s in enumerate(elenco, start=1):
        print(f" {numero}. {s.nome}: {s.descrizione()}")
    scelta = leggi_numero("Numero scenario (0 = annulla): ", 0, len(elenco), True)
    return None if scelta == 0 else elenco[scelta - 1]


def chiedi_modifiche(a):
    prezzo = leggi_numero(f"Prezzo EUR/kg [base {a.prezzo_kg:g}]: ", facoltativo=True)
    resa = None
    persi = None
    if isinstance(a, Coltura):
        resa = leggi_numero(f"Resa kg/m2 [base {a.resa_kg_m2:g}]: ", facoltativo=True)
    else:
        persi = leggi_numero(f"Persi % [base {a.percentuale_persi:g}]: ", 0, 100,
                             facoltativo=True)
    return prezzo, resa, persi


def nuovo_scenario(a):
    nome = leggi_testo("Nome dello scenario (es. prezzo basso): ")
    print("Premi Invio per lasciare invariato il valore.")
    prezzo, resa, persi = chiedi_modifiche(a)
    try:
        s = Scenario(nome, prezzo, resa, persi, attivita_id=a.id, nome_attivita=a.nome)
    except ValueError as err:
        print(f"Dati non validi: {err}")
        return
    if database.inserisci_scenario(s):
        print("Scenario salvato.")


def modifica_scenario(a):
    s = scegli_scenario(a)
    if s is None:
        return
    print("Premi Invio per lasciare invariato il valore.")
    prezzo, resa, persi = chiedi_modifiche(a)
    try:
        nuovo = Scenario(s.nome, prezzo, resa, persi, s.attivita_id,
                         s.nome_attivita, s.id)
    except ValueError as err:
        print(f"Dati non validi: {err}")
        return
    if database.aggiorna_scenario(nuovo):
        print("Scenario aggiornato.")


def confronta_scenari(a):
    lista = database.leggi_scenari(a.id)
    if not lista:
        print("Crea almeno uno scenario per fare il confronto.")
        return None
    righe = scenari.confronta(a, lista)
    print()
    print(scenari.tabella_testo(righe))
    print(scenari.statistiche_testo(scenari.statistiche(righe)))
    return righe


def menu_scenari(a):
    voci = [(1, "Nuovo scenario"), (2, "Elenco scenari"), (3, "Confronta scenari"),
            (4, "Modifica scenario"), (5, "Elimina scenario"), (0, "Indietro")]
    while True:
        stampa_menu(f"Scenari di {a.nome}", voci)
        scelta = leggi_numero("Scegli un'opzione: ", 0, 5, True)
        if scelta == 0:
            return
        elif scelta == 1:
            nuovo_scenario(a)
        elif scelta == 2:
            elenco = database.leggi_scenari(a.id)
            if not elenco:
                print("Non ci sono scenari.")
            for s in elenco:
                print(f" - {s.nome}: {s.descrizione()}")
        elif scelta == 3:
            confronta_scenari(a)
        elif scelta == 4:
            modifica_scenario(a)
        elif scelta == 5:
            s = scegli_scenario(a)
            if s is not None and database.elimina_scenario(s.id):
                print("Scenario eliminato.")


def menu_esporta(a):
    voci = [(1, "Risultati di tutte le attivita' in CSV"),
            (2, "Confronto scenari in CSV"),
            (3, "Copia dei dati in JSON"),
            (4, "Scheda di calcolo in PDF"),
            (5, "Confronto scenari in PDF"),
            (0, "Indietro")]
    stampa_menu("Esporta e stampa", voci)
    scelta = leggi_numero("Scegli un'opzione: ", 0, 5, True)
    if scelta == 1:
        percorso = archivio.percorso_uscita("risultati.csv")
        if archivio.esporta_risultati_csv(database.leggi_attivita(), percorso):
            print(f"Creato {percorso}")
    elif scelta == 3:
        if archivio.esporta_da_database():
            print(f"Creato {archivio.FILE_DATI}")
    elif scelta in (2, 4, 5):
        if a is None:
            print("Scegli prima un'attivita' (opzione 2).")
        elif scelta == 4:
            percorso = archivio.percorso_uscita(f"scheda_{a.nome}.pdf")
            if stampa.pdf_attivita(a, percorso):
                print(f"Creato {percorso}")
        else:
            righe = confronta_scenari(a)
            if righe is not None:
                if scelta == 2:
                    percorso = archivio.percorso_uscita(f"confronto_{a.nome}.csv")
                    ok = archivio.esporta_confronto_csv(righe, percorso)
                else:
                    percorso = archivio.percorso_uscita(f"confronto_{a.nome}.pdf")
                    ok = stampa.pdf_confronto(a, righe, percorso)
                if ok:
                    print(f"Creato {percorso}")


def avvia():
    print("=========== AgroPrezzi ===========")
    utente = login()
    if utente is None:
        print("Accesso negato.")
        return
    print(f"Benvenuto, {utente}!")
    corrente = None
    voci = [(1, "Nuova attivita'"), (2, "Scegli un'attivita'"),
            (3, "Calcola costi, ricavi e margine"),
            (4, "Aggiungi una voce di costo"), (5, "Elimina una voce di costo"),
            (6, "Modifica l'attivita'"), (7, "Elimina l'attivita'"),
            (8, "Scenari (salva e confronta)"),
            (9, "Esporta e stampa"), (0, "Esci")]
    while True:
        stampa_menu("AgroPrezzi", voci)
        if corrente is not None:
            print(f"Attivita' scelta: {corrente.nome}")
        scelta = leggi_numero("Scegli un'opzione: ", 0, 9, True)
        if scelta == 0:
            print("Arrivederci!")
            return
        if scelta == 1:
            nuova = nuova_attivita()
            if nuova is not None:
                corrente = nuova
        elif scelta == 2:
            nuova = scegli_attivita()
            if nuova is not None:
                corrente = nuova
        elif scelta == 9:
            menu_esporta(corrente)
        elif corrente is None:
            print("Scegli prima un'attivita' (opzione 2).")
        elif scelta == 3:
            print()
            print("\n".join(corrente.riepilogo()))
        elif scelta == 4:
            aggiungi_costo(corrente)
        elif scelta == 5:
            elimina_costo(corrente)
        elif scelta == 6:
            corrente = modifica_attivita(corrente)
        elif scelta == 7:
            if elimina_attivita(corrente):
                corrente = None
        elif scelta == 8:
            menu_scenari(corrente)
