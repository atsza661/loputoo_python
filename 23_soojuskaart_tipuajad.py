"""
23 - Tipuajad soojuskaardina: 21 tipptunni algus ja liikluse keskaeg ühtlase värvipinnana (nagu temperatuurikaart)
koos samaaja joontega. Punktkaardil (21) näeb iga koha väärtust, soojuskaardil piirkondi: kuhu tipp jõuab varem ja
kuhu hiljem ning kuidas tipuaeg linnast eemale liikudes muutub.

SISEND
  valjund/21_tipuajad.csv   skripti 21 tabel (21 käib enne): iga maantee suuna ja Tallinna ristmiku tavalise tööpäeva
                            (E-R õppetöö ajal alates 01.09.2025) hommikuse ja õhtuse tipptunni algus ja liikluse
                            keskaeg, koordinaadid ja maanteel suund (sisse / välja)
  common.add_basemap()      ortofototaust (Maa- ja Ruumiamet)

ARVUTUS
  Värvipind = loenduskohtade väärtuste Gaussi kaaluga keskmine (Nadaraya-Watsoni silumine) igas võrgusõlmes x:
    z(x) = Σ w_i z_i / Σ w_i,   w_i = exp(-d_i² / (2 h²)),   d_i = kaugus loenduskohast i maapinnal
  h = silumislaius (H_KM: Harjumaa kaardil 3 km, Tallinna kaardil 1 km). Kaalutud keskmine jääb alati mõõdetud
  väärtuste vahemikku (ei teki üle- ega alalöökeid nagu splainidel) ja üksiku loenduskoha ümber on värv selle koha
  väärtus. Kaugemal kui 2 h lähimast loenduskohast hakkab pind hajuma ja 3 h kaugusel kaob (seal mõõtmisi pole,
  paistab ortofoto). Samaaja jooned iga 5, 10, 15 või 30 min järel nii, et jooni oleks kuni 8. Hommikukaardil on maanteel suund linna poole,
  õhtukaardil linnast välja (nagu 07 ja 21); ristmikud on mõlemal.

VÄLJUND (kaust valjund/)
  23_01_soojus_harju_tipptund.png, 23_02_soojus_tallinn_tipptund.png
      Näitab: mis kell algab tööpäeva tipptund Harjumaa (Tallinna) eri osades: varase ja hilise tipuga piirkonnad.
      Kuidas: kaks kaarti ortofototaustal - hommik ja õhtu. Värv = tipptunni algus (sinine = varaseim, roheline-kollane
      = keskmine, punane = hiliseim; skaala otstes pinna varaseim ja hiliseim väärtus), valged jooned = sama kellaaja
      jooned sildiga, mustad märgid = loenduskohad (ring = maantee suund, ruut = ristmik), maanteeloendurid nimega,
      Tallinna kaardil ka ristmikud koodiga.
  23_03_soojus_harju_keskaeg.png, 23_04_soojus_tallinn_keskaeg.png
      Näitab: sama liikluse keskaja järgi (hommikul kell 6-10, õhtul 15-19), mis on tipu algusest sujuvam näitaja.
      Kuidas: nagu eelmine, värv = liikluse keskaeg.
"""
import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

from common import (OUT_DIR, add_basemap, bbox, map_extent, to_merc, hhmm, time_ticks, otsamargid, place_labels,
                    set_style, save)

H_KM = {"harju": 3, "tallinn": 1}      # silumislaius h (km); pinda joonistatakse kuni 3 h kaugusele loenduskohast
VORK = 600                             # võrgusõlmi kaardi laiuses
VARV = LinearSegmentedColormap.from_list("turbo_t", plt.get_cmap("turbo")(np.linspace(0.1, 0.93, 256)))  # sinine -> punane


def silu(x, y, z, gx, gy, h):
    """Gaussi kaaluga keskmine z võrgusõlmedes (gx, gy); kõik samades meetrites. Kaugemal kui 3 h lähimast punktist NaN.
    Tagastab pinna ja läbipaistmatuse (1 kuni 2 h kauguseni lähimast punktist, sealt 3 h-ni lineaarselt 0-ni)."""
    d2 = (gx.reshape(-1, 1) - x) ** 2 + (gy.reshape(-1, 1) - y) ** 2
    d2min = d2.min(axis=1, keepdims=True)
    w = np.exp(-(d2 - d2min) / (2 * h * h))          # lähima punkti kaal = 1: kaugel ei tule 0/0
    zz = (w @ z) / w.sum(axis=1)
    kaug = np.sqrt(d2min[:, 0]) / h
    return np.where(kaug <= 3, zz, np.nan).reshape(gx.shape), np.clip(3 - kaug, 0, 1).reshape(gx.shape)


(_z, _a) = silu(np.array([0.0, 10.0]), np.array([0.0, 0.0]), np.array([7.0, 9.0]), np.array([0.0, 5.0, 40.0]), np.zeros(3), 2.0)
assert abs(_z[0] - 7) < 1e-4 and abs(_z[1] - 8) < 1e-9 and np.isnan(_z[2]) and _a[1] == 0.5   # koha peal, keskel, kaugel

set_style()
d = pd.read_csv(OUT_DIR / "21_tipuajad.csv", encoding="utf-8-sig")
for c in ["hommik_algus", "hommik_keskaeg", "ohtu_algus", "ohtu_keskaeg"]:
    d[f"{c}_h"] = d[c].str[:2].astype(int) + d[c].str[3:5].astype(int) / 60
lo0, la0, lo1, la1 = bbox(d[d["tyyp"] == "ristmik"], pad=0.04)       # Tallinna kaardi ala nagu 07 ja 21
kaardid = {"harju": d, "tallinn": d[d["lon"].between(lo0, lo1) & d["lat"].between(la0, la1)]}

for nr_kaart, (kaart, df) in enumerate(kaardid.items()):    # joonised 23_01 ... 23_04 nagu 21
    lon0, lat0, lon1, lat1 = map_extent(df)
    (x0, y0), (x1, y1) = to_merc(lon0, lat0), to_merc(lon1, lat1)
    ratio = (x1 - x0) / (y1 - y0)
    h = H_KM[kaart] * 1000 / np.cos(np.radians((lat0 + lat1) / 2))   # km maapinnal -> Mercatori meetrid
    gx, gy = np.meshgrid(np.linspace(x0, x1, VORK), np.linspace(y0, y1, int(VORK / ratio)))
    for nr_naitaja, (naitaja, sona) in enumerate([("algus", "tipptund"), ("keskaeg", "keskaeg")]):
        fig, axes = plt.subplots(1, 2, figsize=(15, 6.3 / ratio + 1.1), layout="constrained")
        for ax, aeg, suund, lab in [(axes[0], "hommik", "sisse", "Hommik (maanteel: sissesõit linna)"),
                                    (axes[1], "ohtu", "välja", "Õhtu (maanteel: väljasõit linnast)")]:
            add_basemap(ax, lon0, lat0, lon1, lat1)
            sub = df[(df["tyyp"] == "ristmik") | (df["suund"] == suund)]
            mx, my = to_merc(sub["lon"].values, sub["lat"].values)
            pind, katvus = silu(mx, my, sub[f"{aeg}_{naitaja}_h"].values, gx, gy, h)
            vmin, vmax = np.nanmin(pind), np.nanmax(pind)
            im = ax.imshow(pind, extent=(x0, x1, y0, y1), origin="lower", cmap=VARV, vmin=vmin, vmax=vmax, alpha=0.8 * katvus,
                           interpolation="bilinear", zorder=2)
            samm = next((m for m in (5, 10, 15) if (vmax - vmin) * 60 / m <= 8), 30)    # jooni kuni 8
            jooned = ax.contour(gx, gy, pind, levels=np.arange(np.ceil(vmin * 60 / samm) * samm, vmax * 60, samm) / 60,
                                colors="white", linewidths=0.9, zorder=3)
            ax.clabel(jooned, fmt=hhmm, fontsize=7)
            for tyyp, marker in [("maantee", "o"), ("ristmik", "s")]:
                m = (sub["tyyp"] == tyyp).values
                ax.scatter(mx[m], my[m], s=12, marker=marker, color="black", edgecolor="white", linewidth=0.5, zorder=4)
            named = sub[(sub["tyyp"] == "maantee") | (kaart == "tallinn")]
            lx, ly = to_merc(named["lon"].values, named["lat"].values)
            place_labels(ax, lx, ly, list(named["nimi"].where(named["tyyp"] == "maantee", named["koht"])),
                         obstacles=(mx, my, np.full(len(mx), 12.0)))
            ax.set_title(f"{lab}: {'tipptunni algus' if naitaja == 'algus' else 'liikluse keskaeg'}", fontsize=11)
            cb = fig.colorbar(im, ax=ax, shrink=0.75)
            cb.set_ticks(time_ticks(vmin, vmax))
            otsamargid(cb, hhmm)
            cb.set_label({"algus": "Tipptunni algus", "keskaeg": "Liikluse keskaeg"}[naitaja] + " (sinine = varem, punane = hiljem)")
        fig.suptitle(f"{'Millal algab tipptund' if naitaja == 'algus' else 'Millal liiklus toimub (mahuga kaalutud keskmine kellaaeg)'}"
                     f" - soojuskaart (15 min loendused, tavaline tööpäev; silumislaius {str(H_KM[kaart]).replace('.', ',')} km)",
                     x=0.01, ha="left", fontweight="bold")
        fig.canvas.draw()
        bottom = min(a.get_position().y0 for a in axes)
        fig.legend(handles=[Line2D([], [], marker="s", ls="", color="black", ms=5, label="linna ristmik"),
                            Line2D([], [], marker="o", ls="", color="black", ms=5, label="maantee loendur (suund)"),
                            Line2D([], [], color="white", lw=1.5, label="sama kellaaja joon",
                                   path_effects=[pe.Stroke(linewidth=3, foreground="#666666"), pe.Normal()])],
                   loc="upper center", bbox_to_anchor=(0.5, bottom - 0.005), ncol=3, fontsize=9)
        save(fig, f"23_{2 * nr_naitaja + nr_kaart + 1:02d}_soojus_{kaart}_{sona}")
print("Valmis.")
