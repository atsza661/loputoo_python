"""
12 - Kaks loomulikku katset ristmike 15 min loendustest: A) koolipäeva alguse nihutamine kella 9-le ja B) "väike langus,
suur võit" - kui palju lüheneb täistasemel oldud aeg, kui liiklust on veidi vähem.

SISEND
  common.load_tallinn()                  ristmike 15 min loendused puhastatult, päevatüübi ja koolivaheaja märkega
                                         (alati kõik suunad koos)
  common.load_junctions()                ristmike koodid ja nimed
  valjund/09_ummikud.csv, 09_tsuklid.csv skripti 09 ummikud ja tsüklid (millistel ristmikel on stabiilne ummik;
                                         kalibreerimine) - 09 käib enne
  valjund/06_hajutamine_ristmikud.csv    skripti 06 hajutamisstsenaariumid (võrdlusjooned)
  common.load_vehicles(None, koik=True)  sõidukipõhised päevad kalibreerimiseks

A) KOOLIPÄEVA ALGUS
  Varem algas kool 07:45...09:00, alates 1.09.2026 kõikjal kell 9. Võrreldakse sama septembriakent (3.-20.09, tööpäevad;
  aktusepäevad välja; nädalapäevad võrdse kaaluga) aastatel 2024, 2025 ja 2026. Paar "2026 vs 2025" on koolialguse
  muutus, "2025 vs 2024" näitab võrdluseks eelmise aasta muutust.
    toores vahe = 15 min pilu liikluse muutus, %
    puhas vahe  = toores vahe - sama ristmiku ööpäeva liikluse muutus samas aknas (protsendipunkti) ehk kuidas muutus
                  liikluse jaotus päeva sees, kui üldine aastane kasv või langus on maha arvatud
  Ristmik, mille ööpäeva liiklus muutus üle 15% (teetööd, ümbersõidud), jääb selle paari mediaanidest välja. Tulemus =
  mediaan üle ristmike ja mediaani 95% usaldusvahemik (bootstrap); ristmiku näitajatel (tipu algus, keskaeg, tipptunni
  maht, osakaal ööpäevast 06:00-07:30, 07:30-08:30 ja 08:30-09:30, aeg täistasemel) lisaks Wilcoxoni p.
  12_01_koolialgus.png
      Näitab: kas ja mis kellaajal hommikune liiklus pärast muudatust nihkus.
      Kuidas: 2 x 2 paneeli. Ülal vasakul hommikune liiklus septembris, tuhat sõidukit 15 min kohta (kõik ühised
      ristmikud kokku): hall = 2024, sinine = 2025, oranž = 2026; ülal paremal sama osakaaluna ööpäevast (aastane kasv
      maha arvatud). Hall vöönd = kooli algus varem 07:45-09:00, katkendjoon = kell 9. All vasakul toores vahe ja all
      paremal puhas vahe 15 min pilude kaupa kell 5-20: oranžid tulbad = 2026 vs 2025 (vurrud = 95% usaldusvahemik),
      sinine astmeline joon = 2025 vs 2024 võrdluseks.
  12_02_koolialgus_ristmikud.png
      Näitab: millistel ristmikel liikluse jaotus muutus.
      Kuidas: kaks soojuskaarti kõrvuti (2025 vs 2024 võrdluseks; 2026 vs 2025 koolialguse muutus). Rida = ristmik
      (järjestatud puhta vahe järgi kell 08:30-09:30), veerg = 15 min pilu 06:00-10:00. Värv = puhas vahe,
      protsendipunkti (sinine = vähem, punane = rohkem, skaala +-15); valge = ristmik selles paaris välja jäetud.
  12_koolialgus_pilud.csv, 12_koolialgus_naitajad.csv, 12_koolialgus_kokkuvote.csv

B) VÄIKE LANGUS, SUUR VÕIT
  Iga ristmiku iga tööpäeva (õppetöö ja lühikesed koolivaheajad) hommiku (06-11) ja õhtu (14-20) kohta:
    täistase          = päeva suurima 15 min loenduse kohalik tavaväärtus (õppetöö-päevade libisev mediaan, 31 päeva;
                        kohalik, sest teetööd muudavad ristmiku taset)
    aeg täistasemel   = minutid, mil 15 min loendus >= 90% täistasemest (ristmiku summa oma näitaja, mitte 09 ummik)
    liikluse indeks   = tipuakna liiklus / selle kohalik tavaväärtus x 100; tipptunni indeks samamoodi
  1) kõver: keskmine aeg täistasemel indeksi 2,5% vahemike kaupa (päevadevaheline loomulik kõikumine; vahemik arvesse
     alates 50 päevast)
  2) lühikesed koolivaheajad vs 2 nädalat enne ja pärast: liiklus -x% -> aeg täistasemel -y%
  3) 06 hajutamisstsenaariumide tipptunni vähenemine samal kõveral (tipptunni indeks)
  4) kalibreerimine sõidukipõhiste päevadega: aeg täistasemel vs täis tsüklites liikunud sõidukite aeg (09), Spearmani
     rho
  Põhitulemus on ristmike ja tippude kohta, kus 09 leidis stabiilse ummiku vähemalt pooltel tööpäevadel ("ummikuga");
  teised ei pruugi täistasemel üldse küllastuda.
  12_03_vaike_muutus.png
      Näitab: kui tundlik on täistasemel oldud aeg liikluse väikese muutuse suhtes.
      Kuidas: 2 x 2 paneeli. Ülal vasakul kõver: x = tipuakna liiklus, % tavalisest (100 = tavaline õppetöö-tööpäev),
      y = aeg täistasemel, min päevas; sinine = hommik, oranž = õhtu, vari = 95% usaldusvahemik, romb = koolivaheaja
      päevade keskmine. All vasakul sama tipptunni mahu järgi; püstjooned = 06 hajutamisstsenaariumid. Ülal paremal
      tulbad iga lühikese koolivaheaja kohta (hommik): hall = tipuakna liikluse muutus, %, sinine = täistasemel oldud
      aja muutus, %. All paremal kalibreerimine: punkt = ristmik ja tipp ühel päeval, x = aeg täistasemel (15 min
      loendus), y = aeg täis tsüklites (09); suur punkt = stabiilse ummikuga ristmik.
  12_taistase_paevad.csv, 12_vaike_muutus_kover.csv, 12_vaheajad_taistase.csv, 12_kalibreerimine.csv
  ponytail: "aeg täistasemel" tuleb ristmiku summaarsest loendusest, mitte järjekorrast - see on ummiku asendusnäitaja
  (kalibreerimine näitab, kui hea) ja seos on vaatluslik, mitte järjekorramudel. Täpsem oleks manöövripõhine tsüklite
  analüüs (09) mitme nädala kohta.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from common import (load_tallinn, load_junctions, load_vehicles, peak_metrics, mediaani_uv, short_name, slot_label,
                    set_style, save, save_table, OUT_DIR, DIVERGING, C_BLUE, C_ORANGE, C_AQUA, C_GRAY, TEXT2)

AKEN = (3, 20)                              # septembri päevad (1.-2.09 aktus; 2026. a andmed lõpevad 20.09)
PAARID = [(2025, 2024), (2026, 2025)]       # (aasta, võrdlusaasta); viimane paar = koolialguse muutus
KASV_MAX = 15                               # ristmik välja, kui ööpäeva liiklus muutus üle +-15%
TIPUD = {"hommik": (6, 11), "õhtu": (14, 20)}    # nagu 09
TAIS = 0.9                                  # täistasemel = loendus >= 90% täistasemest
VIIDE_PAEVI = 31                            # kohaliku tavaväärtuse libisev aken, õppetöö-päeva
SAMM = 2.5                                  # indeksi vahemiku laius kõveral, %
VARV = {"hommik": C_BLUE, "õhtu": C_ORANGE}
AASTA_VARV = {2024: C_GRAY, 2025: C_BLUE, 2026: C_ORANGE}
loe = lambda nimi, **kw: pd.read_csv(OUT_DIR / f"{nimi}.csv", encoding="utf-8-sig", **kw)


def taistase_min(v, tase, aken=TIPUD["hommik"]):
    """Minutid aknas, mil 15 min loendus >= tase."""
    return int((np.asarray(v)[aken[0] * 4:aken[1] * 4] >= tase).sum() * 15)


def kokkuvote(x):
    """Mediaan, selle 95% usaldusvahemik ja Wilcoxoni p (erineb nullist)."""
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    uv = mediaani_uv(x)
    return dict(n=len(x), mediaan=np.median(x), uv_alumine=uv[0], uv_ylemine=uv[1],
                p=stats.wilcoxon(x).pvalue if (x != 0).any() else 1.0)


assert taistase_min(np.r_[np.zeros(24), [5, 9, 10, 9, 5], np.zeros(67)], 9) == 45
assert kokkuvote([1, 2, 3, 4, 5, 6, 7, 8])["p"] < 0.05 and kokkuvote([0, 0])["p"] == 1

set_style()
print("Laen Tallinna ristmike andmeid...")
t, day = load_tallinn()
j = load_junctions().set_index("mp_id")
too = t[t["paevatyyp"] == "tööpäev"]

# === A) Koolipäeva algus ================================================================================
sep = too[(too["paev"].dt.month == 9) & too["paev"].dt.day.between(*AKEN)]
aasta = sep["paev"].dt.year.rename("aasta")
P = (sep.groupby([aasta, "mp_id", "nadalapaev", "slot"])["v"].mean()
     .groupby(["aasta", "mp_id", "slot"]).mean().unstack("slot").dropna())        # ainult täielikud profiilid
print("A) Koolialgus: tööpäevi aknas " + ", ".join(f"{a}: {n}" for a, n in sep.groupby(aasta)["paev"].nunique().items()))

PILUD = range(22, 80)                       # 05:30-20:00 (öösel on loendused väikesed ja suhted mürased)
pilud, nait, puhas_paar, toores_paar = [], [], {}, {}
for a, b in PAARID:
    paar = f"{a} vs {b}"
    ids = P.loc[a].index.intersection(P.loc[b].index)
    A, B = P.loc[a].loc[ids], P.loc[b].loc[ids]
    kasv = (A.sum(axis=1) / B.sum(axis=1) - 1) * 100
    ok = kasv.index[kasv.abs() <= KASV_MAX]
    toores = (A.loc[ok] / B.loc[ok] - 1) * 100
    puhas = toores.sub(kasv[ok], axis=0)
    toores_paar[paar], puhas_paar[paar] = toores, puhas
    valjas = ", ".join(f"{j.at[m, 'code']} {kasv[m]:+.0f}%" for m in kasv.index.difference(ok)) or "-"
    print(f"   {paar}: {len(ok)} ristmikku, ööpäeva liiklus {kasv[ok].median():+.1f}% (mediaan); välja jäid (muutus üle "
          f"{KASV_MAX}%): {valjas}")
    for s in PILUD:
        ut, up = mediaani_uv(toores[s]), mediaani_uv(puhas[s])
        pilud.append(dict(paar=paar, kell=slot_label(s), slot=s, ristmikke=len(ok), soidukeid=A.loc[ok, s].sum(),
                          soidukeid_vordlus=B.loc[ok, s].sum(), toores_mediaan=toores[s].median(), toores_uv_alumine=ut[0],
                          toores_uv_ylemine=ut[1], puhas_mediaan=puhas[s].median(), puhas_uv_alumine=up[0],
                          puhas_uv_ylemine=up[1], kasvas_ristmikel_pct=(puhas[s] > 0).mean() * 100))
    for mp in ok:
        va, vb = A.loc[mp].values, B.loc[mp].values
        ma, mb = peak_metrics(va, per_hour=4), peak_metrics(vb, per_hour=4)
        osa = lambda v, x, y: v[int(x * 4):int(y * 4)].sum() / v.sum() * 100
        tase = TAIS * vb[TIPUD["hommik"][0] * 4:TIPUD["hommik"][1] * 4].max()
        tipp = (ma["hommik_soid_h"] / mb["hommik_soid_h"] - 1) * 100
        nait.append({"paar": paar, "mp_id": mp, "kasv_%": kasv[mp],
                     "tipu_algus_min": (ma["hommik_algus_h"] - mb["hommik_algus_h"]) * 60,
                     "keskaeg_min": (ma["hommik_keskaeg_h"] - mb["hommik_keskaeg_h"]) * 60,
                     "tipptund_toores_%": tipp, "tipptund_puhas_pp": tipp - kasv[mp],
                     "osa_0600_0730_pp": osa(va, 6, 7.5) - osa(vb, 6, 7.5),
                     "osa_0730_0830_pp": osa(va, 7.5, 8.5) - osa(vb, 7.5, 8.5),
                     "osa_0830_0930_pp": osa(va, 8.5, 9.5) - osa(vb, 8.5, 9.5),
                     "taistasemel_toores_min": taistase_min(va, tase) - taistase_min(vb, tase),
                     "taistasemel_puhas_min": taistase_min(va / (1 + kasv[mp] / 100), tase) - taistase_min(vb, tase)})
pilud, nait = pd.DataFrame(pilud), pd.DataFrame(nait)
save_table(pilud.drop(columns="slot").round(2), "12_koolialgus_pilud")
save_table(nait.assign(mp=nait["mp_id"].map(j["code"])).round(2), "12_koolialgus_naitajad")
kv = pd.DataFrame([dict(paar=paar, naitaja=c, **kokkuvote(g[c])) for paar, g in nait.groupby("paar", sort=False)
                   for c in nait.columns[2:]])
save_table(kv.round(4), "12_koolialgus_kokkuvote")
print("   Näitajate muutus (mediaan üle ristmike, 95% usaldusvahemik, Wilcoxoni p):")
print(kv.round(3).to_string(index=False))

viimane, eelmine = (f"{a} vs {b}" for a, b in PAARID[::-1])
uhised = puhas_paar[viimane].index.intersection(puhas_paar[eelmine].index)
fig, axes = plt.subplots(2, 2, figsize=(14, 9))
X = (np.arange(96) + 0.5) / 4
for ax, osakaal in zip(axes[0], [False, True]):
    for a in sorted({y for p in PAARID for y in p}):
        v = P.loc[a].loc[uhised].sum()
        ax.plot(X, v / v.sum() * 100 if osakaal else v / 1000, color=AASTA_VARV.get(a, TEXT2), lw=2, label=str(a))
    ax.axvspan(7.75, 9, color=C_GRAY, alpha=0.12, lw=0)
    ax.axvline(9, color=TEXT2, lw=0.8, ls="--")
    ax.set_xlim(5.5, 10.5)
    ax.set_xticks(np.arange(6, 10.6, 0.5))
    ax.xaxis.set_major_formatter(lambda h, _: slot_label(h * 4))
    ax.tick_params(axis="x", labelsize=8)
    ax.set_ylabel("Osakaal ööpäeva liiklusest, % 15 min kohta" if osakaal else "Tuhat sõidukit 15 min kohta")
    ax.set_title("Sama, osakaaluna ööpäevast (aastane kasv maha arvatud)" if osakaal else
                 f"Hommikune liiklus septembris, {len(uhised)} ristmikku kokku", fontsize=11)
    ax.legend(fontsize=9, title="hall = kooli algus varem 07:45–09:00\nkatkendjoon = kell 9", title_fontsize=7.5)
for ax, liik, yl in zip(axes[1], ["toores", "puhas"], ["Muutus, %", "Muutus, protsendipunkti"]):
    pv, pe = (pilud[pilud["paar"] == p].set_index("slot") for p in (viimane, eelmine))
    xs = pv.index / 4
    ax.bar(xs, pv[f"{liik}_mediaan"], width=0.21, align="edge", color=C_ORANGE, alpha=0.9, label=viimane,
           yerr=[pv[f"{liik}_mediaan"] - pv[f"{liik}_uv_alumine"], pv[f"{liik}_uv_ylemine"] - pv[f"{liik}_mediaan"]],
           error_kw=dict(lw=0.6, ecolor=TEXT2))
    ax.step(np.r_[pe.index / 4, pe.index[-1] / 4 + 0.25], np.r_[pe[f"{liik}_mediaan"], pe[f"{liik}_mediaan"].iloc[-1]],
            where="post", color=C_BLUE, lw=1.6, label=f"{eelmine} (võrdluseks)")
    ax.axhline(0, color=TEXT2, lw=0.6)
    ax.axvline(9, color=TEXT2, lw=0.8, ls="--")
    ax.set_xlim(5, 20)
    ax.set_xticks(range(5, 21))
    ax.set_xlabel("Kellaaeg (15 min pilu algus; mediaan üle ristmike, joon = 95% usaldusvahemik)")
    ax.set_ylabel(yl)
    ax.set_title("Toores vahe: liikluse muutus pilus" if liik == "toores" else
                 "Puhas vahe: ööpäeva liikluse muutus maha arvatud", fontsize=11)
    ax.legend(fontsize=9, loc="lower right")
fig.suptitle(f"Koolipäeva algus kell 9 (alates 1.09.2026): tööpäevad {AKEN[0]}.–{AKEN[1]}. septembril",
             x=0.01, ha="left", fontweight="bold")
fig.tight_layout()
save(fig, "12_01_koolialgus")

H = range(24, 40)                           # 06:00-10:00
jarj = puhas_paar[viimane][list(range(34, 38))].mean(axis=1).sort_values(ascending=False).index     # 08:30-09:30
fig, axes = plt.subplots(1, 2, figsize=(13, 0.25 * len(jarj) + 2), sharey=True)
for ax, paar in zip(axes, [eelmine, viimane]):
    sns.heatmap(puhas_paar[paar].reindex(jarj)[list(H)], cmap=DIVERGING, center=0, vmin=-15, vmax=15, ax=ax,
                yticklabels=False, cbar=paar == viimane, cbar_kws=dict(label="Puhas vahe, protsendipunkti", shrink=0.6))
    ax.set_xticks(np.arange(0, len(H) + 1, 2))
    ax.set_xticklabels([slot_label(s) for s in range(H[0], H[-1] + 2, 2)], rotation=0, fontsize=8)
    ax.set_xlabel("Kellaaeg")
    ax.set_ylabel("")
    ax.set_title(paar + (" (võrdluseks)" if paar == eelmine else " (koolialguse muutus)"), fontsize=11)
axes[0].set_yticks(np.arange(len(jarj)) + 0.5)
axes[0].set_yticklabels([f"{j.at[m, 'code']} {short_name(j.at[m, 'name'], 32, compact=True)}" for m in jarj], fontsize=7,
                        rotation=0)
fig.suptitle("Kus liikluse jaotus muutus: puhas vahe ristmiku ja kellaaja kaupa (valge = ristmik sel paaril välja jäetud)",
             x=0.01, ha="left", fontweight="bold")
fig.tight_layout()
save(fig, "12_02_koolialgus_ristmikud")

# === B) Väike langus, suur võit =========================================================================
kal = too.drop_duplicates("paev").set_index("paev")["vaheaeg"]
ummikuga = set()                            # (mp_id, tipp), kus 09 leidis stabiilse ummiku >= pooltel tööpäevadel
if (OUT_DIR / "09_ummikud.csv").exists():
    um = loe("09_ummikud", parse_dates=["paev"])
    um = um[um["stabiilne"] & (um["tyyp"] == "tööpäev")]
    for tipp in TIPUD:
        n = um[um["tipp"].str.contains(tipp)].groupby("mp")["paev"].nunique()
        ummikuga |= {(int(m[2:]), tipp) for m in n.index[n >= um["paev"].nunique() / 2]}
osad = []
for tipp, (a, b) in TIPUD.items():
    x = too[too["slot"].between(a * 4, b * 4 - 1) & too["vaheaeg"].isin(["kool", "lühike"])]
    W = x.groupby(["mp_id", "paev", "slot"])["v"].sum(min_count=1).unstack("slot").dropna()     # ainult terved aknad
    d = pd.DataFrame({"maht": W.sum(axis=1), "suurim": W.max(axis=1),
                      "tipptund": np.lib.stride_tricks.sliding_window_view(W.values, 4, axis=1).sum(axis=2).max(axis=1)},
                     index=W.index).reset_index()
    d["vaheaeg"] = d["paev"].map(kal)
    kool = d[d["vaheaeg"] == "kool"].sort_values(["mp_id", "paev"])
    ref = kool.groupby("mp_id")[["suurim", "maht", "tipptund"]].transform(
        lambda s: s.rolling(VIIDE_PAEVI, center=True, min_periods=10).median())
    kool = kool.assign(tase=ref["suurim"], tava=ref["maht"], tava_tipptund=ref["tipptund"]).dropna(subset=["tase"])
    d = pd.merge_asof(d.sort_values("paev"), kool[["mp_id", "paev", "tase", "tava", "tava_tipptund"]].sort_values("paev"),
                      on="paev", by="mp_id", direction="nearest").dropna(subset=["tase"])
    d["min_tais"] = (W.reindex(pd.MultiIndex.from_frame(d[["mp_id", "paev"]])).values
                     >= TAIS * d["tase"].values[:, None]).sum(axis=1) * 15
    d["indeks"], d["tipptunni_indeks"] = d["maht"] / d["tava"] * 100, d["tipptund"] / d["tava_tipptund"] * 100
    osad.append(d.assign(tipp=tipp, ummikuga=[(m, tipp) in ummikuga for m in d["mp_id"]]))
d = pd.concat(osad, ignore_index=True)
save_table(d.assign(mp=d["mp_id"].map(j["code"]), paev=d["paev"].dt.date)
           [["mp", "paev", "tipp", "vaheaeg", "ummikuga", "maht", "indeks", "tipptund", "tipptunni_indeks", "tase", "min_tais"]]
           .round(1), "12_taistase_paevad")
RYHM = "ummikuga" if ummikuga else "kõik"
valik = lambda x, ryhm=RYHM: x[x["ummikuga"]] if ryhm == "ummikuga" else x
kooli = d[d["vaheaeg"] == "kool"]
print(f"\nB) Väike langus, suur võit: {len(d):,} ristmik-päev-tippu; stabiilse ummikuga ristmik-tippe {len(ummikuga)} "
      f"(põhitulemus: {RYHM})")


def kover(x, veerg):
    """Keskmine aeg täistasemel indeksi vahemike kaupa (vahemiku keskpunkt), ainult >= 50 päevaga vahemikud."""
    g = x.groupby(x[veerg] // SAMM * SAMM + SAMM / 2)["min_tais"].agg(["mean", "sem", "size"])
    return g[(g["size"] >= 50) & (g.index >= 80) & (g.index <= 115)]


juures = lambda x, veerg, c: x.loc[(x[veerg] - c).abs() <= SAMM, "min_tais"].mean()
krows = []
for ryhm in ["kõik"] + (["ummikuga"] if ummikuga else []):
    for tipp in TIPUD:
        x = valik(kooli[kooli["tipp"] == tipp], ryhm)
        for veerg in ["indeks", "tipptunni_indeks"]:
            krows.append(kover(x, veerg).rename_axis("indeksi_vahemiku_keskpunkt").reset_index()
                         .assign(ryhm=ryhm, tipp=tipp, indeks=veerg))
            m100, m95, m90 = (juures(x, veerg, c) for c in (100, 95, 90))
            print(f"   {ryhm}, {tipp}, {veerg}: tavalisel päeval {m100:.0f} min täistasemel; 5% vähem liiklust -> "
                  f"{m95:.0f} min ({(m95 / m100 - 1) * 100:+.0f}%); 10% vähem -> {m90:.0f} min ({(m90 / m100 - 1) * 100:+.0f}%)")
save_table(pd.concat(krows).rename(columns={"mean": "min_tais_keskmine", "sem": "standardviga", "size": "paevi"}).round(2),
           "12_vaike_muutus_kover")

# lühikesed koolivaheajad vs 2 nädalat enne ja pärast
luh = pd.Series(sorted(d.loc[d["vaheaeg"] == "lühike", "paev"].unique()))
vrows = []
for _, (b0, b1) in luh.groupby((luh.diff() > pd.Timedelta(days=4)).cumsum()).agg(["min", "max"]).iterrows():
    k14, k1 = pd.Timedelta(days=14), pd.Timedelta(days=1)
    viide = d[(d["vaheaeg"] == "kool") & (d["paev"].between(b0 - k14, b0 - k1) | d["paev"].between(b1 + k1, b1 + k14))]
    vahe = d[d["paev"].between(b0, b1)]
    veerud = ["maht", "tipptund", "min_tais"]
    g = (viide.groupby(["mp_id", "tipp", "ummikuga"])[veerud].mean()
         .join(vahe.groupby(["mp_id", "tipp", "ummikuga"])[veerud].mean(), lsuffix="_viide", rsuffix="_vaheaeg").dropna())
    for ryhm in ["kõik"] + (["ummikuga"] if ummikuga else []):
        for tipp, x in valik(g.reset_index(), ryhm).groupby("tipp"):
            vrows.append({"vaheaeg_algus": b0.date(), "ryhm": ryhm, "tipp": tipp, "ristmikke": len(x),
                          "liiklus_%": ((x["maht_vaheaeg"] / x["maht_viide"] - 1) * 100).median(),
                          "tipptund_%": ((x["tipptund_vaheaeg"] / x["tipptund_viide"] - 1) * 100).median(),
                          "min_tais_viide": x["min_tais_viide"].mean(), "min_tais_vaheaeg": x["min_tais_vaheaeg"].mean(),
                          "aeg_taistasemel_%": (x["min_tais_vaheaeg"].sum() / x["min_tais_viide"].sum() - 1) * 100})
va = pd.DataFrame(vrows)
save_table(va.round(1), "12_vaheajad_taistase")
vk = va[va["ryhm"] == RYHM].groupby("tipp")[["liiklus_%", "tipptund_%", "aeg_taistasemel_%"]].median()
print(f"   Lühikesed koolivaheajad ({va['vaheaeg_algus'].nunique()} tk, {RYHM}; mediaan üle vaheaegade): "
      + "; ".join(f"{tp}: liiklus {r['liiklus_%']:+.1f}%, tipptund {r['tipptund_%']:+.1f}%, aeg täistasemel "
                  f"{r['aeg_taistasemel_%']:+.0f}%" for tp, r in vk.iterrows()))

# kalibreerimine: sama näitaja sõidukipõhistest päevadest vs täis tsüklites liikunud sõidukite aeg (09, nagu 10_02_kullastus)
kalib = None
veh = load_vehicles(None, koik=True)
if veh is not None and (OUT_DIR / "09_tsuklid.csv").exists():
    veh = veh.assign(paev=veh["ts"].dt.normalize(), slot=veh["ts"].dt.hour * 4 + veh["ts"].dt.minute // 15)
    tunde = veh.groupby("paev")["ts"].agg(lambda s: s.dt.hour.nunique())
    veh = veh[veh["paev"].isin(tunde[tunde >= 23].index) & (veh["paev"].dt.dayofweek < 5)]      # terved tööpäevad
    n15 = veh.groupby(["mp_id", "paev", "slot"]).size().unstack("slot", fill_value=0).reindex(columns=range(96), fill_value=0)
    c = loe("09_tsuklid", parse_dates=["algus"])
    c = c.assign(mp_id=c["mp"].str[2:].astype(int), paev=c["algus"].dt.normalize(), slot=(c["t"] // 900).astype(int),
                 tn=c["n"] * c["ummikus"])
    k = c.groupby(["mp_id", "paev", "slot"])[["tn", "n"]].sum()
    k = (k["tn"] / k["n"].where(k["n"] > 0)).unstack("slot").reindex(columns=range(96)).fillna(0) * 15     # min veerandis
    viim = d.sort_values("paev").groupby(["mp_id", "tipp"])["tase"].last()          # viimane teadaolev täistase
    rows = []
    for tipp, (a, b) in TIPUD.items():
        sl = list(range(a * 4, b * 4))
        for (mp, paev), r in n15[sl].iterrows():
            if (mp, tipp) in viim.index and (mp, paev) in k.index:
                rows.append(dict(mp_id=mp, paev=paev.date(), tipp=tipp, ummikuga=(mp, tipp) in ummikuga,
                                 min_taistasemel_15min=int((r.values >= TAIS * viim[(mp, tipp)]).sum() * 15),
                                 min_tais_tsuklites=k.loc[(mp, paev), sl].sum()))
    kalib = pd.DataFrame(rows)
    rho = stats.spearmanr(kalib["min_taistasemel_15min"], kalib["min_tais_tsuklites"])
    save_table(kalib.assign(mp=kalib["mp_id"].map(j["code"])).round(1), "12_kalibreerimine")
    print(f"   Kalibreerimine ({kalib['paev'].nunique()} tööpäeva, {len(kalib)} ristmik-tippu): aeg täistasemel (15 min "
          f"loendus) vs täis tsüklite aeg (09): Spearmani rho = {rho.statistic:.2f} (p = {rho.pvalue:.3g})")

# joonis
fig, axes = plt.subplots(2, 2, figsize=(14, 9.5))
for ax, veerg, xl in [(axes[0, 0], "indeks", "Tipuakna liiklus, % tavalisest (100 = tavaline õppetöö-tööpäev)"),
                      (axes[1, 0], "tipptunni_indeks", "Tipptunni maht, % tavalisest")]:
    for tipp, col in VARV.items():
        x = valik(kooli[kooli["tipp"] == tipp])
        g = kover(x, veerg)
        ax.fill_between(g.index, g["mean"] - 1.96 * g["sem"], g["mean"] + 1.96 * g["sem"], color=col, alpha=0.2, lw=0)
        m100, m95 = juures(x, veerg, 100), juures(x, veerg, 95)
        ax.plot(g.index, g["mean"], "o-", color=col, ms=4,
                label=f"{tipp}: 5% vähem -> {(m95 / m100 - 1) * 100:+.0f}% aega täistasemel")
        if veerg == "indeks":                                    # koolivaheaja päevad samal teljel
            h = valik(d[(d["vaheaeg"] == "lühike") & (d["tipp"] == tipp)])
            ax.plot(h[veerg].mean(), h["min_tais"].mean(), "D", color=col, ms=9, mec="black", zorder=5)
    ax.axvline(100, color=TEXT2, lw=0.6, ls=":")
    ax.set_xlabel(xl)
    ax.set_ylabel("Aeg täistasemel, min päevas (keskmine)")
    ax.set_ylim(0, None)
    ax.legend(fontsize=9, loc="upper left", title="romb = koolivaheaja päevade keskmine" if veerg == "indeks" else None,
              title_fontsize=8)
axes[0, 0].set_title("Vähem liiklust tipuaknas -> vähem aega täistasemel\n(õppetöö-tööpäevad, vari = 95% usaldusvahemik)",
                     fontsize=11)
axes[1, 0].set_title("Sama tipptunni mahu järgi\n(püstjooned = 06 hajutamisstsenaariumid, hommik)", fontsize=11)
axes[1, 0].legend(fontsize=9, loc="lower right")
hf = OUT_DIR / "06_hajutamine_ristmikud.csv"
if hf.exists():                             # 06: tipptunni vähenemine, kui 20% tipptunni sõitudest nihkub
    hr = pd.read_csv(hf, encoding="utf-8-sig")
    for veerg, ls in [("hommik_20%_mõlemad_30min_%", "--"), ("hommik_20%_ühtlane_60min_%", "-.")]:
        if veerg in hr:
            vah = hr[veerg].median()
            axes[1, 0].axvline(100 - vah, color=TEXT2, lw=1, ls=ls)
            axes[1, 0].text(100 - vah, axes[1, 0].get_ylim()[1] * 0.97, f"20% sõitudest {veerg.split('_')[2]} ±{veerg.split('_')[3]}: −{vah:.1f}% ",
                            rotation=90, ha="right", va="top", fontsize=8, color=TEXT2)
ax = axes[0, 1]
vh = va[(va["ryhm"] == RYHM) & (va["tipp"] == "hommik")].reset_index(drop=True)
xs = np.arange(len(vh))
ax.bar(xs - 0.2, vh["liiklus_%"], 0.4, color=C_GRAY, label="tipuakna liiklus")
ax.bar(xs + 0.2, vh["aeg_taistasemel_%"], 0.4, color=C_BLUE, label="aeg täistasemel")
for x0, liiklus, aeg in zip(xs, vh["liiklus_%"], vh["aeg_taistasemel_%"]):
    ax.text(x0 - 0.2, liiklus - 1.5, f"{liiklus:+.0f}%", ha="center", va="top", fontsize=8)
    ax.text(x0 + 0.2, aeg - 1.5, f"{aeg:+.0f}%", ha="center", va="top", fontsize=8)
ax.axhline(0, color=TEXT2, lw=0.6)
ax.set_xticks(xs)
ax.set_xticklabels([f"{pd.Timestamp(v):%m.%Y}" for v in vh["vaheaeg_algus"]])
ax.set_ylabel("Muutus, % (vs 2 nädalat enne ja pärast)")
ax.set_ylim(min(-100, vh["aeg_taistasemel_%"].min() - 12), 16)
ax.legend(fontsize=9, loc="upper right", ncol=2)
ax.set_title(f"Lühikesed koolivaheajad, hommik ({RYHM} ristmikud)", fontsize=11)
ax = axes[1, 1]
if kalib is not None:
    for tipp, col in VARV.items():
        g = kalib[kalib["tipp"] == tipp]
        ax.scatter(g["min_taistasemel_15min"] + np.random.default_rng(0).uniform(-3, 3, len(g)), g["min_tais_tsuklites"],
                   s=np.where(g["ummikuga"], 34, 14), color=col, alpha=0.7, edgecolor="none", label=tipp)
    ax.set_xlabel("Aeg täistasemel, min (ristmiku 15 min loendus)")
    ax.set_ylabel("Aeg täis tsüklites, min (09, fooritsüklid)")
    ax.legend(fontsize=9, title="suur punkt = stabiilse ummikuga", title_fontsize=8)
    ax.set_title(f"Kalibreerimine sõidukipõhiste päevadega\n({kalib['paev'].nunique()} tööpäeva, Spearmani rho = "
                 f"{rho.statistic:.2f})", fontsize=11)
else:
    ax.axis("off")
fig.suptitle(f"Väike langus, suur võit: aeg, mil ristmik töötab täistasemel (>= {TAIS:.0%} tavalisest suurimast 15 min loendusest)",
             x=0.01, ha="left", fontweight="bold")
fig.tight_layout()
save(fig, "12_03_vaike_muutus")
print("Valmis.")
