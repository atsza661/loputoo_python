"""
24 - Nädal sõidukipõhiseid loendusi soojuskaardina ajateljel: kui koormatud on iga Tallinna ristmik (loendurite kogum)
igal 5 minutil kell 06.00-19.00, kaheksa järjestikust päeva. Kaart iga 5 min kohta, nendest GIF ja MP4, ning iga päeva
kohta ristmik x kellaaeg soojuskaart.

SISEND
  common.load_vehicles(koik=True)   Traffic 24h sõidukikirjed (tallinn.vehicle_passage, puhastatud): ristmik,
                                    kanal (loendur = rada), aeg, loenduril oldud aeg occ (s); päevad PAEVAD
  common.load_junctions()           ristmike koodid, nimed ja koordinaadid
  common.add_basemap()              ortofototaust (Maa- ja Ruumiamet; internetita joonistatakse ilma)

ARVUTUS
  Iga kanali (loenduri) iga päeva 5 min pilus:
    läbilase q   = sõidukeid pilus x 12 (sõidukit tunnis)
    hõivatus H   = pilu sõidukite loenduril oldud aegade summa / 300 s (osa ajast, mil loendur oli kaetud)
    täistase     = kanali läbilaskevõime hinnang: 15 min libiseva keskmise läbilaske päeva suurim väärtus, andmetega
                   päevade mediaan (nagu 09 täistase). Kanal arvesse, kui täistase >= MIN_TAIS sõidukit tunnis.
    H_täis       = hõivatuse mediaan piludes, kus q >= 80% täistasemest (hõivatus läbilaskevõimel)
  Liiklusolek põhidiagrammi järgi (lävi 80% nagu 09 ummikul, seisak nagu 09 seisakul):
    vaba         q < 50% täistasemest
    tihe         50% <= q < 80%
    täis         q >= 80% täistasemest (läbilaskevõimel, küllastunud voog)
    seisak       q < 80% täistasemest JA H >= max(H_täis, 10%): loendur on kaetud vähemalt sama palju kui täistasemel,
                 aga läbi pääseb vähem - sõidukid seisavad või roomavad (ülekoormatud, sunnitud voog)
  Kanali koormusaste = min(q / täistase, 1); seisakus = 1 (läbilaskevõime on ammendatud, kuigi läbi pääseb vähe).
  Ristmiku koormusaste = kanalite koormusastmete täistasemega kaalutud keskmine x 100 (0-100%): 100% = kõik rajad
  on täis või seisavad. Seisakuosa (täis osa) = seisakus (täis) kanalite täistasemete osa ristmiku täistasemest.
  Rike: kanali sõidukiteta lõik vähemalt RIKE_MIN minutit, kui kanali tavaline (päevade mediaan) läbilase samal ajal
  on kuskil lõigus vähemalt 20% täistasemest, on puuduv (mitte 0); ristmik on pilus puuduv, kui puudub üle poole selle
  täistasemest.
  Kaardi värvipind = ristmike koormusastme Gaussi kaaluga keskmine (nagu 23, silumislaius H_KM): z(x) = Σ w_i z_i /
  Σ w_i, w_i = exp(-d_i² / (2 h²)); pind hajub 2 h ja kaob 3 h kaugusel lähimast ristmikust, millel pilus on andmed.
  ponytail: loendurid on stoppjoonel, seega q ja H on punktimõõdud; viivitust ja järjekorra pikkust (HCM/HBS
  teenindustase) need ei anna. 5 min pilus on 3-5 fooritsüklit, seega üksik pilu on mürane.

VÄLJUND (kaust valjund/24_soojus_ajatelg/)
  24_01_<kuupäev>_<HHMM>.png   (8 päeva x 156 kaarti, kell 06.00-18.55)
      Näitab: kui koormatud on Tallinna ristmikud ühel 5 minutil: kus liiklus on läbilaskevõimel ja kus seisab.
      Kuidas: Tallinna kaart ortofototaustal. Värvipind = ristmike koormusaste (heledast kollasest 0% tumepunaseni
      100%, nagu 20); ruut = ristmik (sama värviskaala, hall = andmed puuduvad), must rõngas ruudu ümber = vähemalt
      SEISAK_MARK ristmiku täistasemest on seisakus; ristmiku kood kõrval. Pealkirjas päev ja kellaaeg; all ajariba:
      kõigi ristmike keskmine koormusaste sel päeval kella 06-st kuni kaardi ajani (punane joon, must püstjoon = kaardi aeg).
  24_01_soojus_ajatelg.mp4, 24_01_soojus_ajatelg.gif
      Näitab: sama kaartide jada liikuva pildina, kaheksa päeva järjest (MP4 FPS kaadrit sekundis; GIF väiksem,
      GIF_LAIUS pikslit lai, kaader GIF_MS ms).
  24_02_ristmikud_<kuupäev>.png   (8 joonist)
      Näitab: iga ristmiku koormusaste igal 5 minutil ühel päeval (soojuskaart ajateljel): millal ja kus tipp tekib
      ja kui kaua see kestab.
      Kuidas: y-telg = ristmik (kood, põhjast lõunasse), x-telg = kellaaeg 06-19, värv = koormusaste (YlOrRd, 0-100%),
      hall = andmed puuduvad. Must täpp = vähemalt SEISAK_MARK ristmiku täistasemest on seisakus.
  24_koormus_5min.csv       iga ristmik, päev ja 5 min pilu (06-19): koormusaste %, seisakuosa %, täis osa %, sõidukeid
  24_kanalid.csv            iga arvesse võetud kanal: täistase (sõid/h), H_täis, olekute osakaalud kell 06-19
"""
import shutil
import subprocess

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from PIL import Image

from common import (OUT_DIR, DATA_DIR, load_vehicles, load_junctions, add_basemap, to_merc, map_extent, loigud,
                    set_style, save, save_table, HALO, C_RED, TEXT2)

PAEVAD = pd.date_range("2026-10-16", "2026-10-23")    # logija teine salvestus: kaheksa täielikku päeva (R-R)
KELL = (6, 19)                       # kaartide ja jooniste kellaajad: pilud 06.00-18.55
SAMM = 5                             # pilu pikkus, min
TAIS, TIHE = 0.8, 0.5                # olekulävid: q >= 80% täistasemest = täis, >= 50% = tihe
SEISAK_H = 0.10                      # seisak: H >= max(H_täis, 10%) ja q < 80% (nagu 09)
MIN_TAIS = 120                       # kanal arvesse, kui täistase >= 120 sõid/h (10 sõidukit 5 min)
RIKE_MIN = 30                        # sõidukiteta lõik >= 30 min, kui tavaliselt on liiklust -> rike (puuduv)
SEISAK_MARK = 0.10                   # must rõngas / must täpp, kui >= 10% ristmiku täistasemest on seisakus
H_KM = 1.0                           # silumislaius (km), nagu 23 Tallinna kaardil
VORK = 500                           # võrgusõlmi kaardi laiuses
DPI = 100                            # kaartide eraldusvõime: 1248 ortofotokaarti, 200 dpi annaks mitu GB
FPS = 8                              # MP4 kaadrit sekundis (156 kaadrit = ~20 s päevas)
GIF_LAIUS, GIF_MS = 480, 125         # GIF-i laius pikslites ja kaadri kestus
CMAP = plt.get_cmap("YlOrRd")
CMAP_PUUDU = CMAP.with_extremes(bad="#a8a7a3")         # ristmiku ruut ilma andmeteta: hall
NORM = Normalize(0, 100)
KAUST = OUT_DIR / "24_soojus_ajatelg"
KOIK = np.arange(0, 24 * 60, SAMM)                     # pilu algus minutites keskööst (täistase terve päeva järgi)
PILUD = KOIK[(KOIK >= KELL[0] * 60) & (KOIK < KELL[1] * 60)]
PAEVANIMI = ["E", "T", "K", "N", "R", "L", "P"]


def olek(q, h, tais, h_tais):
    """Liiklusolek 0 vaba, 1 tihe, 2 täis, 3 seisak (q ja tais sõid/h, h ja h_tais osad 0-1)."""
    r = q / tais
    return np.where((r < TAIS) & (h >= np.maximum(h_tais, SEISAK_H)), 3, np.where(r >= TAIS, 2, np.where(r >= TIHE, 1, 0)))


assert list(olek(np.array([10, 60, 90, 30, 30.0]), np.array([0.02, 0.05, 0.3, 0.3, 0.05]), 100, 0.2)) == [0, 1, 2, 3, 0]


def silu_kaalud(x, y, gx, gy, h):
    """Gaussi kaalud (võrgusõlm x ristmik) ja kaugused ristmikest h ühikutes; kõik Mercatori meetrites."""
    d2 = (gx.reshape(-1, 1) - x) ** 2 + (gy.reshape(-1, 1) - y) ** 2
    return np.exp(-d2 / (2 * h * h)), np.sqrt(d2) / h


def pind(w, kaug, z, shape):
    """Kaalutud keskmine z (NaN = puuduv ristmik) ja läbipaistmatus (1 kuni 2 h, 3 h-ni 0-ni), nagu 23 silu()."""
    ok = ~np.isnan(z)
    if not ok.any():
        return np.full(shape, np.nan), np.zeros(shape)
    lahim = kaug[:, ok].min(axis=1)
    zz = (w[:, ok] @ z[ok]) / np.maximum(w[:, ok].sum(axis=1), 1e-300)
    return np.where(lahim <= 3, zz, np.nan).reshape(shape), np.clip(3 - lahim, 0, 1).reshape(shape)


_w, _k = silu_kaalud(np.array([0.0, 10.0]), np.array([0.0, 0.0]), np.array([0.0, 5.0, 40.0]), np.zeros(3), 2.0)
_z, _a = pind(_w, _k, np.array([7.0, np.nan]), (3,))
assert abs(_z[0] - 7) < 1e-9 and abs(_z[1] - 7) < 1e-9 and np.isnan(_z[2]) and _a[1] == 0.5   # puuduv punkt ei loe
_z, _ = pind(_w, _k, np.array([7.0, 9.0]), (3,))
assert abs(_z[1] - 8) < 1e-9                                                                 # kahe punkti keskel


def kell(s):
    """Minutid keskööst -> 'HH:MM'."""
    return f"{s // 60:02d}:{s % 60:02d}"


set_style()
KAUST.mkdir(parents=True, exist_ok=True)

# --- Sõidukid -> kanali 5 min pilud (rida = ristmik, kanal, päev; veerg = pilu) ----------------------------------------
print("Laen sõidukipõhised kirjed...")
v = load_vehicles(suund=None, koik=True)
v = v[v["ts"].dt.normalize().isin(PAEVAD)]
puudu = sorted(set(PAEVAD.date) - set(v["ts"].dt.date))
assert not puudu, f"andmebaasis pole päevi {puudu}: lae logija päevafailid (db_laadimine.py)"
v = v.assign(paev=v["ts"].dt.normalize(), pilu=(v["ts"].dt.hour * 60 + v["ts"].dt.minute) // SAMM * SAMM)
g = v.groupby(["mp_id", "kanal", "paev", "pilu"])["occ"].agg(["size", "sum"])
read = pd.MultiIndex.from_tuples([(m, c, p) for m, c in g.index.droplevel(["paev", "pilu"]).unique() for p in PAEVAD],
                                 names=["mp_id", "kanal", "paev"])     # ka päev, mil kanal ei saatnud midagi (rike)
n = g["size"].unstack("pilu", fill_value=0).reindex(index=read, columns=KOIK, fill_value=0)
q = n * 60 / SAMM
H = g["sum"].unstack("pilu", fill_value=0).reindex(index=read, columns=KOIK, fill_value=0) / (SAMM * 60)
print(f"{len(v):,} sõidukit, {len(read) // len(PAEVAD)} kanalit, {v['mp_id'].nunique()} ristmikku, "
      f"{PAEVAD[0]:%d.%m}-{PAEVAD[-1]:%d.%m.%Y}")
del v, g

# --- Kanali täistase, H_täis ja rikked ---------------------------------------------------------------------------------
paeva_max = q.T.rolling(15 // SAMM, center=True, min_periods=1).mean().max()
tais = paeva_max.where(paeva_max > 0).groupby(["mp_id", "kanal"]).median().rename("tais")
kan = q.index.droplevel("paev")
T = tais.reindex(kan).values[:, None]                  # iga rea kanali täistase
h_tais = (H.where(q.values / T >= TAIS).stack().groupby(["mp_id", "kanal"]).median()
          .reindex(tais.index).fillna(SEISAK_H).rename("h_tais"))
tava = q.groupby(["mp_id", "kanal"]).median()            # kanali tavaline läbilase igal kellaajal
rike = np.zeros(q.shape, bool)
for i, (rida, (m, c)) in enumerate(zip(q.values, kan)):
    ootus = tava.loc[(m, c)].values >= 0.2 * tais[(m, c)]
    for a, b in loigud(rida == 0, 0):
        if (b - a) * SAMM >= RIKE_MIN and ootus[a:b].any():
            rike[i, a:b] = True
arvesse = (tais.reindex(kan) >= MIN_TAIS).values
print(f"Kanaleid arvesse {int((tais >= MIN_TAIS).sum())} / {len(tais)} (täistase >= {MIN_TAIS} sõid/h); "
      f"rikkepilusid kell 06-19: {int(rike[arvesse][:, np.isin(KOIK, PILUD)].sum())}")

# --- Olekud ja ristmiku koormusaste ------------------------------------------------------------------------------------
q, H, T, rike, kan = q[arvesse], H[arvesse], T[arvesse], rike[arvesse], kan[arvesse]
ol = olek(q.values, H.values, T, h_tais.reindex(kan).values[:, None])
aste = np.where(ol == 3, 1.0, np.minimum(q.values / T, 1.0))
w = np.where(rike, 0.0, T)                               # kanali kaal pilus: täistase, rikke ajal 0
summa = lambda x: pd.DataFrame(x, index=q.index, columns=KOIK).groupby(["mp_id", "paev"]).sum()
kaal = summa(w)
kaetud = kaal / summa(np.broadcast_to(T, q.shape))
puudub = kaetud < 0.5
koormus = (summa(aste * w) / kaal * 100).mask(puudub)
seisak = (summa((ol == 3) * w) / kaal * 100).mask(puudub)
tais_osa = (summa((ol == 2) * w) / kaal * 100).mask(puudub)
soidukeid = n[arvesse].groupby(["mp_id", "paev"]).sum()
assert np.nanmin(koormus.values) >= 0 and np.nanmax(koormus.values) <= 100 + 1e-9 and np.nanmax(seisak.values) <= 100 + 1e-9


def pikk(x):
    """Lai tabel (ristmik, päev) x pilu -> pikk rida iga ristmiku, päeva ja pilu (PILUD) kohta, puuduv = NaN."""
    s = x[PILUD].rename_axis(columns="pilu").stack()
    return s.reindex(pd.MultiIndex.from_tuples([(m, p, t) for m, p in x.index for t in PILUD],
                                               names=["mp_id", "paev", "pilu"]))


jn = load_junctions().dropna(subset=["lat", "lon"]).set_index("mp_id")
jn = jn.loc[jn.index.intersection(koormus.index.get_level_values("mp_id").unique())]
tab = pd.concat({"koormus_pct": pikk(koormus), "seisak_pct": pikk(seisak), "tais_pct": pikk(tais_osa),
                 "soidukeid": pikk(soidukeid)}, axis=1).reset_index()
tab = tab[tab["mp_id"].isin(jn.index)]
save_table(tab.assign(kood=tab["mp_id"].map(jn["code"]), nimi=tab["mp_id"].map(jn["name"]),
                      paev=tab["paev"].dt.strftime("%Y-%m-%d"), kell=tab["pilu"].map(kell))
           [["kood", "nimi", "paev", "kell", "koormus_pct", "seisak_pct", "tais_pct", "soidukeid"]].round(2),
           "24_soojus_ajatelg/24_koormus_5min")
paevane = np.isin(KOIK, PILUD)
osa = [np.where(rike[:, paevane], np.nan, ol[:, paevane] == o) for o in range(4)]
kanalid = pd.DataFrame({f"{nimi}_osa": pd.DataFrame(x, index=q.index).stack().groupby(["mp_id", "kanal"]).mean()
                        for nimi, x in zip(["vaba", "tihe", "tais", "seisak"], osa)})
kanalid = tais.to_frame("taistase_soid_h").join(h_tais.rename("H_tais")).join(kanalid, how="inner").reset_index()
save_table(kanalid.assign(kood=kanalid["mp_id"].map(jn["code"])).drop(columns="mp_id").round(4), "24_soojus_ajatelg/24_kanalid")
print("Olekute osakaal kell 06-19 (kanali 5 min pilud): " +
      ", ".join(f"{nimi} {np.nanmean(x):.1%}" for nimi, x in zip(["vaba", "tihe", "täis", "seisak"], osa)))

# --- Ristmik x kellaaeg soojuskaart, joonis päeva kohta ------------------------------------------------------------------
jarjestus = jn.sort_values("lat", ascending=False).index          # põhjast lõunasse
tunnid = np.arange(KELL[0], KELL[1] + 1)
for paev in PAEVAD:
    m = koormus.xs(paev, level="paev").reindex(index=jarjestus, columns=PILUD)
    s = seisak.xs(paev, level="paev").reindex(index=jarjestus, columns=PILUD)
    fig, ax = plt.subplots(figsize=(14, 0.13 * len(jarjestus) + 1.6), layout="constrained")
    ax.set_facecolor("#d9d8d4")
    ax.imshow(m.values, aspect="auto", cmap=CMAP, norm=NORM, interpolation="nearest",
              extent=(PILUD[0], PILUD[-1] + SAMM, len(jarjestus), 0))
    yy, xx = np.nonzero(s.values >= SEISAK_MARK * 100)
    ax.scatter(PILUD[xx] + SAMM / 2, yy + 0.5, s=3, color="black", zorder=3)
    ax.set_yticks(np.arange(len(jarjestus)) + 0.5, jn.loc[jarjestus, "code"], fontsize=6)
    ax.set_xticks(tunnid * 60, [f"{t:02d}" for t in tunnid])
    ax.set_xlabel("Kellaaeg")
    ax.grid(False)
    fig.colorbar(ScalarMappable(NORM, CMAP), ax=ax, shrink=0.6, pad=0.01, label="Ristmiku koormusaste, % läbilaskevõimest")
    fig.suptitle(f"Tallinna ristmike koormusaste 5 min kaupa: {PAEVANIMI[paev.day_of_week]} {paev:%d.%m.%Y} kell "
                 f"{KELL[0]:02d}-{KELL[1]:02d} (sõidukipõhised loendused; must täpp = vähemalt {SEISAK_MARK:.0%} seisakus, "
                 f"hall = andmed puuduvad)", x=0.01, ha="left", fontweight="bold", fontsize=11)
    save(fig, f"24_soojus_ajatelg/24_02_ristmikud_{paev:%Y-%m-%d}")

# --- Kaardid iga 5 min kohta ---------------------------------------------------------------------------------------------
lon0, lat0, lon1, lat1 = map_extent(jn, pad=0.05)
(x0, y0), (x1, y1) = to_merc(lon0, lat0), to_merc(lon1, lat1)
ratio = (x1 - x0) / (y1 - y0)
h = H_KM * 1000 / np.cos(np.radians((lat0 + lat1) / 2))            # km maapinnal -> Mercatori meetrid
gx, gy = np.meshgrid(np.linspace(x0, x1, VORK), np.linspace(y0, y1, int(VORK / ratio)))
jx, jy = to_merc(jn["lon"].values, jn["lat"].values)
W, KAUG = silu_kaalud(jx, jy, gx, gy, h)
plt.rcParams["savefig.bbox"] = "standard"                         # kõik kaadrid täpselt ühe mõõduga (MP4, GIF)
fig = plt.figure(figsize=(12, 12 * 0.86 / ratio / 0.80), dpi=DPI)
ax = fig.add_axes([0.01, 0.13, 0.86, 0.80])
cax = fig.add_axes([0.89, 0.25, 0.02, 0.6])
tax = fig.add_axes([0.06, 0.035, 0.81, 0.05])
add_basemap(ax, lon0, lat0, lon1, lat1)
im = ax.imshow(np.full(gx.shape, np.nan), extent=(x0, x1, y0, y1), origin="lower", cmap=CMAP, norm=NORM,
               interpolation="bilinear", zorder=2)
ruudud = ax.scatter(jx, jy, s=46, marker="s", c=np.zeros(len(jx)), cmap=CMAP_PUUDU, norm=NORM, edgecolor="black",
                    linewidth=0.5, zorder=4)
rongad = ax.scatter(jx, jy, s=np.zeros(len(jx)), marker="o", facecolor="none", edgecolor="black", linewidth=1.6, zorder=4.5)
for x, y, kood in zip(jx, jy, jn["code"]):
    ax.annotate(kood, (x, y), xytext=(4, 3), textcoords="offset points", fontsize=6.5, zorder=5, path_effects=HALO)
fig.colorbar(ScalarMappable(NORM, CMAP), cax=cax, label="Koormusaste, % läbilaskevõimest")
ax.legend(handles=[Line2D([], [], marker="s", ls="", color="#f8b04b", markeredgecolor="black", ms=7, label="ristmik"),
                   Line2D([], [], marker="o", ls="", markerfacecolor="none", markeredgecolor="black", markeredgewidth=1.6,
                          ms=11, label=f"vähemalt {SEISAK_MARK:.0%} seisakus"),
                   Line2D([], [], marker="s", ls="", color="#a8a7a3", markeredgecolor="black", ms=7, label="andmed puuduvad")],
          loc="upper left", fontsize=8, framealpha=0.8)
pealkiri = fig.text(0.01, 0.975, "", ha="left", va="top", fontweight="bold", fontsize=12)
keskmine = koormus.loc[jn.index].groupby("paev").mean()
tax.set_xlim(KELL[0] * 60, KELL[1] * 60)
tax.set_ylim(0, 100)
tax.set_xticks(tunnid * 60, [f"{t:02d}" for t in tunnid], fontsize=7)
tax.set_yticks([0, 50, 100], ["0", "50", "100%"], fontsize=6)
tax.tick_params(length=0)
joon, = tax.plot([], [], color=C_RED, lw=1.2)
riba = tax.axvline(KELL[0] * 60, color="black", lw=1.5)
tax.set_title("Kõigi ristmike keskmine koormusaste", fontsize=7, color=TEXT2, loc="left", pad=1)

kaadrid = []
for paev in PAEVAD:
    kz = koormus.xs(paev, level="paev").reindex(jn.index)
    sz = seisak.xs(paev, level="paev").reindex(jn.index)
    for s in PILUD:
        z, sk = kz[s].values, np.nan_to_num(sz[s].values) >= SEISAK_MARK * 100
        p, a = pind(W, KAUG, z, gx.shape)
        im.set_data(p)
        im.set_alpha(0.75 * a)
        ruudud.set_array(np.ma.masked_invalid(z))
        rongad.set_sizes(np.where(sk, 150, 0))
        pealkiri.set_text(f"Tallinna ristmike koormusaste: {PAEVANIMI[paev.day_of_week]} {paev:%d.%m.%Y} kell {kell(s)}-"
                          f"{kell(s + SAMM)} (sõidukipõhised loendused, 5 min; silumislaius "
                          f"{f'{H_KM:g}'.replace('.', ',')} km)")
        joon.set_data(PILUD[PILUD <= s] + SAMM / 2, keskmine.loc[paev, PILUD[PILUD <= s]].values)
        riba.set_xdata([s + SAMM / 2])
        f = KAUST / f"24_01_{paev:%Y-%m-%d}_{s // 60:02d}{s % 60:02d}.png"
        fig.savefig(f, dpi=DPI)
        kaadrid.append(f)
    print(f"  -> {KAUST.relative_to(DATA_DIR)}/24_01_{paev:%Y-%m-%d}_*.png ({len(PILUD)} kaarti)")
plt.close(fig)

# --- MP4 ja GIF kaartidest -----------------------------------------------------------------------------------------------
try:
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    ffmpeg = shutil.which("ffmpeg")
mp4 = KAUST / "24_01_soojus_ajatelg.mp4"
if ffmpeg:
    loend = KAUST / "_kaadrid.txt"                    # ffmpeg concat: failinimed on loendi kausta suhtes
    loend.write_text("".join(f"file '{f.name}'\nduration {1 / FPS}\n" for f in kaadrid) + f"file '{kaadrid[-1].name}'\n",
                     encoding="utf-8")
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(loend),
                    "-vf", f"fps={FPS},scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "23", str(mp4)], check=True)
    loend.unlink()
    print(f"  -> {mp4.relative_to(DATA_DIR)} ({mp4.stat().st_size / 1e6:.0f} MB)")
else:
    print("MP4 jäi tegemata: ffmpeg puudub (pip install imageio-ffmpeg)")
vaike = []
for f in kaadrid:                                     # üks fail korraga lahti (1248 kaarti)
    with Image.open(f) as p:
        korgus = round(GIF_LAIUS * p.height / p.width)
        vaike.append(p.convert("RGB").resize((GIF_LAIUS, korgus), Image.LANCZOS)
                     .quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE))
assert len({x.size for x in vaike}) == 1, "kaardid pole ühe suurusega"
gif = KAUST / "24_01_soojus_ajatelg.gif"
vaike[0].save(gif, save_all=True, append_images=vaike[1:], duration=GIF_MS, loop=0, optimize=True)
print(f"  -> {gif.relative_to(DATA_DIR)} ({gif.stat().st_size / 1e6:.0f} MB)")
print("Valmis.")
