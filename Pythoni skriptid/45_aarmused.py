"""
45 - Äärmused: Tallinna ristmike ja maanteede suurimad ja väikseimad päevad, veerandtunnid ja kuud (huvitavad leiud).

SISEND
  common.load_tallinn()      ristmike 15 min loendused puhastatult ja päevasummad (tallinn.count_15min, 29.07.2024 ...
                             01.11.2026); rikked ja vigased päevad on NaN / kehtiv = False
  valjund/29_paevaindeks.csv linna päevaindeks (skript 29): 100 = tavaline tööpäev, mediaan üle ristmike
  valjund/02_kuuandmed.csv   Eesti maanteede kuu liiklusindeks (skript 02), 2023 = 100
  common.load_daily(), counter_month()   maanteeloendurite päevasummad kanali kaupa ja kahtlase mahuga loendur-kuud

ARVUTUS
  Linna päev: 29 päevaindeksi 3 suurimat ja 3 väikseimat päeva.
  Ristmiku tase = kehtivate päevasummade mediaan tavalistel tööpäevadel (E-R, õppetöö, mitte püha). Suurim ja väikseim
    tase; suurima ristmiku suurim kehtiv päevasumma. Suurim veerandtund = suurim 15 min väärtus kehtival päeval.
  Linna veerandtund: LINN ristmikku (kõik peale MP47 ja MP49, mis on MP06 ja MP04 teised koodid, ning MP02, millel on
    andmeid 663 päeva) kokku, ainult pilud, kus kõigi LINN ristmike väärtus on olemas (sama ristmike hulk igas pilus).
    Suurim ja väikseim pilu; tavalise tööpäeva profiil = iga pilu mediaan tavalistel tööpäevadel.
  Uusaastaöö: linna summa 1. jaanuaril kell 00.00-01.00 vs tavalise tööpäeva ja tavalise pühapäeva (laupäeva öö) sama
    tund (pilude mediaanide summa).
  Maantee: Eesti kuu liiklusindeksi (02) väikseim ja suurim kuu. Maanteeloenduri tase = päevasummade mediaan päevadel,
    kus kõik loenduri kanalid on kehtivad, ilma korduvate tundideta ja kahtlase mahuga kuudeta (counter_month); suurim
    tase. Suurim üksik päevasumma (ilma tasemepiiranguta) näitab, kui suured on loenduri vead.

CALCULATION IN PLAIN ENGLISH
  City day = script 29's day index (100 = typical workday); the three highest and lowest days.
  Junction level = median daily total on typical workdays; busiest and quietest junction; the busiest junction's
    largest valid day; the largest single 15-minute value on a valid day.
  City 15 minutes = sum over a fixed set of junctions (LINN), only slots where every one of them has a value. Highest
    and lowest slot; typical workday profile = median of each slot over typical workdays.
  New Year's night = city sum 00:00-01:00 on 1 January vs the same hour on a typical workday and a typical Sunday.
  Highway: lowest and highest month of the national index (02). Counter level = median daily total on days with all
    channels valid, no doubled hours and no suspicious month; the highest level. The largest raw counter-day shows
    how large counter faults are.

VÄLJUND (joonised kaustas Graafikud/, tabelid kaustas valjund/)
  45_01_aarmused.png
      Näitab: linna kõige vaiksemad ja tihedamad päevad ning kuidas vaikseim päev (uusaasta) ja tihedaim päev
      erinevad tavalisest tööpäevast kellaaja kaupa.
      Kuidas: üleval hall joon = 29 päevaindeks (100 = tavaline tööpäev) päevade kaupa, sinised punktid ja sildid =
      kolm suurimat päeva, oranžid = kolm väikseimat; alla 20 päeva vahega päevade punktid kattuvad, neil on üks
      ühine silt (nt N 18.06 ja R 19.06.2026). All x = kellaaeg, y = LINN ristmiku sõidukid 15 min kohta: tume
      joon = tavalise tööpäeva mediaan, sinine = tihedaim päev, oranž = uusaasta 01.01.2025 (keskööl tipp).
  45_aarmused.csv   leid: koht, aeg, väärtus, ühik, võrdlus, märkus
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import (load_tallinn, load_junctions, load_daily, counter_month, load_locations, set_style, save,
                    save_table, OUT_DIR, C_BLUE, C_ORANGE, TEXT, TEXT2)

PAEV = ["E", "T", "K", "N", "R", "L", "P"]
VALJA = {2, 47, 49}       # MP47 = MP06 ja MP49 = MP04 teise koodiga; MP02-l on andmeid 663 päeva (teistel 714-826)
set_style()
read = []


def lisa(leid, koht, aeg, vaartus, uhik, vordlus="", markus=""):
    read.append(dict(leid=leid, koht=koht, aeg=aeg, vaartus=vaartus, uhik=uhik, vordlus=vordlus, markus=markus))
    print(f"{leid:<40} {koht:<34} {aeg:<22} {vaartus:>12,.1f} {uhik:<18} {vordlus}  {markus}")


kell = lambda ts: f"{ts:%d.%m.%Y} kell {ts.hour}.{ts.minute:02d}"
paev = lambda d: f"{PAEV[d.dayofweek]} {d:%d.%m.%Y}"

# --- Linna päevad (29) ------------------------------------------------------------------------------------------
ix = pd.read_csv(OUT_DIR / "29_paevaindeks.csv", parse_dates=["paev"])
for r in ix.nsmallest(3, "indeks").itertuples():
    lisa("Linna vaikseim päev", "Tallinna ristmikud (29 indeks)", paev(r.paev), r.indeks, "% tavalisest tööpäevast",
         "", r.puha if isinstance(r.puha, str) else r.paevatyyp)
top = ix.nlargest(10, "indeks")
for r in top.head(3).itertuples():
    lisa("Linna tihedaim päev", "Tallinna ristmikud (29 indeks)", paev(r.paev), r.indeks, "% tavalisest tööpäevast",
         "", r.vaheaeg)
lisa("Tihedaimast 10 päevast reedeid", "Tallinna ristmikud (29 indeks)", "", (top["nadalapaev"] == 4).sum(), "päeva",
     "10-st")

# --- Ristmikud ---------------------------------------------------------------------------------------------------
t, day = load_tallinn()
jn = load_junctions().set_index("mp_id")
nimi = lambda m: f"{jn.at[m, 'code']} {jn.at[m, 'name']}"
ok = day[day["kehtiv"]]
tav = ok[(ok["paevatyyp"] == "tööpäev") & (ok["vaheaeg"] == "kool")]
tase = tav[~tav["mp_id"].isin({47, 49})].groupby("mp_id")["summa"].median().sort_values()
suur, vaike = tase.index[-1], tase.index[0]
lisa("Tihedaim ristmik", nimi(suur), "tavaline tööpäev", tase.iloc[-1], "sõidukit ööpäevas")
lisa("Vaikseim ristmik", nimi(vaike), "tavaline tööpäev", tase.iloc[0], "sõidukit ööpäevas",
     f"{tase.iloc[-1] / tase.iloc[0]:.0f} korda vähem kui tihedaimal")
r = ok[ok["mp_id"] == suur].nlargest(1, "summa").iloc[0]
lisa("Tihedaima ristmiku rekordpäev", nimi(suur), paev(r.paev), r.summa, "sõidukit ööpäevas",
     f"{r.summa / tase.iloc[-1] - 1:+.0%} tavalisest tööpäevast")
v = t.merge(ok[["mp_id", "paev"]], on=["mp_id", "paev"])
r = v.loc[v["v"].idxmax()]
lisa("Ristmiku tihedaim veerandtund", nimi(r.mp_id), kell(r.ts), r.v, "sõidukit 15 min jooksul",
     f"{r.v / 900:.1f} sõidukit sekundis")

# --- Linna veerandtunnid -----------------------------------------------------------------------------------------
LINN = sorted(set(ok["mp_id"]) - VALJA)
lv = v[v["mp_id"].isin(LINN)]
g = lv.groupby("ts")["v"].agg(["sum", "count"])
linn = g.loc[g["count"] == len(LINN), "sum"]
lf = linn.to_frame("v").assign(paev=linn.index.normalize(), slot=linn.index.hour * 4 + linn.index.minute // 15)
kal = day[["paev", "paevatyyp", "vaheaeg"]].drop_duplicates("paev").set_index("paev")
lf = lf.join(kal, on="paev")
prof = lf[(lf["paevatyyp"] == "tööpäev") & (lf["vaheaeg"] == "kool")].groupby("slot")["v"].median()
puhap = lf[(lf["paevatyyp"] == "pühapäev") & (lf["vaheaeg"] == "kool")].groupby("slot")["v"].median()
assert linn.min() <= prof.min() < prof.max() <= linn.max() and len(prof) == 96, "profiil peab jääma äärmuste vahele"
lisa("Linna tihedaim veerandtund", f"{len(LINN)} ristmikku kokku", kell(linn.idxmax()), linn.max(),
     "sõidukit 15 min jooksul")
lisa("Linna vaikseim veerandtund", f"{len(LINN)} ristmikku kokku", kell(linn.idxmin()), linn.min(),
     "sõidukit 15 min jooksul", f"{linn.max() / linn.min():.0f} korda vähem kui tihedaimal")
lisa("Tavalise tööpäeva tipp-veerandtund", f"{len(LINN)} ristmikku kokku", f"kell {prof.idxmax() // 4}."
     f"{prof.idxmax() % 4 * 15:02d}", prof.max(), "sõidukit 15 min jooksul")
lisa("Tavalise tööpäeva vaikseim veerandtund", f"{len(LINN)} ristmikku kokku", f"kell {prof.idxmin() // 4}."
     f"{prof.idxmin() % 4 * 15:02d}", prof.min(), "sõidukit 15 min jooksul",
     f"{prof.max() / prof.min():.0f} korda vähem kui tipus")
for aasta in sorted(lf.loc[(lf["paev"].dt.month == 1) & (lf["paev"].dt.day == 1), "paev"].dt.year.unique()):
    x = lf[(lf["paev"] == f"{aasta}-01-01") & (lf["slot"] < 4)]
    if len(x) == 4:
        lisa("Uusaastaöö kell 0.00-1.00", f"{len(LINN)} ristmikku kokku", f"01.01.{aasta}", x["v"].sum(),
             "sõidukit tunnis", f"{x['v'].sum() / prof.loc[0:3].sum():.1f} korda tavalise tööpäeva ja "
             f"{x['v'].sum() / puhap.loc[0:3].sum():.1f} korda tavalise pühapäeva sama tund")

# --- Maanteed ----------------------------------------------------------------------------------------------------
k = pd.read_csv(OUT_DIR / "02_kuuandmed.csv")
for f, leid in ((pd.Series.idxmin, "Eesti maanteede vaikseim kuu"), (pd.Series.idxmax, "Eesti maanteede tihedaim kuu")):
    r = k.loc[f(k["liiklus_kokku"])]
    lisa(leid, "kõik maanteeloendurid (02 indeks)", r.kuu, r.liiklus_kokku, "indeks, 2023 = 100")
d = load_daily()
cm = counter_month(d)
nk = d.groupby("id")["kanal"].nunique()
cd = (d[d["kehtiv"]].groupby(["id", "paev", "kuu"])
      .agg(k=("kanal", "nunique"), kokku=("kokku", "sum"), dup=("duplikaat", "any")).reset_index())
cd = cd[(cd["k"] == cd["id"].map(nk)) & ~cd["dup"]]
loc = load_locations().set_index("id")
lnimi = lambda i: f"{loc.at[i, 'nimi']} (mnt {loc.at[i, 'tee_nr']}, km {loc.at[i, 'tee_km']:.1f}, {i})"
puhas = cd.merge(cm.loc[~cm["maht_kahtlane"], ["id", "kuu"]], on=["id", "kuu"])
mt = puhas.groupby("id")["kokku"].median().sort_values()
lisa("Tihedaim maanteeloendur", lnimi(mt.index[-1]), "mediaanpäev 2019-2026", mt.iloc[-1], "sõidukit ööpäevas")
r = cd.loc[cd["kokku"].idxmax()]
lisa("Suurim üksik maantee päevasumma", lnimi(r.id), paev(r.paev), r.kokku, "sõidukit ööpäevas",
     f"{r.kokku / cd.loc[cd['id'] == r.id, 'kokku'].median():.0f} korda loenduri mediaanpäevast", "loenduri viga")
save_table(pd.DataFrame(read), "45_aarmused")

# --- Joonis -----------------------------------------------------------------------------------------------------
fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 8.5), gridspec_kw={"height_ratios": [1, 1.1]})
a1.plot(ix["paev"], ix["indeks"], color="#b9b8b4", lw=1)
for sub, col, va in ((ix.nlargest(3, "indeks"), C_BLUE, "bottom"), (ix.nsmallest(3, "indeks"), C_ORANGE, "top")):
    a1.scatter(sub["paev"], sub["indeks"], s=40, color=col, edgecolor="white", lw=1, zorder=3)
    s = sub.sort_values("paev")
    for _, g in s.groupby((s["paev"].diff().dt.days.fillna(99) >= 20).cumsum()):
        # alla 20 päeva vahega päevade punktid kattuvad sellel teljel: üks silt nimetab kõik päevad
        paevad = " ja ".join(f"{PAEV[d.dayofweek]} {d:%d.%m.%Y}" for d in g["paev"])
        tekst = paevad + "\n" + " / ".join(f"{x:.0f}%" for x in g["indeks"]) + (" (kõrvuti päevad)" if len(g) > 1 else "")
        a1.annotate(tekst, (g["paev"].iloc[0] + (g["paev"].iloc[-1] - g["paev"].iloc[0]) / 2, g["indeks"].max()
                    if va == "bottom" else g["indeks"].min()), fontsize=8, color=TEXT2, ha="center", va=va,
                    xytext=(0, 6 if va == "bottom" else -6), textcoords="offset points")
a1.axhline(100, color=TEXT2, lw=0.8, ls="--")
a1.set_ylim(30, 125)
a1.set_ylabel("% tavalisest tööpäevast")
a1.set_title("Linna päevaindeks (29): kolm tihedaimat ja kolm vaikseimat päeva", loc="left", fontweight="bold")
h = np.arange(96) / 4
tipp = ix.loc[ix["indeks"].idxmax(), "paev"]
a2.plot(h, prof.values, color=TEXT, lw=2, label="tavaline tööpäev (mediaan)")
for d_, col, silt in ((tipp, C_BLUE, "tihedaim päev"), (pd.Timestamp("2025-01-01"), C_ORANGE, "uusaasta")):
    x = lf[lf["paev"] == d_].set_index("slot")["v"].reindex(range(96))
    a2.plot(h, x.values, color=col, lw=2, label=f"{silt} {PAEV[d_.dayofweek]} {d_:%d.%m.%Y}")
a2.set_xlim(0, 24)
a2.set_xticks(range(0, 25, 3))
a2.set_xlabel("kellaaeg")
a2.set_ylabel("sõidukeid 15 min jooksul")
a2.set_title(f"{len(LINN)} ristmikku kokku veerandtunni kaupa", loc="left", fontweight="bold")
a2.legend(loc="upper left", fontsize=9)
fig.tight_layout()
save(fig, "45_01_aarmused")
