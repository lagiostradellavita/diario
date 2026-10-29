"""Invio delle email, quando c'e' una casella con cui mandarle.

L'applicazione non ha una posta propria: si appoggia a un server SMTP che
l'utente configura con quattro variabili d'ambiente. Su Render si scrivono
nella scheda Environment, e da qui non si vedono mai - il codice le legge, non
le stampa e non le salva da nessuna parte.

    SMTP_HOST       smtps.aruba.it
    SMTP_PORT       465
    SMTP_USER       info@lagiostradellavita.it
    SMTP_PASSWORD   la password di quella casella
    SMTP_MITTENTE   facoltativo, il nome che compare come mittente

ATTENZIONE: SUL PIANO GRATUITO DI RENDER L'SMTP NON PARTE. Da settembre 2025
Render blocca le porte 25, 465 e 587 dei servizi gratuiti: la connessione va in
timeout e nessuna email esce. Le strade sono due:

- Brevo (brevo.com, societa' francese, dati in Europa), che si chiama via HTTPS
  e quindi passa anche dal piano gratuito:
    BREVO_API_KEY      la chiave API, da app.brevo.com -> SMTP e API -> Chiavi API
    POSTA_MITTENTE     l'indirizzo da cui partono, verificato su Brevo
                       (info@lagiostradellavita.it)
    SMTP_MITTENTE      facoltativo, il nome che compare come mittente
- un piano a pagamento di Render, e allora l'SMTP qui sotto funziona, anche
  quello di Aruba (smtps.aruba.it, porta 465, utente = l'indirizzo intero).

Se c'e' BREVO_API_KEY si usa Brevo, altrimenti l'SMTP.

SE NON E' CONFIGURATO NON SI ROMPE NIENTE. manda() torna semplicemente False:
le richieste d'accesso di Leggo e Conto si vedono comunque nel backoffice,
l'email e' solo l'avviso che ne e' arrivata una.
"""
import json
import os
import smtplib
import ssl
import urllib.request
from email.message import EmailMessage
from email.utils import formataddr


def _brevo() -> bool:
    return bool(os.getenv("BREVO_API_KEY") and os.getenv("POSTA_MITTENTE"))


def configurata() -> bool:
    return _brevo() or bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_USER")
                            and os.getenv("SMTP_PASSWORD"))


def _manda_brevo(destinatario: str, oggetto: str, testo: str) -> bool:
    corpo = {"sender": {"name": os.getenv("SMTP_MITTENTE") or "Leggo e Conto", "email": os.getenv("POSTA_MITTENTE")},
             "to": [{"email": destinatario}], "subject": oggetto, "textContent": testo}
    r = urllib.request.Request(os.getenv("BREVO_URL") or "https://api.brevo.com/v3/smtp/email",
                               data=json.dumps(corpo).encode(), method="POST",
                               headers={"api-key": os.getenv("BREVO_API_KEY"), "content-type": "application/json",
                                        "accept": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=20) as x:
            return 200 <= x.status < 300
    except urllib.error.HTTPError as e:
        print("[posta] Brevo ha rifiutato l'email a %s: %s %s" % (destinatario, e.code, e.read()[:300]))
    except Exception as e:                      # noqa: BLE001
        print("[posta] Brevo non raggiungibile per %s: %s" % (destinatario, e))
    return False


# le email partono da info@, che la cooperativa legge: chi ha un dubbio puo' rispondere
PIEDE = "\n--\nLa Giostra della Vita - per qualsiasi domanda rispondi a questa email.\n"


def manda(destinatario: str, oggetto: str, testo: str) -> bool:
    """Manda una email. Torna True se e' partita, False se non si poteva.

    Non solleva mai: una famiglia che chiede l'accesso non deve vedere un
    errore per una casella configurata male. L'errore vero, quello che serve a
    capire, finisce nei log del server.
    """
    if not configurata():
        return False
    testo = testo.rstrip("\n") + "\n" + PIEDE
    if _brevo():
        return _manda_brevo(destinatario, oggetto, testo)
    host = os.getenv("SMTP_HOST")
    porta = int(os.getenv("SMTP_PORT") or 587)
    utente = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    mittente = os.getenv("SMTP_MITTENTE") or "Leggo e Conto"

    msg = EmailMessage()
    msg["Subject"] = oggetto
    msg["From"] = formataddr((mittente, utente))
    msg["To"] = destinatario
    msg.set_content(testo)

    try:
        contesto = ssl.create_default_context()
        if porta == 465:
            with smtplib.SMTP_SSL(host, porta, context=contesto, timeout=20) as s:
                s.login(utente, password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, porta, timeout=20) as s:
                s.starttls(context=contesto)
                s.login(utente, password)
                s.send_message(msg)
        return True
    except Exception as e:                      # noqa: BLE001
        print("[posta] invio non riuscito a %s: %s" % (destinatario, e))
        return False
