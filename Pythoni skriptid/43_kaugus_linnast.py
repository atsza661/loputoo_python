"""
43 - Liiklussagedus tee aadressi (km) järgi: Tallinna ristmike harud ja Tallinna lähedased maanteeloendurid samal
nädalal, nagu Transpordiameti baasprognoosi joonis 2.12 "AKÖL linnalähedastel kõrvalmaanteedel" (Kaal, Metsvahi ja
Kendra 2020, lk 24: linnapiirist eemaldudes liiklussagedus väheneb üsna kiiresti, tagamaa üle 10-15 km on harukordne).
Kolm joonist: linn, maantee ja mõlemad koos neil riigiteedel, mis jätkuvad linnast maanteeks (sama tee number ja km).

SISEND
  common.load_vehicles()      logija nädala sõidukid (tallinn.vehicle_passage), ristmiku täispäevad (tervetel_paevadel)
  common.load_manoeuvres()    kanali lähte- ja sihtharu (T08)
  common.ristmike_harud()     haru tee number ja aadress teeregistris (Transpordiameti teeregistri WFS-teenus)
  common.load_daily()         maanteeloendurite päevasummad kanali kaupa (highway.count_hourly)
  common.load_locations()     maanteeloenduri tee number ja aadress (tee_nr, tee_km)

ARVUTUS
  NKÖL = nädala keskmine ööpäevane liiklussagedus, mõlemad suunad kokku (a/ööp; Kaal jt 2020 lk 2, AKÖL = NKÖL / NT
     lk 38), nädal 16.-22.10.2026 (R-N, seitse päeva, koolivaheaega ega riigipühi pole): NKÖL = (5 x tööpäevade
     keskmine + 2 x nädalavahetuse keskmine) / 7, kui mõlemast on vähemalt üks täispäev (puuduv päev ei nihuta
     tulemust tööpäevade või nädalavahetuse poole). AKÖL-iks teisendust (nädalategur NT) ei tehta: kõik punktid on
     samast nädalast, seega on nad omavahel võrreldavad.
  Linna haru: haru kaudu ristmikule sisenevad (T08 lähteharu) + väljuvad (sihtharu) sõidukid. Ainult ristmikud, kus
     igal sõidukitega kanalil on lähte- ja sihtharu teada, ja harud, mille kaudu loendatakse nii sisse- kui
     väljasõitu (ühepoolne haru, nt MP48 Pronksi ainult Kunderi poole, annaks kahe suuna mahuks ühe suuna osa).
     Ristmik loendab ainult T08 suundades olevaid manöövreid (nt MP17 ainult otse), seega võib haru NKÖL olla
     tegelikust väiksem. Riigiteed 1 ja 2 kattuvad teeregistris km 0-2,8; seal on haru mõlema tee joonel.
  Maanteeloendur: kõik kanalid (mõlemad suunad), päev arvesse, kui kõik loenduri kanalid on kehtivad (load_daily).
     Tallinna lähedal = kuni 40 km linnulennult Viru väljakust (riigiteede 1, 2, 4 ja 8 km 0): joonis 2.12 ulatub
     25 km linnapiirist ja linnapiir on Viru väljakust 10-15 km kaugusel.
  x = aadress teel, km (teeregistri meeter / 1000). Riigitee, mis algab linnas (1, 2, 4, 8, 15, 11250, 11290, 11340,
     11390), saab linnas sama aadressi kui maanteel, seega on linna harud ja maanteeloendurid ühel teljel.

CALCULATION IN PLAIN ENGLISH
  Weekly average daily traffic (both directions) = (5 x average workday + 2 x average weekend day) / 7 over
  16-22 Oct 2026. A city leg = vehicles entering the junction from the leg + vehicles leaving into it; only junctions
  where every counted lane has a known start and end leg. A highway counter = all lanes, days with every lane valid.
  The x axis is the road address (km) from the road register, so a national road continues from city to highway.

VÄLJUND (joonised kaustas Graafikud/, tabelid kaustas valjund/)
  43_01_linn.png
      Mida: iga linna ristmiku haru NKÖL tee aadressi järgi.
      Kuidas: x = km teel, y = NKÖL (a/ööp); joon ühendab sama tee (tänava) harud. Värviline = riigitee, mis jätkub
      maanteena (sama värv kõigil joonistel), hall = linnatänav. Silt joone lõpus = tee või tänav.
      Näitab: kas liiklus kasvab kesklinna poole ja millised tänavad on koormatumad.
  43_02_maantee.png
      Mida: Tallinna lähedaste maanteeloendurite NKÖL tee aadressi järgi (nagu joonis 2.12).
      Kuidas: x = km teel, y = NKÖL; joon tee kaupa, värv nagu 43_01. Tühi ring = teadaoleva rikkega loendur.
      Näitab: kui kiiresti liiklus linnast eemaldudes väheneb.
  43_03_linn_ja_maantee.png
      Mida: riigiteed, millel on nii linna haru kui maanteeloendur.
      Kuidas: x = km teel, y = NKÖL; ruut = linna ristmiku haru, ring = maanteeloendur, joon tee kaupa.
      Näitab: kas linnast maanteele on liiklussageduses hüpe või sujuv muutus.
  43_nkol.csv   punkt (linna haru või maanteeloendur): tee, tee_nimi, km, NKÖL, päevi, märkus
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import (load_vehicles, tervetel_paevadel, load_manoeuvres, ristmike_harud, haru, load_daily, load_locations,
                    km, set_style, save, save_table, C_BLUE, C_ORANGE, C_AQUA, C_YELLOW, C_MAGENTA, C_GREEN,
                    C_VIOLET, C_RED, C_GRAY, TEXT2)

NADAL = ("2026-10-16", "2026-10-23")      # 16.-22.10.2026 (lõpp mitte kaasa), seitse päeva
VIRU = (59.4372, 24.7533)                 # riigiteede 1, 2, 4 ja 8 algus (teeregistri km 0)
LAHEDAL_KM = 40                           # maanteeloendur kuni 40 km Viru väljakust (vt ARVUTUS)
RIKKED = {"74018": "Kanama: Tallinn->Pärnu 2. rada loendab alates 12.2025 liiga vähe"}
TEE_VARV = dict(zip(["1", "2", "4", "8", "15", "11290", "11340", "11390"],
                    [C_BLUE, C_ORANGE, C_AQUA, C_YELLOW, C_MAGENTA, C_GREEN, C_VIOLET, C_RED]))


def nkol(d, vaartus):
    """NKÖL veergudest paev ja vaartus (üks rida päeva kohta): (5 x E-R keskmine + 2 x L-P keskmine) / 7."""
    nv = d["paev"].dt.day_of_week >= 5
    return pd.Series({"nkol": (5 * d.loc[~nv, vaartus].mean() + 2 * d.loc[nv, vaartus].mean()) / 7,
                      "paevi": d["paev"].nunique()})


_t = pd.DataFrame({"paev": pd.date_range("2026-10-16", "2026-10-22"), "x": [10, 4, 4, 10, 10, 10, 10.]})
assert np.isclose(nkol(_t, "x")["nkol"], 58 / 7) and np.isnan(nkol(_t[_t["x"] > 5], "x")["nkol"])   # nädalavahetuseta: NaN

set_style()

# --- Maanteeloendurid ---------------------------------------------------------------------------------------
loc = load_locations()
loc = loc[km(*VIRU, loc["latitude"], loc["longitude"]) <= LAHEDAL_KM].copy()
loc["tee"] = loc["tee_nr"].astype(int).astype(str)
d = load_daily()
d = d[d["id"].isin(loc["id"]) & (d["paev"] >= NADAL[0]) & (d["paev"] < NADAL[1])]
kanaleid = d.groupby("id")["kanal"].nunique()
p = d.groupby(["id", "paev"]).agg(kehtivaid=("kehtiv", "sum"), maht=("kokku", "sum")).reset_index()
p = p[p["kehtivaid"] == p["id"].map(kanaleid)]
mt = p.groupby("id").apply(nkol, "maht", include_groups=False).reset_index().merge(loc, on="id")
mt = mt.assign(liik="maantee", koht=mt["nimi"], km=mt["tee_km"], tee_nimi=mt["tee_nimi"].str.title(),
               markus=mt["id"].map(RIKKED).fillna(""))
print(f"Maanteeloendureid {len(loc)} (kuni {LAHEDAL_KM} km), NKÖL olemas {mt['nkol'].notna().sum()}")

# --- Linna ristmike harud -------------------------------------------------------------------------------------
print("Laen sõidukipõhised loendused...")
v = tervetel_paevadel(load_vehicles(None))
v = v[(v["ts"] >= NADAL[0]) & (v["ts"] < NADAL[1])]
dm = load_manoeuvres()
dm = dm.assign(mp_id=dm["mp"].str[2:].astype(int), lahe=dm["from_leg"].map(lambda s: haru(s)[1]),
               siht=dm["to_leg"].map(lambda s: haru(s)[1])).rename(columns={"channel": "kanal"})
k = (v.groupby(["mp_id", "kanal", v["ts"].dt.normalize().rename("paev")]).size().rename("n").reset_index()
     .merge(dm[["mp_id", "kanal", "lahe", "siht"]], on=["mp_id", "kanal"], how="left"))
terve = k.groupby("mp_id")[["lahe", "siht"]].agg(lambda s: s.notna().all()).all(axis=1)
print(f"Ristmikke {k['mp_id'].nunique()}, kõigi kanalite harud teada {terve.sum()}; välja: "
      + ", ".join(f"MP{i:02d}" for i in terve.index[~terve]))
k = k[k["mp_id"].map(terve)]
hp = pd.concat([k.rename(columns={"lahe": "haru"}).assign(pool="sisse"), k.rename(columns={"siht": "haru"}).assign(pool="välja")])
kahepoolne = hp.groupby(["mp_id", "haru"])["pool"].nunique() == 2    # haru kaudu loendatakse nii sisse- kui väljasõitu
print(f"Harusid {len(kahepoolne)}, neist mõlemas suunas loendatud {kahepoolne.sum()} (ühepoolsed välja: "
      + ", ".join(f"MP{m:02d} {h}" for m, h in kahepoolne.index[~kahepoolne]) + ")")
hp = hp[pd.MultiIndex.from_frame(hp[["mp_id", "haru"]]).isin(kahepoolne.index[kahepoolne])]
hp = hp.groupby(["mp_id", "haru", "paev"])["n"].sum().unstack("paev")
koik = k.groupby(["mp_id", "paev"]).size().unstack("paev").notna()             # ristmiku täispäevad
hp = hp.fillna(0).where(koik.reindex(index=hp.index.get_level_values("mp_id"), columns=hp.columns).to_numpy())
hp = hp.stack().dropna().rename("maht").reset_index()                             # täispäeval puuduv haru = 0

riigiteed = sorted(loc["tee"].unique(), key=int)
harud = ristmike_harud(riigiteed)
lt = (hp.groupby(["mp_id", "haru"]).apply(nkol, "maht", include_groups=False).reset_index()
      .merge(harud, on=["mp_id", "haru"], how="left"))
lt = lt.assign(liik="linn", koht=lt["mp"] + " " + lt["haru"] + " " + lt["tanav"], km=lt["meeter"] / 1000, markus="")
print(f"Linna harusid {len(lt)}, neist teeregistri aadressiga {lt['tee'].notna().sum()}; aadressita: "
      + ", ".join(lt.loc[lt["tee"].isna(), "koht"]))

# --- Tabel --------------------------------------------------------------------------------------------------
tab = pd.concat([lt, mt])[["liik", "koht", "tee", "tee_nimi", "km", "nkol", "paevi", "kiirus_piir", "markus"]]
tab = tab.dropna(subset=["tee", "nkol"]).sort_values(["tee", "km"], key=lambda s: s.map(str) if s.name == "tee" else s)
save_table(tab.round({"km": 3, "nkol": 0}), "43_nkol")
uhised = sorted(set(tab.loc[tab["liik"] == "linn", "tee"]) & set(tab.loc[tab["liik"] == "maantee", "tee"]), key=int)
print("Riigiteed linnas ja maanteel:", ", ".join(uhised))


# --- Joonised -----------------------------------------------------------------------------------------------
def joonis(df, pealkiri, nimi, markerid):
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for tee, g in df.groupby("tee"):
        g = g.sort_values("km")
        varv = TEE_VARV.get(tee, C_GRAY)
        hall = tee not in TEE_VARV
        ax.plot(g["km"], g["nkol"], color=varv, lw=0.8 if hall else 1.6, alpha=0.6 if hall else 1, zorder=1 if hall else 2)
        for liik, m in markerid.items():
            x = g[g["liik"] == liik]
            rike = x["markus"] != ""
            ax.scatter(x["km"], x["nkol"], marker=m, s=22 if hall else 34, color=varv, edgecolor="white", lw=0.6,
                       zorder=3, alpha=0.7 if hall else 1)
            ax.scatter(x.loc[rike, "km"], x.loc[rike, "nkol"], marker=m, s=60, facecolor="white", edgecolor=varv,
                       lw=1.2, zorder=4)
        silt = g["tee_nimi"].iloc[-1] if hall else f"mnt nr {tee}"
        yles = len(g) == 1 and not hall          # üksik riigitee punkt: silt punkti kohale, mitte naabri sildile
        ax.annotate(silt, (g["km"].iloc[-1], g["nkol"].iloc[-1]), xytext=(0, 6) if yles else (4, 0),
                    textcoords="offset points", fontsize=7 if hall else 8.5, color=TEXT2 if hall else varv,
                    ha="center" if yles else "left", va="bottom" if yles else "center",
                    fontweight="normal" if hall else "bold")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Aadress teel, km (teeregister)")
    ax.set_ylabel("NKÖL, a/ööp (mõlemad suunad)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", " ")))
    ax.set_title(pealkiri)
    kasutatud = [(liik, m) for liik, m in markerid.items() if (df["liik"] == liik).any()]
    tahis = [plt.Line2D([], [], marker=m, ls="", color=C_GRAY, ms=7,
                        label={"linn": "linna ristmiku haru", "maantee": "maanteeloendur"}[liik]) for liik, m in kasutatud]
    if (df["markus"] != "").any():
        tahis.append(plt.Line2D([], [], marker="o", ls="", mfc="white", mec=C_GRAY, ms=8, label="teadaolev rike"))
    ax.legend(handles=tahis, loc="upper right", fontsize=9)
    fig.text(0.01, -0.01, "NKÖL 16.-22.10.2026 = (5 x tööpäev + 2 x nädalavahetuse päev) / 7. Värviline = riigitee, "
             "mis jätkub linnast maanteeks; hall = muu tee või tänav.", fontsize=8, color=TEXT2)
    save(fig, nimi)


MARK = {"linn": "s", "maantee": "o"}
joonis(tab[tab["liik"] == "linn"], "Tallinna ristmike harude liiklussagedus tee aadressi järgi", "43_01_linn", MARK)
joonis(tab[tab["liik"] == "maantee"], "Tallinna lähedaste maanteeloendurite liiklussagedus tee aadressi järgi",
       "43_02_maantee", MARK)
joonis(tab[tab["tee"].isin(uhised)], "Linnast maanteeks jätkuvad riigiteed: liiklussagedus tee aadressi järgi",
       "43_03_linn_ja_maantee", MARK)
print("Valmis.")
