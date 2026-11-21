"""Un generatore di PDF minimale, senza librerie esterne (come la copertina
dell'app di contabilita'): scrive pagine di testo in Helvetica con la codifica
WinAnsi, cosi' gli accenti italiani ci sono e il resto diventa '?'. Serve a
comporre la Ricevuta e l'Allegato G lato server, per poterli scrivere su Dropbox.

Non e' un impaginatore: riceve righe gia' pronte (testo, dimensione, grassetto)
e le dispone dall'alto verso il basso, impaginando su piu' fogli A4 se servono.
"""
from typing import List, Tuple

A4 = (595, 842)  # punti (72 dpi)
MARGINE = 56

# Caratteri non ASCII piu' comuni nell'italiano -> codice WinAnsi (cp1252).
def _winansi(s: str) -> bytes:
    out = bytearray()
    for ch in s:
        try:
            b = ch.encode("cp1252")
        except Exception:
            b = b"?"
        out += b
    return bytes(out)


def _esc(s: str) -> bytes:
    b = _winansi(s)
    return b.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


class Riga:
    __slots__ = ("testo", "dim", "grassetto", "sopra")

    def __init__(self, testo: str, dim: int = 11, grassetto: bool = False, sopra: int = 4):
        self.testo = testo
        self.dim = dim
        self.grassetto = grassetto
        self.sopra = sopra  # spazio in piu' sopra la riga


def _taglia(testo: str, dim: int, larghezza: int) -> List[str]:
    # Stima grossolana: Helvetica ~0,52*dim per carattere. Spezza sulle parole.
    max_ch = max(8, int(larghezza / (dim * 0.52)))
    parole = testo.split(" ")
    righe, cur = [], ""
    for p in parole:
        prova = (cur + " " + p).strip()
        if len(prova) <= max_ch:
            cur = prova
        else:
            if cur:
                righe.append(cur)
            cur = p
    if cur:
        righe.append(cur)
    return righe or [""]


def _pagine(righe: List[Riga]) -> List[List[Tuple[int, int, int, bool, str]]]:
    """Ritorna una lista di pagine; ogni pagina e' una lista di
    (x, y, dim, grassetto, testo)."""
    larghezza = A4[0] - 2 * MARGINE
    pagine, cur = [], []
    y = A4[1] - MARGINE
    for r in righe:
        sotto = _taglia(r.testo, r.dim, larghezza)
        for i, t in enumerate(sotto):
            interlinea = int(r.dim * 1.35)
            y -= (r.sopra if i == 0 else 0) + interlinea
            if y < MARGINE:
                pagine.append(cur)
                cur = []
                y = A4[1] - MARGINE - interlinea
            cur.append((MARGINE, y, r.dim, r.grassetto, t))
    pagine.append(cur)
    return pagine


def genera(righe: List[Riga]) -> bytes:
    """Costruisce il PDF e torna i byte."""
    pagine = _pagine(righe)
    oggetti: List[bytes] = []

    def add(b: bytes) -> int:
        oggetti.append(b)
        return len(oggetti)  # numero 1-based

    font_reg = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    font_bold = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")

    page_ids = []
    content_ids = []
    for pg in pagine:
        parti = [b"BT"]
        for (x, y, dim, grassetto, testo) in pg:
            fnt = b"/F2" if grassetto else b"/F1"
            parti.append(b"%s %d Tf 1 0 0 1 %d %d Tm (%s) Tj" % (fnt, dim, x, y, _esc(testo)))
        parti.append(b"ET")
        flusso = b"\n".join(parti)
        cid = add(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(flusso), flusso))
        content_ids.append(cid)

    # Le pagine hanno bisogno dell'id del Pages: lo riserviamo ora.
    pages_id = len(oggetti) + len(pagine) + 1
    for cid in content_ids:
        pid = add(
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] "
            b"/Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> /Contents %d 0 R >>"
            % (pages_id, A4[0], A4[1], font_reg, font_bold, cid)
        )
        page_ids.append(pid)

    kids = b" ".join(b"%d 0 R" % p for p in page_ids)
    real_pages_id = add(b"<< /Type /Pages /Count %d /Kids [%s] >>" % (len(page_ids), kids))
    catalog_id = add(b"<< /Type /Catalog /Pages %d 0 R >>" % real_pages_id)

    # Scrittura con xref.
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0] * (len(oggetti) + 1)
    for i, body in enumerate(oggetti, start=1):
        offsets[i] = len(out)
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 %d\n" % (len(oggetti) + 1)
    out += b"0000000000 65535 f \n"
    for i in range(1, len(oggetti) + 1):
        out += b"%010d 00000 n \n" % offsets[i]
    out += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(oggetti) + 1, catalog_id, xref_pos)
    return bytes(out)
