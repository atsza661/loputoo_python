"""
06_2 - Tallinna ristmikud, teine versioon: tipuaeg ei ole kindel 60 min tund, vaid muutuva pikkusega aeg, mil liiklus
on sama aeglane või sama tihe kui ristmiku tavalises tipus (15 min kuni mitu tundi). 06 joonised, mis sõltuvad
tipptunnist, uue määratlusega: profiilid, soojuskaart, tipuajad, koolivaheaja mõju ja hajutamine.

SISEND
  common.load_tallinn(), load_junctions()     ristmike 15 min loendused puhastatult, päevatüübi ja koolivaheaja märkega;
                                              ristmike koodid ja nimed
  common.tooaeva_profiilid()                  tavaliste tööpäevade 15 min profiilid päevade kaupa (päevast päeva kõikumine)
  common.mudeli_parameetrid()                 mudel A (foori viivitus -> kiirus, vt 40_0): ristmiku piir (27), tsükkel (09),
                                              g/C ja küllastusvoog (33)
  valjund/07_maantee_profiilid.csv            Tallinna kaardi maanteeloendurite 15 min profiilid (07)
  valjund/07_2_tipuajad_kohad.csv             nende tipuajad mõõdetud kiirusega (07_2 käib enne)
  Ainult 15 min samm (toorandmed, nagu mudel A ja päevast päeva kõikumine) ja mõlemad suunad: SUUND ja RES ei kehti.

ARVUTUS
  Tüüpiline tööpäev nagu 06: E-R, mitte püha ega lühendatud päev, õppetöö ajal; profiil = iga 15 min pilu keskmine.
  Kiirus = mudel A: foori viivitus (HCM valem) 500 m lõigul vaba kiirusega 50 km/h. Kiirus väheneb ainult voo kasvades.
  Päevast päeva kõikumine (common.ristmike_tipumura): kõik tavalised tööpäevad, iga päeva suurim 15 min voog ja
    aeglaseim kiirus tipuaknas, 21 päeva liikuva mediaani suhtes; voo kõikumine = kui palju väiksem on kerge päeva (10.
    protsentiil) tipp, kiiruse kõikumine = kui palju kiirem on kerge päeva (90. protsentiil) tipp (nagu 40_0). Kõik
    ristmikud kokku: ainult voog, kõikumine ristmike summast päevadel, kus on kõik valimi ristmikud (andmed >= 85%
    päevadest).
  Tipuaeg (common.tipuaja_lavi, tipuaeg; sama kui 07_2), hommikul ja õhtul eraldi:
    tipu pilu = suurima vooga 15 min hommikul 06:00-10:00, õhtul 14:00-19:00
    pilu on tipuaja tasemel, kui
      voog >= tipu voog x (1 - voo kõikumine)                    sama tihe kui tavaline tipp, VÕI
      kiirus <= tipu kiirus x (1 + kiiruse kõikumine)            sama aeglane kui tavaline tipp ja ühtlasi märgatavalt
             ja <= tavakiirus x (1 - kiiruse kõikumine)          aeglasem kui tavaliselt (pilude mediaan kell 06-20;
                                                                 voog vähemalt pool tipu voost). Kiiruse tingimus kehtib
                                                                 ainult siis, kui tipp ise on märgatavalt aeglasem.
    Tipuaeg = tipu pilu ümber olevad järjestikused tipuaja tasemel pilud (üks madalam pilu vahel loetakse sisse),
    hommikul kell 05-12, õhtul 12-21. Ristmikul on kiiruse tingimus samuti voo lävi (mudel A); see on voo lävest madalam
    küllastuse lähedal, kus viivitus kasvab järsult. Tipuaja lävi = väikseim voog, mille juures pilu on tipuaja tasemel.
  Koolivaheajad: nagu 06 (iga lühike vaheaeg vs õppetöö-tööpäevad 14 päeva enne ja 14 päeva pärast; profiil, millest on
    puudu üle 1 h, jääb välja). Lävendid viiteperioodi profiilist; muutus = tipuaja tasemel minutite muutus vaheajal
    (samade lävenditega) ja tipu 15 min voo muutus, %; vaheaegade keskmine.
  Hajutamine (common.shift_peak kogu tipuaja kohta): osa tipuaja sõidukitest (0...40%) sõidab Δ = 15, 30 või 60 min
    varem, hiljem, pooleks täpselt +-Δ ("mõlemad") või jaotub ühtlaselt vahemikku +-Δ ("ühtlane"). Tulemus = tipuaja
    tasemel minutid otsingualas (praeguste lävenditega: sama tihe või sama aeglane kui praegu tipus; ka kahe eraldi
    lõiguna; madalamaid vahepilusid sisse lugemata, nii enne kui pärast) ja tipu 15 min voo vähenemine, %. Kogumaht ei
    muutu; läbilaskevõimet ei arvestata (nagu 06).

CALCULATION IN PLAIN ENGLISH
  Profiles as in 06: average of each 15-minute slot over typical workdays.
  Speed (model A): delay per vehicle from the HCM signal formula for the slot's flow, turned into the speed on a 500 m
    stretch at free speed 50 km/h: speed = 3.6 x 500 / (500 / (50 / 3.6) + delay). Speed only falls when flow rises.
  Day-to-day noise: for every workday, the largest 15-minute flow and the slowest speed in the peak window, each divided
    by its own 21-day moving median. Flow noise = 1 - (10th percentile / median) of that ratio, i.e. how much
    smaller a light day's peak is; speed noise = 90th percentile / median - 1, i.e. how much faster a light day is.
  Rush period, morning and evening separately:
    peak slot = the 15 minutes with the most flow (06:00-10:00, 14:00-19:00);
    a slot is at peak level when flow >= peak flow x (1 - flow noise), OR (speed <= peak speed x (1 + speed noise) AND
    speed <= usual speed x (1 - speed noise), with flow at least half the peak flow); peak speed = slowest slot among
    those with at least half the peak flow, usual speed = median slot speed 06-20. The speed test is used only when the
    peak speed itself is below usual speed x (1 - speed noise).
    Rush period = consecutive peak-level slots around the peak slot (one lower slot in between is allowed), within
    05-12 or 12-21. Its threshold = the smallest flow at which a slot counts as peak level.
  School holidays: thresholds from the reference profile (14 days before and after); change = holiday minutes at peak
    level - reference minutes, and peak 15-minute flow change %, averaged over the holidays.
  Spreading: share p (0-40%) of all rush-period vehicles moves by D = 15, 30 or 60 min (modes as in 06). Result =
    minutes still at peak level with today's thresholds, and peak 15-minute flow reduction %. Total traffic does not
    change; capacity is not modelled.

VÄLJUND (kaust valjund/)
  06_2_01_profiilid.png
      Näitab: iga ristmiku tüüpilise tööpäeva kuju ja tipuaegu (pikkus erineb).
      Kuidas: väikesed joondiagrammid, paneel ristmiku kohta, lõpus Tallinna ümbruse maanteeloendurid (türkiis joon;
      sama koha linna sisse ja linnast välja järjest). x-telg = kellaaeg 0-24, y-telg = sõidukeid 15 min kohta.
      Sinine vöönd = hommikune, oranž = õhtune tipuaeg; nurgas kummagi algus ja lõpp ning kestus.
  06_2_02_profiil_heatmap.png
      Näitab: kuidas liiklus päeva peale jaotub ja kui pikk on tipuaeg, kõik ristmikud kõrvuti.
      Kuidas: soojuskaart; rida = ristmik (järjestatud hommikuse tipuaja alguse järgi; maanteeloendurid musta joone
      all, sama koha sisse ja välja järjest, koht oma varasema hommikuse tipuaja järgi), veerg = 15 min pilu. Värv =
      pilu osakaal ööpäeva liiklusest, % (tumedam = suurem; skaala otstes vähim ja suurim). Sinine ja oranž kriips =
      hommikune ja õhtune tipuaeg.
  06_2_03_tipptunnid.png
      Näitab: millal tipuaeg igal ristmikul algab ja lõpeb.
      Kuidas: rida = ristmik (järjestus nagu 06_2_02), x-telg = kellaaeg. Sinine riba = hommikune, oranž = õhtune
      tipuaeg, riba järel kestus. Taustavöönd = kõigi ristmike summa tipuaeg; punktiir = 60 min pikkus (06 tipptund)
      riba alguses.
  06_2_04_koolivaheajad_ristmikud.png
      Näitab: kui palju lühem on tipuaeg lühikese koolivaheaja ajal igal ristmikul.
      Kuidas: punktdiagramm; rida = ristmik, x-telg = tipuaja tasemel minutite muutus vaheajal (vs 2 nädalat enne ja
      pärast, samade lävenditega; vaheaegade keskmine). Sinine = hommik, oranž = õhtu.
  06_2_05_hajutamine.png
      Näitab: kui palju lüheneb tipuaeg, kui osa tipuaja sõitudest nihkub.
      Kuidas: 2 x 2 paneeli (read: nihkujad jaotuvad ühtlaselt vahemikku +-Δ / pooleks täpselt +-Δ; veerud: hommik,
      õhtu). x-telg = tipuajast nihkuvate sõidukite osakaal, %, y-telg = tipuaja lühenemine, min (tipuaja tasemel
      minutid enne - pärast; miinus = tipuaeg pikeneb). Jooned Δ = 15 (türkiis), 30 (sinine) ja 60 min (oranž): ristmike mediaan, vöönd =
      kvartiilid. Katkendjoon = praeguse tipuaja mediaan (tipuaeg kaob täielikult).
  06_2_06_hajutamine_naide.png
      Näitab: hajutamist suurima hommikuse tipuga ristmiku näitel.
      Kuidas: joondiagramm kell 5-11; tume joon = praegune profiil, sinine = 20% tipuaja sõitudest jaotub +-30 min,
      oranž = +-60 min; hall vöönd = praegune tipuaeg, punktiir = tipuaja lävi (sõidukeid 15 min). Legendis tipuaja
      tasemel minutid ja muutus.
  06_2_tipptunnid.csv                   tipuaja näitajad ristmiku kaupa (common.tipuaja_naitajad; + kõik kokku, maanteed
                                        07_2-st), kõikumine ja tipuaja lävi
  06_2_koolivaheajad_muutus.csv         muutus vaheaja, ristmiku ja tipu kaupa
  06_2_hajutamine_stsenaariumid.csv     kõik stsenaariumid (ristmik x tipp x viis x Δ x osakaal)
  06_2_hajutamine_ristmikud.csv         ristmiku kokkuvõte: tipuaeg ja 20% nihke mõju
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from common import (OUT_DIR, SUUND, STS_AKNAD, TIPUAJA_ALA, load_tallinn, load_junctions, tooaeva_profiilid,
                    mudeli_parameetrid, ristmike_kiirus, ristmike_tipumura, tipu_mura, tipuaja_lavi, tipuaeg,
                    tipuaja_naitajad, shift_peak, peak_hour, short_name, slot_label, set_style, save, save_table,
                    otsamargid, suunad_korvuti, AM_WINDOW, C_BLUE, C_ORANGE, C_AQUA, C_GRAY, TEXT2)

assert not SUUND, "06_2 teeb ainult mõlemad suunad koos (SUUND ei kehti)"
PH = 4                                   # 15 min pilud
X = (np.arange(96) + 0.5) / PH          # pilu keskpunkt tundides
SHARES = np.arange(0, 0.41, 0.05)
SHIFTS = [15, 30, 60]
MODES = ["varem", "hiljem", "mõlemad", "ühtlane"]
TIPP_TXT = {"hommik": "Hommikune tipuaeg", "ohtu": "Õhtune tipuaeg"}

# enesekontroll: kogu tipuaja nihutamine ei muuda päeva summat
_v = np.linspace(5, 50, 96)
for _m in MODES:
    assert abs(shift_peak(_v, 30, 0.25, 4, _m, pikkus=7).sum() - _v.sum()) < 1e-9

set_style()
pd.set_option("display.width", 220)
print("Laen andmeid...")
t, day = load_tallinn()
j = load_junctions().set_index("mp_id")
j["silt"] = j["code"] + " " + j["name"]
pa, _ = mudeli_parameetrid()
mura = ristmike_tipumura(pa)
kiirus = lambda mp, V: ristmike_kiirus(np.full(len(V), mp), V, pa)       # mudel A, read = sama ristmik

# --- 1) Tüüpilise tööpäeva profiilid ja tipuajad ------------------------------------------------------------------------
typ = (t["paevatyyp"] == "tööpäev") & (t["vaheaeg"] == "kool")
prof = t[typ].groupby(["mp_id", "slot"])["v"].mean().unstack("slot").reindex(columns=range(96))
puudulik = prof.index[prof.isna().any(axis=1)]
if len(puudulik):
    print("Tüüpilise tööpäeva profiil puudulik, jäetakse välja:", ", ".join(j.loc[puudulik, "code"]))
    prof = prof.drop(puudulik)
n_days = t[typ & t["v"].notna()].groupby("mp_id")["paev"].nunique()
city = prof.sum(axis=0).to_numpy()
S = {mp: kiirus(mp, prof.loc[[mp]].to_numpy())[0] for mp in prof.index}


def lavid(v, mp, s):
    """Ristmiku mõlema tipu lävendid (mp = 0: kõik ristmikud kokku, ainult voog)."""
    mu = lambda tp: mura_city[tp] if mp == 0 else (mura.at[(mp, tp), "mura_q"], mura.at[(mp, tp), "mura_s"])
    return {tp: tipuaja_lavi(v, tp, mu(tp)[0], s, mu(tp)[1]) for tp in STS_AKNAD}


def efektiivne_lavi(mp, lv):
    """Väikseim 15 min voog, mille juures ristmik on tipuaja tasemel (voo või kiiruse tingimus; mudel A)."""
    if lv["s"] is None:
        return lv["q"]
    q = np.linspace(0, 2 * lv["q"], 4001)
    aeglane = q[(kiirus(mp, q[:, None])[:, 0] <= lv["s"]) & (q >= lv["q_s"])]
    return min(lv["q"], aeglane.min()) if len(aeglane) else lv["q"]


# kõik ristmikud kokku: kõikumine ristmike summast (valim = andmed >= 85% päevadest, päevad, kus kõik valimis)
ix, V = tooaeva_profiilid(algus="2000-01-01")
osa = ix.groupby("mp_id").size() / ix["paev"].nunique()
valim = osa[osa >= 0.85].index
iv = ix["mp_id"].isin(valim).to_numpy()
Vc = pd.DataFrame(V[iv]).groupby(ix.loc[iv, "paev"].to_numpy()).agg(["sum", "count"])
koos = Vc.xs("count", axis=1, level=1).iloc[:, 0] == len(valim)
mura_city = {tp: (mq, np.nan) for tp, (mq, _) in
             tipu_mura(Vc.index[koos], Vc.xs("sum", axis=1, level=1)[koos].to_numpy()).items()}

rows, LV = [], {}
for mp in prof.index:
    v = prof.loc[mp].to_numpy()
    LV[mp] = lavid(v, mp, S[mp])
    rows.append(dict(mp_id=mp, code=j.at[mp, "code"], nimi=j.at[mp, "name"], paevi=int(n_days.get(mp, 0)),
                     **{f"{tp}_mura_q_%": mura.at[(mp, tp), "mura_q"] * 100 for tp in STS_AKNAD},
                     **{f"{tp}_mura_s_%": mura.at[(mp, tp), "mura_s"] * 100 for tp in STS_AKNAD},
                     **{f"{tp}_lavi_kokku_soid_15min": efektiivne_lavi(mp, LV[mp][tp]) for tp in STS_AKNAD},
                     **tipuaja_naitajad(v, LV[mp], S[mp])))
LV[0] = lavid(city, 0, None)
rows.append(dict(mp_id=0, code="KÕIK", nimi="Kõik ristmikud kokku (ainult voog)", paevi=int(n_days.max()),
                 **{f"{tp}_mura_q_%": mura_city[tp][0] * 100 for tp in STS_AKNAD},
                 **{f"{tp}_lavi_kokku_soid_15min": LV[0][tp]["q"] for tp in STS_AKNAD},
                 **tipuaja_naitajad(city, LV[0])))

# Tallinna kaardi maanteeloendurid: profiil 07-st, tipuaeg 07_2-st (mõõdetud kiirusega). mp_id < 0 = maantee.
hw = pd.read_csv(OUT_DIR / "07_maantee_profiilid.csv", encoding="utf-8-sig")
hw.index = -np.arange(1, len(hw) + 1)
hprof = pd.DataFrame(hw[[str(i) for i in range(96)]].to_numpy(), index=hw.index)
h2 = pd.read_csv(OUT_DIR / "07_2_tipuajad_kohad.csv", encoding="utf-8-sig").set_index("koht")
for k, r in hw.iterrows():
    rows.append(dict(mp_id=k, code="MAANTEE", nimi=r.koht, paevi=np.nan,
                     **h2.loc[r.koht].drop(["tyyp", "linn", "suund", "id", "lat", "lon", "km_linnast"]).to_dict()))
pm = pd.DataFrame(rows)
save_table(pm, "06_2_tipptunnid")
silt = {**j["silt"].to_dict(), **{k: f"Maantee: {r.koht}" for k, r in hw.iterrows()}}
order = pm[pm.mp_id > 0].sort_values(["hommik_algus_h", "hommik_lopp_h"])["mp_id"].tolist()
hw_order = suunad_korvuti(pm[pm.mp_id < 0].set_index("mp_id").join(hw[["id", "linn", "suund"]]), ["id", "linn"], "suund",
                          ["hommik_algus_h", "hommik_lopp_h"])           # sama koha sisse ja välja järjest
allp = pd.concat([prof.set_axis(range(96), axis=1), hprof])
P = pm.set_index("mp_id")
n, n_all = len(prof), len(prof) + len(hprof)
fs = 7 if n_all > 35 else 8
vahemik = lambda r, tp: f"{getattr(r, f'{tp}_algus')}–{getattr(r, f'{tp}_lopp')}"

# 1a) väikesed mitmikud
cols = 6 if n_all > 30 else 5
rws = int(np.ceil(n_all / cols))
fig, axes = plt.subplots(rws, cols, figsize=(cols * 3.0, rws * 2.2), sharex=True)
for ax, mp in zip(axes.flat, sorted(prof.index) + hw_order):
    v = allp.loc[mp].to_numpy()
    r = P.loc[mp]
    for tp, col in [("hommik", C_BLUE), ("ohtu", C_ORANGE)]:
        ax.axvspan(r[f"{tp}_algus_h"], r[f"{tp}_lopp_h"], color=col, alpha=0.18, lw=0)
    ax.plot(X, v, color=TEXT2 if mp > 0 else C_AQUA, lw=1.3)
    ax.set_title(short_name(silt[mp], 44, compact=True), fontsize=7.5)
    ax.text(0.02, 0.95, "\n".join(f"{r[f'{tp}_algus']}–{r[f'{tp}_lopp']}  {int(r[f'{tp}_kestus_min'])} min"
                                  for tp in STS_AKNAD), transform=ax.transAxes, va="top", fontsize=7, color=TEXT2)
    ax.set_ylim(0, v.max() * 1.3)
    ax.set_xticks([0, 6, 12, 18, 24])
    ax.tick_params(labelsize=7)
for k in range(n_all, rws * cols):
    axes.flat[k].axis("off")
    axes.flat[k - cols].tick_params(labelbottom=True)
fig.supxlabel("Kellaaeg", color=TEXT2)
fig.supylabel("Sõidukeid 15 min kohta", color=TEXT2)
fig.suptitle(f"Tüüpiline tööpäev õppetöö ajal, {n} ristmikku + {len(hprof)} maanteeloendurit (türkiis): tipuaeg = "
             "sama aeglane või sama tihe kui tavalises tipus (sinine = hommik, oranž = õhtu)",
             x=0.01, ha="left", fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.985))
save(fig, "06_2_01_profiilid")

# 1b) soojuskaart
hm_order = order + hw_order
share = allp.div(allp.sum(axis=1), axis=0).loc[hm_order] * 100
fig, ax = plt.subplots(figsize=(12, 0.3 * n_all + 1.8))
sns.heatmap(share, cmap=sns.light_palette(C_BLUE, as_cmap=True), ax=ax, yticklabels=False,
            cbar_kws=dict(label="Osakaal ööpäeva liiklusest, % 15 min kohta", shrink=0.7))
otsamargid(ax.collections[0].colorbar, lambda x: f"{x:.2f}")
for i, mp in enumerate(hm_order):
    for tp, col in [("hommik", C_BLUE), ("ohtu", C_ORANGE)]:
        ax.plot([P.at[mp, f"{tp}_algus_h"] * PH, P.at[mp, f"{tp}_lopp_h"] * PH], [i + 0.5, i + 0.5], color=col, lw=2.5,
                solid_capstyle="butt")
ax.axhline(len(order), color="black", lw=1.2)
ax.set_yticks(np.arange(n_all) + 0.5)
ax.set_yticklabels([silt[m] for m in hm_order], fontsize=fs, rotation=0)
ax.set_xticks(np.arange(0, 24 * PH + 1, 2 * PH))
ax.set_xticklabels([f"{h:02d}" for h in range(0, 25, 2)], rotation=0)
ax.set_xlabel("Kellaaeg")
ax.set_ylabel("")
ax.set_title("Liikluse jaotus päeva jooksul (tööpäev, õppetöö; 15 min); jooned = tipuajad (pikkus erineb); "
             "all maanteeloendurid")
save(fig, "06_2_02_profiil_heatmap")

# 1c) tipuajad: kus ja millal
p2 = P.loc[hm_order[::-1]]
fig, ax = plt.subplots(figsize=(9.5, 0.27 * n_all + 1.6))
for i, (mp, r) in enumerate(p2.iterrows()):
    for tp, col in [("hommik", C_BLUE), ("ohtu", C_ORANGE)]:
        a, b = r[f"{tp}_algus_h"], r[f"{tp}_lopp_h"]
        ax.plot([a, b], [i, i], color=col, lw=5, solid_capstyle="butt", alpha=0.9)
        ax.plot([a, a + 1], [i - 0.32, i - 0.32], color=TEXT2, lw=0.7, ls=":")
        ax.text(b + 0.08, i, f"{int(r[f'{tp}_kestus_min'])}", va="center", fontsize=6.5, color=TEXT2)
for tp, col in [("hommik", C_BLUE), ("ohtu", C_ORANGE)]:
    ax.axvspan(P.at[0, f"{tp}_algus_h"], P.at[0, f"{tp}_lopp_h"], color=col, alpha=0.08, lw=0)
ax.axhline(len(hw_order) - 0.5, color="black", lw=1)
ax.set_yticks(range(len(p2)))
ax.set_yticklabels([silt[m] for m in p2.index], fontsize=fs)
ax.set_xlim(5, 21)
ax.set_xticks(range(5, 22))
ax.set_xlabel("Kellaaeg (riba = tipuaeg, number = kestus, min; punktiir = 60 min; taust = kõigi ristmike summa tipuaeg)")
ax.set_ylim(-0.7, len(p2) - 0.3)
ax.set_title(f"Hommikune ja õhtune tipuaeg ({n} ristmikku, all {len(hw_order)} maanteeloendurit)")
save(fig, "06_2_03_tipptunnid")

# --- 2) Koolivaheajad: tipuaja tasemel minutid vaheajal vs 2 nädalat enne ja pärast -----------------------------------
work = t[t["paevatyyp"] == "tööpäev"]
bd = pd.Series(sorted(work.loc[work["vaheaeg"] == "lühike", "paev"].unique()))
breaks = bd.groupby((bd.diff() > pd.Timedelta(days=4)).cumsum()).agg(["min", "max"])
pr = lambda m: work[m].groupby(["mp_id", "slot"])["v"].mean().unstack("slot").reindex(columns=range(96))
cmp_rows = []
for _, b in breaks.iterrows():
    ref = pr((work["vaheaeg"] == "kool") & (
        work["paev"].between(b["min"] - pd.Timedelta(days=14), b["min"] - pd.Timedelta(days=1)) |
        work["paev"].between(b["max"] + pd.Timedelta(days=1), b["max"] + pd.Timedelta(days=14))))
    brk = pr(work["paev"].between(b["min"], b["max"]))
    for mp in ref.index.intersection(brk.index).intersection(mura.index.get_level_values(0)):
        if ref.loc[mp].isna().sum() > PH or brk.loc[mp].isna().sum() > PH:    # üle 1 h puudu
            continue
        vr, vb = (ref.loc[mp].interpolate(limit_direction="both").to_numpy(),    # kuni 1 h auke täidetakse
                  brk.loc[mp].interpolate(limit_direction="both").to_numpy())
        sr, sb = kiirus(mp, np.vstack([vr, vb]))
        lv = lavid(vr, mp, sr)
        for tp in STS_AKNAD:
            lo, hi = (h * PH for h in TIPUAJA_ALA[tp])
            m0, m1 = tipuaeg(vr, tp, lv[tp], sr)["minuteid"], tipuaeg(vb, tp, lv[tp], sb)["minuteid"]
            cmp_rows.append(dict(vaheaeg_algus=b["min"].date(), mp_id=mp, tipp=tp, viide_min=m0, vaheaeg_min=m1,
                                 muutus_min=m1 - m0, tipp15_muutus_pct=(vb[lo:hi].max() / vr[lo:hi].max() - 1) * 100))
cmpd = pd.DataFrame(cmp_rows).rename(columns={"tipp15_muutus_pct": "tipp15_muutus_%"})
save_table(cmpd, "06_2_koolivaheajad_muutus")
per_j = cmpd.groupby(["mp_id", "tipp"])[["viide_min", "muutus_min", "tipp15_muutus_%"]].mean().unstack("tipp")
print("\nLühikesed koolivaheajad vs 2 nädalat enne/pärast (mediaan üle ristmike):")
print(cmpd.groupby(["vaheaeg_algus", "tipp"])[["viide_min", "vaheaeg_min", "muutus_min", "tipp15_muutus_%"]]
      .median().round(1).to_string())

pj = per_j.loc[[m for m in order if m in per_j.index]][::-1]
fig, ax = plt.subplots(figsize=(8.5, 0.22 * len(pj) + 1.8))
yy = np.arange(len(pj))
ax.axvline(0, color=TEXT2, lw=0.6)
for tp, col, dy in [("hommik", C_BLUE, 0.12), ("ohtu", C_ORANGE, -0.12)]:
    ax.scatter(pj[("muutus_min", tp)], yy + dy, color=col, s=30, zorder=3,
               label=f"{TIPP_TXT[tp]} (enne vaheaega mediaan {pj[('viide_min', tp)].median():.0f} min)")
ax.set_yticks(yy)
ax.set_yticklabels([j.at[m, "silt"] for m in pj.index], fontsize=fs)
ax.set_ylim(-0.7, len(pj) - 0.3)
ax.set_xlabel("Tipuaja muutus lühikese koolivaheaja ajal, min (vs 2 nädalat enne ja pärast, samad lävendid)")
ax.set_title("Lühikese koolivaheaja mõju tipuaja pikkusele ristmike kaupa")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06 if len(pj) > 30 else -0.13), ncol=1, fontsize=8)
save(fig, "06_2_04_koolivaheajad_ristmikud")

# --- 3) Hajutamine: osa tipuaja sõidukitest nihkub ----------------------------------------------------------------------
sc = []
profiles = {**{mp: prof.loc[mp].to_numpy() for mp in prof.index}, 0: city}
for mp, v in profiles.items():
    for tp in STS_AKNAD:
        lv = LV[mp][tp]
        s0 = S[mp] if mp else None
        t0 = tipuaeg(v, tp, lv, s0)
        lo, hi = (h * PH for h in TIPUAJA_ALA[tp])
        stsen = [(mode, sh, p) for mode in MODES for sh in SHIFTS for p in SHARES]
        V1 = np.array([shift_peak(v, t0["a"], p, sh // 15, mode, pikkus=t0["b"] - t0["a"]) for mode, sh, p in stsen])
        S1 = kiirus(mp, V1) if mp else [None] * len(V1)
        for (mode, sh, p), v1, s1 in zip(stsen, V1, S1):
            m1 = tipuaeg(v1, tp, lv, s1)["minuteid"]
            sc.append({"mp_id": mp, "tipp": tp, "suund": mode, "nihe_min": sh, "nihutatud_%": round(p * 100),
                       "tipuaeg_enne_min": t0["minuteid"], "tipuaeg_parast_min": m1,
                       "tipuaja_luhenemine_min": t0["minuteid"] - m1,
                       "tipp15_vahenemine_%": (1 - v1[lo:hi].max() / v[lo:hi].max()) * 100})
sc = pd.DataFrame(sc)
assert (sc.loc[sc["nihutatud_%"] == 0, "tipuaja_luhenemine_min"] == 0).all()
save_table(sc, "06_2_hajutamine_stsenaariumid")
key = sc[(sc["nihutatud_%"] == 20) & sc.suund.isin(["mõlemad", "ühtlane"])].pivot_table(
    index="mp_id", columns=["tipp", "suund", "nihe_min"], values="tipuaja_luhenemine_min")
key.columns = [f"{a}_20%_{b}_{c}min_luhenemine_min" for a, b, c in key.columns]
summary = P.loc[P.index >= 0, ["code", "nimi", "hommik_algus", "hommik_lopp", "hommik_kestus_min", "hommik_minuteid",
                               "ohtu_algus", "ohtu_lopp", "ohtu_kestus_min", "ohtu_minuteid"]].join(key)
save_table(summary.reset_index(), "06_2_hajutamine_ristmikud")

MODE_TITLE = {"mõlemad": "pool nihkub täpselt Δ võrra varem, pool hiljem",
              "ühtlane": "nihkuvad jaotuvad ühtlaselt vahemikku ±Δ"}
fig, axes = plt.subplots(2, 2, figsize=(13, 8.6), sharey=True, sharex=True)
for i, mode in enumerate(["ühtlane", "mõlemad"]):
    for k, tp in enumerate(STS_AKNAD):
        ax = axes[i, k]
        sub = sc[(sc.tipp == tp) & (sc.suund == mode) & (sc.mp_id > 0)]
        for sh, col in zip(SHIFTS, [C_AQUA, C_BLUE, C_ORANGE]):
            g = sub[sub.nihe_min == sh].groupby("nihutatud_%")["tipuaja_luhenemine_min"]
            ax.fill_between(g.median().index, g.quantile(0.25), g.quantile(0.75), color=col, alpha=0.15, lw=0)
            ax.plot(g.median().index, g.median(), color=col, marker="o", ms=4, label=f"Δ = {sh} min")
        pot = P.loc[P.index > 0, f"{tp}_minuteid"].median()
        ax.axhline(pot, color=TEXT2, ls="--", lw=1)
        ax.text(40, pot + 1.5, f"tipuaeg kaob täielikult (praegu mediaan {pot:.0f} min)", fontsize=8, color=TEXT2,
                ha="right")
        ax.axhline(0, color=TEXT2, lw=0.6)
        ax.set_title(f"{TIPP_TXT[tp]}: {MODE_TITLE[mode]}", fontsize=10)
        if i == 1:
            ax.set_xlabel("Tipuajast nihkuvate sõidukite osakaal, %")
    axes[i, 0].set_ylabel("Tipuaja lühenemine, min\n(miinus = pikeneb)")
fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="lower center", ncol=3, fontsize=9.5)
fig.suptitle("Hajutamise mõju tipuaja pikkusele: tipuaja tasemel minutid enne - pärast (ristmike mediaan, vöönd = "
             "kvartiilid)", x=0.01, ha="left", fontweight="bold")
fig.tight_layout(rect=(0, 0.04, 1, 1))
save(fig, "06_2_05_hajutamine")

# näide: suurima hommikuse tipptunniga ristmik (nagu 06)
top = max(prof.index, key=lambda m: peak_hour(prof.loc[m].to_numpy(), AM_WINDOW, PH)[1])
v, lv = prof.loc[top].to_numpy(), LV[top]["hommik"]
t0 = tipuaeg(v, "hommik", lv, S[top])
q_eff = P.at[top, "hommik_lavi_kokku_soid_15min"]
fig, ax = plt.subplots(figsize=(9, 4.5))
xs = slice(5 * PH, 11 * PH)
ax.plot(X[xs], v[xs], color=TEXT2, lw=2.2, label=f"Praegu: tipuaeg {t0['minuteid']} min")
for sh, col in [(30, C_BLUE), (60, C_ORANGE)]:
    new = shift_peak(v, t0["a"], 0.2, sh // 15, "ühtlane", pikkus=t0["b"] - t0["a"])
    m1 = tipuaeg(new, "hommik", lv, kiirus(top, new[None])[0])["minuteid"]
    ax.plot(X[xs], new[xs], color=col, lw=1.8,
            label=f"20% tipuaja sõitudest jaotub ±{sh} min: {m1} min tipuaja tasemel ({m1 - t0['minuteid']:+d} min)")
ax.axvspan(t0["a"] / PH, t0["b"] / PH, color=C_GRAY, alpha=0.12, lw=0)
ax.axhline(q_eff, color=TEXT2, ls=":", lw=1)
ax.text(5.05, q_eff, f"tipuaja lävi {q_eff:,.0f} sõid/15 min".replace(",", " "), va="bottom", fontsize=8, color=TEXT2)
ax.set_xlabel("Kellaaeg")
ax.set_ylabel("Sõidukeid 15 min kohta")
ax.set_ylim(0, v[xs].max() * 1.12)
ax.set_title(f"Hajutamise näide: {j.at[top, 'code']} {j.at[top, 'name']} (hommik, tüüpiline tööpäev)")
ax.legend(loc="lower right", fontsize=8.5)
save(fig, "06_2_06_hajutamine_naide")

print("\nTipuajad (tüüpiline tööpäev; kestus = tipuaja pikkus, voog = ainult voo tingimusega):")
print(pm[pm.mp_id >= 0][["code", "nimi", "hommik_algus", "hommik_lopp", "hommik_kestus_min", "hommik_kestus_voog_min",
                         "ohtu_algus", "ohtu_lopp", "ohtu_kestus_min", "ohtu_kestus_voog_min"]].to_string(index=False))
for tp in STS_AKNAD:
    z = pm.loc[pm.mp_id > 0, f"{tp}_kestus_min"]
    print(f"{tp}: kestus mediaan {z.median():.0f} min (kvartiilid {z.quantile(0.25):.0f}-{z.quantile(0.75):.0f}, "
          f"{z.min():.0f}-{z.max():.0f}); 60 min tipptunnist lühem {int((z < 60).sum())}, pikem {int((z > 60).sum())} "
          f"ristmikul; kiiruse tingimus kehtib {int(pm.loc[pm.mp_id > 0, f'{tp}_kiirus_tingimus'].sum())} ristmikul")
print("\nHajutamine, 20% tipuaja sõitudest: tipuaja lühenemine, min (ristmike mediaan):")
print(sc[(sc["nihutatud_%"] == 20) & (sc.mp_id > 0)]
      .groupby(["tipp", "suund", "nihe_min"])["tipuaja_luhenemine_min"].median().unstack().round(1))
