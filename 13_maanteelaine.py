"""
13 - Maanteeloendurite 15 min loendused: A) pendelrände laine, B) nädalalõpu laine ja C) maantee kui linna ummiku
eelhoiatus.

SISEND
  common.load_15m()                          maanteeloendurite 15 min loendused (import_raw."15m_count"). Pikk ajalugu on
                                             Harjumaa loenduritel (5-37 km Tallinnast); teistel üksikud päevad
  traffic.counter_channel                    radade nimed; loenduri suund = raja nime otspunktid (nt "Tartu - Tallinn")
  common.load_locations()                    loenduri nimi, tee number, tee km ja koordinaadid
  common.load_daily(), counter_month()       kahtlase mahuga loendur-kuude väljajätmiseks (nt Kodasoo 2025-09...2026-05)
  common.day_calendar()                      päevatüüp ja koolivaheajad
  valjund/09_ummikud.csv                     ristmike stabiilsed hommikused ummikud (osa C; 09 käib enne)
  common.load_junctions(), add_basemap()     ristmike koordinaadid; kaardi taust

ÜHINE ETTEVALMISTUS
  Suuna rajad liidetakse; arvesse lähevad ainult veerandtunnid, kus kõik suuna rajad on olemas. Periood algab seadest
  ALGUS (viimane õppeaasta). Tavaline tööpäev = E-R, mitte püha ega lühendatud päev, õppetöö ajal. Profiil = iga
  veerandtunni keskmine üle päevade; loenduri suund läheb arvesse, kui päevi on >= MIN_PAEVI ja vähemalt 90%
  veerandtundidest on olemas.

A) PENDELRÄNDE LAINE (tavaliste tööpäevade profiil)
    laine         = hommiku (06-10) osakaal ööpäevast - õhtu (15-19) osakaal; sissesuund = loenduri kahest suunast see,
                    mille laine on suurem (hommikul linna poole, õhtul tagasi)
    asümmeetria   = sissesuuna laine - väljasuuna laine. Pendelrände ala = kaugus lähimast linnast (Tallinn, Tartu,
                    Pärnu; linnulennult), milleni 10 km vööndi mediaanasümmeetria on >= 0,10 (">=" = laine ei kao enne
                    andmete serva)
    laine kiirus  = sissesuuna hommikuse liikluse keskaeg (05-10) ja väljasuuna õhtuse keskaeg (14-20) kauguse järgi
                    (Tallinna pendelrände ala loendurid; sirge tõus min/km)
  13_pendellaine.png
      Näitab: kui kaugele linnast pendelränne ulatub ja kui kiiresti hommikune ja õhtune laine liigub.
      Kuidas: 2 x 2 paneeli. Ülal vasakul hajuvusdiagramm: punkt = loendur, x = kaugus lähimast linnast, km, y =
      asümmeetria; värv = linn (sinine Tallinn, oranž Tartu, türkiis Pärnu), suurus = liiklus, katkendjoon =
      pendelrände tunnus 0,10. Ülal paremal kaart ortofototaustal: ring = loendur, värv = asümmeetria (kollasest
      punaseni, 0-0,4). All vasakul hommik, Tallinna poole: x = kaugus Tallinnast, y = liikluse keskaeg 05-10; all
      paremal õhtu, Tallinnast välja: keskaeg 14-20. Katkendjoon = sirge sobitus; pealkirjas tõus min/km, r ja
      loendurite arv; nimega on märgitud kuus kaugeimat loendurit.
  13_pendellaine.csv   loenduri suuna kaupa: linn, kaugus, päevi, sissesuund, asümmeetria, osakaalud, keskajad

B) NÄDALALÕPU LAINE Tallinnast algavatel põhimaanteedel 1, 2 ja 4
  Suund raja nime järgi: sihtkoht Tallinn = sisse, lähtekoht Tallinn = välja; kaugus = tee km. Reede väljasõit (maht
  kell 12-21) ja pühapäeva tagasitulek (kell 12-24) jagatud E-N keskmisega samal kellaajal, ning liikluse keskaeg kell
  12-24; kõik õppetöö ajal. Pühapäeva profiil tehakse ka ühe päeva põhjal, et kaugemad loendurid (ainult üks pühapäev)
  oleksid laine liikumise joonisel.
  13_nadalalopp.png
      Näitab: kui suur on reedene väljasõit ja pühapäevane tagasitulek ning kuidas laine mööda teed liigub.
      Kuidas: kaks hajuvusdiagrammi, punkt = loendur, x = kaugus Tallinnast mööda teed, km. Vasakul y = maht / E-N
      keskmine (joon 1 = sama mis tavaliselt). Paremal y = liikluse keskaeg kell 12-24; katkendjoon = sirge sobitus
      (legendis min/km ja r), õõnes punkt = loenduril on alla 5 päeva. Oranž = reede väljasõit, sinine = pühapäeva
      tagasitulek.
  13_nadalalopp.csv

C) EELHOIATUS
  Tallinna piiri sissesuuna loendurid (<= 25 km, asümmeetria >= 0,10). Maantee tõusuaeg = kellaaeg, mil vool ületab 80%
  loenduri tavalisest hommikusest (05-09) suurimast veerandtunnist (lineaarselt veerandtundide vahel). Edumaa = ristmiku
  manöövri stabiilse hommikuse ummiku algus (09) - lähima piiriloenduri tõusuaeg (mõlemad tööpäevade mediaanid; maanteel
  tavalised tööpäevad ummikupäevadest kuni 4 nädalat tagasi). Kui samu tööpäevi on >= 3: kas päeval, mil maantee täitub
  varem, algab ka ummik varem (kõrvalekalded mediaanist, Spearmani rho).
  13_eelhoiatus.png
      Näitab: mitu minutit enne ristmiku ummiku algust on maantee linna piiril juba täitunud.
      Kuidas: rida = piiriloendur (sildis tõusuaeg ja manöövrite arv, järjestatud edumaa järgi), x-telg = edumaa, min.
      Sinine punkt = ristmiku manööver, oranž kriips = loenduri mediaan, püstjoon = 0. Kui samu tööpäevi on >= 3,
      lisandub paremale hajuvusdiagramm: x = maantee täitumine tavalisest varem (-) või hiljem (+), min, y = ummiku
      algus tavalisest varem või hiljem, min; punkt = manööver ühel päeval.
  13_eelhoiatus.csv, 13_eelhoiatus_paevad.csv
  ponytail: sissesuund tuleb andmetest (hommikune ülekaal), mitte teegeomeetriast, ja ristmik seotakse lähima
  piiriloenduriga linnulennult - koridoride täpseks sidumiseks on vaja käsitsi tabelit (ristmik -> maantee).
"""
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

from common import (load_15m, load_locations, load_junctions, load_daily, counter_month, ilma_vigaste_kuudeta, tabel, ends,
                    day_calendar, km, add_basemap, to_merc, slot_label, set_style, save, save_table, OUT_DIR,
                    C_BLUE, C_ORANGE, C_AQUA, TEXT2)

ALGUS = "2025-09-01"      # profiilide periood: viimane õppeaasta kuni andmete lõpuni
MIN_PAEVI = 20            # profiil arvesse, kui loenduri suunal on vähemalt nii palju päevi
LINNAD = {"Tallinn": (59.4372, 24.7454), "Tartu": (58.3806, 26.7225), "Pärnu": (58.3859, 24.4971)}
LINNA_VARV = {"Tallinn": C_BLUE, "Tartu": C_ORANGE, "Pärnu": C_AQUA}
TALLINN = ("tallinn", "talinn")      # Tallinna kirjapildid radade nimedes
ASYM_PIIR = 0.10          # pendelrände tunnus (osakaalude vahe)
KATVUS = 0.9              # profiil arvesse, kui vähemalt 90% veerandtundidest on olemas
RADIAALTEED = [1, 2, 4]   # Tallinnast algavad põhimaanteed (tee km = kaugus Tallinnast)
PIIR_KM = 25              # eelhoiatus: sissesuuna loendurid kuni 25 km Tallinna keskusest
HOMMIK = (5, 9)           # maantee hommikuse tõusu aken
TOUS = 0.8                # tõusuaeg: vool ületab 80% tavalisest hommikusest suurimast veerandtunnist
H = (np.arange(96) + 0.5) / 4
hhmm = lambda h: slot_label(h * 60, 60)


def profiil(x, min_paevi=MIN_PAEVI):
    """Keskmine ööpäeva profiil (read = site, veerud = 96 veerandtundi); liiga väheste päevade või alla KATVUS
    kaetusega loenduri suunad välja."""
    x = x[x.groupby("site")["paev"].transform("nunique") >= min_paevi]
    p = x.groupby(["site", "slot"])["c"].mean().unstack("slot").reindex(columns=range(96))
    return p[p.notna().mean(axis=1) >= KATVUS].interpolate(axis=1, limit_direction="both")


def touseaeg(h, c, lavi):
    """Kellaaeg, mil vool c esimest korda ületab läve (lineaarselt veerandtundide keskpunktide vahel); NaN, kui ei ületa."""
    i = int(np.argmax(c >= lavi))
    if c[i] < lavi:
        return np.nan
    return h[0] if i == 0 else h[i - 1] + (lavi - c[i - 1]) / (c[i] - c[i - 1]) * (h[i] - h[i - 1])


def sirge(x, y):
    """Sirge y = a + b x: (tõus, vabaliige, r, n); alla 4 punkti -> NaN."""
    if len(x) < 4:
        return np.nan, np.nan, np.nan, len(x)
    r = stats.linregress(x, y)
    return r.slope, r.intercept, r.rvalue, len(x)


assert touseaeg(np.array([6., 6.25, 6.5]), np.array([0., 100, 200]), 150) == 6.375
assert np.isnan(touseaeg(np.array([6., 6.25]), np.array([0., 100]), 150))
assert abs(sirge(np.arange(5.), 2 * np.arange(5.) + 1)[0] - 2) < 1e-9

set_style()
# --- Loendurite suundade kataloog: raja nimi -> suund; lähim linn, tee nr ja km ----------------------------------
chn = tabel("traffic.counter_channel", dtype={"id": str})
chn[["lahte", "siht"]] = pd.DataFrame([ends(x) for x in chn["channel_label"]], index=chn.index)
chn = chn[chn["lahte"] != ""]
chn["site"] = chn["id"] + " | " + chn["lahte"] + " - " + chn["siht"]
loc = load_locations().set_index("id").rename(columns={"latitude": "lat", "longitude": "lon"})
ds = chn.groupby("site").agg(id=("id", "first"), lahte=("lahte", "first"), siht=("siht", "first"))
ds = ds.join(loc[["nimi", "tee_nr", "tee_km", "lat", "lon"]], on="id")
kaugus = pd.DataFrame({c: km(ds["lat"], ds["lon"], *xy) for c, xy in LINNAD.items()})
ds["linn"], ds["km_linnast"] = kaugus.idxmin(axis=1), kaugus.min(axis=1)
ds["tee_suund"] = np.select([ds["siht"].isin(TALLINN), ds["lahte"].isin(TALLINN)], ["sisse", "välja"], default="")

# --- 15 min loendused suuna kaupa ----------------------------------------------------------------------------
m = ilma_vigaste_kuudeta(load_15m(), counter_month(load_daily()))
m = m[m["ts"] >= ALGUS].merge(chn[["id", "kanal", "site"]], on=["id", "kanal"])
dq = m.groupby(["site", "ts"])["v"].agg(c="sum", n="size").reset_index().rename(columns={"ts": "start"})
dq = dq[dq["n"] == dq.groupby("site")["n"].transform("max")]              # ainult veerandtunnid, kus kõik suuna rajad on olemas
dq["paev"] = dq["start"].dt.normalize()
dq["slot"] = dq["start"].dt.hour * 4 + dq["start"].dt.minute // 15
kal = day_calendar(dq["paev"]).set_index("paev")
dq["kool"] = dq["paev"].map(kal["vaheaeg"]) == "kool"
dq["toopaev"] = dq["kool"] & (dq["paev"].map(kal["paevatyyp"]) == "tööpäev")       # tavaline tööpäev
dq["dow"] = dq["paev"].dt.dayofweek
TP = dq.loc[dq["toopaev"], "paev"].nunique()
print(f"15 min loendused {dq['start'].min():%d.%m.%Y} – {dq['start'].max():%d.%m.%Y}: {dq['site'].nunique()} loenduri suunda, "
      f"tavalisi tööpäevi {TP}")

# === A) Pendelrände laine ===============================================================================
T = profiil(dq[dq["toopaev"]])
osa = lambda p, a, b: p.loc[:, a * 4:b * 4 - 1].sum(axis=1) / p.sum(axis=1)
kesk = lambda p, a, b: (p.loc[:, a * 4:b * 4 - 1] * H[a * 4:b * 4]).sum(axis=1) / p.loc[:, a * 4:b * 4 - 1].sum(axis=1)
k = ds.join(pd.DataFrame({"soidukeid": T.sum(axis=1), "hommik": osa(T, 6, 10), "ohtu": osa(T, 15, 19),
                          "hommik_kesk_h": kesk(T, 5, 10), "ohtu_kesk_h": kesk(T, 14, 20),
                          "paevi": dq[dq["toopaev"]].groupby("site")["paev"].nunique()}), how="inner")
k["koht"] = k["id"]
k["laine"] = k["hommik"] - k["ohtu"]
k = k[k.groupby("koht")["laine"].transform("size") == 2].copy()            # ainult mõlema suunaga loendurid
k["sisse"] = k.index.isin(k.groupby("koht")["laine"].idxmax())
k["asym"] = k["koht"].map(k[k["sisse"]].set_index("koht")["laine"] - k[~k["sisse"]].set_index("koht")["laine"])
save_table(k.reset_index().assign(hommik_kesk=k["hommik_kesk_h"].map(hhmm).values, ohtu_kesk=k["ohtu_kesk_h"].map(hhmm).values)
           [["site", "nimi", "linn", "km_linnast", "tee_nr", "tee_km", "paevi", "sisse", "asym", "soidukeid", "hommik", "ohtu",
             "hommik_kesk", "ohtu_kesk"]].round(3), "13_pendellaine")
s_in, s_out = k[k["sisse"]], k[~k["sisse"]].set_index("koht")
ala = {}
for linn, g in s_in.groupby("linn"):
    med = g.groupby(g["km_linnast"] // 10)["asym"].median()
    alla = med.index[med < ASYM_PIIR]                                       # esimene vöönd, kus laine kaob
    ala[linn] = "?" if len(g) < 5 else f"~{alla[0] * 10:.0f}" if len(alla) else f">= {(med.index.max() + 1) * 10:.0f}"
print(f"A) Pendelrände laine: {len(s_in)} loendurit; pendelrände ala (asümmeetria >= {ASYM_PIIR}): "
      + ", ".join(f"{c} {r} km" for c, r in ala.items()))
tl = s_in[(s_in["linn"] == "Tallinn") & (s_in["asym"] >= ASYM_PIIR)]
laine_h = sirge(tl["km_linnast"], tl["hommik_kesk_h"] * 60)
tv = s_out.loc[tl["koht"]]
laine_o = sirge(tv["km_linnast"], tv["ohtu_kesk_h"] * 60)
for nimi, (b, a, r, n) in [("hommik, sissesuund", laine_h), ("õhtu, väljasuund", laine_o)]:
    print(f"   Tallinn, {nimi}: liikluse keskaeg {b:+.2f} min/km (r = {r:.2f}, n = {n})"
          + (f" -> laine liigub ~{60 / abs(b):.0f} km/h" if abs(b) > 0.2 else " -> ajaline nihe kaugusega on väike"))

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
ax = axes[0, 0]
for linn, col in LINNA_VARV.items():
    g = s_in[s_in["linn"] == linn]
    if len(g):
        ax.scatter(g["km_linnast"], g["asym"], s=np.sqrt(g["soidukeid"]) * 0.7, color=col, alpha=0.75, edgecolor="none",
                   label=f"{linn} ({len(g)} loendurit; pendelrände ala {ala[linn]} km)")
ax.axhline(ASYM_PIIR, color=TEXT2, lw=0.8, ls="--")
ax.set_ylim(0, None)
ax.set_xlabel("Kaugus lähimast linnast, km (linnulennult)")
ax.set_ylabel("Suundade asümmeetria (hommiku ja õhtu osakaalu vahe)")
ax.set_title("Pendelrände ulatus: kui kaugel on hommikul selge linna-suunaline ülekaal\n(punkti suurus = liiklus; "
             "katkendjoon = pendelrände tunnus)", fontsize=10)
ax.legend(fontsize=8)
ax = axes[0, 1]
lon0, lat0, lon1, lat1 = s_in["lon"].min() - 0.3, s_in["lat"].min() - 0.25, s_in["lon"].max() + 0.3, s_in["lat"].max() + 0.15
add_basemap(ax, lon0, lat0, lon1, lat1)
px, py = to_merc(s_in["lon"].values, s_in["lat"].values)
sc = ax.scatter(px, py, c=s_in["asym"], cmap="YlOrRd", vmin=0, vmax=0.4, s=np.sqrt(s_in["soidukeid"]) * 0.7,
                edgecolor="black", linewidth=0.6, zorder=5)
fig.colorbar(sc, ax=ax, shrink=0.7, label="Asümmeetria")
ax.set_title("Kus on pendelrände laine tugev", fontsize=10)
for ax, g, veerg, (b, a, r, n), nimi in [(axes[1, 0], tl, "hommik_kesk_h", laine_h, "Hommik, Tallinna poole: liikluse keskaeg 05–10"),
                                         (axes[1, 1], tv, "ohtu_kesk_h", laine_o, "Õhtu, Tallinnast välja: liikluse keskaeg 14–20")]:
    ax.scatter(g["km_linnast"], g[veerg], s=np.sqrt(g["soidukeid"]) * 0.7, color=C_BLUE if "hommik" in veerg else C_ORANGE,
               alpha=0.8, edgecolor="none")
    if n >= 4:
        xx = np.array([0, g["km_linnast"].max()])
        ax.plot(xx, (a + b * xx) / 60, color=TEXT2, lw=1, ls="--")
    for r_ in g.nlargest(6, "km_linnast").itertuples():
        ax.annotate(r_.nimi, (r_.km_linnast, getattr(r_, veerg)), xytext=(3, 3), textcoords="offset points", fontsize=7,
                    color=TEXT2)
    ax.yaxis.set_major_formatter(lambda h, _: hhmm(h))
    ax.set_xlabel("Kaugus Tallinnast, km (linnulennult)")
    ax.set_ylabel("Liikluse keskaeg")
    ax.set_title(f"{nimi}\n{b:+.2f} min/km (r = {r:.2f}, {n} loendurit pendelrände alal)", fontsize=10)
fig.suptitle(f"Pendelrände laine maanteedel (15 min loendused, {TP} tavalist tööpäeva alates {pd.Timestamp(ALGUS):%d.%m.%Y})",
             x=0.01, ha="left", fontweight="bold")
fig.tight_layout()
save(fig, "13_pendellaine")

# === B) Nädalalõpu laine radiaalteedel ====================================================================
R = ds[ds["tee_nr"].isin(RADIAALTEED) & (ds["tee_suund"] != "")]
lahedal = k[k.index.isin(R.index) & (k["asym"] >= ASYM_PIIR) & (k["tee_km"] <= 40)]
print(f"B) Radiaalteed {RADIAALTEED}: {R['id'].nunique()} loendurit; raja nime suuna ja andmete sissesuuna kokkulangevus "
      f"Tallinna lähedal: {((lahedal['tee_suund'] == 'sisse') == lahedal['sisse']).mean() * 100:.0f}% ({len(lahedal)} suunda)")
maskid = {"E-N": dq["toopaev"] & (dq["dow"] < 4), "reede": dq["toopaev"] & (dq["dow"] == 4), "pühapäev": dq["kool"] & (dq["dow"] == 6)}
ETN, RE, PU = profiil(dq[maskid["E-N"]]), profiil(dq[maskid["reede"]], 5), profiil(dq[maskid["pühapäev"]], 1)
rows = []
for nimi, P_, paev, suund, (a, b) in [("reede väljasõit", RE, "reede", "välja", (12, 21)),
                                      ("pühapäeva tagasitulek", PU, "pühapäev", "sisse", (12, 24))]:
    ids = R.index[R["tee_suund"] == suund].intersection(P_.index)
    rows.append(R.loc[ids, ["nimi", "tee_nr", "tee_km"]].assign(
        laine=nimi, paevi=dq[maskid[paev]].groupby("site")["paev"].nunique().reindex(ids),
        suhe_ETN=P_.loc[ids, a * 4:b * 4 - 1].sum(axis=1) / ETN.reindex(ids).loc[:, a * 4:b * 4 - 1].sum(axis=1, min_count=1),
        keskaeg_h=kesk(P_.loc[ids], 12, 24)))
nl = pd.concat(rows)
save_table(nl.reset_index().assign(keskaeg=nl["keskaeg_h"].map(hhmm).values).round(3), "13_nadalalopp")
fig, axes = plt.subplots(1, 2, figsize=(14, 5.2))
for nimi, col in [("reede väljasõit", C_ORANGE), ("pühapäeva tagasitulek", C_BLUE)]:
    g = nl[nl["laine"] == nimi]
    palju = g["paevi"] >= 5
    b, a, r, n = sirge(g["tee_km"], g["keskaeg_h"] * 60)
    axes[0].scatter(g["tee_km"], g["suhe_ETN"], color=col, alpha=0.8, edgecolor="none", label=f"{nimi} ({g['suhe_ETN'].notna().sum()})")
    axes[1].scatter(g.loc[palju, "tee_km"], g.loc[palju, "keskaeg_h"], color=col, alpha=0.8, edgecolor="none",
                    label=f"{nimi}: {b:+.2f} min/km, r = {r:.2f}")
    axes[1].scatter(g.loc[~palju, "tee_km"], g.loc[~palju, "keskaeg_h"], facecolors="none", edgecolors=col, alpha=0.9)
    if n >= 4:
        xx = np.array([0, g["tee_km"].max()])
        axes[1].plot(xx, (a + b * xx) / 60, color=col, lw=1, ls="--")
    print(f"   {nimi}: maht {g['suhe_ETN'].median():.2f}x E-N (mediaan, {g['suhe_ETN'].notna().sum()} loendurit), keskaeg "
          f"{b:+.2f} min/km (r = {r:.2f}, n = {n}, neist alla 5 päevaga {(~palju).sum()})")
axes[0].axhline(1, color=TEXT2, lw=0.6)
axes[0].set_xlabel("Kaugus Tallinnast mööda teed, km")
axes[0].set_ylabel("Maht / E–N keskmine")
axes[0].set_title("Nädalalõpu laine suurus (reede 12–21, pühapäev 12–24)", fontsize=10)
axes[0].legend(fontsize=9)
axes[1].yaxis.set_major_formatter(lambda h, _: hhmm(h))
axes[1].set_xlabel("Kaugus Tallinnast mööda teed, km")
axes[1].set_ylabel("Liikluse keskaeg kell 12–24")
axes[1].set_title("Laine liikumine: millal on liikluse raskuskese eri kaugustel\n(õõnes punkt = loenduril alla 5 päeva)", fontsize=10)
axes[1].legend(fontsize=8)
fig.suptitle(f"Nädalalõpu laine Tallinnast algavatel põhimaanteedel (teed {', '.join(map(str, RADIAALTEED))}; õppetöö ajal alates "
             f"{pd.Timestamp(ALGUS):%d.%m.%Y})", x=0.01, ha="left", fontweight="bold")
fig.tight_layout()
save(fig, "13_nadalalopp")

# === C) Eelhoiatus: piiriloenduri tõusuaeg vs ristmike ummiku algus ===========================================
if not (OUT_DIR / "09_ummikud.csv").exists():
    print("C) Eelhoiatus: 09_ummikud.csv puudub (09 käib enne). Valmis.")
    sys.exit(0)
um = pd.read_csv(OUT_DIR / "09_ummikud.csv", encoding="utf-8-sig", parse_dates=["paev"])
um = um[um["stabiilne"] & (um["tyyp"] == "tööpäev") & um["tipp"].str.contains("hommik")]
jn = load_junctions().dropna(subset=["lat"]).set_index("code")
um = um[um["mp"].isin(jn.index)]
piir = k[k["sisse"] & (k["linn"] == "Tallinn") & (k["km_linnast"] <= PIIR_KM) & (k["asym"] >= ASYM_PIIR)]
sl = list(range(HOMMIK[0] * 4, HOMMIK[1] * 4))
aken = dq["paev"].between(um["paev"].min() - pd.Timedelta(days=28), um["paev"].max()) if len(um) else False
M = (dq[dq["site"].isin(piir.index) & dq["toopaev"] & aken & dq["slot"].isin(sl)]
     .pivot_table(index=["site", "paev"], columns="slot", values="c").reindex(columns=sl).dropna())      # terved hommikud
lavi = TOUS * M.max(axis=1).groupby("site").median()
mt = pd.DataFrame({"tous_h": [touseaeg(H[sl], r.values, lavi[s]) for (s, _), r in M.iterrows()],
                   "maht": M.sum(axis=1).values}, index=M.index).dropna().reset_index()
pk = piir.loc[piir.index.intersection(mt["site"].unique())]
if um.empty or pk.empty:
    print("C) Eelhoiatus: pole stabiilseid hommikusi ummikuid või piiriloendurite terveid hommikuid. Valmis.")
    sys.exit(0)
vahe = km(jn.loc[um["mp"], "lat"].values[:, None], jn.loc[um["mp"], "lon"].values[:, None], pk["lat"].values[None], pk["lon"].values[None])
um = um.assign(site=pk.index[vahe.argmin(axis=1)], km_loendurist=vahe.min(axis=1))
KEY = ["mp", "direction_id", "manoeuvre", "site"]
eel = (um.groupby(KEY).agg(km_loendurist=("km_loendurist", "first"), ummikupaevi=("paev", "nunique"),
                           ummiku_algus_h=("algus_h", "median"), kestus_min=("kestus_min", "median")).reset_index()
       .merge(mt.groupby("site").agg(maantee_tous_h=("tous_h", "median"), maanteepaevi=("paev", "nunique")), on="site"))
eel["edumaa_min"] = (eel["ummiku_algus_h"] - eel["maantee_tous_h"]) * 60
eel["loendur"] = eel["site"].map(pk["nimi"])
save_table(eel.assign(ummiku_algus=eel["ummiku_algus_h"].map(hhmm), maantee_tous=eel["maantee_tous_h"].map(hhmm))
           .drop(columns=["ummiku_algus_h", "maantee_tous_h"]).round(1), "13_eelhoiatus")
uhised = sorted(set(um["paev"]) & set(mt["paev"]))
print(f"C) Eelhoiatus: {len(pk)} piiriloendurit, {len(eel)} stabiilse hommikuse ummikuga manöövrit; maantee täitub enne "
      f"ummiku algust mediaanis {eel['edumaa_min'].median():.0f} min (kvartiilid {eel['edumaa_min'].quantile(.25):.0f}–"
      f"{eel['edumaa_min'].quantile(.75):.0f}); samu tööpäevi {len(uhised)}")
pv = None
if len(uhised) >= 3:
    pv = um[um["paev"].isin(uhised)].merge(mt, on=["site", "paev"])
    med = lambda veerg, voti: pv.groupby(voti)[veerg].transform("median")
    pv = pv.assign(ummik_varem_min=(pv["algus_h"] - med("algus_h", KEY)) * 60, maantee_varem_min=(pv["tous_h"] - med("tous_h", "site")) * 60,
                   kestus_vahe_min=pv["kestus_min"] - med("kestus_min", KEY), maht_vahe_pct=(pv["maht"] / med("maht", "site") - 1) * 100)
    pv = pv[pv.groupby(KEY)["paev"].transform("nunique") >= 3]
    save_table(pv[KEY + ["paev", "ummik_varem_min", "maantee_varem_min", "kestus_vahe_min", "maht_vahe_pct"]]
               .assign(paev=pv["paev"].dt.date).round(1), "13_eelhoiatus_paevad")
    r1 = stats.spearmanr(pv["maantee_varem_min"], pv["ummik_varem_min"])
    r2 = stats.spearmanr(pv["maht_vahe_pct"], pv["kestus_vahe_min"])
    print(f"   Päevade kaupa ({len(pv)} manööver-päeva): maantee tõusuaeg vs ummiku algus rho = {r1.statistic:.2f} (p = "
          f"{r1.pvalue:.3g}); maantee hommikune maht vs ummiku kestus rho = {r2.statistic:.2f} (p = {r2.pvalue:.3g})")
jarj = eel.groupby("loendur")["edumaa_min"].median().sort_values()
fig, axes = plt.subplots(1, 2 if pv is not None else 1, figsize=(15 if pv is not None else 9, max(0.42 * len(jarj) + 2.4, 5.2 if pv is not None else 0)), squeeze=False)
ax = axes[0, 0]
for i, nimi in enumerate(jarj.index):
    g = eel[eel["loendur"] == nimi]
    ax.scatter(g["edumaa_min"], np.full(len(g), i) + np.random.default_rng(0).uniform(-0.18, 0.18, len(g)), s=22, color=C_BLUE,
               alpha=0.6, edgecolor="none")
    ax.plot([jarj[nimi]] * 2, [i - 0.3, i + 0.3], color=C_ORANGE, lw=2.5)
ax.axvline(0, color=TEXT2, lw=0.6)
ax.set_yticks(range(len(jarj)))
ax.set_yticklabels([f"{n} (tõus {hhmm(eel.loc[eel['loendur'] == n, 'maantee_tous_h'].iloc[0])}; {(eel['loendur'] == n).sum()} manöövrit)"
                    for n in jarj.index], fontsize=8)
ax.set_xlabel("Edumaa, min (punkt = manööver, kriips = mediaan)")
ax.set_title(f"Maantee kui eelhoiatus: edumaa enne ummiku algust\n(maantee {mt['paev'].nunique()} "
             f"tööpäeva, ummikud {um['paev'].nunique()} tööpäeva)", fontsize=10)
if pv is not None:
    ax = axes[0, 1]
    ax.scatter(pv["maantee_varem_min"], pv["ummik_varem_min"], s=16, color=C_BLUE, alpha=0.6, edgecolor="none")
    ax.axhline(0, color=TEXT2, lw=0.6)
    ax.axvline(0, color=TEXT2, lw=0.6)
    ax.set_xlabel("Maantee täitumine: hiljem (+) / varem (−), min")
    ax.set_ylabel("Ummiku algus: hiljem (+) / varem (−), min")
    ax.set_title(f"Päevade kaupa: varasem täitumine -> varasem ummik?\n(Spearmani rho = "
                 f"{r1.statistic:.2f}, p = {r1.pvalue:.3g})", fontsize=10)
fig.tight_layout()
save(fig, "13_eelhoiatus")
print("Valmis.")
