"""
41 - Sisse- ja väljasõidu bilanss vastassuunaliste paaride kaupa: kas loenduskohas sõidab ööpäevas ühte suunda sama
palju kui tagasi, kui arvestada ainult täpselt vastupidiseid manöövreid (A -> B ja B -> A), mida tööle ja koju sõitja
teeb kumbagi üks kord päevas.

SISEND
  common.load_vehicles(None, koik=True)   sõidukipõhised kirjed (tallinn.vehicle_passage): ristmik, kanal, aeg
  common.load_manoeuvres()                kanal -> manööver: lähteharu (from_leg) ja sihtharu (to_leg)
  common.maantee_suunad()                 sissesõiduteede maanteeloendurite 15 min loendused suundade kaupa
  common.load_junctions()                 ristmike nimed

ARVUTUS
  Paar = ristmiku kaks manöövrit, millest üks on teise täpne vastand: lähteharu A -> sihtharu B ja B -> A (sama haru
    nimi ristmiku joonisel). Ilma sihtharuta loendurid (nt ringil või viaduktil), tagasipöörded ja vastandita
    manöövrid jäävad välja; sama manöövri rajad liidetakse.
  Sisse = tööle sõidu suund: paari pool, kus hommikune (06-10) osakaal tema ööpäeva sõidukitest miinus õhtune
    (15-19) osakaal on suurem. Sama reegel kõigil ristmikel ja maanteedel, ka kesklinnas, kus linna sisse suund pole
    üheselt määratud; "sisse" ei tähenda seega alati geograafiliselt linna poole. Hommikuse ülekaalu vahe (sisse- ja
    väljapoole tous, %-punktides) näitab, kui selge suund on (väike vahe = mõlemas suunas sarnane päev).
  Päevad: logija nädala tööpäevad (NADAL), ainult ristmiku terved päevad (kõik pordid kaetud 05-23,
    common.tervetel_paevadel).
  Ristmik on sees, kui vastaspaaride sõidukeid on vähemalt MIN_OSA (75%) tema kõigist sõidukitest; muidu esindaks
    bilanss ainult väikest osa ristmikust (välja jäävad nt MP07, MP37, MP39, kus paar on 10-30% liiklusest).
  Bilanss ristmiku päeval = (sisse - välja) / (sisse + välja) x 100, kõigi ristmiku paaride summadest; 0 = mõlemas
    suunas sama palju, +10 = sissepoole 10% paaride liiklusest rohkem kui välja. Ristmiku väärtus = päevade mediaan,
    vahemik = päevade 10. ja 90. protsentiil.
  Maanteeloendurid (MAANTEED, samad nagu 27 ja 32): loenduri kaks suunda on paar (sisse nagu ristmikel); tavalised
    tööpäevad (E-R, õppetöö, mitte püha) alates ALGUS_MAANTEE, ainult päevad, kus mõlemal suunal on kõik 96
    veerandtundi ja kummagi suuna ööpäev on RIKE...1/RIKE (pool kuni kaks korda) selle suuna kohalikust tasemest
    (29 kõrvuti oleva päeva mediaan); muidu ühe suuna rike (nt Peterburi tee 09.2025 ja 05.2026).
  Koondread (ainult ööpäeva bilansi paneelil): MP kokku = iga päeva kõigi sees olevate ristmike paaride sisse ja
    välja summad (ristmikud, mille see päev on terve); Maanteed kokku = iga päeva kõigi maanteeloendurite summad, kui
    kehtivaid loendureid on sel päeval vähemalt MIN_MAANTEID (5 / 7). Bilanss, mediaan ja protsentiilid nagu kohtadel.
  Kumulatiivne bilanss kellaaja järgi = iga päeva (sisse - välja) keskööst selle veerandtunni lõpuni / selle päeva
    (sisse + välja) x 100, mediaan üle päevade (ristmikud kokku: kõigi ristmike paarid päeva kaupa liidetud); ööpäeva
    lõpus on see ligikaudu ööpäeva bilanss.

CALCULATION IN PLAIN ENGLISH
  A pair = two movements of one junction where one is the exact reverse of the other (arm A -> arm B and B -> A).
    Counters without a destination arm, U-turns and movements without a reverse are left out; lanes of the same
    movement are added.
  Inbound side ("sisse") = the trip to work: the side of the pair with the larger (morning 06-10 share of its day's
    vehicles - evening 15-19 share). The same rule at every junction and highway, also in the centre, so "sisse" is
    not always geographically towards the city.
  Days: logger-week workdays, complete junction-days only. A junction is used only when its pairs carry at least
    MIN_OSA (75%) of all its vehicles.
  Balance of a junction-day = (inbound - outbound) / (inbound + outbound) x 100 over all its pairs. Junction value =
    median over days; range = 10th and 90th percentile of days.
  Highway counters: the two directions of one counter are the pair (inbound by the same morning rule); workdays
    from ALGUS_MAANTEE with all 96 quarter hours in both directions and each direction's day total between RIKE (half)
    and 1/RIKE (double) of that direction's local level = median of 29 neighbouring days (otherwise a fault).
  Total rows (daily-balance panel only): "MP kokku" = each day's inbound and outbound summed over all included
    junctions complete that day; "Maanteed kokku" = the same over the highway counters, on days with at least
    MIN_MAANTEID (5 of 7) valid counters. Median and percentiles as for single places.
  Cumulative balance at a clock time = each day's (inbound - outbound) from midnight to the end of that quarter hour /
    that day's (inbound + outbound) x 100, then the median over days (junctions together: all pairs added per day); at
    midnight it is about the day's balance.

VÄLJUND (kaust valjund/)
  41_01_suunabilanss.png
      Näitab: kas igas loenduskohas liigub ööpäevas sama palju sisse kui välja, kui arvestada ainult täpselt
      vastupidiseid manöövreid (tööle ja tagasi), ja millal päeva jooksul vahe tekib ja tasandub.
      Kuidas: vasakul rida = ristmik, kus paarides on vähemalt 75% liiklusest (sildis kood, nimi, paaride arv ja paaride
      osakaal ristmiku liiklusest; järjestatud bilansi järgi), viimane rida MP kokku; musta joone all maanteeloendurid
      ja Maanteed kokku (koondread rombiga, paksus kirjas; kumulatiivsel paneelil neid ei ole). x-telg = bilanss, %
      ((sisse - välja) / kokku; sisse = hommikul ülekaalus ehk tööle sõidu suund); punkt = päevade mediaan (sinine =
      rohkem sisse, oranž = rohkem välja), hall joon = päevade 10.-90. protsentiil, hallid täpid = üksikud päevad; rea
      lõpus paaride sõidukid ööpäevas. Paremal kumulatiivne bilanss kellaaja järgi: x = kellaaeg, y = (sisse - välja)
      keskööst, % ööpäeva paaride liiklusest (mediaanpäev); must katkendjoon = ristmikud kokku, värvilised jooned =
      maanteeloendurid (värvid nagu 32); hall joon = 0.
  41_suunabilanss.csv          ristmik / maantee ja koondread: päevi, paare, paaride osakaal liiklusest, sisse ja välja
                               ööpäevas, bilanss (mediaan, päevade 10. ja 90. protsentiil)
  41_suunabilanss_paarid.csv   iga paar: ristmik, sisse- ja väljamanööver (harud), hommikuse ülekaalu vahe
                               (%-punkti), sõidukeid ööpäevas, bilanss
"""
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common import (tervetel_paevadel, maantee_suunad, load_vehicles, load_manoeuvres, load_junctions,
                    day_calendar, set_style, save, save_table, short_name, TEXT, TEXT2, C_BLUE, C_ORANGE, C_GRAY, C_AQUA,
                    C_YELLOW, C_MAGENTA, C_GREEN, C_VIOLET)

NADAL = pd.to_datetime(["2026-10-16", "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"])   # nagu 32
ALGUS_MAANTEE = "2024-08-01"
MAANTEED = [("Peterburi tee (Loo)", "0cfcf | narva - tallinn"), ("Tartu mnt", "0f55c | tartu - tallinn"),
            ("Pärnu mnt (Laagri)", "8560b | peoleo - tallinn"), ("Viljandi mnt (Kangru)", "1d86e | rapla - tallinn"),
            ("Paldiski mnt", "1cf12 | paldiski - tallinn"), ("Rannamõisa tee", "36408 | rannamoisa - tallinn"),
            ("Randvere tee (Viimsi)", "d2421 | randvere - viimsi")]
VARVID = [C_BLUE, C_ORANGE, C_AQUA, C_YELLOW, C_MAGENTA, C_GREEN, C_VIOLET]     # kindlas järjekorras, nagu 32
HOMMIK, OHTU = (6, 10), (15, 19)                                                # suuna määramiseks (kellaajad)
MIN_OSA = 75             # ristmik sees, kui vastaspaarides on vähemalt nii mitu % tema liiklusest (muidu ei esinda ristmikku)
MIN_MAANTEID = 5         # "Maanteed kokku" päev: vähemalt nii mitu maanteeloendurit (7-st) on sel päeval kehtiv
RIKE = 0.5               # maanteel päev välja, kui ühe suuna ööpäev on alla poole või üle kahe korra suuna kohalikust tasemest


def vastaspaarid(dm):
    """Manöövrid (veerud mp_id, a = lähteharu, b = sihtharu) -> ainult need, millel on samal ristmikul vastand
    (b -> a); lisab veeru paar (harud tähestiku järjekorras, mõlemal poolel sama)."""
    k = set(zip(dm["mp_id"], dm["a"], dm["b"]))
    d = dm[[(m, y, x) in k for m, x, y in zip(dm["mp_id"], dm["a"], dm["b"])]].copy()
    d["paar"] = [" ↔ ".join(sorted([x, y])) for x, y in zip(d["a"], d["b"])]
    return d


def bilanss(sisse, valja):
    """(sisse - välja) / (sisse + välja) x 100."""
    return (sisse - valja) / (sisse + valja) * 100


def tous(tund, n):
    """Hommikune (HOMMIK) miinus õhtune (OHTU) osakaal suuna sõidukitest; tund = kellaaeg tundides, n = sõidukid."""
    tund, n = np.asarray(tund), np.asarray(n, float)
    return (n[(tund >= HOMMIK[0]) & (tund < HOMMIK[1])].sum() - n[(tund >= OHTU[0]) & (tund < OHTU[1])].sum()) / n.sum()


def kumulatiivne(s, v):
    """Päev x 15 min pilu (sisse s, välja v) -> mediaanpäeva kumulatiivne bilanss igas pilus: iga päeva
    (sisse - välja) keskööst pilu lõpuni / päeva (sisse + välja) x 100, siis mediaan üle päevade."""
    s, v = s.reindex(columns=range(96), fill_value=0), v.reindex(columns=range(96), fill_value=0)
    return ((s - v).cumsum(axis=1).div((s + v).sum(axis=1), axis=0) * 100).median()


def vastassuund(site):
    """'0cfcf | narva - tallinn' -> '0cfcf | tallinn - narva'."""
    i, s = site.split(" | ")
    a, b = s.split(" - ")
    return f"{i} | {b} - {a}"


def haru(nimi):
    """'3 Sõpruse pst (SW)' -> 'Sõpruse pst (SW)': number eest ära, ' side' -> ' pool'; ilmakaar jääb, sest samal
    ristmikul võib sama tänav olla kaks haru (nt MP33 Pärnu mnt põhjast ja lõunast)."""
    return re.sub(r"^\d+\s+", "", nimi).replace(" side", " pool")


def kokku_rida(s, v, nimi):
    """Koondrida: päevade sisse (s) ja välja (v) summad üle kohtade (indeks = päev) -> sama kuju kui koha rida."""
    bp = bilanss(s, v)
    return dict(nimi=nimi, paevi=len(bp), sisse_paevas=s.mean(), valja_paevas=v.mean(), bilanss=bp.median(),
                p10=bp.quantile(0.1), p90=bp.quantile(0.9), paevad=bp.values)


_t = vastaspaarid(pd.DataFrame({"mp_id": [1, 1, 1, 2], "a": ["X", "Y", "X", "Y"], "b": ["Y", "X", "Z", "X"]}))
assert _t.index.tolist() == [0, 1] and _t["paar"].nunique() == 1
assert kumulatiivne(pd.DataFrame([[3, 1]]), pd.DataFrame([[1, 3]])).tolist()[:2] == [25, 0] and bilanss(60, 40) == 20 and vastassuund("0cfcf | narva - tallinn") == "0cfcf | tallinn - narva"
assert haru("3 Tammsaare, Tondi side (E)") == "Tammsaare, Tondi pool (E)" and tous([7, 16, 12], [3, 1, 4]) == 0.25

set_style()
jn = load_junctions().set_index("mp_id")

# --- ristmike vastaspaarid ----------------------------------------------------------------------------------------------
dm = load_manoeuvres()
dm["mp_id"] = dm["mp"].str[2:].astype(int)
dm = dm.dropna(subset=["from_leg", "to_leg"]).assign(a=lambda z: z["from_leg"].str.strip(), b=lambda z: z["to_leg"].str.strip())
dm = vastaspaarid(dm[dm["a"] != dm["b"]])

v = load_vehicles(None, koik=True)
v = tervetel_paevadel(v[v["ts"].dt.normalize().isin(NADAL)])
v = v.assign(paev=v["ts"].dt.normalize(), slot=v["ts"].dt.hour * 4 + v["ts"].dt.minute // 15)
koik = v.groupby("mp_id").size()                                           # ristmiku kõik sõidukid (terved päevad)
x = v.merge(dm[["mp_id", "channel", "paar", "a", "b"]].rename(columns={"channel": "kanal"}),
            on=["mp_id", "kanal"])
osa = x.groupby("mp_id").size() / koik.reindex(x["mp_id"].unique()) * 100      # paaride osakaal ristmiku liiklusest
valja_jaetud = osa[osa < MIN_OSA].sort_values()
print(f"Välja (paarides alla {MIN_OSA}% ristmiku liiklusest): "
      + ", ".join(f"{jn.loc[m, 'code']} {o:.0f}%" for m, o in valja_jaetud.items()))
x = x[~x["mp_id"].isin(valja_jaetud.index)].copy()
x["h"] = x["ts"].dt.hour

# paari pooled: hommikune ülekaal -> kumb pool on sisse (tööle sõidu suund)
pool = x.groupby(["mp_id", "paar", "a"])["h"].agg(lambda h: tous(h, np.ones(len(h)))).rename("tous").reset_index()
sisse = {}
for (mp, paar), g in pool.groupby(["mp_id", "paar"]):
    if len(g) != 2:
        continue
    g = g.sort_values("tous", ascending=False)
    sisse[(mp, paar)] = (g["a"].iloc[0], (g["tous"].iloc[0] - g["tous"].iloc[1]) * 100)
x = x[[(m, p) in sisse for m, p in zip(x["mp_id"], x["paar"])]].copy()
x["sisse"] = [sisse[(m, p)][0] == a for m, p, a in zip(x["mp_id"], x["paar"], x["a"])]

paevad = x.groupby(["mp_id", "paev"])["sisse"].agg(sisse="sum", kokku="size")
paevad["valja"] = paevad["kokku"] - paevad["sisse"]
paevad["bilanss"] = bilanss(paevad["sisse"], paevad["valja"])
ndays = paevad.groupby("mp_id").size()
r = (paevad.groupby("mp_id").agg(paevi=("bilanss", "size"), sisse_paevas=("sisse", "mean"), valja_paevas=("valja", "mean"),
                                 bilanss=("bilanss", "median"), p10=("bilanss", lambda z: z.quantile(0.1)),
                                 p90=("bilanss", lambda z: z.quantile(0.9)))
     .assign(paare=x.groupby("mp_id")["paar"].nunique(), osakaal_pct=x.groupby("mp_id").size() / koik * 100))
r["tyyp"], r["kood"] = "ristmik", [jn.loc[m, "code"] for m in r.index]
r["nimi"] = [jn.loc[m, "name"] for m in r.index]

# paaride tabel
pk = x.groupby(["mp_id", "paar", "sisse"]).size().unstack("sisse").rename(columns={True: "s", False: "v"})
paarid = pd.DataFrame({
    "kood": [jn.loc[m, "code"] for m, _ in pk.index],
    "sisse": [f"{haru(sisse[k][0])} -> {haru([h for h in k[1].split(' ↔ ') if h != sisse[k][0]][0])}" for k in pk.index],
    "valja": [f"{haru([h for h in k[1].split(' ↔ ') if h != sisse[k][0]][0])} -> {haru(sisse[k][0])}" for k in pk.index],
    "hommiku_ylekaal_pp": [sisse[k][1] for k in pk.index],
    "sisse_paevas": pk["s"].values / ndays.reindex(pk.index.get_level_values(0)).values,
    "valja_paevas": pk["v"].values / ndays.reindex(pk.index.get_level_values(0)).values})
paarid["bilanss"] = bilanss(paarid["sisse_paevas"], paarid["valja_paevas"])
save_table(paarid.sort_values(["kood", "bilanss"]).round(1), "41_suunabilanss_paarid")

# --- maanteeloendurid ---------------------------------------------------------------------------------------------------
_, dq = maantee_suunad(ALGUS_MAANTEE)
dq = dq[dq["toopaev"]]
dq = dq[~dq["paev"].isin(day_calendar(dq["paev"]).query("paevatyyp != 'tööpäev'")["paev"])]
m_rows, m_kum, m_paev = [], {}, {}
for nimi, s in MAANTEED:
    a = dq[dq["site"] == s].set_index(["paev", "slot"])["c"]
    b = dq[dq["site"] == vastassuund(s)].set_index(["paev", "slot"])["c"]
    yhine = a.index.intersection(b.index)
    terve = yhine.get_level_values(0).value_counts()
    yhine = yhine[yhine.get_level_values(0).isin(terve.index[terve == 96])]
    if yhine.get_level_values(0).nunique() < 20:
        print(f"  {nimi}: mõlema suuna terveid päevi alla 20, välja")
        continue
    a, b = a.loc[yhine], b.loc[yhine]
    if tous(b.index.get_level_values(1) // 4, b) > tous(a.index.get_level_values(1) // 4, a):
        a, b = b, a                                                      # sisse = hommikul ülekaalus suund
        print(f"  {nimi}: hommikul ülekaalus on linnast välja suund, see on sisse")
    pa, pb = a.groupby("paev").sum(), b.groupby("paev").sum()
    ma, mb = (z.rolling(29, center=True, min_periods=10).median() for z in (pa, pb))     # suuna kohalik tase
    ok = pa.between(RIKE * ma, ma / RIKE) & pb.between(RIKE * mb, mb / RIKE)      # ühe suuna rike: päev välja
    a, b, pa, pb = a[a.index.get_level_values(0).isin(ok.index[ok])], b[b.index.get_level_values(0).isin(ok.index[ok])], pa[ok], pb[ok]
    bp = bilanss(pa, pb)
    m_rows.append(dict(tyyp="maantee", kood="", nimi=nimi, paevi=len(bp), paare=1, osakaal_pct=np.nan,
                       sisse_paevas=pa.mean(), valja_paevas=pb.mean(), bilanss=bp.median(), p10=bp.quantile(0.1),
                       p90=bp.quantile(0.9), paevad=bp.values))
    m_kum[nimi] = kumulatiivne(a.unstack("slot"), b.unstack("slot"))
    m_paev[nimi] = (pa, pb)
mt = pd.DataFrame(m_rows)

# koondread (ainult vasakul paneelil): päeva kaupa kõigi kohtade paarid kokku
pj = paevad.groupby(level="paev")[["sisse", "valja"]].sum()
k_rist = kokku_rida(pj["sisse"], pj["valja"], f"MP kokku ({len(r)} ristmikku)")
S = pd.concat({n: z[0] for n, z in m_paev.items()}, axis=1, sort=True)
V = pd.concat({n: z[1] for n, z in m_paev.items()}, axis=1, sort=True)
piisav = S.notna().sum(axis=1) >= MIN_MAANTEID
k_mt = kokku_rida(S[piisav].sum(axis=1), V[piisav].sum(axis=1), f"Maanteed kokku ({len(m_paev)} loendurit)")

tabel = pd.concat([r.reset_index(drop=True), pd.DataFrame([dict(k_rist, tyyp="ristmikud kokku")]).drop(columns="paevad"),
                   mt.drop(columns="paevad"), pd.DataFrame([dict(k_mt, tyyp="maanteed kokku")]).drop(columns="paevad")],
                  ignore_index=True)
save_table(tabel[["tyyp", "kood", "nimi", "paevi", "paare", "osakaal_pct", "sisse_paevas", "valja_paevas", "bilanss", "p10",
                  "p90"]].round(1), "41_suunabilanss")

# ristmikud kokku: kumulatiivne bilanss kellaaja järgi
ps = x.groupby(["paev", "slot", "sisse"]).size().unstack("sisse", fill_value=0)
kum_linn = kumulatiivne(ps[True].unstack("slot"), ps[False].unstack("slot"))
linn_bil = bilanss(ps[True].sum(), ps[False].sum())
print(f"Ristmikke {len(r)}, paare {len(paarid)}; ristmikud kokku bilanss {linn_bil:+.1f}% (ristmike keskmiste summa: sisse "
      f"{r['sisse_paevas'].sum():,.0f}, välja {r['valja_paevas'].sum():,.0f} sõidukit ööpäevas)")
print(f"Ristmikke, kus |bilanss| < 5%: {(r['bilanss'].abs() < 5).sum()} / {len(r)}; suurimad: "
      + ", ".join(f"{k} {b:+.0f}%" for k, b in r.set_index("kood")["bilanss"].sort_values(key=abs).tail(5)[::-1].items()))
for m in [k_rist, k_mt]:
    print(f"  {m['nimi']}: bilanss {m['bilanss']:+.1f}% ({m['paevi']} päeva, P10...P90 {m['p10']:+.1f}...{m['p90']:+.1f})")
for _, m in mt.iterrows():
    print(f"  maantee {m['nimi']}: bilanss {m['bilanss']:+.1f}% ({m['paevi']} päeva, P10...P90 {m['p10']:+.1f}...{m['p90']:+.1f})")

# --- joonis -------------------------------------------------------------------------------------------------------------
rr = r.sort_values("bilanss", ascending=False)
koond = lambda k: dict(silt=k["nimi"], b=k["bilanss"], lo=k["p10"], hi=k["p90"], n=k["sisse_paevas"] + k["valja_paevas"],
                       paevad=k["paevad"], kokku=True)
read = ([dict(silt=f"{k} {short_name(n, 30, compact=True)} ({p}; {o:.0f}%)", b=b, lo=lo, hi=hi, n=s + v_,
              paevad=paevad.loc[m, "bilanss"].values)
         for m, k, n, p, o, b, lo, hi, s, v_ in zip(rr.index, rr["kood"], rr["nimi"], rr["paare"], rr["osakaal_pct"],
                                                   rr["bilanss"], rr["p10"], rr["p90"], rr["sisse_paevas"], rr["valja_paevas"])]
        + [koond(k_rist)]
        + [dict(silt=f"Maantee: {m['nimi']}", b=m["bilanss"], lo=m["p10"], hi=m["p90"],
                n=m["sisse_paevas"] + m["valja_paevas"], paevad=m["paevad"]) for _, m in mt.iterrows()]
        + [koond(k_mt)])
fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, max(7, 0.27 * len(read) + 1.8)), gridspec_kw={"width_ratios": [1.15, 1]})
rng = np.random.default_rng(0)
for i, q in enumerate(read):
    a1.plot([q["lo"], q["hi"]], [i, i], color=C_GRAY, lw=1.2, zorder=2)
    a1.scatter(q["paevad"], i + rng.uniform(-0.15, 0.15, len(q["paevad"])), s=6, color=C_GRAY, alpha=0.5, lw=0, zorder=2)
    a1.scatter(q["b"], i, s=70 if q.get("kokku") else 40, marker="D" if q.get("kokku") else "o",
               color=C_BLUE if q["b"] >= 0 else C_ORANGE, edgecolor=TEXT if q.get("kokku") else "white", zorder=3)
    a1.text(1.01, i, f"{q['n']:,.0f}".replace(",", " "), transform=a1.get_yaxis_transform(), va="center", fontsize=7,
            color=TEXT2)
a1.axvline(0, color=TEXT2, lw=1)
a1.axhline(len(rr) + 0.5, color="black", lw=1)                       # ristmikud | maanteed
for i, q in enumerate(read):
    if q.get("kokku"):
        a1.axhline(i - 0.5, color=TEXT2, lw=0.6, ls=":")
a1.set_yticks(range(len(read)), [q["silt"] for q in read], fontsize=7.5)
for t, q in zip(a1.get_yticklabels(), read):
    if q.get("kokku"):
        t.set_fontweight("bold")
a1.set_ylim(len(read) - 0.4, -0.6)
a1.set_xlabel("bilanss, % = (sisse - välja) / (sisse + välja); sisse = hommikul ülekaalus suund")
a1.set_ylabel("ristmik (paare; paaride osakaal ristmiku liiklusest)", fontsize=9)
a1.legend(handles=[Line2D([], [], marker="o", ls="", color=C_BLUE, label="mediaan: rohkem sisse (tööle sõidu suund)"),
                   Line2D([], [], marker="o", ls="", color=C_ORANGE, label="mediaan: rohkem välja"),
                   Line2D([], [], color=C_GRAY, marker="o", ms=3, label="päevad (joon = 10.-90. protsentiil)"),
                   Line2D([], [], marker="D", ls="", color=C_GRAY, markeredgecolor=TEXT,
                          label="kokku: kõigi kohtade paarid päeva kaupa liidetud")],
          loc="upper left", fontsize=8)
a1.set_title(f"Vastaspaaride ööpäeva bilanss (ristmikud: tööpäevad {NADAL[0]:%d.%m}-{NADAL[-1]:%d.%m.%Y};\n"
             f"maanteed: tööpäevad alates {pd.Timestamp(ALGUS_MAANTEE):%d.%m.%Y})", fontsize=10)
a1.text(1.01, 1.0, "sõidukit\nööpäevas", transform=a1.transAxes, fontsize=7, color=TEXT2, va="bottom")

xh = (np.arange(96) + 1) / 4
a2.axhline(0, color=TEXT2, lw=1)
for (nimi, _), c in zip(MAANTEED, VARVID):
    if nimi in m_kum:
        a2.plot(xh, m_kum[nimi].reindex(range(96)).values, color=c, lw=1.6, label=nimi)
a2.plot(xh, kum_linn.values, color=TEXT, lw=2.2, ls="--", label=f"linna ristmikud kokku ({len(r)}; {len(paarid)} paari)")
a2.set_xlim(0, 24)
a2.set_xticks(range(0, 25, 2), [f"{h:02d}" for h in range(0, 25, 2)])
a2.set_xlabel("kellaaeg")
a2.set_ylabel("(sisse - välja) keskööst, % ööpäeva paaride liiklusest")
a2.set_title("Kumulatiivne bilanss: hommikul koguneb sissepoole, õhtul tasandub", fontsize=10)
a2.legend(loc="lower left", fontsize=8)
fig.suptitle("Sisse- ja väljasõidu tasakaal: ainult täpselt vastupidised manöövrid (tööle ja tagasi)", x=0.01, ha="left",
             fontweight="bold")
fig.tight_layout()
save(fig, "41_01_suunabilanss")
