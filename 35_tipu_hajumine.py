"""
35 - Kas tipp hajub ajas? Tipptunni osakaal, liikluse keskaeg ja tipu teravus kuude kaupa 2024-08 ... 2026-10, iga
õppeaasta oma joonena: kui inimesed juba ise sõiduaegu nihutavad, peaks tipptunni osakaal aasta-aastalt langema ja
tipp laienema.

SISEND
  common.load_tallinn()      ristmike 15 min loendused puhastatult (tallinn.count_15min)

ARVUTUS
  Päevad: tööpäevad (E-R, mitte püha ega lühendatud päev), ka koolivaheajal - kuu väärtus sisaldab sama kuu vaheaegu
    igal aastal (vaheajad on samadel nädalatel). Ristmikud: kindel valim - ristmikud, millel on kehtiv päev vähemalt
    PANEEL_OSA kõigist tööpäevadest (ristmike koosseisu muutus ei tohi tekitada näilist trendi).
  Iga ristmiku iga päeva kohta common.peak_metrics (15 min profiil): K = tipptunni osakaal ööpäevast, %; keskaeg =
    mahuga kaalutud keskmine kellaaeg (hommik 06-10, õhtu 15-19); teravus = 1 - (tipptund +-1 h keskmine tunnimaht) /
    tipptunni maht, % (peak_metrics max_potentsiaal_%: nii palju väheneks tipptund, kui liiklus jaotuks 3 tunnile
    ühtlaselt; tipu laius minutites oleks 15 min andmetel astmeline).
  Linna päeva väärtus = ristmike mediaan; kuu väärtus = päevade mediaan (kuud, kus on vähemalt MIN_PAEVI tööpäeva).
  Õppeaasta = august kuni juuli (2024/25, 2025/26, 2026/27).
  Aastamuutus: sama kuu kahel järjestikusel õppeaastal; iga ristmiku kuumediaanide paariserinevus, ristmike mediaan ja
    Wilcoxoni märgiga astakute test (scipy) - kas muutus on ristmikel ühesuunaline.

VÄLJUND (kaust valjund/)
  35_01_tipu_hajumine.png
      Näitab: kas tipptund on aasta-aastalt lamedamaks või laiemaks muutunud ja kas liikluse keskaeg on nihkunud.
      Kuidas: 2 x 3 paneeli; rida = hommik, õhtu; veerg = K (% ööpäevast), keskaeg (kellaaeg, telg vähemalt 12 min
      lai, et väike kõikumine ei paistaks suurena), teravus (%). x =
      õppeaasta kuu (aug ... juuli), joon = õppeaasta (heledam = varasem, tumedam = hilisem), punkt = kuu mediaan. Hall
      vöönd = suvevaheaja kuud.
  35_kuud.csv           kuu ja õppeaasta: tööpäevi, K, keskaeg, teravus (hommik, õhtu)
  35_aastamuutus.csv    näitaja, kuu, õppeaastad: linna muutus, ristmike mediaanmuutus, ristmikke, Wilcoxoni p
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon

from common import load_tallinn, peak_metrics, set_style, save, save_table, hhmm, GRID, TEXT2

PANEEL_OSA = 0.85
MIN_PAEVI = 10
KUUD = ["aug", "sept", "okt", "nov", "dets", "jaan", "veebr", "märts", "apr", "mai", "juuni", "juuli"]
NAITAJAD = [("osakaal_%", "K: tipptund, % ööpäevast"), ("keskaeg_h", "liikluse keskaeg"),
            ("max_potentsiaal_%", "teravus: tipptund vs +-1 h, %")]
KESKAEG_SPAN = 12 / 60                       # keskaja telg vähemalt 12 min lai


def oppeaasta(p):
    """Kuupäev -> (õppeaasta 'AAAA/AA', kuu järjekord 0 = august ... 11 = juuli)."""
    a = p.year if p.month >= 8 else p.year - 1
    return f"{a}/{(a + 1) % 100:02d}", (p.month - 8) % 12


assert oppeaasta(pd.Timestamp("2025-08-01")) == ("2025/26", 0) and oppeaasta(pd.Timestamp("2026-07-31")) == ("2025/26", 11)

set_style()
t, d = load_tallinn()
d = d[d["kehtiv"] & (d["paevatyyp"] == "tööpäev")]
tp = d["paev"].nunique()
paneel = d.groupby("mp_id").size()
paneel = paneel[paneel >= PANEEL_OSA * tp].index
d = d[d["mp_id"].isin(paneel)]
t = t.merge(d[["mp_id", "paev"]], on=["mp_id", "paev"])
w = t.pivot_table(index=["mp_id", "paev"], columns="slot", values="v", aggfunc="sum")
w = w[w.notna().sum(axis=1) >= 88].T.interpolate(limit_direction="both").T
veerud = [f"{tipp}_{n}" for tipp in ["hommik", "ohtu"] for n, _ in NAITAJAD]
pm = pd.DataFrame([peak_metrics(x) for x in w.values], index=w.index)[veerud].astype(float).reset_index()
pm[["oppeaasta", "kuu_nr"]] = pd.DataFrame([oppeaasta(p) for p in pm["paev"]], index=pm.index)

paev = pm.groupby(["paev", "oppeaasta", "kuu_nr"])[veerud].median().reset_index()
kuu = paev.groupby(["oppeaasta", "kuu_nr"]).agg(tooaevi=("paev", "size"), **{c: (c, "median") for c in veerud}).reset_index()
kuu = kuu[kuu["tooaevi"] >= MIN_PAEVI]
save_table(kuu.assign(kuu=kuu["kuu_nr"].map(dict(enumerate(KUUD)))), "35_kuud")

# --- aastamuutus: ristmike paariserinevused -------------------------------------------------------------------------------
rk = pm.groupby(["mp_id", "oppeaasta", "kuu_nr"])[veerud].median()
aastad = sorted(kuu["oppeaasta"].unique())
rows = []
for a0, a1 in zip(aastad[:-1], aastad[1:]):
    for k in sorted(set(kuu.loc[kuu["oppeaasta"] == a0, "kuu_nr"]) & set(kuu.loc[kuu["oppeaasta"] == a1, "kuu_nr"])):
        for c in veerud:
            x0 = rk.xs((a0, k), level=["oppeaasta", "kuu_nr"])[c]
            x1 = rk.xs((a1, k), level=["oppeaasta", "kuu_nr"])[c]
            dd = (x1 - x0).dropna()
            linn = kuu.set_index(["oppeaasta", "kuu_nr"])[c]
            rows.append(dict(naitaja=c, kuu=KUUD[k], oppeaastad=f"{a0} -> {a1}", linna_muutus=linn[(a1, k)] - linn[(a0, k)],
                             ristmike_mediaan=dd.median(), ristmikke=len(dd), langes=int((dd < 0).sum()),
                             wilcoxon_p=wilcoxon(dd).pvalue if (dd != 0).sum() >= 6 else np.nan))
am = pd.DataFrame(rows)
save_table(am, "35_aastamuutus")

# --- joonis ----------------------------------------------------------------------------------------------------------------
varv = dict(zip(aastad, plt.get_cmap("Blues")(np.linspace(0.4, 0.95, len(aastad)))))
fig, ax = plt.subplots(2, 3, figsize=(16, 8.5), sharex=True)
for i, tipp in enumerate(["hommik", "ohtu"]):
    for j, (n, nimi) in enumerate(NAITAJAD):
        a = ax[i, j]
        a.axvspan(9.5, 12.5, color=GRID, alpha=0.7, lw=0)            # juuni (osaliselt) ... juuli
        a.axvspan(-0.5, 0.5, color=GRID, alpha=0.7, lw=0)            # august
        for oa in aastad:
            z = kuu[kuu["oppeaasta"] == oa]
            a.plot(z["kuu_nr"], z[f"{tipp}_{n}"], color=varv[oa], marker="o", ms=5, lw=2, label=oa)
        a.set_title(f"{'Hommik' if tipp == 'hommik' else 'Õhtu'}: {nimi}", fontsize=11)
        if n == "keskaeg_h":
            lo, hi = a.get_ylim()
            if hi - lo < KESKAEG_SPAN:
                m = (lo + hi) / 2
                a.set_ylim(m - KESKAEG_SPAN / 2, m + KESKAEG_SPAN / 2)
            a.yaxis.set_major_locator(plt.MultipleLocator(2 / 60))
            a.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: hhmm(v)))
        a.set_xlim(-0.5, 11.5)
        a.set_xticks(range(12), KUUD, rotation=45)
ax[0, 0].legend(title="õppeaasta", fontsize=9, title_fontsize=9)
ax[1, 0].text(11, ax[1, 0].get_ylim()[0], "suvi", ha="center", va="bottom", fontsize=8, color=TEXT2)
fig.suptitle(f"Kas tipp hajub? Tööpäevade kuu mediaanid, {len(paneel)} ristmiku kindel valim", x=0.01, ha="left",
             fontweight="bold", fontsize=12)
fig.tight_layout()
save(fig, "35_01_tipu_hajumine")

print(f"ristmikke valimis {len(paneel)}, tööpäevi {tp}")
koond = am.groupby(["naitaja", "oppeaastad"]).agg(kuid=("kuu", "size"), linna_muutus=("linna_muutus", "mean"),
                                                  olulisi=("wilcoxon_p", lambda p: int((p < 0.05).sum())))
print(koond.round(3).to_string())
