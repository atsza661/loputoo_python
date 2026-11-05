"""
05 - Kütusekulu hinnang loenduri andmetest (sõidukiklass x kiirus) ja tipptundide lisakulu.

SISEND
  common.load_hourly_profile()           maanteeloendurite tunniprofiil: iga loenduri, kanali, kuu, päevatüübi (tööpäev
                                         E-R või mitte) ja kellatunni kohta tunniridade arv (n_hours) ning sõidukite
                                         summad 10 klassi ja 11 kiirusvahemiku kaupa
  common.load_daily(), counter_month()   kehtivad loendur-kuud (kahtlase mahu või klassijaotusega kuud jäävad välja)
  common.load_locations()                loenduri nimi, maakond, tee
  common.load_fuel_national()            kütuse jaemüük, liitrit päevas (võrdluseks)

EELDUSED (muudetavad koodi alguses)
  FC_BASE        klassi baaskulu soodsaimal kiirusel, l/100 km (ligikaudsed sõidukipargi keskmised)
  CURVE_POINTS   suhteline kulu kiirusel v: r(v) = a/v + b + c x v^2; kõver läbib kolme etteantud punkti (kerged: 30,
                 65 ja 120 km/h; rasked: 30, 70 ja 100 km/h), miinimum = 1
  Tipptunnid 7-9 ja 16-18, võrdlusaeg 10-15, profiilide aastad 2023-2025.

ARVUTUS
  Kütusekulu iga profiilirea kohta, liitrit teekilomeetri kohta loenduri asukohas:
      kulu = summa üle klasside [ N_klass x FC_klass / 100 x summa üle kiirusvahemike ( p_kiirus x r(v_kesk) ) ]
    N_klass = klassi sõidukite arv, p_kiirus = kiirusvahemiku osakaal samas reas (kõigi klasside peale kokku, sest
    loendur ei seo klassi ja kiirust omavahel), v_kesk = vahemiku keskpunkt.
  Tipptunni lisakulu. Võrdluseks arvutatakse sama rea kulu nii, nagu sõidukid sõidaksid sama loenduri, kanali ja kuu
    tööpäeva vaikse aja (10-15) kiirusjaotusega. Vahe jagatakse kaheks:
      aeglustumine   alla 60 km/h vahemike osakaalu kasvust tulenev lisakulu (ummik, sõlmed)
      kiirus         kiiremate vahemike osakaalu muutusest tulenev (nt öösel sõidetakse kiiremini)
    Lisakulu % = lisakulu / võrdluskulu x 100.
  Mudeli kütuseindeks: loenduri kuu keskmine ööpäevane kulu (summa / (n_hours / 24), kanalid liidetud) ja sellest
    mahuga kaalutud indeks nagu liiklusindeks (common.traffic_index, 2023 = 100), eraldi bensiini (kl 1-3) ja diisli
    (kl 4-10) kohta; võrdlus müügiindeksiga kolmel kujul (tase, YoY, STL jääk; vt 02).
  NB! Loendur mõõdab punktkiirust; tegelik ummikukulu (seisak, kiirendused) on tõenäoliselt suurem, seega on
  aeglustumise lisakulu alumine hinnang. Tulemus on kulu loenduri asukohas, mitte kogu riigi kütusekulu.

VÄLJUND (kaust valjund/)
  05_01_kiiruskoverad.png
      Näitab: mudeli eeldust - kuidas kütusekulu sõltub kiirusest.
      Kuidas: joondiagramm; x-telg = kiirus, km/h, y-telg = suhteline kulu (miinimum = 1). Sinine = kerged (kl 1-5, 9),
      oranž = rasked (kl 6-8, 10); punktid = etteantud kolm punkti, mida kõver läbib.
  05_02_tunniprofiil.png
      Näitab: kuidas jaotuvad tööpäeva jooksul sõidukid ja hinnanguline kütusekulu (kõik loendurid, 2023-2025).
      Kuidas: kolm paneeli ühise x-teljega (tunni algus). Ülal osakaal ööpäevast, %: hall = sõidukid, oranž = kütus.
      Keskel sõidukipargi keskmine hinnanguline kulu, l/100 km. All keskmine punktkiirus, km/h. Hall taust = tipptunnid.
  05_03_lisakulu_tunnid.png
      Näitab: millistes maakondades ja mis kell suurendab aeglustumine kütusekulu.
      Kuidas: soojuskaart; rida = maakond (järjestatud tipptundide keskmise lisakulu järgi), veerg = tunni algus,
      tööpäevad. Värv = aeglustumise lisakulu % võrreldes kella 10-15 kiirusjaotusega (punane = lisakulu, sinine =
      väiksem kulu; skaala otsad = väärtuste 98. protsentiil).
  05_04_lisakulu_loendurid.png
      Näitab: 15 loendurit, kus tipptundide aeglustumise lisakulu on suurim.
      Kuidas: rõhtsad tulbad; pikkus = lisakulu %, tulba järel väärtus ja alla 50 km/h sõitnud sõidukite osakaal.
  05_05_hinnang_vs_muuk.png
      Näitab: kas loenduritest arvutatud kütuseindeks järgib tegelikku müüki.
      Kuidas: kaks paneeli (bensiin, diisel); x-telg = aeg, y-telg = indeks (2023 = 100). Hall = mudeli hinnang,
      värviline = jaemüük; pealkirjas aastaste muutuste r.
  05_tunniprofiil.csv                    riigi tööpäeva profiil tunni kaupa
  05_lisakulu_maakond_tund.csv           lisakulu maakonna ja tunni kaupa
  05_lisakulu_loendurid.csv              tipptundide lisakulu loenduri kaupa
  05_hinnang_kuud.csv                    mudeli kütuseindeks ja müügiindeks kuude kaupa
  05_hinnang_vs_muuk_korrelatsioon.csv   nende korrelatsioon kolmel kujul
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from common import (to_period, load_daily, load_locations, counter_month, traffic_index, load_fuel_national,
                    set_style, save, save_table, yoy, stl_resid, corr_pair, month_axis,
                    CLASS_COLS, SPEED_COLS, SPEED_MID, FUEL_COLOR, FUEL_LABEL, C_BLUE, C_ORANGE,
                    C_AQUA, C_GRAY, TEXT2, BASE_YEAR, load_hourly_profile, START, END)

# ============================ EELDUSED (muuda vajadusel) ============================
# Baaskulu optimaalsel kiirusel, l/100 km (ligikaudsed sõidukipargi keskmised)
FC_BASE = {"1": 4.0, "2": 6.0, "3": 9.0, "4": 8.5, "5": 12.0,
           "6": 22.0, "7": 30.0, "8": 30.0, "9": 11.0, "10": 25.0}
# Suhteline kulu r(v) = a/v + b + c*v^2, mis läbib kolme punkti (kiirus, suhe):
CURVE_POINTS = {
    "kerge": [(30, 1.35), (65, 1.00), (120, 1.25)],  # sõiduautod, kaubikud
    "raske": [(30, 1.45), (70, 1.00), (100, 1.10)],  # veokid, bussid
}
CURVE_GROUP = {"1": "kerge", "2": "kerge", "3": "kerge", "4": "kerge", "5": "kerge",
               "9": "kerge", "6": "raske", "7": "raske", "8": "raske", "10": "raske"}
PEAK_HOURS = [7, 8, 16, 17]        # tunnid 7:00-9:00 ja 16:00-18:00
REF_HOURS = [10, 11, 12, 13, 14]   # võrdlus: päevane vaiksem aeg
PROFILE_YEARS = [2023, 2024, 2025]
PETROL_CLASSES = ["1", "2", "3"]   # võrdluseks bensiinimüügiga
DIESEL_CLASSES = ["4", "5", "6", "7", "8", "9", "10"]
# ====================================================================================

set_style()
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)


def fit_curve(points):
    """Kõvera r(v) = a/v + b + c*v^2 kordajad (a, b, c) nii, et kõver läbib kolme punkti [(kiirus, suhteline kulu), ...]:
    kolme võrrandiga lineaarsüsteemi lahend."""
    A =np.array([[1 / v, 1, v ** 2] for v, _ in points])
    y = np.array([r for _, r in points])
    return np.linalg.solve(A, y)


COEF = {g: fit_curve(p) for g, p in CURVE_POINTS.items()}


def r_of_v(group, v):
    """Suhteline kütusekulu kiirusel v (km/h; arv või massiiv) rühma group ("kerge" või "raske") kõveralt; miinimum = 1."""
    a, b, c = COEF[group]
    v = np.asarray(v, dtype=float)
    return a / v + b + c * v ** 2


V = np.array([SPEED_MID[s] for s in SPEED_COLS])
R = {g: r_of_v(g, V) for g in COEF}  # suhtelised kulud kiirusvahemike keskpunktides

# --- 1) Kõverate joonis (eelduste läbipaistvus) ---------------------------------------
vv = np.linspace(25, 135, 200)
fig, ax = plt.subplots(figsize=(7, 4))
for g, col in [("kerge", C_BLUE), ("raske", C_ORANGE)]:
    ax.plot(vv, r_of_v(g, vv), color=col, label={"kerge": "Kerged (kl 1-5, 9)",
                                                  "raske": "Rasked (kl 6-8, 10)"}[g])
    ax.scatter(*zip(*CURVE_POINTS[g]), color=col, s=40, zorder=3, edgecolor="white")
ax.axhline(1, color=TEXT2, lw=0.6, ls=":")
ax.set_xlabel("Kiirus, km/h")
ax.set_ylabel("Suhteline kütusekulu (min = 1)")
ax.set_title("Mudeli eeldus: kütusekulu sõltuvus kiirusest")
ax.legend()
save(fig, "05_01_kiiruskoverad")

# --- 2) Tunniprofiilid ja kütuse hinnang ------------------------------------------------
print("Laen tunniprofiile...")
hp = load_hourly_profile()
hp["toopaev"] = hp["toopaev"].map({"t": True, "f": False, True: True, False: False})
hp["kuu"] = to_period(hp["aasta"], hp["kuu"])
hp = hp[(hp["kuu"] >= START) & (hp["kuu"] <= END)]

# ainult kehtivad loendur-kuud (sama loogika nagu 02-04; kahtlased välja)
d = load_daily()
cm = counter_month(d)
good = cm[~cm["maht_kahtlane"] & ~cm["klass_kahtlane"]][["id", "kuu"]]
hp = hp.merge(good, on=["id", "kuu"])

N = hp[CLASS_COLS].to_numpy(float)
S = hp[SPEED_COLS].to_numpy(float)
Ssum = S.sum(axis=1, keepdims=True)
P = np.divide(S, Ssum, out=np.zeros_like(S), where=Ssum > 0)  # kiirusjaotus


def fuel_matrix(P):
    """Liitrit/km iga rea kohta, klasside kaupa (read x klassid)."""
    out = np.zeros_like(N)
    for j, c in enumerate(CLASS_COLS):
        out[:, j] = N[:, j] * FC_BASE[c] / 100 * (P @ R[CURVE_GROUP[c]])
    return out


F = fuel_matrix(P)
hp["kutus"] = F.sum(axis=1)
hp["kutus_bensiin"] = F[:, [CLASS_COLS.index(c) for c in PETROL_CLASSES]].sum(axis=1)
hp["kutus_diisel"] = F[:, [CLASS_COLS.index(c) for c in DIESEL_CLASSES]].sum(axis=1)
hp["soidukeid"] = N.sum(axis=1)
hp["alla50"] = hp[["<40Kph", "40-<50"]].sum(axis=1)

# võrdlusstsenaarium: iga loendur-kanal-kuu tööpäeva vaikse aja (10-15) kiirusjaotus
ref = (hp[hp["toopaev"] & hp["tund"].isin(REF_HOURS)]
       .groupby(["id", "kanal", "kuu"])[SPEED_COLS].sum())
ref = ref.div(ref.sum(axis=1), axis=0)
Pref = hp[["id", "kanal", "kuu"]].join(ref, on=["id", "kanal", "kuu"])[SPEED_COLS].to_numpy(float)
has_ref = ~np.isnan(Pref).any(axis=1)
Pref = np.where(has_ref[:, None], Pref, P)
hp["kutus_ref"] = fuel_matrix(Pref).sum(axis=1)

# Lisakulu jagatakse kaheks (sum(P - Pref) = 0, seega summa = kutus - kutus_ref):
#   aeglustumine - aeglasemate vahemike (< 60 km/h) osakaalu kasv (ummik, sõlmed)
#   kiirus       - kiiremate vahemike (>= 60 km/h) osakaalu muutus (nt öine kiiruse tõus)
SLOW = V < 60
dP = P - Pref


def component(mask):
    """Lisakulu (l/km iga profiilirea kohta), mis tuleb kiirusvahemike `mask` osakaalu muutusest võrreldes vaikse aja
    jaotusega: summa üle klasside N x FC/100 x summa((P - Pref) x (r - 1)) valitud vahemikes."""
    out =np.zeros(len(hp))
    for j, c in enumerate(CLASS_COLS):
        out += N[:, j] * FC_BASE[c] / 100 * (dP[:, mask] @ (R[CURVE_GROUP[c]][mask] - 1))
    return out


hp["lisakulu_aeglustumine"] = component(SLOW)
hp["lisakulu_kiirus"] = component(~SLOW)
hp["lisakulu"] = hp["lisakulu_aeglustumine"] + hp["lisakulu_kiirus"]
hp["v_summa"] = S @ V  # keskmise kiiruse arvutamiseks

LK = ["lisakulu", "lisakulu_aeglustumine", "lisakulu_kiirus"]

# --- 2a) Riigi tööpäeva tunniprofiil ----------------------------------------------------
loc = load_locations()
w = hp[hp["toopaev"] & hp["aasta"].isin(PROFILE_YEARS)]
# keskmine tunni kohta: summa / n_hours (n_hours loeb ka duplikaatread, seega keskmine on õige)
prof = w.groupby("tund")[["soidukeid", "kutus", "kutus_ref", *LK, "alla50", "v_summa", "n_hours"]].sum()
prof["soidukite_osakaal_%"] = prof["soidukeid"] / prof["soidukeid"].sum() * 100
prof["kutuse_osakaal_%"] = prof["kutus"] / prof["kutus"].sum() * 100
prof["l_100km"] = prof["kutus"] / prof["soidukeid"] * 100
prof["keskmine_kiirus"] = prof["v_summa"] / prof["soidukeid"]
prof["alla50_%"] = prof["alla50"] / prof["soidukeid"] * 100
for c in LK:
    prof[f"{c}_%"] = prof[c] / prof["kutus_ref"] * 100
save_table(prof.reset_index(), "05_tunniprofiil")

fig, axes = plt.subplots(3, 1, figsize=(9, 9.5), sharex=True)
for x0 in [7, 16]:
    for a in axes:
        a.axvspan(x0 - 0.5, x0 + 1.5, color="#f0efec", zorder=0)
ax = axes[0]
ax.plot(prof.index, prof["soidukite_osakaal_%"], color=C_GRAY, marker="o", ms=4, label="Sõidukid")
ax.plot(prof.index, prof["kutuse_osakaal_%"], color=C_ORANGE, marker="o", ms=4,
        label="Hinnanguline kütusekulu")
ax.set_ylabel("Osakaal ööpäevast, %")
ax.set_title(f"Tööpäeva tunniprofiil, kõik loendurid {PROFILE_YEARS[0]}-{PROFILE_YEARS[-1]} "
             "(hall taust = tipptunnid)")
ax.legend(loc="lower center", ncol=2)
ax = axes[1]
ax.plot(prof.index, prof["l_100km"], color=C_BLUE, marker="o", ms=4)
ax.set_ylabel("l/100 km")
ax.set_title("Sõidukipargi keskmine hinnanguline kulu (öösel suur veokite osakaal)")
ax = axes[2]
ax.plot(prof.index, prof["keskmine_kiirus"], color=C_AQUA, marker="o", ms=4)
ax.set_ylabel("km/h")
ax.set_title("Keskmine punktkiirus loenduri juures")
ax.set_xlabel("Tund (algus)")
ax.set_xticks(range(0, 24, 2))
save(fig, "05_02_tunniprofiil")

# --- 2b) Aeglustumise lisakulu tunni kaupa, maakonniti -----------------------------------
w = w.merge(loc[["id", "maakond_full", "nimi", "tee_nr"]], on="id")
mk = w.groupby(["maakond_full", "tund"])[[*LK, "kutus_ref", "alla50", "soidukeid"]].sum()
for c in LK:
    mk[f"{c}_%"] = mk[c] / mk["kutus_ref"] * 100
mk["alla50_%"] = mk["alla50"] / mk["soidukeid"] * 100
mk = mk.reset_index()
save_table(mk, "05_lisakulu_maakond_tund")
hm = mk.pivot(index="maakond_full", columns="tund", values="lisakulu_aeglustumine_%")
hm = hm.loc[hm[PEAK_HOURS].mean(axis=1).sort_values(ascending=False).index]
fig, ax = plt.subplots(figsize=(12, 6))
lim = np.nanpercentile(np.abs(hm.values), 98)
sns.heatmap(hm, cmap=sns.blend_palette(["#1c5cab", "#f0efec", "#b3302f"], as_cmap=True),
            center=0, vmin=-lim, vmax=lim, linewidths=1, linecolor="white",
            cbar_kws=dict(label="Lisakulu vs kell 10-15, %"), ax=ax)
ax.set_xlabel("Tund (algus), tööpäevad")
ax.set_ylabel("")
ax.set_title("Aeglustumisest (< 60 km/h osakaalu kasv) tulenev kütuse lisakulu")
save(fig, "05_03_lisakulu_tunnid")

# --- 2c) Loendurid suurima tipptunni aeglustumise lisakuluga -------------------------------
pk = w[w["tund"].isin(PEAK_HOURS)]
cnt = pk.groupby(["id", "nimi", "maakond_full", "tee_nr"]).agg(
    **{c: (c, "sum") for c in LK}, kutus_ref=("kutus_ref", "sum"), kutus=("kutus", "sum"),
    alla50=("alla50", "sum"), soidukeid=("soidukeid", "sum"), n_hours=("n_hours", "sum")).reset_index()
for c in LK:
    cnt[f"{c}_%"] = cnt[c] / cnt["kutus_ref"] * 100
cnt["alla50_%"] = cnt["alla50"] / cnt["soidukeid"] * 100
# liitrit teekilomeetri kohta ühe tööpäeva tipptundides (kõik suunad kokku)
kanaleid = w.groupby("id")["kanal"].nunique()
cnt["paevi"] = cnt["n_hours"] / len(PEAK_HOURS) / cnt["id"].map(kanaleid)
cnt["aeglustumine_l_km_paevas"] = cnt["lisakulu_aeglustumine"] / cnt["paevi"]
cnt = cnt.sort_values("lisakulu_aeglustumine_%", ascending=False)
save_table(cnt, "05_lisakulu_loendurid")

top = cnt.head(15).iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 6))
ax.barh([f"{n} ({m}, T{t})" for n, m, t in zip(top["nimi"], top["maakond_full"], top["tee_nr"])],
        top["lisakulu_aeglustumine_%"], color=C_ORANGE, height=0.6)
for y, (v, a) in enumerate(zip(top["lisakulu_aeglustumine_%"], top["alla50_%"])):
    ax.text(v + 0.05, y, f"{v:.1f}%  (alla 50 km/h: {a:.0f}%)", va="center", fontsize=8, color=TEXT2)
ax.set_xlabel("Tipptundide (7-9, 16-18) aeglustumise lisakulu vs kell 10-15, %")
ax.set_title("Loendurid suurima tipptunni aeglustumise lisakuluga")
ax.set_xlim(0, top["lisakulu_aeglustumine_%"].max() * 1.5)
save(fig, "05_04_lisakulu_loendurid")

# --- 3) Mudeli kütuseindeks vs tegelik müük ---------------------------------------------
m = hp.groupby(["id", "kanal", "kuu"])[["kutus", "kutus_bensiin", "kutus_diisel", "n_hours"]].sum()
for c in ["kutus", "kutus_bensiin", "kutus_diisel"]:
    m[c] = m[c] / (m["n_hours"] / 24)       # keskmine ööpäevas, l/km
m = m.groupby(["id", "kuu"])[["kutus", "kutus_bensiin", "kutus_diisel"]].sum().reset_index()
m = m.merge(cm[["id", "kuu", "aasta", "maht_kahtlane", "klass_kahtlane"]], on=["id", "kuu"])
fn = load_fuel_national().set_index("kuu")
fn["kokku"] = fn["bensiin"] + fn["diisel"]
fidx = fn / fn[fn.index.year == BASE_YEAR].mean() * 100

est = pd.DataFrame({
    "hinnang_kokku": traffic_index(m, value="kutus").set_index("kuu")["indeks"],
    "hinnang_bensiin": traffic_index(m, value="kutus_bensiin").set_index("kuu")["indeks"],
    "hinnang_diisel": traffic_index(m, value="kutus_diisel").set_index("kuu")["indeks"],
}).join(fidx, how="inner")
save_table(est.reset_index(), "05_hinnang_kuud")

rows = []
for f in ["bensiin", "diisel", "kokku"]:
    a, b = est[f"hinnang_{f}"], est[f]
    for kuju, fa, fb in [("tase", a, b), ("YoY", yoy(a), yoy(b)), ("STL jääk", stl_resid(a), stl_resid(b))]:
        rows.append(dict(kutus=f, kuju=kuju, **corr_pair(fa, fb)))
cmp_ = pd.DataFrame(rows)
save_table(cmp_, "05_hinnang_vs_muuk_korrelatsioon")

fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
for ax, f in zip(axes, ["bensiin", "diisel"]):
    t = est.index.to_timestamp()
    ax.plot(t, est[f"hinnang_{f}"], color=C_GRAY, label="Mudeli hinnang loenduritest")
    ax.plot(t, est[f], color=FUEL_COLOR[f], label=f"{FUEL_LABEL[f]} jaemüük")
    c = cmp_[(cmp_.kutus == f) & (cmp_.kuju == "YoY")].iloc[0]
    ax.set_title(f"{FUEL_LABEL[f]}: mudeli kütuseindeks vs müük  (aastamuutuste r = {c.r:.2f})")
    ax.set_ylabel(f"Indeks, {BASE_YEAR} = 100")
    ax.axhline(100, color=TEXT2, lw=0.6, ls=":")
    ax.legend(loc="upper left", ncol=2, fontsize=9)
month_axis(axes[1])
save(fig, "05_05_hinnang_vs_muuk")

print("\nTööpäeva profiil (valik):")
print(prof.loc[[3, 7, 8, 12, 16, 17, 22], ["soidukite_osakaal_%", "kutuse_osakaal_%", "l_100km",
                                          "keskmine_kiirus", "alla50_%", "lisakulu_aeglustumine_%",
                                          "lisakulu_kiirus_%"]].round(2))
pk_share = prof.loc[PEAK_HOURS, "kutus"].sum() / prof["kutus"].sum() * 100
veh_share = prof.loc[PEAK_HOURS, "soidukeid"].sum() / prof["soidukeid"].sum() * 100
print(f"\nTipptunnid ({PEAK_HOURS}): {veh_share:.1f}% sõidukitest, {pk_share:.1f}% kütusest")
print("\nMudel vs müük:")
print(cmp_.round(3).to_string(index=False))
print("\nTop 10 loendurit (tipptunni lisakulu):")
print(cnt.head(10)[["nimi", "maakond_full", "tee_nr", "lisakulu_aeglustumine_%", "lisakulu_kiirus_%",
                    "alla50_%", "aeglustumine_l_km_paevas"]].round(2).to_string(index=False))
