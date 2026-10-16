# Sentinelle VPS (surveillance externe)

Petit robot **gratuit** qui vit chez GitHub et surveille le VPS de Jérémy.

- Toutes les 15 minutes : test TCP sur `VPS_HOST:VPS_PORT` (port SSH par défaut)
- **1 alerte Telegram** quand le serveur devient injoignable (après 2 échecs consécutifs ≈ 30 min)
- **1 alerte Telegram** quand il revient
- Aucun autre message : zéro spam
- N'écrit aucune donnée de Jérémy : seul `etat.json` (up/down + compteur) est versionné

## Secrets à configurer (Settings → Secrets and variables → Actions)

| Nom | Valeur |
|---|---|
| `TELEGRAM_BOT_TOKEN` | token du bot Telegram (jamais en clair dans le repo) |
| `TELEGRAM_CHAT_ID` | `6314421909` |
| `VPS_HOST` | `72.62.38.150` |
| `VPS_PORT` | `22` |

## Tester

Actions → *Sentinelle VPS* → **Run workflow** → cocher `test` → un message
« 🧪 Test de la sentinelle » doit arriver sur Telegram.

## Notes

- Le cron GitHub peut avoir quelques minutes de retard aux heures de pointe (normal).
- Un commit par jour au minimum est fait pour que GitHub ne désactive pas le
  planificateur après 60 jours d'inactivité.
- ⚠️ À mettre à jour quand le VPS change d'adresse (migration Oracle) :
  nouvelles valeurs dans les secrets `VPS_HOST` / `VPS_PORT`.
