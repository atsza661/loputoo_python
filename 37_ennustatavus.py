"""
37 - Tipu ennustatavus: kui palju linna ja üksiku ristmiku liiklus tavalisel tööpäeval päevast päeva kõigub (lehvikdiagramm)
ning kui kindel on tipptunni maht ristmike kaupa.

SISEND
  common.load_tallinn()      ristmike 15 min loendused puhastatult (tallinn.count_15min)
  common.load_junctions()    ristmike nimed

ARVUTUS
  Päevad: tavalised tööpäevad (E-R, õppetöö, mitte püha ega lühendatud päev) alates ALGUS.
  Linn: kindel ristmike valim - ristmikud, millel on kehtiv päev vähemalt PANEEL_OSA nendest päevadest; linna päev on
    sees ainult siis, kui kõik valimi ristmikud on kehtivad (summa on päevade vahel võrreldav). Linna voog = valimi
    ristmike 15 min summa x 4 (sõidukit tunnis).
  Lehvik: iga 15 min pilu 10., 25., 50., 75. ja 90. protsentiil üle päevade. Võrdluseks väikseima ja suurima
    ööpäevaga päev.
  Ristmiku tipu kõikumine: hommikune ja õhtune tipptund igal päeval (suurim liikuv 60 min summa, algus 06:00-09:45 ja
    14:00-18:45); kõikumine = (90. protsentiil - 10. protsentiil) / mediaan, %; sama linna summa kohta.
    Päevast päeva kõikumine: sama, aga iga päeva tipp jagatakse ristmiku enda liikuva mediaaniga (TASE_PAEVI
    tööpäeva, keskel) - ehitus, loenduri vahetus või hooajaline tasemenihe ei suurenda seda. Joonisel see, tabelis
    mõlemad (kogu kõikumine suur, päevast päeva väike = tasemenihe perioodi sees). Hajutamise
    seisukohalt: kui kõikumine on suur, ei ole tipp igal päeval sama ja "keskmise päeva" järgi tehtud nihked ei
    vasta igale päevale.

VÄLJUND (kaust valjund/)
  37_01_lehvik.png
      Näitab: milline on linna tavaline tööpäev ja kui palju see päevast päeva kõigub.
      Kuidas: x = kellaaeg 05-23, y = tuhat sõidukit tunnis (valimi ristmikud kokku). Tume joon = mediaan, tumedam vöönd =
      25.-75. protsentiil, hele vöönd = 10.-90. protsentiil; peenikesed jooned = väikseima (hall) ja suurima (oranž)
      ööpäevaga päev. Pealkirjas päevade ja ristmike arv; tipptundide kõikumine tekstina.
  37_02_tipu_koikumine.png
      Näitab: kui kindel on iga ristmiku tipptunni maht päevast päeva.
      Kuidas: rida = ristmik (järjestatud suurema kõikumise järgi); x = päevast päeva kõikumine (p90 - p10) / mediaan
      tipu suhtest ristmiku liikuvasse mediaani, %; hall rõngas = kogu kõikumine (koos hooaja- ja tasemenihetega), kui see on
      päevast päeva kõikumisest üle 1,5 korra suurem (suurem neist kahest tipust). Sinine =
      hommikune, oranž = õhtune tipptund; katkendjooned = linna summa kõikumine (sinine hommik, oranž õhtu).
  37_lehvik.csv            pilu: protsentiilid, sõid/h
  37_tipu_koikumine.csv    ristmik: päevi, hommiku- ja õhtutipu mediaan, p10, p90, kogu ja päevast päeva kõikumine %
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common import (load_tallinn, load_junctions, set_style, save, save_table, short_name, slot_label, C_BLUE, C_ORANGE,
                    C_GRAY, TEXT, TEXT2)

ALGUS = "2025-09-01"
PANEEL_OSA = 0.9
Q = [0.1, 0.25, 0.5, 0.75, 0.9]
HOMMIK, OHTU = (24, 39), (56, 75)
KELL = (20, 92)                              # 05:00-23:00
NADALAPAEV = ["E", "T", "K", "N", "R", "L", "P"]
TASE_PAEVI = 21


def tunnitipp(w, aken):
    """Lai tabel (rida = päev, veerud = pilud 0..95) -> iga päeva suurim liikuv 60 min summa, algus aknas."""
    h = w.T.rolling(4).sum().shift(-3).T
    return h.loc[:, aken[0]:aken[1]].max(axis=1)


def koikumine(x):
    """(p90 - p10) / mediaan, %."""
    return 100 * (x.quantile(0.9) - x.quantile(0.1)) / x.median()


def paevast_paeva(x):
    """Päevade jada -> suhe liikuvasse mediaani (TASE_PAEVI päeva, keskel): tasemenihked välja."""
    return x / x.rolling(TASE_PAEVI, center=True, min_periods=7).median()


assert koikumine(pd.Series(np.arange(1, 102))) == 100 * 80 / 51
assert koikumine(paevast_paeva(pd.Series(np.r_[np.full(60, 100.0), np.full(60, 150.0)]))) < 1     # astmeline nihe kaob
assert tunnitipp(pd.DataFrame([np.r_[np.zeros(30), np.full(4, 5.0), np.zeros(62)]]), HOMMIK).iloc[0] == 20

set_style()
jn = load_junctions().set_index("mp_id")
t, d = load_tallinn()
d = d[d["kehtiv"] & (d["paevatyyp"] == "tööpäev") & (d["vaheaeg"] == "kool") & (d["paev"] >= ALGUS)]
t = t.merge(d[["mp_id", "paev"]], on=["mp_id", "paev"])
w = t.pivot_table(index=["mp_id", "paev"], columns="slot", values="v", aggfunc="sum")
w = w[w.notna().sum(axis=1) >= 88].T.interpolate(limit_direction="both").T
paevi = d["paev"].nunique()

# --- linn: kindel valim ----------------------------------------------------------------------------------------------------
n = w.groupby("mp_id").size()
paneel = n[n >= PANEEL_OSA * paevi].index
wp = w.loc[paneel]
taielik = wp.groupby("paev").size()
taielik = taielik[taielik == len(paneel)].index
linn = wp[wp.index.get_level_values("paev").isin(taielik)].groupby("paev").sum() * 4
lv = linn.quantile(Q).T
lv.columns = [f"p{int(q * 100)}" for q in Q]
save_table(lv.assign(kell=[slot_label(s) for s in lv.index]).reset_index().round(1), "37_lehvik")
ooopaev = linn.sum(axis=1) / 4
pmin, pmax = ooopaev.idxmin(), ooopaev.idxmax()

# --- ristmike tipud --------------------------------------------------------------------------------------------------------
tp = pd.DataFrame({"hommik": tunnitipp(w, HOMMIK), "ohtu": tunnitipp(w, OHTU)})
rows = []
for mp, g in tp.groupby("mp_id"):
    if len(g) < 30:
        continue
    rows.append(dict(mp_id=mp, kood=jn.loc[mp, "code"], nimi=jn.loc[mp, "name"], paevi=len(g),
                     **{f"{k}_{s}": f(g[k]) for k in ["hommik", "ohtu"]
                        for s, f in [("mediaan", np.median), ("p10", lambda x: x.quantile(0.1)),
                                     ("p90", lambda x: x.quantile(0.9)), ("koikumine_pct", koikumine),
                                     ("paevast_paeva_pct", lambda x: koikumine(paevast_paeva(x)))]}))
r = pd.DataFrame(rows)
r["max_koikumine"] = r[["hommik_paevast_paeva_pct", "ohtu_paevast_paeva_pct"]].max(axis=1)
r["max_kogu"] = r[["hommik_koikumine_pct", "ohtu_koikumine_pct"]].max(axis=1)
r = r.sort_values("max_koikumine")
save_table(r.round(2), "37_tipu_koikumine")
lt = pd.DataFrame({"hommik": tunnitipp(linn / 4, HOMMIK), "ohtu": tunnitipp(linn / 4, OHTU)})
lk = {k: koikumine(paevast_paeva(lt[k])) for k in ["hommik", "ohtu"]}

# --- joonis 1: lehvik ------------------------------------------------------------------------------------------------------
x = np.arange(96) / 4 + 0.125
s = slice(KELL[0], KELL[1])
fig, a = plt.subplots(figsize=(13, 6))
a.fill_between(x[s], lv["p10"].values[s] / 1000, lv["p90"].values[s] / 1000, color=C_BLUE, alpha=0.18, lw=0,
               label="10.-90. protsentiil")
a.fill_between(x[s], lv["p25"].values[s] / 1000, lv["p75"].values[s] / 1000, color=C_BLUE, alpha=0.35, lw=0,
               label="25.-75. protsentiil")
a.plot(x[s], lv["p50"].values[s] / 1000, color=C_BLUE, lw=2.4, label="mediaan")
a.plot(x[s], linn.loc[pmin].values[s] / 1000, color=C_GRAY, lw=1, label=f"väikseim ööpäev ({NADALAPAEV[pmin.day_of_week]} {pmin:%d.%m.%Y})")
a.plot(x[s], linn.loc[pmax].values[s] / 1000, color=C_ORANGE, lw=1, label=f"suurim ööpäev ({NADALAPAEV[pmax.day_of_week]} {pmax:%d.%m.%Y})")
a.set_xlim(KELL[0] / 4, KELL[1] / 4)
a.set_xticks(range(5, 24), [f"{h:02d}" for h in range(5, 24)])
a.set_ylim(0, None)
a.set_xlabel("kellaaeg")
a.set_ylabel("tuhat sõidukit tunnis (valimi ristmikud kokku)")
a.set_title(f"Linna tavaline tööpäev ja selle kõikumine: {len(linn)} päeva, {len(paneel)} ristmikku "
            f"(alates {pd.Timestamp(ALGUS):%d.%m.%Y})")
a.text(0.99, 0.04, f"Tipptunni kõikumine päevast päeva (p90 - p10) / mediaan: hommik {lk['hommik']:.1f}%, õhtu "
       f"{lk['ohtu']:.1f}%\nÜksikul ristmikul mediaan: hommik {r['hommik_paevast_paeva_pct'].median():.1f}%, õhtu "
       f"{r['ohtu_paevast_paeva_pct'].median():.1f}%".replace(".", ","), transform=a.transAxes, ha="right", va="bottom",
       fontsize=9, color=TEXT2)
a.legend(loc="upper left", fontsize=9)
fig.tight_layout()
save(fig, "37_01_lehvik")

# --- joonis 2: ristmike tipu kõikumine ------------------------------------------------------------------------------------
y = np.arange(len(r))
fig, a = plt.subplots(figsize=(9, 0.24 * len(r) + 1.6))
a.hlines(y, r["hommik_paevast_paeva_pct"], r["ohtu_paevast_paeva_pct"], color=C_GRAY, lw=1)
a.scatter(r["hommik_paevast_paeva_pct"], y, color=C_BLUE, s=24, zorder=3)
a.scatter(r["ohtu_paevast_paeva_pct"], y, color=C_ORANGE, s=24, zorder=3)
nihe = (r["max_kogu"] > 1.5 * r["max_koikumine"]).values
a.scatter(r.loc[nihe, "max_kogu"], y[nihe], facecolor="none", edgecolor=C_GRAY, s=30, lw=1.2, zorder=2)
a.axvline(lk["hommik"], color=C_BLUE, ls="--", lw=1)
a.axvline(lk["ohtu"], color=C_ORANGE, ls="--", lw=1)
a.set_yticks(y, [f"{k} {short_name(m, 28, compact=True)}" for k, m in zip(r["kood"], r["nimi"])], fontsize=8)
a.set_ylim(-0.7, len(r) - 0.3)
a.set_xlim(0, None)
a.set_xlabel(f"kõikumine päevast päeva ({TASE_PAEVI} päeva taseme suhtes): (p90 - p10) / mediaan, %")
a.set_title("Kui kindel on tipptunni maht?")
a.legend(handles=[Line2D([], [], marker="o", ls="", color=C_BLUE, label="hommikune tipptund"),
                  Line2D([], [], marker="o", ls="", color=C_ORANGE, label="õhtune tipptund"),
                  Line2D([], [], ls="--", color=TEXT2, label="linna summa (värv = tipp)"),
                  Line2D([], [], marker="o", ls="", mfc="none", mec=C_GRAY, label="kogu kõikumine (koos hooaja- ja tasemenihetega)")],
         loc="lower right", fontsize=8.5)
fig.tight_layout()
save(fig, "37_02_tipu_koikumine")

print(f"päevi {paevi}, linna valimis {len(paneel)} ristmikku, täielikke päevi {len(linn)}; linna kõikumine "
      f"hommik {lk['hommik']:.1f}%, õhtu {lk['ohtu']:.1f}%; ristmike mediaan hommik "
      f"{r['hommik_paevast_paeva_pct'].median():.1f}%, õhtu {r['ohtu_paevast_paeva_pct'].median():.1f}%; suurim "
      f"{r['kood'].iloc[-1]} {r['max_koikumine'].iloc[-1]:.0f}%; kogu kõikumine üle 1,5x: {', '.join(r.loc[nihe, 'kood'])}")
