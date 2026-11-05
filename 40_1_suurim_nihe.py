"""
40_1 - Suurim nihe, mis veel aitab: kui kaugele võivad tipptunni autod nihkuda (pool varem, pool hiljem), enne kui nad
jõuavad juba tihedasse aega (tipu serv, keskpäev, teine tipp) ja linna kogu päeva võit kaob.

SISEND
  common.sts_andmed()             ajaloolised tööpäevade profiilid ja mudelid A (viivitus) ja B (ummikuosa), vt 40_0
  valjund/40_0_murdepunkt.csv     linna päevast päeva kõikumine ja murdepunktid (40_0 käib enne)
  valjund/40_0_ristmikud.csv      ristmike päevast päeva kõikumine
  valjund/34_profiilituubid.csv   ristmiku profiilitüüp (34)

ARVUTUS
  Osakaal p tipu kaupa nagu 40_3 (common.sts_osakaal: nii palju, et 60 min nihe on mõlema mudeli järgi märgatav).
  Nihe Δ = 15 min sammuga kuni hommikul 360 min (6 h), õhtul 240 min (4 h; kaugemale jõuaks nihe üle südaöö):
    p iga päeva tipptunni autodest nihkub pool Δ varem, pool Δ hiljem (common.sts_nihete_voit). Kaks näitajat:
    tipu võit     halvima tunni kiiruse kasv (A, %) või ummikuosa vähenemine (B, pp), päevade mediaan
    päeva võit    kogu päeva viivituse (A: sõidukid x viivitus) või ummikuosa summa (B) vähenemine, %: kas nihkunud
                  autod tekitavad uues kohas rohkem viivitust, kui nad tipus vähendasid (miinus = päev läks halvemaks)
  Aitab = tipu võit on märgatav (>= päevast päeva kõikumine ja >= STS_MIN_VOIT) ja päeva võit > 0.
  Suurim nihe = esimese järjestikuse "aitab" lõigu viimane Δ; kui lõik ulatub arvutuse lõpuni, on suurim nihe vähemalt
    nii suur (tsenseeritud, märgitud ">="). Parim nihe = Δ, mille juures päeva võit on suurim (kaugemal hakkavad
    nihkunud autod juba tihedamat aega koormama); kui see on viimane arvutatud Δ, on parim nihe veel kaugemal.

VÄLJUND (kaust valjund/)
  40_1_01_suurim_nihe.png
      Näitab: kas linna võit kaob, kui nihe läheb väga pikaks, ja kus on nihke parim pikkus kogu päeva jaoks.
      Kuidas: 2 x 4 paneeli; veerg = mudel ja tipp (A hommik, A õhtu, B hommik, B õhtu). Ülemine rida: tipu võit
      (oranž joon), hall vöönd = päevast päeva kõikumine. Alumine rida: päeva võit, % (oranž joon), must joon = 0.
      Roheline taust = nihked, mis aitavad; punkt ja silt alumises reas = parim nihe; tekst = suurim nihe.
  40_1_02_ristmikud.png
      Näitab: kuidas kogu päeva võit muutub nihke pikkusega eri päevaprofiiliga ristmikel (34): kus nihkunud autod
      jõuavad tihedasse aega, joon langeb.
      Kuidas: kaks paneeli (hommik, õhtu); x = nihe, min; y = kogu päeva võit, % (tüübi ristmike mediaan); värv =
      profiilitüüp (nagu 34), pidev joon = A, katkendjoon = B; must joon = 0.
  40_1_suurim_nihe.csv   linn: mudel, tipp, p, nihe: tipu võit, päeva võit, aitab; suurim ja parim nihe
  40_1_ristmikud.csv     ristmik, mudel, tipp: vähim aitav nihe, suurim nihe (tsenseeritud või mitte), parim nihe
                         (tsenseeritud või mitte), päeva võit parima nihke juures, tüüp
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.lines import Line2D

from common import (sts_andmed, sts_nihete_voit, sts_osakaal, set_style, save, save_table, OUT_DIR, STS_AKNAD,
                    STS_MIN_VOIT, C_BLUE, C_ORANGE, C_AQUA, C_GREEN, GRID, TEXT, TEXT2)

NIHKED = {"hommik": list(range(15, 361, 15)), "ohtu": list(range(15, 241, 15))}      # min
MUDEL = {"A": "kiiruse kasv, %", "B": "ummikuosa vähenemine, pp"}
TIPP_TXT = {"hommik": "hommik", "ohtu": "õhtu"}
TYYBID = ["ühtlane päev", "kaks teravat tippu", "õhtutipuga"]
TYYBI_VARV = dict(zip(TYYBID, [C_BLUE, C_ORANGE, C_AQUA]))      # nagu 34


def aitav_loik(nihe, aitab):
    """(vähim, suurim, tsenseeritud): esimene järjestikune lõik, kus aitab; tsenseeritud = lõik ulatub viimase nihkeni."""
    nihe, aitab = np.asarray(nihe), np.asarray(aitab, dtype=bool)
    if not aitab.any():
        return np.nan, np.nan, False
    i = int(np.argmax(aitab))
    j = i
    while j + 1 < len(aitab) and aitab[j + 1]:
        j += 1
    return float(nihe[i]), float(nihe[j]), j == len(aitab) - 1


assert aitav_loik([15, 30, 45, 60], [False, True, True, False]) == (30, 45, False)
assert aitav_loik([15, 30, 45], [False, True, True]) == (30, 45, True)
set_style()
a = sts_andmed()
l0 = pd.read_csv(OUT_DIR / "40_0_murdepunkt.csv")
mura_l = l0.groupby(["mudel", "tipp"])["koikumine"].first()
r0 = pd.read_csv(OUT_DIR / "40_0_ristmikud.csv")
mura_r = r0[r0["stsenaarium"] == "yt"].set_index(["mp_id", "mudel", "tipp"])["koikumine"]
tyyp = pd.read_csv(OUT_DIR / "34_profiilituubid.csv").set_index("mp_id")["ryhma_nimi"]
osakaal = sts_osakaal(l0)
print("nihkujate osakaal:", osakaal)

LL, RR = [], []
for tipp, aken in STS_AKNAD.items():
    linn, rist = sts_nihete_voit(a, osakaal[tipp] / 100, aken, NIHKED[tipp])
    LL.append(linn.assign(tipp=tipp, p=osakaal[tipp]))
    RR.append(rist.assign(tipp=tipp, p=osakaal[tipp]))
ll = pd.concat(LL, ignore_index=True)
ll = ll[ll["stsenaarium"] == "nihe"].copy()
rr = pd.concat(RR, ignore_index=True)
rr = rr[rr["stsenaarium"] == "nihe"].copy()
ll["koikumine"] = [mura_l[(m, t)] for m, t in zip(ll["mudel"], ll["tipp"])]
rr["koikumine"] = [mura_r.get((mp, m, t), np.nan) for mp, m, t in zip(rr["mp_id"], rr["mudel"], rr["tipp"])]
for z in (ll, rr):
    z["aitab"] = (z["tipu_voit"] >= np.maximum(z["koikumine"], STS_MIN_VOIT)) & (z["paeva_voit"] > 0)


def kokkuvote(g):
    g = g.sort_values("nihe_min")
    lo, hi, ts = aitav_loik(g["nihe_min"], g["aitab"])
    b = g.loc[g["paeva_voit"].idxmax()] if g["paeva_voit"].notna().any() else None
    return pd.Series(dict(vahim_aitav_min=lo, suurim_nihe_min=hi, suurim_tsenseeritud=ts,
                          parim_nihe_min=b["nihe_min"] if b is not None and b["paeva_voit"] > 0 else np.nan,
                          parim_tsenseeritud=b is not None and b["nihe_min"] == g["nihe_min"].iloc[-1],
                          paeva_voit_parim=b["paeva_voit"] if b is not None else np.nan,
                          viimane_nihe_min=g["nihe_min"].iloc[-1]))


kl = ll.groupby(["mudel", "tipp", "p"]).apply(kokkuvote, include_groups=False).reset_index()
save_table(ll.merge(kl, on=["mudel", "tipp", "p"]).round(3), "40_1_suurim_nihe")
kr = rr.groupby(["mp_id", "mudel", "tipp", "p"]).apply(kokkuvote, include_groups=False).reset_index()
kr = kr.assign(kood=kr["mp_id"].map(a["pa"]["kood"]), tyyp=kr["mp_id"].map(tyyp))
save_table(kr.round(3), "40_1_ristmikud")

# --- joonis 1: linn -------------------------------------------------------------------------------------------------------
fig, axes = plt.subplots(2, 4, figsize=(18, 8.5), sharex="col")
for j, (m, tipp) in enumerate([("A", "hommik"), ("A", "ohtu"), ("B", "hommik"), ("B", "ohtu")]):
    g = ll[(ll["mudel"] == m) & (ll["tipp"] == tipp)].sort_values("nihe_min")
    k = kl[(kl["mudel"] == m) & (kl["tipp"] == tipp)].iloc[0]
    x = np.r_[0, g["nihe_min"]]
    for i, (col, ylab) in enumerate([("tipu_voit", f"halvima tunni {MUDEL[m]}"),
                                     ("paeva_voit", "kogu päeva " + ("viivituse" if m == "A" else "ummikuosa")
                                      + " vähenemine, %")]):
        ax = axes[i, j]
        for nh, ok in zip(g["nihe_min"], g["aitab"]):
            if ok:
                ax.axvspan(nh - 7.5, nh + 7.5, color=C_GREEN, alpha=0.12, lw=0)
        if i == 0:
            ax.axhspan(0, g["koikumine"].iloc[0], color=GRID, alpha=0.55, lw=0)
        ax.axhline(0, color=TEXT, lw=0.9)
        ax.plot(x, np.r_[0, g[col]], color=C_ORANGE, lw=2.3, marker="o", ms=3.5)
        ax.set_ylabel(ylab, fontsize=9.5)
        ax.set_xlim(0, x[-1] + 7.5)
        ax.set_xticks(range(0, int(x[-1]) + 1, 60))
        if i == 1:
            if np.isfinite(k["parim_nihe_min"]):
                ax.plot(k["parim_nihe_min"], k["paeva_voit_parim"], "o", color=C_ORANGE, ms=10, mec=TEXT, mew=1.2,
                        zorder=5)
                ots = bool(k["parim_tsenseeritud"])
                ax.annotate(f"parim {k['parim_nihe_min']:.0f} min" + (" või kaugemal" if ots else ""),
                            (k["parim_nihe_min"], k["paeva_voit_parim"]), xytext=(0, -18), textcoords="offset points",
                            ha="right" if ots else "center", fontsize=9.5, fontweight="bold",
                            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
            lo, hi = ax.get_ylim()
            ax.set_ylim(min(lo, -0.05 * hi), hi * 1.12)
            ax.set_xlabel("nihe, min (pool varem, pool hiljem)")
            if np.isfinite(k["suurim_nihe_min"]):
                txt = (f"aitab {k['vahim_aitav_min']:.0f}-{k['suurim_nihe_min']:.0f} min"
                       + (" ja kaugemale" if k["suurim_tsenseeritud"] else ""))
            else:
                txt = "ei aita ühegi nihkega"
            ax.text(0.97, 0.96, txt, transform=ax.transAxes, ha="right", va="top", fontsize=9.5, color=TEXT,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=GRID))
        else:
            ax.set_title(f"{m}: {TIPP_TXT[tipp]}, nihkub {k['p']:.0f}%", fontsize=11)
            ax.set_ylim(bottom=0)
fig.suptitle("Suurim nihe, mis veel aitab: ülemine rida = võit tipus (hall = päevast päeva kõikumine), alumine = kogu "
             "päeva võit (miinus = nihkunud autod koormavad uut aega rohkem); roheline = aitab", x=0.01, ha="left",
             fontweight="bold", fontsize=11.5)
fig.tight_layout()
save(fig, "40_1_01_suurim_nihe")

# --- joonis 2: päeva võit profiilitüübi kaupa ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 5.2))
rr["tyyp"] = rr["mp_id"].map(tyyp)
for ax, tipp in zip(axes, STS_AKNAD):
    for t in TYYBID:
        for m, ls, lw in [("A", "-", 2.4), ("B", "--", 1.6)]:
            q = rr[(rr["tipp"] == tipp) & (rr["mudel"] == m) & (rr["tyyp"] == t)].groupby("nihe_min")["paeva_voit"]
            q = q.median()
            ax.plot(np.r_[0, q.index], np.r_[0, q.values], color=TYYBI_VARV[t], ls=ls, lw=lw)
    ax.axhline(0, color=TEXT, lw=0.9)
    ax.set_xlim(0, NIHKED[tipp][-1] + 5)
    ax.set_xticks(range(0, NIHKED[tipp][-1] + 1, 60))
    ax.set_xlabel("nihe, min (pool varem, pool hiljem)")
    ax.set_ylabel("kogu päeva võit, % (tüübi ristmike mediaan)")
    ax.set_title(f"{TIPP_TXT[tipp].capitalize()} (nihkub {osakaal[tipp]:.0f}%)", fontsize=11)
n_t = rr[(rr["mudel"] == "A") & (rr["nihe_min"] == 60) & (rr["tipp"] == "hommik")]["tyyp"].value_counts()
axes[0].legend(handles=[Line2D([], [], color=TYYBI_VARV[t], lw=2.4, label=f"{t} ({n_t.get(t, 0)})") for t in TYYBID]
               + [Line2D([], [], color=TEXT2, lw=2.4, label="A: viivitus"),
                  Line2D([], [], color=TEXT2, lw=1.6, ls="--", label="B: ummikuosa")], fontsize=9, loc="upper left")
fig.suptitle("Kogu päeva võit nihke pikkuse järgi päevaprofiili tüübiti (34): langev joon = nihkunud autod jõuavad "
             "tihedasse aega", x=0.01, ha="left", fontweight="bold", fontsize=12)
fig.tight_layout()
save(fig, "40_1_02_ristmikud")

print(kl.round(2).to_string(index=False))
print(kr.groupby(["mudel", "tipp"]).agg(ristmikke=("mp_id", "size"), ei_aita=("suurim_nihe_min", lambda s: s.isna().sum()),
                                        tsenseeritud=("suurim_tsenseeritud", "sum"),
                                        suurim_med=("suurim_nihe_min", "median"),
                                        parim_med=("parim_nihe_min", "median")).to_string())
print(kr[~kr["suurim_tsenseeritud"] & kr["suurim_nihe_min"].notna()]
      [["kood", "mudel", "tipp", "tyyp", "vahim_aitav_min", "suurim_nihe_min", "parim_nihe_min"]].to_string(index=False))
