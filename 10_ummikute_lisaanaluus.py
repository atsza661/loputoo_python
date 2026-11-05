"""
10 - Lisaanalüüsid fooritsüklitest ja ummikutest: vaba ruum ummiku ümber, küllastus, päevade võrdlus, vool ja kiirus,
järjekorra tühjenemine, pikad sõidukid, hooga läbijad ja linna koonddiagramm.

SISEND
  valjund/09_tsuklid.csv, 09_ummikud.csv, 09_ummiku_umber.csv, 09_manoovrid.csv   skripti 09 väljund (09 käib enne)
  common.load_vehicles(None, koik=True), load_manoeuvres()   sõidukipõhised kirjed: aeg, kiirus, pikkus, loenduril oldud
                                                             aeg (occ), ajavahe (gap), loenduri järjekorranumber (life)
  common.load_junctions(), add_basemap()                     ristmike koordinaadid ja kaardi taust
  Kõik tööpäevade kohta, kell 05-21; ummikutest ainult stabiilsed (vt 09).

ANALÜÜSID: ARVUTUS JA VÄLJUND (kaust valjund/)
  1) Vaba ruum ummiku ümber (fooriga manöövrid). Iga 15 min akna kohta enne ummiku algust ja pärast lahenemist: vaba
     ruum = täistase x (1 - täituvus) / 4 sõidukit, kus täituvus = akna keskmine läbilase / täistase - nii palju
     sõidukeid mahuks veel aknasse, enne kui tsüklid täis saavad. Võrdluseks ummiku ajal 15 min jooksul läbiv sõidukite
     arv (täistase / 4): nii palju sõite peaks nihkuma, et ummik 15 min lüheneks. Manöövri väärtus = päevade mediaan.
     10_01_vaba_ruum.png   soojuskaart; rida = manööver ja tipp (22 pikimat ummikut; sildis ummiku kestus ja sõidukeid
                        15 min jooksul ummiku ajal), veerg = aken (45-60 ... 0-15 min enne | 0-15 ... 45-60 min pärast;
                        must joon = ummik). Ruudus vaba ruum sõidukites; värv = vaba ruum % ummikuaegsest läbilaskest.
     10_vaba_ruum.csv
  2) Küllastus. Iga ristmiku iga veerandtunni kohta: täis tsüklites (vabal voolul ummikukiirusel) liikunud sõidukite
     osakaal ristmiku kõigist sõidukitest, %.
     10_02_kullastus.png         soojuskaart; rida = ristmik (järjestatud keskmise küllastuse järgi), veerg = veerandtund
                              06-20; värv = osakaal 0-100% (tumedam oranž = rohkem liiklust täis tsüklites).
     10_03_kullastus_kaart.png   kaks kaarti ortofototaustal (hommik, õhtu). Värviline ring = ristmik, selle pikim
                              stabiilne ummik: värv = ummiku algus (hilisem = tumedam), suurus = kestus (tööpäevade
                              mediaan). Väike valge ring = stabiilset ummikut pole.
     10_kullastus.csv
  3) Päevade võrdlus. Manöövri ummiku alguse ja lahenemise vähim, mediaan, suurim ja standardhälve (min) üle tööpäevade.
     10_04_paevade_vordlus.png   (vajab >= 2 tööpäeva) rida = manööver ja tipp, x-telg = kellaaeg. Sinine punkt = ummiku
                              algus igal päeval, oranž punkt = lahenemine, hall riba = mediaanalgusest
                              mediaanlahenemiseni.
     10_paevade_vordlus.csv
  4) Vool ja kiirus vaba vooluga radadel (5 min aknad): vool = sõidukeid x 12 (sõidukit tunnis), kiirus = sõidukite
     keskmine. Läbilaskevõime = voolu 99. protsentiil; kiirus läbilaskevõimel = mediaankiirus, kui vool on >= 95% sellest.
     10_05_vool_kiirus.png   hajuvusdiagrammid kuni 9 suurima manöövri kohta; punkt = 5 min, x = vool, y = kiirus, värv =
                          kellaaeg. Püstine katkendjoon = läbilaskevõime, oranž katkendjoon = 70% vabast kiirusest.
     10_vool_kiirus.csv
  5) Järjekorra tühjenemine (kindla tsükliga manöövrite täis tsüklid, raja kaupa). Vahe esiotsast esiotsani = eelmise
     sõiduki loenduril oldud aeg (occ) + ajavahe (gap), mõlemad loenduri enda mõõdetud, järjestus loenduri
     järjekorranumbri (life) järgi - sündmuse aeg (ts) on ainult kontrolleri küsitluse aeg ega sobi vahede mõõtmiseks.
     Sõiduk on järjekorras seni, kuni ajavahe eelmisega on <= 4 s. Küllastusvahe = järjekorra 5. ja tagumiste sõidukite
     vahede mediaan; küllastusvoog rajal = 3600 / küllastusvahe; stardikadu = 2.-4. sõiduki vahede ja küllastusvahe
     erinevuste summa.
     10_06_kullastusvoog.png   vasakul vahe eelmise sõidukiga järjekorra koha (2-12) järgi: sinine joon = manöövrite
                            mediaan, vöönd = kvartiilid, oranž katkendjoon = küllastusvahe. Paremal rõhtsad tulbad =
                            küllastusvoog raja kohta 25 kõige sagedamini täis manöövril; katkendjoon = kõigi mediaan.
     10_kullastusvoog.csv
  6) Pikad sõidukid (>= 7,5 m). Osakaal 30 min kaupa (kõik, linna sisse LSS, linnast välja LVS). Mõju täis tsüklile
     vahedest: pika sõiduki kulutatud aeg = tema vahe eelmisega + järgmise sõiduauto vahe temaga, võrreldes auto-auto
     vahega; sõiduauto ekvivalent = (vahe pikal + vahe autol pika järel) / vahe autol auto järel - 1. (Tsüklite
     loenduse võrdlus eksitaks: tihedamas tsüklis on juhuslikult ka rohkem pikki.)
     10_07_pikad_soidukid.png   vasakul joondiagramm: pikkade osakaal, % kellaaja järgi (tume = kõik, sinine = LSS, oranž =
                             LVS). Paremal tulbad: vahe mediaan täis tsüklis - sõiduauto auto järel, pikk sõiduk auto
                             järel, sõiduauto pika järel; pealkirjas, mitme sõiduauto aja üks pikk sõiduk kulutab.
     10_pikad_soidukid.csv, 10_pikad_moju.csv
  7) Hooga läbijad: sõidukite osakaal, kes läbivad loenduri vähemalt 80% manöövri vabast kiirusest (kiiruste 85.
     protsentiil) ehk ei alusta paigalt - näitab, kui hästi saabutakse rohelise ajal. Kindla tsükliga manöövrid.
     10_08_hooga.png   soojuskaart; rida = ristmik, veerg = pooltund 06-20; värv = hooga läbijate osakaal, % (0-80).
     10_hooga.csv   sama manöövri ja tunni kaupa
  8) Linna koonddiagramm (kogu linn ühe punktina, 5 min aknad, kell 6-20).
     a) Klassikaline vool vs tihedus: vool = sõidukit tunnis raja kohta, tihedus = summa(1 / kiirus) ajaühikus raja
        kohta (sõidukit km kohta). Loendurid on stoppjoonel ja järjekorda ei näe, seega murdepunkti ei teki.
     b) Linna läbilase (kõik manöövrid kokku, % 99. protsentiilist) vs täis tsüklites liikuvate sõidukite osakaal.
        Murdepunkt = läbilaske tase, millest alates küllastus kasvama hakkab (murtud joone sobitus vähimruutudega:
        tasane kuni murdepunktini, sealt lineaarne), ja mitu tundi tööpäevas ollakse sellest üle.
     10_09_linna_koonddiagramm.png   kaks hajuvusdiagrammi; punkt = 5 min ühel tööpäeval, värv = kellaaeg. Vasakul x =
                                  tihedus, y = vool, katkendjoon = võrdeline seos. Paremal x = linna läbilase, %
                                  suurimast, y = täis tsüklite osakaal, %; oranž murdjoon = sobitus, püstine
                                  katkendjoon = murdepunkt.
     10_linna_koonddiagramm.csv
  ponytail: rohelise algust ei tea, seega stardikadu on ilma esimese sõiduki reageerimisajata ja "hooga" on suhteline
  (manöövri enda kiirete sõidukite suhtes); täpsemaks on vaja foorikavasid.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

from common import (load_vehicles, load_junctions, add_basemap, to_merc, save, save_table, set_style, short_name,
                    slot_label, OUT_DIR, load_manoeuvres, C_BLUE, C_ORANGE, C_AQUA, C_GRAY, TEXT2)

PIKK_M = 7.5          # pikk sõiduk (veok, buss), m
HOOGA = 0.8           # hooga läbija: kiirus >= 80% manöövri kiiruste 85. protsentiilist
JARJEKORD_GAP = 4.0   # järjekorras on sõiduk seni, kuni ajavahe eelmisega on <= 4 s
KELL = (5, 21)
MIN_VAATLUSI = 30     # väikseim tsüklite / sõidukite arv, millest näitajat arvutatakse
KEY = ["mp", "direction_id"]
NIHKED = [-60, -45, -30, -15, 15, 30, 45, 60]
NIHE_SILT = [f"{abs(x) - 15}–{abs(x)}\n{'enne' if x < 0 else 'pärast'}" for x in NIHKED]
LIIGID = ["sõiduauto auto järel", "pikk sõiduk", "sõiduauto pika järel"]
HALO = [pe.withStroke(linewidth=2.2, foreground="white")]
hhmm = lambda h: slot_label(h * 60, 60)
ramp = lambda name: LinearSegmentedColormap.from_list(name + "_t", plt.get_cmap(name)(np.linspace(0.3, 1, 256)))


def tsukli_indeks(st, T, t):
    """Iga aja t tsükli järjekorranumber (algused st, pikkused T) või -1, kui t ei jää ühtegi tsüklisse."""
    k = np.clip(np.searchsorted(st, t, side="right") - 1, 0, None)
    return np.where((t >= st[k]) & (t < st[k] + T[k]), k, -1)


def murdepunkt(x, y):
    """Murtud joon y = a (x <= x0), a + b (x - x0) (x > x0): väikseima ruutveaga (x0, a, b)."""
    parim = None
    for x0 in np.arange(np.percentile(x, 10), np.percentile(x, 95), 0.5):
        z = np.clip(x - x0, 0, None)
        b, a = np.polyfit(z, y, 1)
        viga = ((a + b * z - y) ** 2).sum()
        if parim is None or viga < parim[0]:
            parim = (viga, x0, a, b)
    return parim[1:]


assert tsukli_indeks(np.array([0., 90]), np.array([90., 90]), np.array([5, 89.9, 90, 200])).tolist() == [0, 0, 1, -1]
assert abs(murdepunkt(np.arange(100.), np.clip(np.arange(100.) - 70, 0, None) * 2)[0] - 70) < 1

set_style()
loe = lambda nimi, **kw: pd.read_csv(OUT_DIR / f"{nimi}.csv", encoding="utf-8-sig", **kw)
c = loe("09_tsuklid", parse_dates=["algus"])
c["paev"] = c["algus"].dt.normalize()
c = c[c["paev"].dt.dayofweek < 5].sort_values(KEY + ["paev", "t"]).reset_index(drop=True)
um = loe("09_ummikud", parse_dates=["paev"])
um = um[um["stabiilne"] & (um["tyyp"] == "tööpäev")]
ub = loe("09_ummiku_umber", parse_dates=["paev"])
ub = ub[ub["stabiilne"] & (ub["tyyp"] == "tööpäev")]
man = loe("09_manoovrid")
man["silt"] = man["mp"] + " " + man["manoeuvre"].map(lambda s: short_name(s, 38))
silt = man.set_index(KEY)["silt"]
jn = load_junctions()
rsilt = (jn["code"] + " " + jn["name"].map(lambda s: short_name(s, 34, compact=True))).set_axis(jn["code"])
PAEVI = c["paev"].nunique()
print(f"Tööpäevi: {PAEVI}, tsükleid {len(c):,}, stabiilseid ummikuid {len(um)}")

# --- 1) Vaba ruum ummiku ümber -------------------------------------------------------------------------
x = ub[ub["meetod"] != "vaba"].merge(um[KEY + ["paev", "tipp", "taistase_soid_h", "kestus_min"]], on=KEY + ["paev", "tipp"])
x["ruum_15min"] = (x["taistase_soid_h"] * (1 - x["taituvus"] / 100) / 4).clip(lower=0)
x["ummikus_15min"] = x["taistase_soid_h"] / 4
ruum = (x.groupby(KEY + ["manoeuvre", "tipp", "nihe_min"])
        .agg(paevi=("paev", "nunique"), kestus_min=("kestus_min", "median"), ummikus_15min=("ummikus_15min", "median"),
             taituvus=("taituvus", "median"), ruum_15min=("ruum_15min", "median")).reset_index())
ruum["ruum_%"] = ruum["ruum_15min"] / ruum["ummikus_15min"] * 100
save_table(ruum.round(1), "10_vaba_ruum")
kokku = ruum.groupby("nihe_min")[["ruum_15min", "ruum_%"]].median().reindex(NIHKED)
print("\n1) Vaba ruum 15 min aknas (mediaan üle manöövrite): sõidukit / % ummikuaegsest läbilaskest")
print("   " + "; ".join(f"{n:+d} min: {r.ruum_15min:.0f} / {r['ruum_%']:.0f}%" for n, r in kokku.iterrows()))
RK = KEY + ["manoeuvre", "tipp"]
P = ruum.pivot(index=RK, columns="nihe_min", values="ruum_15min").reindex(columns=NIHKED)
Pp = ruum.pivot(index=RK, columns="nihe_min", values="ruum_%").reindex(columns=NIHKED)
info = ruum.drop_duplicates(RK).set_index(RK)
top = info["kestus_min"].nlargest(22).index
fig, ax = plt.subplots(figsize=(12, 0.42 * len(top) + 2.2))
sns.heatmap(Pp.loc[top], annot=P.loc[top], fmt=".0f", cmap=sns.light_palette(C_AQUA, as_cmap=True), vmin=0, vmax=60,
            annot_kws=dict(fontsize=8), cbar_kws=dict(label="Vaba ruum, % ummiku ajal läbivast sõidukite arvust", shrink=0.7),
            linewidths=0.5, linecolor="white", ax=ax)
ax.set_yticklabels([f"{k[0]} {short_name(k[2], 34)} ({k[3]}; {info.at[k, 'kestus_min']:.0f} min; "
                    f"{info.at[k, 'ummikus_15min']:.0f})" for k in top], fontsize=8, rotation=0)
ax.set_xticklabels(NIHE_SILT, rotation=0, fontsize=8)
ax.set_xlabel("min ummiku algusest / lahenemisest")
ax.set_ylabel("")
ax.axvline(4, color="black", lw=1.5)
ax.set_title("Vaba ruum ummiku ümber: mitu sõidukit mahuks veel 15 min aknasse, enne kui tsüklid täis saavad\n"
             "(rea järel: tipp; ummiku kestus; sõidukeid 15 min jooksul ummiku ajal)", fontsize=10)
save(fig, "10_01_vaba_ruum")

# --- 2) Küllastus: soojuskaart ja kaart ----------------------------------------------------------------
c["veerand"] = (c["t"] // 900).astype(int)
k = c.assign(tn=c["n"] * c["ummikus"]).groupby(["mp", "veerand"])[["tn", "n"]].sum()
K = (k["tn"] / k["n"] * 100).unstack("veerand").reindex(columns=range(24, 80)).fillna(0)       # 06:00-20:00
K = K.loc[K.mean(axis=1).sort_values(ascending=False).index]
save_table(K.rename(columns=lambda q: hhmm(q / 4)).rename_axis(columns=None).reset_index().round(1), "10_kullastus")
print(f"\n2) Küllastus: kõige rohkem liiklust täis tsüklites kell {hhmm(K.mean().idxmax() / 4)} "
      f"(ristmike keskmine {K.mean().max():.0f}%); ristmikke, kus mõnel veerandtunnil üle 50%: {(K.max(axis=1) > 50).sum()}")
fig, ax = plt.subplots(figsize=(12, 0.27 * len(K) + 1.8))
sns.heatmap(K, cmap=sns.light_palette(C_ORANGE, as_cmap=True), vmin=0, vmax=100, ax=ax, yticklabels=False,
            cbar_kws=dict(label="% ristmiku sõidukitest täis tsüklites / ummikukiirusel", shrink=0.6))
ax.set_yticks(np.arange(len(K)) + 0.5)
ax.set_yticklabels([rsilt.get(m, m) for m in K.index], fontsize=7, rotation=0)
ax.set_xticks(np.arange(0, 57, 4))
ax.set_xticklabels([f"{h:02d}" for h in range(6, 21)], rotation=0)
ax.set_xlabel("Kellaaeg")
ax.set_ylabel("")
ax.set_title(f"Küllastus ristmiku ja kellaaja kaupa ({PAEVI} tööpäeva keskmine): kui suur osa liiklusest liigub täis tsüklites")
save(fig, "10_02_kullastus")

u2 = um.groupby(KEY + ["tipp"]).agg(algus_h=("algus_h", "median"), kestus_min=("kestus_min", "median")).reset_index()
jk = jn.dropna(subset=["lat"])
lon0, lon1, lat0, lat1 = jk["lon"].min(), jk["lon"].max(), jk["lat"].min(), jk["lat"].max()
dx, dy = (lon1 - lon0) * 0.06, (lat1 - lat0) * 0.06
lon0, lon1, lat0, lat1 = lon0 - dx, lon1 + dx, lat0 - 2 * dy, lat1 + dy
(mx0, my0), (mx1, my1) = to_merc(lon0, lat0), to_merc(lon1, lat1)
fig, axes = plt.subplots(1, 2, figsize=(15, 6.3 * (my1 - my0) / (mx1 - mx0) + 1.1), layout="constrained")
for ax, (tipp, cmap) in zip(axes, [("hommik", "Blues"), ("õhtu", "Oranges")]):
    s = u2[u2["tipp"].str.contains(tipp)]
    d = jk.merge(s.loc[s.groupby("mp")["kestus_min"].idxmax()], left_on="code", right_on="mp", how="left")
    add_basemap(ax, lon0, lat0, lon1, lat1)
    px, py = to_merc(d["lon"].values, d["lat"].values)
    on = d["kestus_min"].notna().values
    ax.scatter(px[~on], py[~on], s=16, c="white", edgecolor="black", linewidth=0.6, zorder=4)
    if on.any():
        vmin, vmax = np.floor(d["algus_h"].min() * 2) / 2, np.ceil(d["algus_h"].max() * 2) / 2
        sc = ax.scatter(px[on], py[on], c=d["algus_h"][on], s=25 + d["kestus_min"][on] * 3, cmap=ramp(cmap),
                        vmin=vmin, vmax=vmax, edgecolor="black", linewidth=0.7, zorder=5)
        for xx, yy, code in zip(px[on], py[on], d["code"][on]):
            ax.annotate(code, (xx, yy), xytext=(5, 4), textcoords="offset points", fontsize=6.5, zorder=6,
                        path_effects=HALO)
        cb = fig.colorbar(sc, ax=ax, shrink=0.75)
        ticks = np.arange(vmin, vmax + 0.01, 0.5 if vmax - vmin <= 3 else 1)
        cb.set_ticks(ticks)
        cb.set_ticklabels([hhmm(q) for q in ticks])
        cb.set_label("Ummiku algus (hilisem = tumedam)")
    for m in (15, 60, 120):
        ax.scatter([], [], s=25 + m * 3, c="white", edgecolor="black", linewidth=0.7, label=f"{m} min")
    ax.scatter([], [], s=16, c="white", edgecolor="black", linewidth=0.6, label="stabiilset ummikut pole")
    ax.legend(loc="upper left", fontsize=8, title="Ummiku kestus", title_fontsize=8, frameon=True, framealpha=0.85,
              labelspacing=1.1, borderpad=0.9)
    ax.set_title(f"{tipp.capitalize()}: {int(on.sum())} ristmikul stabiilne ummik", fontsize=11)
fig.suptitle("Iga ristmiku pikim ummik: värv = algus, suurus = kestus (tööpäevade mediaan)", x=0.01, ha="left",
             fontweight="bold")
save(fig, "10_03_kullastus_kaart")

# --- 3) Päevade võrdlus: ummiku alguse ja lahenemise kõikumine --------------------------------------------
p = (um.groupby(KEY + ["manoeuvre", "meetod", "tipp"])
     .agg(paevi=("paev", "nunique"), algus_min=("algus_h", "min"), algus_med=("algus_h", "median"),
          algus_max=("algus_h", "max"), lahenes_min=("lahenes_h", "min"), lahenes_med=("lahenes_h", "median"),
          lahenes_max=("lahenes_h", "max"), kestus_med=("kestus_min", "median"),
          algus_hajuvus_min=("algus_h", lambda s: s.std() * 60), lahenes_hajuvus_min=("lahenes_h", lambda s: s.std() * 60))
     .reset_index())
p["osa_paevadest_%"] = p["paevi"] / PAEVI * 100
save_table(p.assign(**{f"{a}_{b}": p[f"{a}_{b}"].map(hhmm) for a in ["algus", "lahenes"] for b in ["min", "med", "max"]})
           .round(1), "10_paevade_vordlus")
pt = p[p["paevi"] >= 2].sort_values(["paevi", "kestus_med"], ascending=False).head(25)
if len(pt):
    print(f"\n3) Päevade võrdlus: {len(p[p['paevi'] >= 2])} manöövril ummik vähemalt 2 päeval; alguse hajuvus (mediaan) "
          f"{p['algus_hajuvus_min'].median():.0f} min, lahenemise {p['lahenes_hajuvus_min'].median():.0f} min")
    fig, ax = plt.subplots(figsize=(11, 0.34 * len(pt) + 1.8))
    for i, r in enumerate(pt.iloc[::-1].itertuples()):
        d = um[(um["mp"] == r.mp) & (um["direction_id"] == r.direction_id) & (um["tipp"] == r.tipp)]
        ax.plot([r.algus_med, r.lahenes_med], [i, i], color=C_GRAY, lw=8, alpha=0.3, solid_capstyle="butt")
        ax.plot(d["algus_h"], [i] * len(d), "o", color=C_BLUE, ms=4.5, label="ummiku algus (iga päev)" if i == 0 else None)
        ax.plot(d["lahenes_h"], [i] * len(d), "o", color=C_ORANGE, ms=4.5, label="lahenemine (iga päev)" if i == 0 else None)
    ax.set_yticks(range(len(pt)))
    ax.set_yticklabels([f"{r.mp} {short_name(r.manoeuvre, 34)} ({r.tipp}, {r.paevi}/{PAEVI} p)"
                        for r in pt.iloc[::-1].itertuples()], fontsize=8)
    ax.set_xlabel("Kellaaeg (hall riba = mediaanalgusest mediaanlahenemiseni)")
    ax.xaxis.set_major_formatter(lambda q, _: hhmm(q))
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=2)
    ax.set_title(f"Kui korrapärane on ummik: algus ja lahenemine tööpäevade kaupa ({PAEVI} päeva)")
    save(fig, "10_04_paevade_vordlus")
else:
    print("\n3) Päevade võrdlus: tabel tehtud; joonis vajab vähemalt 2 tööpäeva sama manöövri ummikuga.")

# --- 4) Vool ja kiirus vaba vooluga radadel ---------------------------------------------------------------
f = c[c["meetod"] == "vaba"].assign(viis=lambda q: (q["t"] // 300).astype(int))
f["kv"], f["nk"] = (f["kiirus"] * f["n"]).fillna(0), f["n"].where(f["kiirus"].notna(), 0)
f5 = f.groupby(KEY + ["paev", "viis"])[["n", "kv", "nk"]].sum().reset_index()
f5["voog"], f5["kiirus"] = f5["n"] * 12, f5["kv"] / f5["nk"].where(f5["nk"] > 0)
f5 = f5.dropna(subset=["kiirus"])
rows = []
for key, g in f5.groupby(KEY):
    cap = g["voog"].quantile(0.99)
    rows.append(dict(mp=key[0], direction_id=key[1], labilaskevoime_soid_h=cap,
                     kiirus_labilaskevoimel=g.loc[g["voog"] >= 0.95 * cap, "kiirus"].median(),
                     vaikseim_kiirus=g["kiirus"].quantile(0.01),
                     voog_vaikseimal_kiirusel=g.loc[g["kiirus"] <= g["kiirus"].quantile(0.02), "voog"].median()))
vk = pd.DataFrame(rows).merge(man[KEY + ["manoeuvre", "soidukeid", "vaba_kiirus"]], on=KEY)
save_table(vk.sort_values("soidukeid", ascending=False).round(1), "10_vool_kiirus")
valik = vk[vk["vaba_kiirus"] >= 45] if (vk["vaba_kiirus"] >= 45).sum() >= 3 else vk
valik = valik.nlargest(9, "soidukeid")
print(f"\n4) Vool ja kiirus: {len(vk)} vaba vooluga manöövrit; suurim läbilaskevõime "
      f"{vk['labilaskevoime_soid_h'].max():.0f} sõid/h ({silt.get(tuple(vk.loc[vk['labilaskevoime_soid_h'].idxmax(), KEY]))})")
ncol = 3
fig, axes = plt.subplots(int(np.ceil(len(valik) / ncol)), ncol, figsize=(13, 3.6 * int(np.ceil(len(valik) / ncol))),
                         squeeze=False, layout="constrained")
for ax, r in zip(axes.flat, valik.itertuples()):
    g = f5[(f5["mp"] == r.mp) & (f5["direction_id"] == r.direction_id)]
    sc = ax.scatter(g["voog"], g["kiirus"], c=g["viis"] / 12, cmap="viridis", vmin=KELL[0], vmax=KELL[1], s=9, alpha=0.8)
    ax.axvline(r.labilaskevoime_soid_h, color=TEXT2, lw=0.8, ls="--")
    ax.axhline(0.7 * r.vaba_kiirus, color=C_ORANGE, lw=0.8, ls="--")
    ax.set_title(f"{r.mp} {short_name(r.manoeuvre, 34)}\nläbilaskevõime ~{r.labilaskevoime_soid_h:.0f} sõid/h, "
                 f"seal kiirus {r.kiirus_labilaskevoimel:.0f} km/h", fontsize=9)
    ax.set_xlim(0, None)
    ax.set_ylim(0, None)
for ax in axes.flat[len(valik):]:
    ax.axis("off")
fig.colorbar(sc, ax=axes, shrink=0.6, label="Kellaaeg", ticks=range(KELL[0], KELL[1] + 1, 2))
fig.supxlabel("Vool, sõidukit tunnis (5 min aken)", color=TEXT2)
fig.supylabel("Kiirus, km/h", color=TEXT2)
fig.suptitle("Vool ja kiirus vaba vooluga radadel (punkt = 5 min; püstjoon = läbilaskevõime, oranž = 70% vabast kiirusest)",
             x=0.01, ha="left", fontweight="bold")
save(fig, "10_05_vool_kiirus")

# --- Sõidukid tsüklitesse (5-7) ---------------------------------------------------------------------------
print("\nLaen sõidukipõhised loendused...")
v = load_vehicles(None, koik=True)
dm = load_manoeuvres()
dm = dm.assign(mp_id=dm["mp"].str[2:].astype(int)).rename(columns={"channel": "kanal"})
v = v.merge(dm[["mp_id", "kanal", "mp", "direction_id"]], on=["mp_id", "kanal"]).dropna(subset=["direction_id"])
v["direction_id"] = v["direction_id"].astype(int)
v["paev"] = v["ts"].dt.normalize()
v["t"] = (v["ts"] - v["paev"]).dt.total_seconds()
v = v[(v["paev"].dt.dayofweek < 5) & (v["t"] >= KELL[0] * 3600) & (v["t"] < KELL[1] * 3600)]
v = v.sort_values(KEY + ["paev", "t"]).reset_index(drop=True)
v["pikk"] = v["pikkus"] >= PIKK_M
v["hooga"] = v["kiirus"] >= HOOGA * v.join(v[v["kiirus"] > 0].groupby(KEY)["kiirus"].quantile(0.85).rename("v85"), on=KEY)["v85"]

# 6a) pikkade sõidukite osakaal päeva jooksul (kõik sõidukid, 30 min)
pool = v["t"] // 1800 / 2
pikad = pd.DataFrame({"kõik": v.groupby(pool)["pikk"].mean(), "LSS (linna sisse)": v[v["LSS"]].groupby(pool)["pikk"].mean(),
                      "LVS (linnast välja)": v[v["LVS"]].groupby(pool)["pikk"].mean()}) * 100
save_table(pikad.rename_axis("kell_h").reset_index().round(2), "10_pikad_soidukid")

ct, cT, ci = c["t"].values, c["T"].values, c.groupby(KEY + ["paev"]).indices
vt, cyc = v["t"].values, np.full(len(v), -1)
for key, iv in v.groupby(KEY + ["paev"]).indices.items():
    ic = ci.get(key)
    if ic is not None:
        kk = tsukli_indeks(ct[ic], cT[ic], vt[iv])
        cyc[iv[kk >= 0]] = ic[kk[kk >= 0]]
v = v.assign(cyc=cyc)[cyc >= 0]
for veerg, kaal in [("hooga", v["hooga"]), ("kiirusega", v["kiirus"] > 0)]:
    c[veerg] = np.bincount(v["cyc"], weights=kaal, minlength=len(c))
tais = (c["ummikus"] & (c["meetod"] == "kindel")).values                # täis tsüklid kindla tsükliga manöövritel

# --- 5) Järjekorra tühjenemine: vahed raja kaupa täis tsüklites ---------------------------------------------
q = v[tais[v["cyc"].values]].sort_values(["mp", "kanal", "life"])       # loenduri õige järjestus
eel = q.groupby(["mp", "kanal"])
jarjest = eel["life"].diff() == 1                                        # eelmine rida on tõesti eelmine sõiduk
q = q.assign(vahe=(eel["occ"].shift() + q["gap"]).where(jarjest), eel_pikk=eel["pikk"].shift().where(jarjest))
q["koht"] = q.groupby(["cyc", "kanal"]).cumcount() + 1
q["katkes"] = ((q["gap"] > JARJEKORD_GAP) & (q["koht"] > 1)).astype(int)
q = q[(q.groupby(["cyc", "kanal"])["katkes"].cumsum() == 0) & q["vahe"].notna() & (q["koht"] > 1)]
H = q[q["koht"] <= 12].groupby(KEY + ["koht"])["vahe"].agg(["median", "size"])
H = H["median"].where(H["size"] >= MIN_VAATLUSI).unstack("koht")
kyll = q[q["koht"] >= 5]
ks = pd.DataFrame({"tais_tsukleid": c[tais].groupby(KEY).size(), "radu": q.groupby(KEY)["kanal"].nunique(),
                   "vaatlusi": kyll.groupby(KEY).size(), "kullastusvahe_s": kyll.groupby(KEY)["vahe"].median()})
ks = ks[ks["vaatlusi"] >= MIN_VAATLUSI]
ks["kullastusvoog_soid_h_rajal"] = 3600 / ks["kullastusvahe_s"]
ks["stardikadu_s"] = H.reindex(ks.index)[[2, 3, 4]].sub(ks["kullastusvahe_s"], axis=0).sum(axis=1, min_count=3)
ks = ks.join(H.add_prefix("vahe_koht_"))
ks.insert(0, "manoeuvre", man.set_index(KEY)["manoeuvre"].reindex(ks.index))
save_table(ks.reset_index().sort_values("tais_tsukleid", ascending=False).round(2), "10_kullastusvoog")
print(f"\n5) Järjekorra tühjenemine ({len(ks)} manöövrit): küllastusvahe mediaan {ks['kullastusvahe_s'].median():.2f} s -> "
      f"{ks['kullastusvoog_soid_h_rajal'].median():.0f} sõid/h rajal; stardikadu mediaan {ks['stardikadu_s'].median():.1f} s")
fig, axes = plt.subplots(1, 2, figsize=(14, 0.3 * min(len(ks), 25) + 2.5), gridspec_kw=dict(width_ratios=[1, 1.25]))
ax = axes[0]
Hk = H.reindex(ks.index)
ax.fill_between(Hk.columns, Hk.quantile(0.25), Hk.quantile(0.75), color=C_BLUE, alpha=0.2, lw=0,
                label="manöövrite kvartiilid")
ax.plot(Hk.columns, Hk.median(), "o-", color=C_BLUE, lw=2.2, label="manöövrite mediaan")
ax.axhline(ks["kullastusvahe_s"].median(), color=C_ORANGE, lw=1, ls="--",
           label=f"küllastusvahe {ks['kullastusvahe_s'].median():.2f} s")
ax.set_ylim(0, None)
ax.set_xticks(Hk.columns)
ax.set_xlabel("Sõiduki koht järjekorras (rajal)")
ax.set_ylabel("Vahe eelmise sõidukiga, s (esiotsast esiotsani)")
ax.set_title("Vahed täis tsüklites järjekorra koha järgi", fontsize=10)
ax.legend(fontsize=8)
ax = axes[1]
kt = ks.nlargest(25, "tais_tsukleid").sort_values("kullastusvoog_soid_h_rajal")
ax.barh(range(len(kt)), kt["kullastusvoog_soid_h_rajal"], color=C_BLUE, alpha=0.85)
ax.axvline(ks["kullastusvoog_soid_h_rajal"].median(), color=C_ORANGE, lw=1, ls="--")
ax.set_yticks(range(len(kt)))
ax.set_yticklabels([silt.get(k, str(k)) for k in kt.index], fontsize=7.5)
ax.set_xlabel("Küllastusvoog, sõidukit tunnis raja kohta (katkendjoon = kõigi mediaan)")
ax.set_title("Küllastusvoog: 25 kõige sagedamini täis manöövrit", fontsize=10)
fig.tight_layout()
save(fig, "10_06_kullastusvoog")

# --- 6) Pikad sõidukid: mõju täis tsükli sõidukite arvule (vahedest) ----------------------------------------
kv = kyll[kyll["eel_pikk"].notna()].copy()
kv["liik"] = np.select([kv["pikk"], kv["eel_pikk"].astype(bool)], [LIIGID[1], LIIGID[2]], LIIGID[0])


def ekvivalent(z):
    """Pika sõiduki sõiduauto ekvivalent täis tsüklis tabelist z (veerud liik, vahe): vahede mediaanid kolme liigi kaupa
    ja (vahe pikal + vahe autol pika järel) / vahe autol auto järel - 1. Tühi, kui mõnes liigis on alla MIN_VAATLUSI."""
    h, n = z.groupby("liik")["vahe"].median().reindex(LIIGID), z["liik"].value_counts().reindex(LIIGID)
    if not (n >= MIN_VAATLUSI).all():
        return pd.Series(dtype=float)
    return pd.Series({"vahe_auto": h[LIIGID[0]], "vahe_pikk": h[LIIGID[1]], "vahe_auto_pika_jarel": h[LIIGID[2]],
                      "pikki": n[LIIGID[1]], "soiduauto_ekvivalent": (h[LIIGID[1]] + h[LIIGID[2]]) / h[LIIGID[0]] - 1})


moju = kv.groupby(KEY).apply(ekvivalent).unstack().dropna()
kogu = ekvivalent(kv)
pce = kogu["soiduauto_ekvivalent"]
moju.insert(0, "manoeuvre", man.set_index(KEY)["manoeuvre"].reindex(moju.index))
save_table(pd.concat([moju.reset_index(), pd.DataFrame([dict(kogu, mp="KÕIK", manoeuvre="kõik manöövrid koos")])]).round(2),
           "10_pikad_moju")
print(f"\n6) Pikad sõidukid: osakaal {v['pikk'].mean() * 100:.1f}% (suurim kell {hhmm(pikad['kõik'].idxmax())}: "
      f"{pikad['kõik'].max():.1f}%); üks pikk sõiduk võtab täis tsüklis {pce:.1f} sõiduauto aja "
      f"(manöövrite kvartiilid {moju['soiduauto_ekvivalent'].quantile(.25):.1f}–{moju['soiduauto_ekvivalent'].quantile(.75):.1f}, "
      f"{len(moju)} manöövrit)")
fig, axes = plt.subplots(1, 2, figsize=(13, 4.4))
for col, cl in zip(pikad, [TEXT2, C_BLUE, C_ORANGE]):
    axes[0].plot(pikad.index + 0.25, pikad[col], color=cl, lw=1.8, label=col)
axes[0].set_xticks(range(KELL[0], KELL[1] + 1, 2))
axes[0].set_xlabel("Kellaaeg")
axes[0].set_ylabel(f"Pikkade sõidukite (>= {PIKK_M:g} m) osakaal, %")
axes[0].set_ylim(0, None)
axes[0].legend(fontsize=8)
axes[0].set_title("Pikkade sõidukite osakaal päeva jooksul", fontsize=10)
vahed = kogu[["vahe_auto", "vahe_pikk", "vahe_auto_pika_jarel"]]
axes[1].bar(["sõiduauto\nauto järel", "pikk sõiduk\nauto järel", "sõiduauto\npika järel"], vahed.values,
            color=[C_GRAY, C_ORANGE, C_BLUE], alpha=0.9)
for i, h in enumerate(vahed.values):
    axes[1].text(i, h + 0.05, f"{h:.2f} s", ha="center", fontsize=9)
axes[1].set_ylabel("Vahe eelmise sõidukiga täis tsüklis, s (mediaan)")
axes[1].set_ylim(0, vahed.max() * 1.18)
axes[1].set_title(f"1 pikk sõiduk kulutab {pce:.1f} sõiduauto aja:\ntäis tsüklisse mahub iga pika kohta "
                  f"{pce - 1:.1f} sõidukit vähem", fontsize=10)
fig.tight_layout()
save(fig, "10_07_pikad_soidukid")

# --- 7) Hooga läbijad (rohelisel saabumine) -------------------------------------------------------------------
s7 = c[c["meetod"] == "kindel"].assign(pool=lambda z: (z["t"] // 1800).astype(int), tund=lambda z: (z["t"] // 3600).astype(int))
hm = s7.groupby(KEY + ["tund"])[["hooga", "kiirusega"]].sum()
hm["osakaal_%"] = hm["hooga"] / hm["kiirusega"].where(hm["kiirusega"] >= MIN_VAATLUSI) * 100
save_table(hm.reset_index().merge(man[KEY + ["manoeuvre"]], on=KEY)[KEY + ["manoeuvre", "tund", "kiirusega", "osakaal_%"]]
           .rename(columns={"kiirusega": "soidukeid"}).round(1), "10_hooga")
hj = s7.groupby(["mp", "pool"])[["hooga", "kiirusega"]].sum()
Hj = (hj["hooga"] / hj["kiirusega"].where(hj["kiirusega"] >= MIN_VAATLUSI) * 100).unstack("pool").reindex(columns=range(12, 40))
Hj = Hj.loc[Hj.mean(axis=1).sort_values(ascending=False).index]
linn = s7.groupby("pool")[["hooga", "kiirusega"]].sum()
linn = (linn["hooga"] / linn["kiirusega"] * 100).reindex(range(12, 40))
print(f"\n7) Hooga läbijaid kokku {s7['hooga'].sum() / s7['kiirusega'].sum() * 100:.0f}%; madalaim kell "
      f"{hhmm(linn.idxmin() / 2)} ({linn.min():.0f}%), kõrgeim kell {hhmm(linn.idxmax() / 2)} ({linn.max():.0f}%)")
fig, ax = plt.subplots(figsize=(12, 0.27 * len(Hj) + 1.8))
sns.heatmap(Hj, cmap=sns.light_palette(C_AQUA, as_cmap=True), vmin=0, vmax=80, ax=ax, yticklabels=False,
            cbar_kws=dict(label="% sõidukitest läbib hooga (>= 80% manöövri vabast kiirusest)", shrink=0.6))
ax.set_yticks(np.arange(len(Hj)) + 0.5)
ax.set_yticklabels([rsilt.get(m, m) for m in Hj.index], fontsize=7, rotation=0)
ax.set_xticks(np.arange(0, 29, 2))
ax.set_xticklabels([f"{h:02d}" for h in range(6, 21)], rotation=0)
ax.set_xlabel("Kellaaeg")
ax.set_ylabel("")
ax.set_title("Rohelisel saabumine: hooga läbijate osakaal ristmiku ja kellaaja kaupa (kindla tsükliga manöövrid, tööpäevad)")
save(fig, "10_08_hooga")

# --- 8) Linna koonddiagramm: kas kogu linnal on murdepunkt? --------------------------------------------------
v8 = v[v["kiirus"] > 0]
radu = v8.groupby(["mp", "kanal"]).ngroups
kd = (v8.assign(viis=(v8["t"] // 300).astype(int), inv=1 / v8["kiirus"]).groupby(["paev", "viis"])["inv"]
      .agg(voog="size", tihedus="sum") * 12 / radu)                      # sõid/h ja sõid/km raja kohta
k8 = c.assign(viis=(c["t"] // 300).astype(int), tn=c["n"] * c["ummikus"]).groupby(["paev", "viis"])[["n", "tn"]].sum()
kd = kd.join(pd.DataFrame({"labilase_soid_h": k8["n"] * 12, "tais_%": k8["tn"] / k8["n"] * 100})).dropna().reset_index()
kd = kd[kd["viis"].between(72, 239)]                                     # 06:00-20:00 (servades on tsükleid vähe)
kd["labilase_%"] = kd["labilase_soid_h"] / kd["labilase_soid_h"].quantile(0.99) * 100
kd["kiirus"] = kd["voog"] / kd["tihedus"]
x0, a0, b0 = murdepunkt(kd["labilase_%"].values, kd["tais_%"].values)
ule = (kd["labilase_%"] > x0).groupby(kd["paev"]).sum() * 5 / 60
r_vk = np.corrcoef(kd["voog"], kd["tihedus"])[0, 1]
save_table(kd.assign(kell=kd["viis"].map(lambda q: hhmm(q / 12)), paev=kd["paev"].dt.date).drop(columns="viis").round(2),
           "10_linna_koonddiagramm")
print(f"\n8) Linna koonddiagramm: vool ja tihedus on lõpuni võrdelised (r = {r_vk:.3f}, kiirus {kd['kiirus'].quantile(.05):.0f}–"
      f"{kd['kiirus'].quantile(.95):.0f} km/h) - klassikalist murdepunkti loendurid ei näe. Täis tsüklite osakaal hakkab "
      f"kasvama, kui linna läbilase ületab {x0:.0f}% suurimast (iga +1% lisab {b0:.1f} protsendipunkti); üle selle "
      f"ollakse {ule.mean():.1f} h tööpäevas")
fig, axes = plt.subplots(1, 2, figsize=(14, 5.8), layout="constrained")
sc = axes[0].scatter(kd["tihedus"], kd["voog"], c=kd["viis"] / 12, cmap="viridis", vmin=6, vmax=20, s=12, alpha=0.8)
axes[0].plot([0, kd["tihedus"].max()], [0, kd["tihedus"].max() * kd["voog"].sum() / kd["tihedus"].sum()], color=TEXT2,
             lw=0.8, ls="--")
axes[0].set_xlim(0, None)
axes[0].set_ylim(0, None)
axes[0].set_xlabel("Tihedus, sõidukit km kohta rajal (punktkiirustest)")
axes[0].set_ylabel("Vool, sõidukit tunnis rajal")
axes[0].set_title(f"Klassikaline diagramm: vool kasvab tihedusega lõpuni\n(r = {r_vk:.2f}; loendurid on stoppjoonel ja "
                  "järjekorda ei näe)", fontsize=10)
axes[1].scatter(kd["labilase_%"], kd["tais_%"], c=kd["viis"] / 12, cmap="viridis", vmin=6, vmax=20, s=12, alpha=0.8)
xx = np.array([kd["labilase_%"].min(), x0, kd["labilase_%"].max()])
axes[1].plot(xx, a0 + b0 * np.clip(xx - x0, 0, None), color=C_ORANGE, lw=2)
axes[1].axvline(x0, color=C_ORANGE, lw=0.8, ls="--")
axes[1].set_ylim(0, None)
axes[1].set_xlabel("Linna läbilase, % suurimast (kõik manöövrid kokku)")
axes[1].set_ylabel("Täis tsüklites liikuvate sõidukite osakaal, %")
axes[1].set_title(f"Küllastuse murdepunkt: {x0:.0f}% suurimast läbilaskest ({ule.mean():.1f} h tööpäevas üle selle)\n"
                  f"sealt edasi lisab iga +1% liiklust {b0:.1f} protsendipunkti täis tsükleid", fontsize=10)
fig.colorbar(sc, ax=axes, shrink=0.8, label="Kellaaeg")
fig.suptitle(f"Kogu linn ühe punktina (5 min, {PAEVI} tööpäeva, kell 6–20)", x=0.01, ha="left", fontweight="bold")
save(fig, "10_09_linna_koonddiagramm")
print("Valmis.")
