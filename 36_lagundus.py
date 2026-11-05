"""
36 - Liikluse lagundamine: kui palju muudavad Tallinna päevast liiklust nädalapäev, koolivaheaeg, riigipüha, aastaaeg
ja pikaajaline trend (regressioon) ning millised päevad jäävad sellest mustrist kõige rohkem välja (erandpäevad).

SISEND
  valjund/29_paevaindeks.csv   skripti 29 väljund (29 käib enne): päeva indeks (% tavalisest tööpäevast, ristmike
                               mediaan), nädalapäev, päevatüüp, riigipüha, koolivaheaeg

ARVUTUS
  Mudel (vähimruutude regressioon, statsmodels OLS): log(indeks) = vabaliige
      + nädalapäev (T, K, N, R, L, P; võrdlus esmaspäev)
      + koolivaheaeg tööpäeval (lühike, jõulud, suvi; võrdlus õppetöö tööpäev) - vaheaeg mõjutab ainult tööpäevi
      + suur püha tööpäeval (SUURED_PYHAD: uusaasta, jõulud, võidupüha ja jaanipäev), muu riigipüha tööpäeval,
        riigipüha nädalavahetusel, lühendatud tööpäev
      + aastaaeg: Fourier' liikmed sin/cos(2 pi k päev / 365,25), k = 1, 2 (sujuv aastane rütm)
      + trend (aastates)
  Mõju = 100 x (exp(b) - 1) % ehk mitu protsenti liiklus selle tunnuse korral muutub, kui muu on sama. 95%
    usaldusvahemik Newey-Westi standardveaga (HAC, viide 7 päeva: järjestikuste päevade jäägid on seotud).
  Osa seletatud kõikumisest: kui palju langeb R² (kõik päevad), kui tunnuste rühm mudelist välja jätta (osaline mõju;
    rühmad on osaliselt seotud, seega ei liitu need täpselt R²-ks).
  Erandpäev: standardiseeritud jääk |z| >= Z_ERAND, z = jääk / (1,4826 x jääkide MAD) (robustne, erandid ise ei
    suurenda hajuvust). Kõrvalekalle % = 100 x (exp(jääk) - 1).

VÄLJUND (kaust valjund/)
  36_01_lagundus.png
      Näitab: millised kalendritunnused muudavad linna liiklust kõige rohkem ja kui palju kõikumisest need seletavad.
      Kuidas: vasakul mõjud, % (punkt = hinnang, joon = 95% usaldusvahemik), rühmitatud: nädalapäev (esmaspäeva
      suhtes), koolivaheaeg (õppetöö tööpäeva suhtes), pühad, trend (% aastas). Keskel aastaaja mõju kalendrikuu järgi
      (Fourier' liikmete summa, %, aasta keskmise suhtes). Paremal R² langus, kui rühm välja jätta (%-punkti).
  36_02_erandpaevad.png
      Näitab: kui hästi kalender päevast liiklust kirjeldab ja millised päevad sellest välja jäävad.
      Kuidas: üleval hallid punktid = päeva indeks, sinised = mudeli väärtus; all jääk, % (punkt), punased = erandpäevad
      (|z| >= Z_ERAND), suurimad sildiga (kuupäev ja nädalapäev).
  36_mojud.csv          tunnus: mõju %, 95% usaldusvahemik, p
  36_erandpaevad.csv    erandpäevad: kuupäev, nädalapäev, päevatüüp, indeks, mudel, kõrvalekalle %, z
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import statsmodels.api as sm

from common import OUT_DIR, set_style, save, save_table, place_labels, C_BLUE, C_RED, C_GRAY, TEXT, TEXT2, GRID

Z_ERAND = 3.5
SILTE = 14
NADALAPAEV = ["E", "T", "K", "N", "R", "L", "P"]
KUUD = ["jaan", "veebr", "märts", "apr", "mai", "juuni", "juuli", "aug", "sept", "okt", "nov", "dets"]
SUURED_PYHAD = {"uusaasta", "jõululaupäev", "esimene jõulupüha", "teine jõulupüha", "võidupüha", "jaanipäev"}
RYHMAD = {"nädalapäev": ["T", "K", "N", "R", "L", "P"], "koolivaheaeg": ["vaheaeg_lühike", "vaheaeg_jõulud", "vaheaeg_suvi"],
          "pühad": ["suur_püha", "muu_püha", "püha_nädalavahetusel", "lühendatud"], "aastaaeg": ["s1", "c1", "s2", "c2"],
          "trend": ["trend"]}
SILDID = {"T": "teisipäev", "K": "kolmapäev", "N": "neljapäev", "R": "reede", "L": "laupäev", "P": "pühapäev",
          "vaheaeg_lühike": "lühike vaheaeg", "vaheaeg_jõulud": "jõuluvaheaeg", "vaheaeg_suvi": "suvevaheaeg",
          "suur_püha": "suur püha tööpäeval", "muu_püha": "muu riigipüha tööpäeval", "püha_nädalavahetusel": "riigipüha L/P", "lühendatud": "lühendatud tööpäev",
          "trend": "trend, % aastas"}


def tunnused(x):
    """Päevade tabel (paev, nadalapaev, paevatyyp, puha, vaheaeg) -> regressiooni tunnuste maatriks (vabaliikmega)."""
    p = pd.to_datetime(x["paev"])
    tp = x["nadalapaev"] < 5
    X = pd.DataFrame(index=x.index)
    for i, n in enumerate(NADALAPAEV[1:], start=1):
        X[n] = (x["nadalapaev"] == i).astype(float)
    for v in ["lühike", "jõulud", "suvi"]:
        X[f"vaheaeg_{v}"] = ((x["vaheaeg"] == v) & tp & (x["paevatyyp"] != "riigipüha")).astype(float)
    puha = x["puha"].notna()
    suur = x["puha"].isin(SUURED_PYHAD)
    X["suur_püha"] = (suur & tp).astype(float)
    X["muu_püha"] = (puha & ~suur & tp).astype(float)
    X["püha_nädalavahetusel"] = (puha & ~tp).astype(float)
    X["lühendatud"] = (x["paevatyyp"] == "lühendatud").astype(float)
    a = 2 * np.pi * p.dt.day_of_year / 365.25
    for k in (1, 2):
        X[f"s{k}"], X[f"c{k}"] = np.sin(k * a), np.cos(k * a)
    X["trend"] = (p - p.min()).dt.days / 365.25
    return sm.add_constant(X)


def mojud(fit, nimed):
    """Logaritmilised kordajad -> mõju % ja 95% usaldusvahemik."""
    ci = fit.conf_int().loc[nimed]
    return pd.DataFrame({"moju_pct": 100 * (np.exp(fit.params[nimed]) - 1), "alumine": 100 * (np.exp(ci[0]) - 1),
                         "ulemine": 100 * (np.exp(ci[1]) - 1), "p": fit.pvalues[nimed]})


# enesekontroll: tehisandmetel peab mudel leidma laupäeva -30% ja suvevaheaja -10%
_p = pd.date_range("2024-08-01", "2026-07-31")
_x = pd.DataFrame({"paev": _p, "nadalapaev": _p.day_of_week, "paevatyyp": np.where(_p.day_of_week == 5, "laupäev", "tööpäev"),
                   "puha": None, "vaheaeg": np.where(_p.month.isin([7]), "suvi", "kool")})
_y = np.log(100) + np.log(0.7) * (_x["nadalapaev"] == 5) + np.log(0.9) * ((_x["vaheaeg"] == "suvi") & (_x["nadalapaev"] < 5))
_X = tunnused(_x)
_m = mojud(sm.OLS(_y + np.random.default_rng(0).normal(0, 0.01, len(_y)), _X.loc[:, _X.abs().sum() > 0]).fit(),
           ["L", "vaheaeg_suvi"])
assert abs(_m.loc["L", "moju_pct"] + 30) < 1 and abs(_m.loc["vaheaeg_suvi", "moju_pct"] + 10) < 1.5, _m

set_style()
d = pd.read_csv(OUT_DIR / "29_paevaindeks.csv", parse_dates=["paev"]).dropna(subset=["indeks"]).reset_index(drop=True)
X, y = tunnused(d), np.log(d["indeks"])
X = X.loc[:, X.abs().sum() > 0]                           # tunnus, mida andmetes pole (nt lühendatud päev), välja
fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 7})
nimed = [c for g, cs in RYHMAD.items() if g != "aastaaeg" for c in cs if c in X.columns]
m = mojud(fit, nimed)
m.insert(0, "tunnus", [SILDID[c] for c in m.index])
m.insert(0, "ryhm", [next(g for g, cs in RYHMAD.items() if c in cs) for c in m.index])
save_table(m.reset_index(names="kood").round(4), "36_mojud")
r2 = fit.rsquared
osa = {g: r2 - sm.OLS(y, X.drop(columns=[c for c in cs if c in X.columns])).fit().rsquared for g, cs in RYHMAD.items()}

d["mudel"] = np.exp(fit.fittedvalues)
d["jaak"] = fit.resid
mad = 1.4826 * np.median(np.abs(d["jaak"] - np.median(d["jaak"])))
d["z"] = d["jaak"] / mad
d["korvalekalle_pct"] = 100 * (np.exp(d["jaak"]) - 1)
er = d[d["z"].abs() >= Z_ERAND].copy()
er["nadalapaev_nimi"] = er["nadalapaev"].map(dict(enumerate(NADALAPAEV)))
save_table(er[["paev", "nadalapaev_nimi", "paevatyyp", "puha", "vaheaeg", "indeks", "mudel", "korvalekalle_pct", "z"]],
           "36_erandpaevad")

# --- joonis 1: mõjud ---------------------------------------------------------------------------------------------------------
fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(16, 6.3), gridspec_kw={"width_ratios": [1.3, 1, 0.8]})
y0, yt, yl = 0, [], []
for g in ["nädalapäev", "koolivaheaeg", "pühad", "trend"]:
    z = m[m["ryhm"] == g]
    a1.text(-0.01, y0 - 0.15, g.upper(), transform=a1.get_yaxis_transform(), ha="right", fontsize=8, color=TEXT2,
            fontweight="bold")
    y0 += 0.6
    for c, r in z.iterrows():
        a1.hlines(y0, r["alumine"], r["ulemine"], color=C_BLUE, lw=2)
        a1.scatter(r["moju_pct"], y0, color=C_BLUE, s=34, zorder=3)
        a1.text(r["ulemine"] + 1, y0, f"{r['moju_pct']:+.1f}%".replace(".", ","), va="center", fontsize=8, color=TEXT)
        yt.append(y0); yl.append(r["tunnus"])
        y0 += 1
    y0 += 0.4
a1.axvline(0, color=TEXT, lw=0.8)
a1.set_yticks(yt, yl, fontsize=9)
a1.set_ylim(y0 - 0.5, -0.7)
a1.set_xlabel("mõju päeva liiklusele, %")
a1.set_title(f"Kalendri mõjud (R² = {r2:.2f}, {len(d)} päeva)".replace(".", ","))
pv = pd.date_range("2025-01-01", "2025-12-31")
Xs = tunnused(pd.DataFrame({"paev": pv, "nadalapaev": 0, "paevatyyp": "tööpäev", "puha": None, "vaheaeg": "kool"}))
hooaeg = Xs[["s1", "c1", "s2", "c2"]] @ fit.params[["s1", "c1", "s2", "c2"]]
a2.plot(pv, 100 * (np.exp(hooaeg - hooaeg.mean()) - 1), color=C_BLUE, lw=2.2)
a2.axhline(0, color=TEXT, lw=0.8)
a2.set_xticks(pd.date_range("2025-01-01", periods=12, freq="MS") + pd.Timedelta(days=14), KUUD, rotation=45)
a2.set_ylabel("%, aasta keskmise suhtes")
a2.set_title("Aastaaja mõju (sujuv, ilma vaheaegadeta)")
og = pd.Series(osa).sort_values()
a3.barh(range(len(og)), og.values * 100, color=C_BLUE, height=0.6)
for i, v in enumerate(og.values * 100):
    a3.text(v + 0.3, i, f"{v:.1f}".replace(".", ","), va="center", fontsize=8.5)
a3.set_yticks(range(len(og)), og.index)
a3.set_xlabel("R² langus, kui rühm välja jätta, %-punkti")
a3.set_title("Osa seletatud kõikumisest")
fig.tight_layout()
save(fig, "36_01_lagundus")

# --- joonis 2: mudel ja erandpäevad ------------------------------------------------------------------------------------------
fig, (b1, b2) = plt.subplots(2, 1, figsize=(16, 8), sharex=True, gridspec_kw={"height_ratios": [1.5, 1]})
b1.scatter(d["paev"], d["indeks"], s=6, color=C_GRAY, alpha=0.7, label="päeva indeks")
b1.scatter(d["paev"], d["mudel"], s=4, color=C_BLUE, label="mudel (kalender)")
b1.set_ylabel("% tavalisest tööpäevast")
b1.set_title(f"Päeva liiklus ja kalendrimudel: jääkide hajuvus {100 * mad:.1f}% (robustne)".replace(".", ","))
b1.legend(loc="lower left", fontsize=9)
on = d["z"].abs() >= Z_ERAND
b2.axhline(0, color=TEXT, lw=0.8)
b2.axhspan(-100 * Z_ERAND * mad, 100 * Z_ERAND * mad, color=GRID, alpha=0.6, lw=0)
b2.scatter(d.loc[~on, "paev"], d.loc[~on, "korvalekalle_pct"], s=6, color=C_GRAY, alpha=0.7)
b2.scatter(d.loc[on, "paev"], d.loc[on, "korvalekalle_pct"], s=18, color=C_RED, zorder=3)
sl = er.reindex(er["z"].abs().sort_values(ascending=False).index).head(SILTE)
place_labels(b2, list(mdates.date2num(sl["paev"])), list(sl["korvalekalle_pct"]),
             [f"{p_:%d.%m.%y} {n}" for p_, n in zip(sl["paev"], sl["nadalapaev_nimi"])], fontsize=7)
b2.set_ylabel("kõrvalekalle mudelist, %")
b2.set_title(f"Erandpäevad: punane = |z| >= {Z_ERAND} ({on.sum()} päeva); hall vöönd = tavaline hajuvus".replace(".", ","))
fig.tight_layout()
save(fig, "36_02_erandpaevad")

print(f"R² {r2:.3f}, jääkide robustne hajuvus {100 * mad:.1f}%, erandpäevi {on.sum()}")
print(m.round(2).to_string())
print({k: round(100 * v, 1) for k, v in osa.items()})
print(er.sort_values("z")[["paev", "nadalapaev_nimi", "paevatyyp", "puha", "indeks", "korvalekalle_pct", "z"]].to_string(
    float_format=lambda v: f"{v:.1f}"))
