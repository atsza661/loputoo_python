"""
22 - Nädalavahetuse pärastlõuna- ja õhtutipp kaardil 15 min andmetest: mis kell algab laupäeva ja pühapäeva tipptund
pärast keskpäeva ja millal liiklus pärastlõunal ja õhtul toimub igal Harjumaa maantee suunal ja Tallinna ristmikul. Sama kujundus kui 07_03_kaart_harju ja 21.

SISEND
  common.maantee_suunad(ALGUS)             maanteeloendurite suundade 15 min loendused (highway.count_15min)
  common.load_tallinn(), load_junctions()  ristmike 15 min loendused puhastatult ja koordinaadid
  common.day_calendar()                    päevatüüp (laupäev, pühapäev, riigipüha) ja koolivaheajad
  valjund/20_kaardiandmed_15min.csv        maantee suuna nimetus (linna poole / linnast välja) tööpäevade järgi (20 käib enne)
  common.timing_map()                      07 kaardifunktsioon (ortofototaust, värviskaala, sildid)

ARVUTUS
  Nädalavahetuse päev = laupäev või pühapäev õppetöö ajal, mis ei ole riigipüha, alates ALGUS (sama periood kui 20).
  Iga maantee suuna ja ristmiku profiil = 96 veerandtunni keskmine sõidukite arv eraldi laupäevade ja pühapäevade üle;
  koht läheb arvesse, kui päevi on vähemalt MIN_PAEVI ja veerandtundidest on olemas vähemalt 90% (üksik puuduv
  veerandtund interpoleeritakse). Nädalavahetusel on tipp varem kui tööpäeva õhtul: ristmikel umbes kell 13-14 ja
  pärast kella 15 liiklus ainult väheneb, seega tööpäeva õhtune aken (algus 14.00-18.59) annaks enamikul kohtadel
  akna servaväärtuse. Seepärast kasutatakse pärastlõuna ja õhtu akent AKEN = kell 12-21:
    tipptunni algus  = suurima mahuga 60 min akna algus vahemikus 12.00-20.59 (15 min täpsusega; common.peak_hour)
    liikluse keskaeg = mahuga kaalutud keskmine kellaaeg kell 12-21
    märgi suurus     = laupäeva ja pühapäeva ööpäevase liikluse keskmine
  Maantee suund on linna poole või linnast välja tööpäevade järgi (20); nädalavahetusel näidatakse mõlemat suunda, sest
  pühapäeva õhtul on põhivoog linna poole (tagasitulek), mitte välja nagu tööpäeval.

CALCULATION IN PLAIN ENGLISH
  Weekend day = Saturday or Sunday in school term, not a public holiday, from ALGUS. Profile = average vehicles per
    quarter hour, Saturdays and Sundays separately (at least MIN_PAEVI days and 90% of quarter hours; a single gap is
    filled from neighbours).
  Peak-hour start = start of the 60-minute window with the most vehicles that starts 12:00-20:59; traffic midpoint =
    vehicle-weighted average clock time 12-21; marker size = average of Saturday and Sunday daily traffic.

VÄLJUND (kaust valjund/)
  22_01_kaart_harju_tipptund.png, 22_02_kaart_tallinn_tipptund.png
      Näitab: mis kell algab laupäeva ja pühapäeva pärastlõuna- või õhtutipp igal Harjumaa maantee suunal ja Tallinna
      ristmikul (pühapäeval linna poole: tagasituleku laine).
      Kuidas: neli kaarti ortofototaustal (2 x 2): ülemises reas laupäev (lillad toonid), alumises pühapäev (oranžid
      toonid); vasakul maanteel suund linnast välja, paremal linna poole. Ristmikud (ruudud) on kõigil neljal, maantee
      suunad (ringid) oma suunaga kaardil. Värv = tipptunni algus (hilisem = tumedam; igal kaardil skaala otstes
      varaseim ja hiliseim), suurus = nädalavahetuse ööpäevane liiklus (ruutjuure skaalas).
  22_03_kaart_harju_keskaeg.png, 22_04_kaart_tallinn_keskaeg.png
      Näitab: sama liikluse keskaja järgi (kell 12-21), mis sõltub kogu pärastlõuna ja õhtu liikluse kujust.
      Kuidas: nagu eelmine, värv = liikluse keskaeg.
  22_nadalavahetuse_tipuajad.csv   iga koht: tüüp, koht, nimi, suund, koordinaadid ning laupäeva ja pühapäeva (kell 12-21)
                                   tipptunni algus, maht, liikluse keskaeg, ööpäevane liiklus ja päevade arv
"""
import numpy as np
import pandas as pd

from common import (maantee_suunad, load_tallinn, load_junctions, day_calendar, peak_hour, timing_map, bbox, ramp,
                    slot_label, set_style, save_table, umarda, OUT_DIR)

ALGUS = "2025-09-01"                 # nagu 13, 20 ja 21
MIN_PAEVI = 10                       # koht arvesse, kui laupäevi (pühapäevi) on vähemalt nii palju
KATVUS = 0.9                         # ... ja vähemalt 90% veerandtundidest on olemas
PAEVAD = {"laupaev": "laupäev", "puhapaev": "pühapäev"}
AKEN = (12, 21)                      # pärastlõuna ja õhtu: tipptunni algus 12.00-20.59, keskaeg kell 12-21


def profiilid(x, koht, v):
    """Keskmine ööpäeva profiil koha kaupa (96 veerandtundi) ja päevade arv; liiga väheste päevade või kaetusega kohad välja."""
    x = x[x.groupby(koht)["paev"].transform("nunique") >= MIN_PAEVI]
    p = x.groupby([koht, "slot"])[v].mean().unstack("slot").reindex(columns=range(96))
    return p[p.notna().mean(axis=1) >= KATVUS].interpolate(axis=1, limit_direction="both"), x.groupby(koht)["paev"].nunique()


def tipp(v):
    """Ööpäeva profiili (96 veerandtundi) tipp aknas AKEN: tipptunni algus ja maht, liikluse keskaeg ja ööpäevane liiklus."""
    s, maht = peak_hour(v, AKEN, 4)
    i = np.arange(AKEN[0] * 4, AKEN[1] * 4)
    kesk = float(np.sum((i + 0.5) / 4 * v[i]) / np.sum(v[i]))
    return dict(ooopaev=float(np.sum(v)), ohtu_algus_h=s / 4, ohtu_algus=slot_label(s), ohtu_soid_h=maht,
                ohtu_keskaeg_h=kesk, ohtu_keskaeg=slot_label(kesk * 4))


_v = np.zeros(96)
_v[64:68] = 10                                       # 16.00-17.00 kümme sõidukit veerandtunnis
assert tipp(_v)["ohtu_algus"] == "16:00" and tipp(_v)["ohtu_soid_h"] == 40 and tipp(_v)["ohtu_keskaeg"] == "16:30"

set_style()
print("Laen maanteede ja ristmike 15 min loendused...")
ds, dq = maantee_suunad(ALGUS)
dq["paevatyyp"] = dq["paev"].map(day_calendar(dq["paev"]).set_index("paev")["paevatyyp"])
tl, _ = load_tallinn()
tl = tl[tl["paev"] >= ALGUS]
d20 = pd.read_csv(OUT_DIR / "20_kaardiandmed_15min.csv", encoding="utf-8-sig")
suund = (d20[d20["tyyp"] == "maantee"].drop_duplicates("koht").set_index("koht")["suund"]
         .map({"linna poole": "sisse", "linnast välja": "välja"}))
jn = load_junctions().set_index("mp_id")

osad = []
for paev, nimi in PAEVAD.items():
    for tyyp, x, koht, v in [("maantee", dq[dq["kool"] & (dq["paevatyyp"] == nimi)], "site", "c"),
                             ("ristmik", tl[(tl["vaheaeg"] == "kool") & (tl["paevatyyp"] == nimi)], "mp_id", "v")]:
        p, n = profiilid(x, koht, v)
        m = pd.DataFrame([tipp(r.values) for _, r in p.iterrows()], index=p.index)
        osad.append(m[["ooopaev", "ohtu_algus_h", "ohtu_algus", "ohtu_soid_h", "ohtu_keskaeg_h", "ohtu_keskaeg"]]
                    .add_prefix(f"{paev}_").assign(**{f"{paev}_paevi": n}).rename_axis("koht").reset_index().assign(tyyp=tyyp))
sites = None
for paev in PAEVAD:
    o = pd.concat([x for x in osad if f"{paev}_ooopaev" in x])
    sites = o if sites is None else sites.merge(o, on=["tyyp", "koht"])           # ainult kohad, kus mõlemad päevad on olemas
mt = sites["tyyp"] == "maantee"
sites.loc[mt, "suund"] = sites.loc[mt, "koht"].map(suund)
sites = sites[~mt | sites["suund"].notna()].copy()
mt = sites["tyyp"] == "maantee"
sites.loc[~mt, "suund"] = "ristmik"
for veerg, maantee, ristmik in [("lat", ds["lat"], jn["lat"]), ("lon", ds["lon"], jn["lon"]), ("nimi", ds["nimi"], jn["name"])]:
    sites[veerg] = sites["koht"].map(maantee).where(mt, sites["koht"].map(ristmik))
sites["id"] = sites["koht"].map(lambda k: str(k)[:5]).where(mt, sites["koht"].map(jn["code"]))
sites["koht"] = (sites["nimi"] + " (" + sites["suund"] + ")").where(mt, sites["id"] + " " + sites["nimi"])
sites["ooopaev"] = sites[[f"{p}_ooopaev" for p in PAEVAD]].mean(axis=1)
save_table(sites.drop(columns=["ooopaev"]).pipe(umarda), "22_nadalavahetuse_tipuajad")
for paev, nimi in PAEVAD.items():
    for t_, s_ in [("ristmik", "ristmik"), ("maantee", "sisse"), ("maantee", "välja")]:
        s = sites[(sites["tyyp"] == t_) & (sites["suund"] == s_)]
        print(f"{nimi}, {t_} ({s_}, {len(s)}, mediaan {s[f'{paev}_paevi'].median():.0f} päeva): tipptunni algus (kell 12-21) mediaanina "
              f"{slot_label(s[f'{paev}_ohtu_algus_h'].median() * 4)} ({slot_label(s[f'{paev}_ohtu_algus_h'].min() * 4)}–"
              f"{slot_label(s[f'{paev}_ohtu_algus_h'].max() * 4)}), keskaeg {slot_label(s[f'{paev}_ohtu_keskaeg_h'].median() * 4)}")

lo0, la0, lo1, la1 = bbox(sites[sites["tyyp"] == "ristmik"], pad=0.04)       # Tallinna kaardi ala nagu 07 ja 21
linnas = sites[sites["lon"].between(lo0, lo1) & sites["lat"].between(la0, la1)]
for i, (naitaja, sona) in enumerate([("algus", "tipptund"), ("keskaeg", "keskaeg")]):   # joonised 22_01 ... 22_04
    aken = {"algus": "tipptunni algus 12.00-20.59", "keskaeg": "liikluse keskaeg 12-21"}[naitaja]
    paneelid = [("laupaev_ohtu", "välja", ramp("Purples"), f"Laupäev, {aken} (maanteel: linnast välja)"),
                ("laupaev_ohtu", "sisse", ramp("Purples"), f"Laupäev, {aken} (maanteel: linna poole)"),
                ("puhapaev_ohtu", "välja", ramp("Oranges"), f"Pühapäev, {aken} (maanteel: linnast välja)"),
                ("puhapaev_ohtu", "sisse", ramp("Oranges"), f"Pühapäev, {aken} (maanteel: linna poole)")]
    pealkiri = {"algus": "Millal algab nädalavahetuse pärastlõuna- ja õhtutipp",
                "keskaeg": "Millal liiklus nädalavahetuse pärastlõunal ja õhtul toimub: mahuga kaalutud keskmine kellaaeg"}[naitaja]
    timing_map(sites, f"22_{2 * i + 1:02d}_kaart_harju_{sona}", f"{pealkiri} (15 min loendused, õppetöö aja nädalavahetused; suurus = "
               "ööpäevane liiklus)", label_junctions=False, size_k=1.3, naitaja=naitaja, paneelid=paneelid)
    timing_map(linnas, f"22_{2 * i + 2:02d}_kaart_tallinn_{sona}", f"Tallinna ristmikud ({(linnas['tyyp'] == 'ristmik').sum()}): "
               f"{pealkiri[0].lower() + pealkiri[1:]} (15 min loendused)", label_junctions=True, size_k=0.8, naitaja=naitaja,
               paneelid=paneelid)
print("Valmis.")
