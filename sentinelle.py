#!/usr/bin/env python3
"""Sentinelle externe : surveille le VPS de Jeremy et previent sur Telegram
UNIQUEMENT quand l'etat change (panne detectee / retour a la normale).
Ne tourne pas sur le VPS : tourne chez GitHub, donc survit a la panne."""
import json, os, socket, datetime, urllib.request, urllib.parse, sys

# Les runners GitHub n'ont pas de route IPv6 : on force l'IPv4 pour joindre l'API Telegram
_getaddrinfo_orig = socket.getaddrinfo
def _getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return _getaddrinfo_orig(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = _getaddrinfo_ipv4

HOST = os.environ.get("VPS_HOST", "72.62.38.150")
PORT = int(os.environ.get("VPS_PORT", "22"))
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
SEUIL = int(os.environ.get("SEUIL_ECHECS", "2"))
TEST = os.environ.get("FORCE_TEST", "").lower() in ("1", "true", "oui")
ETAT = "etat.json"


def joignable(timeout=10):
    try:
        s = socket.create_connection((HOST, PORT), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False


def telegram(txt):
    if not TOKEN or not CHAT:
        print("!! pas de token/chat -> alerte non envoyee")
        return False
    data = urllib.parse.urlencode({"chat_id": CHAT, "text": txt, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request("https://api.telegram.org/bot%s/sendMessage" % TOKEN, data=data)
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
        print("telegram ok:", r.get("ok"), "| msg_id:", r.get("result", {}).get("message_id"))
        return bool(r.get("ok"))
    except Exception as e:
        print("!! echec envoi telegram:", e)
        return False


def charger():
    try:
        with open(ETAT) as f:
            return json.load(f)
    except Exception:
        return {"etat": "inconnu", "echecs": 0, "jour": ""}


def sauver(st):
    with open(ETAT, "w") as f:
        json.dump(st, f, indent=1, ensure_ascii=False)


def main():
    maintenant = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    jour = maintenant[:10]

    if TEST:
        ok = telegram(
            "🧪 <b>Test de la sentinelle</b>\n"
            "Si tu lis ce message, le robot fonctionne : il te préviendra "
            "quand ton serveur Hostinger tombera.\n<i>%s</i>" % maintenant
        )
        sys.exit(0 if ok else 1)

    st = charger()
    ancien = st.get("etat", "inconnu")
    up = joignable()
    alerte = None

    if up:
        if ancien == "down":
            alerte = telegram(
                "✅ <b>Ton serveur est de retour</b>\n"
                "Il répond à nouveau (%s:%s). Hermes, les crons et les veilles sont relancés."
                % (HOST, PORT)
            )
        st["etat"] = "up"
        st["echecs"] = 0
    else:
        st["echecs"] = int(st.get("echecs", 0)) + 1
        if st["echecs"] >= SEUIL and ancien != "down":
            alerte = telegram(
                "⚠️ <b>Ton serveur ne répond plus</b>\n"
                "Impossible de le joindre (%s:%s) sur %d tests consécutifs, soit environ %d minutes.\n"
                "Tes veilles mail et mes réponses sont à l'arrêt.\n"
                "<i>Dernier test : %s</i>" % (HOST, PORT, SEUIL, SEUIL * 15, maintenant)
            )
            st["etat"] = "down"
        elif st["echecs"] < SEUIL:
            print("panne possible mais sous le seuil (%d/%d) : pas d'alerte" % (st["echecs"], SEUIL))

    # on n'ecrit (donc on ne commit) que si quelque chose a change, ou une fois par jour
    change = st["etat"] != ancien or st.get("jour") != jour
    if change:
        st["jour"] = jour
        st["derniere_verif"] = maintenant
        sauver(st)
    print("verif %s | joignable=%s | etat=%s | echecs=%s | commit=%s | alerte=%s"
          % (maintenant, up, st["etat"], st["echecs"], change, alerte))


main()
