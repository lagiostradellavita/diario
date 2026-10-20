"""Invio delle email, quando c'e' una casella con cui mandarle.

L'applicazione non ha una posta propria: si appoggia a un server SMTP che
l'utente configura con quattro variabili d'ambiente. Su Render si scrivono
nella scheda Environment, e da qui non si vedono mai - il codice le legge, non
le stampa e non le salva da nessuna parte.

    SMTP_HOST       smtp.gmail.com
    SMTP_PORT       587
    SMTP_USER       asslagiostradellavita@gmail.com
    SMTP_PASSWORD   la password per le app generata da Google, non quella
                    dell'account: sedici lettere, si crea da
                    myaccount.google.com/apppasswords e richiede la verifica
                    in due passaggi attiva
    SMTP_MITTENTE   facoltativo, il nome che compare come mittente

SE NON E' CONFIGURATO NON SI ROMPE NIENTE. manda() torna semplicemente False:
le richieste d'accesso di Leggo e Conto si vedono comunque nel backoffice,
l'email e' solo l'avviso che ne e' arrivata una.
"""
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr


def configurata() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_USER")
                and os.getenv("SMTP_PASSWORD"))


def manda(destinatario: str, oggetto: str, testo: str) -> bool:
    """Manda una email. Torna True se e' partita, False se non si poteva.

    Non solleva mai: una famiglia che chiede l'accesso non deve vedere un
    errore per una casella configurata male. L'errore vero, quello che serve a
    capire, finisce nei log del server.
    """
    if not configurata():
        return False
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
