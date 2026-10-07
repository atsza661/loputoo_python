"""
11 - Arvukontrollid enne tulemuste avaldamist: kas sõidukipõhised andmed on terviklikud ja usutavad ning kui kindlad on
skriptide 06, 09 ja 10 tulemused. Jooniseid ei tee; tulemused trükitakse ekraanile ja tabelitesse. Käivita pärast 06
(ka LSS/LVS), 09 ja 10; uuesti siis, kui nädala kirjed on andmebaasi laetud.

SISEND
  common.load_vehicles(None, koik=True)   sõidukipõhised kirjed (ainult terved ööpäevad, >= 23 tundi andmeid)
  common.load_tallinn()                   ristmike 15 min loendused (tavalise tööpäeva võrdluseks)
  valjund/09_tsuklid.csv, 09_ummikud.csv, 09_ummiku_umber.csv; valjund/LSS ja valjund/LVS/06_tipptunnid.csv

KONTROLLID: ARVUTUS JA VÄLJUND (kaust valjund/)
  1) Terviklikkus: iga loendur nummerdab sõidukid (life). Vahele jäänud numbrid = kaotsi läinud read (salvestamisel või
     edastamisel). Korduva numbriga read (mitte-sõidukid) ja kiiruse koodi 255 eemaldab common.load_vehicles - siin
     näidatakse, kui palju.                                                   -> 11_terviklikkus.csv
  2) Kas sõidukipõhine päev on tavaline? Ristmiku ööpäeva summa ja 15 min profiil võrreldes 2026. a tavalise
     õppetöö-aegse tööpäevaga: summade suhe ja profiilide korrelatsioon.     -> 11_paeva_tavalisus.csv
  3) Usutavus: kiirus 0 või üle 120 km/h, pikkus 0 või üle 25 m (% ristmiku sõidukitest).  -> 11_usutavus.csv
  4) Künnise tundlikkus: kui palju nihkub ummiku algus ja lahenemine, kui ummiku lävi on 75% või 85% täistasemest
     (mitte 80%; lubatud lühikese vajumise põhi on alati 5 protsendipunkti madalam). Kindla tsükliga stabiilsed
     ummikud.                                                                  -> 11_tundlikkus.csv
  5) Olulisus: LSS ja LVS tipu alguse erinevus samal ristmikul (Wilcoxoni märgiastaktest) ning ummiku ümber kiiruse
     võidu mediaani 95% usaldusvahemik (bootstrap, common.mediaani_uv).       -> 11_olulisus.csv
  6) Ühe päeva jaotuste püsivus (vajab >= 2 tervet tööpäeva): 5 min osakaalude ja LSS/LVS osakaalu standardhälve
     päevade vahel, protsendipunkti.                                           -> 11_pysivus.csv
"""
import numpy as np
import pandas as pd
from scipy import stats

from common import (load_vehicles, load_tallinn, five_min_shares, direction_share, ummiku_loik, ummikumask, save_table,
                    OUT_DIR, PUHASTUS, mediaani_uv)

TIPUD = {"hommik": (6, 11), "õhtu": (14, 20)}
loe = lambda nimi, **kw: pd.read_csv(OUT_DIR / f"{nimi}.csv", encoding="utf-8-sig", **kw)
mp_nimi = lambda s: "MP" + s.astype(str).str.zfill(2)


assert (lambda u: u[0] <= 5 <= u[1])(mediaani_uv(np.arange(11)))

v = load_vehicles(None, koik=True)
v["paev"] = v["ts"].dt.normalize()
tunde = v.groupby("paev")["ts"].agg(lambda s: s.dt.hour.nunique())
v = v[v["paev"].isin(tunde[tunde >= 23].index)]                         # ainult terved ööpäevad
paevad = sorted(v["paev"].unique())
print(f"Terveid ööpäevi: {len(paevad)} ({', '.join(pd.Timestamp(p).strftime('%d.%m %a') for p in paevad)}); "
      f"osalised jäeti välja: {', '.join(str(p.date()) for p in tunde[tunde < 23].index) or '-'}")

# --- 1) Terviklikkus loenduri järjekorranumbri järgi ---------------------------------------------------
v = v.sort_values(["mp_id", "kanal", "life"])
d = v.groupby(["mp_id", "kanal", "paev"])["life"].diff()
v["puudu"] = d.where((d > 1) & (d < 10000), 1) - 1                      # loenduri nullimist ei loeta
terv = v.groupby(["paev", "mp_id"]).agg(soidukeid=("life", "size"), puudu=("puudu", "sum")).reset_index()
terv["puudu_%"] = terv["puudu"] / (terv["soidukeid"] + terv["puudu"]) * 100
puh = PUHASTUS[True]
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
c["sile"] = (c["n"] * 3600 / c["T"]).groupby([c["mp"], c["direction_id"], c["paev"]]).transform(
    lambda s: s.rolling(5, center=True, min_periods=3).median())
grupid = dict(tuple(c.groupby(["mp", "direction_id", "paev"])))
um = loe("09_ummikud", parse_dates=["paev"])
um = um[um["stabiilne"] & (um["meetod"] == "kindel")]
KUNNISED = (0.75, 0.80, 0.85)                                           # 09: ALGUS = 0,80, PUSIB = ALGUS - 0,05
rows = []
for r in um.itertuples():
    g = grupid[(r.mp, r.direction_id, r.paev)]
    tt, T, s = g["t"].values, g["T"].values, g["sile"].values
    lo, hi = np.searchsorted(tt, np.array(TIPUD[r.tipp.split("+")[0]]) * 3600)
    for kunnis in KUNNISED:
        loik = ummiku_loik(ummikumask(s, r.taistase_soid_h, kunnis, kunnis - 0.05), lo, hi, 0)
        if loik:
            rows.append(dict(ummik=r.Index, kunnis=kunnis, algus=tt[loik[0]] / 60, lahenes=(tt[loik[1] - 1] + T[loik[1] - 1]) / 60))
tn = pd.DataFrame(rows).pivot(index="ummik", columns="kunnis")
tundl = pd.DataFrame({k: {"ummikuid": tn[("algus", k)].notna().sum(),
                          "alguse_nihe_min_mediaan": (tn[("algus", k)] - tn[("algus", 0.80)]).median(),
                          "lahenemise_nihe_min_mediaan": (tn[("lahenes", k)] - tn[("lahenes", 0.80)]).median(),
                          "kestus_min_mediaan": (tn[("lahenes", k)] - tn[("algus", k)]).median(),
                          "algus_nihkub_ule_15min_%": ((tn[("algus", k)] - tn[("algus", 0.80)]).abs() > 15).mean() * 100}
                      for k in KUNNISED}).T.rename_axis("kunnis")
save_table(tundl.reset_index().round(1), "11_tundlikkus")
print("\n4) Künnise tundlikkus (kindla tsükliga stabiilsed ummikud; nihe võrreldes 80% künnisega):")
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
    sh = pd.concat({p: five_min_shares(v, day=str(p.date())) for p in tp}, names=["paev"])
    sh = sh[sh.index.get_level_values("slot").isin(tipp)]
    h5 = sh.groupby(["mp_id", "slot"]).std().stack() * 100              # protsendipunkti
    rows = [dict(naitaja="5 min osakaal 15 min pilus, tipptunnid (hajuvus päevade vahel, protsendipunkti)",
                 mediaan=h5.median(), p90=h5.quantile(.9))]
    for suund in ("LSS", "LVS"):
        osa = pd.DataFrame({p: direction_share(v, suund, day=str(p.date()))[1] for p in tp}) * 100
        rows.append(dict(naitaja=f"{suund} osakaal ristmiku ööpäevast (hajuvus päevade vahel, protsendipunkti)",
                         mediaan=osa.std(axis=1).median(), p90=osa.std(axis=1).quantile(.9)))
    pys = pd.DataFrame(rows)
    save_table(pys.round(2), "11_pysivus")
    print(f"\n6) Püsivus {len(tp)} tööpäeva vahel:")
    print(pys.round(2).to_string(index=False))
else:
    print("\n6) Püsivus: vajab vähemalt 2 tervet tööpäeva (praegu ühe päeva jaotus rakendub kõigile päevadele).")
print("Valmis.")
