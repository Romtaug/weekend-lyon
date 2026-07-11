#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
weekend_lyon.py
Chaque vendredi (via GitHub Actions) : envoie un email avec un bouton qui
ouvre Claude avec un prompt DEJA ECRIT. C'est au clic que Claude fait la
recherche (dans ta session Claude, donc sans API et sans cout API).

Aucune dependance externe : uniquement la librairie standard Python.

Variables d'environnement :
  Requis (2 secrets) :
    SMTP_USER   ton adresse Gmail
    SMTP_PASS   mot de passe d'application Gmail (16 caracteres, cf README)
  Optionnels (defauts Gmail deja poses) :
    SMTP_HOST   defaut smtp.gmail.com
    SMTP_PORT   defaut 587 (STARTTLS ; 465 = SSL)
    MAIL_FROM   defaut = SMTP_USER
    MAIL_TO     destinataire(s) separes par virgule (defaut = MAIL_FROM)
    PERIOD          "weekend" (defaut) ou texte libre ("cette semaine", "ce soir"...)
    ORIGIN_ADDRESS  point de depart (defaut: 5 rue de Conde, 69002 Lyon)
    DRY_RUN         "1" pour generer le HTML sans envoyer l'email
"""

import os
import sys
import smtplib
import datetime as dt
from zoneinfo import ZoneInfo
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import quote

ORIGIN = os.environ.get("ORIGIN_ADDRESS") or "5 rue de Conde, 69002 Lyon"
PERIOD = (os.environ.get("PERIOD") or "weekend").strip()
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def compute_period():
    """Renvoie (libelle_court, description_pour_le_prompt)."""
    today = dt.date.today()
    if PERIOD.lower() == "weekend":
        friday, _, sunday = weekend_dates()
        label = f"weekend du {friday.strftime('%d/%m')} au {sunday.strftime('%d/%m/%Y')}"
        desc = (f"le weekend qui vient, du vendredi {friday.strftime('%d/%m/%Y')} soir "
                f"au dimanche {sunday.strftime('%d/%m/%Y')} soir")
        return label, desc
    label = PERIOD
    desc = f"{PERIOD} (nous sommes le {today.strftime('%d/%m/%Y')})"
    return label, desc


def weekend_dates():
    """Vendredi, samedi, dimanche du weekend qui vient (ou en cours)."""
    today = dt.date.today()
    days_to_friday = (4 - today.weekday()) % 7
    friday = today + dt.timedelta(days=days_to_friday)
    return friday, friday + dt.timedelta(days=1), friday + dt.timedelta(days=2)



def build_prompt(desc, extra=""):
    """Le prompt qui sera pre-rempli dans Claude au clic."""
    base = (
        f"Nous sommes le {dt.date.today().strftime('%d/%m/%Y')}. Tu es mon concierge "
        f"lyonnais. Objectif : maximiser mon plaisir et mon divertissement pour "
        f"{desc}, autour du {ORIGIN} (rayon environ 30 min). {extra}"
        "IMPORTANT : fais de VRAIES recherches web et croise au moins deux sources "
        "par reco. Priorise les references lyonnaises : Le Petit Bulletin, Tribune de "
        "Lyon, Lyon Secret ; les billetteries (Fnac Spectacles, Dice, Shotgun, "
        "Billetreduc) ; les salles (Transbordeur, Ninkasi, Halle Tony Garnier, "
        "Radiant-Bellevue, Bourse du Travail, Auditorium, Le Sucre) ; les cinemas (UGC, "
        "Pathe, Comoedia, Institut Lumiere, via Allocine) ; les clubs officiels OL, LOU "
        "Rugby, ASVEL ; les musees (Confluences, MAC, Beaux-Arts, Gadagne). Ne propose "
        "que des choses effectivement programmees sur cette periode precise. Verifie les "
        "dates : pas de suggestions generiques ou intemporelles, pas d'evenement "
        "deja passe. Si une info (date, prix, dispo) n'est pas sure, dis-le. "
        "Verifie aussi la METEO du weekend et adapte (terrasses, parcs, plein air si "
        "beau ; options couvertes si pluie), en le signalant. "
        "Couvre large puis ne garde que le top : concerts et lives, spectacles, "
        "cinema (films forts et sorties du moment), sport en live (OL, LOU, ASVEL, "
        "autres evenements), expos / musees / festivals, restos et bars remarquables "
        "ou nouveautes, et toute pepite ou evenement ponctuel marquant. Cherche un bon "
        "equilibre entre les categories et quelques options gratuites ou pas cheres. "
        "Donne 8 a 12 recos, classees de la meilleure (rang 1) a la moins prioritaire, "
        "avec 2-3 coups de coeur mis en avant. "
        "Pour chaque reco : titre, categorie, lieu et quartier, date et horaire precis, "
        "prix approximatif, distance et temps de trajet depuis le point de depart, "
        "l'ambiance qui lui va le mieux (solo / en couple / entre amis), "
        "une phrase qui donne envie, et un lien officiel ou de reservation. "
        "PRESENTE le resultat comme un ARTEFACT HTML : une carte par reco (badge pour "
        "les coups de coeur, categorie, lieu/quartier, date/horaire, prix, distance et "
        "trajet, tag ambiance, un bouton 'Itineraire' = lien Google Maps en itineraire "
        "depuis le point de depart, et un lien de reservation). Ajoute en tete un mini "
        "programme ideal enchaine pour la periode. "
        "TERMINE par une rangee de 4 boutons cliquables pour rebondir : "
        "'Vendredi soir', 'Samedi', 'Dimanche', 'Gratuit ou pas cher' : chaque bouton "
        "est un lien https://claude.ai/new?q=... qui relance une recherche ciblee sur "
        "ce jour (ou ce critere). "
        "Reste concret, va droit au but."
    )
    return base


def claude_link(prompt):
    return "https://claude.ai/new?q=" + quote(prompt)


def cta(url, text, primary=True):
    if primary:
        style = ("display:inline-block;background:#c2410c;color:#ffffff;font-size:16px;"
                 "font-weight:700;text-decoration:none;padding:14px 26px;border-radius:10px;")
    else:
        style = ("display:inline-block;background:#f1f5f9;color:#0f172a;font-size:14px;"
                 "font-weight:600;text-decoration:none;padding:10px 16px;border-radius:8px;"
                 "border:1px solid #e2e8f0;margin:4px 6px 0 0;")
    return f'<a href="{url}" style="{style}">{text}</a>'


def render_html(label, desc):
    main_url = claude_link(build_prompt(desc))
    fri, sat, sun = weekend_dates()
    fri_url = claude_link(build_prompt(
        f"le vendredi {fri.strftime('%d/%m/%Y')} au soir"))
    sat_url = claude_link(build_prompt(
        f"le samedi {sat.strftime('%d/%m/%Y')} (journee et soiree)"))
    sun_url = claude_link(build_prompt(
        f"le dimanche {sun.strftime('%d/%m/%Y')}"))

    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:28px 0;">
<tr><td align="center">
  <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">
    <tr><td style="padding:0 20px;">
      <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;padding:28px 24px;text-align:center;">
        <div style="font-size:13px;color:#c2410c;font-weight:700;text-transform:uppercase;letter-spacing:.6px;">
          Ton {label}
        </div>
        <div style="font-size:24px;font-weight:800;color:#0f172a;margin:8px 0 6px;">
          Qu'est-ce qu'on fait a Lyon&nbsp;?
        </div>
        <div style="font-size:15px;color:#475569;line-height:1.5;margin-bottom:22px;">
          Clique&nbsp;: Claude cherche pour toi le meilleur du divertissement
          autour du {ORIGIN} et te sort une selection classee avec liens,
          trajets et coups de coeur.
        </div>
        <div style="margin-bottom:18px;">
          {cta(main_url, "Ouvrir Claude &rarr; mon weekend")}
        </div>
        <div style="border-top:1px solid #eef2f7;padding-top:16px;">
          <div style="font-size:12px;color:#94a3b8;margin-bottom:8px;">Ou par jour&nbsp;:</div>
          {cta(fri_url, "Vendredi soir", primary=False)}
          {cta(sat_url, "Samedi", primary=False)}
          {cta(sun_url, "Dimanche", primary=False)}
        </div>
      </div>
      <div style="font-size:12px;color:#94a3b8;text-align:center;margin-top:14px;">
        Le bouton ouvre Claude avec la recherche prete a lancer.
      </div>
    </td></tr>
  </table>
</td></tr></table>
</body></html>"""


def parse_recipients(raw):
    """Accepte une liste separee par virgules ou points-virgules."""
    if not raw:
        return []
    parts = raw.replace(";", ",").split(",")
    return [p.strip() for p in parts if p.strip()]


def send_email(html, subject):
    # 2 secrets requis : SMTP_USER (ton adresse) + SMTP_PASS (mot de passe d'app).
    # Serveur/port Gmail par defaut, surchargeables si besoin.
    smtp_host = os.environ.get("SMTP_HOST") or "smtp.gmail.com"
    smtp_port = int(os.environ.get("SMTP_PORT") or "587")
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"].replace(" ", "")
    mail_from = os.environ.get("MAIL_FROM") or smtp_user
    recipients = parse_recipients(os.environ.get("MAIL_TO")) or [mail_from]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText("Active l'affichage HTML pour voir le bouton.", "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    if smtp_port == 465:
        # Port SSL implicite
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(mail_from, recipients, msg.as_string())
    else:
        # STARTTLS (587 et autres)
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(mail_from, recipients, msg.as_string())
    print(f"Email envoye a {', '.join(recipients)}")


def hour_gate():
    """En run planifie, n'autorise l'envoi qu'a l'heure de Paris voulue.
    SEND_HOUR_PARIS vide => pas de garde-fou (lancements manuels)."""
    target = os.environ.get("SEND_HOUR_PARIS")
    if not target:
        return True
    now_paris = dt.datetime.now(ZoneInfo("Europe/Paris"))
    if now_paris.hour != int(target):
        print(f"Heure de Paris {now_paris.hour}h != {target}h cible : envoi ignore.")
        return False
    return True


def main():
    if not hour_gate():
        return

    label, desc = compute_period()
    print(f"Periode : {label}")
    html = render_html(label, desc)

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "weekend_lyon.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML sauvegarde : {out_path}")

    subject = f"Ton {label} a Lyon - qu'est-ce qu'on fait ?"
    if os.environ.get("DRY_RUN") == "1":
        print("DRY_RUN=1 : email non envoye.")
        return
    send_email(html, subject)


if __name__ == "__main__":
    main()
