"""
40_3 - Vähim nihe täisvõiduks: kui kaugele peavad tipptunni autod nihkuma (pool varem, pool hiljem), et tipp saaks peaaegu
kogu võidu, mida nihe üldse anda saab. Lühike nihe jätab osa autodest samasse tundi või naabertundi, mis on niigi
tihe.

SISEND
  common.sts_andmed()             ajaloolised tööpäevade profiilid ja mudelid A (viivitus) ja B (ummikuosa), vt 40_0
  valjund/40_0_murdepunkt.csv     linna päevast päeva kõikumine ja murdepunktid (40_0 käib enne)
  valjund/40_0_ristmikud.csv      ristmike päevast päeva kõikumine
  valjund/34_profiilituubid.csv   ristmiku profiilitüüp (34)

ARVUTUS
  Osakaal p tipu kaupa (common.sts_osakaal): suurem A ja B linna murdepunktist 40_0 stsenaariumis "pool 60 min varem,
    pool hiljem" - nii palju autosid peab nihkuma, et 60 min nihe oleks märgatav.
  Nihe Δ = 15, 30, ..., 240 min (15 min andmete samm): p iga päeva tipptunni autodest nihkub pool Δ varem, pool Δ
    hiljem (common.sts_nihete_voit). Võit = halvima tunni kiiruse kasv (A, %) või ummikuosa vähenemine (B, pp),
    päevade mediaan; linn ja iga ristmik.
  Täisvõit = suurim võit üle kõigi Δ. Vähim nihe = vähim Δ, mille juures võit on vähemalt TAIS_OSA (90%) täisvõidust.
    Võrdluseks võit, kui samad autod kaoksid (ühistransport): nihe ei saa sellest suurem olla.
  Ristmik arvesse, kui tema täisvõit on vähemalt common.STS_MIN_VOIT.

VÄLJUND (kaust valjund/)
  40_3_01_vahim_nihe.png
      Näitab: kuidas võit kasvab nihke pikkusega ja kus on vähim nihe, mis annab 90% täisvõidust.
      Kuidas: 2 x 2 paneeli; rida = mudel (A kiiruse kasv %, B ummikuosa vähenemine pp), veerg = hommik, õhtu. x =
      nihe, min; oranž joon = linn, oranž vöönd = ristmike kvartiilid; sinine katkendjoon = võit, kui samad autod
      kaoksid; hall vöönd = päevast päeva kõikumine (selle sees ei märka); punktiirjoon = 90% täisvõidust; punkt ja
      silt = vähim nihe.
  40_3_02_ristmikud.png
      Näitab: vähim nihe ristmike kaupa ja kas see sõltub ristmiku päevaprofiilist (34).
      Kuidas: kaks paneeli (hommik, õhtu); rida = profiilitüüp, punkt = ristmik (sinine ring = A, oranž romb = B),
      must kriips = tüübi mediaan.
  40_3_vahim_nihe.csv   linn: mudel, tipp, p, nihe, võit, kõikumine, 90% piir; vähim nihe
  40_3_ristmikud.csv    ristmik, mudel, tipp: täisvõit, vähim nihe, võit 60 min juures, võit kui autod kaoks, tüüp
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import (sts_andmed, sts_nihete_voit, sts_osakaal, stsenaarium, set_style, save, save_table, OUT_DIR,
                    STS_AKNAD, STS_MIN_VOIT, AM_WINDOW, C_BLUE, C_ORANGE, GRID, TEXT, TEXT2)

NIHKED = list(range(15, 241, 15))                              # min
TAIS_OSA = 0.9
MUDEL = {"A": "kiiruse kasv, %", "B": "ummikuosa vähenemine, pp"}
TIPP_TXT = {"hommik": "hommik", "ohtu": "õhtu"}
TYYBID = ["ühtlane päev", "kaks teravat tippu", "õhtutipuga"]


def vahim_nihe(nihe, voit):
    """Vähim nihe, mille võit on >= TAIS_OSA x suurim võit (NaN, kui suurim võit < STS_MIN_VOIT)."""
    nihe, voit = np.asarray(nihe), np.asarray(voit)
    if not np.nanmax(voit) >= STS_MIN_VOIT:
        return np.nan
    return float(nihe[voit >= TAIS_OSA * np.nanmax(voit)][0])


assert vahim_nihe([15, 30, 45, 60], [1, 4, 9.5, 10]) == 45
set_style()
a = sts_andmed()
_v = a["V"][:20]
assert np.allclose(stsenaarium(_v, "nihe", 0.1, AM_WINDOW, 60).sum(axis=1), _v.sum(axis=1))   # autosid ei kao
l0 = pd.read_csv(OUT_DIR / "40_0_murdepunkt.csv")
mura_l = l0.groupby(["mudel", "tipp"])["koikumine"].first()
r0 = pd.read_csv(OUT_DIR / "40_0_ristmikud.csv")
mura_r = r0[r0["stsenaarium"] == "yt"].set_index(["mp_id", "mudel", "tipp"])["koikumine"]
tyyp = pd.read_csv(OUT_DIR / "34_profiilituubid.csv").set_index("mp_id")["ryhma_nimi"]
osakaal = sts_osakaal(l0)
print("nihkujate osakaal:", osakaal)

LL, RR = [], []
for tipp, aken in STS_AKNAD.items():
    linn, rist = sts_nihete_voit(a, osakaal[tipp] / 100, aken, NIHKED)
    LL.append(linn.assign(tipp=tipp, p=osakaal[tipp]))
    RR.append(rist.assign(tipp=tipp, p=osakaal[tipp]))
ll, rr = pd.concat(LL, ignore_index=True), pd.concat(RR, ignore_index=True)

rows = []
for (m, tipp), g in ll.groupby(["mudel", "tipp"]):
    n = g[g["stsenaarium"] == "nihe"].sort_values("nihe_min")
    rows.append(dict(mudel=m, tipp=tipp, p=osakaal[tipp], koikumine=mura_l[(m, tipp)], taisvoit=n["tipu_voit"].max(),
                     vahim_nihe_min=vahim_nihe(n["nihe_min"], n["tipu_voit"]),
                     voit_yt=g.loc[g["stsenaarium"] == "yt", "tipu_voit"].iloc[0]))
kl = pd.DataFrame(rows)
save_table(ll.merge(kl, on=["mudel", "tipp", "p"]).round(3), "40_3_vahim_nihe")

rows = []
for (mp, m, tipp), g in rr.groupby(["mp_id", "mudel", "tipp"]):
    n = g[g["stsenaarium"] == "nihe"].sort_values("nihe_min")
    if n["tipu_voit"].isna().all():
        continue
    rows.append(dict(mp_id=mp, kood=a["pa"].loc[mp, "kood"], mudel=m, tipp=tipp, p=osakaal[tipp],
                     tyyp=tyyp.get(mp, ""), koikumine=mura_r.get((mp, m, tipp), np.nan),
                     taisvoit=n["tipu_voit"].max(), vahim_nihe_min=vahim_nihe(n["nihe_min"], n["tipu_voit"]),
                     voit_60min=n.loc[n["nihe_min"] == 60, "tipu_voit"].iloc[0],
                     voit_yt=g.loc[g["stsenaarium"] == "yt", "tipu_voit"].iloc[0]))
kr = pd.DataFrame(rows)
save_table(kr.round(3), "40_3_ristmikud")

# --- joonis 1: linn -------------------------------------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 9), sharex=True)
for i, m in enumerate("AB"):
    for j, tipp in enumerate(STS_AKNAD):
        ax = axes[i, j]
        k = kl[(kl["mudel"] == m) & (kl["tipp"] == tipp)].iloc[0]
        n = ll[(ll["mudel"] == m) & (ll["tipp"] == tipp) & (ll["stsenaarium"] == "nihe")].sort_values("nihe_min")
        q = (rr[(rr["mudel"] == m) & (rr["tipp"] == tipp) & (rr["stsenaarium"] == "nihe")]
             .groupby("nihe_min")["tipu_voit"].quantile([0.25, 0.75]).unstack())
        ax.axhspan(0, k["koikumine"], color=GRID, alpha=0.55, lw=0, label="päevast päeva kõikumine (ei märka)")
        ax.fill_between(q.index, q[0.25], q[0.75], color=C_ORANGE, alpha=0.15, lw=0, label="ristmikud (kvartiilid)")
        ax.plot(np.r_[0, n["nihe_min"]], np.r_[0, n["tipu_voit"]], color=C_ORANGE, lw=2.4, marker="o", ms=4,
                label=f"linn: pool varem, pool hiljem")
        ax.axhline(k["voit_yt"], color=C_BLUE, ls="--", lw=1.6, label="kui samad autod kaoksid (ühistransport)")
        ax.axhline(TAIS_OSA * k["taisvoit"], color=TEXT2, ls=":", lw=1.2)
        if np.isfinite(k["vahim_nihe_min"]):
            yv = n.loc[n["nihe_min"] == k["vahim_nihe_min"], "tipu_voit"].iloc[0]
            ax.plot(k["vahim_nihe_min"], yv, "o", color=C_ORANGE, ms=10, mec=TEXT, mew=1.2, zorder=5)
            ax.annotate(f"{k['vahim_nihe_min']:.0f} min", (k["vahim_nihe_min"], yv), xytext=(8, -16),
                        textcoords="offset points", fontsize=10, fontweight="bold", color=TEXT,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
        ax.set_xlim(0, NIHKED[-1] + 5)
        ax.set_xticks(range(0, NIHKED[-1] + 1, 30))
        ax.set_ylim(bottom=0)
        ax.set_title(f"{m}: {TIPP_TXT[tipp]}, nihkub {k['p']:.0f}% tipptunni autodest", fontsize=11)
        ax.set_ylabel(f"halvima tunni {MUDEL[m]}")
        if i == 1:
            ax.set_xlabel("nihe, min (pool autodest nii palju varem, pool hiljem)")
axes[0, 0].legend(fontsize=8.5, loc="lower right")
fig.suptitle(f"Vähim nihe täisvõiduks: punkt = vähim nihe, mis annab {TAIS_OSA:.0%} suurimast võidust (punktiirjoon)",
             x=0.01, ha="left", fontweight="bold", fontsize=12)
fig.tight_layout()
save(fig, "40_3_01_vahim_nihe")

# --- joonis 2: ristmikud tüübi kaupa --------------------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 4.6), sharey=True)
rng = np.random.default_rng(3)
for ax, tipp in zip(axes, STS_AKNAD):
    for k_, t in enumerate(TYYBID):
        for m, mk, c, dy in [("A", "o", C_BLUE, 0.17), ("B", "D", C_ORANGE, -0.17)]:
            x = kr.loc[(kr["tipp"] == tipp) & (kr["mudel"] == m) & (kr["tyyp"] == t), "vahim_nihe_min"].dropna()
            ax.scatter(x + rng.uniform(-3, 3, len(x)), np.full(len(x), k_ + dy) + rng.uniform(-0.07, 0.07, len(x)),
                       marker=mk, s=30, color=c, alpha=0.75, edgecolor="white", lw=0.5,
                       label={"A": "A: viivitus -> kiirus", "B": "B: ummikuosa"}[m] if k_ == 0 else None)
            if len(x):
                ax.plot([x.median()] * 2, [k_ + dy - 0.13, k_ + dy + 0.13], color=TEXT, lw=2.2)
    ax.set_yticks(range(len(TYYBID)),
                  [f"{t}\n({(kr[(kr['tipp'] == tipp) & (kr['mudel'] == 'A')]['tyyp'] == t).sum()} ristmikku)"
                   for t in TYYBID])
    xmax = 30 * np.ceil((kr["vahim_nihe_min"].max() + 15) / 30)
    ax.set_xlim(0, xmax)
    ax.set_xticks(range(0, int(xmax) + 1, 30))
    ax.set_xlabel("vähim nihe täisvõiduks, min")
    ax.set_title(f"{TIPP_TXT[tipp].capitalize()} (nihkub {osakaal[tipp]:.0f}%)", fontsize=11)
    ax.invert_yaxis()
axes[1].legend(fontsize=9, loc="upper right")
fig.suptitle("Vähim nihe ristmike kaupa päevaprofiili tüübi järgi (34); must kriips = mediaan", x=0.01, ha="left",
             fontweight="bold", fontsize=12)
fig.tight_layout()
save(fig, "40_3_02_ristmikud")

print(kl.round(2).to_string(index=False))
print(kr.groupby(["mudel", "tipp", "tyyp"])["vahim_nihe_min"].agg(["count", "median"]).to_string())
