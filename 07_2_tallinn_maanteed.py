"""
07_2 - Tallinna ristmikud ja maanteede püsiloendurid, teine versioon: tipuaeg ei ole kindel 60 min tund, vaid muutuva
pikkusega aeg, mil liiklus on sama aeglane või sama tihe kui koha tavalises tipus (15 min kuni mitu tundi). 07
joonised, mis sõltuvad tipptunnist, uue määratlusega: tipu teravus linnade ja suundade kaupa ning kaardid.

SISEND
  valjund/07_tipptunnid_kohad.csv          loenduskohad 07-st: linn, suund, koordinaadid
  valjund/07_loendurid_suunad.csv          maanteeloendurite rajad, nende linn ja suund (07)
  valjund/07_maantee_profiilid_koik.csv    kõigi maanteeloendurite 15 min profiilid (07)
  common.load_15m()                        maanteeloendurite 15 min loendused: sõidukite arv kiirusvahemike kaupa (päevast
                                           päeva kõikumine ja kiirus); pikk ajalugu on Harjumaa loenduritel
  common.load_hourly_profile()             tunniprofiili kiirusvahemikud (loendurid, millel 15 min päevi on vähe)
  common.load_daily(), counter_month()     kahtlase mahuga loendur-kuud välja
  common.load_tallinn(), tooaeva_profiilid(), mudeli_parameetrid()
                                           ristmike 15 min loendused; mudel A (foori viivitus -> kiirus, vt 40_0)
  common.load_locations(), load_junctions()  maakond (Harjumaa kaart) ja ristmike koordinaadid (Tallinna kaardi ala)
  Ainult mõlemad suunad koos ja 15 min samm: SUUND ja RES ei kehti.

ARVUTUS
  Profiilid nagu 07: E-R koolikuudel (september-mai) 2024-08...2026-08; ristmikul iga 15 min pilu keskmine, maanteel 07
    15 min profiil (tunniprofiil x veerandtundide osakaalud).
  Kiirus:
    ristmik   mudel A: foori viivitus (HCM valem; ristmiku piir 27, tsükkel 09, g/C ja küllastusvoog 33) 500 m lõigul,
              vaba kiirus 50 km/h. Kiirus väheneb ainult voo kasvades, seega on kiiruse tingimus ristmikul samuti voo
              lävi; see on voo tingimusest madalam ristmikul, mis on küllastuse lähedal (viivitus kasvab järsult).
    maantee   mõõdetud keskmine kiirus (kiirusvahemike keskpunktid): 15 min loendustest tavalistel tööpäevadel (pilu
              arvesse, kui seal on keskmiselt >= MIN_SOIDUKEID sõidukit), kui loenduri suunal on vähemalt MIN_PAEVI
              päeva; muidu tunniprofiilist (sama kiirus tunni kõigil veerandtundidel).
  Päevast päeva kõikumine (common.tipu_mura): tavalised tööpäevad (E-R, mitte püha ega lühendatud päev, õppetöö ajal),
    iga päeva suurim 15 min voog ja aeglaseim kiirus tipuaknas, 21 päeva liikuva mediaani suhtes. Voo kõikumine = kui
    palju väiksem on kerge päeva (10. protsentiil) tipp, kiiruse kõikumine = kui palju kiirem on kerge päeva (90.
    protsentiil) tipp (nagu 40_0). Maanteeloenduril, millel 15 min päevi on alla MIN_PAEVI, = teiste maanteeloendurite
    mediaan.
  Tipuaeg (common.tipuaja_lavi, tipuaeg; sama kui 06_2): tipu pilu = suurima vooga 15 min hommikul 06:00-10:00, õhtul
    14:00-19:00. Pilu on tipuaja tasemel, kui voog >= tipu voog x (1 - voo kõikumine) VÕI kiirus on tipu kiiruse
    lähedal (<= tipu kiirus x (1 + kiiruse kõikumine)) ja ühtlasi märgatavalt alla koha tavakiiruse (pilude mediaan kell
    06-20, x (1 - kiiruse kõikumine)); kiirus loeb ainult pilus, kus voog on vähemalt pool tipu voost (varahommikune
    aeglus pimedas ja veokite tõttu ei ole tipp), ja ainult siis, kui tipp ise on märgatavalt aeglasem kui tavaliselt
    (vaba vooga maanteel loeb ainult voog). Tipuaeg = tipu pilu ümber olevad järjestikused tipuaja tasemel pilud (üks
    madalam pilu vahel loetakse sisse), hommikul kell 05-12, õhtul 12-21.
  Näitajad: tipuaja algus, lõpp ja kestus; tipuaja sõidukite osakaal ööpäeva liiklusest; keskmine voog tipuajal.

VÄLJUND (kaust valjund/)
  07_2_01_tipu_teravus.png
      Näitab: kui kaua tipuaeg kestab ja kui suur osa päeva liiklusest sellesse jääb, linnade ja suundade kaupa.
      Kuidas: punktdiagrammid 2 x 2 (veerud: hommik, õhtu). Ülal tipuaja kestus, min; all tipuaja osakaal ööpäevast,
      %. x-telg = linn ja suund, punkt = loenduskoht, kriips = mediaan; musta servaga punkt = kohal kehtib kiiruse
      tingimus (tipp on märgatavalt aeglasem kui tavaliselt). Punktiir ülal = 60 min (07 tipptund).
  07_2_02_kaart_harju.png, 07_2_03_kaart_tallinn.png, 07_2_04_kaart_kesklinn.png
      Näitab: kus on tipuaeg pikk ja kus lühike (Harjumaa; Tallinn; kesklinn kuni 3 km).
      Kuidas: nagu 07 kaardid (ortofototaust; hommik = maanteel sissesuund, sinised toonid; õhtu = väljasuund, oranžid
      toonid; ruut = ristmik, ring = maanteeloendur; suurus = ööpäevane liiklus), värv = tipuaja kestus (pikem =
      tumedam; skaala otstes lühim ja pikim, KAART_MAX või pikem = skaala ülemine ots).
  07_2_tipuajad_kohad.csv     tipuaja näitajad loenduskoha kaupa (common.tipuaja_naitajad) + kõikumine ja kiiruse allikas
  07_2_linnad_kokkuvote.csv   mediaanid linna ja suuna kaupa
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from common import (OUT_DIR, SUUND, SPEED_COLS, SPEED_MID, STS_AKNAD, load_tallinn, load_15m, load_daily, counter_month,
                    ilma_vigaste_kuudeta, load_hourly_profile, day_calendar, mudeli_parameetrid, ristmike_kiirus,
                    ristmike_tipumura, tipu_mura, tipuaja_lavi, tipuaeg, tipuaja_naitajad, timing_map, bbox, map_extent,
                    km, load_junctions, load_locations, set_style, save, save_table, hhmm, C_BLUE, C_ORANGE, GRID, TEXT2)

assert not SUUND, "07_2 teeb ainult mõlemad suunad koos (SUUND ei kehti)"
P0, P1 = pd.Period("2024-08", "M"), pd.Period("2026-08", "M")     # nagu 07
SCHOOL_MONTHS = [9, 10, 11, 12, 1, 2, 3, 4, 5]
MIN_PAEVI = 40          # maanteel kõikumine ja kiirus 15 min loendustest, kui täielikke tööpäevi on vähemalt nii palju
MIN_SOIDUKEID = 20      # 15 min kiirus arvesse, kui pilus on vähemalt nii palju kiirusega sõidukeid (nagu 13)
KAART_MAX = 180         # kaardi värviskaala ülemine ots, min (üksik väga pikk tipuaeg ei sega teisi)
TALLINN = (59.4372, 24.7454)
TIPP_TXT = {"hommik": "Hommikune tipuaeg", "ohtu": "Õhtune tipuaeg"}
P = [str(i) for i in range(96)]

# enesekontroll: tipp 60 min (üks madalam pilu sees); kiiruse tingimus pikendab tipuaega 30 min (voog >= pool tipust),
# aga mitte vähese liiklusega aeglasesse varahommikusse
_v = np.full(96, 10.0)
_v[32:38] = [100, 80, 100, 100, 60, 60]
_s = np.full(96, 50.0)
_s[32:38] = 30
_s[20:31] = 20
_lv = tipuaja_lavi(_v, "hommik", 0.05, _s, 0.05)
assert tipuaeg(_v, "hommik", {**_lv, "s": None, "ks": None})["kestus_min"] == 60
assert tipuaeg(_v, "hommik", _lv, _s)["kestus_min"] == 90 and _lv["s"] == 31.5 and _lv["ks"] == 32
assert tipuaja_lavi(_v, "hommik", 0.05, np.full(96, 50.0), 0.05)["s"] is None      # aeglasemat tippu pole

set_style()
sites = pd.read_csv(OUT_DIR / "07_tipptunnid_kohad.csv", encoding="utf-8-sig", dtype={"id": str})
cat = pd.read_csv(OUT_DIR / "07_loendurid_suunad.csv", encoding="utf-8-sig", dtype={"id": str})
hw = pd.read_csv(OUT_DIR / "07_maantee_profiilid_koik.csv", encoding="utf-8-sig",
                 dtype={"id": str}).set_index(["id", "linn", "suund"])
cm = counter_month(load_daily())

# --- maanteed: päevast päeva kõikumine ja kiirus 15 min loendustest --------------------------------------------------
print("Maanteeloendurite 15 min loendused...")
m = ilma_vigaste_kuudeta(load_15m(), cm).merge(cat[["id", "kanal", "linn", "suund"]], on=["id", "kanal"])
g = (m.groupby(["id", "linn", "suund", "ts"])
     .agg(v=("v", "sum"), ks=("ks", "sum"), kn=("kn", "sum"), n=("v", "size")).reset_index())
g = g[g["n"] == g.groupby(["id", "linn", "suund"])["n"].transform("max")]      # kõik suuna rajad olemas
g["paev"] = g["ts"].dt.normalize()
g["slot"] = g["ts"].dt.hour * 4 + g["ts"].dt.minute // 15
kal = day_calendar(g["paev"]).set_index("paev")
g = g[(g["paev"].map(kal["paevatyyp"]) == "tööpäev") & (g["paev"].map(kal["vaheaeg"]) == "kool")]
mura_hw, kiir15 = {}, {}
for key, d in g.groupby(["id", "linn", "suund"]):
    tab = lambda c: d.pivot(index="paev", columns="slot", values=c).reindex(columns=range(96))
    Q = tab("v")
    Q = Q[Q.iloc[:, 24:76].notna().all(axis=1)]                    # päeval on kõik pilud kell 06-19
    if len(Q) < MIN_PAEVI:
        continue
    KS, KN = tab("ks").reindex(Q.index), tab("kn").reindex(Q.index)
    mura_hw[key] = tipu_mura(Q.index, Q.to_numpy(), (KS / KN.where(KN >= MIN_SOIDUKEID)).to_numpy())
    kiir15[key] = np.where(KN.mean() >= MIN_SOIDUKEID, KS.sum() / KN.sum(), np.nan)
mura_med = {tp: tuple(np.nanmedian([mura_hw[k][tp][i] for k in mura_hw]) for i in range(2)) for tp in STS_AKNAD}

# tunniprofiili kiirus (loendurid, millel 15 min päevi on vähe): nagu 07, E-R koolikuudel, kahtlased kuud välja
hp = load_hourly_profile()
hp["toopaev"] = hp["toopaev"].astype(str).str.lower().isin(["t", "true", "1"])
hp["per"] = pd.PeriodIndex(pd.to_datetime(dict(year=hp["aasta"], month=hp["kuu"], day=1)), freq="M")
hp = hp[hp["toopaev"] & hp["kuu"].isin(SCHOOL_MONTHS) & (hp["per"] >= P0) & (hp["per"] <= P1)]
bad = cm.loc[cm["maht_kahtlane"], ["id", "kuu"]].rename(columns={"kuu": "per"}).assign(_bad=True)
hp = hp.merge(bad, on=["id", "per"], how="left")
hp = hp[hp["_bad"].isna()].merge(cat[["id", "kanal", "linn", "suund"]], on=["id", "kanal"])
hk = hp.groupby(["id", "linn", "suund", "tund"])[SPEED_COLS].sum()
kiir1h = ((hk * pd.Series(SPEED_MID)).sum(axis=1) / hk.sum(axis=1).where(hk.sum(axis=1) > 0)).unstack("tund")

# --- ristmikud: profiil nagu 07, kiirus mudelist A ---------------------------------------------------------------------
print("Ristmikud...")
pa, _ = mudeli_parameetrid()
mura_j = ristmike_tipumura(pa)
t, _ = load_tallinn()
kuu = t["paev"].dt.to_period("M")
tt = t[(t["nadalapaev"] < 5) & t["paev"].dt.month.isin(SCHOOL_MONTHS) & (kuu >= P0) & (kuu <= P1)]
p15 = tt.groupby(["mp_id", "slot"])["v"].mean().unstack("slot").reindex(columns=range(96)).dropna()
Sj = ristmike_kiirus(p15.index, p15.to_numpy(), pa)

# --- tipuajad kõigil kohtadel -------------------------------------------------------------------------------------------
rows = []
for r in sites.itertuples():
    if r.tyyp == "ristmik":
        mp = int(r.id[2:])
        if mp not in p15.index:
            continue
        v, s = p15.loc[mp].to_numpy(), Sj[p15.index.get_loc(mp)]
        mu = {tp: tuple(mura_j.loc[(mp, tp), ["mura_q", "mura_s"]]) for tp in STS_AKNAD}
        allikas, mura_allikas = ("mudel A" if mp in pa.index else "puudub"), "ristmiku päevad"
    else:
        key = (r.id, r.linn, r.suund)
        v = hw.loc[key, P].to_numpy(float)
        if key in mura_hw:
            mu, s, allikas, mura_allikas = mura_hw[key], kiir15[key], "15 min loendus", "loenduri päevad"
        else:
            s = np.repeat(kiir1h.loc[key].reindex(range(24)).to_numpy(float), 4) if key in kiir1h.index else None
            mu, allikas, mura_allikas = mura_med, ("tunniprofiil" if s is not None else "puudub"), "maanteede mediaan"
    lv = {tp: tipuaja_lavi(v, tp, mu[tp][0], s, mu[tp][1]) for tp in STS_AKNAD}
    rows.append(dict(koht=r.koht, tyyp=r.tyyp, linn=r.linn, suund=r.suund, id=r.id, lat=r.lat, lon=r.lon,
                     km_linnast=r.km_linnast, kiiruse_allikas=allikas, kõikumise_allikas=mura_allikas,
                     **{f"{tp}_mura_q_%": mu[tp][0] * 100 for tp in STS_AKNAD},
                     **{f"{tp}_mura_s_%": mu[tp][1] * 100 for tp in STS_AKNAD},
                     **tipuaja_naitajad(v, lv, s)))
k = pd.DataFrame(rows)
assert (k.filter(like="_kestus_min") >= 15).all().all() and (k["hommik_lopp_h"] <= 12).all()
save_table(k, "07_2_tipuajad_kohad")

grp_order = [("Tallinn", "ristmik"), ("Tallinn", "sisse"), ("Tallinn", "välja"), ("Tallinn", "muu"),
             ("Tartu", "sisse"), ("Tartu", "välja"), ("Pärnu", "sisse"), ("Pärnu", "välja"),
             ("Viimsi", "sisse"), ("Viimsi", "välja")]
agg = dict(kohti=("koht", "size"))
for tp in STS_AKNAD:
    agg.update({f"{tp}_algus_h": (f"{tp}_algus_h", "median"), f"{tp}_lopp_h": (f"{tp}_lopp_h", "median"),
                f"{tp}_kestus_min": (f"{tp}_kestus_min", "median"), f"{tp}_kestus_min_q1": (f"{tp}_kestus_min", lambda x: x.quantile(0.25)),
                f"{tp}_kestus_min_q3": (f"{tp}_kestus_min", lambda x: x.quantile(0.75)),
                f"{tp}_osakaal_%": (f"{tp}_osakaal_%", "median"), f"{tp}_kiirus_tingimus": (f"{tp}_kiirus_tingimus", "sum")})
summ = k.groupby(["linn", "suund"]).agg(**agg).reindex(grp_order).dropna(how="all")
for tp in STS_AKNAD:
    for c in ("algus", "lopp"):
        summ[f"{tp}_{c}"] = summ[f"{tp}_{c}_h"].map(hhmm)
save_table(summ.reset_index(), "07_2_linnad_kokkuvote")

# --- 07_2_01_tipu_teravus ------------------------------------------------------------------------------------------------
k["grupp"] = k["linn"] + "\n" + k["suund"]
order = [f"{c}\n{s}" for c, s in grp_order if ((k.linn == c) & (k.suund == s)).any()]
rng = np.random.default_rng(0)
jit = rng.uniform(-0.18, 0.18, len(k))
xg = k["grupp"].map({g_: i for i, g_ in enumerate(order)}).to_numpy() + jit
fig, axes = plt.subplots(2, 2, figsize=(14, 8.4), sharex=True)
for i, tp in enumerate(STS_AKNAD):
    col = C_BLUE if tp == "hommik" else C_ORANGE
    for j, (c, ylab) in enumerate([(f"{tp}_kestus_min", "Tipuaja kestus, min"),
                                    (f"{tp}_osakaal_%", "Tipuaja osakaal ööpäevast, %")]):
        ax = axes[j, i]
        kt = k[f"{tp}_kiirus_tingimus"].to_numpy()
        ax.scatter(xg[~kt], k.loc[~kt, c], s=26, color=col, alpha=0.75, edgecolor="none", zorder=3)
        ax.scatter(xg[kt], k.loc[kt, c], s=26, color=col, alpha=0.85, edgecolor="black", linewidth=0.8, zorder=3)
        med = k.groupby("grupp")[c].median().reindex(order)
        ax.scatter(range(len(order)), med.values, marker="_", s=900, color=TEXT2, zorder=4, lw=2)
        if j == 0:
            ax.axhline(60, color=TEXT2, lw=0.8, ls=":", zorder=1)
            ax.set_yscale("log")
            ax.set_yticks([15, 30, 60, 120, 240, 480])
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:g}"))
            ax.yaxis.set_minor_locator(plt.NullLocator())
            ax.set_title(f"{TIPP_TXT[tp]} (kriips = mediaan)")
        ax.set_ylabel(ylab if i == 0 else "")
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels(order, fontsize=8)
handles = [Line2D([], [], marker="o", ls="", color=TEXT2, alpha=0.6, markeredgecolor="none",
                  label="ainult voo tingimus (sama tihe kui tipp)"),
           Line2D([], [], marker="o", ls="", color=TEXT2, alpha=0.8, markeredgecolor="black",
                  label="ka kiiruse tingimus (tipp märgatavalt aeglasem)"),
           Line2D([], [], ls=":", color=TEXT2, label="60 min (07 tipptund)")]
fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=9, bbox_to_anchor=(0.5, 0))
fig.suptitle("Muutuva pikkusega tipuaeg: aeg, mil liiklus on sama aeglane või sama tihe kui koha tavalises tipus "
             "(päevast päeva kõikumise piires)", x=0.01, ha="left", fontweight="bold", fontsize=11.5)
fig.tight_layout(rect=(0, 0.04, 1, 1))
save(fig, "07_2_01_tipu_teravus")

# --- kaardid ----------------------------------------------------------------------------------------------------------------
loc = load_locations()
jn = load_junctions()
kk = k.assign(**{f"{tp}_kestus_min": k[f"{tp}_kestus_min"].clip(upper=KAART_MAX) for tp in STS_AKNAD})
harju_ids = set(loc.loc[loc.maakond == "Harju", "id"])
mp_ = kk[(kk.tyyp == "ristmik") | kk.id.isin(harju_ids)]
yle = lambda df: ", ".join(f"{r.id if r.tyyp == 'ristmik' else r.koht.split(' (')[0]} {tp[0].upper()} "
                           f"{int(k.at[r.Index, f'{tp}_kestus_min'])} min"
                           for tp in STS_AKNAD for r in df[k.loc[df.index, f"{tp}_kestus_min"] > KAART_MAX].itertuples())
markus = lambda df: f" (üle {KAART_MAX} min: {yle(df)})" if yle(df) else ""
timing_map(mp_, "07_2_02_kaart_harju", "Tipuaja kestus: kui kaua on liiklus sama aeglane või sama tihe kui tavalises "
           f"tipus{markus(mp_)}", label_junctions=False, size_k=1.3, naitaja="kestus")
lo0, la0, lo1, la1 = bbox(jn, pad=0.04)                            # nagu 07: kõigi ristmike ümbris
in_city = mp_[mp_.lon.between(lo0, lo1) & mp_.lat.between(la0, la1)]
jun = mp_[mp_.tyyp == "ristmik"]
centre = jun[km(jun.lat, jun.lon, *TALLINN) <= 3.0]
CENTRE_PAD = 0.12
timing_map(in_city, "07_2_03_kaart_tallinn", f"Tallinna ristmikud ({len(jun)}): tipuaja kestus{markus(in_city)}",
           label_junctions=True, size_k=0.8, zoom_box=map_extent(centre, CENTRE_PAD),
           zoom_label=f"kesklinn, {len(centre)} ristmikku: vt 07_2_04_kaart_kesklinn", naitaja="kestus")
timing_map(centre, "07_2_04_kaart_kesklinn", f"Tallinna ristmikud (≤ 3 km, {len(centre)}): tipuaja kestus{markus(centre)}",
           label_junctions=True, size_k=1.4, label_fs=8, pad=CENTRE_PAD, naitaja="kestus")

pd.set_option("display.width", 220)
print(f"\nMaanteeloendureid {int((k.tyyp == 'maantee').sum())}: kõikumine ja kiirus 15 min loendustest {len(mura_hw)}, "
      f"tunniprofiilist {int((k.kiiruse_allikas == 'tunniprofiil').sum())}; maanteede mediaan: hommik voog "
      f"{mura_med['hommik'][0] * 100:.1f}%, kiirus {mura_med['hommik'][1] * 100:.1f}%; õhtu voog "
      f"{mura_med['ohtu'][0] * 100:.1f}%, kiirus {mura_med['ohtu'][1] * 100:.1f}%")
print("\nTipuaeg linna ja suuna kaupa (mediaanid):")
print(summ[["kohti", "hommik_algus", "hommik_lopp", "hommik_kestus_min", "hommik_osakaal_%", "hommik_kiirus_tingimus",
            "ohtu_algus", "ohtu_lopp", "ohtu_kestus_min", "ohtu_osakaal_%", "ohtu_kiirus_tingimus"]].round(1).to_string())
print("\nMaanteed, kus kiiruse tingimus kehtib:")
for tp in STS_AKNAD:
    z = k[(k.tyyp == "maantee") & k[f"{tp}_kiirus_tingimus"]]
    print(f"  {tp}: " + "; ".join(f"{r.koht} {getattr(r, f'{tp}_algus')}-{getattr(r, f'{tp}_lopp')} "
                                  f"({getattr(r, f'{tp}_tipu_kiirus_kmh'):.0f} vs {getattr(r, f'{tp}_tavakiirus_kmh'):.0f} km/h)"
                                  for r in z.itertuples()))
