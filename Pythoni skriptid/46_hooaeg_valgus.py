"""
46 - Hooajalisus ja päeva pikkus: kas päevases liikluses on kalendri (nädalapäev, pühad, koolivaheajad, trend) kõrval
aastaaja mõju (hooajategur) ja kas seda kirjeldab päeva pikkus (valge aeg). Tallinna ristmikud ja Harjumaa maanteed.

SISEND
  valjund/29_paevaindeks.csv   Tallinna ristmike päevaindeks (skript 29, 29 käib enne), 29.07.2024-01.11.2026
  common.load_daily(), counter_month(), load_locations()
                               Harjumaa maanteeloendurite päevasummad (highway.count_hourly) alates MAANTEE_ALGUS
  common.day_calendar(), kalendri_tunnused()   nädalapäev, riigipüha, koolivaheaeg; regressiooni kalendritunnused (36)

ARVUTUS
  Maantee päevaindeks (nagu 29 ristmikel): loenduri päevasumma päeval, kus kõik loenduri kanalid on kehtivad, ilma
    korduvate tundideta ja kahtlase mahuga kuudeta (counter_month); loenduri tase = päevasummade mediaan tavalistel
    tööpäevadel (E-R, õppetöö, mitte püha); päeva indeks = 100 x mediaan üle loendurite (päevasumma / tase), kui
    loendureid on vähemalt MIN_LOENDUREID. Periood alates 2022 (COVID-19 aastad 2020-2021 välja).
  Päeva pikkus D, h (Tallinn 59,437° N): CBM-mudel (Forsythe jt 1995, lk 89, valemid 1-3), p = 0,8333° (päikese ülaserv
    horisondil koos valguse murdumisega).
  Mudelid: vähimruutude regressioon log(indeks), Newey-Westi standardviga (HAC, viide 7 päeva, nagu 36).
    M0   kalender (common.kalendri_tunnused ilma aastaajata: nädalapäev, koolivaheaeg tööpäeval, pühad, trend)
    MF   M0 + aastaaja Fourier' liikmed sin/cos(2 pi k päev / 365,25), k = 1, 2 (sama mis 36)
    MD   M0 + D
    MDA  M0 + D + A, A = sin(2 pi (päev - 172) / 365,25): sügisel (suvisest pööripäevast talviseni, päev lüheneb)
         positiivne, kevadel negatiivne. D on pööripäevade suhtes sümmeetriline ja A antisümmeetriline, seega mõõdab A,
         kas sama päeva pikkusega kevad- ja sügispäev erinevad. Kui aastaaja mõju tuleks ainult päeva pikkusest, oleks
         A mõju 0.
  1) Hooajategur: MF Fourier' liikmete ühine Waldi test (HAC); aastaaja kõver (Fourier' liikmete summa) kalendrikuu
     keskmisena, % aasta keskmise suhtes; ulatus = kõrgeima ja madalaima kuu vahe.
  2) Päeva pikkus: MDA D mõju (% tunni kohta) ja A mõju: sügise ja kevade erinevus sama päeva pikkuse juures
     (pööripäevadel, A = 1 vs -1), % = 100 x (exp(2 b_A) - 1). AIC: MD vs MF (väiksem on parem).
     Kontroll: sama MDA ainult õppetöö tööpäevadel (suvevaheaeg, pühad ja nädalavahetus välja).
  Joonis b, c: õppetöö tööpäevade (mitte püha) indeks M0 suhtes ehk nädalapäeva ja trendi mõjuta, päeva pikkuse 1 h
    vahemike keskmine, kevad (päev pikeneb) ja sügis (päev lüheneb) eraldi.

CALCULATION IN PLAIN ENGLISH
  Highway day index (like script 29 for junctions): each counter's daily total on complete days / its median typical
    workday; the day's index = 100 x median over counters (at least MIN_LOENDUREID). Harju County, 2022 onwards.
  Day length D (hours) for Tallinn from the CBM model (Forsythe et al. 1995), sunrise/sunset at p = 0.8333 degrees.
  Regressions of log(index): calendar only (M0); + seasonal waves (MF, as in 36); + D (MD); + D + A (MDA), where A is a
    sine that is negative in spring and positive in autumn. D is the same on both sides of the summer solstice, A has
    opposite signs, so A measures whether a spring and an autumn day with the same day length differ.
  Seasonality = joint Wald test of the seasonal waves; seasonal factor by month = average of the seasonal curve.
  Daylight = D's effect in % per hour and A's autumn-minus-spring difference at the same day length.
  Robustness: MDA on school-term workdays only.

VÄLJUND (joonised kaustas Graafikud/, tabelid kaustas valjund/)
  46_01_hooaeg_valgus.png
      Näitab: kui palju liiklus aastaaja järgi muutub ning kas sama päeva pikkusega kevad- ja sügispäevadel on liiklust
      sama palju.
      Kuidas: a) x = kalendrikuu, y = aastaaja mõju % aasta keskmise suhtes (MF Fourier' kõver): must = Tallinna
      ristmikud, hall = Harjumaa maanteed. b) ristmikud, c) maanteed: x = päeva pikkus (h), y = õppetöö tööpäeva liiklus
      % kalendrimudeli (M0) ootusest; punkt = 1 h vahemiku keskmine, vurrud = 95% usaldusvahemik (keskmise standardviga);
      sinine = kevad (päev pikeneb), oranž = sügis (päev lüheneb). Kui päeva pikkus seletaks kõike, kattuksid jooned.
  46_hooaeg_valgus.csv     andmestik ja mudel: päevi, R², AIC, Fourier' Waldi p, hooajateguri ulatus, D mõju % tunnis,
                           sügise ja kevade erinevus % sama päeva pikkusel (95% usaldusvahemik, p)
  46_hooajategurid.csv     andmestik ja kalendrikuu: aastaaja mõju % aasta keskmise suhtes (MF)
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

from common import (OUT_DIR, load_daily, counter_month, load_locations, day_calendar, kalendri_tunnused, set_style,
                    save, save_table, C_BLUE, C_ORANGE, C_GRAY, TEXT, TEXT2)

LAIUS = 59.437               # Tallinna keskus, ° N
P_KRAAD = 0.8333             # päikesetõus ja -loojang: ülaserv horisondil koos murdumisega (Forsythe jt 1995, tabel 1)
MAANTEE_ALGUS = "2022-01-01"
MIN_LOENDUREID = 15          # nagu 29 MIN_RISTMIKKE
KUUD = ["jaan", "veebr", "märts", "apr", "mai", "juuni", "juuli", "aug", "sept", "okt", "nov", "dets"]
FOURIER = ["s1", "c1", "s2", "c2"]


def paeva_pikkus(paev_nr, laius=LAIUS, p=P_KRAAD):
    """Päeva pikkus tundides, CBM-mudel (Forsythe jt 1995, valemid 1-3); paev_nr = päeva number aastas (1-366)."""
    theta = 0.2163108 + 2 * np.arctan(0.9671396 * np.tan(0.00860 * (np.asarray(paev_nr, float) - 186)))
    phi = np.arcsin(0.39795 * np.cos(theta))
    x = (np.sin(np.radians(p)) + np.sin(np.radians(laius)) * np.sin(phi)) / (np.cos(np.radians(laius)) * np.cos(phi))
    return 24 - 24 / np.pi * np.arccos(np.clip(x, -1, 1))


def tunnused(x, kuju):
    """Mudeli kuju (M0, MF, MD, MDA) tunnused; ainult nullist erinevad veerud."""
    X = kalendri_tunnused(x, hooaeg=kuju == "MF")
    nr = pd.to_datetime(x["paev"]).dt.day_of_year
    if kuju in ("MD", "MDA"):
        X["D"] = paeva_pikkus(nr)
    if kuju == "MDA":
        X["A"] = np.sin(2 * np.pi * (nr - 172) / 365.25)
    return X.loc[:, X.abs().sum() > 0]


def sobita(x, kuju):
    return sm.OLS(np.log(x["indeks"]), tunnused(x, kuju)).fit(cov_type="HAC", cov_kwds={"maxlags": 7})


def p_tekst(p):
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def pct(b):
    return 100 * (np.exp(b) - 1)


# enesekontroll: Tallinna pikim päev ~18,7 h ja lühim ~6,0 h; tehisandmetel leiab MDA +2% tunnis ja sügis = kevad
assert 18.5 < paeva_pikkus(172) < 18.9 and 5.9 < paeva_pikkus(355) < 6.2, (paeva_pikkus(172), paeva_pikkus(355))
_x = day_calendar(pd.date_range("2022-01-01", "2025-12-31"))
_x["indeks"] = 100 * np.exp(np.log(1.02) * paeva_pikkus(_x["paev"].dt.day_of_year)
                            + np.random.default_rng(0).normal(0, 0.01, len(_x)))
_f = sobita(_x, "MDA")
assert abs(pct(_f.params["D"]) - 2) < 0.2 and abs(_f.params["A"]) < 0.005, _f.params[["D", "A"]]

# --- Andmed --------------------------------------------------------------------------------------------------------
ristmik = pd.read_csv(OUT_DIR / "29_paevaindeks.csv", parse_dates=["paev"]).dropna(subset=["indeks"])
ristmik = ristmik[["paev", "indeks"]].merge(day_calendar(ristmik["paev"]), on="paev")

d = load_daily()
cm = counter_month(d)
loc = load_locations().set_index("id")
harju = set(loc.index[loc["maakond"].str.strip() == "Harju"])
nk = d.groupby("id")["kanal"].nunique()
cd = (d[d["kehtiv"] & d["id"].isin(harju) & (d["paev"] >= MAANTEE_ALGUS)]
      .groupby(["id", "paev", "kuu"]).agg(k=("kanal", "nunique"), kokku=("kokku", "sum"), dup=("duplikaat", "any"))
      .reset_index())
cd = cd[(cd["k"] == cd["id"].map(nk)) & ~cd["dup"]].merge(cm.loc[~cm["maht_kahtlane"], ["id", "kuu"]])
cd = cd.merge(day_calendar(cd["paev"]), on="paev")
tase = cd[(cd["paevatyyp"] == "tööpäev") & (cd["vaheaeg"] == "kool")].groupby("id")["kokku"].median()
cd["suhe"] = cd["kokku"] / cd["id"].map(tase)
mi = cd.groupby("paev").agg(indeks=("suhe", "median"), loendureid=("id", "nunique")).reset_index()
mi = mi[mi["loendureid"] >= MIN_LOENDUREID].assign(indeks=lambda x: 100 * x["indeks"])
maantee = mi[["paev", "indeks"]].merge(day_calendar(mi["paev"]), on="paev")
print(f"maantee: {cd['id'].nunique()} Harjumaa loendurit, {len(maantee)} päeva "
      f"({maantee['paev'].min():%d.%m.%Y}-{maantee['paev'].max():%d.%m.%Y}), loendureid päevas mediaan "
      f"{mi['loendureid'].median():.0f}")
ANDMED = {"Tallinna ristmikud": ristmik, "Harjumaa maanteed": maantee}

# --- Mudelid -------------------------------------------------------------------------------------------------------
read, kuud = [], []
pv = pd.DataFrame({"paev": pd.date_range("2025-01-01", "2025-12-31"), "nadalapaev": 0, "paevatyyp": "tööpäev",
                   "puha": None, "vaheaeg": "kool"})
Xs = kalendri_tunnused(pv)[FOURIER]
for nimi, x in ANDMED.items():
    oppetoo = x[(x["paevatyyp"] == "tööpäev") & (x["vaheaeg"] == "kool")]
    fits = {k: sobita(x, k) for k in ("M0", "MF", "MD", "MDA")}
    mf, mda, kontroll = fits["MF"], fits["MDA"], sobita(oppetoo, "MDA")
    kover = Xs @ mf.params[FOURIER]
    kuu = (100 * (np.exp(kover - kover.mean()) - 1)).groupby(pv["paev"].dt.month).mean()
    kuud += [dict(andmestik=nimi, kuu=k, moju_pct=round(v, 2)) for k, v in kuu.items()]
    wald = mf.wald_test(", ".join(f"{c} = 0" for c in FOURIER), scalar=True)
    for mudel, f, n in (("kõik päevad", mda, len(x)), ("õppetöö tööpäevad", kontroll, len(oppetoo))):
        ci = f.conf_int()
        read.append(dict(
            andmestik=nimi, mudel=mudel, paevi=n, r2_M0=fits["M0"].rsquared if mudel == "kõik päevad" else np.nan,
            r2_MF=mf.rsquared if mudel == "kõik päevad" else np.nan, r2_MDA=f.rsquared,
            aic_MF=mf.aic if mudel == "kõik päevad" else np.nan, aic_MD=fits["MD"].aic if mudel == "kõik päevad" else np.nan,
            aic_MDA=f.aic, fourier_wald_p=float(wald.pvalue) if mudel == "kõik päevad" else np.nan,
            hooajateguri_ulatus_pp=kuu.max() - kuu.min() if mudel == "kõik päevad" else np.nan,
            korgeim_kuu=KUUD[kuu.idxmax() - 1] if mudel == "kõik päevad" else "",
            madalaim_kuu=KUUD[kuu.idxmin() - 1] if mudel == "kõik päevad" else "",
            D_pct_tunnis=pct(f.params["D"]), D_alumine=pct(ci.loc["D", 0]), D_ulemine=pct(ci.loc["D", 1]),
            D_p=f.pvalues["D"], sygis_vs_kevad_pct=pct(2 * f.params["A"]), sk_alumine=pct(2 * ci.loc["A", 0]),
            sk_ulemine=pct(2 * ci.loc["A", 1]), sk_p=f.pvalues["A"]))
tab = pd.DataFrame(read)
save_table(tab.round(4), "46_hooaeg_valgus")
save_table(pd.DataFrame(kuud), "46_hooajategurid")
pd.set_option("display.width", 250)
print(tab.round(3).T.to_string())
print(pd.DataFrame(kuud).pivot(index="kuu", columns="andmestik", values="moju_pct").round(1).to_string())

# --- Joonis -------------------------------------------------------------------------------------------------------
set_style()
fig, ax = plt.subplots(1, 3, figsize=(16, 5.2), gridspec_kw={"width_ratios": [1.1, 1, 1]})
k = pd.DataFrame(kuud)
for (nimi, col) in zip(ANDMED, (TEXT, C_GRAY)):
    z = k[k["andmestik"] == nimi]
    ax[0].plot(z["kuu"], z["moju_pct"], color=col, lw=2, marker="o", ms=5, label=nimi)
ax[0].axhline(0, color=TEXT2, lw=0.8)
ax[0].set_xticks(range(1, 13), KUUD, rotation=45)
ax[0].set_ylabel("aastaaja mõju, % aasta keskmise suhtes")
ax[0].legend(fontsize=9)
ax[0].set_title("a) Hooajategur kalendri kõrval (MF)", loc="left", fontweight="bold", fontsize=10)
for a, (nimi, x) in zip(ax[1:], ANDMED.items()):
    f0 = sobita(x, "M0")
    z = x.assign(jaak=100 * (np.exp(f0.resid) - 1), D=paeva_pikkus(x["paev"].dt.day_of_year),
                 sygis=x["paev"].dt.day_of_year.between(172, 355))
    z = z[(z["paevatyyp"] == "tööpäev") & (z["vaheaeg"] == "kool")]
    z["vahemik"] = np.floor(z["D"]) + 0.5
    r = tab[(tab["andmestik"] == nimi) & (tab["mudel"] == "kõik päevad")].iloc[0]
    for syg, col, silt, dx in ((False, C_BLUE, "kevad (päev pikeneb)", -0.08), (True, C_ORANGE, "sügis (päev lüheneb)", 0.08)):
        g = z[z["sygis"] == syg].groupby("vahemik")["jaak"].agg(["mean", "sem", "size"])
        g = g[g["size"] >= 5]
        a.errorbar(g.index + dx, g["mean"], yerr=1.96 * g["sem"], color=col, lw=1.6, marker="o", ms=4, capsize=2,
                   label=silt)
    a.axhline(0, color=TEXT2, lw=0.8)
    a.set_xlabel("päeva pikkus, h (Tallinn)")
    a.set_ylabel("õppetöö tööpäev, % kalendrimudeli ootusest")
    a.legend(fontsize=9, loc="lower right")
    a.set_title(f"{'b' if a is ax[1] else 'c'}) {nimi}: sügis vs kevad sama päeva pikkusel "
                f"{r['sygis_vs_kevad_pct']:+.1f}% ({p_tekst(r['sk_p'])})".replace(".", ","), loc="left",
                fontweight="bold", fontsize=10)
fig.tight_layout()
save(fig, "46_01_hooaeg_valgus")
