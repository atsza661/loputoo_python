"""
11 - Arvukontrollid enne tulemuste avaldamist: kas sõidukipõhised andmed on terviklikud ja usutavad ning kui kindlad on
skriptide 06, 09 ja 10 tulemused. Tulemused trükitakse ekraanile, tabelitesse ja nelja joonisele (vt JOONISED).
Käivita pärast 06 (ka LSS/LVS), 09 ja 10; uuesti siis, kui nädala kirjed on andmebaasi laetud.

SISEND
  common.load_vehicles(None)   sõidukipõhised kirjed (ainult ristmiku terved päevad: kõik pordid
                                          kaetud 05-23, common.tervetel_paevadel)
  common.load_tallinn()                   ristmike 15 min loendused (tavalise tööpäeva võrdluseks)
  valjund/09_tsuklid.csv, 09_ummikud.csv, 09_ummiku_umber.csv; valjund/LSS ja valjund/LVS/06_tipptunnid.csv

KONTROLLID: ARVUTUS JA VÄLJUND (joonised kaustas Graafikud/, tabelid kaustas valjund/)
  1) Terviklikkus: iga loendur nummerdab sõidukid (life). Vahele jäänud numbrid = kaotsi läinud read (salvestamisel või
     edastamisel). Korduva numbriga read (mitte-sõidukid) ja kiiruse koodi 255 eemaldab common.load_vehicles - siin
     näidatakse, kui palju.                                                   -> 11_terviklikkus.csv
  2) Kas sõidukipõhine päev on tavaline? Ristmiku ööpäeva summa ja 15 min profiil võrreldes 2026. a tavalise
     õppetöö-aegse tööpäevaga: summade suhe ja profiilide korrelatsioon.     -> 11_paeva_tavalisus.csv
  3) Usutavus: kiirus 0 või üle 120 km/h, pikkus 0 või üle 25 m (% ristmiku sõidukitest).  -> 11_usutavus.csv
  4) Künnise tundlikkus: kui palju nihkub ummiku algus ja lahenemine, kui ummiku lävi on 80% või 90% täistasemest
     (mitte 85% nagu 09). Kindla tsükliga stabiilsed
     ummikud; silumine ja ummik nagu 09 lõigu (09_tsuklid veerg loik) sees.  -> 11_tundlikkus.csv
  5) Olulisus: LSS ja LVS tipu alguse erinevus samal ristmikul (Wilcoxoni märgiastaktest) ning ummiku ümber kiiruse
     võidu mediaani 95% usaldusvahemik (bootstrap, common.mediaani_uv).       -> 11_olulisus.csv
  6) Ühe päeva jaotuste püsivus (vajab >= 2 tervet tööpäeva): 5 min osakaalude ja LSS/LVS osakaalu standardhälve
     päevade vahel, protsendipunkti.                                           -> 11_pysivus.csv

JOONISED (kaustas Graafikud/)
  11_01_terviklikkus.png      kaks soojuskaarti, rida = ristmik, veerg = logija nädala päev. Vasakul kaotsi läinud kirjete
                              osakaal, % (1); paremal päeva summa / 2026. a tavaline õppetöö tööpäev (2; sinine = vähem,
                              punane = rohkem, valge = 1). Näitab, kas mõni ristmik-päev on puudulik või ebatavaline.
  11_02_usutavus.png          punkt ristmiku ja näitaja kohta (3): kiirus 0, kiirus üle 120 km/h, pikkus 0, pikkus üle
                              25 m, % ristmiku sõidukitest. Näitab, kus loendur annab ebausutavaid väärtusi.
  11_03_tundlikkus.png        vasakul stabiilse ummiku kestuse mediaan läve 80%, 85% (09) ja 90% korral; paremal alguse
                              ja lahenemise nihke mediaan võrreldes 85%-ga, all ummikute osakaal, mille algus nihkub üle
                              15 min (4). Näitab, kui palju sõltuvad ummiku kellaajad lävest.
  11_04_olulisus_pysivus.png  mediaan (punkt) ja 95% usaldusvahemik (vurrud) iga võrdluse kohta (5): LVS - LSS tipu algus
                              ja kiiruse võit ummiku ümber (sinine = foor, oranž = vaba vool), sildis Wilcoxoni p ja n;
                              paremal päevadevaheline hajuvus (6), mediaan ja 90. protsentiil.
  11_04b_suunad.png          11_04 suunavõrdlus eraldi: LVS - LSS tipu algus hommikul ja õhtul, 95% usaldusvahemik.
  11_05_baasprognoos.png      tulp ristmiku kohta (7): logija nädala tööpäevade keskmine (sinine) ja Transpordiameti
                              baasprognoosi linna piiri ristlõige 2020. a 10. nädala tööpäevadel (hall), sildis suhe.
                              Näitab, kas ristmiku loendus on ühe tee ristlõikega sama suurusjärku.                -> 11_baasprognoos.csv

CALCULATION IN PLAIN ENGLISH
  Only complete junction-days (every port of the junction recorded 05-23).
  1) Completeness: every detector numbers its vehicles; lost rows = missing numbers in the sequence; share = lost /
     (kept + lost) x 100. Also how many repeated-number rows and speed-code-255 rows load_vehicles removed.
  2) Typical day? Junction's daily total on each logger-week day / its typical 2026 school-workday total, and the
     correlation of the two 15-minute profiles.
  3) Plausibility: % of the junction's vehicles with speed 0 or above 120 km/h, length 0 or above 25 m.
  4) Threshold sensitivity: congestion start and end found again with 80% and 90% instead of 85% of full level; shift
     in minutes. Smoothing and congestion stay inside one recording stretch of 09 (column loik).
  5) Significance: Wilcoxon signed-rank test of inbound vs outbound peak start at the same junction; 95% bootstrap
     interval of the median speed gain around congestion (rows resampled independently, so repeated observations of a
     place make the interval rather too narrow).
  6) Stability: standard deviation over days of the 5-minute shares and of the inbound/outbound share (percentage
     points).
  Figures: 11_01 heat maps of lost-row % and day total / typical workday by junction and day; 11_02 implausible-value
  shares per junction; 11_03 congestion duration and start/end shift by threshold; 11_04 medians with 95% intervals and
  day-to-day spread.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from common import (tervetel_paevadel, load_vehicles, load_tallinn, five_min_shares, direction_share, ummiku_loik, ummikumask, save_table,
                    X_LAHEDAL, OUT_DIR, PUHASTUS, KAETUS, mediaani_uv, set_style, save, DIVERGING, C_BLUE, C_ORANGE,
                    C_AQUA, C_YELLOW, C_GRAY, TEXT2)

TIPUD = {"hommik": (6, 11), "õhtu": (14, 20)}
loe = lambda nimi, **kw: pd.read_csv(OUT_DIR / f"{nimi}.csv", encoding="utf-8-sig", **kw)
mp_nimi = lambda s: "MP" + s.astype(str).str.zfill(2)


assert (lambda u: u[0] <= 5 <= u[1])(mediaani_uv(np.arange(11)))

v = load_vehicles(None)
n0 = len(v)
v = tervetel_paevadel(v).copy()                     # ainult ristmiku terved päevad (kõik pordid kaetud 05-23)
v["paev"] = v["ts"].dt.normalize()
paevad = sorted(v["paev"].unique())
print(f"Terveid ristmiku päevi {v.groupby(['mp_id', 'paev']).ngroups}, päevi {len(paevad)} "
      f"({', '.join(pd.Timestamp(p).strftime('%d.%m %a') for p in paevad)}); osalise kaetusega ristmiku päevad välja "
      f"({(n0 - len(v)) / n0 * 100:.1f}% kirjetest)")
print("Harva elumärke saatvad pordid (vaikust ei saa kontrollida; % ristmiku sõidukitest): "
      + (", ".join(f"MP{r.mp_id:02d} port {r.port} {r.osa_ristmikust * 100:.2f}%" for r in KAETUS["kontrollimata"].itertuples())
         or "-")
      + f"; teadmata kaetusega ristmikud (välja): {', '.join(f'MP{m:02d}' for m in KAETUS['teadmata']) or '-'}")

# --- 1) Terviklikkus loenduri järjekorranumbri järgi ---------------------------------------------------
v = v.sort_values(["mp_id", "kanal", "life"])
d = v.groupby(["mp_id", "kanal", "paev"])["life"].diff()
v["puudu"] = d.where((d > 1) & (d < 10000), 1) - 1                      # loenduri nullimist ei loeta
terv = v.groupby(["paev", "mp_id"]).agg(soidukeid=("life", "size"), puudu=("puudu", "sum")).reset_index()
terv["puudu_%"] = terv["puudu"] / (terv["soidukeid"] + terv["puudu"]) * 100
puh = PUHASTUS
save_table(terv.assign(mp=mp_nimi(terv["mp_id"]), paev=terv["paev"].dt.date).drop(columns="mp_id").round(3), "11_terviklikkus")
print(f"\n1) Terviklikkus: puudu {terv['puudu'].sum():.0f} sõidukit ({terv['puudu'].sum() / (terv['soidukeid'].sum() + terv['puudu'].sum()) * 100:.2f}%), "
      f"laadimisel eemaldati {puh['korduv_number']} korduva numbriga rida ({puh['korduv_number'] / puh['ridu'] * 100:.2f}%), "
      f"{puh['kiirus_255']} sõidukil loeti kiirus mõõtmata (kood 255). Suurim puudujääk: "
      + "; ".join(f"MP{r['mp_id']:02d} {r['paev']:%d.%m} {r['puudu_%']:.1f}%" for _, r in terv.nlargest(4, "puudu_%").iterrows()))

# --- 2) Kas päev on tavaline? ---------------------------------------------------------------------------
t, day = load_tallinn()
tav = (t["paevatyyp"] == "tööpäev") & (t["vaheaeg"] == "kool") & (t["paev"] >= "2026-01-01")
tav_prof = t[tav].groupby(["mp_id", "slot"])["v"].mean()
dt = day[day["kehtiv"] & (day["paevatyyp"] == "tööpäev") & (day["vaheaeg"] == "kool") & (day["paev"] >= "2026-01-01")]
tav_summa = dt.groupby("mp_id")["summa"].median()
vs = v.assign(slot=v["ts"].dt.hour * 4 + v["ts"].dt.minute // 15).groupby(["paev", "mp_id", "slot"]).size()
rows = []
for (paev, mp), g in vs.groupby(level=[0, 1]):
    if mp in tav_summa.index:
        prof = g.droplevel([0, 1]).reindex(range(96), fill_value=0)
        rows.append(dict(paev=paev, mp_id=mp, soidukeid=g.sum(), tavaline_toopaev=tav_summa[mp],
                         suhe=g.sum() / tav_summa[mp], profiili_r=prof.corr(tav_prof[mp].reindex(range(96)))))
tavalisus = pd.DataFrame(rows)
save_table(tavalisus.assign(mp=mp_nimi(tavalisus["mp_id"]), paev=tavalisus["paev"].dt.date).drop(columns="mp_id").round(3),
           "11_paeva_tavalisus")
for paev, g in tavalisus.groupby("paev"):
    print(f"{'2) Tavalisus:' if paev == paevad[0] else '             '} {paev:%d.%m %a} ristmiku summa / tavaline tööpäev: mediaan "
          f"{g['suhe'].median():.2f} (kvartiilid {g['suhe'].quantile(.25):.2f}–{g['suhe'].quantile(.75):.2f}); profiili r mediaan "
          f"{g['profiili_r'].median():.3f}; üle ±15%: {', '.join(mp_nimi(g.loc[(g['suhe'] - 1).abs() > 0.15, 'mp_id'])) or '-'}")

# --- 3) Usutavus -----------------------------------------------------------------------------------------
us = v.groupby("mp_id").agg(soidukeid=("kiirus", "size"), kiirus_0=("kiirus", lambda s: (s == 0).mean() * 100),
                            kiirus_ule_120=("kiirus", lambda s: (s > 120).mean() * 100),
                            pikkus_0=("pikkus", lambda s: (s == 0).mean() * 100),
                            pikkus_ule_25=("pikkus", lambda s: (s > 25).mean() * 100)).reset_index()
save_table(us.assign(mp=mp_nimi(us["mp_id"])).drop(columns="mp_id").round(3), "11_usutavus")
print(f"\n3) Usutavus: kiirus 0 {(v['kiirus'] == 0).mean() * 100:.2f}%, üle 120 km/h {(v['kiirus'] > 120).mean() * 100:.3f}% "
      f"(suurim {v['kiirus'].max():.0f}); pikkus 0 {(v['pikkus'] == 0).mean() * 100:.2f}%, üle 25 m "
      f"{(v['pikkus'] > 25).mean() * 100:.3f}%. Ristmikud, kus kiirus 0 üle 2%: "
      f"{', '.join(mp_nimi(us.loc[us['kiirus_0'] > 2, 'mp_id'])) or '-'}")

# --- 4) Künnise tundlikkus ---------------------------------------------------------------------------------
c = loe("09_tsuklid", parse_dates=["algus"])
c = c[c["meetod"] == "kindel"].assign(paev=lambda z: z["algus"].dt.normalize())
c["sile"] = (c["n"] * 3600 / c["T"]).groupby([c["mp"], c["direction_id"], c["paev"], c["loik"]]).transform(
    lambda s: s.rolling(5, center=True, min_periods=3).median())         # nagu 09: silumine ega ummik ei ulatu üle augu
grupid = dict(tuple(c.groupby(["mp", "direction_id", "paev"])))
um = loe("09_ummikud", parse_dates=["paev"])
um = um[um["stabiilne"] & (um["meetod"] == "kindel")]
KUNNISED = (X_LAHEDAL - 0.05, X_LAHEDAL, X_LAHEDAL + 0.05)             # 09: ALGUS = X_LAHEDAL (0,85)
rows = []
for r in um.itertuples():
    g = grupid[(r.mp, r.direction_id, r.paev)]
    tt, T, s, lk = g["t"].values, g["T"].values, g["sile"].values, g["loik"].values
    lo, hi = np.searchsorted(tt, np.array(TIPUD[r.tipp.split("+")[0]]) * 3600)
    for kunnis in KUNNISED:
        loik = ummiku_loik(ummikumask(s, r.taistase_soid_h, kunnis, loik=lk), lo, hi, 0, loik=lk)
        if loik:
            rows.append(dict(ummik=r.Index, kunnis=kunnis, algus=tt[loik[0]] / 60, lahenes=(tt[loik[1] - 1] + T[loik[1] - 1]) / 60))
tn = pd.DataFrame(rows).pivot(index="ummik", columns="kunnis")
tundl = pd.DataFrame({k: {"ummikuid": tn[("algus", k)].notna().sum(),
                          "alguse_nihe_min_mediaan": (tn[("algus", k)] - tn[("algus", X_LAHEDAL)]).median(),
                          "lahenemise_nihe_min_mediaan": (tn[("lahenes", k)] - tn[("lahenes", X_LAHEDAL)]).median(),
                          "kestus_min_mediaan": (tn[("lahenes", k)] - tn[("algus", k)]).median(),
                          "algus_nihkub_ule_15min_%": ((tn[("algus", k)] - tn[("algus", X_LAHEDAL)]).abs() > 15).mean() * 100}
                      for k in KUNNISED}).T.rename_axis("kunnis")
save_table(tundl.reset_index().round(2), "11_tundlikkus")
print(f"\n4) Künnise tundlikkus (kindla tsükliga stabiilsed ummikud; nihe võrreldes {X_LAHEDAL:.0%} künnisega):")
print(tundl.round(1).to_string())

# --- 5) Olulisus -------------------------------------------------------------------------------------------
rows = []
try:
    a, b = (loe(f"{s}/06_tipptunnid").query("mp_id > 0").set_index("mp_id") for s in ("LSS", "LVS"))
    for veerg, nimi in [("hommik_algus_h", "hommikuse tipu algus"), ("ohtu_algus_h", "õhtuse tipu algus")]:
        vahe = ((b[veerg] - a[veerg]) * 60).dropna()
        uv = mediaani_uv(vahe)
        rows.append(dict(vordlus=f"LVS - LSS, {nimi} (min)", n=len(vahe), mediaan=vahe.median(), uv_alumine=uv[0],
                         uv_ylemine=uv[1], p=stats.wilcoxon(vahe).pvalue))
except FileNotFoundError:
    print("   (LSS/LVS 06_tipptunnid.csv puudub - käivita 06 suunaanalüüs)")
ub = loe("09_ummiku_umber")
ub = ub[ub["stabiilne"] & (ub["tyyp"] == "tööpäev")].assign(ryhm=lambda z: np.where(z["meetod"] == "vaba", "vaba vool", "foor"))
for (ryhm, nihe), g in ub.groupby(["ryhm", "nihe_min"]):
    uv = mediaani_uv(g["voit_kmh"])
    rows.append(dict(vordlus=f"kiiruse võit, {ryhm}, nihe {nihe:+d} min (km/h)", n=len(g), mediaan=g["voit_kmh"].median(),
                     uv_alumine=uv[0], uv_ylemine=uv[1], p=stats.wilcoxon(g["voit_kmh"]).pvalue))
ol = pd.DataFrame(rows)
save_table(ol.round(4), "11_olulisus")
print("\n5) Olulisus (mediaan, 95% usaldusvahemik, Wilcoxoni p; p < 0,05 = erineb nullist):")
print(ol.round(3).to_string(index=False))

# --- 6) Ühe päeva jaotuste püsivus päevade vahel -----------------------------------------------------------
tp = [pd.Timestamp(p) for p in paevad if pd.Timestamp(p).dayofweek < 5]
if len(tp) >= 2:
    tipp = list(range(28, 40)) + list(range(60, 76))                    # kell 7-10 ja 15-19
    sh = pd.concat({p: five_min_shares(v, days=[p]) for p in tp}, names=["paev"])
    sh = sh[sh.index.get_level_values("slot").isin(tipp)]
    h5 = sh.groupby(["mp_id", "slot"]).std().stack() * 100              # protsendipunkti
    rows = [dict(naitaja="5 min osakaal 15 min pilus, tipptunnid (hajuvus päevade vahel, protsendipunkti)",
                 mediaan=h5.median(), p90=h5.quantile(.9))]
    for suund in ("LSS", "LVS"):
        osa = pd.DataFrame({p: direction_share(v, suund, days=[p])[1] for p in tp}) * 100
        rows.append(dict(naitaja=f"{suund} osakaal ristmiku ööpäevast (hajuvus päevade vahel, protsendipunkti)",
                         mediaan=osa.std(axis=1).median(), p90=osa.std(axis=1).quantile(.9)))
    pys = pd.DataFrame(rows)
    save_table(pys.round(2), "11_pysivus")
    print(f"\n6) Püsivus {len(tp)} tööpäeva vahel:")
    print(pys.round(2).to_string(index=False))
else:
    pys = None
    print("\n6) Püsivus: vajab vähemalt 2 tervet tööpäeva.")

# --- Joonised ----------------------------------------------------------------------------------------------
set_style()
paeva_silt = lambda p: f"{pd.Timestamp(p):%d.%m}\n{'ETKNRLP'[pd.Timestamp(p).dayofweek]}"
fig, axes = plt.subplots(1, 2, figsize=(14, 12), sharey=True, layout="constrained")
for ax, (df, veerg, pealkiri, kw) in zip(axes, [
        (terv, "puudu_%", "Kaotsi läinud kirjed, % (vahele jäänud järjekorranumbrid)",
         dict(cmap="Reds", vmin=0, vmax=max(terv["puudu_%"].max(), 0.5), fmt=".2f")),
        (tavalisus, "suhe", "Ristmiku päeva summa / 2026. a tavaline õppetöö tööpäev",
         dict(cmap=DIVERGING, vmin=0.6, vmax=1.4, center=1, fmt=".2f"))]):
    m = df.assign(mp=mp_nimi(df["mp_id"])).pivot(index="mp", columns="paev", values=veerg)
    sns.heatmap(m, ax=ax, annot=True, annot_kws={"fontsize": 6}, linewidths=0.4, linecolor="white",
                cbar_kws={"shrink": 0.6}, **kw)
    ax.set_xticklabels([paeva_silt(p) for p in m.columns], rotation=0, fontsize=8)
    ax.set_title(pealkiri, fontsize=10)
    ax.set_xlabel("")
    ax.set_ylabel("")
fig.suptitle("Sõidukipõhiste kirjete terviklikkus ja päeva tavalisus (ristmiku terved päevad)", x=0.01, ha="left",
             fontweight="bold")
save(fig, "11_01_terviklikkus")

US = {"kiirus_0": ("kiirus 0 km/h", C_BLUE), "kiirus_ule_120": ("kiirus üle 120 km/h", C_ORANGE),
      "pikkus_0": ("pikkus 0 m", C_AQUA), "pikkus_ule_25": ("pikkus üle 25 m", C_YELLOW)}
u = us.assign(mp=mp_nimi(us["mp_id"])).sort_values("mp", ascending=False)
fig, ax = plt.subplots(figsize=(9, 11), layout="constrained")
for veerg, (silt, varv) in US.items():
    ax.scatter(u[veerg], u["mp"], s=26, color=varv, edgecolor="white", lw=0.5, label=silt, zorder=3)
ax.set_xlim(left=0)
ax.set_xlabel("Osakaal ristmiku sõidukitest, %")
ax.legend(loc="lower right", fontsize=9)
ax.set_title("Ebausutavad mõõtmised ristmiku kaupa (logija nädal, terved päevad)")
save(fig, "11_02_usutavus")

fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), layout="constrained")
kx = np.arange(len(tundl))
silt = [f"{k:.0%}" for k in tundl.index]
axes[0].bar(kx, tundl["kestus_min_mediaan"], color=[C_GRAY if k != X_LAHEDAL else C_BLUE for k in tundl.index], width=0.6)
for x, r in zip(kx, tundl.itertuples()):
    axes[0].annotate(f"{r.kestus_min_mediaan:.1f} min\n{int(r.ummikuid)} ummikut", (x, r.kestus_min_mediaan),
                     xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8)
axes[0].set_ylim(0, tundl["kestus_min_mediaan"].max() * 1.2)
axes[0].set_xticks(kx, silt)
axes[0].set_xlabel("Ummiku lävi, % täistasemest (09: 85%, HCM 2000 ptk. 10-46)")
axes[0].set_ylabel("Stabiilse ummiku kestus, min (mediaan)")
axes[0].set_title("Kestus sõltub lävest", fontsize=10)
w = 0.35
axes[1].bar(kx - w / 2, tundl["alguse_nihe_min_mediaan"], w, color=C_BLUE, label="algus")
axes[1].bar(kx + w / 2, tundl["lahenemise_nihe_min_mediaan"], w, color=C_ORANGE, label="lahenemine")
axes[1].axhline(0, color=TEXT2, lw=0.8)
axes[1].set_xticks(kx, [f"{k}\nalgus nihkub üle 15 min: {o:.0f}%" for k, o in zip(silt, tundl["algus_nihkub_ule_15min_%"])],
                   fontsize=9)
axes[1].set_ylabel("Nihe võrreldes 85% lävega, min (mediaan)")
axes[1].set_title("Alguse ja lahenemise nihe (miinus = varem)", fontsize=10)
axes[1].legend(fontsize=9)
fig.suptitle("Ummikuläve tundlikkus (kindla tsükliga stabiilsed ummikud)", x=0.01, ha="left", fontweight="bold")
save(fig, "11_03_tundlikkus")

osad = [("min", "Tipu algus samal ristmikul: LVS − LSS, min"),
        ("km/h", "Kiiruse võit ummiku ümber, km/h\n(nihe: aken enne (−) või pärast (+) ummikut)")]
fig, axes = plt.subplots(1, 3 if pys is not None else 2, figsize=(16, 6.5), layout="constrained",
                         gridspec_kw={"width_ratios": [0.8, 1.5, 1][:3 if pys is not None else 2]})
for ax, (yhik, pealkiri) in zip(axes, osad):
    o = ol[ol["vordlus"].str.endswith(f"({yhik})")].iloc[::-1].reset_index(drop=True)
    if o.empty:
        ax.axis("off")
        continue
    varv = np.where(o["vordlus"].str.contains("vaba vool"), C_ORANGE, C_BLUE)
    ax.errorbar(o["mediaan"], o.index, xerr=[o["mediaan"] - o["uv_alumine"], o["uv_ylemine"] - o["mediaan"]], fmt="none",
                ecolor=C_GRAY, lw=1.2, capsize=3, zorder=2)
    ax.scatter(o["mediaan"], o.index, color=varv, s=40, zorder=3, edgecolor="white", lw=0.6)
    ax.axvline(0, color=TEXT2, lw=0.8)
    ax.set_yticks(o.index, [f"{s.split(', ', 1)[1].rsplit(' (', 1)[0]}  (p = {p:.3f}, n = {n})"
                            for s, p, n in zip(o["vordlus"], o["p"], o["n"])], fontsize=8)
    ax.set_xlabel(f"Mediaan ja 95% usaldusvahemik (bootstrap), {yhik}")
    ax.set_title(pealkiri, fontsize=10)
if pys is not None:
    ax = axes[2]
    p6 = pys.iloc[::-1].reset_index(drop=True)
    ax.hlines(p6.index, p6["mediaan"], p6["p90"], color=C_GRAY, lw=1.2)
    ax.scatter(p6["mediaan"], p6.index, color=C_BLUE, s=40, zorder=3, label="mediaan")
    ax.scatter(p6["p90"], p6.index, color=C_GRAY, marker="|", s=120, zorder=3, label="90. protsentiil")
    ax.set_yticks(p6.index, [s.split(" (")[0] for s in p6["naitaja"]], fontsize=8)
    ax.set_xlim(left=0)
    ax.set_xlabel("Hajuvus tööpäevade vahel, protsendipunkti")
    ax.set_title("Ühe päeva jaotuste püsivus", fontsize=10)
    ax.legend(fontsize=8, loc="lower right")
axes[1].legend(handles=[plt.Line2D([], [], marker="o", ls="", color=C_BLUE, label="foor"),
                        plt.Line2D([], [], marker="o", ls="", color=C_ORANGE, label="vaba vool")], fontsize=8,
               loc="upper right")
fig.suptitle("Olulisus ja püsivus: mediaanid usaldusvahemikega (p = Wilcoxoni märgiastaktest)", x=0.01, ha="left",
             fontweight="bold")
save(fig, "11_04_olulisus_pysivus")
o = ol[ol["vordlus"].str.startswith("LVS - LSS")].reset_index(drop=True)        # 11_04b: suunavõrdlus eraldi
if len(o):
    fig, ax = plt.subplots(figsize=(10, 3.2), layout="constrained")
    ax.errorbar(o["mediaan"], o.index, xerr=[o["mediaan"] - o["uv_alumine"], o["uv_ylemine"] - o["mediaan"]], fmt="o",
                color=C_BLUE, ecolor=C_GRAY, capsize=4, ms=7)
    ax.axvline(0, color=TEXT2, lw=0.8)
    ax.set_yticks(o.index, [f"{s.split(', ', 1)[1].rsplit(' (', 1)[0]}\n(p = {p:.3f}, n = {n})"
                            for s, p, n in zip(o["vordlus"], o["p"], o["n"])], fontsize=9)
    ax.set_ylim(-0.6, len(o) - 0.4)
    ax.set_xlabel("Linnast välja (LVS) miinus linna sisse (LSS) suunduva tipu algus samal ristmikul, min "
                  "(mediaan, 95% usaldusvahemik)")
    ax.set_title("Kas linnast välja suunduv tipp algab hiljem kui linna suunduv?", fontsize=10, loc="left")
    save(fig, "11_04b_suunad")
# --- 7) Linna piiri ristlõiked: Transpordiameti baasprognoos (Kaal jt 2020, tabel 10.1 lk 100) ------------------------
# 2020. a 10. nädala tööpäevade keskmine ööpäevane liiklussagedus (NTPKÖL), mõlemad suunad. True = ristmik loendab
# peamiselt sama tee läbivat liiklust; False = ka ristuvate tänavate manöövreid, seega on ristmiku summa suurem.
BP2020 = {11: ("Paldiski mnt (Ilmajaam)", 19168, True), 25: ("Peterburi tee (Väo)", 25671, True),
          28: ("Ranna tee (Viimsi)", 21324, True), 12: ("Rannamõisa tee (Haabersti)", 48478, False),
          20: ("Suur-Sõjamäe (Smuuli)", 8405, False), 22: ("Vana-Narva mnt (Iru)", 11133, False)}
tp = tavalisus[tavalisus["paev"].dt.day_of_week < 5].groupby("mp_id")["soidukeid"].mean()
bp = pd.DataFrame([dict(mp_id=m, ristloige=n, bp_2020=q, uks_tee=u, logija_toopaev=tp.get(m)) for m, (n, q, u) in BP2020.items()])
bp["suhe"] = bp["logija_toopaev"] / bp["bp_2020"]
assert bp["logija_toopaev"].notna().all(), "baasprognoosi ristmikul pole logija nädala tööpäevi"
save_table(bp.assign(mp=mp_nimi(bp["mp_id"])).drop(columns="mp_id").round(3), "11_baasprognoos")
print("7) Baasprognoos: " + "; ".join(f"MP{r.mp_id:02d} {r.logija_toopaev:,.0f} vs {r.bp_2020:,} ({r.suhe:.2f})"
                                       for r in bp.itertuples()).replace(",", " "))
fig, ax = plt.subplots(figsize=(11, 4.8), layout="constrained")
y = np.arange(len(bp))[::-1]
ax.barh(y + 0.18, bp["logija_toopaev"], 0.34, color=C_BLUE, label="ristmik, logija nädala tööpäevade keskmine")
ax.barh(y - 0.18, bp["bp_2020"], 0.34, color=C_GRAY, label="baasprognoosi ristlõige, 2020. a 10. nädala tööpäevad")
for yy, r in zip(y, bp.itertuples()):
    ax.text(max(r.logija_toopaev, r.bp_2020) * 1.01, yy, f"{r.suhe:.2f}×", va="center", fontsize=9, color=TEXT2)
ax.set_yticks(y, [f"MP{r.mp_id:02d} – {r.ristloige}" + ("" if r.uks_tee else " *") for r in bp.itertuples()], fontsize=9)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", " ")))
ax.set_xlabel("Sõidukit ööpäevas (mõlemad suunad)")
ax.legend(fontsize=8, loc="lower right")
ax.set_title("Ristmike loendus ja baasprognoosi linna piiri ristlõiked (* = ristmik loendab ka ristuvaid tänavaid)",
             fontsize=10, loc="left")
save(fig, "11_05_baasprognoos")
print("Valmis.")
