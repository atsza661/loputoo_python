"""
28 - Koridorid: ühe tänava järjestikused ristmikud koos (Tartu mnt, Paldiski mnt, Tammsaare tee, Sõpruse pst).
Kas ummik tekib korraga kogu tänaval või ühes kohas ja levib edasi; kumb ristmik jääb kinni enne; kas naabrid on
koos koormatud.

SISEND
  common.load_vehicles(None, koik=True)   sõidukipõhised kirjed (import_raw.traffic24h_tallinn), logija nädala
                                          tööpäevad NADAL: ristmik, kanal, aeg ja loenduril oldud aeg (occ)
  common.channel_direction()              kanali suund: linna sisse (LSS) või linnast välja (LVS) manöövri nime järgi
  valjund/24_soojus_ajatelg/24_kanalid.csv   kanali täistase ja H_täis (24 käib enne)
  valjund/27_ristmikud_piir.csv           ristmiku vaadeldud piir C (27 käib enne)
  common.load_tallinn()                   15 min loendused 2024-2026 (pikaajaline sagedus)
  common.load_junctions()                 ristmike koordinaadid (kaugus koridori algusest)

ARVUTUS
  Koridor = KORIDORID: ristmikud tänava järjekorras, alates kesklinna (Tammsaare teel Pärnu mnt) otsast; asukoht =
    linnulennuline kaugus naaberristmike vahel kokku liidetuna (km).
  Koormus nagu 24, aga suuna kaupa: kanali olek 5 min pilus (vaba, tihe, täis, seisak; läved nagu 24), koormusaste =
    min(q / täistase, 1), seisakus 1; ristmiku suuna koormus = suuna kanalite täistasemega kaalutud keskmine (rikkega
    kanal ei loe; alla poole kaalust = puuduv). Suund = LSS (linna sisse) või LVS (välja) kanali manöövri järgi;
    Tammsaare teel ja Sõpruse pst-l tähendab see sama: kesklinna poole või sealt eemale, kuid ristmiku suunda loevad
    ka ristuvad tänavad. Lisaks "kõik suunad" = kõik kanalid (nagu 24); MP34 ja MP09 kanalitel LSS/LVS märget pole,
    need on ainult seal.
  Koormatud = suuna koormus >= KOORMATUD% vähemalt KESTUS min järjest (kuni 5 min vahe loetakse sisse).
    Algus = esimese koormatud lõigu algus tipuaknas (hommik 06-11, õhtu 14-19).
  Levik = koormuse alguse ja asukoha seos sama päeva, suuna ja tipu kõigi koormatud ristmike vahel: sirge tõus min/km
    (positiivne = väljapoole hiljem ehk ummik algab kesklinna otsast ja kasvab väljapoole; negatiivne = algab
    äärest ja liigub kesklinna poole). Päevade mediaan.
  Naabrid: kõrvalasuvate ristmike paarid (A = kesklinnale lähem). Kõrvalekalle = koormus - sama ristmiku ja suuna
    tööpäevade keskmine samal kellaajal (päevaomane ummik, mitte tavaline päevarütm). Ristkorrelatsioon nihkega
    -30...+30 min (5 min samm, päeva sees): suurim r ja selle nihe (positiivne = B järgneb A-le). Koos koormatud:
    tõste = P(B koormatud | A koormatud) / P(B koormatud) (1 = sõltumatud, > 1 = koormatud koos).
  Pikaajaline sagedus (15 min, kõik suunad kokku): iga ristmiku tunnivoog (liikuv 60 min summa) tööpäevadel
    2024-2026; osa päevadest, mil tunnivoog algusega sel kellaajal on >= LAE_OSA x C (27).

VÄLJUND (kaust valjund/)
  28_01_koridorid_ajaruum.png
      Näitab: kus ja millal on koridor tavalisel tööpäeval koormatud - ummiku ruumiline ja ajaline kuju.
      Kuidas: rida = koridor, veerg = suund (sisse / välja / kõik). Aja-ruumi soojuskaart: x-telg = kellaaeg 06-19, y-telg =
      ristmik koridori järjekorras (ülal kesklinna ots, sildis kaugus km). Värv = suuna koormus % (6 tööpäeva
      keskmine; kollane = vaba, punane = täis; hall = selle suuna kanaleid pole), must joon = koormus KOORMATUD%
      (15 min silutud), must täpp = keskmiselt >= 5% suuna täistasemest seisab.
  28_paevad_<koridor>.png (tartu, paldiski, tammsaare, sopruse)
      Näitab: sama iga tööpäeva kohta eraldi: kas ummiku muster kordub.
      Kuidas: read = suund (sisse, välja, kõik), veerud = tööpäevad; värv nagu eelmisel, must kontuur = koormatud
      (>= KOORMATUD%).
  28_06_koridorid_15min.png
      Näitab: kui sageli on koridori ristmik kahe aasta jooksul olnud oma piiri lähedal, kellaaja järgi.
      Kuidas: paneel koridori kohta; x-telg = tunni algus 06-19, y-telg = ristmik; värv = % tööpäevadest, mil
      tunnivoog oli >= LAE_OSA x C.
  28_koridorid_koormus.csv   ristmik x suund x päev x 5 min: koormus %, seisak %, sõidukeid
  28_koridorid_algus.csv     koridor x suund x päev x tipp x ristmik: koormatud lõigu algus ja lõpp
  28_koridorid_levik.csv     koridor x suund x tipp: koormatud päevi, levikukiirus (min/km, mediaan), järjekord
  28_koridorid_paarid.csv    naaberpaarid: korrelatsioon, nihe, tõste
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common import (OUT_DIR, load_vehicles, channel_direction, load_tallinn, load_junctions, day_calendar, km, loigud,
                    set_style, save, save_table, TEXT2)

KORIDORID = {"Tartu mnt": [34, 35, 39, 19], "Paldiski mnt": [7, 3, 12, 11, 16],
             "Tammsaare tee": [10, 43, 8, 9], "Sõpruse pst": [1, 8]}
FAIL = {"Tartu mnt": "tartu", "Paldiski mnt": "paldiski", "Tammsaare tee": "tammsaare", "Sõpruse pst": "sopruse"}
NADAL = pd.to_datetime(["2026-10-16", "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"])
SAMM = 5
KELL = (6, 19)
TAIS, TIHE, SEISAK_H = 0.8, 0.5, 0.10           # olekud nagu 24
MIN_TAIS, RIKE_MIN = 120, 30                     # nagu 24
KOORMATUD, KESTUS = 70, 15                       # koormatud: suuna koormus >= 70% vähemalt 15 min
TIPUD = {"hommik": (6, 11), "õhtu": (14, 19)}
NIHE = 6                                         # ristkorrelatsiooni nihe kuni 6 pilu (30 min)
LAE_OSA = 0.95                                   # 15 min: tunnivoog >= 95% vaadeldud piirist
SUUNAD = {"LSS": "sisse", "LVS": "välja", "koik": "kõik suunad"}
KOIK = np.arange(0, 24 * 60, SAMM)
PILUD = KOIK[(KOIK >= KELL[0] * 60) & (KOIK < KELL[1] * 60)]
CMAP = plt.get_cmap("YlOrRd")


def olek(q, h, tais, h_tais):
    """Liiklusolek 0 vaba, 1 tihe, 2 täis, 3 seisak (nagu 24)."""
    r = q / tais
    return np.where((r < TAIS) & (h >= np.maximum(h_tais, SEISAK_H)), 3, np.where(r >= TAIS, 2, np.where(r >= TIHE, 1, 0)))


def koormatud_loigud(x):
    """Koormatud lõigud [(a, b), ...] pilu indeksites (koormus >= KOORMATUD vähemalt KESTUS min)."""
    return [(a, b) for a, b in loigud(np.nan_to_num(x) >= KOORMATUD, 1) if (b - a) * SAMM >= KESTUS]


def ristkorr(a, b, nihe):
    """corr(a(t), b(t + nihe)) üle päevade (read), ainult päeva sees; NaN-id välja."""
    x, y = (a[:, :a.shape[1] - nihe], b[:, nihe:]) if nihe >= 0 else (a[:, -nihe:], b[:, :b.shape[1] + nihe])
    x, y = x.ravel(), y.ravel()
    ok = ~np.isnan(x) & ~np.isnan(y)
    return np.corrcoef(x[ok], y[ok])[0, 1] if ok.sum() > 30 else np.nan


_t = np.r_[np.full(10, 50.0), np.full(4, 80.0), np.full(10, 50.0)]
_s = np.sin(np.arange(40.0))[None, :]
assert koormatud_loigud(_t) == [(10, 14)] and koormatud_loigud(_t[:12]) == [] and \
       abs(ristkorr(_s, np.roll(_s, 2, axis=1), 2) - 1) < 1e-9          # B = A 2 pilu hiljem -> r = 1 nihkel +2

set_style()
jn = load_junctions().set_index("mp_id")
mps = sorted({m for v in KORIDORID.values() for m in v})
asukoht = {}
for kor, ms in KORIDORID.items():
    d = [0.0] + [km(jn.loc[a, "lat"], jn.loc[a, "lon"], jn.loc[b, "lat"], jn.loc[b, "lon"]) for a, b in zip(ms, ms[1:])]
    asukoht[kor] = dict(zip(ms, np.cumsum(d)))

# --- kanalid 5 min pilud ------------------------------------------------------------------------------------------------
print("Laen sõidukipõhised kirjed...")
v = load_vehicles(None, koik=True)
v = v[v["ts"].dt.normalize().isin(NADAL) & v["mp_id"].isin(mps)]
v = v.assign(paev=v["ts"].dt.normalize(), pilu=(v["ts"].dt.hour * 60 + v["ts"].dt.minute) // SAMM * SAMM)
g = v.groupby(["mp_id", "kanal", "paev", "pilu"])["occ"].agg(["size", "sum"])
del v
kan24 = pd.read_csv(OUT_DIR / "24_soojus_ajatelg" / "24_kanalid.csv")
kan24["mp_id"] = kan24["kood"].str[2:].astype(int)
kan24 = kan24.set_index(["mp_id", "kanal"])
kan24 = kan24[kan24["taistase_soid_h"] >= MIN_TAIS]
read = pd.MultiIndex.from_tuples([(m, c, p) for m, c in kan24.index if m in mps for p in NADAL], names=["mp_id", "kanal", "paev"])
n = g["size"].unstack("pilu", fill_value=0).reindex(index=read, columns=KOIK, fill_value=0)
q = n.values * 60 / SAMM
H = g["sum"].unstack("pilu", fill_value=0).reindex(index=read, columns=KOIK, fill_value=0).values / (SAMM * 60)
kan = read.droplevel("paev")
T = kan24["taistase_soid_h"].reindex(kan).values[:, None]
HT = kan24["H_tais"].reindex(kan).values[:, None]
tava = pd.DataFrame(q, index=read).groupby(["mp_id", "kanal"]).median()
rike = np.zeros(q.shape, bool)
for i, (m, c) in enumerate(kan):
    ootus = tava.loc[(m, c)].values >= 0.2 * T[i, 0]
    for a, b in loigud(q[i] == 0, 0):
        if (b - a) * SAMM >= RIKE_MIN and ootus[a:b].any():
            rike[i, a:b] = True
ol = olek(q, H, T, HT)
aste = np.where(ol == 3, 1.0, np.minimum(q / T, 1.0))
w = np.where(rike, 0.0, np.broadcast_to(T, q.shape))
suund = channel_direction().set_index(["mp_id", "kanal"]).reindex(kan)
print(f"{len(set(kan))} kanalit {len(mps)} ristmikul, rikkepilusid kell 06-19: "
      f"{int(rike[:, np.isin(KOIK, PILUD)].sum())}")

# --- ristmiku suuna koormus ---------------------------------------------------------------------------------------------
tab = []
for sd in SUUNAD:
    mask = np.ones(len(kan), bool) if sd == "koik" else suund[sd].fillna(False).values.astype(bool)
    idx = read[mask]
    summa = lambda x: pd.DataFrame(x[mask], index=idx, columns=KOIK).groupby(["mp_id", "paev"]).sum()
    kaal = summa(w)
    kaetud = kaal / summa(np.broadcast_to(T, q.shape))
    k = (summa(aste * w) / kaal * 100).mask(kaetud < 0.5)
    s = (summa((ol == 3) * w) / kaal * 100).mask(kaetud < 0.5)
    nn = pd.DataFrame(n.values[mask], index=idx, columns=KOIK).groupby(["mp_id", "paev"]).sum()
    tab.append(pd.concat({"koormus_pct": k[PILUD].stack(), "seisak_pct": s[PILUD].stack(),
                          "soidukeid": nn[PILUD].stack()}, axis=1).rename_axis(["mp_id", "paev", "pilu"]).reset_index()
               .assign(suund=sd))
tab = pd.concat(tab, ignore_index=True)
assert tab["koormus_pct"].max() <= 100 + 1e-9 and tab["seisak_pct"].max() <= 100 + 1e-9
save_table(tab.assign(kood=tab["mp_id"].map(jn["code"]), paev=tab["paev"].dt.strftime("%Y-%m-%d"),
                      kell=tab["pilu"].map(lambda x: f"{x // 60:02d}:{x % 60:02d}"))
           [["kood", "suund", "paev", "kell", "koormus_pct", "seisak_pct", "soidukeid"]].round(2), "28_koridorid_koormus")
K = tab.set_index(["suund", "mp_id", "paev", "pilu"])["koormus_pct"].unstack("pilu")     # rida = suund, ristmik, päev
S = tab.set_index(["suund", "mp_id", "paev", "pilu"])["seisak_pct"].unstack("pilu")

# --- koormatud lõigud, levik, naabrid -----------------------------------------------------------------------------------
alg = []
for (sd, mp, p), row in K.iterrows():
    for a, b in koormatud_loigud(row.values):
        t0, t1 = PILUD[a], PILUD[min(b, len(PILUD)) - 1] + SAMM
        for tipp, (h0, h1) in TIPUD.items():
            if h0 * 60 <= t0 < h1 * 60:
                alg.append(dict(suund=sd, mp_id=mp, paev=p, tipp=tipp, algus_min=t0, lopp_min=t1))
alg = pd.DataFrame(alg).sort_values("algus_min").drop_duplicates(["suund", "mp_id", "paev", "tipp"])   # tipu esimene lõik
lev, alg_k = [], []
for kor, ms in KORIDORID.items():
    for (sd, tipp), gk in alg[alg["mp_id"].isin(ms)].groupby(["suund", "tipp"]):
        alg_k.append(gk.assign(koridor=kor, km=gk["mp_id"].map(asukoht[kor])))
        tousud, esimene = [], []
        for p, gp in gk.groupby("paev"):
            if len(gp) >= 2:
                x, y = gp["mp_id"].map(asukoht[kor]).values, gp["algus_min"].values
                if np.ptp(x) > 0:
                    tousud.append(np.polyfit(x, y, 1)[0])
                esimene.append(jn.loc[gp.loc[gp["algus_min"].idxmin(), "mp_id"], "code"])
        lev.append(dict(koridor=kor, suund=sd, tipp=tipp, koormatud_paevi=gk["paev"].nunique(),
                        ristmikke_koormatud=gk.groupby("paev")["mp_id"].nunique().mean(),
                        levik_min_km=np.median(tousud) if tousud else np.nan, paevi_levikuga=len(tousud),
                        esimesena=", ".join(f"{k} {c}x" for k, c in pd.Series(esimene).value_counts().items())))
lev = pd.DataFrame(lev)
alg_k = pd.concat(alg_k, ignore_index=True)
save_table(alg_k.assign(kood=alg_k["mp_id"].map(jn["code"]), paev=alg_k["paev"].dt.strftime("%Y-%m-%d"),
                        algus=alg_k["algus_min"].map(lambda x: f"{x // 60:02d}:{x % 60:02d}"),
                        lopp=alg_k["lopp_min"].map(lambda x: f"{x // 60:02d}:{x % 60:02d}"))
           [["koridor", "suund", "tipp", "paev", "kood", "km", "algus", "lopp"]].round(2), "28_koridorid_algus")
save_table(lev.round(2), "28_koridorid_levik")

kesk = K.groupby(["suund", "mp_id"]).transform("mean")
A = K - kesk                                                              # päevaomane kõrvalekalle
paarid = []
for kor, ms in KORIDORID.items():
    for a, b in zip(ms, ms[1:]):
        for sd in SUUNAD:
            if (sd, a) not in K.index.droplevel("paev") or (sd, b) not in K.index.droplevel("paev"):
                continue
            xa, xb = A.loc[(sd, a)].reindex(NADAL).values, A.loc[(sd, b)].reindex(NADAL).values
            r = {L * SAMM: ristkorr(xa, xb, L) for L in range(-NIHE, NIHE + 1)}
            L = max(r, key=lambda x: -np.inf if np.isnan(r[x]) else r[x])
            ka = np.nan_to_num(K.loc[(sd, a)].reindex(NADAL).values) >= KOORMATUD
            kb = np.nan_to_num(K.loc[(sd, b)].reindex(NADAL).values) >= KOORMATUD
            paarid.append(dict(koridor=kor, A=jn.loc[a, "code"], B=jn.loc[b, "code"], vahe_km=asukoht[kor][b] - asukoht[kor][a],
                               suund=sd, r_0=r[0], r_max=r[L], nihe_min=L,
                               p_B=kb.mean(), p_B_kui_A=kb[ka].mean() if ka.any() else np.nan,
                               tost=kb[ka].mean() / kb.mean() if ka.any() and kb.any() else np.nan))
paarid = pd.DataFrame(paarid)
save_table(paarid.round(3), "28_koridorid_paarid")
print("\nLEVIK (koormatud lõigu algus vs asukoht):")
print(lev.round(1).to_string())
print("\nNAABRID:")
print(paarid.round(2).to_string())

# --- 15 min: kahe aasta sagedus piiri lähedal ---------------------------------------------------------------------------
t, _ = load_tallinn()
t = t[t["mp_id"].isin(mps)]
kal = day_calendar(t["paev"]).set_index("paev")
w15 = t.pivot_table(index=["mp_id", "paev"], columns="slot", values="v", aggfunc="sum", dropna=False)
w15 = w15[w15.notna().sum(axis=1) >= 88].T.interpolate(limit_direction="both").T
w15 = w15[kal.reindex(w15.index.get_level_values("paev"))["paevatyyp"].values == "tööpäev"]
tund = w15.T.rolling(4).sum().shift(-3).T.loc[:, 24:75]
C = pd.read_csv(OUT_DIR / "27_ristmikud_piir.csv").set_index("mp_id")["C"]
lagi = tund.ge(LAE_OSA * C.reindex(tund.index.get_level_values("mp_id")).values, axis=0).groupby("mp_id").mean() * 100
save_table(lagi.rename(columns=lambda s: f"{s // 4:02d}:{s % 4 * 15:02d}").assign(kood=lambda x: x.index.map(jn["code"])),
           "28_koridorid_15min")


# --- joonised -----------------------------------------------------------------------------------------------------------
def ajaruum(ax, kor, sd, k, s=None, kontuur=False):
    """Aja-ruumi soojuskaart: rida = koridori ristmik, veerg = 5 min pilu; k ja s = DataFrame (mp_id x PILUD)."""
    ms = KORIDORID[kor]                              # kõik koridori ristmikud; puuduv rida = hall
    z = k.reindex(index=ms, columns=PILUD).values
    im = ax.imshow(z, aspect="auto", cmap=CMAP.with_extremes(bad="#d4d3cf"), vmin=0, vmax=100, interpolation="nearest",
                   extent=(KELL[0], KELL[1], len(ms) - 0.5, -0.5))
    if kontuur:
        ax.contour(np.linspace(KELL[0] + SAMM / 120, KELL[1] - SAMM / 120, len(PILUD)), np.arange(len(ms)),
                   pd.DataFrame(np.nan_to_num(z)).T.rolling(3, center=True, min_periods=1).mean().T.values,   # 15 min
                   levels=[KOORMATUD], colors="black", linewidths=0.9)
    if s is not None:
        yy, xx = np.nonzero(np.nan_to_num(s.reindex(index=ms, columns=PILUD).values) >= 5)
        ax.scatter(KELL[0] + (xx + 0.5) * SAMM / 60, yy, s=4, color="black", lw=0)
    ax.set_yticks(range(len(ms)), [f"{jn.loc[m, 'code']} {asukoht[kor][m]:.1f} km" for m in ms], fontsize=8)
    ax.set_xticks(range(KELL[0], KELL[1] + 1, 2))
    ax.grid(False)
    return im


fig, axes = plt.subplots(len(KORIDORID), len(SUUNAD), figsize=(20, 3 + 2.2 * len(KORIDORID)), layout="constrained",
                         height_ratios=[len(v) for v in KORIDORID.values()])
for i, kor in enumerate(KORIDORID):
    for j, sd in enumerate(SUUNAD):
        k = K.loc[sd].groupby("mp_id").mean()
        s = S.loc[sd].groupby("mp_id").mean()
        im = ajaruum(axes[i, j], kor, sd, k, s, kontuur=True)
        axes[i, j].set_title(f"{kor}: {SUUNAD[sd]}" + {"LSS": " (linna poole)", "LVS": " (linnast välja)"}.get(sd, ""),
                             fontsize=10)
for ax in axes[-1]:
    ax.set_xlabel("kellaaeg")
cb = fig.colorbar(im, ax=axes, shrink=0.5, pad=0.01)
cb.set_label("suuna koormus, % täistasemest")
fig.legend(handles=[Line2D([], [], color="black", lw=0.9, label=f"koormus {KOORMATUD}%"),
                    Line2D([], [], marker="o", ls="", color="black", ms=3, label="seisak >= 5%")],
           loc="outside lower center", ncol=2)
fig.suptitle(f"Koridorid: tavalise tööpäeva koormus ({NADAL[0]:%d.%m}-{NADAL[-1]:%d.%m.%Y}, {len(NADAL)} tööpäeva keskmine; "
             "ülal kesklinna ots)", x=0.01, ha="left", fontweight="bold")
save(fig, "28_01_koridorid_ajaruum")

for joonis_nr, kor in enumerate(KORIDORID, 2):        # joonised 28_02 ... 28_05
    nr = len(KORIDORID[kor])
    fig, axes = plt.subplots(len(SUUNAD), len(NADAL), figsize=(3.1 * len(NADAL), 1.2 + 1.0 * nr * len(SUUNAD)), sharex=True,
                             sharey=True,
                             layout="constrained")
    for i, sd in enumerate(SUUNAD):
        for j, p in enumerate(NADAL):
            k = K.loc[sd].xs(p, level="paev") if (p in K.loc[sd].index.get_level_values("paev")) else pd.DataFrame()
            s = S.loc[sd].xs(p, level="paev") if not k.empty else None
            im = ajaruum(axes[i, j], kor, sd, k.reindex(columns=PILUD) if not k.empty else
                         pd.DataFrame(np.nan, index=KORIDORID[kor], columns=PILUD), s, kontuur=True)
            axes[i, j].set_title(f"{['E', 'T', 'K', 'N', 'R', 'L', 'P'][p.day_of_week]} {p:%d.%m}, {SUUNAD[sd]}", fontsize=9)
            axes[i, j].tick_params(labelsize=7)
    cb = fig.colorbar(im, ax=axes, shrink=0.6, pad=0.01)
    cb.set_label("suuna koormus, %")
    fig.suptitle(f"{kor}: koormus tööpäevade kaupa (must joon = {KOORMATUD}%, täpp = seisak >= 5%; ülal kesklinna ots)",
                 x=0.01, ha="left", fontweight="bold")
    save(fig, f"28_{joonis_nr:02d}_paevad_{FAIL[kor]}")

fig, axes = plt.subplots(len(KORIDORID), 1, figsize=(12, 2 + 1.6 * len(KORIDORID)), layout="constrained",
                         height_ratios=[len(v) for v in KORIDORID.values()])
for ax, kor in zip(axes, KORIDORID):
    ms = [m for m in KORIDORID[kor] if m in lagi.index]
    im = ax.imshow(lagi.reindex(ms).values, aspect="auto", cmap="Reds", vmin=0, vmax=float(np.ceil(lagi.values.max() / 10) * 10),
                   extent=(6, 19, len(ms) - 0.5, -0.5), interpolation="nearest")
    ax.set_yticks(range(len(ms)), [f"{jn.loc[m, 'code']} {jn.loc[m, 'name']}" for m in ms], fontsize=8)
    ax.set_xticks(range(6, 20))
    ax.grid(False)
    ax.set_title(kor, fontsize=10)
axes[-1].set_xlabel("tunni algus")
cb = fig.colorbar(im, ax=axes, shrink=0.6, pad=0.01)
cb.set_label(f"% tööpäevadest, tunnivoog >= {LAE_OSA:.0%} piirist")
fig.suptitle(f"Koridoride ristmikud piiri lähedal: tööpäevad {w15.index.get_level_values('paev').min():%m.%Y}-"
             f"{w15.index.get_level_values('paev').max():%m.%Y} (15 min loendused, kõik suunad)", x=0.01, ha="left",
             fontweight="bold")
save(fig, "28_06_koridorid_15min")
