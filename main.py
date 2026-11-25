import sys

import archivio
import database
import utenti


def prepara_dati():
    if not database.crea_tabelle():
        print("Impossibile preparare il database.")
        return False
    utenti.inizializza_utenti()
    if not database.leggi_attivita():
        archivio.importa_in_database()
    return True


def main():
    if not prepara_dati():
        return
    if "--gui" in sys.argv:
        import gui
        gui.avvia()
    else:
        import tui
        tui.avvia()
    archivio.esporta_da_database()


if __name__ == "__main__":
    main()
