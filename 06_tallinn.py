"""
06 - Tallinna ristmikud: tipptunnid, koolivaheaegade mõju, hajutamise stsenaariumid ja seos Harjumaa kütusemüügiga.

Uurimisküsimused: (1) millised on tipptunni mustrid, (2) kui palju saab koormust hajutada, (3) milline on hajutamise
mõju tipule; lisaks koolivaheajad kui loomulik katse ja võrdlus kütusemüügiga.

SISEND
  common.load_tallinn()                ristmike 15 min loendused (tallinn.count_15min; seire.tallinn.ee
                                       aruanne T09; ts = 15 min pilu algus) puhastatult, koos päevatüübi ja
                                       koolivaheaja märkega
  common.load_junctions()              ristmike koodid (MP01...), nimed ja koordinaadid
  common.load_vehicles(),              sõidukipõhine ööpäev (30.09.2026): selle järgi jagatakse iga 15 min pilu
  five_min_shares()                    kolmeks 5 min osaks (ristmik ilma oma ööpäevata saab ristmike keskmise jaotuse)
  valjund/07_maantee_profiilid.csv     Tallinna ümbruse maanteeloendurite 15 min profiilid skriptist 07 (07 käib enne)
  common.load_fuel_county()            Harjumaa kütusemüük, liitrit päevas
  Keskkonnamuutujad: RES=15 -> toored 15 min andmed (failid *_15min); SUUND=LSS|LVS -> ainult linna sisse või linnast
  välja suunduvad kanalid, väljund kausta valjund/LSS või valjund/LVS (vt common).

ARVUTUS
  Tüüpiline tööpäev = E-R, mitte riigipüha ega lühendatud tööpäev, õppetöö ajal. Ristmiku profiil = iga pilu keskmine
    üle selliste päevade; 15 min profiil jagatakse 5 min piludeks (common.to_5min).
  Tipptund (common.peak_hour, peak_metrics) = suurima mahuga 60 min aken, mille algus on hommikul 06:00-09:59 ja õhtul
    14:00-18:59. Näitajad: algus, maht (sõidukit tunnis), osakaal ööpäevast, PHF, tipu laius, liikluse keskaeg ja
    teoreetiline hajutamise potentsiaal = tipptunni mahu vähenemine, kui liiklus tipptunnist +-1 h (kokku 3 tundi)
    oleks täiesti ühtlane.
  Koolivaheajad: iga lühikese vaheaja (sügis, veebruar, kevad) tööpäevade profiil vs õppetöö-tööpäevad 14 päeva enne ja
    14 päeva pärast; muutus % ööpäeva ja tipptundide mahus. Profiil, millest on puudu üle 1 h, jääb välja; lühemad augud
    täidetakse lineaarselt (mitte nulliga).
  Hajutamise mudel (common.shift_peak, spread_reduction): osa tipptunni sõidukitest (0...40%) sõidab Δ = 15, 30 või
    60 min varem, hiljem, pooleks täpselt +-Δ ("mõlemad") või jaotub ühtlaselt vahemikku +-Δ ("ühtlane", nt paindlik
    tööaja algus). Uus tipptund otsitakse 2 h võrra laiendatud aknast; tulemus = tipptunni mahu vähenemine, %.
    Mudel eeldab, et nõudlus ainult nihkub (kogumaht ei muutu), ega arvesta läbilaskevõimet: küllastunud ristmikul
    näitab loendus läbilaskevõimet, mitte tegelikku nõudlust.
  Kuuindeks: ristmiku kuu keskmine ööpäeva summa (kuud, kus kehtivaid päevi on >= 15) ja sellest mahuga kaalutud
    indeks (common.ratio_index, 2025 = 100); korrelatsioon Harjumaa müügiindeksiga logaritmitud tasemetes, kuumuutustes
    ja aastamuutustes. Suunaanalüüsis (SUUND) seda osa ei tehta, sest kütusemüügil suunda pole.

CALCULATION IN PLAIN ENGLISH
  Typical workday = Monday-Friday in school term, not a public holiday or shortened day. Junction profile = average
    of each 15-minute slot over those days (a missing slot is skipped, not counted as 0). For 5-minute steps each
    15-minute value is split by the 5-minute shares measured on the per-vehicle day.
  Peak hour = the 60-minute window with the most vehicles, starting 06:00-09:59 (morning) or 14:00-18:59 (evening).
    Volume = vehicles in that window. Share of day = volume / daily total x 100. PHF = volume / (4 x busiest 15
    minutes inside it). Width = minutes (05-11 or 13-20) with at least 90% of the busiest slot of the peak hour.
    Traffic midpoint = average clock time weighted by vehicles (06-10, 15-19).
    Spreading potential = (1 - average hourly volume from 1 h before to 1 h after the peak hour / peak-hour volume) x
    100: how much lower the peak would be if those 3 hours were perfectly even.
  School holidays: profile of the holiday workdays vs school workdays 14 days before and after; change % = holiday
    volume / reference volume x 100 - 100, for the day and the peak hours. Profiles missing more than 1 h are dropped;
    shorter gaps are filled by straight lines between neighbouring slots.
  Spreading model: share p (0-40%) of the peak-hour vehicles moves by D = 15, 30 or 60 min: earlier, later, half
    exactly D earlier and half D later ("both"), or evenly over the slots within +-D ("even"). The new peak hour is
    searched in a window 2 h wider. Result = (1 - new peak-hour volume / old peak-hour volume) x 100. Total traffic does
    not change and junction capacity is not modelled.
  Monthly index: junction's average daily total in months with at least 15 valid days; index = sum over junctions in
    the month / the same junctions' 2025 averages summed x 100. Correlated with Harju county fuel sales in log levels,
    month-on-month and year-on-year changes (not in the direction runs, sales have no direction).

VÄLJUND (kaust valjund/, suunaanalüüsis valjund/LSS või valjund/LVS)
  06_01_profiilid.png
      Näitab: iga ristmiku tüüpilise tööpäeva kuju ja tipptundide asukohta.
      Kuidas: väikesed joondiagrammid, paneel ristmiku kohta, lõpus Tallinna ümbruse maanteeloendurid (türkiis joon;
      sama koha linna sisse ja linnast välja järjest). x-telg = kellaaeg 0-24, y-telg = sõidukeid pilu (5 või 15 min)
      kohta. Sinine vöönd = hommikune, oranž = õhtune tipptund; nurgas kummagi tipptunni algus ja maht tunnis.
  06_02_profiil_heatmap.png
      Näitab: kuidas liiklus päeva peale jaotub, kõik ristmikud kõrvuti.
      Kuidas: soojuskaart; rida = ristmik (järjestatud hommikuse tipptunni alguse järgi; maanteeloendurid musta joone
      all, sama koha sisse ja välja järjest, koht oma varasema hommikuse tipptunni järgi), veerg = pilu. Värv = pilu
      osakaal ööpäeva liiklusest, % (tumedam = suurem; värviskaala otstes vähim ja suurim väärtus). Sinine ja oranž
      kriips = hommikune ja õhtune tipptund.
  06_03_tipptunnid.png
      Näitab: mis kell on tipptund igal ristmikul.
      Kuidas: rida = ristmik (järjestus nagu 06_02), x-telg = kellaaeg. Sinine riba = hommikune, oranž = õhtune
      tipptund (60 min), riba järel maht (sõidukit tunnis). Taustavöönd = kõigi ristmike summa tipptund.
  06_04_nadalapaevad.png
      Näitab: nädalapäevade erinevust (õppetöö ajal, ilma pühadeta).
      Kuidas: joondiagramm, kõik ristmikud kokku; x-telg = kellaaeg, y-telg = tuhat sõidukit pilu kohta. E-N sinise
      toonid, R oranž, L hall katkendjoon, P hall punktiir.
  06_05_koolivaheajad.png
      Näitab: tööpäeva profiili õppetöö, lühikese koolivaheaja ja suvevaheaja ajal.
      Kuidas: joondiagramm, kõik ristmikud kokku; sinine = õppetöö, oranž = lühike vaheaeg, türkiis = suvi.
  06_06_koolivaheajad_ristmikud.png
      Näitab: kui palju liiklus lühikese koolivaheaja ajal igal ristmikul väheneb.
      Kuidas: punktdiagramm; rida = ristmik, x-telg = muutus, % (vs 2 nädalat enne ja pärast; vaheaegade keskmine).
      Sinine punkt = hommikune tipptund, oranž = õhtune tipptund, hall kriips = ööpäev.
  06_07_hajutamine.png
      Näitab: kui palju väheneb tipptunni maht, kui osa sõitudest nihkub.
      Kuidas: 2 x 2 paneeli (read: nihkujad jaotuvad ühtlaselt vahemikku +-Δ / pooleks täpselt +-Δ; veerud: hommik,
      õhtu). x-telg = tipptunnist nihkuvate sõidukite osakaal, %, y-telg = tipptunni mahu vähenemine, %. Jooned Δ = 15
      (türkiis), 30 (sinine) ja 60 min (oranž): ristmike mediaan, vöönd = kvartiilid. Katkendjoon "piir, kui liiklus
      +-1 h ühtlane" = ristmike teoreetilise hajutamise potentsiaali mediaan ehk suurim võimalik vähenemine.
  06_08_hajutamine_naide.png
      Näitab: hajutamist suurima hommikuse tipuga ristmiku näitel.
      Kuidas: joondiagramm kell 5-11; tume joon = praegune profiil, sinine = 20% tipptunni sõitudest jaotub +-30 min,
      oranž = +-60 min; hall vöönd = praegune tipptund. Legendis uus tipptunni maht ja vähenemine.
  06_09_kutus_harju.png
      Näitab: ristmike liikluse ja Harjumaa kütusemüügi käiku kuude kaupa.
      Kuidas: joondiagramm; y-telg = indeks (2025 = 100). Tume = ristmike liiklusindeks, oranž = kütus kokku, sinine
      katkendjoon = bensiin, türkiis katkendjoon = diisel. Pealkirjas taseme ja kuumuutuste r.
  06_andmed.csv                        päevade, kehtivate päevade ja rikkepilude arv ristmiku kaupa
  06_tipptunnid.csv                    tipunäitajad ristmiku kaupa (+ kõik kokku ja maanteeloendurid)
  06_nadalapaevad.csv                  tipunäitajad nädalapäeva kaupa
  06_koolivaheajad_muutus.csv          muutus vaheaja ja ristmiku kaupa
  06_hajutamine_stsenaariumid.csv      kõik stsenaariumid (ristmik x tipp x viis x Δ x osakaal)
  06_hajutamine_ristmikud.csv          ristmiku kokkuvõte: potentsiaal ja 20% nihke mõju
  06_kuuindeks.csv, 06_kutus_korrelatsioon.csv   kuuindeks ja selle korrelatsioon kütusemüügiga
"""
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from common import (load_tallinn, load_junctions, peak_metrics, peak_hour, shift_peak,
                    spread_reduction, ratio_index, load_fuel_county, corr_pair, slot_label, short_name,
                    set_style, save, save_table, month_axis, AM_WINDOW, PM_WINDOW,
                    TALLINN_BASE_YEAR, VAHEAEG_LABEL, load_vehicles, five_min_shares, to_5min, OUT_DIR, SUUND,
                    RES, SUFFIX, otsamargid, suunad_korvuti,
                    C_BLUE, C_ORANGE, C_AQUA, C_YELLOW, C_GRAY, TEXT2, GRID)

set_style()
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

print("Laen Tallinna ristmike andmeid...")
t, day = load_tallinn()
j = load_junctions().set_index("mp_id")
j["silt"] = j["code"] + " " + j["name"]
# 5 min samm: iga ristmiku 15 min profiil jagatakse 5 min osadeks tema sõidukipõhise ööpäeva järgi (08);
# RES=15 -> toored 15 min andmed
veh = load_vehicles()                   # suunaanalüüsis (SUUND) ainult selle suuna kanalid
SH = five_min_shares(veh, outage_from=load_vehicles(None)) if veh is not None and RES == 5 else None
PH = 12 if SH is not None else 4       # pilusid tunnis
MIN = 60 // PH                          # pilu pikkus minutites
to5 = (lambda p: to_5min(p, SH).reindex(columns=range(24 * PH))) if SH is not None else (lambda p: p)
X = (np.arange(24 * PH) + 0.5) / PH    # pilu keskpunkt tundides

# --- 0) Andmete kokkuvõte ---------------------------------------------------------------------
summ = (day.groupby("mp_id")
        .agg(esimene=("paev", "min"), viimane=("paev", "max"), paevi=("paev", "size"),
             kehtivaid=("kehtiv", "sum"), rikke_pilusid=("rikkeid", "sum")))
summ = j[["code", "name"]].join(summ, how="left")
summ["andmeid"] = summ["paevi"].fillna(0) > 0
save_table(summ.reset_index(), "06_andmed")
tyhjad = summ.index[~summ["andmeid"]].tolist()
print(f"Andmetega ristmikke: {int(summ['andmeid'].sum())}; tühjad (jäetakse joonistelt välja): "
      + ", ".join(j.loc[tyhjad, "code"]))

# --- 1) Tüüpilise tööpäeva profiilid ja tipptunnid -----------------------------------------------
typ = (t["paevatyyp"] == "tööpäev") & (t["vaheaeg"] == "kool")
prof = to5(t[typ].groupby(["mp_id", "slot"])["v"].mean().unstack("slot").reindex(columns=range(96)))
puudulik = prof.index[prof.isna().any(axis=1)]
if len(puudulik):
    print("Tüüpilise tööpäeva profiil puudulik, jäetakse välja:", ", ".join(j.loc[puudulik, "code"]))
    prof = prof.drop(puudulik)
n_days = t[typ & t["v"].notna()].groupby("mp_id")["paev"].nunique()
city = prof.sum(axis=0)

# Tallinna kaardi (07) maanteeloendurid: 15 min profiil 07-st (DATEX-iga; muidu tunni piires ühtlane),
# 5 min pilud ühtlaselt. mp_id < 0 = maantee.
hwf = OUT_DIR / f"07_maantee_profiilid{SUFFIX}.csv"
hw = pd.read_csv(hwf, encoding="utf-8-sig") if hwf.exists() else pd.DataFrame(columns=["koht", "samm"])
hw.index = -np.arange(1, len(hw) + 1)
hprof = pd.DataFrame(np.repeat(hw[[str(i) for i in range(96)]].values / (PH // 4), PH // 4, axis=1)
                     if len(hw) else None, index=hw.index)
silt = {**j["silt"].to_dict(), **{k: f"Maantee: {r.koht}" for k, r in hw.iterrows()}}

rows = []
for mp, v in prof.iterrows():
    rows.append(dict(mp_id=mp, code=j.at[mp, "code"], nimi=j.at[mp, "name"],
                     paevi=int(n_days.get(mp, 0)), **peak_metrics(v.values, per_hour=PH)))
rows.append(dict(mp_id=0, code="KÕIK", nimi="Kõik ristmikud kokku", paevi=int(n_days.max()),
                 **peak_metrics(city.values, per_hour=PH)))
for k, r in hw.iterrows():
    rows.append(dict(mp_id=k, code="MAANTEE", nimi=f"{r.koht} (andmesamm {r.samm})", paevi=np.nan,
                     **peak_metrics(hprof.loc[k].values, per_hour=PH)))
pm = pd.DataFrame(rows)
save_table(pm, "06_tipptunnid")
order = pm[pm.mp_id > 0].sort_values("hommik_algus_h")["mp_id"].tolist()
hw_order = (suunad_korvuti(pm[pm.mp_id < 0].set_index("mp_id").join(hw[["id", "linn", "suund"]]), ["id", "linn"], "suund",
                           "hommik_algus_h") if len(hw) else [])            # sama koha sisse ja välja järjest
allp = pd.concat([prof, hprof])                 # ristmikud + maanteed, samad 5 min pilud

# 1a) väikesed mitmikud: ristmikud, seejärel Tallinna kaardi maanteeloendurid
n = len(prof)
n_all = n + len(hprof)
cols = 6 if n_all > 30 else 5
rws = int(np.ceil(n_all / cols))
fig, axes = plt.subplots(rws, cols, figsize=(cols * 3.0, rws * 2.2), sharex=True)
for ax, mp in zip(axes.flat, sorted(prof.index) + hw_order):
    v = allp.loc[mp].values
    r = pm[pm.mp_id == mp].iloc[0]
    for w, col in [(AM_WINDOW, C_BLUE), (PM_WINDOW, C_ORANGE)]:
        s, _ = peak_hour(v, w, PH)
        ax.axvspan(s / PH, s / PH + 1, color=col, alpha=0.15, lw=0)
    ax.plot(X, v, color=TEXT2 if mp > 0 else C_AQUA, lw=1.3)
    ax.set_title(short_name(silt[mp] if mp < 0 else f"{j.at[mp, 'code']} {j.at[mp, 'name']}", 44, compact=True),
                 fontsize=7.5)
    ax.text(0.02, 0.95, f"{r.hommik_algus}  {r.hommik_soid_h:,.0f}/h\n{r.ohtu_algus}  {r.ohtu_soid_h:,.0f}/h"
            .replace(",", " "), transform=ax.transAxes, va="top", fontsize=7, color=TEXT2)
    ax.set_ylim(0, None)
    ax.set_xticks([0, 6, 12, 18, 24])
    ax.tick_params(labelsize=7)
for k in range(n_all, rws * cols):
    axes.flat[k].axis("off")
    axes.flat[k - cols].tick_params(labelbottom=True)   # all tühi koht -> ülemisele paneelile kellaajad
fig.supxlabel("Kellaaeg", color=TEXT2)
fig.supylabel(f"Sõidukeid {MIN} min kohta", color=TEXT2)
hw_txt = f" + {len(hprof)} maanteeloendurit (türkiis; E-R sept-mai)" if len(hprof) else ""
fig.suptitle(f"Tüüpiline tööpäev õppetöö ajal, {n} ristmikku{hw_txt} (sinine = hommikune, oranž = õhtune "
             f"tipptund)", x=0.01, ha="left", fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.985))
save(fig, "06_01_profiilid")

# 1b) heatmap: osakaal ööpäevast, järjestatud hommikuse tipu järgi; maanteed eraldi plokis all
hm_order = order + hw_order
share = allp.div(allp.sum(axis=1), axis=0) * 100
share = share.loc[hm_order]
fs = 7 if n_all > 35 else 8
fig, ax = plt.subplots(figsize=(12, 0.3 * n_all + 1.8))
sns.heatmap(share, cmap=sns.light_palette(C_BLUE, as_cmap=True), ax=ax, yticklabels=False,
            cbar_kws=dict(label=f"Osakaal ööpäeva liiklusest, % {MIN} min kohta", shrink=0.7))
otsamargid(ax.collections[0].colorbar, lambda x: f"{x:.2f}")
for i, mp in enumerate(hm_order):
    r = pm[pm.mp_id == mp].iloc[0]
    for h, col in [(r.hommik_algus_h, C_BLUE), (r.ohtu_algus_h, C_ORANGE)]:
        ax.plot([h * PH, h * PH + PH], [i + 0.5, i + 0.5], color=col, lw=2.5, solid_capstyle="butt")
if hw_order:
    ax.axhline(len(order), color="black", lw=1.2)
ax.set_yticks(np.arange(n_all) + 0.5)
ax.set_yticklabels([silt[m] for m in hm_order], fontsize=fs, rotation=0)
ax.set_xticks(np.arange(0, 24 * PH + 1, 2 * PH))
ax.set_xticklabels([f"{h:02d}" for h in range(0, 25, 2)], rotation=0)
ax.set_xlabel("Kellaaeg")
ax.set_ylabel("")
ax.set_title(f"Liikluse jaotus päeva jooksul (tööpäev, õppetöö; {MIN} min); jooned = tipptunnid"
             + ("; all maanteeloendurid (andmed 15 min / 1 h)" if hw_order else ""))
save(fig, "06_02_profiil_heatmap")

# 1c) tipptunni ajastus: kus ja millal
p2 = pm.set_index("mp_id").loc[hm_order[::-1]]          # alt üles: maanteed, siis ristmikud
fig, ax = plt.subplots(figsize=(9, 0.27 * n_all + 1.6))
for i, (mp, r) in enumerate(p2.iterrows()):
    for h, vol, col in [(r.hommik_algus_h, r.hommik_soid_h, C_BLUE), (r.ohtu_algus_h, r.ohtu_soid_h, C_ORANGE)]:
        ax.plot([h, h + 1], [i, i], color=col, lw=5, solid_capstyle="butt", alpha=0.9)
        ax.text(h + 1.08, i, f"{vol:,.0f}".replace(",", " "), va="center", fontsize=6.5, color=TEXT2)
cr = pm[pm.mp_id == 0].iloc[0]
for h, col in [(cr.hommik_algus_h, C_BLUE), (cr.ohtu_algus_h, C_ORANGE)]:
    ax.axvspan(h, h + 1, color=col, alpha=0.08, lw=0)
if hw_order:
    ax.axhline(len(hw_order) - 0.5, color="black", lw=1)
ax.set_yticks(range(len(p2)))
ax.set_yticklabels([silt[m] for m in p2.index], fontsize=fs)
ax.set_xlim(5.5, 20)
ax.set_xticks(range(6, 21))
ax.set_xlabel(f"Kellaaeg (riba = tipptund, {MIN} min samm; number = sõidukit tunnis; taust = kõigi ristmike "
              "ühine tipp)")
ax.set_ylim(-0.7, len(p2) - 0.3)
ax.set_title(f"Hommikune ja õhtune tipptund ({n} ristmikku" + (f", all {len(hw_order)} maanteeloendurit)"
                                                              if hw_order else ")"))
save(fig, "06_03_tipptunnid")

# --- 2) Nädalapäevad ------------------------------------------------------------------------------
term = t["vaheaeg"] == "kool"
DN = ["E", "T", "K", "N", "R", "L", "P"]
m15 = (t[term & ~t["paevatyyp"].isin(["riigipüha", "lühendatud"])]
       .groupby(["nadalapaev", "mp_id", "slot"])["v"].mean())
by_dow = pd.DataFrame({d: to5(m15.loc[d].unstack("slot")).sum() for d in range(7)}).T
blues = sns.light_palette(C_BLUE, n_colors=6)[2:]
fig, ax = plt.subplots(figsize=(10, 4.8))
for d in range(7):
    v = by_dow.loc[d].values / 1000
    if d < 4:
        ax.plot(X, v, color=blues[d], lw=1.6, label=DN[d])
    elif d == 4:
        ax.plot(X, v, color=C_ORANGE, lw=2.2, label="R")
    else:
        ax.plot(X, v, color=C_GRAY, lw=1.4, ls="--" if d == 5 else ":", label=DN[d])
ax.set_xticks(range(0, 25, 2))
ax.set_xlim(0, 24)
ax.set_xlabel("Kellaaeg")
ax.set_ylabel(f"Tuhat sõidukit {MIN} min kohta (kõik ristmikud)")
ax.set_title("Nädalapäevade profiilid õppetöö ajal")
ax.legend(ncol=7, loc="upper left", fontsize=9)
save(fig, "06_04_nadalapaevad")
dow_rows = [dict(paev=DN[d], **peak_metrics(by_dow.loc[d].values, per_hour=PH)) for d in range(7)]
save_table(pd.DataFrame(dow_rows), "06_nadalapaevad")

# --- 3) Koolivaheajad: võrdlus vaheajale eelneva ja järgneva 2 nädalaga ----------------------------
work = t[t["paevatyyp"] == "tööpäev"]
bd = pd.Series(sorted(work.loc[work["vaheaeg"] == "lühike", "paev"].unique()))
breaks = bd.groupby((bd.diff() > pd.Timedelta(days=4)).cumsum()).agg(["min", "max"])
cmp_rows = []
for _, b in breaks.iterrows():
    ref_mask = (work["vaheaeg"] == "kool") & (
        work["paev"].between(b["min"] - pd.Timedelta(days=14), b["min"] - pd.Timedelta(days=1)) |
        work["paev"].between(b["max"] + pd.Timedelta(days=1), b["max"] + pd.Timedelta(days=14)))
    brk_mask = work["paev"].between(b["min"], b["max"])
    for kind, m in [("viide", ref_mask), ("vaheaeg", brk_mask)]:
        pr = to5(work[m].groupby(["mp_id", "slot"])["v"].mean().unstack("slot").reindex(columns=range(96)))
        for mp, v in pr.iterrows():
            if v.isna().sum() > PH:                         # üle 1 h puudu
                continue
            met = peak_metrics(v.interpolate(limit_direction="both").values, per_hour=PH)   # kuni 1 h auke täidetakse
            cmp_rows.append(dict(vaheaeg_algus=b["min"].date(), tyyp=kind, mp_id=mp, **met))
cmpd = pd.DataFrame(cmp_rows)
piv = cmpd.pivot_table(index=["vaheaeg_algus", "mp_id"], columns="tyyp",
                       values=["ooopaev", "hommik_soid_h", "ohtu_soid_h"])
chg = pd.DataFrame({k: (piv[(k, "vaheaeg")] / piv[(k, "viide")] - 1) * 100
                    for k in ["ooopaev", "hommik_soid_h", "ohtu_soid_h"]}).dropna()
per_j = chg.groupby("mp_id").mean()
per_break = chg.groupby("vaheaeg_algus").median()
save_table(chg.reset_index(), "06_koolivaheajad_muutus")
print("\nLühikesed koolivaheajad vs 2 nädalat enne/pärast (mediaan üle ristmike, %):")
print(per_break.round(1))

# kogu linna profiil: õppetöö vs lühike vaheaeg vs suvi (tööpäevad)
v15 = (work[work["vaheaeg"].isin(["kool", "lühike", "suvi"])]
       .groupby(["vaheaeg", "mp_id", "slot"])["v"].mean())
vp = pd.DataFrame({k: to5(v15.loc[k].unstack("slot")).sum() for k in ["kool", "lühike", "suvi"]}).T
fig, ax = plt.subplots(figsize=(10, 5))
for k, col in [("kool", C_BLUE), ("lühike", C_ORANGE), ("suvi", C_AQUA)]:
    ax.plot(X, vp.loc[k].values / 1000, color=col, label=VAHEAEG_LABEL[k])
ax.set_xticks(range(0, 25, 2))
ax.set_xlim(0, 24)
ax.set_xlabel("Kellaaeg")
ax.set_ylabel(f"Tuhat sõidukit {MIN} min kohta ({n} ristmikku kokku)")
ax.set_title("Tööpäeva profiil õppetöö ja koolivaheaegade ajal")
ax.legend(loc="upper left", fontsize=9)
save(fig, "06_05_koolivaheajad")

pj = per_j.loc[[m for m in order if m in per_j.index]][::-1]
fig, ax = plt.subplots(figsize=(8.5, 0.22 * len(pj) + 1.8))
yy = np.arange(len(pj))
ax.axvline(0, color=TEXT2, lw=0.6)
ax.scatter(pj["hommik_soid_h"], yy, color=C_BLUE, s=30, label="Hommikune tipptund", zorder=3)
ax.scatter(pj["ohtu_soid_h"], yy, color=C_ORANGE, s=30, label="Õhtune tipptund", zorder=3)
ax.scatter(pj["ooopaev"], yy, color=C_GRAY, marker="|", s=80, label="Ööpäev", zorder=3)
ax.set_yticks(yy)
ax.set_yticklabels([j.at[m, "silt"] for m in pj.index], fontsize=fs)
ax.set_ylim(-0.7, len(pj) - 0.3)
ax.set_xlabel("Muutus lühikese koolivaheaja ajal, % (vs 2 nädalat enne ja pärast)")
ax.set_title("Lühikese koolivaheaja mõju ristmike kaupa")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06 if len(pj) > 30 else -0.13), ncol=3, fontsize=8)
save(fig, "06_06_koolivaheajad_ristmikud")

# --- 4) Hajutamise stsenaariumid --------------------------------------------------------------------
SHARES = np.arange(0, 0.41, 0.05)
SHIFTS = [15, 30, 60]
MODES = ["varem", "hiljem", "mõlemad", "ühtlane"]
sc = []
profiles = {**{mp: prof.loc[mp].values for mp in prof.index}, 0: city.values}
for mp, v in profiles.items():
    for name, win in [("hommik", AM_WINDOW), ("ohtu", PM_WINDOW)]:
        for mode in MODES:
            for sh in SHIFTS:
                for s in SHARES:
                    sc.append(dict(mp_id=mp, tipp=name, suund=mode, nihe_min=sh, osakaal_=round(s * 100),
                                   tipu_vahenemine_=spread_reduction(v, win, s, sh, mode, per_hour=PH)))
sc = pd.DataFrame(sc).rename(columns={"osakaal_": "nihutatud_%", "tipu_vahenemine_": "tipu_vahenemine_%"})
save_table(sc, "06_hajutamine_stsenaariumid")

key = sc[(sc["nihutatud_%"] == 20) & sc.suund.isin(["mõlemad", "ühtlane"])].pivot_table(
    index="mp_id", columns=["tipp", "suund", "nihe_min"], values="tipu_vahenemine_%")
key.columns = [f"{a}_20%_{b}_{c}min_%" for a, b, c in key.columns]
summary = pm[pm.mp_id >= 0].set_index("mp_id")[["code", "nimi", "hommik_algus", "hommik_soid_h",
                                 "hommik_max_potentsiaal_%", "ohtu_algus", "ohtu_soid_h",
                                 "ohtu_max_potentsiaal_%"]].join(key)
save_table(summary.reset_index(), "06_hajutamine_ristmikud")

MODE_TITLE = {"mõlemad": "pool nihkub täpselt Δ võrra varem, pool hiljem",
              "ühtlane": "nihkuvad jaotuvad ühtlaselt vahemikku ±Δ"}
fig, axes = plt.subplots(2, 2, figsize=(13, 8.6), sharey=True, sharex=True)
for i, mode in enumerate(["ühtlane", "mõlemad"]):
    for k, (name, title) in enumerate([("hommik", "Hommikune tipptund"), ("ohtu", "Õhtune tipptund")]):
        ax = axes[i, k]
        sub = sc[(sc.tipp == name) & (sc.suund == mode) & (sc.mp_id > 0)]
        for sh, col in zip(SHIFTS, [C_AQUA, C_BLUE, C_ORANGE]):
            g = sub[sub.nihe_min == sh].groupby("nihutatud_%")["tipu_vahenemine_%"]
            med, q1, q3 = g.median(), g.quantile(0.25), g.quantile(0.75)
            ax.fill_between(med.index, q1, q3, color=col, alpha=0.15, lw=0)
            ax.plot(med.index, med, color=col, marker="o", ms=4, label=f"Δ = {sh} min")
        pot = pm[pm.mp_id > 0][f"{name}_max_potentsiaal_%"].median()
        ax.axhline(pot, color=TEXT2, ls="--", lw=1)
        ax.text(40, pot + 0.4, f"piir, kui liiklus ±1 h ühtlane: {pot:.1f}%", fontsize=8,
                color=TEXT2, ha="right")
        ax.axhline(0, color=TEXT2, lw=0.6)
        ax.set_title(f"{title}: {MODE_TITLE[mode]}", fontsize=10)
        if i == 1:
            ax.set_xlabel("Tipptunnist nihkuvate sõidukite osakaal, %")
    axes[i, 0].set_ylabel("Tipptunni mahu vähenemine, %")
axes[0, 0].legend(loc="lower left", fontsize=9)
fig.suptitle("Hajutamise mõju tipptunnile (ristmike mediaan, vöönd = kvartiilid)",
             x=0.01, ha="left", fontweight="bold")
fig.tight_layout()
save(fig, "06_07_hajutamine")

# näide: suurima hommikuse tipuga ristmik
top = pm[pm.mp_id > 0].sort_values("hommik_soid_h", ascending=False).iloc[0]
v = prof.loc[top.mp_id].values
s0, vol0 = peak_hour(v, AM_WINDOW, PH)
fig, ax = plt.subplots(figsize=(9, 4.5))
xs = slice(5 * PH, 11 * PH)
ax.plot(X[xs], v[xs], color=TEXT2, lw=2.2, label=f"Praegu: tipptund {vol0:,.0f} sõid/h".replace(",", " "))
for sh, col in [(30, C_BLUE), (60, C_ORANGE)]:
    new = shift_peak(v, s0, 0.2, sh // MIN, "ühtlane", per_hour=PH)
    _, nv = peak_hour(new, (AM_WINDOW[0] - 2, AM_WINDOW[1] + 2), PH)
    ax.plot(X[xs], new[xs], color=col, lw=1.8,
            label=f"20% jaotub ±{sh} min: {nv:,.0f} sõid/h (−{(1 - nv / vol0) * 100:.1f}%)".replace(",", " "))
ax.axvspan(s0 / PH, s0 / PH + 1, color=C_GRAY, alpha=0.12, lw=0)
ax.set_xlabel("Kellaaeg")
ax.set_ylabel(f"Sõidukeid {MIN} min kohta")
ax.set_title(f"Hajutamise näide: {top.code} {top.nimi} (hommik, tüüpiline tööpäev)")
ax.legend(loc="lower right", fontsize=9)
save(fig, "06_08_hajutamine_naide")

# --- 5) Kuuindeks vs Harjumaa kütusemüük --------------------------------------------------------------
if SUUND:      # suuna osakaal on ristmikul konstantne -> kuuindeks sama mis kokku; kütusel suunda pole
    sys.exit(0)
dv = day[day["kehtiv"]].assign(kuu=day["paev"].dt.to_period("M"))
jm = dv.groupby(["mp_id", "kuu"]).agg(paevi=("paev", "size"), maht=("summa", "mean")).reset_index()
jm = jm[jm["paevi"] >= 15]
jidx = ratio_index(jm, "maht", site="mp_id").set_index("kuu")
fuel = load_fuel_county()
fuel = fuel[fuel["maakond_full"] == "Harjumaa"].set_index("kuu")[["bensiin", "diisel"]]
fuel["kokku"] = fuel["bensiin"] + fuel["diisel"]
fidx = fuel / fuel[fuel.index.year == TALLINN_BASE_YEAR].mean() * 100
m = jidx[["indeks", "kohti"]].join(fidx, how="inner")
save_table(m.reset_index(), "06_kuuindeks")

crows = []
for f in ["kokku", "bensiin", "diisel"]:
    a, b = np.log(m["indeks"]), np.log(m[f])
    for kuju, fa, fb in [("tase", a, b), ("kuumuutus", a.diff(), b.diff()), ("YoY", a.diff(12), b.diff(12))]:
        crows.append(dict(kutus=f, kuju=kuju, **corr_pair(fa, fb)))
fc = pd.DataFrame(crows)
save_table(fc, "06_kutus_korrelatsioon")
print("\nRistmike indeks vs Harjumaa kütus:")
print(fc.round(3).to_string(index=False))

fig, ax = plt.subplots(figsize=(10, 4.6))
tt = m.index.to_timestamp()
ax.plot(tt, m["indeks"], color=TEXT2, lw=2.4, label="Tallinna ristmikud (liiklusindeks)")
for f, col, lab in [("kokku", C_ORANGE, "Harjumaa kütus kokku"), ("bensiin", C_BLUE, "bensiin"),
                    ("diisel", C_AQUA, "diisel")]:
    ax.plot(tt, m[f], color=col, lw=2 if f == "kokku" else 1.2, ls="-" if f == "kokku" else "--", label=lab)
ax.axhline(100, color=TEXT2, lw=0.6, ls=":")
c = fc[(fc.kutus == "kokku") & (fc.kuju == "tase")].iloc[0]
c2 = fc[(fc.kutus == "kokku") & (fc.kuju == "kuumuutus")].iloc[0]
ax.set_title(f"Tallinna ristmike liiklus vs Harjumaa kütusemüük\n(taseme r = {c.r:.2f}; kuumuutuste r = "
             f"{c2.r:.2f}; n = {int(c.n)} kuud)", fontsize=11)
ax.set_ylabel(f"Indeks, {TALLINN_BASE_YEAR} = 100")
ax.legend(loc="lower right", fontsize=8, ncol=2)
save(fig, "06_09_kutus_harju")

print("\nTipptunnid (tüüpiline tööpäev):")
print(pm[["code", "nimi", "paevi", "ooopaev", "hommik_algus", "hommik_soid_h", "hommik_osakaal_%",
          "hommik_phf", "hommik_max_potentsiaal_%", "ohtu_algus", "ohtu_soid_h", "ohtu_osakaal_%",
          "ohtu_max_potentsiaal_%"]].round(2).to_string(index=False))
print("\nHajutamine, 20% (ristmike mediaan, %):")
print(sc[(sc["nihutatud_%"] == 20) & (sc.mp_id > 0)]
      .groupby(["tipp", "suund", "nihe_min"])["tipu_vahenemine_%"].median().unstack().round(1))
