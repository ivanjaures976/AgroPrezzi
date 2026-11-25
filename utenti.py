import getpass
import hashlib
import hmac
import os

import database

# Le credenziali NON sono nel codice. Al primo avvio si inseriscono da terminale
# oppure con la variabile d'ambiente AGROPREZZI_UTENTI="utente1:password1,utente2:password2"


def calcola_hash(password, sale):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                               bytes.fromhex(sale), 100000).hex()


def _credenziali():
    coppie = []
    for voce in os.environ.get("AGROPREZZI_UTENTI", "").split(","):
        if ":" in voce:
            username, password = voce.split(":", 1)
            if username.strip() and password:
                coppie.append((username.strip(), password))
    if coppie:
        return coppie
    print("Primo avvio: crea gli utenti (invio vuoto per terminare).")
    for i in range(2):
        username = input(f"Utente {i + 1}: ").strip()
        if not username:
            break
        password = getpass.getpass("Password: ")
        if password:
            coppie.append((username, password))
    return coppie


def inizializza_utenti():
    if database.conta_utenti() != 0:
        return
    for username, password in _credenziali():
        sale = os.urandom(16).hex()
        database.inserisci_utente(username, sale, calcola_hash(password, sale))


def accedi(username, password):
    riga = database.leggi_utente(username.strip())
    if riga is None:
        return False
    sale, hash_salvato = riga
    return hmac.compare_digest(calcola_hash(password, sale), hash_salvato)