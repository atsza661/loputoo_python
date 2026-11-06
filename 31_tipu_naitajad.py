"""
31 - Tipptunni näitajad ristmike kaupa: tipptunni osakaal ööpäevast (K-tegur), tipptunni tegur (PHF) ning hommiku- ja
õhtutipu suurus ja kellaaeg - liikluskorralduse standardnäitajad, mis näitavad, kui terav ja kui suur on tipp.

SISEND
  common.load_tallinn()      ristmike 15 min loendused puhastatult (tallinn.count_15min)

ARVUTUS
  Tüüpiline tööpäev (nagu 06): E-R õppetöö ajal, mitte püha ega lühendatud päev, alates ALGUS (vähemalt MIN_PAEVI
    päeva). common.peak_metrics arvutatakse iga päeva kohta eraldi ja ristmiku väärtus on päevade mediaan (keskmise
    profiili PHF oleks liiga suur: päevade keskmistamine silub veerandtundide kõikumise). Tipptunni algus ja keskaeg
    on ristmiku keskmisest profiilist (iga pilu keskmine), et see oleks võrreldav 06-ga.
  common.peak_metrics:
    tipptund   - suurim liikuv 60 min summa, algus hommikul 06:00...09:59, õhtul 14:00...18:59 (sõidukit tunnis)
    K-tegur    - tipptunni maht / ööpäeva maht, %. Mida suurem, seda rohkem liiklust on ühte tundi koondunud
                 (linnatänavatel tavaliselt 7-12%).
    PHF        - tipptunni maht / (4 x tipptunni suurim veerandtund). 1 = tunni sees ühtlane, 0,25 = kogu tund ühes
                 veerandtunnis; väike PHF = terav lühike tipp (nt kooli algus).
  Tipu iseloom: hommik / õhtu = hommikuse ja õhtuse tipptunni suhe (> 1,1 hommikutipuga, < 0,9 õhtutipuga).

CALCULATION IN PLAIN ENGLISH
  Typical workdays from ALGUS (at least MIN_PAEVI). Peak metrics are computed for each day separately and the junction
    value is the median over days (a PHF from the averaged profile would be too high, averaging smooths the quarter
    hours). Peak start and traffic midpoint come from the average profile, comparable with 06.
  K-factor = peak-hour volume / daily volume x 100. PHF = peak-hour volume / (4 x its busiest quarter hour).
  Peak type: morning / evening peak-hour ratio (> 1.1 morning peak, < 0.9 evening peak).

VÄLJUND (kaust valjund/)
  31_01_tipu_naitajad.png
      Näitab: kui terav (K-tegur, PHF) ja kui suur on iga ristmiku hommikune ja õhtune tipp ning kumb on suurem.
      Kuidas: rida = ristmik (järjestatud suurema K-teguri järgi), kolm paneeli ühise y-teljega. 1) K-tegur, %;
      2) PHF; 3) tipptunni maht, tuhat sõidukit tunnis, joon hommiku ja õhtu vahel. Sinine = hommik, oranž = õhtu;
      paremal tipptundide algused. Hall vöönd 1. paneelil = linnatänavate tavaline K 7-12%.
  31_02_k_vs_phf.png
      Näitab: kas teravad tipud (suur K) on ka tunni sees teravad (väike PHF) - kus hajutamisel oleks kõige rohkem mõju.
      Kuidas: hajuvusdiagramm; x = K-tegur, %, y = PHF; punkt = ristmiku tipp (sinine = hommik, oranž = õhtu),
      suurus = tipptunni maht. Sildid ristmikel, mille K on suurim või PHF väikseim.
  31_tipu_naitajad.csv   ristmik: päevi, ööpäev, mõlema tipu algus, maht, K, PHF, laius, keskaeg; hommik/õhtu suhe
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common import (paeva_maatriks, load_tallinn, load_junctions, peak_metrics, set_style, save, save_table, short_name, place_labels,
                    C_BLUE, C_ORANGE, C_GRAY, TEXT2, GRID)

ALGUS = "2025-09-01"
MIN_PAEVI = 40

_v = np.ones(96) + np.r_[np.zeros(32), [10, 10, 40, 20], np.zeros(60)]      # tase 1 + tipp kell 08:00-09:00
_m = peak_metrics(_v)
assert _m["hommik_algus"] == "08:00" and abs(_m["hommik_phf"] - 84 / 164) < 1e-9 and abs(_m["hommik_osakaal_%"] - 8400 / 176) < 1e-9

set_style()
jn = load_junctions().set_index("mp_id")
t, d = load_tallinn()
ok = d[d["kehtiv"] & (d["paevatyyp"] == "tööpäev") & (d["vaheaeg"] == "kool") & (d["paev"] >= ALGUS)]
t = t.merge(ok[["mp_id", "paev"]], on=["mp_id", "paev"])
prof = t.pivot_table(index="mp_id", columns="slot", values="v", aggfunc="mean")
n = ok.groupby("mp_id").size()
prof = prof[(n.reindex(prof.index) >= MIN_PAEVI) & prof.notna().all(axis=1)]
r = pd.DataFrame([peak_metrics(prof.loc[mp].values) for mp in prof.index], index=prof.index)
w = paeva_maatriks(t[t["mp_id"].isin(prof.index)])            # puuduv pilu jääb NaN-iks (mitte 0)
w = w[w.notna().sum(axis=1) >= 88].T.interpolate(limit_direction="both").T
pv = pd.DataFrame([peak_metrics(x) for x in w.values], index=w.index)
arv = [c for c in pv.columns if c.endswith(("_soid_h", "_osakaal_%", "_phf", "_laius_min", "_potentsiaal_%")) or c == "ooopaev"]
r[arv] = pv[arv].astype(float).groupby("mp_id").median()           # arvulised näitajad: päevade mediaan
r.insert(0, "paevi", n.reindex(r.index))
r.insert(0, "nimi", jn.loc[r.index, "name"])
r.insert(0, "kood", jn.loc[r.index, "code"])
r["hommik_ohtu_suhe"] = r["hommik_soid_h"] / r["ohtu_soid_h"]
r["iseloom"] = np.select([r["hommik_ohtu_suhe"] > 1.1, r["hommik_ohtu_suhe"] < 0.9], ["hommikutipuga", "õhtutipuga"],
                         "tasakaalus")
r["K_max"] = r[["hommik_osakaal_%", "ohtu_osakaal_%"]].max(axis=1)
r = r.sort_values("K_max")
save_table(r.reset_index(), "31_tipu_naitajad")

# --- joonis 1: kolm paneeli ---------------------------------------------------------------------------------------------
y = np.arange(len(r))
fig, ax = plt.subplots(1, 3, figsize=(15, 0.25 * len(r) + 1.6), sharey=True, gridspec_kw={"width_ratios": [1, 1, 1.25]})
ax[0].axvspan(7, 12, color=GRID, alpha=0.6, lw=0)
for k, c in [("hommik", C_BLUE), ("ohtu", C_ORANGE)]:
    ax[0].scatter(r[f"{k}_osakaal_%"], y, color=c, s=24, zorder=3)
    ax[1].scatter(r[f"{k}_phf"], y, color=c, s=24, zorder=3)
ax[2].hlines(y, r["hommik_soid_h"] / 1000, r["ohtu_soid_h"] / 1000, color=C_GRAY, lw=1.2)
ax[2].scatter(r["hommik_soid_h"] / 1000, y, color=C_BLUE, s=24, zorder=3)
ax[2].scatter(r["ohtu_soid_h"] / 1000, y, color=C_ORANGE, s=24, zorder=3)
xm = (r[["hommik_soid_h", "ohtu_soid_h"]].max(axis=1) / 1000).max()
for i, (_, q) in enumerate(r.iterrows()):
    ax[2].text(xm * 1.04, i, f"{q['hommik_algus']} / {q['ohtu_algus']}", va="center", fontsize=7.5, color=TEXT2)
ax[2].text(xm * 1.04, len(r) - 0.2, "tipu algus\nhommik / õhtu", fontsize=7.5, color=TEXT2, va="bottom")
ax[2].set_xlim(0, xm * 1.3)
ax[0].set_yticks(y, [f"{k} {short_name(m, 28, compact=True)}" for k, m in zip(r["kood"], r["nimi"])], fontsize=8)
ax[0].set_ylim(-0.7, len(r) + 0.6)
ax[0].set_title("K-tegur: tipptund, % ööpäevast")
ax[0].set_xlabel("% ööpäeva liiklusest")
ax[1].set_title("Tipptunni tegur PHF")
ax[1].set_xlabel("PHF (1 = tunni sees ühtlane)")
ax[2].set_title("Tipptunni maht")
ax[2].set_xlabel("tuhat sõidukit tunnis")
fig.legend(handles=[Line2D([], [], marker="o", ls="", color=C_BLUE, label="hommikune tipptund (algus 06-10)"),
                    Line2D([], [], marker="o", ls="", color=C_ORANGE, label="õhtune tipptund (algus 14-19)"),
                    plt.Rectangle((0, 0), 1, 1, color=GRID, alpha=0.6, label="tavaline K linnatänaval 7-12%")],
           loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.02), fontsize=9)
fig.suptitle(f"Tipptunni näitajad, tüüpiline tööpäev (õppetöö, alates {pd.Timestamp(ALGUS):%d.%m.%Y})",
             x=0.01, ha="left", fontweight="bold", fontsize=12)
fig.tight_layout(rect=(0, 0.03, 1, 0.98))
save(fig, "31_01_tipu_naitajad")

# --- joonis 2: K vs PHF ---------------------------------------------------------------------------------------------------
fig, a = plt.subplots(figsize=(9, 6.5))
xs, ys, tx = [], [], []
for k, c in [("hommik", C_BLUE), ("ohtu", C_ORANGE)]:
    a.scatter(r[f"{k}_osakaal_%"], r[f"{k}_phf"], s=r[f"{k}_soid_h"] / 60, color=c, alpha=0.75, edgecolor="white",
              lw=0.8, label="hommik" if k == "hommik" else "õhtu")
    vali = r[(r[f"{k}_osakaal_%"].rank(ascending=False) <= 4) | (r[f"{k}_phf"].rank() <= 3)]
    xs += list(vali[f"{k}_osakaal_%"]); ys += list(vali[f"{k}_phf"]); tx += list(vali["kood"])
place_labels(a, xs, ys, tx, fontsize=7.5)
a.set_xlabel("K-tegur: tipptund, % ööpäevast")
a.set_ylabel("PHF (tipptund / 4 x suurim veerandtund)")
a.set_title("Tipu teravus: tunni osakaal ööpäevast vs tunni sisemine ühtlus")
for s in [2000, 5000, 10000]:
    a.scatter([], [], s=s / 60, color=C_GRAY, alpha=0.5, label=f"{s:,} sõid/h".replace(",", " "))
a.legend(loc="lower left", fontsize=8.5, labelspacing=1.2, borderpad=1)
fig.tight_layout()
save(fig, "31_02_k_vs_phf")

print(r["iseloom"].value_counts().to_string())
print(f"K hommik mediaan {r['hommik_osakaal_%'].median():.1f}%, õhtu {r['ohtu_osakaal_%'].median():.1f}%; "
      f"PHF hommik {r['hommik_phf'].median():.3f}, õhtu {r['ohtu_phf'].median():.3f}; "
      f"suurim K {r['K_max'].max():.1f}% ({r['kood'].iloc[-1]})")
