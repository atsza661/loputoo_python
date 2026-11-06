"""
21 - Tipuajad kaardil 15 min andmetest: millal on tavalisel tööpäeval tipptund ja liikluse keskaeg igal maantee
suunal ja Tallinna ristmikul. Sama kujundus kui 07_03_kaart_harju, aga kõik punktid tulevad oma 15 min loendustest
(maanteel highway.count_15min, ristmikel seire 15 min loendused), mitte tunniprofiilist ega DATEX-ist.

SISEND
  valjund/20_kaardiandmed_15min.csv   skripti 20 tabel (20 käib enne): iga maantee suuna ja ristmiku tavalise tööpäeva
                                      vool iga veerandtunni kohta (E-R õppetöö ajal alates 01.09.2025), koordinaadid ja
                                      maanteel suund (linna poole / linnast välja)
  common.timing_map()                 07 kaardifunktsioon (ortofototaust, värviskaala, sildid)

ARVUTUS
  Iga koha ööpäeva profiil = 96 veerandtunni keskmine sõidukite arv (vool / 4); üksik puuduv veerandtund
  interpoleeritakse naabritest. Tipunäitajad (common.peak_metrics, nagu 06 ja 07):
    tipptunni algus   = suurima mahuga 60 min akna algus, hommikul 06.00-09.59 ja õhtul 14.00-18.59 (15 min täpsusega)
    liikluse keskaeg  = mahuga kaalutud keskmine kellaaeg aknas, hommikul 06-10 ja õhtul 15-19
    ööpäevane liiklus = profiili summa (märgi suurus)
  Hommikukaardil on maanteel suund linna poole, õhtukaardil linnast välja (nagu 07); ristmikud on mõlemal.

CALCULATION IN PLAIN ENGLISH
  Daily profile of each place = average vehicles in each of the 96 quarter hours (flow / 4); a single missing quarter
    hour is filled from its neighbours.
  Peak-hour start = start of the 60-minute window with the most vehicles, 06:00-09:59 or 14:00-18:59.
  Traffic midpoint = average clock time weighted by vehicles, 06-10 and 15-19.
  Marker size = daily traffic = sum of the profile.

VÄLJUND (kaust valjund/)
  21_01_kaart_harju_tipptund.png, 21_02_kaart_tallinn_tipptund.png
      Näitab: mis kell algab tipptund igal Harjumaa maantee suunal ja Tallinna ristmikul.
      Kuidas: kaks kaarti ortofototaustal - hommik (maanteel sissesõit linna, sinised toonid) ja õhtu (maanteel
      väljasõit, oranžid toonid). Ruut = ristmik, ring = maantee suund. Värv = tipptunni algus (hilisem = tumedam;
      värviskaala otstes varaseim ja hiliseim), suurus = ööpäevane liiklus (ruutjuure skaalas); maanteeloendurid on
      nimega, Tallinna kaardil ka ristmikud koodiga.
  21_03_kaart_harju_keskaeg.png, 21_04_kaart_tallinn_keskaeg.png
      Näitab: sama liikluse keskaja järgi, mis on tipu algusest sujuvam näitaja (sõltub kogu tipu kujust).
      Kuidas: nagu eelmine, värv = liikluse keskaeg.
  21_tipuajad.csv   iga koht: tüüp, koht, nimi, suund, koordinaadid, ööpäevane liiklus, hommikuse ja õhtuse tipptunni
                    algus ja maht ning liikluse keskaeg
"""
import numpy as np
import pandas as pd

from common import OUT_DIR, peak_metrics, timing_map, bbox, set_style, save_table, umarda, slot_label

set_style()
d = pd.read_csv(OUT_DIR / "20_kaardiandmed_15min.csv", encoding="utf-8-sig")
d["slot"] = d["kell"].str[:2].astype(int) * 4 + d["kell"].str[3:5].astype(int) // 15
v = d.pivot_table(index=["tyyp", "koht"], columns="slot", values="vool_soid_h").reindex(columns=range(96)) / 4
v = v.interpolate(axis=1, limit_direction="both")
info = d.drop_duplicates(["tyyp", "koht"]).set_index(["tyyp", "koht"])[["nimi", "suund", "lat", "lon"]]
sites = pd.DataFrame([dict(tyyp=t, koht0=k, **peak_metrics(p.values, per_hour=4)) for (t, k), p in v.iterrows()])
sites = sites.join(info, on=["tyyp", "koht0"])
sites["suund"] = sites["suund"].map({"linna poole": "sisse", "linnast välja": "välja"}).fillna("ristmik")
sites["id"] = np.where(sites["tyyp"] == "ristmik", sites["koht0"], sites["koht0"].str[:5])
sites["koht"] = np.where(sites["tyyp"] == "ristmik", sites["koht0"] + " " + sites["nimi"].fillna(""),
                         sites["nimi"].fillna("") + " (" + sites["suund"] + ")")
save_table(sites[["tyyp", "koht0", "nimi", "suund", "lat", "lon", "ooopaev", "hommik_algus", "hommik_soid_h", "hommik_keskaeg",
                  "ohtu_algus", "ohtu_soid_h", "ohtu_keskaeg"]].rename(columns={"koht0": "koht"}).pipe(umarda), "21_tipuajad")
for tyyp, suund, aeg in [("ristmik", "ristmik", "hommik"), ("maantee", "sisse", "hommik"), ("ristmik", "ristmik", "ohtu"),
                         ("maantee", "välja", "ohtu")]:
    s = sites[(sites["tyyp"] == tyyp) & (sites["suund"] == suund)]
    print(f"{tyyp} ({suund}, {len(s)}): {aeg} tipptunni algus mediaanina {slot_label(s[f'{aeg}_algus_h'].median() * 4)}, "
          f"vahemik {slot_label(s[f'{aeg}_algus_h'].min() * 4)}–{slot_label(s[f'{aeg}_algus_h'].max() * 4)}; keskaeg "
          f"{slot_label(s[f'{aeg}_keskaeg_h'].median() * 4)}")

lo0, la0, lo1, la1 = bbox(sites[sites["tyyp"] == "ristmik"], pad=0.04)       # Tallinna kaardi ala nagu 07
linnas = sites[sites["lon"].between(lo0, lo1) & sites["lat"].between(la0, la1)]
for i, (naitaja, sona) in enumerate([("algus", "tipptund"), ("keskaeg", "keskaeg")]):   # joonised 21_01 ... 21_04
    pealkiri = {"algus": "Millal algab tipptund", "keskaeg": "Millal liiklus toimub: mahuga kaalutud keskmine kellaaeg"}[naitaja]
    timing_map(sites, f"21_{2 * i + 1:02d}_kaart_harju_{sona}", f"{pealkiri} (15 min loendused, tavaline tööpäev; suurus = ööpäevane liiklus)",
               label_junctions=False, size_k=1.3, naitaja=naitaja)
    timing_map(linnas, f"21_{2 * i + 2:02d}_kaart_tallinn_{sona}", f"Tallinna ristmikud ({(linnas['tyyp'] == 'ristmik').sum()}): {pealkiri.lower()} "
               "(15 min loendused, tavaline tööpäev)", label_junctions=True, size_k=0.8, naitaja=naitaja)
print("Valmis.")
