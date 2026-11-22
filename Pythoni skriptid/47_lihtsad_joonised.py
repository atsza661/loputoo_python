"""
47 - Lihtsad joonised: iga töös kasutatud joonise lihtsam versioon samal eesmärgil, nii et ka 10-aastane saab aru.
Üks sõnum joonise kohta, pealkiri küsimusena, suur kiri, lihtsad sõnad, otsesildid legendi asemel. Stiil nagu mujal
(common.set_style, samad värvid: sinine = hommik, oranž = õhtu). Failinimi = algse joonise number + "_10yo".

SISEND
  valjund/*.csv                    teiste skriptide tabelid (01, 06, 06_2, 07, 07_2, 09, 10, 11, 12, 13, 32, 33, 45)
  common.load_daily(), counter_month()   maanteeloendurite päevad ja kuud (01 joonised)
  Käib pärast kõiki teisi skripte (run_all lõpus pärast 11). Joonised, mis vajavad skripti sisemisi andmeid, teeb
  skript ise samal kujul: 07 (07_01b, 07_01bp), 09 (09_01...09_07b), 10 (10_09...10_13) ja 12 (12_03b).

VÄLJUND (joonised kaustas Graafikud/)
  <nr>_10yo.png                    iga algse joonise <nr> lihtne versioon
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from common import (OUT_DIR, set_style, save, load_daily, counter_month, load_locations, load_junctions, tooaeva_profiilid,
                    peak_hour, shift_peak, AM_WINDOW, PM_WINDOW, C_BLUE, C_ORANGE, C_AQUA, C_GRAY, C_RED, C_GREEN,
                    TEXT, TEXT2)

set_style()
plt.rcParams.update({"font.size": 13, "axes.titlesize": 15, "axes.labelsize": 13, "xtick.labelsize": 12,
                     "ytick.labelsize": 12})
f1 = lambda x: f"{x:.1f}".replace(".", ",")                                  # üks koht, koma
lae = lambda nimi, **kw: pd.read_csv(OUT_DIR / f"{nimi}.csv", encoding="utf-8-sig", **kw)


def pealkiri(ax, kysimus, vastus=None):
    """Pealkiri küsimusena; vastus väiksemalt teisel real."""
    ax.set_title(kysimus + (f"\n{vastus}" if vastus else ""), loc="left")


def ruudud(ax, osa, varv, silt, muu_silt):
    """10 x 10 ruudustik: osa (0...100) ruutu värviline, ülejäänud hall."""
    k = int(round(osa))
    for i in range(100):
        r, c = divmod(i, 10)
        ax.add_patch(plt.Rectangle((c, 9 - r), 0.9, 0.9, color=varv if i < k else C_GRAY, lw=0))
    ax.set_xlim(-0.2, 10)
    ax.set_ylim(-0.2, 10)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.text(10.4, 7, f"{k} {silt}", color=TEXT, fontsize=14, va="center")
    ax.text(10.4, 2, f"{100 - k} {muu_silt}", color=TEXT2, fontsize=14, va="center")


# === 01: andmete kvaliteet ===========================================================================================
kv = lae("01_kvaliteet_kokkuvote").set_index("näitaja")["väärtus"]
fig, ax = plt.subplots(figsize=(9, 5.5))
ruudud(ax, float(kv["Kehtivaid kanal-päevi, %"]), C_BLUE, "päeva korras", "päeva puudulik")
pealkiri(ax, "Kas loendurite andmed on korras?", "Iga 100 loenduripäeva kohta")
save(fig, "01_01_10yo")

d = load_daily()
cm = counter_month(d)
kuus = cm[~cm["maht_kahtlane"]].groupby("kuu")["id"].nunique()
kuus = kuus[kuus.index >= pd.Period("2020-01", "M")]
fig, ax = plt.subplots(figsize=(10, 4.8))
x = kuus.index.to_timestamp()
ax.fill_between(x, kuus.values, color=C_BLUE, alpha=0.25, lw=0)
ax.plot(x, kuus.values, color=C_BLUE)
ax.set_ylim(0, kuus.max() * 1.15)
ax.set_ylabel("töötavaid loendureid")
ax.annotate(f"kõige vähem: {kuus.min()}", (kuus.idxmin().to_timestamp(), kuus.min()), xytext=(10, -28),
            textcoords="offset points", fontsize=12, color=TEXT2, arrowprops=dict(arrowstyle="-", color=TEXT2))
ax.annotate(f"kõige rohkem: {kuus.max()}", (kuus.idxmax().to_timestamp(), kuus.max()), xytext=(-40, 12),
            textcoords="offset points", fontsize=12, color=TEXT2)
pealkiri(ax, "Mitu maanteeloendurit töötas igal kuul?")
save(fig, "01_02_10yo")

lo = load_locations()
tln = lae("07_loendurid_suunad", dtype={"id": str})
tln = tln[tln["linn"] == "Tallinn"].drop_duplicates("id")
kuud = pd.period_range("2020-01", cm["kuu"].max(), freq="M")
ok = (cm[~cm["maht_kahtlane"] & cm["id"].isin(tln["id"])].assign(v=1)
      .pivot_table(index="id", columns="kuu", values="v", aggfunc="max").reindex(columns=kuud).fillna(0))
ok = ok.loc[ok.sum(axis=1).sort_values().index]
nimi = lo.set_index("id")["nimi"]
fig, ax = plt.subplots(figsize=(10, 0.36 * len(ok) + 1.8))
for r, (i, row) in enumerate(ok.iterrows()):
    for k, v in enumerate(row.values):
        ax.add_patch(plt.Rectangle((k, r - 0.38), 1, 0.76, color=C_GREEN if v else "#e4e3df", lw=0))
ax.set_xlim(0, len(kuud))
ax.set_ylim(-0.6, len(ok) - 0.4)
ax.set_yticks(range(len(ok)), [nimi.get(i, i) for i in ok.index], fontsize=10)
jan = [k for k, m in enumerate(kuud) if m.month == 1]
ax.set_xticks(jan, [kuud[k].year for k in jan])
ax.grid(False)
pealkiri(ax, "Millal iga Tallinna lähedane maanteeloendur töötas?", "roheline = töötas, hall = andmeid ei olnud")
save(fig, "01_03_10yo")

# === 11: sõidukipõhiste kirjete kontroll ==============================================================================
t11 = lae("11_terviklikkus")
kadu = t11["puudu"].sum() / (t11["soidukeid"].sum() + t11["puudu"].sum()) * 1000
fig, ax = plt.subplots(figsize=(10, 5.2))
n_kadu = int(round(kadu))
xx, yy = np.meshgrid(np.arange(50), np.arange(20))                     # 1000 täppi = 1000 autot
ax.scatter(xx.ravel(), yy.ravel(), s=22, color=C_BLUE, lw=0)
kad = zip(*np.random.default_rng(1).integers((0, 0), (50, 20), (n_kadu, 2)).T)    # kadunud autod, koht näitlik
for x_, y_ in kad:
    ax.scatter([x_], [y_], s=40, color=C_RED, zorder=3)
    ax.add_patch(plt.Circle((x_, y_), 1.6, fill=False, color=C_RED, lw=1.5))
ax.set_xlim(-1, 50)
ax.set_ylim(-1, 20)
ax.set_aspect("equal")
ax.axis("off")
pealkiri(ax, "Kui palju autosid läks ristmike loendamisel kaduma?",
         f"Iga täpp on üks auto. 1000 autost läks kaduma {n_kadu} (punane)")
save(fig, "11_01_10yo")

u = lae("11_usutavus")
w = u["soidukeid"] / u["soidukeid"].sum()
imelik = {"auto seisis\n(kiirus 0)": "kiirus_0", "pikkust ei\nmõõdetud (0 m)": "pikkus_0",
          "liiga kiire\n(üle 120 km/h)": "kiirus_ule_120", "liiga pikk\n(üle 25 m)": "pikkus_ule_25"}
v = {k: (u[c] * w).sum() * 10 for k, c in imelik.items()}                   # % -> 1000 auto kohta
fig, ax = plt.subplots(figsize=(10, 4.6))
ax.bar(list(v), list(v.values()), color=C_BLUE, width=0.55)
for k, (s, x_) in enumerate(v.items()):
    ax.text(k, x_ + 0.1, f"{x_:.0f}" if x_ >= 0.5 else "alla 1", ha="center", va="bottom", fontsize=14)
ax.set_ylim(0, max(v.values()) * 1.35 + 0.5)
ax.set_ylabel("autot 1000-st")
pealkiri(ax, "Kui tihti oli loenduri mõõtmine imelik?", "Iga 1000 auto kohta")
save(fig, "11_02_10yo")

s = lae("11_tundlikkus")
fig, ax = plt.subplots(figsize=(9, 4.8))
silt = [f"{k * 100:.0f}%" for k in s["kunnis"]]
ax.bar(silt, s["kestus_min_mediaan"], color=[C_GRAY, C_BLUE, C_GRAY], width=0.55)
for k, m in enumerate(s["kestus_min_mediaan"]):
    ax.text(k, m + 1, f"{m:.0f} min", ha="center", va="bottom", fontsize=14)
ax.set_ylabel("ummik kestis, min")
ax.set_xlabel("piir: kui täis peab foori roheline olema, et lugeda ummikuks")
ax.set_ylim(0, s["kestus_min_mediaan"].max() * 1.25)
pealkiri(ax, "Kui piiri veidi muuta, kui pikk on ummik?", "Töö kasutab 85% (sinine)")
save(fig, "11_03_10yo")


# === 06 ja 06_2: Tallinna ristmike päev, tipptund ja tipuaeg ===========================================================
ix, V = tooaeva_profiilid(algus="2000-01-01")
prof = pd.DataFrame(V).groupby(ix["mp_id"].values).mean()                 # ristmiku tavaline tööpäev, 96 veerandtundi
linn = prof.sum()                                                         # kõik ristmikud kokku
H = np.arange(96) / 4
kell = lambda h: f"{int(h)}.{int(round(h % 1 * 60)):02d}"
tt = lae("06_tipptunnid")
ta = lae("06_2_tipptunnid")
k_tt, k_ta = tt[tt["code"] == "KÕIK"].iloc[0], ta[ta["code"] == "KÕIK"].iloc[0]


def paev(ax, v, aknad, silt):
    """Linna päevakõver: autosid veerandtunnis; aknad = [(algus_h, lõpp_h, värv, tekst)]."""
    ax.fill_between(H, v, color=C_GRAY, alpha=0.25, lw=0)
    ax.plot(H, v, color=TEXT2, lw=2)
    for a, b, c, tekst in aknad:
        ax.axvspan(a, b, color=c, alpha=0.3, lw=0)
        ax.text((a + b) / 2, v.max() * 1.04, tekst, color=c, ha="center", va="bottom", fontsize=13, fontweight="bold")
    ax.set_xlim(5, 22)
    ax.set_ylim(0, v.max() * 1.22)
    ax.set_xticks(range(6, 23, 2), [f"kell {h}" if h == 6 else str(h) for h in range(6, 23, 2)])
    ax.set_ylabel(silt)


fig, ax = plt.subplots(figsize=(10, 5))
paev(ax, linn.to_numpy(), [(k_tt["hommik_algus_h"], k_tt["hommik_algus_h"] + 1, C_BLUE, "hommikune\ntipptund"),
                           (k_tt["ohtu_algus_h"], k_tt["ohtu_algus_h"] + 1, C_ORANGE, "õhtune\ntipptund")],
     "autosid 15 minutis (kõik ristmikud)")
pealkiri(ax, "Millal on Tallinna ristmikel kõige rohkem autosid?",
         f"Tipptund: kõige tihedam tund, kell {kell(k_tt['hommik_algus_h'])} ja {kell(k_tt['ohtu_algus_h'])}")
save(fig, "06_01_10yo")

fig, ax = plt.subplots(figsize=(10, 5))
paev(ax, linn.to_numpy(), [(k_ta["hommik_algus_h"], k_ta["hommik_lopp_h"], C_BLUE, "hommikune\ntipuaeg"),
                           (k_ta["ohtu_algus_h"], k_ta["ohtu_lopp_h"], C_ORANGE, "õhtune\ntipuaeg")],
     "autosid 15 minutis (kõik ristmikud)")
pealkiri(ax, "Kui kaua kestab kõige tihedam aeg?",
         f"Tipuaeg: kell {kell(k_ta['hommik_algus_h'])}–{kell(k_ta['hommik_lopp_h'])} ja "
         f"{kell(k_ta['ohtu_algus_h'])}–{kell(k_ta['ohtu_lopp_h'])}")
save(fig, "06_2_01_10yo")

lahedal = (prof.div(prof.max(axis=1), axis=0) >= 0.8).mean() * 100      # osa ristmikest oma tipu lähedal (80% suurimast)
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.fill_between(H, lahedal, color=C_AQUA, alpha=0.35, lw=0)
ax.plot(H, lahedal, color=C_AQUA, lw=2)
ax.set_xlim(5, 22)
ax.set_ylim(0, 100)
ax.set_xticks(range(6, 23, 2))
ax.set_ylabel("% ristmikest")
ax.set_xlabel("kell")
pealkiri(ax, "Mitu ristmikku on igal kellaajal oma kõige tihedama aja lähedal?",
         "Hommikul ja õhtul on paljud ristmikud korraga tihedad")
save(fig, "06_02_10yo")


def tapid(ax, x, y, varv, samm):
    """Täpid ümardatud väärtuse kaupa üksteise peale: üks täpp = üks ristmik."""
    r = np.round(np.asarray(x) / samm) * samm
    for u in np.unique(r):
        n = int((r == u).sum())
        ax.scatter([u] * n, y + np.arange(n) * 0.22, s=60, color=varv, lw=0)


fig, ax = plt.subplots(figsize=(10, 4.6))
m = tt[tt["code"].str.startswith("MP")]
tapid(ax, m["hommik_algus_h"], 0, C_BLUE, 0.25)
tapid(ax, m["ohtu_algus_h"], 0, C_ORANGE, 0.25)
ax.set_xlim(6, 19)
ax.set_xticks(range(6, 20), [str(h) for h in range(6, 20)])
ax.set_yticks([])
ax.set_xlabel("kell")
ax.text(7.2, ax.get_ylim()[1] * 0.85, "hommik", color=C_BLUE, fontsize=14, fontweight="bold")
ax.text(15.3, ax.get_ylim()[1] * 0.85, "õhtu", color=C_ORANGE, fontsize=14, fontweight="bold")
pealkiri(ax, "Mis kell algab ristmikel tipptund?", "Üks täpp = üks ristmik")
save(fig, "06_03_10yo")

fig, ax = plt.subplots(figsize=(10, 7))
m = ta[ta["code"].str.startswith("MP")].sort_values("hommik_algus_h").reset_index(drop=True)
for i, r in m.iterrows():
    ax.plot([r["hommik_algus_h"], r["hommik_lopp_h"]], [i, i], color=C_BLUE, lw=4, solid_capstyle="butt")
    ax.plot([r["ohtu_algus_h"], r["ohtu_lopp_h"]], [i, i], color=C_ORANGE, lw=4, solid_capstyle="butt")
ax.set_xlim(6, 20)
ax.set_xticks(range(6, 21, 2))
ax.set_yticks([])
ax.set_xlabel("kell")
ax.grid(axis="y", visible=False)
pealkiri(ax, "Millal on igal ristmikul tipuaeg?", "Üks rida = üks ristmik, sinine = hommik, oranž = õhtu")
save(fig, "06_2_03_10yo")

fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
klassid = [(0, 30, "kuni 30"), (31, 45, "45"), (46, 60, "60"), (61, 90, "75–90"), (91, 999, "üle 90")]
for ax, tp, c in zip(axes, ["hommik", "ohtu"], [C_BLUE, C_ORANGE]):
    k = m[f"{tp}_kestus_min"]
    n = [int(k.between(a, b).sum()) for a, b, _ in klassid]
    ax.bar([t for *_, t in klassid], n, color=c, width=0.6)
    for i, x_ in enumerate(n):
        ax.text(i, x_ + 0.3, str(x_), ha="center", va="bottom", fontsize=13)
    ax.set_xlabel("minutit")
    ax.set_title("hommikul" if tp == "hommik" else "õhtul", loc="left", color=c)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
axes[0].set_ylabel("ristmikke")
fig.suptitle("Kui kaua kestab tipuaeg? Hommikul enamasti kuni tund, õhtul enamasti kauem", x=0.01, ha="left",
             fontsize=15, fontweight="bold")
fig.tight_layout()
save(fig, "06_2_02_10yo")


# --- koolivaheaeg (06_06, 06_2_04) -------------------------------------------------------------------------------------
kv6 = lae("06_koolivaheajad_muutus").groupby("mp_id")[["hommik_soid_h", "ohtu_soid_h", "ooopaev"]].mean().median()
fig, ax = plt.subplots(figsize=(10, 4.6))
silt = ["hommikune\ntipptund", "õhtune\ntipptund", "terve päev"]
ax.bar(silt, -kv6.values, color=[C_BLUE, C_ORANGE, C_GRAY], width=0.55)
for k, x_ in enumerate(-kv6.values):
    ax.text(k, x_ + 0.3, f"{f1(x_)}% vähem", ha="center", va="bottom", fontsize=14)
ax.set_ylim(0, -kv6.min() * 1.3)
ax.set_ylabel("autosid vähem, %")
pealkiri(ax, "Kui palju vähem autosid on lühikesel koolivaheajal?", "Võrreldud kahe nädalaga enne ja pärast vaheaega")
save(fig, "06_06_10yo")

kv2 = lae("06_2_koolivaheajad_muutus").groupby("tipp")[["viide_min", "vaheaeg_min"]].median()   # nagu tekst (3.5)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
for ax, tp, c in zip(axes, ["hommik", "ohtu"], [C_BLUE, C_ORANGE]):
    n = kv2.loc[tp, ["viide_min", "vaheaeg_min"]].to_numpy()
    ax.bar(["tavaline\nnädal", "koolivaheaeg"], n, color=[c, C_GRAY], width=0.55)
    for i, x_ in enumerate(n):
        ax.text(i, x_ + 1, f"{x_:.0f} min", ha="center", va="bottom", fontsize=14)
    ax.set_title("hommikul" if tp == "hommik" else "õhtul", loc="left", color=c)
axes[0].set_ylabel("tipuaeg, min")
axes[0].set_ylim(0, kv2.to_numpy().max() * 1.3)
fig.suptitle("Kui kaua kestab tipuaeg koolivaheajal?\nHommikul kaob tipuaeg peaaegu ära", x=0.01, ha="left",
             fontsize=15, fontweight="bold")
fig.tight_layout()
save(fig, "06_2_04_10yo")

# --- hajutamine (06_07, 06_07b, 06_08, 06_2_05, 06_2_05b, 06_2_06) -------------------------------------------------------
sc = lae("06_hajutamine_stsenaariumid")
sc = sc[sc["mp_id"] > 0]
sc2 = lae("06_2_hajutamine_stsenaariumid")
sc2 = sc2[sc2["mp_id"] > 0]
TIPP = {"hommik": ("hommikul", C_BLUE), "ohtu": ("õhtul", C_ORANGE)}


def kover(ax, df, veerg, suund, nihe, mark=1, legend=False):
    """Ristmike mediaan nihkuvate osakaalu järgi, hommik ja õhtu; mark = -1 pöörab märgi.
    legend=True, kui joonte otsad kattuvad."""
    for tp, (nimi_, c) in TIPP.items():
        g = df[(df["tipp"] == tp) & (df["suund"] == suund) & (df["nihe_min"] == nihe)]
        med = g.groupby("nihutatud_%")[veerg].median() * mark
        ax.plot(med.index, med.values, color=c, marker="o", ms=6, lw=2.5, label=nimi_)
        if not legend:
            ax.text(med.index[-1] + 0.8, med.values[-1], nimi_, color=c, fontsize=14, fontweight="bold", va="center")
    if legend:
        ax.legend(loc="upper left", fontsize=13)
    ax.axhline(0, color=TEXT2, lw=0.8)
    ax.set_xlim(0, 46)
    ax.set_xlabel("mitu autot 100-st sõidab teisel ajal")


fig, ax = plt.subplots(figsize=(10, 4.8))
kover(ax, sc, "tipu_vahenemine_%", "ühtlane", 60)
ax.set_ylabel("tipptund väiksem, %")
pealkiri(ax, "Mida rohkem autosid sõidab kuni tund varem või hiljem,", "seda väiksem on tipptund")
save(fig, "06_07_10yo")

fig, ax = plt.subplots(figsize=(10, 4.8))
kover(ax, sc2, "tipuaja_luhenemine_min", "ühtlane", 60, legend=True)
ax.set_ylim(top=ax.get_ylim()[1] * 1.3)
ax.set_ylabel("tipuaeg lühem, min")
pealkiri(ax, "Mida rohkem autosid sõidab kuni tund varem või hiljem,", "seda lühem on tipuaeg")
save(fig, "06_2_05_10yo")


def kolm_tulpa(df, veerg, mark, yhik, kysimus, nimi_):
    """20% nihkub: kolm võimalust, hommik ja õhtu kõrvuti; roheline = väheneb, punane = kasvab."""
    valik = [("ühtlane", 30, "kuni pool tundi\nvarem või hiljem"), ("ühtlane", 60, "kuni tund\nvarem või hiljem"),
             ("hiljem", 30, "kõik pool tundi\nhiljem")]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    for ax, (tp, (tnimi, c)) in zip(axes, TIPP.items()):
        g = df[(df["tipp"] == tp) & (df["nihutatud_%"] == 20)]
        y = [g[(g["suund"] == a) & (g["nihe_min"] == b)][veerg].median() * mark + 0.0 for a, b, _ in valik]
        ax.bar([t for *_, t in valik], y, color=[C_GREEN if v_ > 0 else C_RED for v_ in y], width=0.55)
        for i, v_ in enumerate(y):
            tekst = "ei muutu" if abs(v_) < 0.05 else f"{f1(abs(v_)) if yhik == '%' else f'{abs(v_):.0f}'}"
            tekst += "" if abs(v_) < 0.05 else (f"{yhik} vähem" if v_ > 0 else f"{yhik} rohkem")
            ax.text(i, max(v_, 0) + 0.02 * abs(ax.get_ylim()[1]), tekst, ha="center", va="bottom", fontsize=13)
        ax.axhline(0, color=TEXT2, lw=0.8)
        ax.set_title(tnimi, loc="left", color=c)
        ax.tick_params(axis="x", labelsize=11)
    axes[0].set_ylabel(f"väiksem ({yhik.strip()})")
    hi = max(a.get_ylim()[1] for a in axes)
    axes[0].set_ylim(min(axes[0].get_ylim()[0], 0), hi * 1.25)
    fig.suptitle(kysimus, x=0.01, ha="left", fontsize=15, fontweight="bold")
    fig.tight_layout()
    save(fig, nimi_)


kolm_tulpa(sc, "tipu_vahenemine_%", 1, "%", "Kui 20 autot 100-st sõidab teisel ajal, kui palju väiksem on tipptund?\n"
           "Roheline = väiksem, punane = suurem", "06_07b_10yo")
kolm_tulpa(sc2, "tipuaja_luhenemine_min", 1, " min", "Kui 20 autot 100-st sõidab teisel ajal, kui palju lühem on "
           "tipuaeg?\nRoheline = lühem", "06_2_05b_10yo")

hr = lae("06_hajutamine_ristmikud").query("mp_id > 0").sort_values("hommik_soid_h", ascending=False).iloc[0]   # nagu 06 näide
hr2 = lae("06_2_hajutamine_ristmikud").set_index("mp_id").loc[hr["mp_id"]]
v = prof.loc[hr["mp_id"]].to_numpy()
s0, _ = peak_hour(v, AM_WINDOW, 4)
xs = slice(5 * 4, 11 * 4)


def naide(ax, uus, a, b, tekst):
    ax.fill_between(H[xs], v[xs], color=C_GRAY, alpha=0.25, lw=0)
    ax.plot(H[xs], v[xs], color=TEXT2, lw=2.5)
    ax.plot(H[xs], uus[xs], color=C_GREEN, lw=2.5)
    ax.axvspan(a, b, color=C_BLUE, alpha=0.15, lw=0)
    ax.text((a + b) / 2, v.max() * 1.05, tekst, color=C_BLUE, ha="center", va="bottom", fontsize=13, fontweight="bold")
    i = int(9.6 * 4)
    ax.annotate("praegu", (H[i], v[i]), xytext=(25, 25), textcoords="offset points", color=TEXT2, fontsize=13,
                arrowprops=dict(arrowstyle="-", color=TEXT2))
    k = int(np.argmax(uus[xs])) + xs.start
    ax.annotate("kui 20 autot 100-st sõidab\nkuni tund varem või hiljem", (H[k], uus[k]), xytext=(-300, -160),
                textcoords="offset points", color=C_GREEN, fontsize=13, arrowprops=dict(arrowstyle="-", color=C_GREEN))
    ax.set_xlim(5, 11)
    ax.set_ylim(0, v.max() * 1.25)
    ax.set_xticks(range(5, 12), [f"kell {h}" if h == 5 else str(h) for h in range(5, 12)])
    ax.set_ylabel("autosid 15 minutis")


fig, ax = plt.subplots(figsize=(10, 5))
naide(ax, shift_peak(v, s0, 0.2, 4, "ühtlane", per_hour=4), s0 / 4, s0 / 4 + 1, "tipptund")
pealkiri(ax, f"Näide: {hr['nimi']}, hommik",
         f"Tipp jääb madalamaks, tipptunnis {f1(hr['hommik_20%_ühtlane_60min_%'])}% vähem autosid")
save(fig, "06_08_10yo")

a2 = int(hr2["hommik_algus"][:2]) * 4 + int(hr2["hommik_algus"][3:]) // 15
fig, ax = plt.subplots(figsize=(10, 5))
naide(ax, shift_peak(v, a2, 0.2, 4, "ühtlane", pikkus=int(hr2["hommik_kestus_min"]) // 15), a2 / 4,
      a2 / 4 + hr2["hommik_kestus_min"] / 60, "tipuaeg")
m0, l0 = int(hr2["hommik_minuteid"]), int(hr2["hommik_20%_ühtlane_60min_luhenemine_min"])
pealkiri(ax, f"Näide: {hr['nimi']}, hommik", f"Tipuaeg lüheneb {m0} minutilt {m0 - l0} minutile")
save(fig, "06_2_06_10yo")

# --- ristmike koormus (06_2_07) --------------------------------------------------------------------------------------------
ko = lae("06_2_koormus_ristmikud")
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
klass = [(0, 0, "alla 10"), (0, 0, "10–50"), (0, 0, "üle 50")]
for ax, (tp, (tnimi, c)) in zip(axes, TIPP.items()):
    k = ko[ko["tipp"] == tp]["tipuaeg"]
    n = [int((k < 10).sum()), int(k.between(10, 50).sum()), int((k > 50).sum())]
    ax.bar([t for *_, t in klass], n, color=c, width=0.55)
    for i, x_ in enumerate(n):
        ax.text(i, x_ + 0.3, str(x_), ha="center", va="bottom", fontsize=14)
    ax.set_title(tnimi, loc="left", color=c)
    ax.set_xlabel("mitu autot 100-st sõitis täis ristmikul")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
axes[0].set_ylabel("ristmikke")
axes[0].set_ylim(0, axes[0].get_ylim()[1] * 1.15)
fig.suptitle("Kui täis on ristmikud tipuajal?\nMõni peaaegu tühi, mõni üle poole täis", x=0.01, ha="left", fontsize=15,
             fontweight="bold")
fig.tight_layout()
save(fig, "06_2_07_10yo")

# === 07 ja 07_2: maanteed ja Tallinna sissesõit ==========================================================================
s7 = lae("07_tipptunnid_kohad")
kella = lambda ax: ax.yaxis.set_major_formatter(lambda y, _: kell(y))


def kaugus(ax, df, veerg, c, tekst):
    ax.scatter(df["km_linnast"], df[veerg], s=90, color=c, alpha=0.85, lw=0)
    ax.set_title(tekst, loc="left", color=c, fontsize=14)
    kella(ax)


fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
m = s7[s7["tyyp"] == "maantee"]
kaugus(axes[0], m[m["suund"] == "sisse"], "hommik_keskaeg_h", C_BLUE, "hommikul linna")
kaugus(axes[1], m[m["suund"] == "välja"], "ohtu_keskaeg_h", C_ORANGE, "õhtul linnast välja")
for ax in axes:
    ax.set_xlabel("kaugus Tallinna keskusest, km")
axes[0].set_ylabel("keskmiselt kell")
fig.suptitle("Kas kaugemal sõidetakse varem? Hommikul jah: mida kaugemal, seda varem.\nÕhtul sõidavad kõik umbes samal "
             "ajal", x=0.01, ha="left", fontsize=15, fontweight="bold")
fig.tight_layout()
save(fig, "07_03_10yo")

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
r7 = s7[s7["tyyp"] == "ristmik"]
kaugus(axes[0], r7, "hommik_keskaeg_h", C_BLUE, "hommikul")
kaugus(axes[1], r7, "ohtu_keskaeg_h", C_ORANGE, "õhtul")
for ax in axes:
    ax.set_xlabel("ristmiku kaugus kesklinnast, km")
axes[0].set_ylabel("keskmiselt kell")
fig.suptitle("Kas kesklinna ristmikel on tipp hiljem? Hommikul jah: autod jõuavad äärelinnast\nkesklinna hiljem. "
             "Õhtul on igal pool umbes samal ajal. Üks täpp = üks ristmik", x=0.01, ha="left", fontsize=15,
             fontweight="bold")
fig.tight_layout()
save(fig, "07_04_10yo")

k7 = lae("07_2_tipuajad_kohad")
grupid = [("ristmik", "ristmik", "Tallinna\nristmikud"), ("maantee", "sisse", "maantee\nlinna poole"),
          ("maantee", "välja", "maantee\nlinnast välja")]
k7t = k7[k7["linn"] == "Tallinn"]
fig, ax = plt.subplots(figsize=(10, 4.8))
for j, (tp, (tnimi, c)) in enumerate(TIPP.items()):
    y = [k7t[(k7t["tyyp"] == a) & (k7t["suund"] == b)][f"{tp}_kestus_min"].median() for a, b, _ in grupid]
    ax.bar(np.arange(3) + (j - 0.5) * 0.36, y, 0.34, color=c, label=tnimi)
    for i, v_ in enumerate(y):
        ax.text(i + (j - 0.5) * 0.36, v_ + 2, f"{v_:.0f}", ha="center", va="bottom", fontsize=13)
ax.set_xticks(range(3), [t for *_, t in grupid])
ax.set_ylabel("tipuaeg, min")
ax.set_ylim(0, ax.get_ylim()[1] * 1.2)
ax.legend(fontsize=13, loc="upper left")
pealkiri(ax, "Kui kaua kestab tipuaeg?", "Tavalisel kohal (mediaan), minutites")
save(fig, "07_2_01_10yo")

mt = k7[k7["tyyp"] == "maantee"]
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, (tp, (tnimi, c)) in zip(axes, TIPP.items()):
    top = mt.sort_values(f"{tp}_kestus_min", ascending=False).head(6)[::-1]
    ax.barh(top["koht"], top[f"{tp}_kestus_min"] / 60, color=c, height=0.6)
    for i, v_ in enumerate(top[f"{tp}_kestus_min"] / 60):
        ax.text(v_ + 0.05, i, f"{f1(v_)} h", va="center", fontsize=12)
    ax.set_title(tnimi, loc="left", color=c)
    ax.set_xlabel("tipuaeg, tundi")
    ax.set_xlim(0, mt[[f"{t}_kestus_min" for t in TIPP]].max().max() / 60 * 1.25)
    ax.tick_params(axis="y", labelsize=10)
    ax.grid(axis="y", visible=False)
fig.suptitle("Kus kestab tipuaeg kõige kauem? Kuus pikimat maanteeloendurit", x=0.01, ha="left", fontsize=15,
             fontweight="bold")
fig.tight_layout()
save(fig, "07_2_02_10yo")

# === 10: ummikud ja küllastus ===========================================================================================
r10 = lae("10_vaba_ruum").groupby("nihe_min")[["ruum_15min", "ruum_%"]].median()
r10 = r10[r10.index < 0]
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.bar([f"{-n} min\nenne" for n in r10.index], r10["ruum_15min"], color=C_GREEN, width=0.55)
for i, (v_, p_) in enumerate(r10.to_numpy()):
    ax.text(i, v_ + 1, f"{v_:.0f} autot", ha="center", va="bottom", fontsize=14)
ax.set_ylim(0, r10["ruum_15min"].max() * 1.3)
ax.set_ylabel("autosid mahuks veel (15 min)")
pealkiri(ax, "Kui palju autosid mahuks veel ristmikule enne ummikut?", "Mida lähemal ummik, seda vähem ruumi")
save(fig, "10_01_10yo")

K = lae("10_kullastus").set_index("mp")
kk = np.arange(K.shape[1]) / 4 + 6
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.bar(kk, (K > 50).sum().to_numpy(), width=0.22, color=C_ORANGE, align="edge")
ax.set_xticks(range(6, 21, 2))
ax.set_xlim(6, 20)
ax.set_xlabel("kell")
ax.set_ylabel("ristmikke")
ax.yaxis.set_major_locator(MaxNLocator(integer=True))
pealkiri(ax, "Mitu ristmikku oli üle poole täis?", f"{(K.max(axis=1) > 50).sum()} ristmikku {len(K)}-st olid mõnel "
         "veerandtunnil üle poole täis")
save(fig, "10_02_10yo")

lk = K.mean().to_numpy()
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.fill_between(kk, lk, color=C_ORANGE, alpha=0.3, lw=0)
ax.plot(kk, lk, color=C_ORANGE, lw=2.5)
for a, b in [(6, 12), (12, 20)]:
    i = int(np.argmax(np.where((kk >= a) & (kk < b), lk, -1)))
    ax.annotate(f"kell {kell(kk[i])}:\n{lk[i]:.0f} autot 100-st", (kk[i], lk[i]), xytext=(10, -5),
                textcoords="offset points", fontsize=13, color=TEXT)
ax.set_xticks(range(6, 21, 2))
ax.set_xlim(6, 20)
ax.set_ylim(0, lk.max() * 1.35)
ax.set_xlabel("kell")
ax.set_ylabel("autosid täis ristmikul, %")
pealkiri(ax, "Mitu autot 100-st sõidab täis ristmikul?", "Kogu linn, tavaline tööpäev")
save(fig, "10_02b_10yo")

um = lae("09_ummikud")
um = um[um["stabiilne"] & (um["tyyp"] == "tööpäev")]
u2 = um.groupby(["mp", "direction_id", "tipp"])[["algus_h", "kestus_min"]].median().reset_index()
fig, axes = plt.subplots(1, 2, figsize=(12, 6.5))
for ax, (tp, tnimi, c, xl) in zip(axes, [("hommik", "hommikul", C_BLUE, (6, 11)), ("õhtu", "õhtul", C_ORANGE, (14, 20))]):
    s_ = u2[u2["tipp"] == tp]
    s_ = s_.loc[s_.groupby("mp")["kestus_min"].idxmax()].sort_values("algus_h").reset_index(drop=True)
    for i, r_ in s_.iterrows():
        ax.plot([r_["algus_h"], r_["algus_h"] + r_["kestus_min"] / 60], [i, i], color=c, lw=5, solid_capstyle="butt")
    ax.set_xlim(*xl)
    ax.set_ylim(len(s_), -1)
    ax.set_yticks([])
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("kell")
    ax.set_title(tnimi, loc="left", color=c)
kind = um[um["meetod"] == "kindel"].groupby("tipp")["kestus_min"].median()                 # nagu tekst (3.3)
fig.suptitle(f"Millal algab ristmikel pikim ummik ja kui kaua see kestab? Üks rida = üks ristmik\nKindla tsükliga "
             f"fooril kestab ummik tavaliselt {f1(kind['hommik']).replace(',0', '')} min hommikul ja "
             f"{f1(kind['õhtu']).replace(',0', '')} min õhtul", x=0.01, ha="left", fontsize=15, fontweight="bold")
fig.tight_layout()
save(fig, "10_03_10yo")

vk = lae("10_vool_kiirus").head(8)[::-1]
fig, ax = plt.subplots(figsize=(11, 5.2))
y = np.arange(len(vk))
ax.hlines(y, vk["kiirus_labilaskevoimel"], vk["vaba_kiirus"], color=C_GRAY, lw=3)
ax.scatter(vk["vaba_kiirus"], y, s=110, color=C_GREEN, zorder=3, label="kui autosid on vähe")
ax.scatter(vk["kiirus_labilaskevoimel"], y, s=110, color=C_ORANGE, zorder=3, label="kui tee on täis")
ax.set_yticks(y, [f"{a} {b}" for a, b in zip(vk["mp"], vk["manoeuvre"].str.slice(0, 26))], fontsize=10)
ax.set_xlim(0, vk["vaba_kiirus"].max() * 1.1)
ax.set_xlabel("kiirus, km/h")
ax.grid(axis="y", visible=False)
ax.legend(fontsize=13, loc="lower left")
pealkiri(ax, "Kas autod sõidavad aeglasemalt, kui neid on palju?", "Vaba vooluga rajad: jah, täis teel on kiirus väiksem")
save(fig, "10_05_10yo")

ks = lae("10_kullastusvoog")
vahe = ks[[f"vahe_koht_{i}" for i in range(2, 13)]].median()
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.plot(range(2, 13), vahe.to_numpy(), "o-", color=C_BLUE, lw=2.5, ms=8)
ax.axhline(ks["kullastusvahe_s"].median(), color=TEXT2, lw=1.2, ls="--")
ax.text(12, ks["kullastusvahe_s"].median() * 0.97, f"{f1(ks['kullastusvahe_s'].median())} s", ha="right", va="top",
        fontsize=14, color=TEXT2)
ax.set_xticks(range(2, 13))
ax.set_ylim(0, vahe.max() * 1.25)
ax.set_xlabel("mitmes auto järjekorras")
ax.set_ylabel("sekundit eelmisest autost")
pealkiri(ax, "Kui tihti sõidab rohelise tule ajal üks auto läbi?",
         f"Esimesed alustavad aeglasemalt, siis umbes iga {ks['kullastusvahe_s'].median():.0f} sekundi tagant")
save(fig, "10_06_10yo")

pm_ = lae("10_pikad_moju").query("mp == 'KÕIK'").iloc[0]
v = [1.0, pm_["VAAB_ekvivalent"], pm_["AR_ekvivalent"]]
fig, ax = plt.subplots(figsize=(10, 4.6))
ax.bar(["sõiduauto", "buss või\nväike veok", "rekka"], v, color=[C_GRAY, C_BLUE, C_ORANGE], width=0.55)
for i, v_ in enumerate(v):
    ax.text(i, v_ + 0.05, f"{f1(v_)}", ha="center", va="bottom", fontsize=15)
ax.set_ylim(0, max(v) * 1.3)
ax.set_ylabel("mitu sõiduauto aega")
pealkiri(ax, "Kui palju rohelist aega võtab üks suur sõiduk?", "Rekka võtab peaaegu kahe sõiduauto aja")
save(fig, "10_07_10yo")

h10 = lae("10_hooga")
fig, ax = plt.subplots(figsize=(9, 5.5))
ruudud(ax, (h10["soidukeid"] * h10["osakaal_%"]).sum() / h10["soidukeid"].sum(), C_GREEN, "sõitis hooga läbi",
       "aeglustas või seisis")
pealkiri(ax, "Mitu autot 100-st sõidab foorist läbi hooga?", "Hooga = peaaegu täie kiirusega. Kindla tsükliga foorid, tööpäevad")
save(fig, "10_08_10yo")

# === 12: koolipäeva algus ja väike liikluse muutus ====================================================================
p12 = lae("12_koolialgus_pilud")
p12 = p12[p12["kell"].between("06:00", "10:00")]
x12 = pd.to_timedelta(p12["kell"].drop_duplicates() + ":00").dt.total_seconds().to_numpy() / 3600
aastad = [("2024", p12[p12["paar"] == "2025 vs 2024"]["soidukeid_vordlus"], C_GRAY),
          ("2025", p12[p12["paar"] == "2025 vs 2024"]["soidukeid"], C_BLUE),
          ("2026", p12[p12["paar"] == "2026 vs 2025"]["soidukeid"], C_ORANGE)]
k12 = lae("12_koolialgus_kokkuvote").query("naitaja == 'keskaeg_min'").set_index("paar")["mediaan"]
fig, ax = plt.subplots(figsize=(10, 5))
for a, v_, c in aastad:
    v_ = v_.to_numpy() / v_.sum() * 100
    ax.plot(x12, v_, color=c, lw=3 if a != "2024" else 2, label=a)
ax.legend(fontsize=14, loc="lower right")
ax.set_xlim(6, 10)
ax.set_xticks(range(6, 11), [f"kell {h}" if h == 6 else str(h) for h in range(6, 11)])
ax.set_ylabel("autosid, % hommiku liiklusest")
pealkiri(ax, "Kas koolipäeva hilisem algus muutis septembri hommikut?",
         f"Peaaegu mitte: 2025 sõideti keskmiselt {f1(abs(k12['2025 vs 2024']))} min hiljem, 2026 "
         f"{f1(abs(k12['2026 vs 2025']))} min varem")
save(fig, "12_01_10yo")

n12 = lae("12_koolialgus_naitajad")
fig, ax = plt.subplots(figsize=(10, 4.8))
for i, (paar, c) in enumerate([("2025 vs 2024", C_BLUE), ("2026 vs 2025", C_ORANGE)]):
    km_ = n12[n12["paar"] == paar]["keskaeg_min"].dropna()
    tapid(ax, km_, i * 4.5, c, 0.5)
    ax.text(-9.5, i * 4.5 + 0.5, f"{paar[:4]}: {(km_ > 0).sum()} hiljem, {(km_ < 0).sum()} varem", color=c, fontsize=13,
            fontweight="bold")
ax.axvline(0, color=TEXT2, lw=1)
ax.set_xlim(-10, 10)
ax.set_yticks([])
ax.set_xlabel("← varem          minutit          hiljem →")
pealkiri(ax, "Kas igal ristmikul sõideti septembri hommikul hiljem?", "Üks täpp = üks ristmik")
save(fig, "12_02_10yo")

v12 = lae("12_vaheajad_taistase").query("ryhm == 'ummikuga'").groupby("tipp")[["liiklus_%", "aeg_taistasemel_%"]].median()
fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
for ax, (tp, tnimi, c) in zip(axes, [("hommik", "hommikul", C_BLUE), ("õhtu", "õhtul", C_ORANGE)]):
    v_ = -v12.loc[tp].to_numpy()
    ax.bar(["autosid\nvähem", "täis ristmikul\nlühem aeg"], v_, color=[C_GRAY, c], width=0.55)
    for i, x_ in enumerate(v_):
        ax.text(i, x_ + 1.5, f"{x_:.0f}%", ha="center", va="bottom", fontsize=15)
    ax.set_title(tnimi, loc="left", color=c)
axes[0].set_ylabel("vähem, %")
axes[0].set_ylim(0, -v12.min().min() * 1.25)
fig.suptitle("Koolivaheajal on autosid veidi vähem, aga ristmikud on palju vähem aega täis", x=0.01, ha="left",
             fontsize=15, fontweight="bold")
fig.tight_layout()
save(fig, "12_03_10yo")

# === 13: maanteed Tallinna ümber =======================================================================================
pl = lae("13_pendellaine")
fig, ax = plt.subplots(figsize=(10, 5))
ax.axhspan(0.10, pl["asym"].max() * 1.15, color=C_BLUE, alpha=0.08, lw=0)
ax.scatter(pl["km_linnast"], pl["asym"], s=70, color=C_BLUE, alpha=0.8, lw=0)
ax.axhline(0.10, color=TEXT2, lw=1.2, ls="--")
ax.text(pl["km_linnast"].max(), 0.11, "pendelrände ala", ha="right", va="bottom", fontsize=14, color=C_BLUE,
        fontweight="bold")
ax.set_ylim(min(0, pl["asym"].min()), pl["asym"].max() * 1.15)
ax.set_xlabel("kaugus Tallinnast, km")
ax.set_ylabel("hommikul linna, õhtul välja")
pealkiri(ax, "Kus käivad inimesed iga päev Tallinnas tööl?", "Joonest kõrgemal sõidetakse hommikul selgelt linna ja õhtul "
         "välja. Üks täpp = üks maanteeloendur")
save(fig, "13_01_10yo")

s13 = pl[pl["sisse"] & (pl["asym"] >= 0.10)].copy()
s13["h"] = pd.to_timedelta(s13["hommik_kesk"] + ":00").dt.total_seconds() / 3600
b13, a13 = np.polyfit(s13["km_linnast"], s13["h"], 1)
fig, ax = plt.subplots(figsize=(10, 5))
ax.scatter(s13["km_linnast"], s13["h"], s=80, color=C_BLUE, alpha=0.85, lw=0)
xx = np.array([0, s13["km_linnast"].max()])
ax.plot(xx, a13 + b13 * xx, color=TEXT2, lw=1.5, ls="--")
for r_ in [s13.loc[s13["km_linnast"].idxmax()], s13.loc[s13["km_linnast"].idxmin()]]:
    ax.annotate(r_["nimi"], (r_["km_linnast"], r_["h"]), xytext=(6, 6), textcoords="offset points", fontsize=13)
kella(ax)
ax.set_xlabel("kaugus Tallinnast, km")
ax.set_ylabel("keskmiselt kell")
pealkiri(ax, "Hommikul liigub autode laine Tallinna poole", f"Mida kaugemal, seda varem: iga 10 km kaugemal umbes "
         f"{-b13 * 600:.0f} minutit varem")
save(fig, "13_01b_10yo")

a13 = lae("13_aeglus").sort_values("osa_paevadest_pct", ascending=False).head(6)[::-1]
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.barh([f"{n} ({l} → {s})" for n, l, s in zip(a13["nimi"], a13["lahte"], a13["siht"])], a13["osa_paevadest_pct"],
        color=C_RED, height=0.6)
for i, v_ in enumerate(a13["osa_paevadest_pct"]):
    ax.text(v_ + 1, i, f"{v_:.0f} päeva 100-st", va="center", fontsize=13)
ax.set_xlim(0, 100)
ax.grid(axis="y", visible=False)
ax.tick_params(axis="y", labelsize=11)
ax.set_xlabel("tööpäevi, mil liiklus oli aeglane, %")
pealkiri(ax, "Kus on Tallinna ümber maanteel kõige sagedamini aeglane?")
save(fig, "13_03_10yo")

ku = a13.iloc[-1]                                                      # kõige sagedamini aeglane (Kurna)
lo13 = lae("13_aeglus_loigud")
lo13 = lo13[lo13["site"] == ku["site"]]
lo13 = lo13[pd.to_datetime(lo13["paev"]).dt.dayofweek < 5]
hh = lambda s_: pd.to_timedelta(s_ + ":00").dt.total_seconds().to_numpy() // 900
pilud = np.zeros(96)
for a_, b_ in zip(hh(lo13["algus"]), hh(lo13["lopp"])):
    pilud[int(a_):int(b_)] += 1
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.bar(np.arange(96) / 4, pilud / ku["toopaevi"] * 100, width=0.22, align="edge", color=C_RED)
ax.set_xlim(6, 21)
ax.set_xticks(range(6, 22, 3))
ax.set_xlabel("kell")
ax.set_ylabel("aeglane, % tööpäevadest")
pealkiri(ax, f"Mis kell on {ku['nimi']} ringteel aeglane?", f"Hommikul kell 8–9. Siis {ku['kiirus_mediaan']:.0f} km/h "
         f"tavalise {ku['tavakiirus']:.0f} km/h asemel")
save(fig, "13_03b_10yo")

e13 = lae("13_eelhoiatus")
g13 = e13.groupby("loendur")["edumaa_min"].agg(["median", "size"]).sort_values("median")
fig, ax = plt.subplots(figsize=(10, 4.6))
ax.barh(g13.index, g13["median"], color=C_GREEN, height=0.55)
for i, (m_, n_) in enumerate(g13.to_numpy()):
    ax.text(m_ + 1, i, f"{m_:.0f} min", va="center", fontsize=14)
ax.set_xlim(0, g13["median"].max() * 1.3)
ax.grid(axis="y", visible=False)
ax.set_xlabel("minutit enne linna ummikut")
pealkiri(ax, "Kui palju varem näeb maanteel, et linnas tuleb ummik?",
         f"Maanteel algab tipp tavaliselt {e13['edumaa_min'].median():.0f} minutit enne ristmiku ummikut")
save(fig, "13_04_10yo")

# === 24: nädal soojuskaardina ==========================================================================================
k24 = lae("24_soojus_ajatelg/24_koormus_5min")
jx = load_junctions().set_index("code")
paev24 = "2026-10-20"
fig, axes = plt.subplots(2, 2, figsize=(11, 10), layout="constrained")
for ax, kl in zip(axes.flat, ["07:00", "08:30", "12:00", "17:00"]):
    s_ = k24[(k24["paev"] == paev24) & (k24["kell"] == kl)].join(jx[["lat", "lon"]], on="kood")
    sc_ = ax.scatter(s_["lon"], s_["lat"], c=s_["koormus_pct"], cmap="YlOrRd", vmin=0, vmax=100, s=90,
                     edgecolor=TEXT2, lw=0.4)
    ax.set_title(f"kell {kl.replace(':', '.')}", fontsize=15)
    ax.set_aspect(1 / np.cos(np.radians(59.43)))
    ax.set_xticks([])
    ax.set_yticks([])
fig.colorbar(sc_, ax=axes, shrink=0.8, label="kui täis, %")
fig.suptitle("Kui täis on Tallinna ristmikud päeva jooksul?\nTeisipäev, 20.10.2026. Üks täpp = üks ristmik", x=0.01,
             ha="left", fontsize=15, fontweight="bold")
save(fig, "24_01_10yo")

lk24 = k24.groupby(["paev", "kell"])["koormus_pct"].mean().unstack("paev")
x24 = pd.to_timedelta(lk24.index + ":00").total_seconds().to_numpy() / 3600
fig, ax = plt.subplots(figsize=(10, 5))
for p_ in lk24.columns:
    nadalavahetus = pd.Timestamp(p_).dayofweek >= 5
    ax.plot(x24, lk24[p_].to_numpy(), color=C_GRAY if nadalavahetus else C_BLUE, lw=2, alpha=0.9)
ax.text(18.9, lk24.iloc[-1].max(), "tööpäevad", color=C_BLUE, fontsize=14, fontweight="bold", ha="right", va="bottom")
ax.text(9, lk24.loc["09:00"].min() * 0.6, "laupäev ja pühapäev", color=C_GRAY, fontsize=14, fontweight="bold")
ax.set_xlim(6, 19)
ax.set_ylim(0, None)
ax.set_xlabel("kell")
ax.set_ylabel("ristmikud täis, % (keskmine)")
pealkiri(ax, "Kui täis on Tallinna ristmikud nädala igal päeval?", "Üks joon = üks päev, 16.–22.10.2026")
save(fig, "24_02_10yo")

# === 32, 33, 45 ======================================================================================================
p32 = lae("32_piir_osakaal")
x32 = p32["slot"].to_numpy() / 4
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.fill_between(x32, 50, p32["osakaal"], where=p32["osakaal"] >= 50, color=C_BLUE, alpha=0.3, lw=0, interpolate=True)
ax.fill_between(x32, 50, p32["osakaal"], where=p32["osakaal"] < 50, color=C_ORANGE, alpha=0.3, lw=0, interpolate=True)
ax.plot(x32, p32["osakaal"], color=TEXT2, lw=2)
ax.axhline(50, color=TEXT2, lw=1)
ax.text(7.2, p32["osakaal"].max() * 1.02, "rohkem linna", color=C_BLUE, fontsize=14, fontweight="bold")
ax.text(16, p32["osakaal"].min() * 0.92, "rohkem linnast välja", color=C_ORANGE, fontsize=14, fontweight="bold",
        va="top")
ax.set_xlim(4, 24)
ax.set_ylim(p32["osakaal"].min() * 0.8, p32["osakaal"].max() * 1.12)
ax.set_xticks(range(4, 25, 4))
ax.set_xlabel("kell")
ax.set_ylabel("sõidab linna poole, %")
pealkiri(ax, "Kas autod sõidavad linna või linnast välja?", "Tallinna piiril: hommikul linna, õhtul välja")
save(fig, "32_01_10yo")

e33 = lae("33_kullastusvoog_eeldus")
liik = e33.groupby("liik")["kullastusvoog_soid_h_rajal"].median().reindex(["otse", "vasakpööre", "parempööre"])
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.bar(["otse", "vasakule", "paremale"], liik.to_numpy(), color=C_BLUE, width=0.55)
for i, v_ in enumerate(liik.to_numpy()):
    ax.text(i, v_ + 30, f"{v_:,.0f}".replace(",", " "), ha="center", va="bottom", fontsize=15)
ax.axhline(1900, color=C_RED, lw=1.5, ls="--")
ax.text(2.45, 1900 + 30, "käsiraamatu eeldus 1900", ha="right", va="bottom", fontsize=13, color=C_RED)
ax.set_ylim(0, 2300)
ax.set_ylabel("autosid tunnis ühel rajal")
pealkiri(ax, "Mitu autot tunnis mahub rohelise tulega ühelt rajalt läbi?", "Tallinnas veidi vähem kui käsiraamatu eeldus")
save(fig, "33_01_10yo")

a45 = lae("45_aarmused")
vaik = a45[a45["leid"] == "Linna vaikseim päev"].iloc[0]
tihe = a45[a45["leid"] == "Linna tihedaim päev"].iloc[0]
v = [vaik["vaartus"], 100, tihe["vaartus"]]
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.bar([f"kõige vaiksem\n{vaik['aeg']} ({vaik['markus']})", "tavaline\ntööpäev", f"kõige tihedam\n{tihe['aeg']}"], v,
       color=[C_GRAY, C_BLUE, C_ORANGE], width=0.55)
for i, v_ in enumerate(v):
    ax.text(i, v_ + 2, f"{v_:.0f}%", ha="center", va="bottom", fontsize=15)
ax.set_ylim(0, 135)
ax.set_ylabel("liiklus, % tavalisest tööpäevast")
pealkiri(ax, "Kui palju erineb kõige vaiksem ja kõige tihedam päev?", "Tallinna ristmikud kokku")
save(fig, "45_01_10yo")
