"""
04 - Tee ja üksiku loenduri tasemel seosed: kui hästi esindavad loendurid tee koormust ja kui hästi järgib üksiku
loenduri liiklus oma maakonna kütusemüüki.

SISEND
  common.load_daily(), counter_month(), clean()     kehtivad loendur-kuud ilma kahtlaste kuudeta
  common.load_locations()                           loenduri tee, maakond ja koordinaadid
  import_raw.labisoit                               põhimaanteede aastane läbisõit, mln sõidukikilomeetrit
  common.load_fuel_county(), load_fuel_national()   kütusemüük maakonniti ja riigis kokku, liitrit päevas
  common.add_basemap()                              kaardi satelliit-/ortofototaust (internetita joonistatakse ilma)

ARVUTUS
  a) Läbisõit vs loendurite liiklus. Loenduri aasta keskmine ööpäevane liiklus = kuude keskmine; arvesse lähevad
     loendur-aastad, kus kehtivaid kuid on >= 10. Tee aasta väärtus = tee loendurite keskmine. Arvutuslik tee pikkus =
     läbisõit / (ööpäevane liiklus x 365): kui loendurid asuvad tee koormatumates kohtades (linnade lähedal), tuleb
     see tegelikust lühem.
  b) Aastased muutused. Iga tee ja aasta kohta võetakse ainult loendurid, mis on olemas ka eelmisel aastal, ja
     leitakse muutus ln(summa / eelmise aasta summa) x 100; läbisõidu muutus samal kujul.
  c) Iga loendur vs oma maakonna kütus. Loenduritel, millel on >= 36 kehtivat kuud, leitakse aastaste muutuste
     korrelatsioon: kerged sõidukid vs maakonna bensiinimüük ja kaubikud-veokid-bussid vs diislimüük.
  d) Riigi aastane läbisõit vs aastane kütusemüük (ainult täielikud aastad): liitrit 100 sõidukikilomeetri kohta.
     Kirjeldav, sest aastaid on vähe.

VÄLJUND (kaust valjund/)
  04_labisoit_vs_adt.png
      Näitab: kas suurema loendatud liiklusega teel on ka suurem läbisõit (2023).
      Kuidas: mullidiagramm; punkt = põhimaantee (silt T + tee number), x-telg = tee loendurite keskmine ööpäevane
      liiklus, y-telg = läbisõit, mln sõidukikm; mulli suurus = loendurite arv. Nurgas r, rho ja teede arv.
  04_labisoit_muutus.png
      Näitab: kas loendurite liikluse aastane muutus langeb kokku ametliku läbisõidu muutusega.
      Kuidas: hajuvusdiagramm; punkt = tee-aasta, x-telg = samade loendurite liikluse muutus, %, y-telg = läbisõidu
      muutus, %; joon = lineaarne regressioon usalduspiirkonnaga, nulljooned; nurgas r, p, rho, n.
  04_loendur_r_tee.png
      Näitab: kui erinevalt järgivad sama tee loendurid maakonna kütusemüüki.
      Kuidas: karpdiagramm punktidega; x-telg = tee number (teed, millel on >= 3 loendurit, järjestatud bensiini
      mediaani järgi), y-telg = aastaste muutuste Pearsoni r. Punkt = loendur; sinine = bensiin vs kerged, oranž =
      diisel vs kaubikud-veokid-bussid.
  04_loendur_r_kaart.png
      Näitab: kus Eestis on loenduri liiklus oma maakonna kütusemüügiga tugevalt seotud.
      Kuidas: kaks kaarti (bensiin, diisel) ortofototaustal. Ring = loendur; värv = r (sinine -1 ... punane +1),
      suurus = ööpäevane liiklus.
  04_labisoit_vs_adt.csv         tee-aasta: loendurite liiklus, läbisõit, arvutuslik pikkus
  04_labisoit_muutus.csv         tee-aasta muutused (b)
  04_loendur_korrelatsioon.csv   iga loenduri r, rho, p, n (c)
  04_aastane_riik.csv            riigi aastane läbisõit, müük ja liitrit 100 sõidukikm kohta (d)
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from common import (load_daily, load_locations, counter_month, clean, load_fuel_county,
                    load_fuel_national, set_style, save, save_table, yoy, corr_pair,
                    FUEL_COLOR, FUEL_LABEL, GROUP_LABEL, C_BLUE, C_ORANGE, C_GRAY, TEXT2,
                    DIVERGING, tabel, add_basemap, to_merc)

set_style()
print("Laen andmeid...")
d = load_daily()
loc = load_locations()
cm = counter_month(d).merge(loc[["id", "nimi", "maakond_full", "tee_nr", "tee_nimi",
                                 "latitude", "longitude"]], on="id")
cm_ok = clean(cm, klass=False)

# --- a) Läbisõit vs loendurite ADT ----------------------------------------------------------
lab = tabel("import_raw.labisoit")
lab = lab[lab["Tee Nr"] != "sum"].copy()
lab["tee_nr"] = lab["Tee Nr"].astype(int)
lab = lab.melt(id_vars=["Tee liik", "Tee Nr", "tee_nr"], var_name="aasta", value_name="mln_skm")
lab["aasta"] = lab["aasta"].astype(int)

# loenduri aasta-ADT: ainult loendur-aastad, kus >= 10 kehtivat kuud
cy = (cm_ok.groupby(["id", "tee_nr", "aasta"])
      .agg(kuid=("kuu", "nunique"), adt=("kokku", "mean")).reset_index())
cy = cy[cy["kuid"] >= 10]
road_y = (cy.groupby(["tee_nr", "aasta"])
          .agg(adt=("adt", "mean"), loendureid=("id", "nunique")).reset_index())
ry = road_y.merge(lab, on=["tee_nr", "aasta"])
# arvutuslik pikkus: läbisõit / (ADT * 365). Kui loendurid asuvad tee koormatumates
# kohtades (linnade lähedal), tuleb pikkus tegelikust lühem.
ry["arvutuslik_pikkus_km"] = ry["mln_skm"] * 1e6 / (ry["adt"] * 365)
save_table(ry, "04_labisoit_vs_adt")

ref = ry[ry["aasta"] == 2023]
fig, ax = plt.subplots(figsize=(7.5, 5.5))
ax.scatter(ref["adt"], ref["mln_skm"], s=ref["loendureid"] * 25 + 20, color=C_BLUE,
           alpha=0.85, edgecolor="white", linewidth=1.5)
for _, r in ref.iterrows():
    ax.annotate(f"T{int(r.tee_nr)}", (r.adt, r.mln_skm), xytext=(6, 4),
                textcoords="offset points", fontsize=9, color=TEXT2)
c = corr_pair(ref["adt"], ref["mln_skm"])
ax.text(0.03, 0.96, f"r = {c['r']:.2f}, ρ = {c['rho']:.2f}, n = {c['n']} teed",
        transform=ax.transAxes, va="top", fontsize=9, color=TEXT2)
ax.set_xlabel("Tee loendurite keskmine ööpäevane liiklus 2023, sõidukit/ööp")
ax.set_ylabel("Läbisõit 2023, mln sõidukikm")
ax.set_title("Põhimaanteede läbisõit vs loendurite liiklus (mulli suurus = loendurite arv)")
save(fig, "04_labisoit_vs_adt")

# --- b) Aastased muutused: fikseeritud loendurite komplekt kahe aasta vahel -------------------
rows = []
for (tee, y), g in cy.groupby(["tee_nr", "aasta"]):
    prev = cy[(cy["tee_nr"] == tee) & (cy["aasta"] == y - 1)]
    both = g.merge(prev, on="id", suffixes=("", "_eelm"))
    if len(both):
        rows.append(dict(tee_nr=tee, aasta=y, loendureid=len(both),
                         adt_muutus=np.log(both["adt"].sum() / both["adt_eelm"].sum()) * 100))
ch = pd.DataFrame(rows)
labw = lab.pivot(index="tee_nr", columns="aasta", values="mln_skm")
lab_ch = (np.log(labw).diff(axis=1) * 100).stack().rename("labisoit_muutus").reset_index()
ch = ch.merge(lab_ch, on=["tee_nr", "aasta"]).dropna()
save_table(ch, "04_labisoit_muutus")

fig, ax = plt.subplots(figsize=(7.5, 5.5))
sns.regplot(data=ch, x="adt_muutus", y="labisoit_muutus", ax=ax, color=C_BLUE,
            scatter_kws=dict(s=30, alpha=0.8, edgecolor="white"))
c = corr_pair(ch["adt_muutus"], ch["labisoit_muutus"])
ax.text(0.03, 0.96, f"r = {c['r']:.2f} (p = {c['p']:.3f}), ρ = {c['rho']:.2f}, n = {c['n']} tee-aastat",
        transform=ax.transAxes, va="top", fontsize=9, color=TEXT2)
ax.axhline(0, color=TEXT2, lw=0.6)
ax.axvline(0, color=TEXT2, lw=0.6)
ax.set_xlabel("Loendurite liikluse aastane muutus, % (samad loendurid)")
ax.set_ylabel("Läbisõidu aastane muutus, %")
ax.set_title("Põhimaanteed: läbisõidu ja loendatud liikluse aastased muutused")
save(fig, "04_labisoit_muutus")

# --- c) Iga loendur vs oma maakonna kütus ----------------------------------------------------
fuel = load_fuel_county()
cmk = clean(cm, klass=True).merge(fuel, on=["kuu", "maakond_full"])
rows = []
for cid, g in cmk.groupby("id"):
    s = g.set_index("kuu").sort_index()
    s = s.reindex(pd.period_range(s.index.min(), s.index.max(), freq="M"))
    if s["kokku"].notna().sum() < 36:
        continue
    info = g.iloc[0]
    for f, grp in [("bensiin", "kerge"), ("diisel", "raske")]:
        c = corr_pair(yoy(s[grp]), yoy(s[f]))
        rows.append(dict(id=cid, nimi=info["nimi"], maakond=info["maakond_full"],
                         tee_nr=info["tee_nr"], tee_nimi=info["tee_nimi"],
                         lat=info["latitude"], lon=info["longitude"],
                         kuid=int(s["kokku"].notna().sum()), adt=s["kokku"].mean(),
                         kutus=f, liiklus=grp, **c))
pc = pd.DataFrame(rows).dropna(subset=["r"])
save_table(pc.sort_values(["kutus", "r"], ascending=[True, False]), "04_loendur_korrelatsioon")

# tee kaupa (teed, millel >= 3 loendurit)
roads = pc.groupby("tee_nr")["id"].nunique()
roads = roads[roads >= 3].index
sub = pc[pc["tee_nr"].isin(roads)].copy()
order = sub[sub.kutus == "bensiin"].groupby("tee_nr")["r"].median().sort_values(ascending=False).index
sub["tee"] = pd.Categorical("T" + sub["tee_nr"].astype(str), ["T" + str(t) for t in order])
fig, ax = plt.subplots(figsize=(10, 5))
sns.boxplot(data=sub, x="tee", y="r", hue="kutus", ax=ax, palette=FUEL_COLOR, fliersize=0,
            boxprops=dict(alpha=0.35), linewidth=1)
sns.stripplot(data=sub, x="tee", y="r", hue="kutus", ax=ax, palette=FUEL_COLOR, dodge=True,
              size=5, edgecolor="white", linewidth=0.5, legend=False)
ax.axhline(0, color=TEXT2, lw=0.6)
h, l = ax.get_legend_handles_labels()
ax.legend(h[:2], [FUEL_LABEL[x] for x in l[:2]], loc="lower left", fontsize=9)
ax.set_xlabel("Tee number (≥3 loendurit)")
ax.set_ylabel("Pearson r (aastased muutused)")
ax.set_title("Üksiku loenduri liiklus vs oma maakonna kütusemüük, tee kaupa")
save(fig, "04_loendur_r_tee")

lo0, lo1, la0, la1 = pc["lon"].min(), pc["lon"].max(), pc["lat"].min(), pc["lat"].max()
ext = (lo0 - 0.04 * (lo1 - lo0), la0 - 0.10 * (la1 - la0), lo1 + 0.04 * (lo1 - lo0), la1 + 0.05 * (la1 - la0))
fig, axes = plt.subplots(1, 2, figsize=(13, 5.0), layout="constrained")
for ax, f in zip(axes, ["bensiin", "diisel"]):
    s = pc[pc.kutus == f]
    att = add_basemap(ax, *ext)
    mx, my = to_merc(s["lon"].values, s["lat"].values)
    sc = ax.scatter(mx, my, c=s["r"], cmap=DIVERGING, vmin=-1, vmax=1,
                    s=np.clip(s["adt"] / 300, 12, 160), edgecolor="black", linewidth=0.5, zorder=5)
    ax.set_title(f"{FUEL_LABEL[f]} vs {GROUP_LABEL['kerge' if f == 'bensiin' else 'raske'].lower()}")
fig.colorbar(sc, ax=axes, shrink=0.8, label="Pearson r (aastased muutused)")
print("Kaardi taust:", att or "puudub (plaaditeenus ei vastanud - joonistati ilma taustata)")
fig.suptitle("Loendurite korrelatsioon oma maakonna kütusemüügiga (mulli suurus = liiklusmaht)",
             x=0.01, ha="left", fontweight="bold")
fig.get_layout_engine().set(h_pad=0.1)
save(fig, "04_loendur_r_kaart")

# --- d) Riigi aastane läbisõit vs kütusemüük ---------------------------------------------------
labs = tabel("import_raw.labisoit")
tot = labs.drop(columns=["Tee liik", "Tee Nr"]).sum()
tot.index = tot.index.astype(int)
fn = load_fuel_national()
fn["aasta"] = fn["kuu"].dt.year
fn["liitrit"] = (fn["bensiin"] + fn["diisel"]) * fn["kuu"].dt.days_in_month
fy = fn.groupby("aasta").agg(kuid=("kuu", "nunique"), liitrit=("liitrit", "sum"))
fy = fy[fy["kuid"] == 12]
ann = pd.DataFrame({"riigiteede_labisoit_mln_skm": tot}).join(fy, how="inner")
ann["liitrit_100_skm_kohta"] = ann["liitrit"] / (ann["riigiteede_labisoit_mln_skm"] * 1e6) * 100
save_table(ann.reset_index(names="aasta"), "04_aastane_riik")
print(ann.round(2))
print("\nTee kaupa arvutuslik pikkus (2023):")
print(ref[["tee_nr", "loendureid", "adt", "mln_skm", "arvutuslik_pikkus_km"]].round(1).to_string(index=False))
print("\nLoendurite r mediaan:")
print(pc.groupby("kutus")["r"].describe().round(2))
