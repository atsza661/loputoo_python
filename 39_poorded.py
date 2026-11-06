"""
39 - Pöörded: kust sõidukid ristmikule tulevad ja kuhu lähevad (Sankey ehk voodiagramm) neljal suurel või
küllastunud ristmikul hommiku- ja õhtutipus.

SISEND
  common.load_vehicles(None, koik=True)   sõidukipõhised kirjed (tallinn.vehicle_passage): ristmik, kanal, aeg
  common.load_manoeuvres()                kanal -> manööver: lähtesuund (from_leg) ja sihtsuund (to_leg)
  common.load_junctions()                 ristmike nimed

ARVUTUS
  Päevad: logija nädala tööpäevad (NADAL). Tipud: hommik 07:00-09:00, õhtu 16:00-18:00 (TIPUD).
  Ristmikud (RISTMIKUD): MP01, MP08, MP19, MP13 - kõigil on iga kanali lähte- ja sihtsuund teada (100% sõidukitest),
    MP08, MP19 ja MP13 on 27 järgi küllastunud, MP01 on logija andmetes suurim.
  Voog = kanali sõidukid tipuaknas / (ristmiku kaetud tipupäevi x 2 h), sõidukit tunnis (ainult päevad, kus kõik
    ristmiku pordid on tipuaknas kaetud, common.tervetel_paevadel); kanalid, mille lähte- ja sihtsuund on samad,
    liidetakse (üks manööver võib olla mitmel rajal). Haru nimi: number eest ära, " side" -> " pool".
  Iga haru sisse- ja väljasõit = selle haru voogude summa (lähte- või sihtsuunana); kõik voog kokku on mõlemal pool sama.

CALCULATION IN PLAIN ENGLISH
  Logger-week workdays, peaks 07-09 and 16-18, four junctions where every lane's origin and destination arm is known.
  Flow of a movement = its vehicles in the peak window / (the junction's fully covered peak days x 2 h), vehicles per
    hour; lanes with the same origin and destination are added.
  Arm inflow and outflow = sum of the flows starting or ending at that arm; total in = total out.
  Share = movement flow / junction total flow x 100.

VÄLJUND (kaust valjund/)
  39_01_poorded.png
      Näitab: ristmiku liiklus pööramiste kaupa: mis suunast tullakse, mis suunda minnakse ja kui suur osa pöörab;
      hommiku ja õhtu võrdlus.
      Kuidas: rida = ristmik, veerg = hommik / õhtu. Paneelis vasakul tulpadena harud, kust tullakse, paremal harud,
      kuhu minnakse (tulba kõrgus = sõidukit tunnis); vöö = manööver, laius = voog, värv = lähteharu. Tulba kõrval haru
      nimi ja voog; pealkirjas ristmik, tipp ja voog kokku.
  39_poorded.csv   ristmik, tipp, lähteharu, sihtharu: sõidukit tunnis, osakaal ristmikust
"""
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle

from common import (tervetel_paevadel, load_vehicles, load_manoeuvres, load_junctions, set_style, save, save_table, short_name, C_BLUE,
                    C_ORANGE, C_AQUA, C_VIOLET, C_MAGENTA, C_GRAY, TEXT, TEXT2)

NADAL = pd.to_datetime(["2026-10-16", "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"])
TIPUD = {"hommik 07-09": (7, 9), "õhtu 16-18": (16, 18)}
RISTMIKUD = [1, 8, 19, 13]
VARVID = [C_BLUE, C_ORANGE, C_AQUA, C_VIOLET, C_MAGENTA]       # harud nime järjekorras
VAHE = 0.025                                                   # tulpade vahe, osa kogu kõrgusest
tuh = lambda x: f"{x:,.0f}".replace(",", " ")                  # tuhandete eraldaja tühik


def haru(nimi):
    """'1 Tammsaare, Mustamäe side (W)' -> 'Tammsaare, Mustamäe pool (W)'."""
    return re.sub(r"^\d+\s+", "", str(nimi)).replace(" side", " pool").strip()


def virn(vood, jarjekord):
    """Harude vood -> iga haru tulba (alumine, ülemine) serv, kõrgus kokku 1 + vahed."""
    kokku, y, out = vood.sum(), 0.0, {}
    for h in jarjekord:
        k = vood.get(h, 0) / kokku
        out[h] = (y, y + k)
        y += k + VAHE
    return out


def voo(ax, x0, x1, a0, b0, a1, b1, color):
    """Vöö vasakult lõigult [a0, b0] (x0) paremale lõigule [a1, b1] (x1), kumerad servad."""
    xm = (x0 + x1) / 2
    v = [(x0, a0), (xm, a0), (xm, a1), (x1, a1), (x1, b1), (xm, b1), (xm, b0), (x0, b0), (x0, a0)]
    c = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
         Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(v, c), facecolor=color, edgecolor="none", alpha=0.55))


assert haru("1 Tammsaare, Mustamäe side (W)") == "Tammsaare, Mustamäe pool (W)"
_s = virn(pd.Series({"a": 30, "b": 10}), ["a", "b"])
assert _s["a"] == (0, 0.75) and abs(_s["b"][1] - (0.75 + VAHE + 0.25)) < 1e-12

set_style()
jn = load_junctions().set_index("mp_id")
dm = load_manoeuvres()
dm["mp_id"] = dm["mp"].str[2:].astype(int)
dm = dm[dm["mp_id"].isin(RISTMIKUD)].dropna(subset=["from_leg", "to_leg"])
dm["lahe"], dm["siht"] = dm["from_leg"].map(haru), dm["to_leg"].map(haru)
v = load_vehicles(None, koik=True)
v = v[v["mp_id"].isin(RISTMIKUD) & v["ts"].dt.normalize().isin(NADAL)]
paevi = v["ts"].dt.normalize().nunique()
rows = []
for tipp, (h0, h1) in TIPUD.items():
    vt = tervetel_paevadel(v[v["ts"].dt.hour.between(h0, h1 - 1)], (h0, h1))   # ainult kaetud tipud
    pj = vt.groupby("mp_id")["ts"].agg(lambda s: s.dt.normalize().nunique())   # ristmiku kaetud tipupäevad
    z = vt.groupby(["mp_id", "kanal"]).size().rename("n").reset_index()
    z = z.merge(dm[["mp_id", "channel", "lahe", "siht"]], left_on=["mp_id", "kanal"], right_on=["mp_id", "channel"])
    g = z.groupby(["mp_id", "lahe", "siht"])["n"].sum().reset_index()
    g["paevi"] = g["mp_id"].map(pj)
    g["soid_h"] = g["n"] / (g["paevi"] * (h1 - h0))
    rows.append(g.assign(tipp=tipp))
p = pd.concat(rows, ignore_index=True)
p["osakaal_pct"] = 100 * p["soid_h"] / p.groupby(["mp_id", "tipp"])["soid_h"].transform("sum")
for (_, _), g in p.groupby(["mp_id", "tipp"]):            # voog on mõlemal pool sama
    assert abs(g.groupby("lahe")["soid_h"].sum().sum() - g.groupby("siht")["soid_h"].sum().sum()) < 1e-6
save_table(p.assign(kood=p["mp_id"].map(jn["code"])).drop(columns="n").round(2), "39_poorded")

# --- joonis ---------------------------------------------------------------------------------------------------------------
fig, axes = plt.subplots(len(RISTMIKUD), len(TIPUD), figsize=(15, 4.6 * len(RISTMIKUD)))
for i, mp in enumerate(RISTMIKUD):
    harud = sorted(set(dm.loc[dm["mp_id"] == mp, "lahe"]) | set(dm.loc[dm["mp_id"] == mp, "siht"]))
    varv = dict(zip(harud, VARVID))
    for j, tipp in enumerate(TIPUD):
        ax = axes[i, j]
        g = p[(p["mp_id"] == mp) & (p["tipp"] == tipp)]
        kokku = g["soid_h"].sum()
        sisse, valja = g.groupby("lahe")["soid_h"].sum(), g.groupby("siht")["soid_h"].sum()
        L, R = virn(sisse, harud), virn(valja, harud)
        lv = {h: L[h][0] for h in harud}                      # järgmise vöö algus igas tulbas
        rv = {h: R[h][0] for h in harud}
        for _, r in g.sort_values(["lahe", "siht"]).iterrows():
            k = r["soid_h"] / kokku
            voo(ax, 0.06, 0.94, lv[r["lahe"]], lv[r["lahe"]] + k, rv[r["siht"]], rv[r["siht"]] + k, varv[r["lahe"]])
            lv[r["lahe"]] += k
            rv[r["siht"]] += k
        for h in harud:
            for x, (a, b), s, ha, xt in [(0, L[h], sisse, "right", -0.01), (0.94, R[h], valja, "left", 1.01)]:
                if b - a <= 0:
                    continue
                ax.add_patch(Rectangle((x, a), 0.06, b - a, facecolor=varv[h] if x == 0 else C_GRAY, edgecolor="none"))
                ax.text(xt, (a + b) / 2, f"{short_name(h, 26)}\n{tuh(s.get(h, 0))} sõid/h", ha=ha,
                        va="center", fontsize=7.5, color=TEXT)
        ax.set_xlim(-0.42, 1.42)
        ax.set_ylim(1 + VAHE * len(harud), -0.02)
        ax.axis("off")
        ax.set_title(f"{jn.loc[mp, 'code']} {short_name(jn.loc[mp, 'name'], 32, compact=True)}, {tipp}: "
                     f"{tuh(kokku)} sõid/h", fontsize=10.5)
fig.suptitle(f"Pöörded tipptundidel: vasakul haru, kust tullakse, paremal haru, kuhu minnakse (sõidukipõhised loendused, "
             f"{paevi} tööpäeva {NADAL[0]:%d.%m}-{NADAL[-1]:%d.%m.%Y})",
             x=0.01, ha="left", fontweight="bold", fontsize=12)
fig.tight_layout(rect=(0, 0, 1, 0.985))
save(fig, "39_01_poorded")

for (mp, tipp), g in p.groupby(["mp_id", "tipp"]):
    t3 = g.nlargest(3, "soid_h")
    print(f"{jn.loc[mp, 'code']} {tipp}: {g['soid_h'].sum():.0f} sõid/h; suurimad: "
          + "; ".join(f"{r.lahe} -> {r.siht} {r.soid_h:.0f} ({r.osakaal_pct:.0f}%)" for r in t3.itertuples()))
