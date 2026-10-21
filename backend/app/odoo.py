"""Gli abbonamenti di Leggo e Conto, letti da Odoo.

Odoo vende gli abbonamenti (sito, pagamenti, fatture); qui si guarda solo se
un'email ha un abbonamento in corso, di che piano e fino a quando. A Odoo non
va niente dei bambini.

Si collega con l'API XML-RPC di Odoo e quattro variabili d'ambiente, che si
scrivono su Render nella scheda Environment:

    ODOO_URL      https://lagiostradellavita.odoo.com   (l'indirizzo dell'istanza)
    ODOO_DB       il nome del database (su Odoo.sh: Impostazioni, in fondo)
    ODOO_UTENTE   l'email dell'utente Odoo con cui si legge
    ODOO_CHIAVE   una chiave API di quell'utente (Preferenze > Sicurezza
                  dell'account > Nuova chiave API), non la password

SE NON E' CONFIGURATO NON SI ROMPE NIENTE: configurato() torna False e gli
accessi arrivano solo dagli avvisi di Odoo (giochi.py, /giochi/odoo/abbonamento)
o dal backoffice.

Gli abbonamenti di Odoo 17 e successivi sono ordini di vendita con
is_subscription: 'subscription_state' vale '3_progress' quando e' in corso;
'next_invoice_date' e' il giorno del prossimo addebito. Il piano si riconosce
dal nome del prodotto: «premium» nel nome vuol dire Premium, il resto e' Base.
"""
import os
import xmlrpc.client
from datetime import datetime, timedelta, timezone

IN_CORSO = {"3_progress"}
MARGINE = timedelta(days=3)   # il giorno dell'addebito il pagamento puo' arrivare in ritardo


def configurato() -> bool:
    return all(os.getenv(k) for k in ("ODOO_URL", "ODOO_DB", "ODOO_UTENTE", "ODOO_CHIAVE"))


def _chiama(model, metodo, args, kw=None):
    url, db = os.getenv("ODOO_URL").rstrip("/"), os.getenv("ODOO_DB")
    utente, chiave = os.getenv("ODOO_UTENTE"), os.getenv("ODOO_CHIAVE")
    uid = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True).authenticate(db, utente, chiave, {})
    if not uid:
        raise RuntimeError("Odoo: utente o chiave non accettati")
    obj = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    return obj.execute_kw(db, uid, chiave, model, metodo, args, kw or {})


def _giorno(v):
    if not v:
        return None
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def piano_da_nomi(nomi) -> str:
    return "premium" if any("premium" in (n or "").lower() for n in nomi) else "base"


def _riassunto(o, prodotti) -> dict:
    """Un abbonamento di Odoo, ridotto a quello che serve: attivo, piano, scadenza."""
    partner = o.get("partner_id") or [None, ""]
    prossimo = _giorno(o.get("next_invoice_date"))
    fine = _giorno(o.get("end_date"))
    scad = min([d for d in (prossimo and prossimo + MARGINE, fine and fine + timedelta(days=1)) if d], default=None)
    return {"rif": o.get("name") or str(o.get("id")), "attivo": o.get("subscription_state") in IN_CORSO,
            "piano": piano_da_nomi(prodotti), "scadenza": scad,
            "nome": partner[1] if isinstance(partner, (list, tuple)) and len(partner) > 1 else None}


CAMPI = ["name", "partner_id", "subscription_state", "next_invoice_date", "end_date", "order_line"]


def _prodotti(righe):
    if not righe:
        return []
    return [r["name"] for r in _chiama("sale.order.line", "read", [righe], {"fields": ["name"]})]


def per_email(email: str):
    """L'abbonamento in corso di quest'email, il migliore se ce n'e' piu' d'uno; None se non c'e'."""
    ordini = _chiama("sale.order", "search_read",
                     [[["is_subscription", "=", True], ["partner_id.email", "=ilike", email]]],
                     {"fields": CAMPI, "order": "id desc", "limit": 20})
    attivi = [_riassunto(o, _prodotti(o.get("order_line"))) for o in ordini]
    attivi = [a for a in attivi if a["attivo"]]
    if not attivi:
        return None
    attivi.sort(key=lambda a: (a["piano"] == "premium", a["scadenza"] or datetime.max.replace(tzinfo=timezone.utc)), reverse=True)
    return attivi[0]


def per_ordine(id_ordine: int):
    """Un abbonamento letto per numero, con l'email del cliente; None se non e' un abbonamento."""
    righe = _chiama("sale.order", "read", [[int(id_ordine)]], {"fields": CAMPI + ["is_subscription"]})
    if not righe or not righe[0].get("is_subscription"):
        return None
    o = righe[0]
    a = _riassunto(o, _prodotti(o.get("order_line")))
    pid = (o.get("partner_id") or [None])[0]
    a["email"] = None
    if pid:
        p = _chiama("res.partner", "read", [[pid]], {"fields": ["email", "name"]})
        if p:
            a["email"], a["nome"] = (p[0].get("email") or "").strip().lower() or None, p[0].get("name")
    return a
