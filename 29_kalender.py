"""
29 - Kalender: Tallinna ristmike liiklus iga päeva kohta 2024-07 ... 2026-10 ühel pildil (nädalarütm, suvi, pühad,
koolivaheajad ja andmeaugud korraga näha).

SISEND
  common.load_tallinn()      ristmike 15 min loendused puhastatult ja päevasummad (tallinn.count_15min)
  common.day_calendar()      päevatüüp (tööpäev, laupäev, pühapäev, riigipüha, lühendatud) ja koolivaheaeg

ARVUTUS
  Ristmiku päevasumma = puhastatud 15 min väärtuste summa (puuduvad pilud tavaväärtusega, load_tallinn), ainult
    kehtivad päevad. Ristmiku tase = tema päevasummade mediaan tavalistel tööpäevadel (E-R, õppetöö, mitte püha).
  Päeva indeks = 100 x mediaan üle ristmike (päevasumma / ristmiku tase); vähemalt MIN_RISTMIKKE ristmikku, muidu
    päev puudub. Mediaan, mitte summa: ristmike arv muutub ajas (uued loendurid, rikked) ja ühe ristmiku püsiv tasemenihe
    (loenduri vahetus) ei muuda linna indeksit.
  Kalender: veerg = nädal (esmaspäevast), rida = nädalapäev; iga aasta oma real.

CALCULATION IN PLAIN ENGLISH
  Junction daily total = sum of its cleaned 15-minute values (missing slots filled with the usual value), valid days
    only. Junction level = median of its daily totals on typical workdays.
  Day index = 100 x median over junctions of (daily total / junction level); needs at least MIN_RISTMIKKE junctions.
    A median, not a sum, so a changing set of junctions or one junction's level shift does not move the city index.

VÄLJUND (kaust valjund/)
  29_01_kalender.png
      Näitab: iga päeva liiklust võrreldes tavalise tööpäevaga kahe aasta jooksul - nädalarütm, suve- ja jõulumadal,
      pühad ja koolivaheajad.
      Kuidas: kolm kalendririba (2024, 2025, 2026); ruut = päev, veerg = nädal, rida = nädalapäev (E üleval). Värv =
      päeva indeks, % tavalisest tööpäevast (heledam = vähem, tumedam sinine = rohkem liiklust). Musta äärisega ruut =
      riigipüha, hall viirutatud = andmed puuduvad. Riba all = koolivaheaeg (värv tüübi järgi); üleval kuude nimed.
  29_paevaindeks.csv   päev: indeks, ristmikke, nädalapäev, päevatüüp, püha, koolivaheaeg (kasutab ka 36)
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch

from common import (load_tallinn, day_calendar, set_style, save, save_table, VAHEAEG_LABEL, TEXT2, GRID, C_ORANGE,
                    C_AQUA, C_VIOLET)

MIN_RISTMIKKE = 15
VMIN, VMAX = 40, 110                 # värviskaala, % tavalisest tööpäevast
KUUD = ["jaan", "veebr", "märts", "apr", "mai", "juuni", "juuli", "aug", "sept", "okt", "nov", "dets"]
VAHEAEG_VARV = {"suvi": C_ORANGE, "jõulud": C_VIOLET, "lühike": C_AQUA}
NADALAPAEVAD = ["E", "T", "K", "N", "R", "L", "P"]


def koht(paev):
    """Päev -> (veerg, rida) oma aasta kalendris: veerg 0 = nädal, mille esmaspäev on 1. jaanuaril või enne seda."""
    p = pd.Timestamp(paev)
    algus = pd.Timestamp(p.year, 1, 1)
    algus -= pd.Timedelta(days=algus.day_of_week)
    return (p - algus).days // 7, p.day_of_week


assert koht("2026-01-01") == (0, 3) and koht("2026-01-05") == (1, 0) and koht("2024-12-31") == (52, 1)

set_style()
_, d = load_tallinn()
d = d[d["kehtiv"]].copy()
tava = (d["paevatyyp"] == "tööpäev") & (d["vaheaeg"] == "kool")
tase = d[tava].groupby("mp_id")["summa"].median()
d["suhe"] = d["summa"] / d["mp_id"].map(tase)
ix = d.groupby("paev").agg(indeks=("suhe", "median"), ristmikke=("suhe", "size"))
ix["indeks"] *= 100
ix = ix[ix["ristmikke"] >= MIN_RISTMIKKE]
kal = day_calendar(pd.date_range(d["paev"].min(), d["paev"].max())).set_index("paev")
ix = kal.join(ix)
save_table(ix.reset_index(), "29_paevaindeks")

aastad = sorted(ix.index.year.unique())
cmap = plt.get_cmap("Blues").copy()
fig, axes = plt.subplots(len(aastad), 1, figsize=(15, 2.35 * len(aastad) + 0.8))
for ax, a in zip(np.atleast_1d(axes), aastad):
    x = ix[ix.index.year == a]
    for p, r in x.iterrows():
        c, w = koht(p)
        if np.isnan(r["indeks"]):
            ax.add_patch(Rectangle((c, w), 1, 1, facecolor="#f4f3f0", edgecolor="white", lw=1.2, hatch="////"))
        else:
            v = (np.clip(r["indeks"], VMIN, VMAX) - VMIN) / (VMAX - VMIN)
            ax.add_patch(Rectangle((c, w), 1, 1, facecolor=cmap(0.08 + 0.92 * v), edgecolor="white", lw=1.2))
        if isinstance(r["puha"], str):
            ax.add_patch(Rectangle((c + 0.08, w + 0.08), 0.84, 0.84, fill=False, edgecolor="black", lw=1.1))
    # koolivaheajad riba all: iga nädal, kus mõni päev on vaheajal
    for p, r in x[x["vaheaeg"] != "kool"].iterrows():
        c, w = koht(p)
        ax.add_patch(Rectangle((c + w / 7, 7.25), 1 / 7, 0.45, facecolor=VAHEAEG_VARV[r["vaheaeg"]], lw=0))
    for m in range(1, 13):
        p = pd.Timestamp(a, m, 1)
        p = max(p, x.index.min())                     # andmete algus kuu keskel: silt esimese päeva kohal
        if (p + pd.offsets.MonthEnd(0) - p).days >= 6 and p <= x.index.max():
            ax.text(koht(p)[0] + 0.1, -0.25, KUUD[m - 1], fontsize=8.5, color=TEXT2, va="bottom")
    ax.set_xlim(-0.2, 54)
    ax.set_ylim(7.9, -1.1)
    ax.set_yticks(np.arange(7) + 0.5, NADALAPAEVAD, fontsize=8)
    ax.set_xticks([])
    ax.tick_params(length=0)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_ylabel(str(a), rotation=0, ha="right", va="center", fontsize=13, fontweight="bold", color="black", labelpad=16)
axes[0].set_title("Tallinna ristmike liiklus päevade kaupa, % tavalisest tööpäevast (ristmike mediaan)", loc="left",
                  pad=14)
sm = plt.cm.ScalarMappable(cmap=plt.matplotlib.colors.LinearSegmentedColormap.from_list("b", cmap(np.linspace(0.08, 1, 256))),
                           norm=plt.Normalize(VMIN, VMAX))
cax = fig.add_axes([0.70, 0.035, 0.2, 0.018])
cb = fig.colorbar(sm, cax=cax, orientation="horizontal", extend="both")
cb.set_label("% tavalisest tööpäevast", fontsize=8.5, color=TEXT2)
cb.ax.tick_params(labelsize=8)
fig.legend(handles=[Patch(facecolor=VAHEAEG_VARV[k], label=VAHEAEG_LABEL[k]) for k in ["suvi", "jõulud", "lühike"]]
           + [Patch(facecolor="white", edgecolor="black", label="Riigipüha")]
           + ([Patch(facecolor="#f4f3f0", edgecolor=GRID, hatch="////", label="Andmed puuduvad")]
              if ix["indeks"].isna().any() else []),
           loc="lower left", bbox_to_anchor=(0.06, 0.0), ncol=5, fontsize=8.5)
fig.subplots_adjust(hspace=0.25, bottom=0.11)
save(fig, "29_01_kalender")

tp = ix[(ix["paevatyyp"] == "tööpäev") & (ix["vaheaeg"] == "kool")]["indeks"]
print(f"päevi indeksiga {ix['indeks'].notna().sum()} / {len(ix)}; tavaline tööpäev mediaan {tp.median():.1f}; "
      + ", ".join(f"{k} {ix.loc[ix['paevatyyp'] == k, 'indeks'].median():.0f}"
                  for k in ["laupäev", "pühapäev", "riigipüha"])
      + "; " + ", ".join(f"{k} (tööpäev) {ix.loc[(ix['vaheaeg'] == k) & (ix['paevatyyp'] == 'tööpäev'), 'indeks'].median():.0f}"
                         for k in ["lühike", "jõulud", "suvi"]))
