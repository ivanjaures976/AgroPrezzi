from xml.sax.saxutils import escape

import scenari

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer,
                                    Table, TableStyle)
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

ultimo_errore = ""


def _stile_tabella():
    return [("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9)]


def _crea_pdf(percorso, contenuto, formato):
    global ultimo_errore
    if not REPORTLAB_OK:
        ultimo_errore = "Libreria reportlab non installata (pip install reportlab)."
        print(ultimo_errore)
        return False
    try:
        documento = SimpleDocTemplate(str(percorso), pagesize=formato,
                                      title="AgroPrezzi")
        documento.build(contenuto)
        return True
    except Exception as err:
        ultimo_errore = str(err)
        print(f"Errore nella creazione del PDF: {err}")
        return False


def pdf_attivita(attivita, percorso):
    if not REPORTLAB_OK:
        return _crea_pdf(percorso, [], None)
    stili = getSampleStyleSheet()
    contenuto = [Paragraph("AgroPrezzi - Scheda di calcolo", stili["Title"])]
    for riga in attivita.riepilogo():
        contenuto.append(Paragraph(escape(riga), stili["Normal"]))
    contenuto.append(Spacer(1, 12))
    contenuto.append(Paragraph("Voci di costo", stili["Heading2"]))
    dati = [["Voce", "Importo (EUR)"]]
    for c in attivita.costi:
        dati.append([c["nome"], f"{c['importo']:.2f}"])
    dati.append(["TOTALE", f"{attivita.costi_totali():.2f}"])
    tabella = Table(dati, colWidths=[300, 100])
    tabella.setStyle(TableStyle(_stile_tabella() + [
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")]))
    contenuto.append(tabella)
    return _crea_pdf(percorso, contenuto, A4)


def pdf_confronto(attivita, righe, percorso):
    if not REPORTLAB_OK:
        return _crea_pdf(percorso, [], None)
    stili = getSampleStyleSheet()
    contenuto = [Paragraph("AgroPrezzi - Confronto scenari", stili["Title"]),
                 Paragraph(escape(f"Attivita': {attivita.nome} ({attivita.tipo})"),
                           stili["Normal"]),
                 Spacer(1, 12)]
    dati = [["Scenario", "Prezzo", "Kg", "Costi", "Ricavi",
             "Margine", "Margine %", "Diff. dalla base"]]
    stile = _stile_tabella() + [("ALIGN", (1, 0), (-1, -1), "RIGHT")]
    for numero, r in enumerate(righe, start=1):
        dati.append([r["nome"], f"{r['prezzo_kg']:.2f}", f"{r['kg']:.1f}",
                     f"{r['costi']:.2f}", f"{r['ricavi']:.2f}",
                     f"{r['margine']:.2f}", f"{r['margine_pct']:.1f}",
                     f"{r['diff_base']:+.2f}"])
        if r["margine"] < 0:
            stile.append(("TEXTCOLOR", (5, numero), (5, numero), colors.red))
    tabella = Table(dati)
    tabella.setStyle(TableStyle(stile))
    contenuto.append(tabella)
    contenuto.append(Spacer(1, 12))
    contenuto.append(Paragraph("Statistiche sui margini", stili["Heading2"]))
    for riga in scenari.statistiche_testo(scenari.statistiche(righe)).splitlines():
        contenuto.append(Paragraph(escape(riga), stili["Normal"]))
    return _crea_pdf(percorso, contenuto, landscape(A4))
