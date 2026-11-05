"""
14 - Sõidukite pikkusrühmad kooliajal ja koolivaheajal: kas vaheajal väheneb ainult sõiduautode liiklus või ka veokite
oma. Rühmad: lühikesed (alla 6 m: sõiduautod, pakiautod), keskmised (6-12 m: veoautod, bussid) ja pikad (üle 12 m:
autorongid).

SISEND
  common.load_15m()                      maanteeloendurite 15 min loendused pikkusrühmade kaupa (veerud luhike, keskmine,
                                         pikk); pikk ajalugu on Harjumaa loenduritel (5-37 km Tallinnast)
  common.load_daily(), counter_month()   kahtlase mahuga loendur-kuude väljajätmiseks
  common.day_calendar()                  päevatüüp ja koolivaheajad
  common.load_vehicles(None, koik=True)  Tallinna ristmike sõidukipõhised kirjed: iga sõiduki mõõdetud pikkus
  NB! Maanteeloendur annab sõiduki klassi, mitte pikkust. Klasside jaotus pikkusrühmadesse (common.PIKKUS) on hinnang:
  alla 6 m = mootorratas, sõiduauto, pakiauto, väikebuss; 6-12 m = haagisega sõiduauto, väike veoauto, veoauto, buss;
  üle 12 m = haagisega veoauto, sadulrong. Ristmikel on pikkus mõõdetud (piirid common.PIKKUS_PIIRID).

ARVUTUS
  A) Maanteed. Loenduri rajad liidetakse (arvesse lähevad veerandtunnid, kus kõik rajad on olemas) ja veerandtunnid
     tundideks; päev läheb arvesse, kui kõik 24 tundi on olemas. Iga lühikese koolivaheaja (sügis, veebruar, kevad)
     kohta võrreldakse vaheaja tööpäevi õppetöö-tööpäevadega 14 päeva enne ja 14 päeva pärast (riigipühad ja lühendatud
     tööpäevad on väljas; mõlemas vähemalt MIN_PAEVI päeva). Iga loenduri ja pikkusrühma kohta:
       muutus % = (vaheaja keskmine maht / võrdluspäevade keskmine maht - 1) x 100
     eraldi ööpäeva, hommiku (06-10) ja õhtu (15-19) kohta. Kokkuvõte = mediaan üle loendur-vaheaeg paaride ja selle 95%
     usaldusvahemik (bootstrap, common.mediaani_uv). Tunni kaupa: kõigi loendurite ja vaheaegade summade suhe.
  B) Pikkusrühmade osakaal kellaaja järgi: maanteedel õppetöö-tööpäevade keskmine, ristmikel sõidukipõhiste päevade
     järgi (ainult terved tööpäevad). Kui sõidukipõhiseid päevi on nii õppetöö kui ka koolivaheaja ajast, trükitakse
     sama muutus ka ristmike kohta (kõik ristmikud kokku); muidu jääb see ootama vaheaja nädala andmeid.
  ponytail: võrdlus on vaatluslik (enne-pärast), ilm ja pühade-eelsed päevad võivad üksikut vaheaega mõjutada - seepärast
  mitu vaheaega koos. Ristmikel võib tihedas järjekorras kaks sõidukit mõõtuda ühe pikana.

VÄLJUND (kaust valjund/)
  14_01_pikkusruhmad_vaheaeg.png
      Näitab: kui palju muutub liiklus koolivaheajal eri pikkusega sõidukitel ja mis kellaajal.
      Kuidas: 2 x 2 paneeli. Ülal vasakul tulbad: muutus % pikkusrühma kaupa ööpäevas, hommikul ja õhtul (mediaan üle
      loendur-vaheaeg paaride, vurrud = 95% usaldusvahemik). Ülal paremal joondiagramm: muutus % tunni kaupa (kell 5-21).
      All vasakul tulbad iga vaheaja kohta eraldi (ööpäeva muutus, loendurite mediaan) - kas tulemus kordub. All paremal
      keskmiste ja pikkade sõidukite osakaal kõigist sõidukitest kellaaja järgi: pidevjoon = maanteed (õppetöö-tööpäevad),
      katkendjoon = Tallinna ristmikud (sõidukipõhised päevad). Värvid: sinine = lühikesed, oranž = keskmised, türkiis =
      pikad.
  14_pikkus_vaheaeg.csv     muutus iga vaheaja, loenduri, pikkusrühma ja ajaakna kohta
  14_pikkus_kokkuvote.csv   mediaan, usaldusvahemik ja paaride arv pikkusrühma ja ajaakna kaupa
  14_pikkus_tunnid.csv      muutus tunni kaupa
  14_pikkus_osakaalud.csv   pikkusrühmade osakaal tunni kaupa (maanteed, ristmikud)
  14_ristmikud_pikkus.csv   ristmike sõidukid päeva ja pikkusrühma kaupa (koos päevatüübi ja vaheaja märkega)
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import (load_15m, load_daily, counter_month, ilma_vigaste_kuudeta, load_locations, load_vehicles, day_calendar,
                    mediaani_uv, set_style, save, save_table, PIKKUS, PIKKUS_PIIRID, PIKKUS_LABEL,
                    C_BLUE, C_ORANGE, C_AQUA, TEXT2)

RYHMAD = list(PIKKUS)                                   # luhike, keskmine, pikk
VARV = dict(zip(RYHMAD, [C_BLUE, C_ORANGE, C_AQUA]))
AKNAD = {"ööpäev": (0, 24), "hommik 06-10": (6, 10), "õhtu 15-19": (15, 19)}
VIIDE_PAEVI = 14                                        # võrdlus: õppetöö-tööpäevad nii palju päevi enne ja pärast vaheaega
MIN_PAEVI = 3                                           # vaheajas ja võrdluses vähemalt nii palju terveid tööpäevi
MIN_MAHT = 20                                           # rühma muutus arvesse, kui võrdluspäeval on aknas vähemalt 20 sõidukit


def muutus(v, r, a, b):
    """Muutus % tundide a...b-1 summas: v ja r = tabelid (read = loendur, veerud = tunnid 0..23), vaheaeg ja võrdlus.
    Liiga väikese võrdlusmahuga (alla MIN_MAHT sõiduki) read -> NaN."""
    s = r.loc[:, a:b - 1].sum(axis=1)
    return (v.loc[:, a:b - 1].sum(axis=1) / s.where(s >= MIN_MAHT) - 1) * 100


_t = pd.DataFrame([[10.] * 24, [1.] * 24])
assert muutus(_t * 0.9, _t, 6, 10).round(6).tolist()[0] == -10 and np.isnan(muutus(_t, _t, 6, 10)[1])
assert pd.cut([5.9, 6, 11.9, 12], PIKKUS_PIIRID, labels=RYHMAD, right=False).tolist() == ["luhike", "keskmine", "keskmine", "pikk"]

set_style()
# === A) Maanteed: vaheaeg vs 2 nädalat enne ja pärast ===========================================================
print("Laen maanteeloendurite 15 min loendused...")
m = ilma_vigaste_kuudeta(load_15m(), counter_month(load_daily()))
x = m.groupby(["id", "ts"])[RYHMAD].sum().assign(n=m.groupby(["id", "ts"]).size()).reset_index()
x = x[x["n"] == x.groupby("id")["n"].transform("max")]                    # ainult veerandtunnid, kus kõik rajad on olemas
x["paev"], x["tund"] = x["ts"].dt.normalize(), x["ts"].dt.hour
h = x.groupby(["id", "paev", "tund"])[RYHMAD].agg(["sum", "size"])
h = h.loc[h[(RYHMAD[0], "size")] == 4].xs("sum", axis=1, level=1)         # tund = 4 veerandtundi
W = h.unstack("tund").dropna()                                            # read = loendur-päev, veerud = (rühm, tund)
kal = day_calendar(W.index.get_level_values("paev")).set_index("paev")
too = kal[kal["paevatyyp"] == "tööpäev"]
paev = W.index.get_level_values("paev")
nimi = load_locations().set_index("id")["nimi"]

read, V_koik, R_koik = [], [], []
bd = pd.Series(sorted(too.index[too["vaheaeg"] == "lühike"]))
for _, (b0, b1) in bd.groupby((bd.diff() > pd.Timedelta(days=4)).cumsum()).agg(["min", "max"]).iterrows():
    k14, k1 = pd.Timedelta(days=VIIDE_PAEVI), pd.Timedelta(days=1)
    viide = too.index[(too["vaheaeg"] == "kool") & (((too.index >= b0 - k14) & (too.index <= b0 - k1))
                                                    | ((too.index >= b1 + k1) & (too.index <= b1 + k14)))]
    osa = {"v": W[paev.isin(too.index[(too.index >= b0) & (too.index <= b1)])], "r": W[paev.isin(viide)]}
    n = {k: d.groupby("id").size() for k, d in osa.items()}
    ids = n["v"].index[n["v"] >= MIN_PAEVI].intersection(n["r"].index[n["r"] >= MIN_PAEVI])
    if not len(ids):
        continue
    V, R = (osa[k].groupby("id").mean().loc[ids] for k in "vr")
    V_koik.append(V)
    R_koik.append(R)
    for g in RYHMAD:
        for aken, (a, b) in AKNAD.items():
            read.append(pd.DataFrame({"vaheaeg_algus": b0.date(), "id": ids, "loendur": nimi.reindex(ids).values, "ryhm": g, "aken": aken,
                                      "vaheaeg_soid": V[g].loc[:, a:b - 1].sum(axis=1).values, "viide_soid": R[g].loc[:, a:b - 1].sum(axis=1).values,
                                      "muutus_%": muutus(V[g], R[g], a, b).values}))
mu = pd.concat(read, ignore_index=True)
save_table(mu.round(2), "14_pikkus_vaheaeg")
kokku = pd.DataFrame([dict(ryhm=g, aken=aken, paare=int(d["muutus_%"].notna().sum()), mediaan=d["muutus_%"].median(),
                           **dict(zip(["uv_alumine", "uv_ylemine"], mediaani_uv(d["muutus_%"].dropna()))),
                           osakaal_liiklusest=d["viide_soid"].sum() / mu.loc[mu["aken"] == aken, "viide_soid"].sum() * 100)
                      for (g, aken), d in mu.groupby(["ryhm", "aken"], sort=False)])
save_table(kokku.round(2), "14_pikkus_kokkuvote")
Vs, Rs = pd.concat(V_koik).sum(), pd.concat(R_koik).sum()                 # kõik loendurid ja vaheajad kokku: (rühm, tund)
tunnid = ((Vs / Rs - 1) * 100).unstack(0)[RYHMAD]
save_table(tunnid.rename_axis("tund").reset_index().round(2), "14_pikkus_tunnid")
print(f"A) Maanteed: {mu['vaheaeg_algus'].nunique()} lühikest koolivaheaega ({', '.join(f'{v:%m.%Y}' for v in sorted(mu['vaheaeg_algus'].unique()))}), "
      f"{mu['id'].nunique()} loendurit. Muutus vaheajal (mediaan, 95% usaldusvahemik):")
for g in RYHMAD:
    print(f"   {PIKKUS_LABEL[g]} ({kokku[(kokku.ryhm == g) & (kokku.aken == 'ööpäev')].osakaal_liiklusest.iloc[0]:.0f}% liiklusest): "
          + "; ".join(f"{r.aken} {r.mediaan:+.1f}% ({r.uv_alumine:+.1f}...{r.uv_ylemine:+.1f})" for r in kokku[kokku.ryhm == g].itertuples()))

# === B) Pikkusrühmade osakaal kellaaja järgi: maanteed ja Tallinna ristmikud ===================================
kooli = W[paev.isin(too.index[too["vaheaeg"] == "kool"])].sum().unstack(0)[RYHMAD]      # tund x rühm, õppetöö-tööpäevad
osak = {"maanteed": kooli.div(kooli.sum(axis=1), axis=0) * 100}
v = load_vehicles(None, koik=True)
if v is not None:
    v = v[v["pikkus"] > 0].assign(paev=lambda z: z["ts"].dt.normalize(), tund=lambda z: z["ts"].dt.hour)
    v["ryhm"] = pd.cut(v["pikkus"], PIKKUS_PIIRID, labels=RYHMAD, right=False)
    tunde = v.groupby("paev")["tund"].nunique()
    v = v[v["paev"].isin(tunde.index[tunde >= 23])]                       # ainult terved ööpäevad
    rk = day_calendar(v["paev"]).set_index("paev")
    rp = v.groupby(["paev", "ryhm"], observed=True).size().unstack("ryhm")[RYHMAD].join(rk[["paevatyyp", "vaheaeg"]])
    save_table(rp.reset_index().assign(paev=lambda z: z["paev"].dt.date), "14_ristmikud_pikkus")
    rt = v[v["paev"].isin(rk.index[rk["paevatyyp"] == "tööpäev"])]
    rt = rt.assign(vaheaeg=rt["paev"].map(rk["vaheaeg"]))
    paevi = rt.groupby("vaheaeg")["paev"].nunique()
    keskm = (rt.groupby(["vaheaeg", "tund", "ryhm"], observed=True).size().unstack("ryhm")[RYHMAD]
             .div(paevi, axis=0, level="vaheaeg"))                        # sõidukeid tunnis tööpäeva kohta
    if "kool" in paevi:
        osak["ristmikud"] = keskm.loc["kool"].div(keskm.loc["kool"].sum(axis=1), axis=0) * 100
    print(f"B) Ristmike sõidukikirjed: terveid tööpäevi õppetöö ajal {paevi.get('kool', 0)}, lühikesel koolivaheajal {paevi.get('lühike', 0)}; "
          f"pikkusrühmade osakaal: " + ", ".join(f"{PIKKUS_LABEL[g]} {rt['ryhm'].eq(g).mean() * 100:.1f}%" for g in RYHMAD))
    if {"kool", "lühike"} <= set(paevi.index):
        for g in RYHMAD:                                                  # kõik ristmikud kokku: vaheaja ja kooliaja tööpäeva suhe
            vah, kool = keskm.loc["lühike", g], keskm.loc["kool", g]
            print(f"   ristmikud, {PIKKUS_LABEL[g]}: " + "; ".join(
                f"{aken} {(vah.loc[a:b - 1].sum() / kool.loc[a:b - 1].sum() - 1) * 100:+.1f}%" for aken, (a, b) in AKNAD.items()))
    else:
        print("   Ristmike võrdlus kooliaeg vs vaheaeg ootab vaheaja nädala sõidukipõhiseid andmeid.")
save_table(pd.concat(osak, names=["allikas"]).reset_index().round(2), "14_pikkus_osakaalud")

# === Joonis =====================================================================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 9.5))
ax = axes[0, 0]
for i, g in enumerate(RYHMAD):
    k = kokku[kokku["ryhm"] == g].set_index("aken").loc[list(AKNAD)]
    xs = np.arange(len(AKNAD)) + (i - 1) * 0.27
    ax.bar(xs, k["mediaan"], 0.25, color=VARV[g], label=PIKKUS_LABEL[g],
           yerr=[k["mediaan"] - k["uv_alumine"], k["uv_ylemine"] - k["mediaan"]], error_kw=dict(lw=1, ecolor=TEXT2, capsize=3))
    for x0, y, lo, hi in zip(xs, k["mediaan"], k["uv_alumine"], k["uv_ylemine"]):          # silt vurru otsa taha
        ax.text(x0, lo - 0.15 if y < 0 else hi + 0.15, f"{y:+.1f}", ha="center", va="top" if y < 0 else "bottom", fontsize=8)
ax.axhline(0, color=TEXT2, lw=0.6)
ax.set_xticks(range(len(AKNAD)))
ax.set_xticklabels(AKNAD)
ax.set_ylabel("Muutus koolivaheajal, %")
ax.set_title("Liikluse muutus lühikesel koolivaheajal pikkusrühma kaupa\n(mediaan üle loendur-vaheaeg paaride, vurrud = 95% usaldusvahemik)",
             fontsize=10)
ax.legend(fontsize=8)
ax = axes[0, 1]
for g in RYHMAD:
    ax.plot(tunnid.index + 0.5, tunnid[g], "o-", ms=3.5, color=VARV[g], label=PIKKUS_LABEL[g])
ax.axhline(0, color=TEXT2, lw=0.6)
ax.set_xlim(5, 21)
ax.set_xticks(range(5, 22, 2))
ax.set_xlabel("Kellaaeg")
ax.set_ylabel("Muutus koolivaheajal, %")
ax.set_ylim(min(tunnid.loc[5:20].min().min() - 2, -2), max(tunnid.loc[5:20].max().max() + 2, 2))
ax.set_title("Muutus tunni kaupa (kõik loendurid ja vaheajad kokku)", fontsize=10)
ax.legend(fontsize=8)
ax = axes[1, 0]
vk = mu[mu["aken"] == "ööpäev"].groupby(["vaheaeg_algus", "ryhm"])["muutus_%"].median().unstack("ryhm")[RYHMAD]
for i, g in enumerate(RYHMAD):
    ax.bar(np.arange(len(vk)) + (i - 1) * 0.27, vk[g], 0.25, color=VARV[g], label=PIKKUS_LABEL[g])
ax.axhline(0, color=TEXT2, lw=0.6)
ax.set_xticks(range(len(vk)))
ax.set_xticklabels([f"{pd.Timestamp(d):%m.%Y}" for d in vk.index])
ax.set_xlabel("Koolivaheaja algus")
ax.set_ylabel("Ööpäeva liikluse muutus, % (loendurite mediaan)")
ax.set_title("Sama iga koolivaheaja kohta eraldi", fontsize=10)
ax = axes[1, 1]
for allikas, ls in [("maanteed", "-"), ("ristmikud", "--")]:
    if allikas in osak:
        for g in RYHMAD[1:]:
            ax.plot(osak[allikas].index + 0.5, osak[allikas][g], color=VARV[g], ls=ls, lw=1.8,
                    label=f"{PIKKUS_LABEL[g]}: {allikas}")
ax.set_xlim(0, 24)
ax.set_xticks(range(0, 25, 3))
ax.set_ylim(0, None)
ax.set_xlabel("Kellaaeg")
ax.set_ylabel("Osakaal kõigist sõidukitest, %")
ax.set_title("Keskmiste ja pikkade sõidukite osakaal kellaaja järgi\n(maanteed: õppetöö-tööpäevad; ristmikud: sõidukipõhised tööpäevad)",
             fontsize=10)
ax.legend(fontsize=8)
fig.suptitle(f"Pikkusrühmad kooliajal ja koolivaheajal: {mu['id'].nunique()} maanteeloendurit Tallinna ümbruses, "
             f"{mu['vaheaeg_algus'].nunique()} vaheaega vs 2 nädalat enne ja pärast", x=0.01, ha="left", fontweight="bold")
fig.tight_layout()
save(fig, "14_01_pikkusruhmad_vaheaeg")
print("Valmis.")
