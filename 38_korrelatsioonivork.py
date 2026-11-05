"""
38 - Ristmike korrelatsioonivõrk: kui ühel ristmikul on tavalisest rohkem või vähem liiklust, kas sama juhtub ka
naaberristmikel? Linna ühine kõikumine (ilm, pühad, kooliaeg) võetakse enne välja, nii et alles jääb kohalik seos.

SISEND
  common.load_tallinn()      ristmike 15 min loendused puhastatult (tallinn.count_15min)
  common.load_junctions(), add_basemap()   ristmike koordinaadid ja kaardi taust

ARVUTUS
  Päevad: tavalised tööpäevad (E-R, õppetöö, mitte püha ega lühendatud päev), kogu andmeperiood.
  Iga ristmiku ja päeva kohta kolm mahtu: ööpäev, hommik 07:00-09:00 ja õhtu 16:00-18:00 (15 min väärtuste summa).
  Kõrvalekalle = log(maht) - sama ristmiku log(maht) liikuv mediaan (TASE tööpäeva, keskel) - ristmiku nädalapäeva
    keskmine sellest: tavaline tase, nädalapäev ja aeglased muutused (hooaeg, ehitus) välja. Lühike aken on oluline:
    loenduri vahetuse vms astmeline tasemenihe annab kõrvalekalde ainult mõnele päevale nihke ümber (pika aknaga
    paistaksid kaks samal ajal nihkunud kauget ristmikku tugevalt seotuna).
  Linna osa välja: kõrvalekalle - kõigi ristmike sama päeva kõrvalekallete mediaan. Alles jääb ristmiku oma kõikumine.
  Seos = Pearsoni korrelatsioon kahe ristmiku jääkide vahel ühistel päevadel (vähemalt MIN_PAEVI).
  Kaugus = linnulennult (common.km). Kaugusvööndi seos = vööndi paaride korrelatsiooni mediaan.
  Kaardil seosed r >= R_KAART (ööpäev).

VÄLJUND (kaust valjund/)
  38_01_korrelatsioonivork.png
      Näitab: millised ristmikud kõiguvad päevast päeva koos (ühine kohalik nõudlus, sama marsruut või ümbersõit).
      Kuidas: kaart (ortofoto); valge ring = ristmik (suurus = seoste arv), joon = seos r >= R_KAART, joone paksus ja
      toon = r (tumedam ja paksem = tugevam). Silt = ristmiku kood.
  38_02_kaugus.png
      Näitab: kas lähedased ristmikud on tugevamalt seotud kui kauged ja kas tipptundidel on seos tugevam kui ööpäeval.
      Kuidas: x = kaugus, km; y = korrelatsioon; hall punkt = ristmike paar (ööpäev); joon = kaugusvööndi mediaan
      (must = ööpäev, sinine = hommik 07-09, oranž = õhtu 16-18).
  38_paarid.csv     paar: kaugus, päevi, r (ööpäev, hommik, õhtu)
  38_kaugus.csv     kaugusvöönd: paare, r mediaanid
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

from common import (load_tallinn, load_junctions, add_basemap, to_merc, map_extent, km, set_style, save, save_table, HALO,
                    ramp, C_BLUE, C_ORANGE, C_GRAY, TEXT, TEXT2)

AKNAD = {"ooopaev": (0, 96), "hommik": (28, 36), "ohtu": (64, 72)}     # 15 min pilud
MIN_PAEVI = 150
R_KAART = 0.3
VOONDID = [0, 1, 2, 3, 5, 8, 12, 25]
TASE = 11


def korvalekalle(x):
    """Ristmiku päevamahud (indeks paev, tööpäevad) -> log(maht) - liikuv mediaan (TASE päeva) - nädalapäeva keskmine."""
    lx = np.log(x)
    j = lx - lx.rolling(TASE, center=True, min_periods=5).median()
    return j - j.groupby(j.index.day_of_week).transform("mean")


_x = pd.Series(100.0, index=pd.bdate_range("2025-01-06", periods=100))
_x.iloc[50] = 150
_k = korvalekalle(_x)
assert abs(_k.iloc[50] - np.log(1.5)) < 0.05 and abs(_k.drop(_k.index[50])).max() < 0.03          # üks erandpäev
_k = korvalekalle(pd.Series(np.r_[np.full(50, 100.0), np.full(50, 130.0)], index=_x.index))
assert (_k.abs() > 0.02).sum() <= TASE                                                             # astmeline nihe

set_style()
jn = load_junctions().set_index("mp_id")
t, d = load_tallinn()
d = d[d["kehtiv"] & (d["paevatyyp"] == "tööpäev") & (d["vaheaeg"] == "kool")]
t = t.merge(d[["mp_id", "paev"]], on=["mp_id", "paev"])
jaagid = {}
for nimi, (a, b) in AKNAD.items():
    z = t[t["slot"].between(a, b - 1)].groupby(["mp_id", "paev"])["v"].agg(["sum", "count"])
    z = z.loc[z["count"] >= 0.9 * (b - a), "sum"].unstack("mp_id")
    k = z.apply(korvalekalle)
    jaagid[nimi] = k.sub(k.median(axis=1), axis=0)
mps = jaagid["ooopaev"].columns
rows = []
for i, a in enumerate(mps):
    for b in mps[i + 1:]:
        r = dict(a=jn.loc[a, "code"], b=jn.loc[b, "code"], kaugus_km=km(jn.loc[a, "lat"], jn.loc[a, "lon"], jn.loc[b, "lat"],
                                                                         jn.loc[b, "lon"]))
        for nimi, j in jaagid.items():
            if a in j and b in j:
                z = j[[a, b]].dropna()
                r[f"paevi_{nimi}"] = len(z)
                r[f"r_{nimi}"] = z[a].corr(z[b]) if len(z) >= MIN_PAEVI else np.nan
        rows.append(r)
p = pd.DataFrame(rows)
save_table(p.round(4), "38_paarid")
p["vood"] = pd.cut(p["kaugus_km"], VOONDID)
kv = p.groupby("vood", observed=True).agg(paare=("r_ooopaev", "count"),
                                          **{f"r_{n}": (f"r_{n}", "median") for n in AKNAD}).reset_index()
kv["vood"] = kv["vood"].astype(str)
save_table(kv.round(3), "38_kaugus")

# --- joonis 1: kaart -------------------------------------------------------------------------------------------------------
koht = jn.set_index("code")[["lat", "lon"]]
koht = koht.loc[koht.index.isin(p["a"]) | koht.index.isin(p["b"])].dropna()
lon0, lat0, lon1, lat1 = map_extent(koht)
fig, ax = plt.subplots(figsize=(12, 10))
add_basemap(ax, lon0, lat0, lon1, lat1)
l = p[p["r_ooopaev"] >= R_KAART].sort_values("r_ooopaev")
cmap, norm = ramp("Reds"), Normalize(R_KAART, max(0.7, l["r_ooopaev"].max() if len(l) else 0.7))
for _, r in l.iterrows():
    (xa, ya), (xb, yb) = to_merc(koht.loc[r["a"], "lon"], koht.loc[r["a"], "lat"]), to_merc(koht.loc[r["b"], "lon"],
                                                                                           koht.loc[r["b"], "lat"])
    ax.plot([xa, xb], [ya, yb], color=cmap(norm(r["r_ooopaev"])), lw=1 + 7 * (r["r_ooopaev"] - R_KAART), zorder=3,
            solid_capstyle="round")
aste = pd.concat([l["a"], l["b"]]).value_counts().reindex(koht.index, fill_value=0)
px, py = to_merc(koht["lon"].values, koht["lat"].values)
ax.scatter(px, py, s=30 + 25 * aste.values, color="white", edgecolor=TEXT, lw=1, zorder=4)
for xx, yy, c in zip(px, py, koht.index):
    ax.annotate(c[2:], (xx, yy), xytext=(5, 4), textcoords="offset points", fontsize=7.5, zorder=6, path_effects=HALO)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
cb = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.01)
cb.set_label("korrelatsioon r (päevast päeva kõrvalekalded, linna osa välja)")
ax.set_title(f"Ristmikud, mis kõiguvad koos: {len(l)} seost r >= {R_KAART:.1f} ({len(p)} paarist), ".replace(".", ",")
             + "tööpäevade ööpäevane liiklus")
save(fig, "38_01_korrelatsioonivork")

# --- joonis 2: kaugus -----------------------------------------------------------------------------------------------------
fig, a = plt.subplots(figsize=(10, 6))
a.scatter(p["kaugus_km"], p["r_ooopaev"], s=8, color=C_GRAY, alpha=0.5, label="paar (ööpäev)")
kesk = [(lo + hi) / 2 for lo, hi in zip(VOONDID[:-1], VOONDID[1:])]
kv2 = p.groupby("vood", observed=False)[[f"r_{n}" for n in AKNAD]].median()
for n, c, s in [("ooopaev", TEXT, "ööpäev"), ("hommik", C_BLUE, "hommik 07-09"), ("ohtu", C_ORANGE, "õhtu 16-18")]:
    a.plot(kesk, kv2[f"r_{n}"].values, color=c, lw=2.4, marker="o", label=f"mediaan: {s}")
a.axhline(0, color=TEXT, lw=0.8)
a.set_xlabel("kaugus linnulennult, km")
a.set_ylabel("korrelatsioon r")
a.set_title("Kas lähedased ristmikud kõiguvad rohkem koos?")
a.legend(fontsize=9)
fig.tight_layout()
save(fig, "38_02_kaugus")

print(f"paare {len(p)}, seoseid r >= {R_KAART}: {len(l)}; r mediaan ööpäev {p['r_ooopaev'].median():.3f}, hommik "
      f"{p['r_hommik'].median():.3f}, õhtu {p['r_ohtu'].median():.3f}")
print(kv.to_string(index=False))
print(p.nlargest(12, "r_ooopaev")[["a", "b", "kaugus_km", "r_ooopaev", "r_hommik", "r_ohtu"]].round(2).to_string(index=False))
