"""
34 - Ristmike profiilitüübid: ristmike rühmitamine tööpäeva liikluse KUJU järgi (mitte mahu järgi) - kus on terav
pendeltipp, kus õhtune tipp, kus päev on ühtlane - ja rühmad kaardil.

SISEND
  common.load_tallinn()      ristmike 15 min loendused puhastatult (tallinn.count_15min)
  common.load_junctions(), add_basemap()   ristmike koordinaadid ja kaardi taust

ARVUTUS
  Tüüpiline tööpäev (nagu 06 ja 31): E-R õppetöö ajal, mitte püha, alates ALGUS; profiil = iga pilu keskmine.
  Kuju: 30 min summad kell 05:00-23:00 (36 väärtust), igaüks % ristmiku ööpäevast (maht ei loe, ainult jaotus).
  Rühmitamine: hierarhiline klasterdamine Wardi meetodiga (eukleidiline kaugus kujude vahel; scipy). Rühmi K = 3:
    siluetiindeks (kui selgelt ristmik oma rühma kuulub, -1...1) on k = 2...7 juures 0,15-0,25 ehk kujud erinevad
    mõõdukalt ja rühmade piirid on pehmed; k = 2 eraldab ainult pendelristmikud, k = 3 lisab õhtutipuga rühma, suurem
    k annab üksikute ristmike rühmi. Kõigi k siluetid on tabelis 34_siluett.csv.
  Rühma nimi tuleb keskmise kuju näitajatest (mitte käsitsi): tipu teravus = (hommiku- ja õhtutipu 30 min osakaal) /
    keskpäeva (10-14) keskmine 30 min osakaal; hommik/õhtu = tippude suhe. Lameim rühm = "ühtlane päev", teised
    "õhtutipuga" (hommik/õhtu < 0,9) või "kaks teravat tippu".
  Kaugus kesklinnast = linnulennult Vabaduse väljakust (KESKLINN).

CALCULATION IN PLAIN ENGLISH
  Typical workday profile (as in 06). Shape = 30-minute sums 05:00-23:00 (36 values), each as % of the junction's daily
    total (volume does not matter, only the split).
  Grouping: hierarchical Ward clustering on the Euclidean distance between shapes, K = 3 groups; silhouette (-1 ... 1)
    shows how clearly a junction belongs to its group.
  Group names from the average shape: peak sharpness = (morning and evening top 30-minute shares) / average 30-minute
    share 10-14; morning/evening = ratio of the two peaks. Distance from the centre = straight line from Vabaduse
    väljak.

VÄLJUND (kaust valjund/)
  34_01_profiilituubid.png
      Näitab: millised on Tallinna ristmike tööpäeva liikluse põhikujud ja kus need ristmikud asuvad.
      Kuidas: vasakul kaart (ortofoto): punkt = ristmik, värv = rühm, silt = kood. Paremal paneel rühma kohta: x =
      kellaaeg 05-23, y = % ööpäeva liiklusest 30 min kohta; peenikesed jooned = rühma ristmikud, jäme joon = rühma
      keskmine, hall katkendjoon = kõigi ristmike keskmine. Pealkirjas rühma nimi, ristmike arv ja mediaankaugus
      kesklinnast.
  34_02_dendrogramm.png
      Näitab: kui sarnased on ristmike profiilid ja kuidas rühmad tekivad.
      Kuidas: dendrogramm; x = ristmik, y = Wardi kaugus (mida madalamal kaks haru ühinevad, seda sarnasem kuju); harude
      värv = rühm, hall katkendjoon = lõikekõrgus K rühma jaoks.
  34_profiilituubid.csv   ristmik: rühm, rühma nimi, kaugus kesklinnast, siluett, kuju näitajad
  34_siluett.csv          k = 2...7: keskmine siluett ja rühmade suurused
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram, set_link_color_palette
from scipy.spatial.distance import pdist, squareform

from common import (load_tallinn, load_junctions, add_basemap, to_merc, map_extent, km, set_style, save, save_table,
                    HALO, C_BLUE, C_ORANGE, C_AQUA, C_GRAY, TEXT2)

ALGUS = "2025-09-01"
K = 3
KELL = (10, 46)                              # 30 min pilud 05:00 ... 22:30 (lõpp välja arvatud)
KESKLINN = (59.4339, 24.7449)                # Vabaduse väljak
VARVID = [C_BLUE, C_ORANGE, C_AQUA]          # rühmad suuruse järjekorras


def siluett(D, lab):
    """Keskmine siluetiindeks kauguste maatriksist D ja rühmadest lab."""
    s = []
    for i in range(len(lab)):
        sama = lab == lab[i]
        sama[i] = False
        if not sama.any():
            s.append(0.0)
            continue
        a = D[i, sama].mean()
        b = min(D[i, lab == c].mean() for c in np.unique(lab) if c != lab[i])
        s.append((b - a) / max(a, b))
    return np.array(s)


def naitajad(kuju):
    """Kuju (30 min pilud 0..47, % ööpäevast) -> hommikutipp, õhtutipp, keskpäev, teravus, hommik/õhtu."""
    h, o, k = kuju.loc[12:19].max(), kuju.loc[28:37].max(), kuju.loc[20:27].mean()
    return dict(hommik=h, ohtu=o, keskpaev=k, teravus=(h + o) / 2 / k, hommik_ohtu=h / o)


_D = squareform(pdist(np.array([[0.0], [0.1], [5.0], [5.1]])))
assert np.allclose(siluett(_D, np.array([1, 1, 2, 2])).mean(), 1 - 0.1 / 4.95, atol=0.01)

set_style()
jn = load_junctions().set_index("mp_id")
t, d = load_tallinn()
ok = d[d["kehtiv"] & (d["paevatyyp"] == "tööpäev") & (d["vaheaeg"] == "kool") & (d["paev"] >= ALGUS)]
t = t.merge(ok[["mp_id", "paev"]], on=["mp_id", "paev"])
prof = t.pivot_table(index="mp_id", columns="slot", values="v", aggfunc="mean")
prof = prof[prof.notna().all(axis=1)]
x = prof.T.groupby(np.arange(96) // 2).sum().T
x = x.div(x.sum(axis=1), axis=0) * 100
X = x.loc[:, KELL[0]:KELL[1] - 1]
D = squareform(pdist(X.values))
L = linkage(X.values, "ward")
sil = pd.DataFrame([dict(k=k, siluett=siluett(D, fcluster(L, k, "maxclust")).mean(),
                         suurused=" ".join(map(str, sorted(np.bincount(fcluster(L, k, "maxclust"))[1:], reverse=True))))
                    for k in range(2, 8)])
save_table(sil.round(3), "34_siluett")

lab = fcluster(L, K, "maxclust")
jarjekord = pd.Series(lab).value_counts().index                 # rühm 0 = suurim
ryhm = pd.Series(lab, index=X.index).map({c: i for i, c in enumerate(jarjekord)})
kesk = {r: naitajad(x[ryhm == r].mean()) for r in range(K)}
ter = pd.Series({r: v["teravus"] for r, v in kesk.items()})
nimi = {}
for r in range(K):
    if r == ter.idxmin():
        nimi[r] = "ühtlane päev"
    else:
        nimi[r] = "õhtutipuga" if kesk[r]["hommik_ohtu"] < 0.9 else "kaks teravat tippu"
r = pd.DataFrame({"kood": jn.loc[X.index, "code"], "nimi": jn.loc[X.index, "name"], "ryhm": ryhm + 1,
                  "ryhma_nimi": ryhm.map(nimi), "lat": jn.loc[X.index, "lat"], "lon": jn.loc[X.index, "lon"],
                  "siluett": siluett(D, lab)}, index=X.index)
r["kaugus_kesklinnast_km"] = km(r["lat"], r["lon"], *KESKLINN)
r = r.join(pd.DataFrame([naitajad(x.loc[m]) for m in r.index], index=r.index))
save_table(r.reset_index().round(3), "34_profiilituubid")

# --- joonis 1: kaart ja profiilid ----------------------------------------------------------------------------------------
lon0, lat0, lon1, lat1 = map_extent(r)
(mx0, my0), (mx1, my1) = to_merc(lon0, lat0), to_merc(lon1, lat1)
fig = plt.figure(figsize=(16, 9))
gs = fig.add_gridspec(K, 2, width_ratios=[1.35, 1], hspace=0.45, wspace=0.16)
am = fig.add_subplot(gs[:, 0])
add_basemap(am, lon0, lat0, lon1, lat1)
px, py = to_merc(r["lon"].values, r["lat"].values)
for g in range(K):
    on = (r["ryhm"] == g + 1).values
    am.scatter(px[on], py[on], s=90, color=VARVID[g], edgecolor="white", lw=1.3, zorder=5,
               label=f"{g + 1}: {nimi[g]} ({on.sum()})")
for xx, yy, c in zip(px, py, r["kood"]):
    am.annotate(c[2:], (xx, yy), xytext=(5, 4), textcoords="offset points", fontsize=7, zorder=6, path_effects=HALO)
am.legend(loc="upper left", fontsize=9, title="profiilitüüp (ristmikke)", title_fontsize=9, frameon=True)
am.set_title(f"Tööpäeva liikluse kuju rühmad (Wardi klasterdamine, K = {K})")
kx = np.arange(KELL[0], KELL[1]) / 2 + 0.25
koik = X.mean()
for g in range(K):
    a = fig.add_subplot(gs[g, 1])
    z = X[r["ryhm"].values == g + 1]
    for _, row in z.iterrows():
        a.plot(kx, row.values, color=VARVID[g], lw=0.6, alpha=0.35)
    a.plot(kx, koik.values, color=C_GRAY, lw=1.3, ls="--")
    a.plot(kx, z.mean().values, color=VARVID[g], lw=2.6)
    a.set_xlim(5, 23)
    a.set_ylim(0, X.values.max() * 1.05)
    a.set_xticks(range(5, 24, 2), [f"{h:02d}" for h in range(5, 24, 2)] if g == K - 1 else [])
    a.set_ylabel("% ööpäevast\n30 min kohta", fontsize=8.5)
    a.set_title(f"{g + 1}: {nimi[g]} - {len(z)} ristmikku, mediaan "
                f"{r.loc[r['ryhm'] == g + 1, 'kaugus_kesklinnast_km'].median():.1f} km kesklinnast".replace(".", ","),
                fontsize=10.5)
a.set_xlabel("kellaaeg (hall katkendjoon = kõigi ristmike keskmine)")
save(fig, "34_01_profiilituubid")

# --- joonis 2: dendrogramm ---------------------------------------------------------------------------------------------------
fig, a = plt.subplots(figsize=(15, 5.5))
lõige = (L[-K, 2] + L[-K + 1, 2]) / 2
leht_varv = {i: VARVID[ryhm.iloc[i]] for i in range(len(ryhm))}
def haru_varv(i):
    """Haru värv: rühma värv, kui kõik selle lehed on samas rühmas, muidu hall."""
    n = len(ryhm)
    lehed = [i] if i < n else None
    if lehed is None:
        stack, lehed = [i], []
        while stack:
            j = stack.pop()
            if j < n:
                lehed.append(j)
            else:
                stack += [int(L[j - n, 0]), int(L[j - n, 1])]
    v = {leht_varv[j] for j in lehed}
    return v.pop() if len(v) == 1 else C_GRAY
dendrogram(L, labels=list(r["kood"]), ax=a, link_color_func=haru_varv, leaf_font_size=8.5)
a.axhline(lõige, color=TEXT2, ls="--", lw=1)
a.set_ylabel("Wardi kaugus (kuju erinevus)")
a.set_title(f"Ristmike tööpäeva profiilide sarnasus (siluett K = {K} juures {sil.set_index('k').loc[K, 'siluett']:.2f})"
            .replace(".", ","))
a.grid(axis="x", visible=False)
save(fig, "34_02_dendrogramm")

print(sil.round(3).to_string(index=False))
for g in range(K):
    z = r[r["ryhm"] == g + 1]
    print(f"{g + 1} {nimi[g]}: {len(z)} ristmikku, mediaan {z['kaugus_kesklinnast_km'].median():.1f} km; teravus "
          f"{kesk[g]['teravus']:.2f}, hommik/õhtu {kesk[g]['hommik_ohtu']:.2f}: {' '.join(z['kood'])}")
