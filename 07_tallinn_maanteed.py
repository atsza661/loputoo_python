"""
07 - Tallinna ristmikud ja maanteede püsiloendurid koos: tipptundide ajastus linnade kaupa, kaardid, päevane seos ja
võrdlus Harjumaa kütusemüügiga.

SISEND
  common.load_tallinn(), load_junctions()            ristmike 15 min loendused puhastatult; ristmike nimed, koordinaadid
  common.load_hourly_profile()                       maanteeloendurite tunniprofiil kuu ja päevatüübi kaupa
  common.load_daily(), counter_month()               maanteeloendurite päevasummad ja kehtivad loendur-kuud
  common.load_locations(), highway.counter_channel   loendurite asukohad ja radade nimed (nt "Tartu - Tallinn")
  common.load_15m()                                  maanteeloendurite 15 min loendused (Harjumaa loendurid)
  common.load_datex_quarters(), load_datex_sites()   DATEX II 15 min vood ühe ööpäeva kohta (loendurid, millel oma
                                                     15 min loendusi pole)
  common.load_vehicles(), five_min_shares()          sõidukipõhine ööpäev ristmike 15 min pilude jagamiseks 5 min osadeks
  common.load_fuel_county()                          Harjumaa kütusemüük
  Keskkonnamuutujad: RES=15 -> ristmikel toored 15 min andmed (failid *_15min); SUUND=LSS|LVS -> ainult Tallinna kaardi
  ala maanteeloendurid selles suunas; Harjumaa kaarti ning päeva- ja kuuindekseid siis ei tehta.

ARVUTUS
  Ühine periood 2024-08 ... 2026-08. Profiilid: E-R koolikuudel (september-mai), sest maanteede tunniprofiil on kuu
    kaupa ja pühi ei saa sealt eraldada; ristmike profiil on tehtud samadel alustel. Tunnid on kellatunnid.
  Loenduri linn ja suund: loendur kuulub linna (Tallinn, Tartu, Pärnu, Viimsi) juurde, kui see on linnast kuni 20 km
    (linnulennult). Suund loetakse raja nimest: sihtkoht linn = "sisse", lähtekoht linn = "välja", muu = "muu" (nt
    ringtee).
  Tunniprofiil: loenduri suuna keskmine sõidukite arv igal kellatunnil (vähemalt ~60 tööpäeva, kõik 24 tundi olemas,
    kahtlase mahuga kuud välja); ristmikul läheb tund arvesse ainult siis, kui kõik 4 veerandtundi on olemas.
  Peenem ajasamm tipunäitajate jaoks:
    ristmikud   15 min profiil jagatakse 5 min osadeks sõidukipõhise ööpäeva järgi (common.five_min_shares)
    maanteed    tunniprofiil jagatakse veerandtundideks 1) loenduri enda 15 min loenduste osakaaludega samadelt
                päevadelt või, kui neid pole, 2) lähima DATEX II loenduskoha (<= 300 m) ööpäeva osakaaludega. DATEX-i
                suund sobitatakse tunniprofiilide korrelatsiooni järgi (parim paar enne, kumbki üks kord); puuduv tund
                jagatakse ühtlaselt. Ülejäänud maanteeloenduritel jäävad tunnid.
  Tipunäitajad (common.peak_metrics): tipptunni algus, osakaal ööpäevast, teoreetiline hajutamise potentsiaal (+-1 h)
    ja liikluse keskaeg = mahuga kaalutud keskmine kellaaeg aknas (hommik 06-10, õhtu 15-19).
  Päevaindeks: koha päeva maht jagatud sama koha sama nädalapäeva 2025. a keskmisega (kohtade summad), x 100; päev jääb
    välja, kui kohti on alla 70% tavalisest. Maanteelt on väljas loendur-päevad, mille maht on alla 40% või üle 250%
    sama nädalapäeva libisevast mediaanist. Korrelatsioon ristmike ja Tallinna sissesõiduteede vahel kõigi päevade ja
    päevatüüpide kaupa.
  Kuuindeksid (common.ratio_index, 2025 = 100): ristmikud, Harjumaa maanteeloendurid, kõik kohad koos ning maanteede
    kerged ja rasked sõidukid; korrelatsioon Harjumaa müügiindeksiga tasemes, kuumuutustes ja aastamuutustes.

CALCULATION IN PLAIN ENGLISH
  Common period 2024-08 ... 2026-08, Monday-Friday in school months (September-May).
  Counter city and direction: a highway counter belongs to a city when it is within 20 km (straight line). The lane name
    gives the direction: city as destination = inbound, city as origin = outbound.
  Hourly profile = average vehicles of the counter direction in each clock hour (complete days only, at least ~60
    workdays, suspicious months left out). A junction hour counts only when all four 15-minute slots exist.
  Finer steps: junction 15-minute values are split into 5-minute parts by the per-vehicle day. A highway hour is split
    into quarters by the counter's own 15-minute shares on the same days, or else by the shares of the nearest DATEX II
    site (within 300 m; the direction is matched by the best correlation of hourly profiles).
  Peak metrics as in 06 (start, share of day, spreading potential, traffic midpoint).
  Daily index: a place's daily volume / the same place's 2025 average for that weekday, summed over places, x 100; a day
    is dropped when fewer than 70% of the usual places report. Highway counter-days below 40% or above 250% of the
    rolling weekday median are dropped. Correlation between junctions and city entry roads.
  Monthly indexes as in 06 (2025 = 100) for junctions, Harju highway counters, both together and highway light/heavy
    vehicles; correlated with Harju fuel sales in levels, month-on-month and year-on-year changes.

VÄLJUND (kaust valjund/, suunaanalüüsis valjund/LSS või valjund/LVS)
  07_01_profiilid_linnad.png
      Näitab: tööpäeva liikluse jaotust linna sisse- ja väljasõidul linnade kaupa.
      Kuidas: paneel linna kohta; x-telg = kellaaeg, y-telg = osakaal ööpäeva liiklusest, % tunnis. Sinine = sissesõit,
      oranž = väljasõit, türkiis katkendjoon = muu; Tallinna paneelil tume joon = linna ristmikud.
  07_02_tipu_teravus.png
      Näitab: kui terav on tipp eri linnades ja suundades.
      Kuidas: punktdiagrammid 2 x 2 (veerud: hommik, õhtu). Ülal tipptunni osakaal ööpäevast, %; all teoreetiline
      hajutamise potentsiaal, %. x-telg = linn ja suund, punkt = loenduskoht, kriips = mediaan.
  07_03_kaart_harju.png, 07_04_kaart_tallinn.png, 07_05_kaart_kesklinn.png
      Näitab: millal liiklus eri kohtades toimub (Harjumaa; Tallinn; kesklinn kuni 3 km).
      Kuidas: kaks kaarti ortofototaustal - hommik 06-10 (maanteel sissesuund, sinised toonid) ja õhtu 15-19 (maanteel
      väljasuund, oranžid toonid). Ruut = linna ristmik, ring = maanteeloendur. Värv = liikluse keskaeg (hilisem =
      tumedam; värviskaala otstes varaseim ja hiliseim väärtus), suurus = ööpäevane liiklus (ruutjuure skaalas).
      Katkendraam Tallinna kaardil = kesklinna lähivaate ala.
  07_06_paevane_seos.png
      Näitab: kas linna ristmike ja Tallinna sissesõiduteede liiklus kõigub päevade kaupa koos.
      Kuidas: vasakul päevaindeksite 7 päeva libisev keskmine (tume = ristmikud, sinine = sissesõiduteed; sama
      nädalapäev 2025 = 100). Paremal hajuvusdiagramm: punkt = päev, x = sissesõiduteede, y = ristmike indeks; värv =
      päevatüüp (sinine = tööpäev õppetöö ajal, türkiis = tööpäev vaheajal, hall = nädalavahetus, oranž = püha või
      lühendatud päev); punktiir = võrdsuse joon; pealkirjas r ja n.
  07_07_kutus_harju.png
      Näitab: liiklusindeksite ja Harjumaa kütusemüügi käiku kuude kaupa.
      Kuidas: joondiagramm; y-telg = indeks (2025 = 100). Tume katkendjoon = ristmikud, sinine = Harjumaa
      maanteeloendurid, must jäme = kõik loenduskohad koos, oranž jäme = kütusemüük; pealkirjas r.
  07_loendurid_suunad.csv          iga raja linn, kaugus ja suund
  07_tipptunnid_kohad.csv          tipunäitajad loenduskoha kaupa
  07_linnad_kokkuvote.csv          mediaanid linna ja suuna kaupa
  07_maantee_15min_osakaalud.csv   veerandtundide osakaalud tunnis ja nende allikas (15 min loendus või DATEX)
  07_maantee_profiilid.csv         Tallinna kaardi maanteeloendurite 15 min profiilid (06 kasutab; 07 käib enne 06)
  07_maantee_profiilid_koik.csv    kõigi maanteeloendurite 15 min profiilid (07_2 kasutab)
  07_paevane_seos.csv, 07_paevane_korrelatsioon.csv, 07_kuuindeksid.csv, 07_kutus_korrelatsioon.csv
"""
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from common import (load_tallinn, load_junctions, load_locations, load_daily, counter_month,
                    load_fuel_county, peak_metrics, ratio_index, corr_pair, set_style, save, day_calendar,
                    add_basemap, to_merc, load_vehicles, five_min_shares, to_5min, load_datex_quarters,
                    SUUND, SUUND_MAANTEE, RES, km, ends, load_15m, ilma_vigaste_kuudeta, bbox, map_extent, timing_map,
                    save_table, CLASS_COLS, tabel, load_hourly_profile, load_datex_sites, TALLINN_BASE_YEAR,
                    C_BLUE, C_ORANGE, C_AQUA, C_YELLOW, C_GRAY, TEXT2)

set_style()
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)

P0, P1 = pd.Period("2024-08", "M"), pd.Period("2026-08", "M")
SCHOOL_MONTHS = [9, 10, 11, 12, 1, 2, 3, 4, 5]
RADIUS_KM = 20
CITIES = {"Tallinn": (59.4372, 24.7454), "Tartu": (58.3806, 26.7225),
          "Pärnu": (58.3859, 24.4971), "Viimsi": (59.5040, 24.8340)}
LABEL_NAME = {"Tallinn": ("tallinn", "talinn"), "Tartu": ("tartu",), "Pärnu": ("parnu", "pärnu"),
              "Viimsi": ("viimsi",)}
SUUND_COLOR = {"sisse": C_BLUE, "välja": C_ORANGE, "muu": C_AQUA}


print("Laen andmeid...")
t, day = load_tallinn()
jn = load_junctions()
TALLINN_BBOX = bbox(jn, pad=0.04)       # Tallinna kaardi ala: kõigi ristmike ümbris (sama igas suunaanalüüsis)
loc = load_locations()
chn = tabel("highway.counter_channel", dtype={"id": str})
d = load_daily()
cm = counter_month(d)
bad_months = cm.loc[cm["maht_kahtlane"], ["id", "kuu"]]

# --- Loendurite kataloog: linn ja suund iga raja kohta --------------------------------------------
rows = []
for _, r in chn.merge(loc[["id", "nimi", "maakond", "tee_nr", "latitude", "longitude"]], on="id").iterrows():
    o, de = ends(r["channel_label"])
    dist = {c: km(r["latitude"], r["longitude"], *xy) for c, xy in CITIES.items()}
    named = [c for c in CITIES if any(n in (o, de) for n in LABEL_NAME[c])]
    city = min(named or CITIES, key=dist.get)
    suund = ("sisse" if de in LABEL_NAME[city] else "välja" if o in LABEL_NAME[city] else "muu")
    rows.append(dict(id=r["id"], kanal=r["kanal"], nimi=r["nimi"], maakond=r["maakond"],
                     tee_nr=r["tee_nr"], lat=r["latitude"], lon=r["longitude"], linn=city,
                     km_linnast=dist[city], suund=suund, rada=r["channel_label"]))
cat = pd.DataFrame(rows)
cat = cat[cat["km_linnast"] <= RADIUS_KM]
if SUUND_MAANTEE:          # suunaanalüüs: LSS = sissesõit, LVS = väljasõit; ainult Tallinna kaardi ala loendurid
    lo0, la0, lo1, la1 = TALLINN_BBOX
    cat = cat[(cat["suund"] == SUUND_MAANTEE) & cat.lon.between(lo0, lo1) & cat.lat.between(la0, la1)]
save_table(cat, "07_loendurid_suunad")

# --- a) Tunniprofiilid ------------------------------------------------------------------------------
hp = load_hourly_profile()
hp["toopaev"] = hp["toopaev"].astype(str).str.lower().isin(["t", "true", "1"])
hp["per"] = pd.PeriodIndex(pd.to_datetime(dict(year=hp["aasta"], month=hp["kuu"], day=1)), freq="M")
hp = hp[hp["toopaev"] & hp["kuu"].isin(SCHOOL_MONTHS) & (hp["per"] >= P0) & (hp["per"] <= P1)]
hp = hp.merge(bad_months.rename(columns={"kuu": "per"}).assign(_bad=True), on=["id", "per"], how="left")
hp = hp[hp["_bad"].isna()]
hp["soidukeid"] = hp[CLASS_COLS].sum(axis=1)
chh = hp.groupby(["id", "kanal", "tund"]).agg(s=("soidukeid", "sum"), n=("n_hours", "sum")).reset_index()
chh = chh[chh["n"] >= 60]                       # vähemalt ~60 tööpäeva
chh["v"] = chh["s"] / chh["n"]
chh = chh.merge(cat[["id", "kanal", "linn", "suund"]], on=["id", "kanal"])
full = chh.groupby(["id", "kanal"])["tund"].transform("nunique") == 24
site_h = (chh[full].groupby(["id", "linn", "suund", "tund"])["v"].sum()
          .unstack("tund").reindex(columns=range(24)).dropna())

# Tallinna ristmikud samadel alustel: kellatunnid, E-R, koolikuud
tt = t[(t["nadalapaev"] < 5) & t["paev"].dt.month.isin(SCHOOL_MONTHS)
       & (t["paev"].dt.to_period("M") >= P0) & (t["paev"].dt.to_period("M") <= P1)]
tt = tt.assign(tund=tt["slot"] // 4)
hourly = tt.groupby(["mp_id", "paev", "tund"])["v"].agg(["sum", "count"]).reset_index()
hourly = hourly[hourly["count"] == 4]           # tund arvesse ainult siis, kui kõik 4 pilu olemas
jprof = hourly.groupby(["mp_id", "tund"])["sum"].mean().unstack("tund").reindex(columns=range(24))

prow = []
for (sid, linn, suund), v in site_h.iterrows():
    info = cat[cat.id == sid].iloc[0]
    prow.append(dict(koht=f"{info.nimi} ({linn}, {suund})", tyyp="maantee", linn=linn, suund=suund,
                     id=sid, lat=info.lat, lon=info.lon, km_linnast=info.km_linnast,
                     **peak_metrics(v.values, per_hour=1)))
for mp, v in jprof.iterrows():
    info = jn.set_index("mp_id").loc[mp]
    prow.append(dict(koht=f"{info.code} {info['name']}", tyyp="ristmik", linn="Tallinn", suund="ristmik",
                     id=f"MP{mp:02d}", lat=info.lat, lon=info.lon,
                     km_linnast=km(info.lat, info.lon, *CITIES["Tallinn"]), **peak_metrics(v.values, per_hour=1)))
sites = pd.DataFrame(prow)

# Ristmike tipunäitajad 5 min täpsusega: 15 min profiil jagatakse 5 min osadeks ühe päeva
# sõidukipõhiste loenduste järgi (common.five_min_shares, vt 08). RES=15 (või sõidukiteta): toored 15 min.
veh = load_vehicles()
p15 = tt.groupby(["mp_id", "slot"])["v"].mean().unstack("slot").reindex(columns=range(96))
jfine = (to_5min(p15, five_min_shares(veh, outage_from=load_vehicles(None))) if veh is not None and RES == 5
         else p15).dropna()
for mp, v in jfine.iterrows():
    m = peak_metrics(v.values, per_hour=jfine.shape[1] // 24)
    sites.loc[sites.id == f"MP{mp:02d}", list(m)] = list(m.values())

# maanteede 15 min profiilid (06 jaoks): tunniprofiil x veerandtundide osakaalud; ilma osakaaludeta tunni piires ühtlased
hw15 = {key: np.repeat(v.values / 4, 4) for key, v in site_h.iterrows()}
hw_res = dict.fromkeys(hw15, "1 h")
rows = []


def jaga(key, q4, **info):
    """Tunniprofiil x veerandtundide osakaalud q4 (24 x 4) -> loenduri 15 min profiil ja tipunäitajad 15 min täpsusega."""
    hw15[key], hw_res[key] = (site_h.loc[key].values[:, None] * q4).ravel(), "15 min"
    m = peak_metrics(hw15[key], per_hour=4)
    hit = (sites.tyyp == "maantee") & (sites.id == key[0]) & (sites.linn == key[1]) & (sites.suund == key[2])
    sites.loc[hit, list(m)] = list(m.values())
    rows.append(pd.DataFrame(q4 * 100, columns=[f"osa_{i}" for i in range(4)]).round(1)
                .assign(id=key[0], linn=key[1], suund=key[2], tund=range(24), **info))


# 1) Loenduri enda 15 min loendused (highway.count_15min, Harjumaa loendurid): veerandtundide osakaalud samadelt
#    päevadelt kui tunniprofiil (E-R, koolikuud, P0...P1, ilma kahtlase mahuga kuudeta).
m15 = ilma_vigaste_kuudeta(load_15m(), cm)
m15 = m15[(m15.ts.dt.dayofweek < 5) & m15.ts.dt.month.isin(SCHOOL_MONTHS) & (m15.ts >= P0.start_time) & (m15.ts <= P1.end_time)]
m15 = m15.merge(cat[["id", "kanal", "linn", "suund"]], on=["id", "kanal"])
q15 = (m15.groupby(["id", "linn", "suund", m15.ts.dt.hour.rename("tund"), (m15.ts.dt.minute // 15).rename("osa")])["v"]
       .sum().unstack("osa"))
sh15 = q15.div(q15.sum(axis=1).where(q15.sum(axis=1) > 0), axis=0)
oma15 = set()
for key in site_h.index.intersection(sh15.index.droplevel("tund").unique()):
    q4 = sh15.loc[key].reindex(range(24))
    if q4.notna().all().all():
        oma15.add(key)
        jaga(key, q4.values, allikas="15 min loendus", datex_site="", datex_nimi="", r=np.nan, datex_tund=True)

# 2) Ülejäänud loendurid: DATEX II ööpäeva (common.load_datex_quarters) järgi. DATEX koht = lähim loendur (<= 300 m);
#    suund (UUID-1/-2) sobitatakse tunniprofiilide korrelatsiooniga (kumbki DATEX suund ühele profiilile).
dq = load_datex_quarters()
if dq is not None:
    ds = load_datex_sites()
    kxy = km(ds.lat.values[:, None], ds.lon.values[:, None], loc.latitude.values[None], loc.longitude.values[None])
    ds = ds.assign(id=loc.id.values[kxy.argmin(1)], m=kxy.min(1) * 1000)[kxy.min(1) <= 0.3]
    dq = dq[dq.start.dt.dayofweek < 5].assign(tund=dq.start.dt.hour, paev=dq.start.dt.normalize())   # tööpäevad
    dq = dq[dq.groupby(["site", "paev", "tund"])["c"].transform("size") == 4]    # ainult tunnid, kus kõik 4 veerandit
    dh = (dq.groupby(["site", "paev", "tund"])["c"].sum().groupby(["site", "tund"]).mean()
          .unstack().reindex(columns=range(24)))                                 # mitme päeva keskmine tund
    q4 = dq.groupby(["site", "tund", (dq.start.dt.minute // 15).rename("osa")])["c"].sum().unstack("osa")
    sh = q4.div(q4.sum(axis=1).where(q4.sum(axis=1) > 0), axis=0)
    pairs = []
    for key, v in site_h.iterrows():
        for s in ds.loc[ds.id == key[0], "site"] if key not in oma15 else []:
            r = pd.Series(v.values).corr(pd.Series(dh.loc[s].values), min_periods=12) if s in dh.index else np.nan
            if r == r:                                                     # mitte NaN
                pairs.append((r, key, s))
    used = set()
    for r, key, s in sorted(pairs, key=lambda x: -x[0]):              # parim paar enne, kumbki üks kord
        if key in used or s in used:
            continue
        used |= {key, s}
        q4 = sh.reindex(pd.MultiIndex.from_product([[s], range(24)]))
        olemas = q4.notna().all(axis=1).values
        jaga(key, q4.fillna(0.25).values, allikas="DATEX", datex_site=s,          # puuduv tund: ühtlane jaotus
             datex_nimi=ds.set_index("site").nimi[s], r=round(r, 3), datex_tund=olemas)
if rows:
    out = pd.concat(rows)
    save_table(out[["id", "linn", "suund", "allikas", "datex_site", "datex_nimi", "r", "tund", "datex_tund",
                    "osa_0", "osa_1", "osa_2", "osa_3"]], "07_maantee_15min_osakaalud")
    dx = out[out.allikas == "DATEX"]
    print(f"Maanteed 15 min täpsusega: {len(rows)} profiili {len(site_h)}-st - {len(oma15)} loenduri enda 15 min loendustest, "
          f"{len(rows) - len(oma15)} DATEX-i ööpäeva järgi"
          + (f" (sobitus r mediaan {dx.groupby('datex_site').r.first().median():.2f}; tipptundidest DATEX-i veerandid "
             f"{dx[dx.tund.isin([6, 7, 8, 9, 15, 16, 17, 18])].datex_tund.mean() * 100:.0f}%)" if len(dx) else ""))
save_table(sites, "07_tipptunnid_kohad")
save_table(pd.DataFrame([{"id": k[0], "linn": k[1], "suund": k[2], "samm": hw_res[k],     # kõik maanteed (07_2)
                          **{str(i): x for i, x in enumerate(np.round(v, 2))}} for k, v in hw15.items()]),
           "07_maantee_profiilid_koik")

# linnade kokkuvõte (mediaanid)
grp_order = [("Tallinn", "ristmik"), ("Tallinn", "sisse"), ("Tallinn", "välja"), ("Tallinn", "muu"),
             ("Tartu", "sisse"), ("Tartu", "välja"), ("Pärnu", "sisse"), ("Pärnu", "välja"),
             ("Viimsi", "sisse"), ("Viimsi", "välja")]
summ = (sites.groupby(["linn", "suund"])
        .agg(kohti=("koht", "size"), hommik_algus_h=("hommik_algus_h", "median"),
             hommik_keskaeg_h=("hommik_keskaeg_h", "median"), ohtu_keskaeg_h=("ohtu_keskaeg_h", "median"),
             hommik_osakaal=("hommik_osakaal_%", "median"),
             hommik_potentsiaal=("hommik_max_potentsiaal_%", "median"),
             ohtu_algus_h=("ohtu_algus_h", "median"), ohtu_osakaal=("ohtu_osakaal_%", "median"),
             ohtu_potentsiaal=("ohtu_max_potentsiaal_%", "median"))
        .reindex(grp_order).dropna(how="all"))
for c in ["hommik_keskaeg_h", "ohtu_keskaeg_h"]:
    summ[c.replace("_h", "")] = summ[c].map(lambda h: f"{int(round(h * 60)) // 60:02d}:{int(round(h * 60)) % 60:02d}"
                                            if pd.notna(h) else "")
save_table(summ.reset_index(), "07_linnad_kokkuvote")
print("\nLinnade kokkuvõte (mediaanid; algus = tunni algus):")
print(summ.round(1).to_string())

# 07_01_profiilid_linnad: osakaal ööpäevast tunni kaupa
share = lambda df: df.sum(axis=0) / df.sum(axis=0).sum() * 100
cities = [c for c in CITIES if c == "Tallinn" or c in site_h.index.get_level_values("linn")]
nr = (len(cities) + 1) // 2
fig, axes = plt.subplots(nr, 2, figsize=(13, 4.25 * nr), sharex=True, sharey=True, squeeze=False)
H = np.arange(24) + 0.5
for ax, city in zip(axes.flat, cities):
    for suund, col, lab in [("sisse", C_BLUE, "sissesõit linna"), ("välja", C_ORANGE, "väljasõit linnast"),
                            ("muu", C_AQUA, "muu (nt ringtee)")]:
        sub = site_h[(site_h.index.get_level_values("linn") == city) &
                     (site_h.index.get_level_values("suund") == suund)]
        if len(sub):
            n_c = sub.index.get_level_values("id").nunique()
            ax.plot(H, share(sub), color=col, lw=1.8, ls="-" if suund != "muu" else "--",
                    label=f"{lab} ({n_c} loendurit)")
    if city == "Tallinn":                           # ristmikud 5/15 min sammuga, ühik sama (% tunni kohta)
        k = jfine.shape[1] // 24
        ax.plot((np.arange(24 * k) + 0.5) / k, share(jfine) * k, color=TEXT2, lw=1.8,
                label=f"linna ristmikud ({len(jfine)}, {60 // k} min)")
    ax.set_title(city)
    ax.legend(fontsize=8, loc="upper left")
    ax.set_xticks(range(0, 25, 3))
    ax.set_xlim(0, 24)
for ax in axes[-1]:
    ax.set_xlabel("Kellaaeg")
for ax in axes[:, 0]:
    ax.set_ylabel("Osakaal ööpäeva liiklusest, % tunnis")
fig.suptitle("Tööpäeva tunniprofiil linnade kaupa (E-R, september-mai, 2024-2026)",
             x=0.01, ha="left", fontweight="bold")
fig.tight_layout()
save(fig, "07_01_profiilid_linnad")

# 07_02_tipu_teravus: tipptunni osakaal ööpäevast ja teoreetiline hajutamise potentsiaal
sites["grupp"] = sites["linn"] + "\n" + sites["suund"]
order = [f"{c}\n{s}" for c, s in grp_order if ((sites.linn == c) & (sites.suund == s)).any()]
fig, axes = plt.subplots(2, 2, figsize=(14, 8), sharex=True)
for i, (name, lab) in enumerate([("hommik", "Hommikune tipptund"), ("ohtu", "Õhtune tipptund")]):
    for k, (col, ylab) in enumerate([(f"{name}_osakaal_%", "Tipptunni osakaal ööpäevast, %"),
                                     (f"{name}_max_potentsiaal_%", "Teoreetiline hajutamise\npotentsiaal (±1 h), %")]):
        ax = axes[k, i]
        sns.stripplot(data=sites, x="grupp", y=col, order=order, ax=ax, size=5, jitter=0.18,
                      color=C_BLUE if name == "hommik" else C_ORANGE, alpha=0.75)
        med = sites.groupby("grupp")[col].median().reindex(order)
        ax.scatter(range(len(order)), med.values, marker="_", s=900, color=TEXT2, zorder=3, lw=2)
        ax.set_xlabel("")
        ax.set_ylabel(ylab if i == 0 else "")
        if k == 0:
            ax.set_title(lab + " (kriips = mediaan)")
        else:                                       # < 0: selget tippu pole, naabertund on suurem
            ax.axhline(0, color=TEXT2, lw=0.6)
        ax.tick_params(axis="x", labelsize=8)
fig.tight_layout()
save(fig, "07_02_tipu_teravus")

# --- b) Kaardid satelliitaluskaardiga: Harjumaa ja Tallinn -------------------------------------
harju_ids = set(loc.loc[loc.maakond == "Harju", "id"])
mp_ = sites[(sites.tyyp == "ristmik") | (sites.id.isin(harju_ids))]


if not SUUND:              # suunaanalüüsis on ainult Tallinna kaardi ala maanteeloendurid
    timing_map(mp_, "07_03_kaart_harju",
               "Millal liiklus toimub: mahuga kaalutud keskmine kellaaeg (suurus = ööpäevane liiklus)",
               label_junctions=False, size_k=1.3)
jun = mp_[mp_.tyyp == "ristmik"]
lo0, la0, lo1, la1 = TALLINN_BBOX
in_city = mp_[(mp_.lon.between(lo0, lo1)) & (mp_.lat.between(la0, la1))]
# Tallinna kaardil olevate maanteeloendurite profiilid 15 min sammuga (06 lisab need oma joonistele)
hw = in_city[(in_city.tyyp == "maantee") & in_city.suund.isin(["sisse", "välja"])]
save_table(pd.DataFrame([{"koht": r.koht, "id": r.id, "linn": r.linn, "suund": r.suund,
                           "samm": hw_res[(r.id, r.linn, r.suund)],
                           **{str(i): x for i, x in enumerate(hw15[(r.id, r.linn, r.suund)].round(2))}}
                          for r in hw.itertuples()]), "07_maantee_profiilid")
centre = jun[km(jun.lat, jun.lon, *CITIES["Tallinn"]) <= 3.0]
CENTRE_PAD = 0.12
att = timing_map(in_city, "07_04_kaart_tallinn",
                 f"Tallinna ristmikud ({len(jun)}): liikluse keskmine kellaaeg (suurus = ööpäevane liiklus)",
                 label_junctions=True, size_k=0.8, zoom_box=map_extent(centre, CENTRE_PAD),
                 zoom_label=f"kesklinn, {len(centre)} ristmikku: vt 07_05_kaart_kesklinn")
timing_map(centre, "07_05_kaart_kesklinn",
           f"Tallinna ristmikud (≤ 3 km, {len(centre)}): liikluse keskmine kellaaeg (suurus = ööpäevane liiklus)",
           label_junctions=True, size_k=1.4, label_fs=8, pad=CENTRE_PAD)
print("Kaartide taust:", att or "puudub (plaaditeenus ei vastanud - joonistati ilma taustata)")

# --- c) Päevane seos -----------------------------------------------------------------------------------
if SUUND:      # suunaanalüüs: päeva- ja kuuindeksid vs kütus jäävad välja (kütusel suunda pole)
    print("Valmis (suunaanalüüs).")
    sys.exit(0)
tal_ids = set(cat[(cat.linn == "Tallinn") & cat.suund.isin(["sisse", "välja"])]["id"])
dd = d[d["kehtiv"] & d["id"].isin(tal_ids)]
dd = dd.merge(bad_months.assign(_bad=True), on=["id", "kuu"], how="left")
dd = dd[dd["_bad"].isna()]
cd = dd.groupby(["id", "paev"]).agg(n=("kanal", "nunique"), v=("kokku", "sum")).reset_index()
typical = cd.groupby("id")["n"].agg(lambda s: s.mode().max())
cd = cd[cd["n"] >= cd["id"].map(typical)].sort_values(["id", "paev"])
# loendur-päev välja, kui maht < 40% või > 250% sama loenduri sama nädalapäeva libisevast mediaanist
# (nt 2024-08-22: 71% loenduritest näitas üle riigi vaid 5-15% tavalisest - andmeviga)
cd["dow"] = cd["paev"].dt.dayofweek
med = cd.groupby(["id", "dow"])["v"].transform(lambda s: s.rolling(9, center=True, min_periods=4).median())
cd = cd[(cd["v"] / med).between(0.4, 2.5)].drop(columns="dow")
cd = cd[(cd.paev.dt.to_period("M") >= P0) & (cd.paev.dt.to_period("M") <= P1)].rename(columns={"id": "koht"})
jd = day[day["kehtiv"]].rename(columns={"mp_id": "koht", "summa": "v"})[["koht", "paev", "v"]]
jd = jd[(jd.paev.dt.to_period("M") >= P0) & (jd.paev.dt.to_period("M") <= P1)]


def day_index(df):
    """Päevaindeks tabelist df (veerud koht, paev, v = päeva maht): iga päeva kohtade mahtude summa jagatud samade
    kohtade sama nädalapäeva baasaasta keskmiste summaga, x 100. Päev jääb välja, kui kohti on alla 70% tavalisest.
    Tagastab (indeks, kohtade arv) päevade kaupa."""
    df = df.assign(dow=df.paev.dt.dayofweek)
    base = df[df.paev.dt.year == TALLINN_BASE_YEAR].groupby(["koht", "dow"])["v"].mean().rename("b")
    x = df.join(base, on=["koht", "dow"]).dropna(subset=["b"])
    g = x.groupby("paev").agg(v=("v", "sum"), b=("b", "sum"), n=("koht", "nunique"))
    g = g[g["n"] >= 0.7 * g["n"].median()]       # liiga vähe kohti -> päev välja
    return (g["v"] / g["b"] * 100).rename("indeks"), g["n"]


ji, jn_ = day_index(jd)
hi, hn_ = day_index(cd)
dx = pd.DataFrame({"ristmikud": ji, "maanteed": hi}).dropna()
dx = dx.join(day_calendar(dx.index).set_index("paev"))
dx["tyyp"] = np.where(dx.paevatyyp.isin(["riigipüha", "lühendatud"]), "püha / lühendatud",
                      np.where(dx.paevatyyp == "tööpäev",
                               np.where(dx.vaheaeg == "kool", "tööpäev, õppetöö", "tööpäev, vaheaeg"),
                               "nädalavahetus"))
save_table(dx.reset_index(names="paev"), "07_paevane_seos")
drows = [dict(valim="kõik päevad", **corr_pair(dx.ristmikud, dx.maanteed))]
for ty, g in dx.groupby("tyyp"):
    drows.append(dict(valim=ty, **corr_pair(g.ristmikud, g.maanteed)))
dcorr = pd.DataFrame(drows)
save_table(dcorr, "07_paevane_korrelatsioon")
print("\nPäevaindeksite korrelatsioon (ristmikud vs Tallinna sissesõiduteed):")
print(dcorr.round(3).to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(15, 5.2), gridspec_kw=dict(width_ratios=[1.6, 1]))
ax = axes[0]
roll = dx[["ristmikud", "maanteed"]].rolling(7, center=True, min_periods=5).mean()
ax.plot(roll.index, roll.ristmikud, color=TEXT2, lw=2, label=f"Tallinna ristmikud ({int(jn_.median())})")
ax.plot(roll.index, roll.maanteed, color=C_BLUE, lw=2,
        label=f"Tallinna sissesõiduteed, mõlemad suunad ({int(hn_.median())})")
ax.axhline(100, color=TEXT2, lw=0.6, ls=":")
ax.set_ylabel(f"Indeks (sama nädalapäev {TALLINN_BASE_YEAR} = 100)")
ax.set_title("Päevane liiklus, 7 päeva libisev keskmine: linna ristmikud vs sissesõiduteed")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=2, fontsize=9)
ax = axes[1]
pal = {"tööpäev, õppetöö": C_BLUE, "tööpäev, vaheaeg": C_AQUA, "nädalavahetus": C_GRAY,
       "püha / lühendatud": C_ORANGE}
for ty, col in pal.items():
    g = dx[dx.tyyp == ty]
    ax.scatter(g.maanteed, g.ristmikud, s=14, color=col, alpha=0.7, label=ty, edgecolor="none")
lim = [dx[["ristmikud", "maanteed"]].min().min() - 3, dx[["ristmikud", "maanteed"]].max().max() + 3]
ax.plot(lim, lim, color=TEXT2, lw=0.6, ls=":")
c0 = dcorr.iloc[0]
ax.set_title(f"Päevaindeksid (r = {c0.r:.2f}, n = {int(c0.n)})")
ax.set_xlabel("Sissesõiduteed, indeks")
ax.set_ylabel("Ristmikud, indeks")
ax.legend(fontsize=8, loc="upper left")
fig.tight_layout()
save(fig, "07_06_paevane_seos")

# --- d) Kuuindeksid vs Harjumaa kütus ----------------------------------------------------------------
dv = day[day["kehtiv"]].assign(kuu=day["paev"].dt.to_period("M"))
jm = dv.groupby(["mp_id", "kuu"]).agg(paevi=("paev", "size"), kokku=("summa", "mean")).reset_index()
jm = jm[(jm["paevi"] >= 15) & (jm.kuu >= P0) & (jm.kuu <= P1)]
jm["koht"] = "MP" + jm["mp_id"].astype(str)
hm = cm[~cm["maht_kahtlane"] & cm["id"].isin(harju_ids) & (cm.kuu >= P0) & (cm.kuu <= P1)]
hm = hm.rename(columns={"id": "koht"})
hm_cls = hm[~hm["klass_kahtlane"]]
both = pd.concat([jm[["koht", "kuu", "kokku"]], hm[["koht", "kuu", "kokku"]]])
series = {
    "ristmikud": ratio_index(jm, "kokku", site="koht").set_index("kuu")["indeks"],
    "maanteed_harju": ratio_index(hm, "kokku", site="koht").set_index("kuu")["indeks"],
    "koik_kohad": ratio_index(both, "kokku", site="koht").set_index("kuu")["indeks"],
    "maanteed_kerged": ratio_index(hm_cls, "kerge", site="koht").set_index("kuu")["indeks"],
    "maanteed_rasked": ratio_index(hm_cls, "raske", site="koht").set_index("kuu")["indeks"],
}
fuel = load_fuel_county()
fuel = fuel[fuel["maakond_full"] == "Harjumaa"].set_index("kuu")[["bensiin", "diisel"]]
fuel["kokku"] = fuel["bensiin"] + fuel["diisel"]
fidx = (fuel / fuel[fuel.index.year == TALLINN_BASE_YEAR].mean() * 100).add_prefix("kutus_")
mi = pd.DataFrame(series).join(fidx, how="inner")
mi = mi[(mi.index >= P0) & (mi.index <= P1)]
save_table(mi.reset_index(), "07_kuuindeksid")

pairs = [("ristmikud", "kutus_kokku"), ("maanteed_harju", "kutus_kokku"), ("koik_kohad", "kutus_kokku"),
         ("maanteed_kerged", "kutus_bensiin"), ("maanteed_rasked", "kutus_diisel")]
frows = []
for a_, b_ in pairs:
    a, b = np.log(mi[a_]), np.log(mi[b_])
    for kuju, fa, fb in [("tase", a, b), ("kuumuutus", a.diff(), b.diff()), ("YoY", a.diff(12), b.diff(12))]:
        frows.append(dict(liiklus=a_, kutus=b_, kuju=kuju, **corr_pair(fa, fb)))
fc = pd.DataFrame(frows)
save_table(fc, "07_kutus_korrelatsioon")
print("\nKuuindeksid vs Harjumaa kütus:")
print(fc.round(3).to_string(index=False))

fig, ax = plt.subplots(figsize=(11, 4.8))
tt_ = mi.index.to_timestamp()
for col, c, lw, lab in [("ristmikud", TEXT2, 1.6, "Tallinna ristmikud"),
                        ("maanteed_harju", C_BLUE, 1.6, "Harjumaa maanteede loendurid"),
                        ("koik_kohad", "black", 2.6, "Kõik loenduskohad koos"),
                        ("kutus_kokku", C_ORANGE, 2.6, "Harjumaa kütusemüük (bensiin + diisel)")]:
    ax.plot(tt_, mi[col], color=c, lw=lw, label=lab, ls="-" if col != "ristmikud" else "--")
ax.axhline(100, color=TEXT2, lw=0.6, ls=":")
cc = fc.set_index(["liiklus", "kuju"])["r"]
ax.set_title(f"Liiklus vs Harjumaa kütusemüük, {P0}...{P1} (kõik kohad: r = {cc[('koik_kohad', 'tase')]:.2f}, "
             f"kuumuutuste r = {cc[('koik_kohad', 'kuumuutus')]:.2f})", fontsize=11)
ax.set_ylabel(f"Indeks, {TALLINN_BASE_YEAR} = 100")
ax.legend(fontsize=8, loc="lower right", ncol=2)
save(fig, "07_07_kutus_harju")
print("Valmis.")
