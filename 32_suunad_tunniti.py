"""
32 - Sisse- ja väljasõidu tasakaal kellaaja järgi: kui suur osa liiklusest liigub linna poole (hommikul sisse, õhtul
välja - "tõusu ja mõõna" muster) maanteeloendurites ja linna ristmikel.

SISEND
  common.maantee_suunad()    sissesõiduteede maanteeloendurite 15 min loendused suundade kaupa (highway.count_15min)
  common.load_vehicles()     sõidukipõhised kirjed (tallinn.vehicle_passage) koos kanali suunaga LSS / LVS
                             (common.channel_direction: manöövri nime järgi linna sisse või linnast välja)
  common.load_junctions()    ristmike nimed

ARVUTUS
  Linna poole osakaal = sissesõit / (sissesõit + väljasõit) igas 15 min pilus; 50% = mõlemas suunas sama palju.
    Sõidukid liidetakse enne jagamist liikuva 60 min aknaga (pilud -2...+1 ehk 30 min enne ja pärast pilu algust,
    SILUMINE), et öine juhuslikkus ei mürataks.
  Maanteeloendurid (MAANTEED: sama loendurid nagu 27): tavalised tööpäevad (E-R, õppetöö, mitte püha) alates
    ALGUS_MAANTEE, mõlema suuna sõidukid summeeritakse üle päevade ja siis jagatakse.
  Ristmikud: logija nädala tööpäevad (NADAL), LSS- ja LVS-kanalite sõidukid summeeritakse üle päevade. Ristmik on sees,
    kui LSS/LVS märgisega on vähemalt MIN_MARGIS tema liiklusest ja kumbagi suunda on vähemalt 5% (muidu pole
    tasakaalu, nt ühe suuna loendur). Pilud, kus kokku on alla MIN_N sõiduki, jäävad tühjaks.
  Linn kokku (ristmikud) = kõigi sobivate ristmike LSS / (LSS + LVS) summadest.
  Tõusu ja mõõna tugevus ristmikul = hommikune osakaal (07:00-09:00) - õhtune osakaal (16:00-18:00), %-punktides.

VÄLJUND (kaust valjund/)
  32_01_suunad_tunniti.png
      Näitab: kuidas liikluse suund päeva jooksul pöördub - hommikul linna, õhtul linnast välja - maanteedel ja igal
      ristmikul.
      Kuidas: vasakul joondiagramm: x = kellaaeg 04-24, y = linna poole osakaal, %; joon = maanteeloendur (värv
      loenduri järgi), must katkendjoon = linna ristmikud kokku, hall joon = 50%. Paremal soojuskaart: rida = ristmik
      (järjestatud tõusu ja mõõna tugevuse järgi), veerg = 15 min; punane = rohkem linna sisse, sinine = rohkem
      välja, hele = tasakaal. Rea lõpus hommiku-õhtu vahe %-punktides.
  32_suunad_tunniti.csv     iga loenduri ja ristmiku osakaal 15 min kaupa (tüüp, nimi, pilu, osakaal, sõidukeid)
  32_tous_moon.csv          ristmik ja maantee: hommikune ja õhtune osakaal, vahe
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common import (maantee_suunad, load_vehicles, load_junctions, day_calendar, set_style, save, save_table,
                    short_name, slot_label, DIVERGING, TEXT, TEXT2, C_BLUE, C_ORANGE, C_AQUA, C_YELLOW, C_MAGENTA,
                    C_GREEN, C_VIOLET)

ALGUS_MAANTEE = "2024-08-01"
NADAL = pd.to_datetime(["2026-10-16", "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"])
MAANTEED = [("Peterburi tee (Loo)", "0cfcf | narva - tallinn"), ("Tartu mnt", "0f55c | tartu - tallinn"),
            ("Pärnu mnt (Laagri)", "8560b | peoleo - tallinn"), ("Viljandi mnt (Kangru)", "1d86e | rapla - tallinn"),
            ("Paldiski mnt", "1cf12 | paldiski - tallinn"), ("Rannamõisa tee", "36408 | rannamoisa - tallinn"),
            ("Randvere tee (Viimsi)", "d2421 | randvere - viimsi")]
VARVID = [C_BLUE, C_ORANGE, C_AQUA, C_YELLOW, C_MAGENTA, C_GREEN, C_VIOLET]     # kindlas järjekorras
MIN_MARGIS, MIN_N = 0.8, 20
SILUMINE = 4                                  # liikuv summa üle 4 pilu (60 min), keskel
HOMMIK, OHTU = (28, 36), (64, 72)             # 07:00-09:00 ja 16:00-18:00 (15 min pilud)
KELL = (16, 96)                               # joonisel 04:00-24:00


def vastassuund(site):
    """'0cfcf | narva - tallinn' -> '0cfcf | tallinn - narva'."""
    i, s = site.split(" | ")
    a, b = s.split(" - ")
    return f"{i} | {b} - {a}"


def silu(x):
    """15 min sõidukid (indeks = pilu 0..95) -> liikuv 60 min summa ümber pilu (ööpäev ringiks)."""
    x = x.reindex(range(96), fill_value=0)
    r = pd.concat([x.iloc[-2:], x, x.iloc[:2]]).rolling(SILUMINE, center=True).sum()
    return r.iloc[2:-2].set_axis(x.index)


def osakaal(sisse, valja, min_n=MIN_N):
    """Linna poole osakaal, %; pilud, kus kokku < min_n, on NaN."""
    k = sisse + valja
    return (100 * sisse / k).where(k >= min_n)


assert vastassuund("0cfcf | narva - tallinn") == "0cfcf | tallinn - narva"
assert osakaal(pd.Series([30, 5]), pd.Series([10, 5])).fillna(-1).tolist() == [75.0, -1]
assert silu(pd.Series(1.0, index=range(96))).eq(4).all() and silu(pd.Series({0: 4.0}))[[94, 95, 0, 1, 2]].tolist() == [0, 4, 4, 4, 4]

set_style()
jn = load_junctions().set_index("mp_id")

# --- maanteeloendurid ---------------------------------------------------------------------------------------------------
_, dq = maantee_suunad(ALGUS_MAANTEE)
dq = dq[dq["toopaev"]]
dq = dq[~dq["paev"].isin(day_calendar(dq["paev"]).query("paevatyyp != 'tööpäev'")["paev"])]
m_rows = []
for nimi, s in MAANTEED:
    a = dq[dq["site"] == s].set_index(["paev", "slot"])["c"]
    b = dq[dq["site"] == vastassuund(s)].set_index(["paev", "slot"])["c"]
    yhine = a.index.intersection(b.index)
    if len(yhine) < 96 * 20:
        print(f"  {nimi}: mõlema suuna andmeid alla 20 päeva, välja")
        continue
    sa, sb = silu(a.loc[yhine].groupby("slot").sum()), silu(b.loc[yhine].groupby("slot").sum())
    m_rows.append(pd.DataFrame({"tyyp": "maantee", "nimi": nimi, "slot": sa.index, "osakaal": osakaal(sa, sb).values,
                                "soidukeid": (sa + sb).values, "paevi": yhine.get_level_values(0).nunique()}))
mt = pd.concat(m_rows, ignore_index=True)

# --- ristmikud (logija nädal) -------------------------------------------------------------------------------------------
v = load_vehicles(None, koik=True)
v = v[v["ts"].dt.normalize().isin(NADAL)]
v["slot"] = v["ts"].dt.hour * 4 + v["ts"].dt.minute // 15
margis = (v["LSS"] | v["LVS"]).groupby(v["mp_id"]).mean()
g = v.groupby(["mp_id", "slot"])[["LSS", "LVS"]].sum()
tot = g.groupby("mp_id").sum()
sobib = margis[(margis >= MIN_MARGIS)].index.intersection(tot[(tot.min(axis=1) / tot.sum(axis=1)) >= 0.05].index)
g = pd.concat({m: g.loc[m].apply(silu) for m in sobib}, names=["mp_id", "slot"])
rt = pd.DataFrame({"tyyp": "ristmik", "nimi": [jn.loc[m, "code"] for m in g.index.get_level_values(0)],
                   "slot": g.index.get_level_values(1), "osakaal": osakaal(g["LSS"], g["LVS"]).values,
                   "soidukeid": (g["LSS"] + g["LVS"]).values, "paevi": len(NADAL)})
linn = g.groupby("slot").sum()
linn = osakaal(linn["LSS"], linn["LVS"])
save_table(pd.concat([mt, rt], ignore_index=True), "32_suunad_tunniti")

hm = rt.pivot(index="nimi", columns="slot", values="osakaal").reindex(columns=range(96))
tm = pd.DataFrame({"hommik": hm.loc[:, HOMMIK[0]:HOMMIK[1] - 1].mean(axis=1),
                   "ohtu": hm.loc[:, OHTU[0]:OHTU[1] - 1].mean(axis=1)})
mp_ = mt.pivot(index="nimi", columns="slot", values="osakaal")
tm = pd.concat([tm.assign(tyyp="ristmik"),
                pd.DataFrame({"hommik": mp_.loc[:, HOMMIK[0]:HOMMIK[1] - 1].mean(axis=1),
                              "ohtu": mp_.loc[:, OHTU[0]:OHTU[1] - 1].mean(axis=1), "tyyp": "maantee"})])
tm["vahe_pp"] = tm["hommik"] - tm["ohtu"]
tm["nimi_pikk"] = [f"{k} {short_name(jn.set_index('code').loc[k, 'name'], 26, compact=True)}" if t_ == "ristmik" else k
                   for k, t_ in zip(tm.index, tm["tyyp"])]
save_table(tm.rename_axis("kood").reset_index().round(2), "32_tous_moon")

# --- joonis -----------------------------------------------------------------------------------------------------------------
r_ = tm[tm["tyyp"] == "ristmik"].sort_values("vahe_pp", ascending=False)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, max(7, 0.22 * len(r_) + 1.5)), gridspec_kw={"width_ratios": [1, 1.15]})
x = np.arange(96) / 4
for (nimi, _), c in zip(MAANTEED, VARVID):
    z = mt[mt["nimi"] == nimi]
    if len(z):
        a1.plot(z["slot"] / 4, z["osakaal"], color=c, lw=1.8, label=f"{nimi} ({z['paevi'].iloc[0]} p)")
a1.plot(x, linn.reindex(range(96)).values, color=TEXT, lw=2.2, ls="--", label=f"linna ristmikud kokku ({len(sobib)})")
a1.axhline(50, color=TEXT2, lw=1)
a1.set_xlim(KELL[0] / 4, KELL[1] / 4)
a1.set_xticks(range(4, 25, 2), [f"{h:02d}" for h in range(4, 25, 2)])
a1.set_ylim(10, 90)
a1.set_xlabel("kellaaeg")
a1.set_ylabel("linna poole liikuvate sõidukite osakaal, %")
a1.set_title("Linna poole osakaal: maanteeloendurid ja ristmikud kokku")
a1.text(4.2, 88, "rohkem linna sisse", fontsize=8.5, color=TEXT2, va="top")
a1.text(4.2, 12, "rohkem linnast välja", fontsize=8.5, color=TEXT2, va="bottom")
a1.legend(loc="lower right", fontsize=8.5)

h = hm.loc[r_.index, KELL[0]:KELL[1] - 1]
im = a2.imshow(h.values, aspect="auto", cmap=DIVERGING, vmin=10, vmax=90, interpolation="nearest",
               extent=(KELL[0] / 4, KELL[1] / 4, len(h) - 0.5, -0.5))
a2.set_yticks(range(len(h)), r_["nimi_pikk"], fontsize=7.5)
for i, val in enumerate(r_["vahe_pp"]):
    a2.text(KELL[1] / 4 + 0.2, i, f"{val:+.0f}", va="center", fontsize=7, color=TEXT2)
a2.set_xticks(range(4, 25, 2), [f"{h_:02d}" for h_ in range(4, 25, 2)])
a2.set_xlabel("kellaaeg")
a2.grid(False)
a2.set_title(f"Ristmikud: LSS / (LSS + LVS), tööpäevad {NADAL[0]:%d.%m}-{NADAL[-1]:%d.%m.%Y}")
a2.text(1.0, -0.11, "rea lõpus: hommik (07-09) - õhtu (16-18), %-punkti", transform=a2.transAxes, ha="right",
        va="top", fontsize=7.5, color=TEXT2)
cb = fig.colorbar(im, ax=a2, fraction=0.03, pad=0.07)
cb.set_label("linna poole osakaal, %")
fig.tight_layout()
save(fig, "32_01_suunad_tunniti")

print(f"maanteeloendureid {mt['nimi'].nunique()}, ristmikke {len(sobib)}; linn kokku hommikul "
      f"{linn.loc[HOMMIK[0]:HOMMIK[1] - 1].mean():.0f}% sisse, õhtul {linn.loc[OHTU[0]:OHTU[1] - 1].mean():.0f}%")
print(tm.sort_values("vahe_pp").round(1).to_string())
