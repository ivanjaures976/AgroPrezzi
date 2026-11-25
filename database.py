import sqlite3
from pathlib import Path

from modelli import Coltura, Allevamento
from scenari import Scenario

FILE_DB = Path(__file__).parent / "agroprezzi.db"

ultimo_errore = ""


def _connetti():
    db = sqlite3.connect(FILE_DB)
    db.execute("PRAGMA foreign_keys = ON")
    return db


def _segnala(err):
    global ultimo_errore
    ultimo_errore = str(err)
    print("ERRORE, effettuo il ROLLBACK!", err)


def crea_tabelle():
    db = _connetti()
    cursor = db.cursor()
    try:
        cursor.execute("""CREATE TABLE IF NOT EXISTS utente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            sale TEXT NOT NULL,
            hash TEXT NOT NULL)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS attivita (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL CHECK (tipo IN ('coltura', 'allevamento')),
            nome TEXT NOT NULL UNIQUE,
            prezzo_kg REAL NOT NULL,
            superficie_m2 REAL,
            resa_kg_m2 REAL,
            animali_iniziali INTEGER,
            percentuale_persi REAL,
            peso_medio_kg REAL)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS costo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attivita_id INTEGER NOT NULL
                REFERENCES attivita(id) ON DELETE CASCADE,
            nome TEXT NOT NULL,
            importo REAL NOT NULL)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS scenario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attivita_id INTEGER NOT NULL
                REFERENCES attivita(id) ON DELETE CASCADE,
            nome TEXT NOT NULL,
            prezzo_kg REAL,
            resa_kg_m2 REAL,
            percentuale_persi REAL,
            UNIQUE (attivita_id, nome))""")
        db.commit()
        return True
    except sqlite3.Error as err:
        _segnala(err)
        db.rollback()
        return False
    finally:
        db.close()


def _valori_attivita(a):
    d = a.a_dizionario()
    return (d["tipo"], d["nome"], d["prezzo_kg"], d.get("superficie_m2"),
            d.get("resa_kg_m2"), d.get("animali_iniziali"),
            d.get("percentuale_persi"), d.get("peso_medio_kg"))


def _righe_costi(a):
    return [(a.id, c["nome"], c["importo"]) for c in a.costi]


def inserisci_attivita(a):
    db = _connetti()
    cursor = db.cursor()
    sql = """INSERT INTO attivita (tipo, nome, prezzo_kg, superficie_m2,
             resa_kg_m2, animali_iniziali, percentuale_persi, peso_medio_kg)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
    try:
        cursor.execute(sql, _valori_attivita(a))
        a.id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO costo (attivita_id, nome, importo) VALUES (?, ?, ?)",
            _righe_costi(a))
        db.commit()
        return True
    except sqlite3.Error as err:
        _segnala(err)
        db.rollback()
        a.id = None
        return False
    finally:
        db.close()


def leggi_attivita():
    db = _connetti()
    cursor = db.cursor()
    elenco = []
    try:
        cursor.execute("""SELECT id, tipo, nome, prezzo_kg, superficie_m2,
                          resa_kg_m2, animali_iniziali, percentuale_persi,
                          peso_medio_kg FROM attivita ORDER BY nome""")
        for r in cursor.fetchall():
            if r[1] == "coltura":
                a = Coltura(r[2], r[4], r[5], r[3])
            else:
                a = Allevamento(r[2], r[6], r[7], r[8], r[3])
            a.id = r[0]
            cursor.execute("SELECT nome, importo FROM costo "
                           "WHERE attivita_id = ? ORDER BY id", (a.id,))
            a.costi = [{"nome": n, "importo": i} for n, i in cursor.fetchall()]
            elenco.append(a)
    except (sqlite3.Error, ValueError) as err:
        _segnala(err)
    finally:
        db.close()
    return elenco


def aggiorna_attivita(a):
    db = _connetti()
    cursor = db.cursor()
    sql = """UPDATE attivita SET tipo = ?, nome = ?, prezzo_kg = ?,
             superficie_m2 = ?, resa_kg_m2 = ?, animali_iniziali = ?,
             percentuale_persi = ?, peso_medio_kg = ? WHERE id = ?"""
    try:
        cursor.execute(sql, _valori_attivita(a) + (a.id,))
        cursor.execute("DELETE FROM costo WHERE attivita_id = ?", (a.id,))
        cursor.executemany(
            "INSERT INTO costo (attivita_id, nome, importo) VALUES (?, ?, ?)",
            _righe_costi(a))
        db.commit()
        return True
    except sqlite3.Error as err:
        _segnala(err)
        db.rollback()
        return False
    finally:
        db.close()


def elimina_attivita(id_attivita):
    db = _connetti()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM attivita WHERE id = ?", (id_attivita,))
        db.commit()
        return True
    except sqlite3.Error as err:
        _segnala(err)
        db.rollback()
        return False
    finally:
        db.close()


def inserisci_scenario(s):
    db = _connetti()
    cursor = db.cursor()
    sql = """INSERT INTO scenario (attivita_id, nome, prezzo_kg, resa_kg_m2,
             percentuale_persi) VALUES (?, ?, ?, ?, ?)"""
    try:
        cursor.execute(sql, (s.attivita_id, s.nome, s.prezzo_kg,
                             s.resa_kg_m2, s.percentuale_persi))
        s.id = cursor.lastrowid
        db.commit()
        return True
    except sqlite3.Error as err:
        _segnala(err)
        db.rollback()
        s.id = None
        return False
    finally:
        db.close()


def leggi_scenari(id_attivita=None):
    db = _connetti()
    cursor = db.cursor()
    sql = """SELECT s.id, s.attivita_id, a.nome, s.nome, s.prezzo_kg,
             s.resa_kg_m2, s.percentuale_persi
             FROM scenario s JOIN attivita a ON a.id = s.attivita_id"""
    parametri = ()
    if id_attivita is not None:
        sql += " WHERE s.attivita_id = ?"
        parametri = (id_attivita,)
    sql += " ORDER BY s.id"
    elenco = []
    try:
        cursor.execute(sql, parametri)
        for r in cursor.fetchall():
            elenco.append(Scenario(r[3], r[4], r[5], r[6], attivita_id=r[1],
                                   nome_attivita=r[2], id_db=r[0]))
    except (sqlite3.Error, ValueError) as err:
        _segnala(err)
    finally:
        db.close()
    return elenco


def aggiorna_scenario(s):
    db = _connetti()
    cursor = db.cursor()
    sql = """UPDATE scenario SET nome = ?, prezzo_kg = ?, resa_kg_m2 = ?,
             percentuale_persi = ? WHERE id = ?"""
    try:
        cursor.execute(sql, (s.nome, s.prezzo_kg, s.resa_kg_m2,
                             s.percentuale_persi, s.id))
        db.commit()
        return True
    except sqlite3.Error as err:
        _segnala(err)
        db.rollback()
        return False
    finally:
        db.close()


def elimina_scenario(id_scenario):
    db = _connetti()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM scenario WHERE id = ?", (id_scenario,))
        db.commit()
        return True
    except sqlite3.Error as err:
        _segnala(err)
        db.rollback()
        return False
    finally:
        db.close()


def conta_utenti():
    db = _connetti()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM utente")
        return cursor.fetchone()[0]
    except sqlite3.Error as err:
        _segnala(err)
        return -1
    finally:
        db.close()


def inserisci_utente(username, sale, hash_password):
    db = _connetti()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO utente (username, sale, hash) VALUES (?, ?, ?)",
                       (username, sale, hash_password))
        db.commit()
        return True
    except sqlite3.Error as err:
        _segnala(err)
        db.rollback()
        return False
    finally:
        db.close()


def leggi_utente(username):
    db = _connetti()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT sale, hash FROM utente WHERE username = ?",
                       (username,))
        return cursor.fetchone()
    except sqlite3.Error as err:
        _segnala(err)
        return None
    finally:
        db.close()
