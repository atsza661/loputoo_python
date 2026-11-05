"""
25 - Ristmike koormusaste päevatüübi kaupa soojuskaardina (23 kujundus): kui koormatud on Tallinna ristmikud igal
5 minutil kell 06.00-19.00 keskmisel teisipäevast neljapäevani ning eraldi esmaspäeval, reedel, laupäeval ja pühapäeval.
Kaart iga 5 min kohta, iga päevatüübi kaartidest GIF ja MP4; kaardi kõrval väike võrdlus, kuidas päevatüübid erinevad
liikluse mahu ja koormusastme poolest.

SISEND
  valjund/24_soojus_ajatelg/24_koormus_5min.csv   skripti 24 tabel (24 käib enne): iga ristmiku koormusaste (% kanalite
                                                  läbilaskevõimest, seisak = täis) ja sõidukite arv igal 5 min pilul
                                                  kell 06-19 logija päevadel 16.-23.10.2026
  common.load_junctions()                         ristmike koordinaadid
  common.add_basemap()                            ortofototaust (Maa- ja Ruumiamet)

ARVUTUS
  Päevatüübid (TYYBID): teisipäev-neljapäev (20.-22.10, kolme päeva keskmine), esmaspäev (19.10), reede (16. ja 23.10
  keskmine), laupäev (17.10), pühapäev (18.10). Ristmiku koormusaste päevatüübil = tüübi päevade koormusastme keskmine
  samal kellaajal (puuduvad päevad jäetakse välja; kui puuduvad kõik, on ristmik puuduv).
  Värvipind ja jooned nagu 23: Gaussi kaaluga keskmine (Nadaraya-Watsoni silumine) z(x) = Σ w_i z_i / Σ w_i,
  w_i = exp(-d_i² / (2 h²)), h = H_KM; pind hajub 2 h ja kaob 3 h kaugusel lähimast ristmikust, millel on andmed.
  Värviskaala on kõigil kaartidel sama (SKAALA), et kaadreid ja päevatüüpe saaks võrrelda; valged jooned = sama
  koormusastme jooned iga JOONE_SAMM protsendipunkti järel.
  Kõrvalgraafik: päevatüübi kõigi ristmike sõidukite summa 5 min pilus (tüübi päevade keskmine; tunnis = x 12) ja
  ristmike keskmine koormusaste igal kellaajal.
  ponytail: sõidukite summas on rikke ajal puuduvad kanalid 0 (24 loeb sõidukeid ka rikkega kanalitel), seega päeval
  rikkega (17.-19.10 port 63) on summa veidi väiksem; koormusaste rikkeid arvesse ei võta.

VÄLJUND (kaust valjund/25_soojus_paevatyybid/)
  25_01_<tüüp>_<HHMM>.png   (5 tüüpi x 156 kaarti; tüüp = t-n, e, r, l, p)
      Näitab: kui koormatud on Tallinna ristmikud päevatüübi ühel 5 minutil ja kuidas koormus linnas paikneb.
      Kuidas: vasakul Tallinna kaart ortofototaustal nagu 23: värvipind = koormusaste (sinine = vaba, roheline-kollane =
      keskmine, punane = läbilaskevõimel; skaala SKAALA), valged jooned = sama koormusastme jooned sildiga, mustad
      ruudud = ristmikud koodiga. Paremal kaks väikest graafikut kell 06-19: üleval kõigi ristmike sõidukeid tunnis,
      all ristmike keskmine koormusaste; joon iga päevatüübi kohta (kaardi tüüp paksult, legend graafikute all), must
      püstjoon = kaardi aeg.
  25_01_<tüüp>.mp4, 25_01_<tüüp>.gif
      Näitab: päevatüübi kaardid liikuva pildina (MP4 FPS kaadrit sekundis; GIF GIF_LAIUS pikslit lai).
  25_02_paevatyybid_vordlus.png
      Näitab: kõrvalgraafik suurelt: kuidas päevatüübid erinevad liikluse mahu ja koormusastme poolest kell 06-19.
      Kuidas: vasakul kõigi ristmike sõidukeid tunnis, paremal keskmine koormusaste; joon iga päevatüübi kohta.
  25_paevatyybid.csv     iga päevatüüp, ristmik ja 5 min pilu: koormusaste %, sõidukeid 5 min, päevi arvesse
"""
import shutil
import subprocess

import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from PIL import Image

from common import (OUT_DIR, DATA_DIR, load_junctions, add_basemap, to_merc, map_extent, place_labels, otsamargid,
                    set_style, save, save_table, C_BLUE, C_AQUA, C_ORANGE, C_VIOLET, C_RED, TEXT2)

TYYBID = {                           # failinimi: (silt, päevad, joone värv)
    "t-n": ("Teisipäev-neljapäev (20.-22.10 keskmine)", ["2026-10-20", "2026-10-21", "2026-10-22"], C_BLUE),
    "e": ("Esmaspäev (19.10)", ["2026-10-19"], C_AQUA),
    "r": ("Reede (16. ja 23.10 keskmine)", ["2026-10-16", "2026-10-23"], C_ORANGE),
    "l": ("Laupäev (17.10)", ["2026-10-17"], C_VIOLET),
    "p": ("Pühapäev (18.10)", ["2026-10-18"], C_RED),
}
KELL = (6, 19)
SAMM = 5
SKAALA = (0, 100)                    # koormusaste %: ühine värviskaala kõigil kaartidel
JOONE_SAMM = 10                      # sama koormusastme jooned iga 10 protsendipunkti järel
H_KM = 1.0                           # silumislaius (km), nagu 23 Tallinna kaardil
VORK = 600                           # võrgusõlmi kaardi laiuses (nagu 23)
DPI = 100                            # 780 ortofotokaarti: 200 dpi annaks mitu GB
FPS = 8
GIF_LAIUS, GIF_MS = 480, 125
VARV = LinearSegmentedColormap.from_list("turbo_t", plt.get_cmap("turbo")(np.linspace(0.1, 0.93, 256)))  # nagu 23
NORM = Normalize(*SKAALA)
SISSE = OUT_DIR / "24_soojus_ajatelg" / "24_koormus_5min.csv"
KAUST = OUT_DIR / "25_soojus_paevatyybid"
PILUD = np.arange(KELL[0] * 60, KELL[1] * 60, SAMM)


def silu(d2, z, h):
    """Gaussi kaaluga keskmine võrgusõlmedes nagu 23 silu(), kaugused ette arvutatud: d2 = (sõlm x ristmik) ruutkaugused,
    z = ristmike väärtused (NaN = puuduv, ei loe). Kaugemal kui 3 h lähimast ristmikust NaN. Tagastab pinna ja
    läbipaistmatuse (1 kuni 2 h kauguseni lähimast ristmikust, sealt 3 h-ni lineaarselt 0-ni)."""
    ok = ~np.isnan(z)
    if not ok.any():
        return np.full(len(d2), np.nan), np.zeros(len(d2))
    d = d2[:, ok]
    dmin = d.min(axis=1, keepdims=True)
    w = np.exp(-(d - dmin) / (2 * h * h))           # lähima punkti kaal = 1: kaugel ei tule 0/0
    zz = (w @ z[ok]) / w.sum(axis=1)
    kaug = np.sqrt(dmin[:, 0]) / h
    return np.where(kaug <= 3, zz, np.nan), np.clip(3 - kaug, 0, 1)


_d2 = (np.array([[0.0], [5.0], [40.0]]) - np.array([0.0, 10.0])) ** 2
_z, _a = silu(_d2, np.array([7.0, 9.0]), 2.0)
assert abs(_z[0] - 7) < 1e-4 and abs(_z[1] - 8) < 1e-9 and np.isnan(_z[2]) and _a[1] == 0.5   # koha peal, keskel, kaugel
_z, _ = silu(_d2, np.array([7.0, np.nan]), 2.0)
assert abs(_z[1] - 7) < 1e-9                                                                 # puuduv ristmik ei loe


def kell(s):
    """Minutid keskööst -> 'HH:MM'."""
    return f"{s // 60:02d}:{s % 60:02d}"


def kellateljed(ax, fs=7):
    """Kellaaja x-telg 06-19 (minutid keskööst), sildid iga 2 tunni järel."""
    ax.set_xlim(KELL[0] * 60, KELL[1] * 60)
    t = np.arange(KELL[0], KELL[1] + 1, 2)
    ax.set_xticks(t * 60, [f"{x:02d}" for x in t], fontsize=fs)


set_style()
KAUST.mkdir(parents=True, exist_ok=True)

# --- 24 tabel -> päevatüübi keskmised ----------------------------------------------------------------------------------
d = pd.read_csv(SISSE, encoding="utf-8-sig")
d["pilu"] = d["kell"].str[:2].astype(int) * 60 + d["kell"].str[3:5].astype(int)
puudu = {p for _, paevad, _ in TYYBID.values() for p in paevad} - set(d["paev"])
assert not puudu, f"24 tabelis pole päevi {sorted(puudu)}: käivita enne 24_soojus_ajatelg.py"
d["tyyp"] = d["paev"].map({p: t for t, (_, paevad, _) in TYYBID.items() for p in paevad})
d = d[d["tyyp"].notna() & d["pilu"].isin(PILUD)]
g = d.groupby(["tyyp", "kood", "pilu"])
k = pd.DataFrame({"koormus": g["koormus_pct"].mean(), "soidukeid": g["soidukeid"].mean(),
                  "paevi": g["koormus_pct"].count()})
assert k["koormus"].dropna().between(*SKAALA).all()
jn = load_junctions().dropna(subset=["lat", "lon"]).set_index("code")
jn = jn.loc[jn.index.intersection(k.index.get_level_values("kood").unique())]
save_table(k.reset_index().assign(kell=lambda z: z["pilu"].map(kell), silt=lambda z: z["tyyp"].map(lambda t: TYYBID[t][0]))
           [["tyyp", "silt", "kood", "kell", "koormus", "soidukeid", "paevi"]]
           .rename(columns={"koormus": "koormus_pct", "soidukeid": "soidukeid_5min"}).round(2),
           "25_soojus_paevatyybid/25_paevatyybid")

# kõrvalgraafiku read: kõigi ristmike sõidukeid tunnis (tüübi päevade keskmine) ja ristmike keskmine koormusaste
paeva_summa = d.groupby(["tyyp", "paev", "pilu"])["soidukeid"].sum() * 60 / SAMM
voog = paeva_summa.groupby(["tyyp", "pilu"]).mean().unstack("pilu").reindex(columns=PILUD)
koorm = k["koormus"].groupby(["tyyp", "pilu"]).mean().unstack("pilu").reindex(columns=PILUD)
print("Päevatüübid kell 06-19: " + "; ".join(
    f"{t}: {voog.loc[t].sum() * SAMM / 60 / 1000:.0f} tuh sõidukit, koormusaste {koorm.loc[t].mean():.0f}%" for t in TYYBID))


def vordlus(ax_v, ax_k, praegu=None, fs=7):
    """Päevatüüpide võrdlus kahel teljel: sõidukeid tunnis ja keskmine koormusaste; praegu = (tüüp, pilu) kaardil."""
    for t, (silt, _, varv) in TYYBID.items():
        paks = praegu is None or praegu[0] == t
        for ax, rida in [(ax_v, voog.loc[t]), (ax_k, koorm.loc[t])]:
            ax.plot(PILUD + SAMM / 2, rida.values, color=varv, lw=2.0 if paks else 0.9, alpha=1 if paks else 0.6,
                    label=silt.split(" (")[0], zorder=3 if paks else 2)
    ax_v.yaxis.set_major_formatter(lambda x, _: f"{x / 1000:.0f} tuh")
    ax_k.set_ylim(0, 100)
    ax_k.yaxis.set_major_formatter(lambda x, _: f"{x:.0f}%")
    for ax in (ax_v, ax_k):
        kellateljed(ax, fs)
        ax.tick_params(labelsize=fs)


fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 4.5), layout="constrained")
vordlus(a1, a2, fs=9)
a1.set_title("Kõigi ristmike sõidukeid tunnis", fontsize=11)
a2.set_title("Ristmike keskmine koormusaste (% läbilaskevõimest)", fontsize=11)
a1.set_xlabel("Kellaaeg")
a2.set_xlabel("Kellaaeg")
fig.legend(*a1.get_legend_handles_labels(), loc="outside lower center", ncol=len(TYYBID), fontsize=10)
fig.suptitle(f"Päevatüüpide erinevus Tallinna ristmikel kell {KELL[0]:02d}-{KELL[1]:02d} (sõidukipõhised loendused "
             f"16.-23.10.2026, 5 min)", x=0.01, ha="left", fontweight="bold")
save(fig, "25_soojus_paevatyybid/25_02_paevatyybid_vordlus")

# --- Kaardid -------------------------------------------------------------------------------------------------------------
lon0, lat0, lon1, lat1 = map_extent(jn, pad=0.05)
(x0, y0), (x1, y1) = to_merc(lon0, lat0), to_merc(lon1, lat1)
ratio = (x1 - x0) / (y1 - y0)
h = H_KM * 1000 / np.cos(np.radians((lat0 + lat1) / 2))            # km maapinnal -> Mercatori meetrid
gx, gy = np.meshgrid(np.linspace(x0, x1, VORK), np.linspace(y0, y1, int(VORK / ratio)))
jx, jy = to_merc(jn["lon"].values, jn["lat"].values)
D2 = (gx.reshape(-1, 1) - jx) ** 2 + (gy.reshape(-1, 1) - jy) ** 2
plt.rcParams["savefig.bbox"] = "standard"                         # kõik kaadrid ühe mõõduga (MP4, GIF)
kaardi_k = 9.0 / ratio                                            # kaardi kõrgus tollides 9 tolli laiuse juures
fig = plt.figure(figsize=(15, kaardi_k + 1.3), dpi=DPI)
H_ = kaardi_k + 1.3
ax = fig.add_axes([0.01, 0.6 / H_, 9.0 / 15, kaardi_k / H_])
cax = fig.add_axes([9.25 / 15, 0.6 / H_ + 0.1 * kaardi_k / H_, 0.15 / 15, 0.8 * kaardi_k / H_])
ax_v = fig.add_axes([11.15 / 15, 0.6 / H_ + 0.55 * kaardi_k / H_, 3.65 / 15, 0.36 * kaardi_k / H_])
ax_k = fig.add_axes([11.15 / 15, 0.6 / H_ + 0.08 * kaardi_k / H_, 3.65 / 15, 0.36 * kaardi_k / H_])
add_basemap(ax, lon0, lat0, lon1, lat1)
im = ax.imshow(np.full(gx.shape, np.nan), extent=(x0, x1, y0, y1), origin="lower", cmap=VARV, norm=NORM,
               interpolation="bilinear", zorder=2)
ax.scatter(jx, jy, s=12, marker="s", color="black", edgecolor="white", linewidth=0.5, zorder=4)
place_labels(ax, jx, jy, list(jn.index), obstacles=(jx, jy, np.full(len(jx), 12.0)))
cb = fig.colorbar(im, cax=cax)
otsamargid(cb, lambda x: f"{x:.0f}%")
cb.set_label("Koormusaste, % läbilaskevõimest (sinine = vaba, punane = täis)")
fig.legend(handles=[Line2D([], [], marker="s", ls="", color="black", ms=5, label="ristmik"),
                    Line2D([], [], color="white", lw=1.5, label="sama koormusastme joon",
                           path_effects=[pe.Stroke(linewidth=3, foreground="#666666"), pe.Normal()])],
           loc="lower left", bbox_to_anchor=(0.01, 0.0), ncol=2, fontsize=9)
fig.legend(handles=[Line2D([], [], color=varv, lw=2, label=silt.split(" (")[0]) for silt, _, varv in TYYBID.values()],
           loc="lower left", bbox_to_anchor=(11.0 / 15, 0.0), ncol=3, fontsize=8, handlelength=1.5)
pealkiri = fig.text(0.01, 1 - 0.15 / H_, "", ha="left", va="top", fontweight="bold", fontsize=12)
ax_v.set_title("Kõigi ristmike sõidukeid tunnis", fontsize=8, color=TEXT2, loc="left")
ax_k.set_title("Ristmike keskmine koormusaste", fontsize=8, color=TEXT2, loc="left")
jooned = []
taseme_jooned = np.arange(SKAALA[0] + JOONE_SAMM, SKAALA[1], JOONE_SAMM)

try:
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    ffmpeg = shutil.which("ffmpeg")
for t, (silt, paevad, _) in TYYBID.items():
    for a in (ax_v, ax_k):
        a.clear()
    vordlus(ax_v, ax_k, praegu=(t, None))
    ax_v.set_title("Kõigi ristmike sõidukeid tunnis", fontsize=8, color=TEXT2, loc="left")
    ax_k.set_title("Ristmike keskmine koormusaste", fontsize=8, color=TEXT2, loc="left")
    ajad = [a.axvline(KELL[0] * 60, color="black", lw=1.2, zorder=4) for a in (ax_v, ax_k)]
    z_t = k["koormus"].xs(t, level="tyyp").unstack("pilu").reindex(index=jn.index, columns=PILUD)
    kaadrid = []
    for s in PILUD:
        p, a = silu(D2, z_t[s].values, h)
        p, a = p.reshape(gx.shape), a.reshape(gx.shape)
        im.set_data(p)
        im.set_alpha(0.8 * a)
        for c in jooned:
            c.remove()
        jooned = []
        if np.isfinite(p).any():
            cs = ax.contour(gx, gy, p, levels=taseme_jooned, colors="white", linewidths=0.9, zorder=3)
            ax.clabel(cs, fmt=lambda x: f"{x:.0f}%", fontsize=7)
            jooned = [cs]
        for v in ajad:
            v.set_xdata([s + SAMM / 2])
        pealkiri.set_text(f"Tallinna ristmike koormusaste: {silt}, kell {kell(s)}-{kell(s + SAMM)} "
                          f"(sõidukipõhised loendused, 5 min; silumislaius {f'{H_KM:g}'.replace('.', ',')} km)")
        f = KAUST / f"25_01_{t}_{s // 60:02d}{s % 60:02d}.png"
        fig.savefig(f, dpi=DPI)
        kaadrid.append(f)
    print(f"  -> {KAUST.relative_to(DATA_DIR)}/25_01_{t}_*.png ({len(kaadrid)} kaarti)")

    # MP4 ja GIF selle päevatüübi kaartidest
    if ffmpeg:
        loend = KAUST / "_kaadrid.txt"                # ffmpeg concat: failinimed on loendi kausta suhtes
        loend.write_text("".join(f"file '{f.name}'\nduration {1 / FPS}\n" for f in kaadrid) + f"file '{kaadrid[-1].name}'\n",
                         encoding="utf-8")
        mp4 = KAUST / f"25_01_{t}.mp4"
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(loend),
                        "-vf", f"fps={FPS},scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-crf", "23", str(mp4)], check=True)
        loend.unlink()
        print(f"  -> {mp4.relative_to(DATA_DIR)} ({mp4.stat().st_size / 1e6:.0f} MB)")
    else:
        print("MP4 jäi tegemata: ffmpeg puudub (pip install imageio-ffmpeg)")
    vaike = []
    for f in kaadrid:
        with Image.open(f) as pilt:
            vaike.append(pilt.convert("RGB").resize((GIF_LAIUS, round(GIF_LAIUS * pilt.height / pilt.width)), Image.LANCZOS)
                         .quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE))
    assert len({x.size for x in vaike}) == 1, "kaardid pole ühe suurusega"
    gif = KAUST / f"25_01_{t}.gif"
    vaike[0].save(gif, save_all=True, append_images=vaike[1:], duration=GIF_MS, loop=0, optimize=True)
    print(f"  -> {gif.relative_to(DATA_DIR)} ({gif.stat().st_size / 1e6:.0f} MB)")
plt.close(fig)
print("Valmis.")
