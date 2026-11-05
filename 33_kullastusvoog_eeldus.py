"""
33 - Mõõdetud küllastusvoog vs eeldus: kas skripti 27 eeldus 1800 sõidukit tunnis raja kohta peab paika, ja kui suure
osa tunnist saab iga manööver rohelist (efektiivse rohelise osa g/C hinnang).

SISEND
  valjund/10_kullastusvoog.csv                  skripti 10 väljund (10 käib enne): manöövri küllastusvahe ja küllastusvoog
                                                raja kohta järjekorra tühjenemisest (logija andmed, täis tsüklid)
  valjund/24_soojus_ajatelg/24_kanalid.csv      skripti 24 väljund: kanali (raja) täistase, sõidukit tunnis
  valjund/27_sissesoit.csv, 27_maanteed_piir.csv  skripti 27 väljund: sissesõiduteede piirid
  common.load_manoeuvres()                      kanal -> manööver (direction_id) ja pöörde liik

ARVUTUS
  Küllastusvoog s (10): järjekorra 5. ja tagumiste sõidukite vahede (esiotsast esiotsani) mediaan -> 3600 / vahe, sõidukit
    tunnis raja kohta. Arvesse manöövrid, kus on vähemalt MIN_VAATLUSI vahet ja MIN_TSUKLEID täis tsüklit.
  Pöörde liik: manöövri kanalite "turn" (vasakpööre, parempööre); tühi = otse.
  Efektiivse rohelise osa hinnang g/C = täistase raja kohta / s: kui manööver on tipus täis tsüklitega (24 täistase), siis
    läbib rada tunnis s x g/C sõidukit. Näitab, kui suure osa tunnist rada tegelikult küllastusvooga tühjeneb; ülejäänu on
    punane, kollane ja stardikadu. Täistase raja kohta = manöövri kanalite täistasemete keskmine.
  Tundlikkus (27): sissesõiduteede eeldatav piir, kui maantee raja läbilaskevõime (27: RADA_NOM = 1800) asendada mõõdetud
    küllastusvoo alumise kvartiili, mediaani ja ülemise kvartiiliga. Muutub ainult maantee, mille kiirus tipul ei lange
    (27: piiril = False); tee piir = väiksem maanteest ja linna serva ristmikust nagu 27-s.
  ponytail: küllastusvoog on mõõdetud foori stoppjoonel; mitme rajaga maanteel ilma foorita on raja läbilaskevõime
  tavaliselt suurem (1900-2200), seega on stoppjoone väärtus maanteele pigem ettevaatlik hinnang.

VÄLJUND (kaust valjund/)
  33_01_kullastusvoog_eeldus.png
      Näitab: vasakul, kui palju sõidukeid tunnis rada rohelisel tegelikult läbi laseb võrreldes eeldusega 1800; paremal,
      kui suure osa tunnist iga manööver küllastusvooga tühjeneb.
      Kuidas: vasakul punkt = manööver (küllastusvoog raja kohta), rida = pöörde liik; must kriips = liigi mediaan,
      punane katkendjoon = eeldus 1800. Paremal hajuvusdiagramm: x = küllastusvoog raja kohta, y = täistase raja kohta
      (sõid/h), hallid kiirjooned = g/C 0,25 / 0,5 / 0,75; värv = pöörde liik (sinine otse, oranž vasakpööre, roheline
      parempööre). Sildis kõige väiksema ja suurima g/C-ga manöövrid.
  33_kullastusvoog_eeldus.csv   manööver: ristmik, nimi, pöörde liik, radu, s, täistase raja kohta, g/C
  33_sissesoit_tundlikkus.csv   rada (sõid/h), Tallinna hommikuse sissesõidu eeldatav piir ja tavalise sissesõidu osa
"""
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common import (OUT_DIR, load_manoeuvres, set_style, save, save_table, place_labels, short_name, C_BLUE, C_ORANGE,
                    C_AQUA, C_RED, C_GRAY, TEXT, TEXT2)

MIN_VAATLUSI, MIN_TSUKLEID = 100, 20
RADA_NOM = 1800                             # skripti 27 eeldus
LIIGID = {"otse": C_BLUE, "vasakpööre": C_ORANGE, "parempööre": C_AQUA}


def liik(turns):
    """Manöövri kanalite pöörde nimed -> liik: kõige sagedasem vasak- või parempööre, muidu otse."""
    t = [str(x) for x in turns if isinstance(x, str)]
    vp, pp = sum("left" in x for x in t), sum("right" in x for x in t)
    return "otse" if vp + pp == 0 else ("vasakpööre" if vp >= pp else "parempööre")


def maantee_piir(eeldatav, radu, piiril, rada):
    """Maantee eeldatav piir uue raja väärtusega: ainult siis, kui kiirus tipul ei lange (27)."""
    return eeldatav if piiril or np.isnan(eeldatav) else radu * rada


assert liik([np.nan, "left (vasakpööre)"]) == "vasakpööre" and liik([np.nan, np.nan]) == "otse"
assert maantee_piir(5400, 3, False, 2000) == 6000 and maantee_piir(2200, 2, True, 2000) == 2200

set_style()
k = pd.read_csv(OUT_DIR / "10_kullastusvoog.csv")
k = k[(k["vaatlusi"] >= MIN_VAATLUSI) & (k["tais_tsukleid"] >= MIN_TSUKLEID)].copy()
dm = load_manoeuvres()
dm["direction_id"] = dm["direction_id"].astype(int)
k["liik"] = k.apply(lambda r: liik(dm.loc[(dm["mp"] == r["mp"]) & (dm["direction_id"] == r["direction_id"]), "turn"]), axis=1)
kan = pd.read_csv(OUT_DIR / "24_soojus_ajatelg" / "24_kanalid.csv").rename(columns={"kood": "mp", "kanal": "channel"})
kan = kan.merge(dm[["mp", "channel", "direction_id"]], on=["mp", "channel"])
k = k.merge(kan.groupby(["mp", "direction_id"])["taistase_soid_h"].mean().rename("taistase_rajal").reset_index(),
            on=["mp", "direction_id"], how="left")
k["g_C"] = k["taistase_rajal"] / k["kullastusvoog_soid_h_rajal"]
s = k["kullastusvoog_soid_h_rajal"]
q25, q50, q75 = s.quantile([0.25, 0.5, 0.75])
save_table(k[["mp", "direction_id", "manoeuvre", "liik", "radu", "vaatlusi", "tais_tsukleid", "kullastusvahe_s",
              "kullastusvoog_soid_h_rajal", "stardikadu_s", "taistase_rajal", "g_C"]].round(3), "33_kullastusvoog_eeldus")

# --- tundlikkus: skripti 27 sissesõidu eeldatav piir --------------------------------------------------------------------
ss = pd.read_csv(OUT_DIR / "27_sissesoit.csv")
mp_ = pd.read_csv(OUT_DIR / "27_maanteed_piir.csv")
mp_ = mp_[mp_["suund"] == "linna"].set_index("nimi")
ss = ss[ss["tee"] != "Kõik kokku"].copy()
ss["m_nimi"] = ss["maantee"].str.replace(r"\s*\(\d+ rada\)", "", regex=True)
rows = []
for nimi, rada in [("27 eeldus", RADA_NOM), ("mõõdetud alumine kvartiil", q25), ("mõõdetud mediaan", q50),
                   ("mõõdetud ülemine kvartiil", q75)]:
    piir = []
    for _, r in ss.iterrows():
        m = mp_.loc[r["m_nimi"]] if r["m_nimi"] in mp_.index else None
        mt = np.nan if m is None else maantee_piir(r["maantee_eeldatav"], m["radu"], bool(m["piiril"]), rada)
        piir.append(np.nanmin([mt, r["ristmik_eeldatav"]]))
    kokku = np.nansum(piir)
    rows.append(dict(rada=nimi, rada_soid_h=round(rada), sissesoidu_piir=round(kokku),
                     tavaline=round(ss["tavaline"].sum()), kasutus_pct=round(100 * ss["tavaline"].sum() / kokku, 1)))
tund = pd.DataFrame(rows)
assert abs(tund.loc[0, "sissesoidu_piir"] - ss["piir_eeldatav"].sum()) < 2, "27 eeldusega peab tulema sama piir kui 27-s"
save_table(tund, "33_sissesoit_tundlikkus")

# --- joonis -----------------------------------------------------------------------------------------------------------------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6.2), gridspec_kw={"width_ratios": [1, 1.25]})
rng = np.random.default_rng(1)
for i, (l, c) in enumerate(LIIGID.items()):
    x = k.loc[k["liik"] == l, "kullastusvoog_soid_h_rajal"]
    a1.scatter(x, i + rng.uniform(-0.18, 0.18, len(x)), s=28, color=c, alpha=0.75, edgecolor="white", lw=0.6)
    a1.plot([x.median()] * 2, [i - 0.3, i + 0.3], color=TEXT, lw=2.5)
    a1.text(x.median() + 12, i + 0.3, f"{x.median():,.0f}".replace(",", " "), ha="left", va="bottom", fontsize=8.5)
a1.axvline(RADA_NOM, color=C_RED, ls="--", lw=1.5)
a1.text(RADA_NOM + 15, 2.62, f"27 eeldus {RADA_NOM}", color=C_RED, fontsize=8.5, va="center")
a1.set_yticks(range(len(LIIGID)), [f"{l}\n({(k['liik'] == l).sum()} manöövrit)" for l in LIIGID])
a1.set_ylim(-0.6, 2.8)
a1.invert_yaxis()
a1.set_xlabel("küllastusvoog, sõidukit tunnis raja kohta")
tuh = lambda x: f"{x:,.0f}".replace(",", " ")
a1.set_title(f"Mõõdetud küllastusvoog: mediaan {tuh(q50)}, kvartiilid {tuh(q25)}-{tuh(q75)}")

for l, c in LIIGID.items():
    z = k[k["liik"] == l]
    a2.scatter(z["kullastusvoog_soid_h_rajal"], z["taistase_rajal"], s=12 * z["radu"] + 18, color=c, alpha=0.75,
               edgecolor="white", lw=0.6, label=l)
xmax = s.max() * 1.05
z = k.dropna(subset=["g_C"])
ymax = z["taistase_rajal"].max() * 1.15
for g in [0.25, 0.5, 0.75]:
    a2.plot([0, xmax], [0, g * xmax], color=C_GRAY, lw=0.9, ls=":")
    xl = min(xmax, 0.97 * ymax / g)                  # silt seal, kus kiirjoon teljestikust väljub
    a2.text(xl, g * xl, f" g/C {g:.2f}".replace(".", ","), fontsize=8, color=TEXT2, va="bottom" if xl < xmax else "center",
            ha="right" if xl < xmax else "left")
vali = pd.concat([z.nsmallest(3, "g_C"), z.nlargest(4, "g_C")])
place_labels(a2, vali["kullastusvoog_soid_h_rajal"].tolist(), vali["taistase_rajal"].tolist(),
             [f"{m} {short_name(n, 22)}" for m, n in zip(vali["mp"], vali["manoeuvre"])], fontsize=7)
a2.set_xlim(s.min() * 0.9, xmax * 1.1)
a2.set_ylim(0, ymax)
a2.set_xlabel("küllastusvoog, sõidukit tunnis raja kohta (rohelisel)")
a2.set_ylabel("täistase raja kohta, sõidukit tunnis (tipp)")
a2.set_title(f"Rohelise osa hinnang g/C: mediaan {z['g_C'].median():.2f}".replace(".", ","))
a2.legend(title="pöörde liik (suurus = radu)", fontsize=8.5, title_fontsize=8.5, loc="upper left")
fig.text(0.01, -0.02, f"Tallinna hommikuse sissesõidu eeldatav piir (27): rajaga {RADA_NOM} -> {tuh(tund.loc[0, 'sissesoidu_piir'])} "
         f"sõid/h; mõõdetud mediaaniga {tuh(q50)} -> {tuh(tund.loc[2, 'sissesoidu_piir'])} sõid/h (kvartiilidega "
         f"{tuh(tund.loc[1, 'sissesoidu_piir'])}-{tuh(tund.loc[3, 'sissesoidu_piir'])}).", fontsize=8.5, color=TEXT2)
fig.tight_layout()
save(fig, "33_01_kullastusvoog_eeldus")

print(f"manöövreid {len(k)}; s mediaan {q50:.0f} (kvartiilid {q25:.0f}-{q75:.0f}); "
      + ", ".join(f"{l} {k.loc[k['liik'] == l, 'kullastusvoog_soid_h_rajal'].median():.0f} (n={(k['liik'] == l).sum()})" for l in LIIGID)
      + f"; g/C mediaan {z['g_C'].median():.2f}, vahemik {z['g_C'].min():.2f}-{z['g_C'].max():.2f}")
print(tund.to_string(index=False))
