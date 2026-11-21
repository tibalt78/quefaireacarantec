"""Génère callot.html : page statique « Horaires de passage vers l'île Callot » (pensée pour Google).
Lit les horaires dans le tableau CALLOT_RAW de index.html (source unique) et liste les jours à partir
d'aujourd'hui (fuseau Europe/Paris) jusqu'au dernier jour connu.

Usage (depuis la racine du dépôt) : python3 outils/callot_page.py
À relancer à chaque mise à jour du site (tâche du samedi), avant le commit.
"""
import datetime, html, os, re, sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOIS = ["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre"]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def lire_horaires():
    src = open(os.path.join(RACINE, "index.html"), encoding="utf-8").read()
    m = re.search(r"const CALLOT_RAW = `(.*?)`", src, re.S)
    if not m: sys.exit("CALLOT_RAW introuvable dans index.html")
    jours = {}
    for l in m.group(1).strip().splitlines():
        p = l.split()
        if len(p) < 2: continue
        slots = [] if p[1] == "AUCUN" else [s.split("-") for s in p[1].split(",")]
        jours[p[0]] = (slots, p[2] if len(p) > 2 else "")
    return jours


def h(t):
    t = t.replace("24h00", "minuit").replace("00h00", "minuit")
    return t[1:] if t[:1] == "0" else t


def ligne_jour(d, slots, coef):
    jour = f"{JOURS[d.weekday()].capitalize()} {d.day}"
    if not slots:
        cr = '<span class="non">Pas de passage (coefficient trop faible)</span>'
    else:
        parts = []
        for a, b in slots:
            ha = int(a[:2])
            nuit = ha < 6 or ha >= 21
            parts.append(f'<span class="cr{" nuit" if nuit else ""}">{h(a)} → {h(b)}</span>')
        cr = " ".join(parts)
    co = f'<span class="co">coef. {html.escape(coef.replace(",", " / "))}</span>' if coef else ""
    return f'<tr><th>{jour}</th><td>{cr}</td><td>{co}</td></tr>'


def page(jours, aujourd_hui):
    dates = sorted(k for k in jours if k >= aujourd_hui.isoformat())
    if not dates: sys.exit("Aucune date à venir dans CALLOT_RAW")
    fin = datetime.date.fromisoformat(dates[-1])
    blocs, mois_cour = [], None
    for k in dates:
        d = datetime.date.fromisoformat(k)
        if (d.year, d.month) != mois_cour:
            if mois_cour: blocs.append("</tbody></table>")
            mois_cour = (d.year, d.month)
            blocs.append(f'<h2 id="m{d.year}-{d.month:02d}">{MOIS[d.month].capitalize()} {d.year}</h2>'
                         '<table><tbody>')
        blocs.append(ligne_jour(d, *jours[k]))
    blocs.append("</tbody></table>")
    maj = aujourd_hui.strftime("%d/%m/%Y")
    titre = f"Horaires de passage vers l'île Callot (Carantec) – {MOIS[aujourd_hui.month]} {aujourd_hui.year}"
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre}</title>
<meta name="description" content="Horaires de passage par la route submersible vers l'île Callot à Carantec, jour par jour jusqu'au {fin.day} {MOIS[fin.month]} {fin.year}, avec les coefficients de marée.">
<link rel="canonical" href="https://quefaireacarantec.fr/callot.html">
<meta property="og:title" content="Horaires de passage vers l'île Callot">
<meta property="og:description" content="Quand peut-on aller à l'île Callot par la route ? Les créneaux jour par jour.">
<meta property="og:image" content="https://quefaireacarantec.fr/img/callot.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@700&family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<style>
body{{margin:0;background:#f3eee6;color:#24243C;font-family:Poppins,system-ui,sans-serif;font-size:15px;line-height:1.5}}
.wrap{{max-width:760px;margin:0 auto;padding:22px 16px 40px}}
a{{color:#2f8a7d}}
h1{{font-family:Lora,serif;font-size:30px;line-height:1.15;margin:10px 0 8px}}
h2{{font-family:Lora,serif;font-size:22px;margin:28px 0 8px}}
.alerte{{background:#fff4d6;border-left:5px solid #F2C230;padding:12px 14px;border-radius:8px;margin:14px 0}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden}}
th,td{{padding:8px 10px;border-bottom:1px solid #e6e0d6;text-align:left;vertical-align:top}}
th{{white-space:nowrap;font-weight:600;width:120px}}
.cr{{display:inline-block;background:#2f8a7d;color:#fff;border-radius:6px;padding:1px 8px;margin:2px 4px 2px 0;font-weight:600}}
.cr.nuit{{background:#24243C}}
.non{{color:#7c7c8e}} .co{{color:#7c7c8e;font-size:13px;white-space:nowrap}}
footer{{margin-top:30px;color:#7c7c8e;font-size:12.5px}}
</style>
</head>
<body><div class="wrap">
<p><a href="/">← Tout l'agenda de Carantec et ses environs</a></p>
<h1>Horaires de passage vers l'île Callot</h1>
<p>L'île Callot, à Carantec, est reliée au continent par une route submersible, praticable seulement à marée basse.
Voici les créneaux de passage <b>jour par jour</b>, jusqu'au {fin.day} {MOIS[fin.month]} {fin.year}. Les créneaux en bleu nuit tombent de nuit.</p>
<div class="alerte">⚠️ <b>La mer remonte vite.</b> Respectez l'heure de retour, ne vous engagez jamais sur la route après la fin du créneau
et suivez les panneaux sur place. Horaires donnés à titre indicatif : la météo (vent, houle, pression) peut les modifier.</div>
<p>Chaque jour, la story « Passage vers l'île Callot » est publiée sur Facebook et Instagram : <b>@quefaireacarantec</b>.</p>
{"".join(blocs)}
<footer>Page indépendante et bénévole, non officielle. Mis à jour le {maj}.
· <a href="/">Agenda</a> · <a href="/carte.html">Carte du jour</a> · <a href="/mentions-legales.html">Mentions légales</a></footer>
</div>
<script data-goatcounter="https://quefaireacarantec.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</body>
</html>
"""


if __name__ == "__main__":
    try:
        from zoneinfo import ZoneInfo
        auj = datetime.datetime.now(ZoneInfo("Europe/Paris")).date()
    except Exception:
        auj = datetime.date.today()
    if len(sys.argv) > 1: auj = datetime.date.fromisoformat(sys.argv[1])
    out = os.path.join(RACINE, "callot.html")
    open(out, "w", encoding="utf-8").write(page(lire_horaires(), auj))
    print("callot.html écrit")
