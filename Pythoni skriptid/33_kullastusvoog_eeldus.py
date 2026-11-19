"""
33 - Mõõdetud küllastusvoog vs HCM 2000: kui palju sõidukeid rada fooril tegelikult läbi laseb võrreldes HCM-i
baasväärtusega 1900 sõiduautot tunnis (lk 16-10), mida see muudab skripti 27 sissesõidu piiris, ja kui suure
osa tunnist saab iga manööver rohelist (efektiivse rohelise osa g/C hinnang).

SISEND
  valjund/10_kullastusvoog.csv                  skripti 10 väljund (10 käib enne): manöövri küllastusvahe ja küllastusvoog
                                                raja kohta järjekorra tühjenemisest (logija andmed, täis tsüklid)
  valjund/24_soojus_ajatelg/24_kanalid.csv      skripti 24 väljund: kanali (raja) täistase, sõidukit tunnis
  valjund/27_sissesoit.csv, 27_sissesoit_piir.csv, 27_maanteed_piir.csv  skripti 27 väljund: sissesõiduteede ja
                                                  linna piiriloendurite piirid
  common.load_manoeuvres()                      kanal -> manööver (direction_id) ja pöörde liik

ARVUTUS
  Küllastusvoog s (10): järjekorra 5. ja tagumiste sõidukite vahede (esiotsast esiotsani) mediaan -> 3600 / vahe, sõidukit
    tunnis raja kohta. Arvesse manöövrid, kus on vähemalt MIN_VAATLUSI vahet ja MIN_TSUKLEID täis tsüklit.
  Pöörde liik: manöövri kanalite "turn" (vasakpööre, parempööre); tühi = otse.
  Efektiivse rohelise osa hinnang g/C = täistase raja kohta / s: kui manööver on tipus täis tsüklitega (24 täistase), siis
    läbib rada tunnis s x g/C sõidukit. Näitab, kui suure osa tunnist rada tegelikult küllastusvooga tühjeneb; ülejäänu on
    punane, kollane ja stardikadu. Täistase raja kohta = manöövri kanalite täistasemete keskmine.
  Tundlikkus (27): sissesõiduteede eeldatav piir, kui maantee raja läbilaskevõime (27: HCM 2000 järgi, rada_hcm) asendada mõõdetud
    küllastusvoo alumise kvartiili, mediaani ja ülemise kvartiiliga. Muutub ainult maantee, mille kiirus tipul ei lange
    (27: piiril = False), ja nagu 27-s ei lange see alla vaadeldud piiri C; tee piir = väiksem maanteest ja linna
    serva ristmikust nagu 27-s.
  ponytail: küllastusvoog on mõõdetud foori stoppjoonel; mitme rajaga maanteel ilma foorita on raja läbilaskevõime
  tavaliselt suurem (1900-2200), seega on stoppjoone väärtus maanteele pigem ettevaatlik hinnang.

CALCULATION IN PLAIN ENGLISH
  Saturation flow s (from 10) = 3600 / median headway of the 5th and later queue positions, vehicles per hour per lane;
    movements with at least MIN_VAATLUSI headways and MIN_TSUKLEID full cycles.
  Effective green share g/C = full level per lane / s: a lane that is full at the peak passes s x g/C vehicles per
    hour. Full level per lane = average full level of the movement's lanes (24).
  Sensitivity (27): the entry-road limits again with the highway lane capacity (27: HCM 2000) replaced by the lower
    quartile, median and upper quartile of measured s. Only highways whose speed does not drop at top flow change, and
    as in 27 never below their observed limit C; road limit = smaller of highway and edge junction.

VÄLJUND (joonised kaustas Graafikud/, tabelid kaustas valjund/)
  33_01_kullastusvoog_eeldus.png
      Näitab: vasakul, kui palju sõidukeid tunnis rada rohelisel tegelikult läbi laseb võrreldes HCM 2000 baasväärtusega 1900; paremal,
      kui suure osa tunnist iga manööver küllastusvooga tühjeneb.
      Kuidas: vasakul punkt = manööver (küllastusvoog raja kohta), rida = pöörde liik; must kriips = liigi mediaan,
      punane katkendjoon = HCM 2000 baasküllastusvoog 1900. Paremal hajuvusdiagramm: x = küllastusvoog raja kohta, y = täistase raja kohta
      (sõid/h), hallid kiirjooned = g/C 0,25 / 0,5 / 0,75; värv = pöörde liik (sinine otse, oranž vasakpööre, roheline
      parempööre). Sildis kõige väiksema ja suurima g/C-ga manöövrid.
  33_02_viivitus_skeem.png
      Näitab: HCM 2000 viivitusmudeli (lõputöö 1.2) kahte osa Tallinna mediaanfooril - ühtlase saabumise viivitus on
      peaaegu püsiv, lisaviivitus kasvab järsult, kui koormusaste läheneb ühele.
      Kuidas: x = koormusaste X (sagedus / läbilaskevõime), y = keskmine viivitus sõiduki kohta (s); sinine = ühtlase
      saabumise viivitus d1, oranž = lisaviivitus d2, tume = kokku (common.hcm_viivitus). Mediaanfoor: tsükkel = kindla
      tsükliga manöövrite mediaan (09_manoovrid.csv), g/C ja küllastusvoog = 33_01 mediaanid, läbilaskevõime = s x g/C.
      Katkendjooned: 0,85 (töö ummikulävi, HCM lk 10-46) ja 1 (läbilaskevõime). Algjärjekorra viivitus d3 = 0.
  33_kullastusvoog_eeldus.csv   manööver: ristmik, nimi, pöörde liik, radu, s, täistase raja kohta, g/C
  33_sissesoit_tundlikkus.csv   rada (sõid/h), Tallinna hommikuse sissesõidu eeldatav piir ja tavalise sissesõidu osa
  33_sissesoit_tundlikkus_piir.csv   sama linna piiriloendurite kohta (27_sissesoit_piir.csv)
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import (OUT_DIR, load_manoeuvres, set_style, save, save_table, place_labels, short_name, hcm_viivitus,
                    X_LAHEDAL, C_BLUE, C_ORANGE, C_AQUA, C_RED, C_GRAY, TEXT, TEXT2)

MIN_VAATLUSI, MIN_TSUKLEID = 100, 20
HCM_S0 = 1900                               # HCM 2000 baasküllastusvoog fooril, sõiduautot tunnis raja kohta (lk 16-10)
LIIGID = {"otse": C_BLUE, "vasakpööre": C_ORANGE, "parempööre": C_AQUA}


def liik(turns):
    """Manöövri kanalite pöörde nimed -> liik: kõige sagedasem vasak- või parempööre, muidu otse."""
    t = [str(x) for x in turns if isinstance(x, str)]
    vp, pp = sum("left" in x for x in t), sum("right" in x for x in t)
    return "otse" if vp + pp == 0 else ("vasakpööre" if vp >= pp else "parempööre")


def maantee_piir(eeldatav, C, radu, piiril, rada):
    """Maantee eeldatav piir uue raja väärtusega: ainult siis, kui kiirus tipul ei lange (27), ja nagu 27-s mitte alla
    vaadeldud piiri C (tee on juba nii palju läbi lasknud)."""
    return eeldatav if piiril or np.isnan(eeldatav) else max(C, radu * rada)


assert liik([np.nan, "left (vasakpööre)"]) == "vasakpööre" and liik([np.nan, np.nan]) == "otse"
assert maantee_piir(5400, 5000, 3, False, 2000) == 6000 and maantee_piir(2200, 2200, 2, True, 2000) == 2200 and \
       maantee_piir(4500, 4500, 2, False, 2000) == 4500                  # vaadeldud voog on alampiir

set_style()
k = pd.read_csv(OUT_DIR / "10_kullastusvoog.csv")
k = k[(k["vaatlusi"] >= MIN_VAATLUSI) & (k["tais_tsukleid"] >= MIN_TSUKLEID)].copy()
dm = load_manoeuvres()
dm["direction_id"] = dm["direction_id"].astype(int)
k["liik"] = k.apply(lambda r: liik(dm.loc[(dm["mp"] == r["mp"]) & (dm["direction_id"] == r["direction_id"]), "turn"]), axis=1)
kan = pd.read_csv(OUT_DIR / "24_soojus_ajatelg" / "24_kanalid.csv").rename(columns={"kood": "mp", "kanal": "channel"})
kan = kan.merge(dm[["mp", "channel", "direction_id"]], on=["mp", "channel"])
k = k.merge(kan.groupby(["mp", "direction_id"])["taistase_soid_h"].mean().rename("taistase_rajal").reset_index(),
            on=["mp", "direction_id"], how="left")
k["g_C"] = k["taistase_rajal"] / k["kullastusvoog_soid_h_rajal"]
s = k["kullastusvoog_soid_h_rajal"]
q25, q50, q75 = s.quantile([0.25, 0.5, 0.75])
save_table(k[["mp", "direction_id", "manoeuvre", "liik", "radu", "vaatlusi", "tais_tsukleid", "kullastusvahe_s",
              "kullastusvoog_soid_h_rajal", "stardikadu_s", "taistase_rajal", "g_C"]].round(3), "33_kullastusvoog_eeldus")

# --- tundlikkus: skripti 27 sissesõidu eeldatav piir --------------------------------------------------------------------
mp_ = pd.read_csv(OUT_DIR / "27_maanteed_piir.csv")
mp_ = mp_[mp_["suund"] == "linna"].set_index("nimi")
for lisa in ("", "_piir"):                # 27 sissesõiduteed ja linna piiriloendurid
    ss = pd.read_csv(OUT_DIR / f"27_sissesoit{lisa}.csv")
    ss = ss[ss["tee"] != "Kõik kokku"].copy()
    ss["m_nimi"] = ss["maantee"].str.replace(r"\s*\(\d+ rada\)", "", regex=True)
    rows = []
    for nimi, rada in [("27 (HCM 2000)", None), ("mõõdetud alumine kvartiil", q25), ("mõõdetud mediaan", q50),
                       ("mõõdetud ülemine kvartiil", q75)]:
        piir = []
        for _, r in ss.iterrows():
            m = mp_.loc[r["m_nimi"]] if r["m_nimi"] in mp_.index else None
            mt = np.nan if m is None else maantee_piir(r["maantee_eeldatav"], m["C"], m["radu"], bool(m["piiril"]),
                                                       m["rada_hcm"] if rada is None else rada)
            piir.append(np.nanmin([mt, r["ristmik_eeldatav"]]))
        kokku = np.nansum(piir)
        rows.append(dict(rada=nimi, rada_soid_h=np.nan if rada is None else round(rada), sissesoidu_piir=round(kokku),
                         tavaline=round(ss["tavaline"].sum()), kasutus_pct=round(100 * ss["tavaline"].sum() / kokku, 1)))
    tund = pd.DataFrame(rows)
    assert abs(tund.loc[0, "sissesoidu_piir"] - ss["piir_eeldatav"].sum()) < 2, "27 eeldusega peab tulema sama piir kui 27-s"
    save_table(tund, f"33_sissesoit_tundlikkus{lisa}")

# --- joonis -----------------------------------------------------------------------------------------------------------------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6.2), gridspec_kw={"width_ratios": [1, 1.25]})
rng = np.random.default_rng(1)
for i, (l, c) in enumerate(LIIGID.items()):
    x = k.loc[k["liik"] == l, "kullastusvoog_soid_h_rajal"]
    a1.scatter(x, i + rng.uniform(-0.18, 0.18, len(x)), s=28, color=c, alpha=0.75, edgecolor="white", lw=0.6)
    a1.plot([x.median()] * 2, [i - 0.3, i + 0.3], color=TEXT, lw=2.5)
    a1.text(x.median() + 12, i + 0.3, f"{x.median():,.0f}".replace(",", " "), ha="left", va="bottom", fontsize=8.5)
a1.axvline(HCM_S0, color=C_RED, ls="--", lw=1.5)
a1.text(HCM_S0 + 15, 2.62, f"HCM 2000 baasväärtus {HCM_S0}", color=C_RED, fontsize=8.5, va="center")
a1.set_yticks(range(len(LIIGID)), [f"{l}\n({(k['liik'] == l).sum()} manöövrit)" for l in LIIGID])
a1.set_ylim(-0.6, 2.8)
a1.invert_yaxis()
a1.set_xlabel("küllastusvoog, sõidukit tunnis raja kohta")
tuh = lambda x: f"{x:,.0f}".replace(",", " ")
a1.set_title(f"Mõõdetud küllastusvoog: mediaan {tuh(q50)}, kvartiilid {tuh(q25)}-{tuh(q75)}")

for l, c in LIIGID.items():
    z = k[k["liik"] == l]
    a2.scatter(z["kullastusvoog_soid_h_rajal"], z["taistase_rajal"], s=12 * z["radu"] + 18, color=c, alpha=0.75,
               edgecolor="white", lw=0.6, label=l)
xmax = s.max() * 1.05
z = k.dropna(subset=["g_C"])
ymax = z["taistase_rajal"].max() * 1.15
for g in [0.25, 0.5, 0.75]:
    a2.plot([0, xmax], [0, g * xmax], color=C_GRAY, lw=0.9, ls=":")
    xl = min(xmax, 0.97 * ymax / g)                  # silt seal, kus kiirjoon teljestikust väljub
    a2.text(xl, g * xl, f" g/C {g:.2f}".replace(".", ","), fontsize=8, color=TEXT2, va="bottom" if xl < xmax else "center",
            ha="right" if xl < xmax else "left")
vali = pd.concat([z.nsmallest(3, "g_C"), z.nlargest(4, "g_C")])
place_labels(a2, vali["kullastusvoog_soid_h_rajal"].tolist(), vali["taistase_rajal"].tolist(),
             [f"{m} {short_name(n, 22)}" for m, n in zip(vali["mp"], vali["manoeuvre"])], fontsize=7)
a2.set_xlim(s.min() * 0.9, xmax * 1.1)
a2.set_ylim(0, ymax)
a2.set_xlabel("küllastusvoog, sõidukit tunnis raja kohta (rohelisel)")
a2.set_ylabel("täistase raja kohta, sõidukit tunnis (tipp)")
a2.set_title(f"Rohelise osa hinnang g/C: mediaan {z['g_C'].median():.2f}".replace(".", ","))
a2.legend(title="pöörde liik (suurus = radu)", fontsize=8.5, title_fontsize=8.5, loc="upper left")
fig.text(0.01, -0.02, f"Tallinna hommikuse sissesõidu eeldatav piir (27): HCM 2000 rajaga -> {tuh(tund.loc[0, 'sissesoidu_piir'])} "
         f"sõid/h; mõõdetud mediaaniga {tuh(q50)} -> {tuh(tund.loc[2, 'sissesoidu_piir'])} sõid/h (kvartiilidega "
         f"{tuh(tund.loc[1, 'sissesoidu_piir'])}-{tuh(tund.loc[3, 'sissesoidu_piir'])}).", fontsize=8.5, color=TEXT2)
fig.tight_layout()
save(fig, "33_01_kullastusvoog_eeldus")

# --- 33_02: HCM viivitusmudel Tallinna mediaanfooril (lõputöö 1.2) ---------------------------------------------------
m9 = pd.read_csv(OUT_DIR / "09_manoovrid.csv")
m9 = m9[m9["meetod"] == "kindel"]
tsykkel = pd.concat([m9["hommik_T"], m9["õhtu_T"]]).median()
gC = z["g_C"].median()
c_rada = q50 * gC                                                   # raja läbilaskevõime = küllastusvoog x g/C
X = np.linspace(0.02, 1.2, 300)
d1, d2 = hcm_viivitus(X, tsykkel, gC, c_rada, osad=True)
assert np.allclose(d1 + d2, hcm_viivitus(X, tsykkel, gC, c_rada))
fig, ax = plt.subplots(figsize=(9, 5.5))
for y, col, nimi, lw in [(d1, C_BLUE, "ühtlase saabumise viivitus", 2), (d2, C_ORANGE, "lisaviivitus", 2),
                         (d1 + d2, TEXT, "kokku", 2.5)]:
    ax.plot(X, y, color=col, lw=lw, label=nimi)
    ax.annotate(nimi, (X[-1], y[-1]), xytext=(6, 0), textcoords="offset points", va="center", fontsize=9, color=col)
for x, nimi in [(X_LAHEDAL, f"{X_LAHEDAL:.2f}: läbilaskevõime lähedal (töö ummikulävi)"), (1, "1: läbilaskevõime")]:
    ax.axvline(x, color=C_GRAY, lw=0.9, ls="--")
    ax.text(x - 0.01, ax.get_ylim()[1] * 0.97, nimi.replace(".", ","), rotation=90, ha="right", va="top", fontsize=8.5,
            color=TEXT2)
ax.xaxis.set_major_formatter(lambda v, p: f"{v:.1f}".replace(".", ","))
ax.set_xlim(0, 1.2)
ax.set_ylim(0, None)
ax.set_xlabel("Koormusaste X (sagedus / läbilaskevõime)")
ax.set_ylabel("Keskmine viivitus sõiduki kohta, s")
ax.set_title(f"HCM 2000 viivitusmudel mediaanfooril: tsükkel {tsykkel:.0f} s, g/C {gC:.2f}, läbilaskevõime "
             f"{c_rada:.0f} sõidukit tunnis raja kohta".replace(".", ","), fontsize=10.5)
fig.text(0.01, -0.01, "Algjärjekorra viivitus (kolmas osa) on 0, sest analüüsiperioodi alguses ei ole järjekorda.",
         fontsize=8.5, color=TEXT2)
fig.tight_layout()
save(fig, "33_02_viivitus_skeem")
print(f"33_02: tsükkel {tsykkel:.0f} s, g/C {gC:.2f}, c {c_rada:.0f}; viivitus X=0,5 {hcm_viivitus(0.5, tsykkel, gC, c_rada):.1f} s, "
      f"X=0,85 {hcm_viivitus(X_LAHEDAL, tsykkel, gC, c_rada):.1f} s, X=1 {hcm_viivitus(1, tsykkel, gC, c_rada):.1f} s")

print(f"manöövreid {len(k)}; s mediaan {q50:.0f} (kvartiilid {q25:.0f}-{q75:.0f}); "
      + ", ".join(f"{l} {k.loc[k['liik'] == l, 'kullastusvoog_soid_h_rajal'].median():.0f} (n={(k['liik'] == l).sum()})" for l in LIIGID)
      + f"; g/C mediaan {z['g_C'].median():.2f}, vahemik {z['g_C'].min():.2f}-{z['g_C'].max():.2f}")
print(tund.to_string(index=False))
