"""
02 - Üleriigiline seos: maanteede liiklusindeks ja mootorikütuse jaemüük.

Bensiini müüki võrreldakse kergsõidukite (klassid 1-3) liiklusega ja diislikütuse müüki kaubikute, veokite ja busside
(klassid 4-10) liiklusega; lisaks diisel vs rasked veokid (klassid 6-8) ja kogu kütus vs kogu liiklus.

SISEND
  common.load_daily(), counter_month()   maanteeloendurite kehtivad loendur-kuud: keskmine ööpäevane liiklus
                                         sõidukirühmade kaupa (tunniloendustest, highway.count_hourly)
  common.load_fuel_national()            kütuse jaemüük tanklatest kuude kaupa, liitrit päevas
                                         (fuel.retail_monthly; bensiin = alla 98 + üle 98)
  fuel.retail_semimonthly                sama poolkuude kaupa (aruandeperiood 1 = kuu 1.-15. päev, 2 = 16. kuni lõpp)

ARVUTUS
  Liiklusindeks (common.traffic_index): iga kuu kohta nende loendurite ööpäevase liikluse summa, millel on sel kuul
    kehtivad andmed, jagatud samade loendurite 2023. a keskmiste summaga, x 100. Loenduri lisandumine või kadumine
    ei tekita seega hüpet. Kuu läheb arvesse, kui loendureid on >= 3; kahtlased loendur-kuud on väljas.
  Müügiindeks: liitrit päevas jagatud 2023. a keskmisega, x 100.
  Iga seos arvutatakse kolmel kujul, sest ühine hooajalisus paisutab toorandmete korrelatsiooni:
    tase      indeksid nii, nagu need on
    YoY       aastane muutus (ln x[kuu] - ln x[kuu - 12]) x 100, ligikaudu % - eemaldab hooajalisuse
    STL jääk  logaritmitud rea STL-lahutuse (periood 12, robustne) jääk x 100 - eemaldab trendi ja hooajalisuse;
              kõige rangem test
  Korrelatsioon (common.corr_pair): Pearsoni r ja Spearmani rho koos p-väärtustega, vähemalt 6 ühist kuud.
    Tundlikkus: sama ilma COVID-kuudeta (2020-03...2020-06; aastase muutuse puhul ka 2021. a samad kuud, sest need
    võrdlevad COVID-kuudega).
  Elastsus: regressioon ln(müük) = a + e x ln(liiklus) + kalendrikuu näivmuutujad + lineaarne trend. e näitab, mitu %
    muutub müük, kui liiklus muutub 1%. Standardvead on autokorrelatsiooni suhtes kindlad (HAC, 3 viidet).
  Viitega korrelatsioon (poolkuu andmed): liiklusindeks poolkuude kaupa (kanal-periood kehtib alates 7 päevast), mõlema
    rea aastane muutus (24 poolkuud) ja nende korrelatsioon, kui müüki nihutada -4...+4 poolkuud (positiivne nihe =
    müük järgneb liiklusele).

CALCULATION IN PLAIN ENGLISH
  Traffic index (one number per month): add up the average daily traffic of the counters that have valid data in the
    month, divide by the 2023 averages of the same counters added up, multiply by 100. The same counters are on both
    sides of the division, so a counter starting or stopping does not make a jump. A month needs at least 3 counters;
    suspicious counter-months are left out. Separate indexes for all vehicles, light (classes 1-3), heavy (4-10) and
    lorries (6-8).
  Sales index: litres sold per day (month's litres / days in the month) / 2023 average x 100.
  Each traffic-sales pair is compared three ways:
    level  the two indexes as they are;
    YoY    year-on-year change = (ln of this month - ln of the same month a year earlier) x 100, close to a % change;
           missing months are inserted as gaps, so the comparison is always exactly 12 months back;
    STL    the log series is split into trend + seasonal pattern + remainder (12-month season, on the longest stretch
           without gaps); remainder x 100 is compared. This is the strictest test.
  Correlation: Pearson r and Spearman rho over the months both series have (at least 6), and again without the COVID
    months (March-June 2020; for YoY also the same months of 2021, which are compared with them).
  Elasticity: regression of ln(sales) on ln(traffic) with one dummy per calendar month and a linear trend. The traffic
    coefficient = % change in sales when traffic changes 1%. Standard errors allow for autocorrelation (HAC, 3 lags).
  Lagged correlation: the same traffic index for half-months (1st-15th, 16th-end; a lane needs 7 valid days); both
    series as year-on-year change over 24 half-months (missing half-months as gaps); correlation when sales are shifted
    -4 ... +4 half-months.

VÄLJUND (kaust valjund/)
  02_01_aegread.png
      Näitab: kas liiklus ja kütusemüük liiguvad ajas koos.
      Kuidas: kaks paneeli üksteise all (bensiin vs kerged sõidukid; diisel vs kaubikud, veokid, bussid). x-telg = aeg,
      y-telg = indeks (2023 = 100). Hall joon = liiklusindeks, värviline joon = müük (sinine bensiin, oranž diisel),
      punktiir = tase 100; märgitud on 2020. a kevade COVID-langus.
  02_02_hajuvus_tase.png, 02_03_hajuvus_yoy.png, 02_04_hajuvus_stl.png
      Näitab: seose tugevust kolmel kujul (tase, aastane muutus, STL jääk).
      Kuidas: hajuvusdiagramm, kaks paneeli (bensiin, diisel). Punkt = üks kuu; x-telg = liiklus, y-telg = müük samal
      kujul. Joon = lineaarne regressioon koos 95% usalduspiirkonnaga. Musta ringiga on märts-mai 2020. Paneeli
      nurgas r, p, rho ja n ning r ja rho ilma COVID-kuudeta.
  02_05_viitega_korrelatsioon.png
      Näitab: kas kütusemüük reageerib liiklusele kohe või viitega.
      Kuidas: joondiagramm; x-telg = nihe poolkuudes (-4...+4), y-telg = aastaste muutuste Pearsoni r. Sinine =
      bensiin vs kerged, oranž = diisel vs kaubikud, veokid, bussid; püstine punktiir = nihe 0.
  02_kuuandmed.csv               kuu liiklus- ja müügiindeksid
  02_korrelatsioonid.csv         kõik korrelatsioonid (paar x kuju x valim)
  02_elastsus.csv                elastsus e, 95% usaldusvahemik, p, trend % aastas, R2, n
  02_viitega_korrelatsioon.csv   korrelatsioon iga nihke kohta
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.formula.api as smf

from common import (load_daily, counter_month, traffic_index, load_fuel_national,
                    set_style, save, save_table, yoy, stl_resid, corr_pair, month_axis,
                    FUEL_COLOR, FUEL_LABEL, GROUP_LABEL, C_GRAY, TEXT2, BASE_YEAR, tabel, START, END)

set_style()
print("Laen andmeid...")
d = load_daily()
cm = counter_month(d)

# Kuu tasemel -----------------------------------------------------------------------
idx = {g: traffic_index(cm, value=g).set_index("kuu")["indeks"]
       for g in ["kokku", "kerge", "raske", "veok"]}
fuel = load_fuel_national().set_index("kuu")
fuel["kokku"] = fuel["bensiin"] + fuel["diisel"]
fidx = fuel / fuel[fuel.index.year == BASE_YEAR].mean() * 100

df = pd.DataFrame({f"liiklus_{g}": s for g, s in idx.items()}).join(fidx, how="inner")
df.index.name = "kuu"
save_table(df.reset_index(), "02_kuuandmed")

COVID = (pd.Period("2020-03", "M"), pd.Period("2020-06", "M"))
PAIRS = [("bensiin", "kerge"), ("diisel", "raske"), ("diisel", "veok"), ("kokku", "kokku")]

# 1) Aegread -----------------------------------------------------------------------
fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
for ax, (f, g) in zip(axes, PAIRS[:2]):
    t = df.index.to_timestamp()
    ax.plot(t, df[f"liiklus_{g}"], color=C_GRAY, label=f"Liiklusindeks: {GROUP_LABEL[g]}")
    ax.plot(t, df[f], color=FUEL_COLOR[f], label=f"{FUEL_LABEL[f]} jaemüük")
    ax.axhline(100, color=TEXT2, lw=0.6, ls=":")
    ax.set_ylabel(f"Indeks, {BASE_YEAR} = 100")
    ax.set_title(f"{FUEL_LABEL[f]} vs {GROUP_LABEL[g].lower()}")
    ax.legend(loc="upper left", fontsize=9, ncol=2)
axes[0].annotate("COVID-19\nkevad 2020", xy=(pd.Timestamp("2020-04-01"), 72),
                 xytext=(pd.Timestamp("2020-10-01"), 62), fontsize=8, color=TEXT2,
                 arrowprops=dict(arrowstyle="-", color=TEXT2, lw=0.6))
month_axis(axes[1])
save(fig, "02_01_aegread")

# 2) Korrelatsioonid kolmel kujul -----------------------------------------------------
rows = []
series = {}
for f, g in PAIRS:
    a, b = df[f"liiklus_{g}"], df[f]
    for kuju, fa, fb in [("tase", a, b), ("YoY", yoy(a), yoy(b)),
                         ("STL jääk", stl_resid(a), stl_resid(b))]:
        rows.append(dict(kutus=f, liiklus=g, kuju=kuju, valim="kõik kuud", **corr_pair(fa, fb)))
        # tundlikkus: COVID-kuud välja (üks äärmuslik punkt võib r-i paisutada)
        keep = ~((fa.index >= COVID[0]) & (fa.index <= COVID[1]))
        if kuju == "YoY":  # 2021 kevade aastamuutus võrdleb COVID-kuudega
            keep &= ~((fa.index >= COVID[0] + 12) & (fa.index <= COVID[1] + 12))
        rows.append(dict(kutus=f, liiklus=g, kuju=kuju, valim="ilma COVID-kuudeta",
                         **corr_pair(fa[keep], fb[keep])))
        series[(f, g, kuju)] = (fa, fb)
corr = pd.DataFrame(rows)
save_table(corr, "02_korrelatsioonid")
print(corr.round(3).to_string(index=False))


def scatter_panel(kuju, name, xlabel, ylabel):
    """Hajuvusdiagramm kahe paneeliga (bensiin vs kerged, diisel vs kaubikud-veokid-bussid) ühel kujul.
    kuju = "tase", "YoY" või "STL jääk" (read sõnastikust series), name = väljundfaili nimi, xlabel/ylabel = telgede
    sildid. Punkt = kuu, joon = lineaarne regressioon 95% usalduspiirkonnaga, must ring = märts-mai 2020; nurka
    kirjutatakse r, p, rho ja n tabelist corr (kõik kuud ja ilma COVID-kuudeta)."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for ax, (f, g) in zip(axes, PAIRS[:2]):
        a, b = series[(f, g, kuju)]
        m = pd.concat([a.rename("x"), b.rename("y")], axis=1).dropna()
        sns.regplot(data=m, x="x", y="y", ax=ax, color=FUEL_COLOR[f],
                    scatter_kws=dict(s=22, alpha=0.8, edgecolor="white"),
                    line_kws=dict(lw=2))
        # märgi COVID kuud
        cov = m[(m.index >= pd.Period("2020-03", "M")) & (m.index <= pd.Period("2020-05", "M"))]
        ax.scatter(cov["x"], cov["y"], s=40, facecolor="none", edgecolor="black", lw=1,
                   label="2020 märts-mai")
        c = corr[(corr.kutus == f) & (corr.liiklus == g) & (corr.kuju == kuju)].iloc[0]
        c2 = corr[(corr.kutus == f) & (corr.liiklus == g) & (corr.kuju == kuju)].iloc[1]
        ax.text(0.03, 0.95, f"r = {c.r:.2f}  (p = {c.p:.3f}), ρ = {c.rho:.2f}, n = {c.n}\nilma COVID-kuudeta: r = {c2.r:.2f}, ρ = {c2.rho:.2f}",
                transform=ax.transAxes, va="top", fontsize=9, color=TEXT2)
        ax.set_xlabel(f"{xlabel}\n{GROUP_LABEL[g]}")
        ax.set_ylabel(f"{ylabel}: {FUEL_LABEL[f].lower()}")
        ax.set_title(f"{FUEL_LABEL[f]}")
        if len(cov):
            ax.legend(loc="lower right", fontsize=8)
    save(fig, name)


scatter_panel("tase", "02_02_hajuvus_tase", f"Liiklusindeks ({BASE_YEAR}=100)",
              f"Müügiindeks ({BASE_YEAR}=100)")
scatter_panel("YoY", "02_03_hajuvus_yoy", "Liikluse aastane muutus, %", "Müügi aastane muutus, %")
scatter_panel("STL jääk", "02_04_hajuvus_stl", "Liikluse STL-jääk, %", "Müügi STL-jääk, %")

# 3) Elastsus: log(kütus) ~ log(liiklus) + kuu näivmuutujad + trend ---------------------
el_rows = []
for f, g in PAIRS:
    m = pd.DataFrame({"y": np.log(df[f]), "x": np.log(df[f"liiklus_{g}"]),
                      "kuu_nr": df.index.month.astype(str),
                      "trend": np.arange(len(df)) / 12}).dropna()
    res = smf.ols("y ~ x + C(kuu_nr) + trend", data=m).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    ci = res.conf_int().loc["x"]
    el_rows.append(dict(kutus=f, liiklus=g, elastsus=res.params["x"], ci_madal=ci[0], ci_korge=ci[1],
                        p=res.pvalues["x"], trend_aastas_pct=res.params["trend"] * 100,
                        r2=res.rsquared, n=int(res.nobs)))
el = pd.DataFrame(el_rows)
save_table(el, "02_elastsus")
print(el.round(3).to_string(index=False))

# 4) Poolkuu andmed: korrelatsioon nihkega ------------------------------------------------
bw = tabel("fuel.retail_semimonthly")
bw["pool"] = (bw["Aasta"].astype(int).astype(str) + "-" + bw["Kuu"].astype(int).astype(str).str.zfill(2)
              + "-" + bw["Aruande-periood"].map({1: "01", 2: "16"}))
start = pd.to_datetime(bw["pool"])
# Eeldus: periood 1 = 1.-15. kuupäev, periood 2 = 16.-kuu lõpp
days = np.where(bw["Aruande-periood"] == 1, 15, start.dt.days_in_month - 15)
bw["bensiin"] = (bw["Bensiin < 98"] + bw["Bensiin > 98"]) / days
bw["diisel"] = bw["Diisel"] / days
bw = bw.set_index("pool")[["bensiin", "diisel"]]

d["pool"] = d["paev"].dt.strftime("%Y-%m") + "-" + np.where(d["paev"].dt.day > 15, "16", "01")
ch = counter_month(d, min_days=7, key="pool")
hb = pd.DataFrame({g: traffic_index(ch, value=g, key="pool").set_index("pool")["indeks"]
                   for g in ["kerge", "raske"]}).join(bw, how="inner").sort_index()
pooled = pd.date_range(hb.index.min(), hb.index.max(), freq="SMS-16").strftime("%Y-%m-%d")   # kõik poolkuud (1. ja 16.)
assert set(hb.index) <= set(pooled)
hb = hb.reindex(pooled)                     # puuduv poolkuu NaN-ina: yoy(24) võrdleb siis alati sama poolkuud aasta tagasi

lags = range(-4, 5)
lag_rows = []
for f, g in PAIRS[:2]:
    # aastane muutus (24 poolkuud) eemaldab hooajalisuse
    a, b = yoy(hb[g], 24), yoy(hb[f], 24)
    for L in lags:
        c = corr_pair(a, b.shift(-L))  # L>0: kütus järgneb liiklusele L poolkuu võrra
        lag_rows.append(dict(kutus=f, liiklus=g, nihe_poolkuud=L, **c))
lag = pd.DataFrame(lag_rows)
save_table(lag, "02_viitega_korrelatsioon")

fig, ax = plt.subplots(figsize=(8, 4))
for f, g in PAIRS[:2]:
    s = lag[lag.kutus == f]
    ax.plot(s["nihe_poolkuud"], s["r"], marker="o", ms=6, color=FUEL_COLOR[f],
            label=f"{FUEL_LABEL[f]} vs {GROUP_LABEL[g].lower()}")
ax.axvline(0, color=TEXT2, lw=0.6, ls=":")
ax.axhline(0, color=TEXT2, lw=0.6)
ax.set_xlabel("Nihe, poolkuud (positiivne = müük järgneb liiklusele)")
ax.set_ylabel("Pearson r (aastased muutused)")
ax.set_title("Liikluse ja kütusemüügi korrelatsioon nihkega (poolkuu andmed, 2021-2026)")
ax.legend(fontsize=9, loc="upper right")
save(fig, "02_05_viitega_korrelatsioon")
print("Valmis.")
