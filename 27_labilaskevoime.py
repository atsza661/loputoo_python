"""
27 - Läbilaskevõime: iga ristmiku eeldatav piir (suurim tunnivoog, mida ristmik on läbi lasknud) ja kui lähedal on
tavaline tipptund sellele; sissesõiduteede (maanteeloendur + linna serva ristmik) piirid ja nende summana Tallinna
hommikuse sissesõidu piir.

SISEND
  common.load_tallinn()      ristmike 15 min loendused puhastatult (tallinn.count_15min), 2024-07 ...
  common.maantee_suunad()    maanteeloendurite 15 min loendused suundade kaupa: sõidukeid, radade arv, kiiruste summa
  common.load_vehicles()     sõidukipõhised kirjed (logija nädal): ristmiku sisse- ja väljasõidu (LSS/LVS) osakaal
  valjund/24_soojus_ajatelg/24_kanalid.csv, 24_koormus_5min.csv   skripti 24 väljund (24 käib enne): kanali täistase
                             ja ristmiku seisakuosa 5 min kaupa, 16.-23.10.2026

ARVUTUS
  Tunnivoog = liikuv 60 min summa (algus 06:00...19:00); päeva tipp = selle suurim väärtus. Tööpäev = E-R, mitte püha.
  Vaadeldud piir C = tööpäevade päevatippude 99. protsentiil (PIIR_Q) kogu andmeperioodil: nii palju on ristmik
    (maantee suund) tunnis läbi lasknud mitte ainult ühel erandpäeval. Tavaline tipp = päevatippude mediaan 2026. a
    sügise õppetöö tööpäevadel (HOOAEG); koormus = tavaline tipp / C.
  Ülempiir (ristmik) = kanalite täistasemete summa (24): kõik kanalid korraga oma tavalisel tipul. See on ülemine
    hinnang, sest ristmiku kanalid jagavad rohelist aega ega saa kõik korraga tipus olla.
  Olek (ristmik):
    küllastunud    - tavaline tipp >= LAGI x C ja logija nädala tööpäevadel on seisakut (>= 10% ristmiku täistasemest
                     seisab) vähemalt SEISAK_MIN min päevas: nõudlus on suurem kui läbilase, C on piir
    lae all        - tavaline tipp >= LAGI x C, aga seisakut vähe: tipp on iga päev peaaegu sama suur (lagi), kuid
                     järjekordi ei teki - kas foorikava piir või lihtsalt püsiv nõudlus
    varu           - tavaline tipp < LAGI x C: ristmik on lasknud läbi oluliselt rohkem
  Eeldatav piir (ristmik) = C, kui ristmik on küllastunud (järjekord näitab, et rohkem läbi ei mahu); muidu suurem
    kahest: C või ülempiir.
  Maantee: sama C suuna kohta, lisaks C raja kohta ja kiirus: vaba kiirus = keskmise kiiruse 85. protsentiil
    veerandtundidel, kus voog on alla 30% C-st; kiirus suurimal voolul = kiiruse mediaan veerandtundidel, kus voog on
    >= 90% C-st; lagunemine = osa tööpäevade veerandtundidest (06-20), kus kiirus on alla 60% vabast kiirusest.
    Piiril = kiirus suurimal voolul < KIIRUS_LANG x vaba kiirus või lagunemine >= 1%: siis eeldatav piir = C (kiirus
    langeb, enamat tee läbi ei lase, sageli järgmise ristmiku tõttu); muidu eeldatav piir = radu x RADA_NOM
    (segaliikluse raja läbilaskevõime, alla mitme rajaga maantee tavapärase 2000-2200 sõiduauto tunnis).
  Sissesõidutee (RADIAALID): maanteeloenduri linna poole suund ja linna serva ristmiku sissesõit = ristmiku piir x
    sissesõidu osakaal (LSS / (LSS + LVS) hommikul 07-09 logija nädala tööpäevadel; kui LSS/LVS märgisega on alla
    80% ristmiku liiklusest, jääb ristmik välja). Tee piir = väiksem neist kahest (pudelikael), eraldi vaadeldud ja
    eeldatav. Tavaline hommikune sissesõit = maanteeloenduri linna poole suuna hommikutipp (algus 06:00-09:45), ilma
    maanteeloendurita ristmiku hommikutipp x sissesõidu osakaal. Tallinna sissesõidu piir = teede piiride summa.
  Piirangud: C on alampiir kohtades, kus nõudlus pole kunagi läbilaskevõimet ületanud; maanteeloendurid on linnast
    7-15 km kaugusel (vahel liituv liiklus jääb välja); teedel ilma maanteeloendurita on ainult ristmik.

VÄLJUND (kaust valjund/)
  27_01_ristmikud_piir.png
      Näitab: kui lähedal on iga ristmiku tavaline tipptund tema vaadeldud piirile.
      Kuidas: rida = ristmik (järjestatud koormuse järgi). x-telg = % vaadeldud piirist C (hall riba = 100%). Punkt =
      tavaline tipp (punane = küllastunud, oranž = lae all, sinine = varu), kriips = kanalite täistasemete summa
      (ülempiir). Paremal C sõidukites tunnis.
  27_02_maanteed_kiirus.png
      Näitab: sissesõiduteede maanteeloendurite voo ja kiiruse seost: kas suurimal voolul kiirus langeb (ummik).
      Kuidas: paneel loenduri kohta; x-telg = sõidukeid tunnis raja kohta (veerandtund x 4 / radu), y-telg = keskmine
      kiirus. Sinine = linna poole, oranž = linnast välja (tööpäevad kell 06-20); katkendjoon = RADA_NOM, punktiir = C
      raja kohta (sinine/oranž).
  27_03_sissesoit.png
      Näitab: kui palju on igal sissesõiduteel ja kokku hommikul varu.
      Kuidas: vasakul rida = sissesõidutee (sildis maanteeloendur ja ristmik). Hele riba = eeldatav piir, tume kitsas
      riba = vaadeldud piir (mõlemad väiksem maantee ja ristmiku piirist), sinine punkt = tavaline hommikune
      sissesõit; paremal kasutus % eeldatavast ja vaadeldud piirist. Parem paneel: kõik teed kokku (eraldi skaala).
  27_ristmikud_piir.csv     ristmik: päevi, C, maksimum, ülempiir, tavaline tipp (päev ja hommik), koormus, seisak,
                            olek, eeldatav piir
  27_maanteed_piir.csv      maantee suund: radu, C, C raja kohta, tavaline tipp, vaba kiirus, kiirus suurimal voolul,
                            lagunemine, piiril, eeldatav piir
  27_sissesoit.csv          sissesõidutee: maantee ja ristmiku piirid, sissesõidu osakaal, tee piirid, pudelikael,
                            tavaline sissesõit, kasutus
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common import (OUT_DIR, load_tallinn, maantee_suunad, load_vehicles, load_junctions, day_calendar, set_style,
                    save, save_table, C_BLUE, C_ORANGE, C_RED, C_GRAY, TEXT2, GRID)

PIIR_Q = 0.99                       # vaadeldud piir = tööpäevade päevatippude 99. protsentiil
HOOAEG = ("2026-09-01", "2026-10-04")   # tavaline tipp: 2026. a sügise õppetöö tööpäevad
LAGI = 0.9                          # tavaline tipp >= 90% piirist = lae all
SEISAK_MIN = 30                     # küllastunud: seisakut >= 30 min tööpäevas (logija nädal)
RADA_NOM = 1800                     # eeldatav maantee raja läbilaskevõime, sõid/h
KIIRUS_LANG = 0.8                   # maantee piiril, kui kiirus suurimal voolul < 80% vabast kiirusest
TUND = (24, 76)                     # tunni algus 06:00 ... 19:00 (15 min pilud)
HOMMIK = (24, 39)                   # hommikutipu algus 06:00 ... 09:45
NADAL = pd.to_datetime(["2026-10-16", "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"])
RADIAALID = [                       # sissesõidutee, maanteeloenduri linna poole suund, linna serva ristmik
    ("Peterburi tee (1)", "0cfcf | narva - tallinn", 25),
    ("Tartu mnt (2)", "0f55c | tartu - tallinn", 19),
    ("Pärnu mnt (4)", "8560b | peoleo - tallinn", 17),
    ("Viljandi mnt (15)", "1d86e | rapla - tallinn", 18),
    ("Paldiski mnt (8)", "1cf12 | paldiski - tallinn", 16),
    ("Rannamõisa tee", "36408 | rannamoisa - tallinn", None),
    ("Randvere tee (Viimsi)", "d2421 | randvere - viimsi", 24),
    ("Pirita tee (Viimsi)", None, 28),
    ("Männiku tee", None, 26),
    ("Muuga (Pärnamäe tee)", None, 23),
]


def paevatipud(w, aken=TUND):
    """Lai tabel (rida = päev, veerg = 96 pilu) -> iga päeva suurim liikuv 60 min summa (tunni algus aknas)."""
    h = w.T.rolling(4).sum().shift(-3).T
    return h.loc[:, aken[0]:aken[1]].max(axis=1)


def piir(tipud, paevad, kal):
    """Päevatippudest: (C, maksimum, tavaline tipp, tööpäevi)."""
    tp = kal.reindex(paevad)["paevatyyp"].values == "tööpäev"
    hooaeg = tp & (paevad >= HOOAEG[0]) & (paevad <= HOOAEG[1]) & (kal.reindex(paevad)["vaheaeg"].values == "kool")
    if not hooaeg.any():            # loendur ilma 2026. a sügiseta (Kangru): oma sügiste õppetöö tööpäevad
        hooaeg = tp & np.isin(paevad.month, [9, 10]) & (kal.reindex(paevad)["vaheaeg"].values == "kool")
    return tipud[tp].quantile(PIIR_Q), tipud[tp].max(), tipud[hooaeg].median(), int(tp.sum())


_w = pd.DataFrame([np.r_[np.zeros(30), np.full(4, 100.0), np.zeros(62)]])
assert paevatipud(_w).iloc[0] == 400 and paevatipud(_w * 0 + 1).iloc[0] == 4        # tunnisumma, mitte pilu

set_style()
jn = load_junctions().set_index("mp_id")

# --- ristmikud ----------------------------------------------------------------------------------------------------------
t, _ = load_tallinn()
kal = day_calendar(t["paev"]).set_index("paev")
w = t.pivot_table(index=["mp_id", "paev"], columns="slot", values="v", aggfunc="sum", dropna=False)
w = w[w.notna().sum(axis=1) >= 88].T.interpolate(limit_direction="both").T
tipud, hommik = paevatipud(w), paevatipud(w, HOMMIK)
rows = []
for mp, g in tipud.groupby("mp_id"):
    p = g.index.get_level_values("paev")
    c, mx, tava, n = piir(g.droplevel("mp_id"), p, kal)
    tava_h = piir(hommik.loc[mp], p, kal)[2]
    rows.append(dict(mp_id=mp, kood=jn.loc[mp, "code"], nimi=jn.loc[mp, "name"], tooaevi=n, C=c, maksimum=mx, tavaline=tava,
                     tavaline_hommik=tava_h))
r = pd.DataFrame(rows).set_index("kood")
k = pd.read_csv(OUT_DIR / "24_soojus_ajatelg" / "24_kanalid.csv").groupby("kood")["taistase_soid_h"].sum()
z = pd.read_csv(OUT_DIR / "24_soojus_ajatelg" / "24_koormus_5min.csv", parse_dates=["paev"])
z = z[z["paev"].isin(NADAL)]
seisak = z.groupby("kood")["seisak_pct"].apply(lambda x: (x >= 10).mean() * 13 * 60)     # min tööpäevas (06-19)
r = r.assign(ulempiir=k, seisak_min=seisak).dropna(subset=["tavaline"])
r["koormus"] = r["tavaline"] / r["C"]
r["olek"] = np.where(r["koormus"] < LAGI, "varu", np.where(r["seisak_min"] >= SEISAK_MIN, "küllastunud", "lae all"))
r["eeldatav"] = np.where(r["olek"] == "küllastunud", r["C"], np.fmax(r["C"], r["ulempiir"]))
save_table(r.reset_index().round(3), "27_ristmikud_piir")

# --- maanteed -----------------------------------------------------------------------------------------------------------
ds, dq = maantee_suunad("2024-08-01")
saidid = [s for _, s, _ in RADIAALID if s]
saidid += [s for s in ds.index if ds.loc[s, "id"] in {x.split(" |")[0] for x in saidid} and s not in saidid]   # vastassuund
dq = dq[dq["site"].isin(saidid)].copy()
dq["kiirus"] = dq["ks"] / dq["kn"]
mrows = []
for s, g in dq.groupby("site"):
    wq = g.pivot(index="paev", columns="slot", values="c")
    wq = wq[wq.notna().sum(axis=1) == 96]
    c, mx, tava, n = piir(paevatipud(wq), wq.index, kal)
    tava_h = piir(paevatipud(wq, HOMMIK), wq.index, kal)[2]
    radu = int(g["n"].max())
    tp = g[g["argipaev"] & g["slot"].between(24, 79)]
    voog = tp["c"] * 4
    vaba = tp.loc[voog < 0.3 * c, "kiirus"].quantile(0.85)
    linna = ds.loc[s, "siht"] in ("tallinn", "viimsi")
    mrows.append(dict(site=s, nimi=ds.loc[s, "nimi"], tee_nr=ds.loc[s, "tee_nr"], suund="linna" if linna else "välja",
                      radu=radu, tooaevi=n, C=c, C_rada=c / radu, maksimum=mx, tavaline=tava, tavaline_hommik=tava_h,
                      koormus=tava / c,
                      koormus_nom=tava / (RADA_NOM * radu), vaba_kiirus=vaba,
                      kiirus_tipul=tp.loc[voog >= 0.9 * c, "kiirus"].median(),
                      lagunemine_pct=(tp["kiirus"] < 0.6 * vaba).mean() * 100))
m = pd.DataFrame(mrows).set_index("site")
m["piiril"] = (m["kiirus_tipul"] < KIIRUS_LANG * m["vaba_kiirus"]) | (m["lagunemine_pct"] >= 1)
m["eeldatav"] = np.where(m["piiril"], m["C"], np.fmax(m["C"], m["radu"] * RADA_NOM))
save_table(m.reset_index().round(3), "27_maanteed_piir")

# --- sissesõiduteed -----------------------------------------------------------------------------------------------------
v = load_vehicles(None, koik=True)
v = v[v["ts"].dt.normalize().isin(NADAL) & v["ts"].dt.hour.between(7, 8)]
osa = v.groupby("mp_id")[["LSS", "LVS"]].mean()
sis = (osa["LSS"] / (osa["LSS"] + osa["LVS"])).where(osa.sum(axis=1) >= 0.8)
del v
srows = []
for tee, s, mp in RADIAALID:
    kood = jn.loc[mp, "code"] if mp else None
    o = sis.get(mp, np.nan) if mp else np.nan
    mt = m.loc[s] if s else None
    rj = r.loc[kood] if kood in r.index and not np.isnan(o) else None
    na = np.nan
    srows.append(dict(tee=tee, maantee=f"{mt['nimi']} ({mt['radu']} rada)" if s else "", ristmik=kood if rj is not None else "",
                      maantee_C=mt["C"] if s else na, maantee_eeldatav=mt["eeldatav"] if s else na,
                      maantee_tavaline=mt["tavaline_hommik"] if s else na, sissesoidu_osa=o,
                      ristmik_C=rj["C"] * o if rj is not None else na, ristmik_eeldatav=rj["eeldatav"] * o if rj is not None else na,
                      ristmik_tavaline=rj["tavaline_hommik"] * o if rj is not None else na))
sr = pd.DataFrame(srows)
sr = sr[sr[["maantee_C", "ristmik_C"]].notna().any(axis=1)]
sr["piir"] = sr[["maantee_C", "ristmik_C"]].min(axis=1)
sr["piir_eeldatav"] = sr[["maantee_eeldatav", "ristmik_eeldatav"]].min(axis=1)
sr["pudelikael"] = np.where(sr["ristmik_eeldatav"] < sr["maantee_eeldatav"].fillna(np.inf), "ristmik", "maantee")
sr["tavaline"] = sr["maantee_tavaline"].fillna(sr["ristmik_tavaline"])
sr["kasutus_pct"] = sr["tavaline"] / sr["piir"] * 100
sr["kasutus_eeldatav_pct"] = sr["tavaline"] / sr["piir_eeldatav"] * 100
kokku = dict(tee="Kõik kokku", piir=sr["piir"].sum(), piir_eeldatav=sr["piir_eeldatav"].sum(), tavaline=sr["tavaline"].sum())
kokku["kasutus_pct"] = kokku["tavaline"] / kokku["piir"] * 100
kokku["kasutus_eeldatav_pct"] = kokku["tavaline"] / kokku["piir_eeldatav"] * 100
sr = pd.concat([sr, pd.DataFrame([kokku])], ignore_index=True)
save_table(sr.round(3), "27_sissesoit")

print("\nRISTMIKUD (olek):", r["olek"].value_counts().to_dict())
print(r.sort_values("koormus", ascending=False)[["nimi", "C", "tavaline", "koormus", "ulempiir", "seisak_min", "olek",
                                                  "eeldatav"]].round(2).to_string())
print("\nMAANTEED:")
print(m[["nimi", "suund", "radu", "C", "C_rada", "tavaline", "koormus", "koormus_nom", "vaba_kiirus", "kiirus_tipul",
         "lagunemine_pct", "piiril", "eeldatav"]].round(2).sort_values(["nimi", "suund"]).to_string())
print("\nSISSESÕIT (hommik):")
print(sr[["tee", "maantee", "ristmik", "sissesoidu_osa", "maantee_C", "maantee_eeldatav", "ristmik_C", "ristmik_eeldatav",
          "piir", "piir_eeldatav", "pudelikael", "tavaline", "kasutus_pct", "kasutus_eeldatav_pct"]].round(2).to_string())

# --- joonis: ristmikud --------------------------------------------------------------------------------------------------
VARV = {"küllastunud": C_RED, "lae all": C_ORANGE, "varu": C_BLUE}
rr = r.sort_values("koormus")
fig, ax = plt.subplots(figsize=(10, 13), layout="constrained")
y = np.arange(len(rr))
ax.barh(y, 100, color=GRID, height=0.7)
ax.scatter(rr["ulempiir"] / rr["C"] * 100, y, marker="|", s=120, color="#0b0b0b", lw=1.5, zorder=3)
ax.scatter(rr["koormus"] * 100, y, s=55, color=rr["olek"].map(VARV), zorder=4, edgecolor="white", lw=1)
ax.axvline(LAGI * 100, color=TEXT2, lw=0.8, ls="--")
ax.set_yticks(y, [f"{k} {n}" for k, n in zip(rr.index, rr["nimi"])], fontsize=8)
for yi, c in zip(y, rr["C"]):
    ax.text(1.005, yi, f"{c:,.0f}".replace(",", " "), transform=ax.get_yaxis_transform(), va="center", fontsize=8, color=TEXT2)
ax.text(1.005, -0.012, "C, sõid/h", transform=ax.transAxes, fontsize=8, color=TEXT2, va="top")
ax.set_xlim(40, max(130, float(np.ceil(rr["ulempiir"].div(rr["C"]).max() * 10) * 10)))
ax.set_ylim(-0.7, len(rr) - 0.3)
ax.set_xlabel("% vaadeldud piirist C (tööpäevade tunnitippude 99. protsentiil 2024-2026)")
ax.legend(handles=[Line2D([], [], marker="o", ls="", color=c, ms=8, label=f"tavaline tipp: {k}") for k, c in VARV.items()]
          + [Line2D([], [], marker="|", ls="", color="#0b0b0b", ms=12, mew=1.5, label="kanalite täistasemete summa (ülempiir)"),
             Line2D([], [], color=TEXT2, ls="--", lw=0.8, label=f"lagi {LAGI:.0%}")],
          loc="lower right", fontsize=8, frameon=True)
ax.set_title("Ristmike tavaline tipptund (sügis 2026) ja suurim läbi lastud tunnivoog", fontsize=11)
save(fig, "27_01_ristmikud_piir")

# --- joonis: maanteede voog ja kiirus -----------------------------------------------------------------------------------
nimed = list(dict.fromkeys(m["nimi"]))
fig, axes = plt.subplots(2, (len(nimed) + 1) // 2, figsize=(4.2 * ((len(nimed) + 1) // 2), 8), sharey=True,
                         layout="constrained", squeeze=False)
for ax, nimi in zip(axes.flat, nimed):
    for s, row in m[m["nimi"] == nimi].iterrows():
        g = dq[(dq["site"] == s) & dq["argipaev"] & dq["slot"].between(24, 79)]
        col = C_BLUE if row["suund"] == "linna" else C_ORANGE
        ax.scatter(g["c"] * 4 / row["radu"], g["kiirus"], s=2, alpha=0.08, color=col, lw=0, rasterized=True)
        ax.axvline(row["C_rada"], color=col, ls=":", lw=1.5)
    ax.axvline(RADA_NOM, color=TEXT2, ls="--", lw=1)
    rad = m[m["nimi"] == nimi]["radu"].iloc[0]
    ax.set_title(f"{nimi} (tee {m[m['nimi'] == nimi]['tee_nr'].iloc[0]}, {rad} rada suunas)", fontsize=10)
    ax.set_xlim(0, RADA_NOM * 1.15)
    ax.set_xlabel("sõid/h raja kohta")
for ax in axes.flat[len(nimed):]:
    ax.set_visible(False)
for ax in axes[:, 0]:
    ax.set_ylabel("keskmine kiirus, km/h")
fig.legend(handles=[Line2D([], [], marker="o", ls="", color=C_BLUE, label="linna poole"),
                    Line2D([], [], marker="o", ls="", color=C_ORANGE, label="linnast välja"),
                    Line2D([], [], color=TEXT2, ls="--", label=f"eeldatav raja läbilaskevõime {RADA_NOM} sõid/h"),
                    Line2D([], [], color=C_GRAY, ls=":", lw=1.5, label="vaadeldud piir C raja kohta")],
           loc="outside lower center", ncol=4)
fig.suptitle("Sissesõiduteede maanteeloendurid: voog ja kiirus (tööpäevad kell 06-20, veerandtunnid 2024-2026)",
             x=0.01, ha="left", fontweight="bold")
save(fig, "27_02_maanteed_kiirus")

# --- joonis: sissesõit (vasakul teed, paremal kokku) ---------------------------------------------------------------------
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 6.5), width_ratios=[4, 1.3], layout="constrained")
s2 = sr[sr["tee"] != "Kõik kokku"].iloc[::-1].reset_index(drop=True)
y = np.arange(len(s2))
ax.barh(y, s2["piir_eeldatav"], color=GRID, height=0.7)
ax.barh(y, s2["piir"], color="#b9b8b3", height=0.3)
ax.scatter(s2["tavaline"], y, s=60, color=C_BLUE, edgecolor="white", zorder=4)
for yi, row in zip(y, s2.itertuples()):
    ax.text(1.005, yi, f"{row.kasutus_eeldatav_pct:.0f}% / {row.kasutus_pct:.0f}%  ({row.pudelikael})",
            transform=ax.get_yaxis_transform(), va="center", fontsize=8)
ax.set_yticks(y, [f"{t}\n{' / '.join(x for x in (mt, k) if x)}" for t, mt, k in
                  zip(s2["tee"], s2["maantee"].fillna(""), s2["ristmik"].fillna(""))], fontsize=8)
ax.text(1.005, 1.005, "kasutus: eeldatav / vaadeldud\n(pudelikael)", transform=ax.transAxes, fontsize=8, color=TEXT2,
        va="bottom")
ax.set_xlabel("sõidukit tunnis linna poole (hommikune tipptund)")
ax.legend(handles=[Line2D([], [], color=GRID, lw=8, label="eeldatav piir"),
                   Line2D([], [], color="#b9b8b3", lw=4, label="vaadeldud piir (suurim läbi lastud)"),
                   Line2D([], [], marker="o", ls="", color=C_BLUE, label="tavaline sissesõit")],
          loc="lower right", fontsize=8, frameon=True)
ax.set_title("Sissesõiduteed: tavaline hommikune sissesõit ja vaadeldud piir", fontsize=11)
kk = sr[sr["tee"] == "Kõik kokku"].iloc[0]
ax2.bar([0], [kk["piir_eeldatav"]], color=GRID, width=0.6)
ax2.bar([0], [kk["piir"]], color="#b9b8b3", width=0.25)
ax2.scatter([0], [kk["tavaline"]], s=80, color=C_BLUE, edgecolor="white", zorder=4)
for val, txt in [(kk["piir_eeldatav"], "eeldatav"), (kk["piir"], "vaadeldud")]:
    ax2.text(0.32, val, f"{txt}\n{val:,.0f}".replace(",", " "), va="center", fontsize=8, color=TEXT2)
ax2.text(-0.32, kk["tavaline"], f"{kk['tavaline']:,.0f}\n{kk['kasutus_eeldatav_pct']:.0f}% / {kk['kasutus_pct']:.0f}%"
         .replace(",", " "), va="center", ha="right", fontsize=8)
ax2.set_xticks([0], ["kõik teed\nkokku"])
ax2.set_xlim(-1.1, 1.1)
ax2.set_ylabel("sõidukit tunnis linna poole")
ax2.set_title("Kokku", fontsize=11)
save(fig, "27_03_sissesoit")
