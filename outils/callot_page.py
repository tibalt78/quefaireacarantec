"""Génère callot.html : page « Horaires de passage vers l'île Callot » (pensée pour Google).

La page contient TOUTE l'année (toutes les dates de CALLOT_RAW, dans index.html) en HTML statique,
et c'est le navigateur du visiteur qui masque les jours passés, met en avant aujourd'hui et affiche
le statut en direct (route praticable / submergée, prochain passage, compte à rebours).
=> À relancer seulement quand CALLOT_RAW change (horaires de l'année suivante, correction).

Source des horaires : Office de tourisme Baie de Morlaix (calendrier annuel en PDF, d'après le Shom).

Usage (depuis la racine du dépôt) : python3 outils/callot_page.py
"""
import datetime, html, json, os, re, sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOIS = ["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre"]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
SOURCE = ("Office de tourisme Baie de Morlaix", "https://www.baiedemorlaix.bzh")
PHOTOS = [("route_promeneurs", "Promeneurs sur la route de Callot"), ("chapelle_couchant", "La chapelle de Callot au couchant"),
          ("route_soleil", "La route de Callot au soleil"), ("chapelle_ciel", "La chapelle Notre-Dame de Callot"),
          ("cabine_callot", "Cabine de plage face à Callot"), ("route_couple", "Balade sur la route de Callot")]


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


def intervalles(jours):
    """Créneaux en heure locale absolue, les passages de minuit fusionnés : [["2026-11-22T20:18", "2026-11-23T00:38"], …]."""
    out = []
    for d in sorted(jours):
        for a, b in jours[d][0]:
            j = datetime.date.fromisoformat(d)
            ha, ma = map(int, a.split("h")); hb, mb = map(int, b.split("h"))
            deb = datetime.datetime(j.year, j.month, j.day) + datetime.timedelta(hours=ha, minutes=ma)
            fin = datetime.datetime(j.year, j.month, j.day) + datetime.timedelta(hours=hb, minutes=mb)
            if out and abs((datetime.datetime.fromisoformat(out[-1][1]) - deb).total_seconds()) <= 60:
                out[-1][1] = fin.isoformat(timespec="minutes")
            else:
                out.append([deb.isoformat(timespec="minutes"), fin.isoformat(timespec="minutes")])
    return out


def jour1(d):
    return "1er" if d.day == 1 else str(d.day)


def h(t):
    t = t.replace("24h00", "minuit").replace("00h00", "minuit")
    return t[1:] if t[:1] == "0" else t


def ligne_jour(k, slots, coef):
    d = datetime.date.fromisoformat(k)
    jour = f"{JOURS[d.weekday()].capitalize()} {d.day}"
    if not slots:
        cr = '<span class="non">Pas de passage (coefficient trop faible)</span>'
    else:
        cr = " ".join(f'<span class="cr{" nuit" if (int(a[:2]) < 6 or int(a[:2]) >= 21) else ""}">{h(a)} → {h(b)}</span>'
                      for a, b in slots)
    co = f'<span class="co">coef. {html.escape(coef.replace(",", " / "))}</span>' if coef else ""
    return f'<tr data-d="{k}"><th>{jour}</th><td>{cr}</td><td>{co}</td></tr>'


def page(jours):
    dates = sorted(jours)
    if not dates: sys.exit("CALLOT_RAW est vide")
    debut, fin = datetime.date.fromisoformat(dates[0]), datetime.date.fromisoformat(dates[-1])
    annees = sorted({debut.year, fin.year})
    an = " – ".join(str(a) for a in annees)
    blocs, mois_cour = [], None
    for k in dates:
        d = datetime.date.fromisoformat(k)
        if (d.year, d.month) != mois_cour:
            if mois_cour: blocs.append("</tbody></table></section>")
            mois_cour = (d.year, d.month)
            blocs.append(f'<section class="mois" data-m="{d.year}-{d.month:02d}"><h2>{MOIS[d.month].capitalize()} {d.year}</h2>'
                         '<table><tbody>')
        blocs.append(ligne_jour(k, *jours[k]))
    blocs.append("</tbody></table></section>")
    photos = "".join(f'<figure><img src="/img/callot/{n}.jpg" alt="{html.escape(t)}" loading="lazy" width="600" height="800"></figure>'
                     for n, t in PHOTOS if os.path.exists(os.path.join(RACINE, "img", "callot", n + ".jpg")))
    data = json.dumps(intervalles(jours), separators=(",", ":"))
    src_nom, src_url = SOURCE
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Horaires de passage vers l'île Callot (Carantec) – {an}</title>
<meta name="description" content="Quand peut-on aller à l'île Callot par la route submersible ? Horaires de passage jour par jour {an}, statut en direct et coefficients de marée, à Carantec.">
<link rel="canonical" href="https://quefaireacarantec.fr/callot.html">
<meta property="og:title" content="Horaires de passage vers l'île Callot – en direct">
<meta property="og:description" content="La route de Callot est-elle praticable maintenant ? Les créneaux jour par jour.">
<meta property="og:image" content="https://quefaireacarantec.fr/img/callot.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@700&family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<style>
body{{margin:0;background:#f3eee6;color:#24243C;font-family:Poppins,system-ui,sans-serif;font-size:15px;line-height:1.5}}
.wrap{{max-width:760px;margin:0 auto;padding:22px 16px 40px}}
a{{color:#2f8a7d}}
h1{{font-family:Lora,serif;font-size:30px;line-height:1.15;margin:10px 0 8px}}
h2{{font-family:Lora,serif;font-size:22px;margin:28px 0 8px}}
.statut{{border-radius:16px;padding:16px 18px;margin:16px 0;color:#fff;background:#2f8a7d}}
.statut.ok{{background:#2f9e5b}} .statut.bientot{{background:#d9822b}} .statut.ko{{background:#24243C}}
.statut b{{display:block;font-size:20px;line-height:1.25}} .statut span{{opacity:.9}}
.alerte{{background:#fff4d6;border-left:5px solid #F2C230;padding:12px 14px;border-radius:8px;margin:14px 0}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden}}
th,td{{padding:8px 10px;border-bottom:1px solid #e6e0d6;text-align:left;vertical-align:top}}
th{{white-space:nowrap;font-weight:600;width:88px}}
@media(max-width:480px){{th,td{{padding:8px 6px}} .co{{font-size:12px}}}}
tr.auj{{background:#e2f2ef}} tr.auj th::after{{content:" · aujourd'hui";color:#2f8a7d;font-weight:400;font-size:12px}}
.passe{{display:none}} body.tout .passe{{display:revert}}
.cr{{display:inline-block;white-space:nowrap;background:#2f8a7d;color:#fff;border-radius:6px;padding:1px 8px;margin:2px 4px 2px 0;font-weight:600}}
.cr.nuit{{background:#24243C}}
.non{{color:#7c7c8e}} .co{{color:#7c7c8e;font-size:13px;white-space:nowrap}}
button.lien{{background:none;border:0;color:#2f8a7d;text-decoration:underline;font:inherit;cursor:pointer;padding:0}}
.galerie{{display:flex;gap:10px;overflow-x:auto;scroll-snap-type:x mandatory;padding:4px 0 10px}}
.galerie figure{{margin:0;flex:0 0 46%;max-width:240px;scroll-snap-align:start}}
.galerie img{{width:100%;height:auto;aspect-ratio:3/4;object-fit:cover;border-radius:12px;display:block}}
.appel{{background:#fff;border-radius:14px;padding:14px 16px;border:2px dashed #C8287A}}
.source{{font-size:13px;color:#4a4a62}}
footer{{margin-top:30px;color:#7c7c8e;font-size:12.5px}}
</style>
</head>
<body><div class="wrap">
<p><a href="/">← Tout l'agenda de Carantec et ses environs</a></p>
<h1>Horaires de passage vers l'île Callot</h1>
<div class="statut" id="statut" aria-live="polite"><b>Horaires de passage {an}</b><span>Activez JavaScript pour voir le statut en direct.</span></div>
<p>L'île Callot, à Carantec, est reliée au continent par une route submersible, praticable seulement à marée basse.
Voici les créneaux de passage <b>jour par jour</b> (en bleu nuit : créneaux de nuit).</p>
<p class="source">Source : calendrier des horaires de passage de l'<a href="{src_url}" target="_blank" rel="noopener">{src_nom}</a>,
établi d'après les données du Shom. Coefficients de marée : Météo Consult (marine.meteoconsult.fr).</p>
<div class="alerte">⚠️ <b>La mer remonte vite.</b> Soyez sur la route au plus tard 30 minutes avant la fin du créneau, ne vous engagez jamais
si l'eau arrive sur la route et suivez les panneaux sur place. Horaires indicatifs : le vent, la houle et la pression peuvent les modifier.</div>
<p><button class="lien" id="toggle" type="button">Afficher aussi les jours passés</button></p>
{"".join(blocs)}
<h2>Callot en images</h2>
<div class="galerie">{photos}</div>
<div class="appel">📸 <b>Vos plus belles photos de Callot !</b> Envoyez-les à
<a href="mailto:quefaireacarantec@gmail.com?subject=Ma%20photo%20de%20Callot">quefaireacarantec@gmail.com</a>
avec votre prénom, ou identifiez <b>@quefaireacarantec</b> sur Instagram. Les plus belles seront publiées ici et sur nos réseaux,
avec votre nom. En nous les envoyant, vous acceptez cette publication.</div>
<p>Chaque jour, les horaires de Callot sont aussi publiés en story et en vidéo sur Facebook et Instagram : <b>@quefaireacarantec</b>.</p>
<footer>Page indépendante et bénévole, non officielle. Horaires du {jour1(debut)} {MOIS[debut.month]} {debut.year} au {jour1(fin)} {MOIS[fin.month]} {fin.year}.
· <a href="/">Agenda</a> · <a href="/carte.html">Carte du jour</a> · <a href="/mentions-legales.html">Mentions légales</a></footer>
</div>
<script>
const CR={data};
const pad=n=>String(n).padStart(2,"0");
const iso=d=>d.getFullYear()+"-"+pad(d.getMonth()+1)+"-"+pad(d.getDate());
const hh=d=>d.getHours()===0&&d.getMinutes()===0?"minuit":d.getHours()+"h"+pad(d.getMinutes());
const duree=ms=>{{const m=Math.round(ms/60000),h=Math.floor(m/60);return (h?h+" h ":"")+(h?pad(m%60):m%60)+" min";}};
const JOURS=["dimanche","lundi","mardi","mercredi","jeudi","vendredi","samedi"];
function quand(d,now){{const a=new Date(now);a.setHours(0,0,0,0);const b=new Date(d);b.setHours(0,0,0,0);
  const n=Math.round((b-a)/864e5);return n===0?"aujourd'hui":n===1?"demain":JOURS[d.getDay()]+" "+d.getDate();}}
function majStatut(){{
  const now=new Date(), el=document.getElementById("statut");
  const iv=CR.map(([a,b])=>[new Date(a),new Date(b)]);
  const en=iv.find(([a,b])=>now>=a&&now<b), suiv=iv.find(([a])=>a>now);
  if(en){{const reste=en[1]-now;
    if(reste<=30*60000){{el.className="statut bientot";el.innerHTML=`<b>🟠 Fin du créneau à ${{hh(en[1])}} : ne vous engagez plus</b><span>Plus que ${{duree(reste)}}.${{suiv?` Prochain passage ${{quand(suiv[0],now)}} à ${{hh(suiv[0])}}.`:""}}</span>`;}}
    else{{el.className="statut ok";el.innerHTML=`<b>🟢 La route est praticable en ce moment</b><span>Retour avant ${{hh(en[1])}} (encore ${{duree(reste)}}).</span>`;}}
  }} else if(suiv){{el.className="statut ko";el.innerHTML=`<b>🔴 Route submergée</b><span>Prochain passage ${{quand(suiv[0],now)}} de ${{hh(suiv[0])}} à ${{hh(suiv[1])}} (dans ${{duree(suiv[0]-now)}}).</span>`;}}
  else{{el.className="statut ko";el.innerHTML="<b>Horaires à venir</b><span>Les horaires de l'année suivante seront publiés dès leur parution.</span>";}}
}}
const today=iso(new Date());
document.querySelectorAll("tr[data-d]").forEach(tr=>{{if(tr.dataset.d<today)tr.classList.add("passe");if(tr.dataset.d===today)tr.classList.add("auj");}});
document.querySelectorAll("section.mois").forEach(s=>{{if(!s.querySelector("tr:not(.passe)"))s.classList.add("passe");}});
document.getElementById("toggle").onclick=e=>{{const t=document.body.classList.toggle("tout");e.target.textContent=t?"Masquer les jours passés":"Afficher aussi les jours passés";}};
majStatut(); setInterval(majStatut,30000);
</script>
<script data-goatcounter="https://quefaireacarantec.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</body>
</html>
"""


if __name__ == "__main__":
    out = os.path.join(RACINE, "callot.html")
    open(out, "w", encoding="utf-8").write(page(lire_horaires()))
    print("callot.html écrit")
