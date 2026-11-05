"""
26 - Ajanihke tundlikkus: kui palju muutub tipptunni maht ja kui palju liigub tipptund, kui 1...15% sõitjatest sõidab
15, 30, 45 või 60 min varem või hiljem. Iga ristmik eraldi ja kõik ristmikud kokku, kahe andmeallika järgi: 15 min
loendused (T09) ja sõidukipõhised kirjed (Traffic 24h, 1 min täpsusega).

SISEND
  common.load_tallinn()      ristmike 15 min loendused puhastatult (tallinn.count_15min); kasutatakse
                             tööpäevi (E-R, mitte püha ega lühendatud päev) õppetöö ajal alates T09_ALGUS
  common.load_vehicles()     sõidukipõhised kirjed (tallinn.vehicle_passage), tööpäevad SOIDUKI_PAEVAD

ARVUTUS
  Ristmiku profiil = iga pilu keskmine üle kehtivate tööpäevade: 15 min andmetes 96 pilu (päev, kust on puudu üle
    2 h, jääb välja; lühemad augud interpoleeritakse), sõidukipõhistes 1440 minutit (ristmiku päev jääb välja, kui
    mõni kanal on kell 06-22 üle 1 h vait, kuigi tal on seal tavaliselt >= 10 sõidukit 15 min kohta, või kui eluaegse
    loenduri järgi on puudu üle 3% sõidukitest). Kõik kokku = ristmike profiilide summa.
  Nihe Δ = -60, -45, -30, -15, +15, +30, +45, +60 min (miinus = varem), nihkujate osakaal p = 1...15%. Kaks mudelit:
    kõik sõidud    - p igal kellaajal sõitvatest nihkub: uus(t) = (1 - p) q(t) + p q(t - Δ)
    tipptunni sõidud - p praeguse tipptunni sõitudest nihkub (common.shift_peak, nagu 06), muu liiklus jääb paigale
  Tipptund (nagu common.peak_hour) = suurima mahuga 60 min aken; algus hommikul 06:00-09:59 ja õhtul 14:00-18:59,
    enne ja pärast nihet samas aknas (laiem aken leiaks ka tunni, mis oli juba enne suurem, nt keskpäeval). Kui uus
    algus on akna serval, võib tegelik tipp olla veel kaugemal (veerg serval). Tulemus: tipptunni mahu muutus (%), tipptunni alguse nihe (min)
    ja praeguse tipptunni akna mahu muutus (%). Kogumaht ei muutu (öösel üle südaöö nihkuv osa jääb välja, alla 0,1%).
  Kõik sõidud mudelis ei saa tipp kasvada, kui tipptund on päeva suurim tund: max[(1-p) H(t) + p H(t-Δ)] <= H_max,
    vähenemine on kuni p (1 - H(t_tipp - Δ) / H_max); akna serval olev tipp võib kasvada (suurem tund tuleb aknasse). Mudel ei arvesta läbilaskevõimet ega seda, et nihkuv sõitja liigub koos teistega.

VÄLJUND (kaust valjund/)
  26_01_ajanihe_tipu_maht.png
      Näitab: kui palju väheneb kõigi ristmike kokku tipptunni maht nihkujate osakaalu ja nihke järgi.
      Kuidas: 2 x 4 soojuskaarti; read = mudel (kõik sõidud / tipptunni sõidud), veerud = hommik ja õhtu kummagi
      andmeallika järgi. x-telg = nihkujate osakaal (%), y-telg = nihe (min, miinus = varem). Värv ja number lahtris =
      tipptunni mahu muutus, % (sinine = väheneb; ühine skaala).
  26_02_ajanihe_tipu_aeg.png
      Näitab: kui palju liigub kõigi ristmike kokku tipptunni algus.
      Kuidas: nagu eelmine, värv ja number = tipptunni alguse nihe, min (punane = hiljem, sinine = varem). 15 min
      andmetes saab algus liikuda ainult 15 min kaupa.
  26_03_ajanihe_ristmikud.png
      Näitab: kui erinevalt ristmikud reageerivad, kui 15% sõitjatest nihkub (15 min andmed).
      Kuidas: 2 x 2 paneeli (read: tipptunni mahu muutus %, alguse nihe min; veerud: hommik, õhtu); x-telg = nihe.
      Punktid = ristmikud (sinine = kõik sõidud, oranž = tipptunni sõidud), must kriips = mediaan.
  26_ajanihe_stsenaariumid.csv   kõik tulemused: andmed x ristmik (või kokku) x mudel x tipp x osakaal x nihe
  26_ajanihe_profiilid.csv       ristmike profiilide kokkuvõte: päevi, ööpäeva maht, tipptunni algus ja maht
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import (load_tallinn, load_vehicles, shift_peak, peak_hour, slot_label, set_style, save, save_table,
                    AM_WINDOW, PM_WINDOW, DIVERGING, C_BLUE, C_ORANGE, TEXT2)

T09_ALGUS = "2026-09-01"                                       # 2026/27 õppeaasta algus
SOIDUKI_PAEVAD = pd.to_datetime(["2026-10-16", "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"])
NIHKED = [-60, -45, -30, -15, 15, 30, 45, 60]                  # min, miinus = varem
OSAKAAL = np.arange(1, 16)                                     # %
TIPUD = {"hommik": AM_WINDOW, "ohtu": PM_WINDOW}
MUDEL = {"koik": "kõik sõidud", "tipp": "tipptunni sõidud"}
ANDMED = {"15min": ("15 min loendused", 4), "soidukid": ("sõidukipõhine, 1 min", 60)}
TIPP_TXT = {"hommik": "hommik", "ohtu": "õhtu"}


def nihuta(v, k):
    """Profiil k pilu võrra hiljem (k < 0: varem); üle päeva otsa nihkuv osa kaob."""
    out = np.zeros_like(v)
    if k > 0:
        out[k:] = v[:-k]
    else:
        out[:k] = v[-k:]
    return out


def tipptund(v, aken, ph):
    """Suurima liikuva tunni algus (pilu) ja maht, nagu common.peak_hour, kumulatiivse summaga."""
    c = np.r_[0, np.cumsum(v)]
    lo, hi = aken[0] * ph, aken[1] * ph
    s = c[lo + ph:hi + ph] - c[lo:hi]
    k = int(np.argmax(s))
    return lo + k, float(s[k])


def stsenaariumid(v, ph):
    """Ühe profiili kõik stsenaariumid -> read (mudel, tipp, osakaal, nihe, tulemused)."""
    rows = []
    for tipp, aken in TIPUD.items():
        s0, h0 = tipptund(v, aken, ph)
        for nihe in NIHKED:
            k = nihe * ph // 60
            for p in OSAKAAL:
                for mudel in MUDEL:
                    uus = ((1 - p / 100) * v + p / 100 * nihuta(v, k) if mudel == "koik"
                           else shift_peak(v, s0, p / 100, abs(k), "hiljem" if k > 0 else "varem", ph))
                    s1, h1 = tipptund(uus, aken, ph)
                    rows.append(dict(mudel=mudel, tipp=tipp, osakaal_pct=p, nihe_min=nihe,
                                     tipp_algus_enne=slot_label(s0, ph), tipp_algus_parast=slot_label(s1, ph),
                                     algus_nihe_min=(s1 - s0) * 60 / ph,
                                     serval=s1 in (aken[0] * ph, aken[1] * ph - 1) and s1 != s0, tipp_maht_enne=h0, tipp_maht_parast=h1,
                                     tipp_maht_muutus_pct=(h1 / h0 - 1) * 100,
                                     vana_tipptund_muutus_pct=(uus[s0:s0 + ph].sum() / h0 - 1) * 100))
    return rows


# kontroll: kiire tipptund = common.peak_hour; kõik sõidud mudelis ei kasva tipp ega muutu kogumaht (ilma ääreta)
_v = 1 + np.r_[np.zeros(20), np.arange(1, 13), np.arange(12, 0, -1), np.zeros(52)]      # 96 pilu, hommikutipp aknas
assert tipptund(_v, (6, 10), 4) == peak_hour(_v, (6, 10), 4) and \
       all(r["tipp_maht_muutus_pct"] <= 1e-9 for r in stsenaariumid(_v, 4) if r["mudel"] == "koik") and \
       abs(nihuta(_v, 3).sum() - _v[:-3].sum()) < 1e-9

set_style()

# --- 15 min profiilid ---------------------------------------------------------------------------------------------------
t, _ = load_tallinn()
t = t[(t["paev"] >= T09_ALGUS) & (t["paevatyyp"] == "tööpäev") & (t["vaheaeg"] == "kool")]
w15 = t.pivot_table(index=["mp_id", "paev"], columns="slot", values="v", aggfunc="sum", dropna=False)
w15 = w15[w15.notna().sum(axis=1) >= 88].T.interpolate(limit_direction="both").T
prof = {"15min": w15.groupby("mp_id").mean()}
paevi = {"15min": w15.groupby("mp_id").size()}
p15 = w15.index.get_level_values("paev")
print(f"15 min: {p15.nunique()} tööpäeva {p15.min():%d.%m}-{p15.max():%d.%m.%Y}, {len(prof['15min'])} ristmikku")

# --- sõidukipõhised profiilid (1 min) ---------------------------------------------------------------------------------
v = load_vehicles(None, koik=True)
v = v[v["ts"].dt.normalize().isin(SOIDUKI_PAEVAD)].assign(paev=lambda x: x["ts"].dt.normalize())
v = v.sort_values(["mp_id", "kanal", "life"])
d = v.groupby(["mp_id", "kanal", "paev"])["life"].diff()
v["puudu"] = d.where((d > 1) & (d < 10000), 1) - 1                 # vahele jäänud loenduri numbrid
terv = v.groupby(["mp_id", "paev"]).agg(n=("life", "size"), puudu=("puudu", "sum"))
k15 = (v.assign(slot=v["ts"].dt.hour * 4 + v["ts"].dt.minute // 15)
       .groupby(["mp_id", "kanal", "paev", "slot"]).size().unstack("slot", fill_value=0).reindex(columns=range(96), fill_value=0))
k15 = k15.reindex(pd.MultiIndex.from_tuples([(m, c, p) for m, c in k15.index.droplevel("paev").unique() for p in SOIDUKI_PAEVAD],
                                            names=k15.index.names), fill_value=0)
med = k15.groupby(["mp_id", "kanal"]).transform("median")
paeval = list(range(24, 88))
vait = ((k15[paeval] == 0) & (med[paeval] >= 10)).sum(axis=1).groupby(["mp_id", "paev"]).max() > 4
kehtiv = (~vait) & (terv["puudu"] / (terv["n"] + terv["puudu"]) <= 0.03).reindex(vait.index, fill_value=False)
m1 = (v.assign(minut=v["ts"].dt.hour * 60 + v["ts"].dt.minute).groupby(["mp_id", "paev", "minut"]).size()
      .unstack("minut", fill_value=0).reindex(columns=range(1440), fill_value=0))
m1 = m1[kehtiv.reindex(m1.index, fill_value=False).values]
prof["soidukid"], paevi["soidukid"] = m1.groupby("mp_id").mean(), m1.groupby("mp_id").size()
print(f"sõidukipõhine: {len(SOIDUKI_PAEVAD)} tööpäeva, kehtivaid ristmiku-päevi {len(m1)} / {len(kehtiv)} "
      f"(välja: {', '.join(f'MP{m:02d} {p:%d.%m}' for (m, p), ok in kehtiv.items() if not ok)}), "
      f"{len(prof['soidukid'])} ristmikku")
del v, k15, med

# --- stsenaariumid ------------------------------------------------------------------------------------------------------
rows, kokkuvote = [], []
for andmed, (_, ph) in ANDMED.items():
    pr = prof[andmed]
    for mp, vv in list(pr.iterrows()) + [("kokku", pr.sum())]:
        vv = vv.values.astype(float)
        rows += [dict(andmed=andmed, mp="kokku" if mp == "kokku" else f"MP{mp:02d}", **r) for r in stsenaariumid(vv, ph)]
        k = {f"{tp}_{x}": y for tp, aken in TIPUD.items()
             for x, y in zip(["algus", "maht"], (lambda s, h: (slot_label(s, ph), round(h)))(*tipptund(vv, aken, ph)))}
        kokkuvote.append(dict(andmed=andmed, mp="kokku" if mp == "kokku" else f"MP{mp:02d}",
                              paevi=int(paevi[andmed].get(mp, paevi[andmed].max())), ooopaev=round(vv.sum()), **k))
r = pd.DataFrame(rows)
save_table(r, "26_ajanihe_stsenaariumid")
save_table(pd.DataFrame(kokkuvote), "26_ajanihe_profiilid")

linn = r[r["mp"] == "kokku"]
print("\nKÕIK RISTMIKUD KOKKU: tipptunni mahu muutus % / alguse nihe min")
for (andmed, mudel, tipp), g in linn.groupby(["andmed", "mudel", "tipp"], sort=False):
    tab = g[g["osakaal_pct"].isin([5, 10, 15])].pivot(index="osakaal_pct", columns="nihe_min",
                                                       values=["tipp_maht_muutus_pct", "algus_nihe_min"])
    print(f"  {ANDMED[andmed][0]}, {MUDEL[mudel]}, {TIPP_TXT[tipp]} (tipp {g['tipp_algus_enne'].iloc[0]}, "
          f"{g['tipp_maht_enne'].iloc[0]:,.0f} sõid/h)")
    for p, x in tab.iterrows():
        print(f"    {p:2d}%: " + "  ".join(f"{n:+d}: {x[('tipp_maht_muutus_pct', n)]:+.1f}% {x[('algus_nihe_min', n)]:+.0f}"
                                         for n in NIHKED))


# --- joonised: kõik kokku soojuskaartidena -------------------------------------------------------------------------------
def soojus(col, nimi, pealkiri, silt, fmt, piir):
    fig, axes = plt.subplots(2, 4, figsize=(22, 8.5), sharex=True, sharey=True, layout="constrained")
    for i, mudel in enumerate(MUDEL):
        for j, (tipp, andmed) in enumerate([(tp, a) for tp in TIPUD for a in ANDMED]):
            ax = axes[i, j]
            g = linn[(linn["andmed"] == andmed) & (linn["mudel"] == mudel) & (linn["tipp"] == tipp)]
            z = g.pivot(index="nihe_min", columns="osakaal_pct", values=col).loc[NIHKED[::-1]]
            im = ax.imshow(z.values, cmap=DIVERGING, vmin=-piir, vmax=piir, aspect="auto")
            for (a, b), x in np.ndenumerate(z.values):
                ax.text(b, a, fmt(x), ha="center", va="center", fontsize=7,
                        color="white" if abs(x) > 0.6 * piir else "#0b0b0b")
            ax.set_xticks(range(len(OSAKAAL)), OSAKAAL, fontsize=8)
            ax.set_yticks(range(len(NIHKED)), [f"{n:+d}" for n in NIHKED[::-1]], fontsize=9)
            ax.grid(False)
            ax.set_title(f"{MUDEL[mudel].capitalize()}, {TIPP_TXT[tipp]} - {ANDMED[andmed][0]}\n"
                         f"tipp {g['tipp_algus_enne'].iloc[0]}, " + f"{g['tipp_maht_enne'].iloc[0]:,.0f}".replace(",", " ") + " sõid/h",
                         fontsize=10)
            if i == 1:
                ax.set_xlabel("nihkujate osakaal, %")
            if j == 0:
                ax.set_ylabel("nihe, min (miinus = varem)")
    cb = fig.colorbar(im, ax=axes, shrink=0.6, pad=0.01)
    cb.set_label(silt)
    fig.suptitle(pealkiri, x=0.01, ha="left", fontweight="bold")
    save(fig, nimi)


piir_maht = float(np.ceil(linn["tipp_maht_muutus_pct"].abs().max()))
soojus("tipp_maht_muutus_pct", "26_01_ajanihe_tipu_maht",
       "Kõik ristmikud kokku: tipptunni mahu muutus, kui osa sõitjatest sõidab varem või hiljem",
       "tipptunni mahu muutus, %", lambda x: f"{x:.1f}", piir_maht)
soojus("algus_nihe_min", "26_02_ajanihe_tipu_aeg",
       "Kõik ristmikud kokku: tipptunni alguse nihe, kui osa sõitjatest sõidab varem või hiljem",
       "tipptunni alguse nihe, min", lambda x: f"{x:+.0f}" if x else "0", 60)

# --- joonis: ristmike hajuvus, 15% nihkujaid, 15 min andmed ---------------------------------------------------------------
x15 = r[(r["andmed"] == "15min") & (r["mp"] != "kokku") & (r["osakaal_pct"] == OSAKAAL.max())]
fig, axes = plt.subplots(2, 2, figsize=(14, 8.5), sharex=True, layout="constrained")
rng = np.random.default_rng(0)
for i, (col, silt) in enumerate([("tipp_maht_muutus_pct", "tipptunni mahu muutus, %"),
                                 ("algus_nihe_min", "tipptunni alguse nihe, min")]):
    for j, tipp in enumerate(TIPUD):
        ax = axes[i, j]
        for nr, (mudel, varv, dx) in enumerate([("koik", C_BLUE, -0.18), ("tipp", C_ORANGE, 0.18)]):
            for xi, nihe in enumerate(NIHKED):
                y = x15[(x15["mudel"] == mudel) & (x15["tipp"] == tipp) & (x15["nihe_min"] == nihe)][col].values
                jit = rng.uniform(-0.07, 0.07, len(y)) + (rng.uniform(-0.04, 0.04, len(y)) if i == 1 else 0)
                ax.scatter(xi + dx + jit, y + (rng.uniform(-1.2, 1.2, len(y)) if i == 1 else 0), s=14, color=varv,
                           alpha=0.55, lw=0, label=MUDEL[mudel] if xi == 0 and i == 0 and j == 0 else None)
                ax.plot([xi + dx - 0.13, xi + dx + 0.13], [np.median(y)] * 2, color="#0b0b0b", lw=2,
                        label="mediaan" if xi == 0 and nr == 1 and i == 0 and j == 0 else None)
        ax.axhline(0, color=TEXT2, lw=0.8)
        ax.set_xticks(range(len(NIHKED)), [f"{n:+d}" for n in NIHKED])
        ax.set_title(f"{TIPP_TXT[tipp].capitalize()}: {silt}", fontsize=11)
        if i == 1:
            ax.set_xlabel("nihe, min (miinus = varem)")
            ax.set_yticks(range(-60, 61, 15))
        if j == 0:
            ax.set_ylabel(silt)
fig.legend(loc="outside lower center", ncol=3)
fig.suptitle(f"Ristmikud eraldi: {OSAKAAL.max()}% sõitjatest nihkub (15 min loendused, "
             f"{len(prof['15min'])} ristmikku; punktid nihutatud, et ei kattuks)", x=0.01, ha="left", fontweight="bold")
save(fig, "26_03_ajanihe_ristmikud")
