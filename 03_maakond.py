"""
03 - Maakonna tasemel seos: maakonna loendurite liiklusindeks ja maakonnas müüdud kütus.

NB! Kütus on arvel seal, kus see müüakse, mitte seal, kus see ära põletatakse. Transiitmaakondades (nt Tallinna-Tartu
maantee ääres) võib seos olla nõrgem - see on tulemus omaette, mitte viga.

SISEND
  common.load_daily(), counter_month()   kehtivad loendur-kuud (maanteeloendurite tunniloendustest)
  common.load_locations()                loenduri maakond (traffic.counter_location)
  common.load_fuel_county()              bensiini ja diislikütuse müük maakonniti, liitrit päevas
                                         (import_raw.bensiin_maakond_monthly, import_raw.diisel_maakond_monthly)

ARVUTUS
  Liiklusindeks maakonniti (common.traffic_index, 2023 = 100): nagu skriptis 02, aga iga maakonna loenduritest eraldi;
    maakond läheb arvesse ka ühe loenduriga. Rühmad: kõik sõidukid, kerged (kl 1-3), kaubikud-veokid-bussid (kl 4-10).
  Müügiindeks: maakonna liitrit päevas jagatud sama maakonna 2023. a keskmisega, x 100.
  Korrelatsioonid iga maakonna kohta paaridele bensiin-kerged ja diisel-kaubikud/veokid/bussid kolmel kujul (tase,
    aastane muutus YoY, STL jääk; vt 02). STL jääk ainult siis, kui liiklusrida on üle 30 kuu pikk.
  Paneelregressioon (kõik maakonnad koos): ln(müük) = e x ln(liiklus) + fikseeritud efektid.
    Mudel A: maakonna efekt + kalendrikuu efekt + iga maakonna oma trend.
    Mudel B: maakonna efekt + aasta-kuu efekt (kahesuunaline) - eemaldab kõik üleriigilised šokid (hinnad, COVID),
             seos tuleb ainult maakondade erinevast käitumisest.
    Standardvead on klasterdatud maakonna järgi. Paarid: bensiin-kerged, diisel-kaubikud/veokid/bussid, kokku-kokku.

VÄLJUND (kaust valjund/)
  03_01_korrelatsioon_heatmap.png
      Näitab: kui tugev on seos igas maakonnas ja kas see püsib pärast hooajalisuse eemaldamist.
      Kuidas: soojuskaart; rida = maakond (sulgudes loendurite arv, järjestatud loendurite arvu järgi), veerg = kütus x
      kuju (Bensiin / Diisel x tase, YoY, STL jääk). Ruudus on Pearsoni r; värv sinisest (-1) läbi heleda (0)
      punaseni (+1).
  03_02_hajuvus_yoy_bensiin.png, 03_03_hajuvus_yoy_diisel.png
      Näitab: aastaste muutuste seost maakondade kaupa.
      Kuidas: väikesed hajuvusdiagrammid, üks paneel maakonna kohta (5 reas). Punkt = kuu; x-telg = liikluse aastane
      muutus, %, y-telg = müügi aastane muutus, %; joon = lineaarne regressioon usalduspiirkonnaga; nurgas r. Telgede
      ulatus on igal paneelil oma.
  03_04_aegread_maakonnad.png
      Näitab: liikluse ja kogu kütusemüügi käiku igas maakonnas.
      Kuidas: joondiagrammide ruudustik (5 x 3), paneel maakonna kohta (pealkirjas loendurite arv). Hall =
      liiklusindeks (kõik sõidukid), oranž = bensiini ja diisli müük kokku; mõlemad 2023 = 100 (punktiir).
  03_kuuandmed.csv           maakonna kuuindeksid ja müük
  03_korrelatsioonid.csv     r, rho, p ja n iga maakonna, paari ja kuju kohta
  03_paneelregressioon.csv   elastsus e, 95% usaldusvahemik, p, R2, n ja maakondade arv mudelite A ja B kohta
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.formula.api as smf

from common import (load_daily, load_locations, counter_month, traffic_index, load_fuel_county,
                    set_style, save, save_table, yoy, stl_resid, corr_pair, month_axis,
                    FUEL_COLOR, FUEL_LABEL, GROUP_LABEL, C_GRAY, TEXT2, DIVERGING, BASE_YEAR)

set_style()
print("Laen andmeid...")
d = load_daily()
loc = load_locations()
cm = counter_month(d).merge(loc[["id", "maakond_full"]], on="id")

PAIRS = [("bensiin", "kerge"), ("diisel", "raske")]
ti = None
for g in ["kokku", "kerge", "raske"]:
    t = traffic_index(cm, value=g, by="maakond_full", min_counters=1).rename(
        columns={"indeks": f"liiklus_{g}", "loendureid": f"loendureid_{g}"})
    ti = t if ti is None else ti.merge(t, on=["kuu", "maakond_full"], how="outer")

fuel = load_fuel_county()
df = ti.merge(fuel, on=["kuu", "maakond_full"], how="inner").sort_values(["maakond_full", "kuu"])
# kütuse indeks (2023 = 100) iga maakonna jaoks
for f in ["bensiin", "diisel"]:
    base = df[df["kuu"].dt.year == BASE_YEAR].groupby("maakond_full")[f].mean()
    df[f"{f}_idx"] = df[f] / df["maakond_full"].map(base) * 100
save_table(df, "03_kuuandmed")

n_counters = cm.groupby("maakond_full")["id"].nunique().sort_values(ascending=False)
counties = list(n_counters.index)

# 1) Korrelatsioonid maakonniti ------------------------------------------------------
rows = []
for mk, g_df in df.groupby("maakond_full"):
    s = g_df.set_index("kuu")
    for f, g in PAIRS:
        a, b = s[f"liiklus_{g}"], s[f]
        for kuju, fa, fb in [("tase", a, b), ("YoY", yoy(a), yoy(b)),
                             ("STL jääk", stl_resid(a) if a.notna().sum() > 30 else a * np.nan,
                              stl_resid(b))]:
            rows.append(dict(maakond=mk, loendureid=n_counters.get(mk, 0), kutus=f, liiklus=g,
                             kuju=kuju, **corr_pair(fa, fb)))
corr = pd.DataFrame(rows)
save_table(corr, "03_korrelatsioonid")

hm = corr.assign(veerg=corr["kutus"].map(FUEL_LABEL) + "\n" + corr["kuju"]).pivot(
    index="maakond", columns="veerg", values="r")
col_order = [f"{FUEL_LABEL[f]}\n{k}" for f, _ in PAIRS for k in ["tase", "YoY", "STL jääk"]]
hm = hm.loc[counties, col_order]
hm.index = [f"{m} ({n_counters[m]})" for m in hm.index]

fig, ax = plt.subplots(figsize=(8, 8))
sns.heatmap(hm, annot=True, fmt=".2f", cmap=DIVERGING, vmin=-1, vmax=1, center=0,
            linewidths=2, linecolor="white", cbar_kws=dict(label="Pearson r", shrink=0.6),
            annot_kws=dict(fontsize=9), ax=ax)
ax.set_xlabel("")
ax.set_ylabel("Maakond (loendurite arv)")
ax.set_title("Liikluse ja kütusemüügi korrelatsioon maakonniti")
ax.tick_params(axis="x", rotation=0)
save(fig, "03_01_korrelatsioon_heatmap")

# 2) Väikesed mitmikud: aastased muutused -------------------------------------------------
for nr, (f, g) in enumerate(PAIRS, 2):          # joonised 03_02 (bensiin) ja 03_03 (diisel)
    y = []
    for mk, g_df in df.groupby("maakond_full"):
        s = g_df.set_index("kuu")
        y.append(pd.DataFrame({"maakond": mk, "x": yoy(s[f"liiklus_{g}"]), "y": yoy(s[f])}))
    y = pd.concat(y).dropna()
    y["maakond"] = pd.Categorical(y["maakond"], counties)
    grid = sns.lmplot(data=y, x="x", y="y", col="maakond", col_wrap=5, height=2.3,
                      scatter_kws=dict(s=10, alpha=0.7, color=FUEL_COLOR[f]),
                      line_kws=dict(color=FUEL_COLOR[f], lw=1.8),
                      facet_kws=dict(sharex=False, sharey=False))
    for ax, mk in zip(grid.axes.flat, counties):
        c = corr[(corr.maakond == mk) & (corr.kutus == f) & (corr.kuju == "YoY")]
        if len(c):
            ax.text(0.04, 0.94, f"r = {c.r.iloc[0]:.2f}", transform=ax.transAxes,
                    va="top", fontsize=8, color=TEXT2)
        ax.set_title(mk, fontsize=9, loc="left")
    grid.set_axis_labels("", "")
    grid.figure.supxlabel(f"Liikluse aastane muutus, % ({GROUP_LABEL[g].lower()})", color=TEXT2)
    grid.figure.supylabel(f"{FUEL_LABEL[f]} müügi aastane muutus, %", color=TEXT2)
    grid.figure.suptitle(f"{FUEL_LABEL[f]} vs {GROUP_LABEL[g].lower()}: aastased muutused maakonniti",
                         x=0.01, ha="left", y=1.03, fontweight="bold")
    save(grid.figure, f"03_{nr:02d}_hajuvus_yoy_{f}")

# 3) Aegread maakonniti (kõik sõidukid vs kogu kütus) ------------------------------------------
df["kutus_kokku_idx"] = (df["bensiin"] + df["diisel"]) / df["maakond_full"].map(
    df[df["kuu"].dt.year == BASE_YEAR].groupby("maakond_full").apply(
        lambda x: (x["bensiin"] + x["diisel"]).mean())) * 100
fig, axes = plt.subplots(5, 3, figsize=(12, 13), sharex=True)
for ax, mk in zip(axes.flat, counties):
    s = df[df["maakond_full"] == mk]
    t = s["kuu"].dt.to_timestamp()
    ax.plot(t, s["liiklus_kokku"], color=C_GRAY, lw=1.5, label="Liiklusindeks (kõik sõidukid)")
    ax.plot(t, s["kutus_kokku_idx"], color=FUEL_COLOR["diisel"], lw=1.5, label="Kütusemüük kokku")
    ax.set_title(f"{mk} ({n_counters[mk]})", fontsize=10)
    ax.axhline(100, color=TEXT2, lw=0.5, ls=":")
    month_axis(ax)
    ax.tick_params(labelsize=8)
handles, labels = axes.flat[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper left", ncol=2, bbox_to_anchor=(0.01, 1.0))
fig.suptitle(f"Liiklusindeks ja kütusemüük maakonniti ({BASE_YEAR} = 100)", x=0.01, y=1.02,
             ha="left", fontweight="bold")
fig.tight_layout()
save(fig, "03_04_aegread_maakonnad")

# 4) Paneelregressioon ---------------------------------------------------------------------------
# log(kütus) ~ log(liiklus) + maakonna FE + kalendrikuu FE [+ aasta-kuu FE]
# Mudel B (kahesuunaline FE) eemaldab kõik üleriigilised šokid (hinnad, COVID) ->
# seos tuleneb ainult maakondade erinevast käitumisest. Standardvead klasterdatud maakonna järgi.
reg_rows = []
for f, g in PAIRS + [("kokku", "kokku")]:
    y = np.log(df[f] if f != "kokku" else df["bensiin"] + df["diisel"])
    m = pd.DataFrame({"y": y, "x": np.log(df[f"liiklus_{g}"]), "mk": df["maakond_full"],
                      "kalkuu": df["kuu"].dt.month.astype(str), "ym": df["kuu"].astype(str),
                      "trend": (df["kuu"].dt.year - BASE_YEAR) + df["kuu"].dt.month / 12}).dropna()
    for nimi, formula in [("A: maakond + kalendrikuu FE + maakonna trend",
                           "y ~ x + C(mk) + C(kalkuu) + C(mk):trend"),
                          ("B: maakond + aasta-kuu FE (kahesuunaline)", "y ~ x + C(mk) + C(ym)")]:
        res = smf.ols(formula, data=m).fit(cov_type="cluster", cov_kwds={"groups": m["mk"]})
        ci = res.conf_int().loc["x"]
        reg_rows.append(dict(kutus=f, liiklus=g, mudel=nimi, elastsus=res.params["x"],
                             ci_madal=ci[0], ci_korge=ci[1], p=res.pvalues["x"],
                             r2=res.rsquared, n=int(res.nobs), maakondi=m["mk"].nunique()))
reg = pd.DataFrame(reg_rows)
save_table(reg, "03_paneelregressioon")
print(reg.round(3).to_string(index=False))
print(corr[corr.kuju == "YoY"].pivot(index="maakond", columns="kutus", values="r").round(2))
