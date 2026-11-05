"""
40_0 - Murdepunkt: kui suur osa autodest peab tipust ära minema (ühistransporti või pool varem, pool hiljem), et
ristmikel oleks liiklus märgatavalt kiirem - rohkem, kui see niigi päevast päeva kõigub. Kaks mudelit: A = foori
viivitus -> kiirus, B = ummikuosa sõidukipõhistest loendustest; kontroll maanteeloendurite mõõdetud kiirusega.

SISEND
  common.tooaeva_profiilid()     ristmike 15 min loendused (import_raw.traffic_15min_tallinn): tavalised tööpäevad
                                 (E-R, õppetöö, mitte püha ega lühendatud päev) 01.09.2025 kuni andmete lõpuni
  common.mudeli_parameetrid()    mudelite parameetrid skriptide 09, 24, 27 ja 33 tabelitest (vt allpool)
  common.maantee_suunad()        maanteeloendurite 15 min loendused ja kiirused (kontroll)

ARVUTUS
  Mudel A (viivitus): koormusaste X = 4 x 15 min voog / C (C = ristmiku eeldatav piir, 27). Foori viivitus sõiduki kohta
    HCM 2010 valemiga (common.hcm_viivitus): ühtlane osa (punane tuli, tsükli pikkus 09 ja g/C 33 järgi) + juhuslik ja
    üleküllastuse osa (raja läbilaskevõime c = küllastusvoog x g/C, 33). Kiirus = LOIK_M (500 m) lõigu kiirus, kui
    vaba kiirusega (50 km/h) sõidule lisandub viivitus. Halvim tund = sõidukitega kaalutud tunnikeskmise suurim
    viivitus (tunni algus hommikul 06:00-09:45, õhtul 14:00-18:45).
  Mudel B (ummikuosa): logija nädala (16., 19.-23.10.2026) 15 min piludest seos voog -> täis või seisakus kanalite osa
    ristmiku täistasemest (24; täis = kanal laseb läbi >= 80% oma tavalisest päeva suurimast voost, seisak = loendur
    kaetud, aga läbi pääseb vähe), kasvav monotoonne regressioon (common.pav). Voog on tavalise tipptunni ühikutes
    (logija nädalal ja T09 2026. a sügisel eraldi), nii saab seose kanda ajaloolistele päevadele. Halvim tund =
    tunnikeskmise suurim ummikuosa.
  Stsenaariumid (osakaal p = 1...30%):
    yt       p kõigist autodest kaob kogu päevaks (läheb ühistransporti)
    nihe30   p iga päeva tipptunni autodest nihkub: pool 30 min varem, pool 30 min hiljem (muu liiklus paigal)
    nihe60   sama 60 min
  Võit päeva kohta: A = halvima tunni kiiruse kasv, %; B = halvima tunni ummikuosa vähenemine, protsendipunkti.
    Ristmiku võit = päevade mediaan. Linn = kõik ristmikud koos (A: sõidukitega kaalutud viivitus, B: täistasemega
    kaalutud ummikuosa), kindel valim: ristmikud, millel on mõlemad mudelid ja vähemalt 85% päevadest.
  Päevast päeva kõikumine (common.paeva_mura): halvima tunni väärtus võrreldes 21 päeva liikuva mediaaniga;
    A: kerge (90. protsentiili) päev on nii palju kiirem kui tavaline (mediaan); B: kerge (10. protsentiili) päeval on
    ummikuosa nii palju väiksem. Märgatav = võit >= kõikumine ja vähemalt STS_MIN_VOIT (1% või 1 pp, et ka peaaegu
    kõikumiseta kohas ei loetaks märgatavaks tühist muutust): muutus on suurem kui tavaline erinevus kahe päeva vahel. Murdepunkt = vähim p, mille juures võit on märgatav. Kõikumine sisaldab ainult voost tulenevat osa
    (ilm, õnnetused ja foorikava muudatused lisaksid veel); maanteekontroll näitab, kui palju mõõdetud kõikumine on
    suurem.
  Maanteekontroll: 7 sissesõiduteed (nagu 27, 32), linna poole suund hommikul ja linnast välja õhtul, mõõdetud
    keskmine kiirus 15 min kaupa. Seos voog -> kiirus = kahanev monotoonne regressioon; halvim tund = madalaima
    kiirusega tund. Kõikumine nii mõõdetud kiirusest kui ka voost (seose järgi); yt murdepunkt mõlema järgi. Välja
    jäävad 15 min, kus voog on üle 600 sõiduki raja kohta (loenduri viga), ja päevad, kus 06-20 on mõni pilu puudu
    (Viljandi mnt Kangru loenduril pole alates 09.2025 ühtegi täielikku tööpäeva).

VÄLJUND (kaust valjund/)
  40_0_01_murdepunkt.png
      Näitab: kui suur osa autodest peab kaduma või nihkuma, et linna ristmikel halvim tund oleks märgatavalt kiirem
      (A) või vähem ummikus (B), ja kus on murdepunkt.
      Kuidas: 2 x 2 paneeli; rida = mudel (A kiiruse kasv %, B ummikuosa vähenemine protsendipunktides), veerg =
      hommik, õhtu. x = autode osakaal, %; joon = stsenaarium (sinine = ühistransport, oranž = pool 60 min varem / pool
      hiljem, roheline katkendjoon = sama 30 min). Hall vöönd kuni katkendjooneni = päevast päeva kõikumine (kerge päev
      vs tavaline päev, väärtus paneeli pealkirjas): selle sees muutust ei märka. Punkt ja number = murdepunkt (vähim
      %, mille juures joon ületab kõikumise).
  40_0_02_ristmikud.png
      Näitab: iga ristmiku murdepunkt ühistranspordi stsenaariumis kummagi mudeli järgi - kas A ja B annavad sama vastuse.
      Kuidas: kaks paneeli (hommik, õhtu); rida = ristmik (järjestatud A hommikuse murdepunkti järgi); sinine ring =
      A, oranž romb = B; "> 30" (hall veerg, ainult kui vaja) = ei ole märgatav ka 30% juures. Paksus kirjas = 27
      järgi küllastunud ristmik.
  40_0_03_maanteed.png
      Näitab: mõõdetud kiirusega kontroll - kas sissesõiduteedel kiirus sõltub voost ja kui palju mõõdetud kiirus päevast
      päeva kõigub võrreldes sellega, mida voog üksi seletab.
      Kuidas: paneel = sissesõidutee linna poole hommikul; hall punkt = 15 min (x = voog, sõid/h; y = keskmine kiirus);
      sinine joon = seos; püstjoon = tavaline hommikune tipptund. Tekstis kõikumine (mõõdetud / voost) ja murdepunkt
      (mõõdetud / voost tuleneva kõikumise järgi).
      Viimane paneel: kõikumine kõigil teedel ja suundadel (tulp = mõõdetud, punkt = voost).
  40_0_murdepunkt.csv    linn: mudel, tipp, stsenaarium, p, võit, kõikumine, märgatav
  40_0_ristmikud.csv     ristmik, mudel, tipp, stsenaarium: kõikumine, murdepunkt, võit murdepunktis, halvim tund enne
                         ja pärast (A: viivitus s ja kiirus km/h; B: ummikuosa %), 27 olek
  40_0_mudel.csv         ristmiku mudeli parameetrid: C, tsükkel, g/C, s, c rajal; B seose punkte, Qref, ummikuosa
                         tavalise tipptunni voo juures
  40_0_maanteed.csv      maantee suund ja tipp: päevi, vaba ja tipu kiirus, kõikumine (mõõdetud, voost), murdepunktid
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import (sts_andmed, sts_naitajad, sts_voit, kiirus_viivitusest, tunni_keskmine, stsenaarium, paeva_mura,
                    hcm_viivitus, pav, maantee_suunad, load_junctions, short_name, set_style, save, save_table, STS_ALGUS,
                    STS_AKNAD, STS_MIN_VOIT, C_BLUE, C_ORANGE, C_AQUA, C_GRAY, TEXT, TEXT2, GRID)

OSAKAAL = np.arange(1, 31)                                     # %
STSEN = {"yt": ("ühistransport (kaob)", "yt", 0), "nihe60": ("pool 60 min varem, pool hiljem", "nihe", 60),
         "nihe30": ("pool 30 min varem, pool hiljem", "nihe", 30)}
STIIL = {"yt": dict(color=C_BLUE, ls="-"), "nihe60": dict(color=C_ORANGE, ls="-"), "nihe30": dict(color=C_AQUA, ls="--")}
MUDEL = {"A": "A: halvima tunni kiiruse kasv, %", "B": "B: halvima tunni ummikuosa vähenemine, protsendipunkti"}
TIPP_TXT = {"hommik": "hommik", "ohtu": "õhtu"}
RADA_MAX = 600                                                 # maantee: üle 600 sõiduki raja kohta 15 min = viga
MAANTEED = [("Peterburi tee (Loo)", "0cfcf | narva - tallinn"), ("Tartu mnt", "0f55c | tartu - tallinn"),
            ("Pärnu mnt (Laagri)", "8560b | peoleo - tallinn"), ("Viljandi mnt (Kangru)", "1d86e | rapla - tallinn"),
            ("Paldiski mnt", "1cf12 | paldiski - tallinn"), ("Rannamõisa tee", "36408 | rannamoisa - tallinn"),
            ("Randvere tee (Viimsi)", "d2421 | randvere - viimsi")]
tagurpidi = lambda site: site.split(" | ")[0] + " | " + " - ".join(site.split(" | ")[1].split(" - ")[::-1])

# HCM valem käsitsi: X = 1, C = 90 s, g/C = 0,28, c = 509 -> d1 = 32,4 s, d2 = 39,9 s
assert abs(hcm_viivitus(1.0, 90, 0.28, 509) - 72.29) < 0.01
assert np.allclose(pav([1, 2, 3, 4], [1, 3, 2, 4])[1], [1, 2.5, 4])

set_style()
jn = load_junctions().set_index("mp_id")
a = sts_andmed()
pa, sb, ix, V, qref = a["pa"], a["sb"], a["ix"], a["V"], a["qref"]
paevad, taisi = a["paevad"], a["taisi"]
print(f"profiile {len(ix)}, päevi {ix['paev'].nunique()}, ristmikke {ix['mp_id'].nunique()} (B seos {len(sb)}), "
      f"linna valim {len(a['paneel'])} ristmikku, {taisi.sum()} päeva")


def murdepunkt(p, g, mura):
    """Vähim osakaal, mille juures võit on märgatav (>= kõikumine ja >= STS_MIN_VOIT); NaN, kui ei ole ka 30% juures."""
    ok = np.asarray(g) >= max(mura, STS_MIN_VOIT)
    return float(np.asarray(p)[ok][0]) if ok.any() else np.nan


rows_l, rows_r, rows_m = [], [], []
for tipp, aken in STS_AKNAD.items():
    alg = sts_naitajad(a, V, aken)
    mura = {}
    for m in "AB":                                  # A: kiirus (suurem parem, %), B: ummikuosa (väiksem parem, pp)
        suund, kord = ("suurem", 100) if m == "A" else ("vaiksem", 1)
        x = kiirus_viivitusest(alg[m]) if m == "A" else alg[m]
        mura[m] = pd.Series({mp: kord * paeva_mura(ix.loc[r, "paev"], x[r], suund)
                             for mp, r in ix.groupby("mp_id").indices.items() if np.isfinite(x[r]).sum() >= 40})
        xl = kiirus_viivitusest(alg[f"linn{m}"]) if m == "A" else alg[f"linn{m}"]
        mura[f"linn{m}"] = kord * paeva_mura(paevad[taisi], xl[taisi], suund)
    for sk, (_, tyyp, nihe) in STSEN.items():
        for p in OSAKAAL:
            uus = sts_naitajad(a, stsenaarium(V, tyyp, p / 100, aken, nihe), aken)
            for m in "AB":
                g = sts_voit(m, alg[f"linn{m}"][taisi], uus[f"linn{m}"][taisi])
                rows_l.append(dict(mudel=m, tipp=tipp, stsenaarium=sk, p=p, voit=np.nanmedian(g),
                                   koikumine=mura[f"linn{m}"]))
                g = pd.DataFrame(dict(mp_id=ix["mp_id"], g=sts_voit(m, alg[m], uus[m]), alg=alg[m], uus=uus[m]))
                g = g.groupby("mp_id").median()
                rows_m.append(g.assign(mudel=m, tipp=tipp, stsenaarium=sk, p=p).reset_index())
    for m in "AB":
        rows_r.append(pd.DataFrame(dict(mp_id=mura[m].index, koikumine=mura[m].values)).assign(mudel=m, tipp=tipp))
ll = pd.DataFrame(rows_l)
ll["margatav"] = ll["voit"] >= np.maximum(ll["koikumine"], STS_MIN_VOIT)
save_table(ll.round(3), "40_0_murdepunkt")

rm = pd.concat(rows_m, ignore_index=True).merge(pd.concat(rows_r, ignore_index=True), on=["mp_id", "mudel", "tipp"])
rm = rm[rm["mp_id"].isin(pa.index)]
rr = []
for (mp, m, tipp, sk), g in rm.groupby(["mp_id", "mudel", "tipp", "stsenaarium"]):
    g = g.sort_values("p")
    mp_ = murdepunkt(g["p"], g["g"], g["koikumine"].iloc[0])
    r = g[g["p"] == mp_].iloc[0] if np.isfinite(mp_) else g.iloc[-1]
    rr.append(dict(mp_id=mp, kood=pa.loc[mp, "kood"], mudel=m, tipp=tipp, stsenaarium=sk, olek=pa.loc[mp, "olek"],
                   koikumine=g["koikumine"].iloc[0], murdepunkt_pct=mp_, voit_murdepunktis=r["g"] if np.isfinite(mp_)
                   else np.nan, halvim_enne=r["alg"], halvim_parast=r["uus"], voit_30pct=g["g"].iloc[-1]))
rr = pd.DataFrame(rr)
rr.loc[rr["mudel"] == "A", "kiirus_enne_kmh"] = kiirus_viivitusest(rr.loc[rr["mudel"] == "A", "halvim_enne"])
rr.loc[rr["mudel"] == "A", "kiirus_parast_kmh"] = kiirus_viivitusest(rr.loc[rr["mudel"] == "A", "halvim_parast"])
save_table(rr.round(3), "40_0_ristmikud")

mudel = pa.copy()
mudel["B_punkte"] = pd.Series({m: s["punkte"] for m, s in sb.items()})
mudel["B_qref_logija"] = pd.Series({m: s["qref"] for m, s in sb.items()})
mudel["qref_T09"] = pd.Series(qref)
mudel["B_ummikuosa_tipul"] = pd.Series({m: float(np.interp(1, s["xk"], s["yk"])) for m, s in sb.items()})
save_table(mudel.reset_index().round(3), "40_0_mudel")

# --- maanteekontroll --------------------------------------------------------------------------------------------------
ds, dq = maantee_suunad(STS_ALGUS)
dq = dq[dq["toopaev"]]
rows_h, fitid = [], {}
for nimi, site0 in MAANTEED:
    for tipp, site in [("hommik", site0), ("ohtu", tagurpidi(site0))]:
        g = dq[dq["site"] == site]
        if g.empty:
            continue
        P = {c: g.pivot_table(index="paev", columns="slot", values=c, aggfunc="sum").reindex(columns=range(96))
             for c in ["c", "ks", "kn", "n"]}
        ok = P["c"].iloc[:, 24:80].notna().all(axis=1) & (P["kn"].iloc[:, 24:80] > 0).all(axis=1)
        if ok.sum() < 40:
            continue
        C, KS, KN, N = (P[c][ok].fillna(0).to_numpy() for c in ["c", "ks", "kn", "n"])
        S = np.where(KN > 0, KS / np.where(KN > 0, KN, 1), np.nan)
        sel = (KN[:, 24:80] >= 10) & (C[:, 24:80] <= RADA_MAX * np.maximum(N[:, 24:80], 1))
        xk, yk = pav(C[:, 24:80][sel], S[:, 24:80][sel], kasvav=False)
        lo, hi = STS_AKNAD[tipp][0] * 4, STS_AKNAD[tipp][1] * 4
        moodet = tunni_keskmine(np.nan_to_num(S), KN)[:, lo:hi].min(axis=1)
        enn = lambda Cx: tunni_keskmine(np.interp(Cx, xk, yk), Cx)[:, lo:hi].min(axis=1)
        e0 = enn(C)
        d = P["c"][ok].index
        mu_m, mu_v = 100 * paeva_mura(d, moodet, "suurem"), 100 * paeva_mura(d, e0, "suurem")
        gv = [np.nanmedian(100 * (enn(C * (1 - p / 100)) / e0 - 1)) for p in OSAKAAL]
        tipp_voog = np.median(4 * tunni_keskmine(C)[:, lo:hi].max(axis=1))
        rows_h.append(dict(tee=nimi, site=site, tipp=tipp, paevi=int(ok.sum()), vaba_kiirus=yk[0], kiirus_tipul=float(
            np.interp(tipp_voog / 4, xk, yk)), tipp_voog_h=tipp_voog, koikumine_moodetud=mu_m, koikumine_voost=mu_v,
            murdepunkt_voost=murdepunkt(OSAKAAL, gv, mu_v), murdepunkt_moodetud=murdepunkt(OSAKAAL, gv, mu_m),
            voit_30pct=gv[-1]))
        if tipp == "hommik":
            fitid[nimi] = (C[:, 24:80][sel] * 4, S[:, 24:80][sel], xk * 4, yk, tipp_voog)
mh = pd.DataFrame(rows_h)
save_table(mh.round(3), "40_0_maanteed")

# --- joonis 1: linn ----------------------------------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 9.5), sharex=True)
for i, m in enumerate("AB"):
    for j, tipp in enumerate(STS_AKNAD):
        ax = axes[i, j]
        z = ll[(ll["mudel"] == m) & (ll["tipp"] == tipp)]
        mu = z["koikumine"].iloc[0]
        ax.axhspan(0, mu, color=GRID, alpha=0.55, lw=0, label="päevast päeva kõikumine (ei märka)")
        ax.axhline(mu, color=TEXT2, ls=(0, (4, 3)), lw=1.2)
        for sk, (dx, dy, ha) in zip(STSEN, [(-6, 7, "right"), (7, -13, "left"), (0, 9, "center")]):
            y = z[z["stsenaarium"] == sk].sort_values("p")
            ax.plot(np.r_[0, y["p"]], np.r_[0, y["voit"]], lw=2.2, label=STSEN[sk][0], **STIIL[sk])
            b = murdepunkt(y["p"], y["voit"], mu)
            if np.isfinite(b):
                yb = y.loc[y["p"] == b, "voit"].iloc[0]
                ax.plot(b, yb, "o", color=STIIL[sk]["color"], ms=8, mec="white", mew=1.5, zorder=5)
                ax.annotate(f"{b:.0f}%", (b, yb), xytext=(dx, dy), textcoords="offset points", ha=ha,
                            fontsize=9.5, fontweight="bold", color=TEXT,
                            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))
        ax.set_xlim(0, 30.5)
        ax.set_ylim(bottom=0)
        ax.set_title(f"{MUDEL[m].split(':')[0]}: {TIPP_TXT[tipp]} (kõikumine {mu:.1f}".replace(".", ",")
                     + (" %)" if m == "A" else " pp)"), fontsize=11)
        ax.set_ylabel(MUDEL[m].split(": ")[1])
        if i == 1:
            ax.set_xlabel("autode osakaal, mis kaob (ühistransport) või nihkub tipptunnist, %")
axes[0, 0].legend(fontsize=9, loc="upper left")
fig.suptitle(f"Murdepunkt: mitu % autodest peab tipust ära minema, et linna ristmikel oleks märgatavalt kiirem "
             f"({len(a['paneel'])} ristmikku, {taisi.sum()} tööpäeva {paevad.min():%d.%m.%Y}-{paevad.max():%d.%m.%Y})",
             x=0.01, ha="left", fontweight="bold", fontsize=12)
fig.tight_layout()
save(fig, "40_0_01_murdepunkt")

# --- joonis 2: ristmikud (yt) ------------------------------------------------------------------------------------------
YLE = 33
z = rr[rr["stsenaarium"] == "yt"].copy()
z["x"] = z["murdepunkt_pct"].fillna(YLE)
jarj = (z[(z["mudel"] == "A") & (z["tipp"] == "hommik")].set_index("mp_id")["x"]
        .add(z[(z["mudel"] == "B") & (z["tipp"] == "hommik")].set_index("mp_id")["x"] / 100, fill_value=0)
        .sort_values(ascending=False).index)
pos = {mp: k for k, mp in enumerate(jarj)}
fig, axes = plt.subplots(1, 2, figsize=(13, 0.27 * len(jarj) + 2), sharey=True)
for ax, tipp in zip(axes, STS_AKNAD):
    for m, mk, c, dy in [("A", "o", C_BLUE, -0.17), ("B", "D", C_ORANGE, 0.17)]:
        q = z[(z["mudel"] == m) & (z["tipp"] == tipp) & z["mp_id"].isin(pos)]
        ax.scatter(q["x"], q["mp_id"].map(pos) + dy, marker=mk, s=34, color=c, edgecolor="white", lw=0.6, zorder=3,
                   label={"A": "A: viivitus -> kiirus", "B": "B: ummikuosa"}[m])
    if z["murdepunkt_pct"].isna().any():
        ax.axvspan(31, 35, color=GRID, alpha=0.6, lw=0)
        ax.set_xlim(0, 35)
        ax.set_xticks(list(range(0, 31, 5)) + [YLE], [str(k) for k in range(0, 31, 5)] + ["> 30"])
    else:
        ax.set_xlim(0, z["murdepunkt_pct"].max() + 2)
    ax.set_title(f"{TIPP_TXT[tipp].capitalize()}", fontsize=11)
    ax.set_xlabel("murdepunkt: autode osakaal, mis peab kaduma, %")
axes[0].set_yticks(range(len(jarj)))
axes[0].set_yticklabels([f"{pa.loc[mp, 'kood']} {short_name(jn.loc[mp, 'name'], 30, compact=True)}" for mp in jarj],
                        fontsize=7.5)
for lab, mp in zip(axes[0].get_yticklabels(), jarj):
    if pa.loc[mp, "olek"] == "küllastunud":
        lab.set_fontweight("bold")
axes[0].set_ylim(-0.7, len(jarj) - 0.3)
axes[1].legend(fontsize=9, loc="lower right")
fig.suptitle("Ristmike murdepunkt, kui autod lähevad ühistransporti: A (viivitus) ja B (ummikuosa); paksus kirjas = "
             "küllastunud ristmik (27)", x=0.01, ha="left", fontweight="bold", fontsize=11.5)
fig.tight_layout()
save(fig, "40_0_02_ristmikud")

# --- joonis 3: maanteed ------------------------------------------------------------------------------------------------
fig, axes = plt.subplots(2, 4, figsize=(17, 8.5))
for ax in axes.flat[len(fitid):-1]:
    ax.axis("off")
for ax, nimi in zip(axes.flat, fitid):
    x, y, xk, yk, tv = fitid[nimi]
    ax.scatter(x, y, s=2, color=C_GRAY, alpha=0.12, lw=0, rasterized=True)
    xg = np.linspace(x.min(), np.percentile(x, 99.9), 300)
    ax.plot(xg, np.interp(xg, xk, yk), color=C_BLUE, lw=2.2)
    ax.set_xlim(0, np.percentile(x, 99.9) * 1.04)
    ax.axvline(tv, color=TEXT2, ls=":", lw=1.2)
    r = mh[(mh["tee"] == nimi) & (mh["tipp"] == "hommik")].iloc[0]
    f = lambda v: "> 30%" if not np.isfinite(v) else f"{v:.0f}%"
    ax.text(0.03, 0.04, f"kõikumine: mõõdetud {r.koikumine_moodetud:.1f}%, voost {r.koikumine_voost:.1f}%\n"
                        f"murdepunkt: {f(r.murdepunkt_moodetud)} / {f(r.murdepunkt_voost)}".replace(".", ","),
            transform=ax.transAxes, fontsize=8, va="bottom", color=TEXT,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=GRID, alpha=0.9))
    ax.set_title(f"{nimi}, linna poole hommikul", fontsize=10)
    ax.set_xlabel("voog, sõid/h")
    ax.set_ylabel("keskmine kiirus, km/h")
    ax.set_ylim(0, max(130, np.nanpercentile(y, 99.5)))
ax = axes.flat[-1]
k = mh.assign(silt=mh["tee"].str.replace(r" \(.*\)", "", regex=True) + " " + mh["tipp"].map({"hommik": "h", "ohtu": "õ"}))
yy = np.arange(len(k))
ax.barh(yy, k["koikumine_moodetud"], color=C_BLUE, alpha=0.75, height=0.6, label="mõõdetud kiirus")
ax.plot(k["koikumine_voost"], yy, "o", color=C_ORANGE, ms=6, label="ainult voost (seose järgi)")
ax.set_yticks(yy, k["silt"], fontsize=7.5)
ax.invert_yaxis()
ax.set_xlabel("päevast päeva kõikumine, % (kerge päev vs tavaline)")
ax.set_title("Kõikumine: h = hommik linna, õ = õhtu välja", fontsize=10)
ax.legend(fontsize=8, loc="center right")
fig.suptitle("Kontroll mõõdetud kiirusega: sissesõiduteede voog ja kiirus (15 min, tööpäevad alates 01.09.2025); "
             "murdepunkt mõõdetud / voost tuleneva kõikumise järgi", x=0.01, ha="left", fontweight="bold", fontsize=11.5)
fig.tight_layout()
save(fig, "40_0_03_maanteed")

for (m, tipp), g in ll.groupby(["mudel", "tipp"]):
    print(f"{m} {tipp}: kõikumine {g['koikumine'].iloc[0]:.2f}; murdepunkt " + ", ".join(
        f"{sk} {murdepunkt(h['p'], h['voit'], h['koikumine'].iloc[0])}" for sk, h in g.groupby("stsenaarium")))
print(rr[rr["stsenaarium"] == "yt"].groupby(["mudel", "tipp"])["murdepunkt_pct"]
      .describe(percentiles=[0.25, 0.5, 0.75]).round(1).to_string())
print(mh[["tee", "tipp", "kiirus_tipul", "koikumine_moodetud", "koikumine_voost", "murdepunkt_moodetud",
          "murdepunkt_voost", "voit_30pct"]].round(2).to_string(index=False))
