"""
44 - Lühike koolivaheaeg vs õppetöö kellaaja kaupa ja koolitee tundide topeltvahe Sun jt (2021) meetodi järgi.

Sun, Guo, Li ja Fang (2021, Regional Science and Urban Economics 86, 103606) mõõtsid Pekingi koolisõitude mõju ummikule
kolmikvahega: koolipäev vs koolivaheaeg, koolitee tunnid vs muud tunnid ning koolide lähedal vs kaugemal olevad teed.
Siin on samad kaks esimest vahet Tallinna ristmike 15 min loendustel: kui palju väheneb liiklus koolivaheajal koolitee
tundidel rohkem kui muudel päevastel tundidel.

SISEND
  common.load_tallinn()      ristmike 15 min loendused (tallinn.count_15min); rikked ja vigased päevad on NaN, kalender
  common.SCHOOL_BREAKS       koolivaheajad (RT I, 19.03.2025, 5), kalendris veerg vaheaeg

ARVUTUS
  Vaheaeg = lühikese koolivaheaja (sügis, veebruar, kevad) tööpäevad. Võrdlus = õppetöö tööpäevad VORDLUS_PAEVI päeva
     enne ja pärast vaheaega (nagu 06_06). Jõulu- ja suvevaheaeg on välja jäetud: jõuludel on riigipühad ja suvel
     puhkab suur osa täiskasvanuid kogu vaheaja.
  Iga ristmiku, vaheaja ja 15 min pilu kohta keskmine sõidukite arv vaheaja ja võrdluspäevadel (pilu arvesse, kui
     andmeid on vähemalt MIN_VAHEAEG ja MIN_VORDLUS päeval). Pilu muutus, % = 100 x (vaheaeg / võrdlus - 1).
  Aknad (kell, AKNAD): koolitee hommikul 7.30-9.00, sest tunnid algavad Tallinnas kell 8.00-9.00 (riiklik reegel kell 9
     või hiljem, erandiga 8.00-8.50; lõputöö 1.5 ja 4.3); koolitee pärastlõunal 13.00-16.00 ja võrdlusaken 10.00-12.00.
     Sun jt aknad olid 7.00-9.00 ja 15.00-20.00, valitud tunnipõhiste hinnangute ja koolide kellaaegade järgi (lk 6,
     12-13); keskpäeval nad koolipäeva ja vaheaja vahel olulist erinevust ei leidnud (lk 5), sellest võrdlusaken.
     Pärastlõuna piirid on autori valik (TÄIENDA: Tallinna koolipäeva lõpp; 44_01 järgi kestab langus kella 20-ni).
     Akna muutus, % = 100 x (akna sõidukid vaheajal / akna sõidukid võrdluspäevadel - 1), seega
     kaalub suurema liiklusega pilu rohkem; aken arvesse, kui vähemalt 75% selle piludest on olemas.
  Topeltvahe (Sun jt mõttes), protsendipunkti = koolitee akna muutus - võrdlusakna muutus. Üldine vaheaja langus
     (puhkused, väiksem nõudlus kogu päeva) taandub, alles jääb koolitee tundide lisalangus. Hommikul langeb koolitee
     aken kokku tööle sõiduga, seega sisaldab topeltvahe ka lapsevanemate puhkust, mitte ainult koolisõite.
  Ebakindlus: 95% vahemik ristmike bootstrapiga (B korda ristmikud tagasipanekuga; mediaan üle ristmik-vaheaja paaride),
     sest sama ristmiku vaheajad pole üksteisest sõltumatud.
  Kui vaheajale ei järgne veel andmeid (2026. aasta sügisvaheaeg kuni andmete lõpuni), on võrdlus ainult enne vaheaega;
     tabelis veerg kontroll.
  shortcut: Sun jt kolmas vahe (tee kooli lähedal vs kaugemal) puudub - lisada, kui koolide asukohad (nt OSM
     amenity=school) ristmikust 400 m raadiuses on käes (Sun jt mõjuraadius, lk 6).

CALCULATION IN PLAIN ENGLISH
  Holiday = workdays of a short school break; comparison = school workdays in the 14 days before and after. For every
  junction, break and 15-minute slot: change % = 100 x (holiday mean / comparison mean - 1). A window's change uses the
  window's vehicle totals, so busy slots weigh more. Double difference (as in Sun et al. 2021) = change in a school-run
  window minus change in the 10-12 reference window, in percentage points: the general holiday drop cancels out and
  the extra drop in school-run hours remains. 95% intervals: bootstrap over junctions, median over junction-break pairs.

VÄLJUND (joonised kaustas Graafikud/, tabelid kaustas valjund/)
  44_01_vaheaeg_profiil.png
      Mida: liikluse muutus lühikese koolivaheaja tööpäevadel kellaaja kaupa, ristmike ja vaheaegade mediaan.
      Kuidas: x = kellaaeg (15 min pilu), y = muutus %; sinine joon = mediaan, vöönd = 95% vahemik; katkendjoon =
      terve päeva muutus; värvilised vööndid = koolitee aknad (oranž) ja võrdlusaken (hall).
      Näitab: millal päeva jooksul vaheaja langus on suurim ja kas see langeb koolitee tundidele.
  44_02_topeltvahe.png
      Mida: koolitee tundide lisalangus (topeltvahe) vaheaja kaupa ja kõik vaheajad koos.
      Kuidas: rida = vaheaeg (alumine = kõik koos), punkt = ristmike mediaan, kriips = 95% vahemik; oranž = hommik,
      sinine = pärastlõuna; x = protsendipunkti (miinus = koolitee tundidel langeb liiklus rohkem kui kell 10-12).
      Näitab: kas koolitee tundide lisalangus on igal vaheajal sama suunaga.
  44_profiil.csv       kell, mediaan, alumine, ülemine, paare
  44_aknad.csv         ristmik, vaheaeg, aken, muutus %
  44_topeltvahe.csv    vaheaeg, aken, mediaan, alumine, ülemine, ristmikke, kontroll
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import load_tallinn, set_style, save, save_table, C_BLUE, C_ORANGE, C_GRAY, TEXT2

AKNAD = {"koolitee hommikul": (7.5, 9.0), "koolitee pärastlõunal": (13.0, 16.0), "võrdlusaken": (10.0, 12.0)}
VORDLUS_PAEVI = 14            # nagu 06_06: 2 nädalat enne ja pärast
MIN_VAHEAEG, MIN_VORDLUS = 3, 5
B = 2000
KELL = (5, 21)
rng = np.random.default_rng(44)


def pilud(a, b):
    """Kellaajad (h) -> 15 min pilud vahemikus [a, b)."""
    return list(range(int(round(a * 4)), int(round(b * 4))))


def kell(a, b):
    """(7.5, 9.0) -> '7.30–9.00'"""
    f = lambda h: f"{int(h)}.{round(h % 1 * 60):02d}"
    return f"{f(a)}–{f(b)}"


def akna_muutus(vah, vrd, slots):
    """Akna muutus, %: vaheaja ja võrdluse pilukeskmiste summade suhe ainult piludel, kus mõlemad on olemas; NaN, kui
    alla 75% akna piludest on olemas. Viimane telg = pilu."""
    v, r = vah[..., slots], vrd[..., slots]
    ok = ~(np.isnan(v) | np.isnan(r))
    sv, sr = np.where(ok, v, 0).sum(-1), np.where(ok, r, 0).sum(-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = 100 * (sv / sr - 1)
    return np.where(ok.sum(-1) >= 0.75 * len(slots), out, np.nan)


def bootstrap(x, B=B):
    """x[ristmik, ...] -> (mediaan, 2,5%, 97,5%) üle kõigi väärtuste; ristmikud tagasipanekuga (klasterbootstrap)."""
    flat = lambda a: a.reshape(-1, a.shape[-1]) if a.ndim > 2 else a.reshape(-1, 1)   # read = ristmik(-vaheaeg) paarid
    med = np.nanmedian(flat(x), axis=0)
    idx = rng.integers(0, x.shape[0], (B, x.shape[0]))
    reps = np.array([np.nanmedian(flat(x[i]), axis=0) for i in idx])
    lo, hi = np.nanpercentile(reps, [2.5, 97.5], axis=0)
    return med, lo, hi


assert pilud(7.5, 9.0) == [30, 31, 32, 33, 34, 35]
_v, _r = np.array([[8.0, 9, np.nan, 10]]), np.array([[10.0, 10, 10, 10]])
assert np.isclose(akna_muutus(_v, _r, [0, 1, 3]), 100 * (27 / 30 - 1))[0]    # puuduv pilu jääb mõlemast välja
assert np.isnan(akna_muutus(_v, _r, [0, 2]))[0]                              # alla 75% piludest olemas
assert np.allclose(bootstrap(np.ones((5, 3)), B=20)[0], 1)

set_style()
print("Laen Tallinna ristmike andmeid...")
t, _ = load_tallinn()
work = t[t["paevatyyp"] == "tööpäev"]
bd = pd.Series(sorted(work.loc[work["vaheaeg"] == "lühike", "paev"].unique()))
breaks = bd.groupby((bd.diff() > pd.Timedelta(days=4)).cumsum()).agg(["min", "max"])
mps = sorted(work["mp_id"].unique())


def keskmine(mask, nmin):
    g = work[mask].groupby(["mp_id", "slot"])["v"]
    return g.mean().unstack("slot").where(g.count().unstack("slot") >= nmin).reindex(index=mps, columns=range(96))


VAH, VRD, info = [], [], []
for _, b in breaks.iterrows():
    kool = work["vaheaeg"] == "kool"
    enne = kool & work["paev"].between(b["min"] - pd.Timedelta(days=VORDLUS_PAEVI), b["min"] - pd.Timedelta(days=1))
    parast = kool & work["paev"].between(b["max"] + pd.Timedelta(days=1), b["max"] + pd.Timedelta(days=VORDLUS_PAEVI))
    vah = work["paev"].between(b["min"], b["max"])
    VAH.append(keskmine(vah, MIN_VAHEAEG).to_numpy())
    VRD.append(keskmine(enne | parast, MIN_VORDLUS).to_numpy())
    info.append(dict(vaheaeg=f"{b['min']:%d.%m.%Y}", kontroll="enne ja pärast" if parast.any() else "ainult enne",
                     paevi=work.loc[vah, "paev"].nunique(), vordluspaevi=work.loc[enne | parast, "paev"].nunique()))
VAH, VRD = np.stack(VAH, 1), np.stack(VRD, 1)          # [ristmik, vaheaeg, pilu]
info = pd.DataFrame(info)
print(info.to_string(index=False))

# --- 1) profiil kellaaja kaupa --------------------------------------------------------------------------------------
with np.errstate(invalid="ignore", divide="ignore"):
    D = 100 * (VAH / VRD - 1)
med, lo, hi = bootstrap(D)
paev = np.nanmedian(akna_muutus(VAH, VRD, pilud(0, 24)))
x = np.arange(96) / 4 + 0.125                          # pilu keskpunkt, h
save_table(pd.DataFrame({"kell": x, "mediaan": med, "alumine": lo, "ulemine": hi,
                         "paare": (~np.isnan(D)).sum((0, 1))}).round(2), "44_profiil")

sel = (x >= KELL[0]) & (x <= KELL[1])
fig, ax = plt.subplots(figsize=(11, 5.2))
for nimi, (a, b) in AKNAD.items():
    col = C_GRAY if nimi == "võrdlusaken" else C_ORANGE
    ax.axvspan(a, b, color=col, alpha=0.13, lw=0)
    ax.text((a + b) / 2, 0.99, nimi, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=8.5, color=TEXT2)
ax.fill_between(x[sel], lo[sel], hi[sel], color=C_BLUE, alpha=0.2, lw=0)
ax.plot(x[sel], med[sel], color=C_BLUE, lw=2, label="ristmike ja vaheaegade mediaan (vöönd = 95% vahemik)")
ax.axhline(paev, color=TEXT2, ls="--", lw=1, label=f"terve päev: {paev:+.1f}%")
ax.axhline(0, color=TEXT2, lw=0.6)
ax.set_xticks(range(KELL[0], KELL[1] + 1))
ax.set_xlim(*KELL)
ax.set_xlabel("Kellaaeg")
ax.set_ylabel("Liikluse muutus koolivaheajal, %\n(vs 2 nädalat enne ja pärast)")
ax.set_title(f"Lühike koolivaheaeg vs õppetöö kellaaja kaupa ({len(info)} vaheaega, {len(mps)} ristmikku)",
             loc="left", fontsize=10.5)
ax.legend(loc="lower right", fontsize=9)
save(fig, "44_01_vaheaeg_profiil")

# --- 2) topeltvahe: koolitee aken - võrdlusaken --------------------------------------------------------------------
W = {nimi: akna_muutus(VAH, VRD, pilud(*ak)) for nimi, ak in AKNAD.items()}          # [ristmik, vaheaeg]
save_table(pd.DataFrame([dict(mp_id=mps[i], vaheaeg=info.at[k, "vaheaeg"], aken=nimi, muutus=W[nimi][i, k])
                         for nimi in W for i in range(len(mps)) for k in range(len(info))]).dropna().round(2), "44_aknad")
DD = {nimi: W[nimi] - W["võrdlusaken"] for nimi in AKNAD if nimi != "võrdlusaken"}
rows = []
for nimi, dd in DD.items():
    for k, r in info.iterrows():
        m, l, h = bootstrap(dd[:, k])
        rows.append(dict(vaheaeg=r["vaheaeg"], aken=nimi, mediaan=m[0], alumine=l[0], ulemine=h[0],
                         ristmikke=int((~np.isnan(dd[:, k])).sum()), kontroll=r["kontroll"]))
    m, l, h = bootstrap(dd[:, :, None])
    rows.append(dict(vaheaeg="kõik", aken=nimi, mediaan=m[0], alumine=l[0], ulemine=h[0],
                     ristmikke=int((~np.isnan(dd)).any(1).sum()), kontroll=""))
tv = pd.DataFrame(rows)
save_table(tv.round(2), "44_topeltvahe")
print("\nTopeltvahe (koolitee aken - kell 10-12), protsendipunkti:")
print(tv.round(1).to_string(index=False))

ridu = list(info["vaheaeg"]) + ["kõik"]
silt = {r["vaheaeg"]: r["vaheaeg"] + (" (ainult enne)" if r["kontroll"] == "ainult enne" else "") for _, r in info.iterrows()}
fig, ax = plt.subplots(figsize=(9, 0.45 * len(ridu) + 1.8))
for j, (nimi, col) in enumerate([("koolitee hommikul", C_ORANGE), ("koolitee pärastlõunal", C_BLUE)]):
    s = tv[tv["aken"] == nimi].set_index("vaheaeg").reindex(ridu)
    y = np.arange(len(ridu))[::-1] + (0.12 if j == 0 else -0.12)
    ax.hlines(y, s["alumine"], s["ulemine"], color=col, lw=1.6)
    ax.scatter(s["mediaan"], y, color=col, s=[60 if v == "kõik" else 30 for v in ridu], zorder=3,
               label=f"{nimi} ({kell(*AKNAD[nimi])}) miinus võrdlusaken ({kell(*AKNAD['võrdlusaken'])})")
ax.axvline(0, color=TEXT2, lw=0.6)
ax.axhline(0.5, color=C_GRAY, lw=0.6, ls=":")
ax.set_yticks(np.arange(len(ridu))[::-1], [silt.get(v, "kõik vaheajad") for v in ridu])
ax.set_xlabel("Topeltvahe, protsendipunkti (miinus = koolitee tundidel langeb liiklus rohkem)")
ax.set_title("Koolitee tundide lisalangus koolivaheajal (Sun jt 2021 meetodi järgi)", loc="left", fontsize=10.5)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=1, fontsize=8.5)
save(fig, "44_02_topeltvahe")
