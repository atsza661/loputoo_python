"""
20 - Kõik 15 min andmepunktid kaardil: tavalise tööpäeva iga veerandtund (00.00-23.45) maanteeloendurite suundadel ja
Tallinna ristmikel, kaart iga veerandtunni kohta.

SISEND
  common.maantee_suunad(ALGUS)             maanteeloendurite suundade 15 min loendused (highway.count_15min):
                                           sõidukite arv ja kiirused; pikk ajalugu on Harjumaa loenduritel (5-37 km
                                           Tallinnast), teistel üksikud päevad, seega kaardil on Harjumaa loendurid
  common.load_tallinn(), load_junctions()  ristmike 15 min loendused puhastatult (seire.tallinn.ee) ja koordinaadid
  common.add_basemap()                     ortofototaust (internetita joonistatakse ilma)

ARVUTUS
  Tavaline tööpäev = E-R õppetöö ajal, mitte riigipüha ega lühendatud tööpäev, alates ALGUS (sama periood kui 13).
  Maantee suund või ristmik läheb kaardile, kui tavalisi tööpäevi on vähemalt MIN_PAEVI ja ööpäeva veerandtundidest
  on olemas vähemalt 90%.
    vool      = veerandtunni keskmine sõidukite arv üle tavaliste tööpäevade x 4 (sõidukit tunnis)
    koormus   = vool / sama koha tavalise tööpäeva suurim veerandtund x 100 (0-100%): kui lähedal on koht oma tipule
    aeglane   = ainult maanteel (ristmikel kiirust 15 min andmetes pole): veerandtund on aeglane, kui keskmine kiirus on
                <= 70% loenduri tavakiirusest (kell 06-20 mediaan) või vähemalt pool sõidukitest sõidab alla 40 km/h
                (sama määratlus mis 13); kaardil märgitakse, kui see juhtub vähemalt 25% tavalistest tööpäevadest
    suund     = loenduri kahest suunast see, mille hommikune (06-10) osakaal ööpäevast on suurem, on "linna poole"
                (nagu 13 sissesuund); ühe suunaga loenduril otsustab hommiku ja õhtu (15-19) osakaalu vahe märk
  ponytail: kolmnurk osutab Tallinna keskuse poole või sealt eemale (mitte mööda teed) ja on nihutatud sõidusuunast
  paremale, et kaks suunda ei kataks teineteist; tee täpse suuna jaoks oleks vaja tee geomeetriat.

CALCULATION IN PLAIN ENGLISH
  Typical workday = Monday-Friday in school term, not a public holiday or shortened day, from ALGUS. A place is shown
    when it has at least MIN_PAEVI such days and at least 90% of the day's quarter hours.
  Flow = average vehicles in the quarter hour over those days x 4 (vehicles per hour).
  Load = flow / the same place's largest quarter-hour flow on a typical day x 100 (0-100%).
  Slow (highways only) = mean speed <= 70% of the counter's usual speed (median 06-20) or at least half the vehicles
    below 40 km/h; marked when that happens on at least 25% of typical days.
  Direction: of the two directions of a highway counter, the one with the larger morning (06-10) share of the day is
    "towards the city".

VÄLJUND (kaust valjund/)
  20_01_harju_00-06.png, 20_02_harju_06-12.png, 20_03_harju_12-18.png, 20_04_harju_18-24.png
      Näitab: kuidas tavalise tööpäeva liiklus Harjumaa maanteedel ja Tallinna ristmikel veerandtund-veerandtunni haaval
      tõuseb ja langeb - kõik 96 veerandtundi neljal joonisel.
      Kuidas: igal joonisel 24 kaarti (6 rida x 4 veergu), üks iga veerandtunni kohta (pealkiri = veerandtunni algus),
      ortofototaustal. Kolmnurk = maanteeloenduri suund, osutab linna poole või linnast välja; ruut = ristmik. Värv =
      koormus, % koha enda tipust (heledast kollasest 0% tumepunaseni 100%; ühine värviskaala paremal), suurus = vool
      (ruutjuure skaalas). Punase äärega kolmnurk = maantee suund, kus liiklus on sel veerandtunnil aeglane vähemalt 25%
      tavalistest tööpäevadest.
  20_05_tallinn_00-06.png ... 20_08_tallinn_18-24.png
      Näitab: sama Tallinna ristmike alal (kõigi ristmike ümbris), kus ristmikud ei kattu.
      Kuidas: nagu eelmine, ainult kaart on Tallinna lähivaade ja märgid on suuremad.
  20_kaardiandmed_15min.csv   iga koht ja veerandtund: tüüp, koht, nimi, suund, koordinaadid, kellaaeg, vool sõidukit
                              tunnis, koormus %, mediaankiirus ja aeglaste päevade osakaal (maanteel); 21 kasutab seda
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D

from common import (maantee_suunad, load_tallinn, load_junctions, add_basemap, to_merc, slot_label, set_style, save,
                    save_table, umarda, C_RED, TEXT2)

ALGUS = "2025-09-01"                 # nagu 13: viimane õppeaasta kuni andmete lõpuni
MIN_PAEVI = 20                       # koht kaardile, kui tavalisi tööpäevi on vähemalt nii palju
KATVUS = 0.9                         # ... ja vähemalt 90% veerandtundidest on olemas
AEGLUS, SEISAK_OSA, MIN_SOID = 0.7, 0.5, 20       # aeglase veerandtunni määratlus nagu 13
AEGLANE_OSA = 0.25                   # kaardil punane äär, kui aeglane vähemalt 25% tavalistest tööpäevadest
KESKUS = (24.7454, 59.4372)          # Tallinna keskus (lon, lat), nagu 07 ja 13
OSAD = [(0, 6), (6, 12), (12, 18), (18, 24)]       # ühe joonise kellaajad: 6 tundi = 24 veerandtundi
CMAP = plt.get_cmap("YlOrRd")
NORM = Normalize(0, 100)


def nihked(lon, lat, linna_poole, ulatus):
    """Kolmnurga asukoht ja pööre Web Mercatoris: suund osutab Tallinna keskuse poole (linna_poole) või sealt eemale, märk on
    nihutatud sõidusuunast paremale `ulatus` meetrit. Tagastab (x, y, nurk kraadides põhjast vastupäeva)."""
    x, y = to_merc(lon, lat)
    cx, cy = to_merc(*KESKUS)
    ux, uy = cx - x, cy - y
    n = np.hypot(ux, uy)
    s = np.where(linna_poole, 1.0, -1.0)
    tx, ty = ux / n * s, uy / n * s                   # sõidusuund (ühikvektor)
    return x + ty * ulatus, y - tx * ulatus, np.degrees(np.arctan2(-tx, ty))


_x, _y, _a = nihked(np.array([24.7454, 24.7454]), np.array([59.3, 59.3]), np.array([True, False]), 100.0)
assert abs(_a[0]) < 1e-6 and abs(abs(_a[1]) - 180) < 1e-6           # keskusest lõunas: linna poole = põhja, välja = lõunasse
assert _x[0] > to_merc(24.7454, 59.3)[0] > _x[1]                    # põhja sõites on parem käsi idas

set_style()
plt.rcParams["savefig.dpi"] = 130     # 24 ortofotokaarti joonisel: 200 dpi annaks ~18 MB faili
print("Laen maanteede ja ristmike 15 min loendused...")
# --- Maanteed: tavalise tööpäeva vool, kiirus ja aeglus veerandtunni kaupa ------------------------------------
ds, dq = maantee_suunad(ALGUS)
t = dq[dq["toopaev"]].copy()
t = t[t.groupby("site")["paev"].transform("nunique") >= MIN_PAEVI]
t["kiirus"] = t["ks"] / t["kn"].where(t["kn"] >= MIN_SOID)
t["a40"] = t["alla40"] / t["kn"].where(t["kn"] >= MIN_SOID)
t["aeglane"] = (t["kiirus"] <= AEGLUS * t["site"].map(t[t["slot"].between(24, 79)].groupby("site")["kiirus"].median())) \
    | (t["a40"] >= SEISAK_OSA)
g = t.groupby(["site", "slot"])
mt = pd.DataFrame({"vool": g["c"].mean() * 4, "kiirus": g["kiirus"].median(), "aeglane_osa": g["aeglane"].mean()}).reset_index()
vool_m = mt.pivot(index="site", columns="slot", values="vool").reindex(columns=range(96))
vool_m = vool_m[vool_m.notna().mean(axis=1) >= KATVUS]
osa = lambda a, b: vool_m.loc[:, a * 4:b * 4 - 1].sum(axis=1) / vool_m.sum(axis=1)
sk = ds.loc[vool_m.index, ["id", "nimi", "lahte", "siht", "lat", "lon"]].assign(laine=osa(6, 10) - osa(15, 19))
mitu = sk.groupby("id")["laine"].transform("size") > 1
sk["linna_poole"] = np.where(mitu, sk["laine"] == sk.groupby("id")["laine"].transform("max"), sk["laine"] > 0)
mt = mt[mt["site"].isin(sk.index)].copy()
mt["koormus"] = mt["vool"] / mt["site"].map(mt.groupby("site")["vool"].max()) * 100

# --- Ristmikud: tavalise tööpäeva vool veerandtunni kaupa ---------------------------------------------------------
tl, _ = load_tallinn()
tt = tl[(tl["paevatyyp"] == "tööpäev") & (tl["vaheaeg"] == "kool") & (tl["paev"] >= ALGUS)]
tt = tt[tt.groupby("mp_id")["paev"].transform("nunique") >= MIN_PAEVI]
jp = tt.groupby(["mp_id", "slot"])["v"].mean().unstack("slot").reindex(columns=range(96))
jp = jp[jp.notna().mean(axis=1) >= KATVUS]
jn = load_junctions().set_index("mp_id").loc[jp.index]
jv, jk = jp * 4, jp.div(jp.max(axis=1), axis=0) * 100
paevi_mt, paevi_j = t["paev"].nunique(), tt["paev"].nunique()
print(f"Maantee suundi {len(sk)} ({sk['id'].nunique()} loendurit, {paevi_mt} tavalist tööpäeva), ristmikke {len(jp)} "
      f"({paevi_j} tavalist tööpäeva)")

# --- Tabel: kõik punktid ----------------------------------------------------------------------------------------------
kell = {s: slot_label(s) for s in range(96)}
save_table(pd.concat([
    mt.join(sk, on="site").assign(tyyp="maantee", koht=lambda z: z["site"],
                                  suund=lambda z: np.where(z["linna_poole"], "linna poole", "linnast välja"),
                                  aeglane_osa_pct=lambda z: z["aeglane_osa"] * 100),
    pd.DataFrame({"tyyp": "ristmik", "koht": jn.loc[jv.stack().index.get_level_values(0), "code"].values,
                  "nimi": jn.loc[jv.stack().index.get_level_values(0), "name"].values, "suund": "",
                  "lat": jn.loc[jv.stack().index.get_level_values(0), "lat"].values,
                  "lon": jn.loc[jv.stack().index.get_level_values(0), "lon"].values,
                  "slot": jv.stack().index.get_level_values(1), "vool": jv.stack().values, "koormus": jk.stack().values})])
           .assign(kell=lambda z: z["slot"].map(kell))
           [["tyyp", "koht", "nimi", "suund", "lat", "lon", "kell", "vool", "koormus", "kiirus", "aeglane_osa_pct"]]
           .rename(columns={"vool": "vool_soid_h", "koormus": "koormus_pct", "kiirus": "kiirus_kmh"}).pipe(umarda),
           "20_kaardiandmed_15min")

# --- Kaardid -----------------------------------------------------------------------------------------------------------
V = mt.set_index(["site", "slot"])


def ulatus(df, pad):
    """Kaardi ala (lon0, lat0, lon1, lat1): punktide ümbris + äär, all lisaruum mõõtkavale."""
    lo0, lo1, la0, la1 = df["lon"].min(), df["lon"].max(), df["lat"].min(), df["lat"].max()
    dx, dy = (lo1 - lo0) * pad, (la1 - la0) * pad
    return lo0 - dx, la0 - 2 * dy, lo1 + dx, la1 + dy


def paneel(ax, slot, ext, k, nihe, viide):
    """Üks veerandtund ühel kaardil: ristmikud ruutudena, maantee suunad kolmnurkadena (värv = koormus, suurus = vool).
    k = (kolmnurga, ruudu) suurustegur: märgi pindala = sqrt(vool) x tegur."""
    att = add_basemap(ax, *ext)
    if not viide:                                     # allikaviide ainult ühel paneelil joonise kohta
        for tx in [x for x in ax.texts if x.get_text() == att]:
            tx.remove()
    lon0, lat0, lon1, lat1 = ext
    jsee = jn["lon"].between(lon0, lon1) & jn["lat"].between(lat0, lat1)
    jx, jy = to_merc(jn.loc[jsee, "lon"].values, jn.loc[jsee, "lat"].values)
    ax.scatter(jx, jy, c=CMAP(NORM(jk.loc[jsee, slot].values)), s=np.sqrt(jv.loc[jsee, slot].values) * k[1], marker="s",
               edgecolor="black", linewidth=0.4, zorder=5)
    msee = sk["lon"].between(lon0, lon1) & sk["lat"].between(lat0, lat1)
    s = sk[msee]
    x, y, nurk = nihked(s["lon"].values, s["lat"].values, s["linna_poole"].values, nihe)
    v = V.reindex(pd.MultiIndex.from_arrays([s.index, np.full(len(s), slot)]))
    aegl = v["aeglane_osa"].values >= AEGLANE_OSA
    for nk in np.unique(np.round(nurk / 5) * 5):      # sama pöördega kolmnurgad ühe kutsega
        i = np.round(nurk / 5) * 5 == nk
        ax.scatter(x[i], y[i], c=CMAP(NORM(np.nan_to_num(v["koormus"].values[i]))), s=np.sqrt(np.nan_to_num(v["vool"].values[i])) * k[0],
                   marker=(3, 0, nk), edgecolor=np.where(aegl[i], C_RED, "black"), linewidth=np.where(aegl[i], 1.6, 0.4), zorder=6)
    ax.set_title(slot_label(slot), fontsize=9, loc="left", pad=2)


nr = 0                                               # joonise number 20_01 ... 20_08
for nimi, punktid, pad, k in [("harju", pd.concat([sk[["lon", "lat"]], jn[["lon", "lat"]]]), 0.05, (2.2, 0.45)),
                              ("tallinn", jn[["lon", "lat"]], 0.04, (2.2, 1.3))]:
    ext = ulatus(punktid, pad)
    (mx0, my0), (mx1, my1) = to_merc(ext[0], ext[1]), to_merc(ext[2], ext[3])
    korgus = 4 * (my1 - my0) / (mx1 - mx0)
    for a, b in OSAD:
        nr += 1
        fig, axes = plt.subplots(6, 4, figsize=(16, 6 * korgus + 1.6), layout="constrained")
        for i, (ax, slot) in enumerate(zip(axes.flat, range(a * 4, b * 4))):
            paneel(ax, slot, ext, k, 0.006 * (mx1 - mx0), viide=i == 23)
        fig.colorbar(ScalarMappable(NORM, CMAP), ax=axes, shrink=0.35, pad=0.01,
                     label="Koormus, % koha enda tipust (tavaline tööpäev)")
        fig.legend(handles=[Line2D([], [], marker="^", ls="", color="#f8b04b", markeredgecolor="black", ms=9,
                                   label="maantee suund (osutab linna poole või linnast välja)"),
                            Line2D([], [], marker="^", ls="", color="#f8b04b", markeredgecolor=C_RED, markeredgewidth=1.6, ms=9,
                                   label=f"aeglane vähemalt {AEGLANE_OSA:.0%} tööpäevadest"),
                            Line2D([], [], marker="s", ls="", color="#f8b04b", markeredgecolor="black", ms=8, label="ristmik")],
                   loc="lower center", ncol=3, fontsize=10, bbox_to_anchor=(0.5, -0.012))
        fig.suptitle(f"{'Harjumaa maanteed ja Tallinna ristmikud' if nimi == 'harju' else 'Tallinna ristmikud'}: tavaline tööpäev "
                     f"15 min kaupa, kell {a:02d}.00–{b - 1:02d}.45 (värv = koormus % koha tipust, suurus = vool; "
                     f"{paevi_mt} / {paevi_j} tööpäeva alates {pd.Timestamp(ALGUS):%d.%m.%Y})", x=0.01, ha="left",
                     fontweight="bold", fontsize=12)
        save(fig, f"20_{nr:02d}_{nimi}_{a:02d}-{b:02d}")
print("Valmis.")
