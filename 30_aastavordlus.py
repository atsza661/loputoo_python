"""
30 - Aastavõrdlus: sama sügise õppetöö nädalad 2025 ja 2026 iga ristmiku kohta - kas liiklus kasvab või kahaneb?

SISEND
  common.load_tallinn()      ristmike 15 min loendused puhastatult ja päevasummad (import_raw.traffic_15min_tallinn)

ARVUTUS
  Võrreldavad perioodid (PERIOODID): septembri 2. nädalast 4 õppetöö nädalat, E-R, mitte püha - 08.09.-03.10.2025 ja
    07.09.-02.10.2026 (sama nädalapäevade arv, mõlemad õppetöö ajal).
  Ristmiku näitajad perioodis (tööpäevade mediaan, ainult kehtivad päevad, vähemalt MIN_PAEVI päeva):
    ööpäev   - päevasumma
    hommik   - hommikune tipptund: suurim liikuv 60 min summa, algus 06:00...09:45
    õhtu     - õhtune tipptund: algus 14:00...18:45
  Muutus = 2026 / 2025 - 1, %. Linn kokku = ristmike summa (ainult ristmikud, mis on mõlemas perioodis).
  Tasemenihe perioodi sees: kui 2026. a perioodi kahe viimase ja kahe esimese nädala päevasummade erinevus on üle
    NIHE (loenduri vahetus, rike või ehitus), on ristmik märgitud - tema muutus ei pruugi olla liikluse muutus.

VÄLJUND (kaust valjund/)
  30_01_aastavordlus.png
      Näitab: iga ristmiku ööpäeva liikluse ja tipptundide muutust 2025. ja 2026. a sama sügise vahel.
      Kuidas: rida = ristmik (järjestatud ööpäeva muutuse järgi). Vasakul hall ring = 2025, sinine punkt = 2026
      (sõidukeid ööpäevas), joon nende vahel. Paremal muutus %: tume punkt = ööpäev, sinine = hommikune tipptund,
      oranž = õhtune tipptund; püstjoon = 0, katkendjoon = linna muutus kokku. Tärn nime juures = tasemenihe 2026. a
      perioodi sees.
  30_aastavordlus.csv   ristmik: päevi, ööpäev, hommiku- ja õhtutipp mõlemal aastal, muutused %, tasemenihe
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common import load_tallinn, load_junctions, set_style, save, save_table, short_name, C_BLUE, C_ORANGE, C_GRAY, TEXT, TEXT2

PERIOODID = {2025: ("2025-09-08", "2025-10-03"), 2026: ("2026-09-07", "2026-10-02")}
HOMMIK, OHTU = (24, 39), (56, 75)    # tipptunni algus 06:00...09:45 ja 14:00...18:45 (15 min pilud)
MIN_PAEVI = 12
NIHE = 0.08


def tunnitipp(w, aken):
    """Lai tabel (rida = päev, veerud = pilud 0..95) -> iga päeva suurim liikuv 60 min summa, algus aknas."""
    h = w.T.rolling(4).sum().shift(-3).T
    return h.loc[:, aken[0]:aken[1]].max(axis=1)


_w = pd.DataFrame([np.r_[np.zeros(30), np.full(4, 10.0), np.zeros(62)]])
assert tunnitipp(_w, HOMMIK).iloc[0] == 40 and tunnitipp(_w, OHTU).iloc[0] == 0

set_style()
jn = load_junctions().set_index("mp_id")
t, d = load_tallinn()
d = d[d["kehtiv"] & (d["paevatyyp"] == "tööpäev") & (d["vaheaeg"] == "kool")]
rows = []
for aasta, (a, b) in PERIOODID.items():
    dd = d[d["paev"].between(a, b)]
    tt = t[t["paev"].between(a, b)].merge(dd[["mp_id", "paev"]], on=["mp_id", "paev"])
    w = tt.pivot_table(index=["mp_id", "paev"], columns="slot", values="v", aggfunc="sum")
    w = w.T.interpolate(limit_direction="both").T
    x = pd.DataFrame({"hommik": tunnitipp(w, HOMMIK), "ohtu": tunnitipp(w, OHTU)}).join(dd.set_index(["mp_id", "paev"])["summa"])
    g = x.groupby("mp_id").agg(paevi=("summa", "size"), ooopaev=("summa", "median"), hommik=("hommik", "median"),
                               ohtu=("ohtu", "median"))
    rows.append(g[g["paevi"] >= MIN_PAEVI].add_suffix(f"_{aasta}"))
    if aasta == 2026:                                   # tasemenihe perioodi sees
        p = pd.to_datetime(dd["paev"])
        alg = dd[p < pd.Timestamp(a) + pd.Timedelta(days=14)].groupby("mp_id")["summa"].median()
        lopp = dd[p >= pd.Timestamp(a) + pd.Timedelta(days=14)].groupby("mp_id")["summa"].median()
        nihe = (lopp / alg - 1).rename("nihe_perioodis")
r = pd.concat(rows, axis=1, join="inner").join(nihe)
for k in ["ooopaev", "hommik", "ohtu"]:
    r[f"{k}_muutus_%"] = (r[f"{k}_2026"] / r[f"{k}_2025"] - 1) * 100
r["tasemenihe"] = r["nihe_perioodis"].abs() > NIHE
r.insert(0, "kood", jn.loc[r.index, "code"])
r.insert(1, "nimi", jn.loc[r.index, "name"])
r = r.sort_values("ooopaev_muutus_%")
save_table(r.reset_index(), "30_aastavordlus")
linn = {k: (r[f"{k}_2026"].sum() / r[f"{k}_2025"].sum() - 1) * 100 for k in ["ooopaev", "hommik", "ohtu"]}
linn_puhas = (r.loc[~r["tasemenihe"], "ooopaev_2026"].sum() / r.loc[~r["tasemenihe"], "ooopaev_2025"].sum() - 1) * 100

fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 0.26 * len(r) + 1.8), sharey=True, gridspec_kw={"width_ratios": [1.25, 1]})
y = np.arange(len(r))
a1.hlines(y, r["ooopaev_2025"] / 1000, r["ooopaev_2026"] / 1000, color=C_GRAY, lw=1.3, zorder=1)
a1.scatter(r["ooopaev_2025"] / 1000, y, s=34, facecolor="white", edgecolor=C_GRAY, lw=1.4, zorder=2)
a1.scatter(r["ooopaev_2026"] / 1000, y, s=34, color=C_BLUE, zorder=3)
a1.set_yticks(y, [f"{'* ' if n else ''}{k} {short_name(m, 30, compact=True)}"
                  for k, m, n in zip(r["kood"], r["nimi"], r["tasemenihe"])], fontsize=8)
a1.set_xlabel("tuhat sõidukit tööpäevas (mediaan)")
a1.set_title("Ööpäeva liiklus: 2025 vs 2026")
a1.legend(handles=[Line2D([], [], marker="o", ls="", mfc="white", mec=C_GRAY, label="2025 (08.09.-03.10.)"),
                   Line2D([], [], marker="o", ls="", color=C_BLUE, label="2026 (07.09.-02.10.)")],
          loc="lower right", fontsize=8.5)
a2.axvline(0, color=TEXT, lw=0.8)
a2.axvline(linn["ooopaev"], color=TEXT2, lw=1, ls="--")
for k, c, m, s in [("hommik", C_BLUE, "o", 22), ("ohtu", C_ORANGE, "o", 22), ("ooopaev", TEXT, "D", 26)]:
    a2.scatter(r[f"{k}_muutus_%"].clip(-40, 40), y, color=c, marker=m, s=s, zorder=3, alpha=0.9)
a2.set_xlim(-42, 42)
a2.set_xlabel("muutus 2025 -> 2026, %")
a2.set_title("Muutus, %")
a2.legend(handles=[Line2D([], [], marker="D", ls="", color=TEXT, label="ööpäev"),
                   Line2D([], [], marker="o", ls="", color=C_BLUE, label="hommikune tipptund"),
                   Line2D([], [], marker="o", ls="", color=C_ORANGE, label="õhtune tipptund"),
                   Line2D([], [], ls="--", color=TEXT2, label=f"linn kokku ({linn['ooopaev']:+.1f}%)")],
          loc="lower right", fontsize=8.5)
a1.set_ylim(-0.7, len(r) - 0.3)
fig.text(0.01, -0.01, f"* tasemenihe 2026. a perioodi sees üle {NIHE:.0%} (loenduri vahetus, rike või ehitus): muutus ei pruugi "
         f"olla liikluse muutus. Ilma nendeta linn kokku {linn_puhas:+.1f}%. Väärtused väljaspool +-40% on serval.",
         fontsize=8, color=TEXT2)
fig.tight_layout()
save(fig, "30_01_aastavordlus")
print(f"ristmikke {len(r)}; linn kokku: ööpäev {linn['ooopaev']:+.1f}%, hommik {linn['hommik']:+.1f}%, õhtu {linn['ohtu']:+.1f}%; "
      f"ilma tasemenihketa {linn_puhas:+.1f}%; tasemenihkega: {', '.join(r.loc[r['tasemenihe'], 'kood'])}")
