"""
40_2 - Juhi tasuvus: kas üksikule juhile tasub tipust ära nihkuda. Juht säästab ristmikel ooteaega, aga kaotab, kui
jõuab kohale varem või hiljem, kui tahab. Suurim nihe, mis juhile veel tasub = kus säästetud aeg võrdub ajakaotuse
hinnaga. Ainult mudel A: mudelil B (ummikuosa) pole ajaühikut.

SISEND
  common.sts_andmed()        ajaloolised tööpäevade profiilid ja mudel A (foori viivitus), vt 40_0
  common.load_junctions()    ristmike nimed

ARVUTUS
  Koridorid nagu 28 (KORIDORID): juht läbib koridori kõik loendatud ristmikud (sõiduaeg nende vahel jäetakse välja,
    s.t ristmikud läbitakse samal kellaajal). Päris teekonnal on rohkem foore kui loendatud ristmikke, seega on sääst
    alampiir; tabelis on ka, mitu sama suurt ristmikku peaks teel olema, et 15 min nihe tasuks.
  Ristmiku tavaline viivitus igal 15 min pilul = mudeli A viivitus (s/sõiduk), päevade mediaan; minutite kaupa lineaarne
    vahepealne (pilu keskel). Koridori viivitus = ristmike viivituste summa. Tipuaeg t* = suurima koridori viivitusega
    minut (hommikul 06:00-10:00, õhtul 14:00-19:00).
  Juht, kes sõitis t* ajal, nihkub Δ = 1...NIHE_MAX min (ainsana: teised jäävad paigale, see on juhile parim juhtum):
    sääst varem = viivitus(t*) - viivitus(t* - Δ), sääst hiljem = viivitus(t*) - viivitus(t* + Δ), min.
  Ajakaotuse hind (Small 1982, sõiduaja väärtuse suhtes): iga minut varem kohal = BETA (0,61) minutit sõiduaega, iga
    minut hiljem = GAMMA (2,40) minutit. Õhtul samad kaalud (varem = lahkub töölt varem, hiljem = jõuab hiljem koju).
    Kohalejõudmise nihe arvestab säästu: Δ varem lahkudes jõuab juht Δ + sääst varem (hind BETA x (Δ + sääst)), Δ
    hiljem lahkudes Δ - sääst hiljem (hind GAMMA x (Δ - sääst); kui sääst on suurem kui Δ, jõuab ta ikkagi varem ja
    hind on BETA x (sääst - Δ)).
  Tasub = sääst >= hind. Suurim tasuv nihe = suurim Δ, milleni tasub katkematult (kõik nihked 1...Δ tasuvad; 0 = ei
    tasu juba 1 minutiga). Vajalik kaal =
    sääst / (Δ + sääst) varem ja sääst / (Δ - sääst) hiljem: nii väike peaks juhi ajakaotuse kaal olema, et nihe Δ
    tasuks (paindliku tööajaga juhil väiksem).

CALCULATION IN PLAIN ENGLISH
  Corridor delay at minute t = sum over the corridor's junctions of model-A delay (median over days, in minutes;
    straight lines between 15-minute slot centres). Peak minute t* = largest corridor delay (06-10 or 14-19).
  One driver who travelled at t* shifts alone by D = 1 ... NIHE_MAX minutes:
    saving earlier = delay(t*) - delay(t* - D); saving later = delay(t*) - delay(t* + D).
  Schedule cost: leaving D earlier he arrives D + saving earlier, cost = BETA x (D + saving), BETA = 0.61 minutes of
    travel time per minute early. Leaving D later he arrives D - saving later, cost = GAMMA x (D - saving), GAMMA =
    2.40; if the saving is larger than D he still arrives early and the cost is BETA x (saving - D).
  Pays = saving >= cost. Largest paying shift = largest D for which every shift 1 ... D pays. Required weight = the
    largest weight at which a shift pays: saving / (D + saving) earlier, saving / (D - saving) later. Junctions
    needed for a 15-minute earlier shift: n x s >= BETA x (15 + n x s), so n = 15 x BETA / ((1 - BETA) x s), s =
    saving per junction.

VÄLJUND (kaust valjund/)
  40_2_01_juhi_tasuvus.png
      Näitab: kui palju ooteaega juht nihkudes säästab ja kui palju see maksab ajakaotusena; kus need jooned ristuvad.
      Kuidas: 2 x 4 paneeli; rida = hommik, õhtu; veerg = koridor. x = nihe, min; y = minutid (logaritmiline skaala,
      et sääst ja hind mahuksid samale teljele; iga jaotis = 10 korda rohkem). Pidev joon = säästetud
      ooteaeg (sinine = varem, oranž = hiljem), katkendjoon = ajakaotuse hind (sinine = varem, BETA x Δ; oranž =
      hiljem, GAMMA x Δ). Tekstis suurim sääst ja suurim tasuv nihe.
  40_2_juhi_tasuvus.csv   koridor, tipp: ristmikud, tipuaeg, viivitus tipus (min), suurim sääst varem / hiljem ja selle
                          nihe, suurim tasuv nihe varem / hiljem, vajalik kaal 15, 30 ja 60 min nihke juures, mitu
                          sama suurt ristmikku peaks teel olema, et 15 min nihe tasuks
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import (sts_andmed, viivitus, load_junctions, short_name, set_style, save, save_table, hhmm, C_BLUE,
                    C_ORANGE, GRID, TEXT, TEXT2)

KORIDORID = {"Tartu mnt": [34, 35, 39, 19], "Paldiski mnt": [7, 3, 12, 11, 16],
             "Tammsaare tee": [10, 43, 8, 9], "Sõpruse pst": [1, 8]}            # nagu 28
BETA, GAMMA = 0.61, 2.40               # Small (1982): minut varem / hiljem kohal = nii mitu minutit sõiduaega
NIHE_MAX = 120                         # min
AKNAD = {"hommik": (6 * 60, 10 * 60), "ohtu": (14 * 60, 19 * 60)}             # tipuaja otsing, minutid
TIPP_TXT = {"hommik": "hommik", "ohtu": "õhtu"}


def suurim_tasuv(saast, hind):
    """Suurim Δ (1, 2, ...), mille juures sääst >= hind kõigil nihetel 1...Δ (tasub katkematult); 0, kui ei tasu juba
    1 minutiga."""
    ok = np.asarray(saast) >= np.asarray(hind)
    return int(np.argmin(np.r_[ok, False]))


assert suurim_tasuv([1.0, 1.5, 1.6], [0.6, 1.2, 1.8]) == 2 and suurim_tasuv([0.1], [0.6]) == 0 and \
       suurim_tasuv([1.0, 0.1, 2.0], [0.6, 1.2, 1.8]) == 1          # vahepeal ei tasu -> katkeb
set_style()
jn = load_junctions().set_index("mp_id")
a = sts_andmed()
D = viivitus(a["ix"], a["V"], a["pa"])
prof = pd.DataFrame(D).groupby(a["ix"]["mp_id"].to_numpy()).median()          # ristmik x pilu, s/sõiduk
minut = np.arange(24 * 60)
d_min = {mp: np.interp(minut, np.arange(96) * 15 + 7.5, prof.loc[mp].to_numpy()) for mp in prof.index}
dlt = np.arange(1, NIHE_MAX + 1)

rows, kõverad = [], {}
for nimi, mps in KORIDORID.items():
    mps = [m for m in mps if m in d_min]
    dk = sum(d_min[m] for m in mps) / 60                                       # koridori viivitus, min
    for tipp, (lo, hi) in AKNAD.items():
        t = lo + int(np.argmax(dk[lo:hi]))
        s_e, s_l = dk[t] - dk[t - dlt], dk[t] - dk[t + dlt]
        # graafikukulu saabumise nihke järgi: varem lahkudes saabub Δ + sääst varem, hiljem lahkudes Δ - sääst hiljem
        # (kui sääst on suurem kui Δ, saabub ta ikkagi varem kui soovitud -> varajase saabumise kulu)
        h_e = BETA * (dlt + s_e)
        h_l = np.where(dlt - s_l >= 0, GAMMA * (dlt - s_l), BETA * (s_l - dlt))
        kõverad[(nimi, tipp)] = (s_e, s_l, t, dk[t], len(mps))
        r = dict(koridor=nimi, tipp=tipp, ristmikud=" ".join(a["pa"].loc[m, "kood"] for m in mps), ristmikke=len(mps),
                 tipuaeg=hhmm(t / 60), viivitus_tipus_min=dk[t], viivitus_min_paeval_min=dk[6 * 60:20 * 60].min(),
                 saast_varem_max_min=s_e.max(), saast_varem_nihe=int(dlt[np.argmax(s_e)]),
                 saast_hiljem_max_min=s_l.max(), saast_hiljem_nihe=int(dlt[np.argmax(s_l)]),
                 tasub_varem_kuni_min=suurim_tasuv(s_e, h_e), tasub_hiljem_kuni_min=suurim_tasuv(s_l, h_l))
        for n in (15, 30, 60):
            # suurim kaal, mille juures nihe n tasub (hind saabumise nihke järgi, vt h_e ja h_l)
            r[f"vajalik_kaal_varem_{n}"] = s_e[n - 1] / (n + s_e[n - 1])
            r[f"vajalik_kaal_hiljem_{n}"] = s_l[n - 1] / (n - s_l[n - 1]) if n > s_l[n - 1] else np.inf
        # mitu sama suurt ristmikku peaks teel olema, et 15 min varem tasuks: n s >= BETA (15 + n s)
        r["ristmikke_vaja_15min_varem"] = (BETA * 15 / ((1 - BETA) * s_e[14] / len(mps))) if s_e[14] > 0 else np.nan
        rows.append(r)
k = pd.DataFrame(rows)
save_table(k.round(3), "40_2_juhi_tasuvus")

# --- joonis ---------------------------------------------------------------------------------------------------------------
fig, axes = plt.subplots(2, len(KORIDORID), figsize=(17, 8.5), sharex=True)
for j, nimi in enumerate(KORIDORID):
    for i, tipp in enumerate(AKNAD):
        ax = axes[i, j]
        s_e, s_l, t, d0, n = kõverad[(nimi, tipp)]
        r = k[(k["koridor"] == nimi) & (k["tipp"] == tipp)].iloc[0]
        pos = lambda x: np.where(x > 0, x, np.nan)                         # logaritmteljel ainult > 0
        ax.plot(dlt, pos(s_e), color=C_BLUE, lw=2.4, label="sääst: varem")
        ax.plot(dlt, pos(s_l), color=C_ORANGE, lw=2.4, label="sääst: hiljem")
        ax.plot(dlt, BETA * dlt, color=C_BLUE, ls="--", lw=1.5, label=f"hind: varem ({BETA:.2f} x nihe)".replace(".", ","))
        ax.plot(dlt, GAMMA * dlt, color=C_ORANGE, ls="--", lw=1.5,
                label=f"hind: hiljem ({GAMMA:.2f} x nihe)".replace(".", ","))
        ax.set_yscale("log")
        ax.set_ylim(0.01, 400)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
        ax.set_xlim(0, NIHE_MAX)
        ax.set_xticks(range(0, NIHE_MAX + 1, 30))
        tas = lambda m: "ei tasu" if m == 0 else f"tasub kuni {m} min"
        ax.text(0.97, 0.03, f"suurim sääst {max(s_e.max(), s_l.max()):.1f} min\n".replace(".", ",")
                + f"varem: {tas(r.tasub_varem_kuni_min)}\nhiljem: {tas(r.tasub_hiljem_kuni_min)}",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=8.5, color=TEXT,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=GRID, alpha=0.92))
        ax.set_title(f"{nimi}, {TIPP_TXT[tipp]} (tipp {hhmm(t / 60)}, {n} ristmikku)", fontsize=10)
        if j == 0:
            ax.set_ylabel("minutit")
        if i == 1:
            ax.set_xlabel("nihe tipuajast, min")
axes[0, 0].legend(fontsize=8, loc="center right", bbox_to_anchor=(0.98, 0.6), ncol=2)
fig.suptitle("Kas juhile tasub tipust nihkuda: säästetud ooteaeg loendatud ristmikel (mudel A) vs ajakaotuse hind "
             "(Small 1982), log-skaala; jooned ei ristu = ei tasu", x=0.01, ha="left", fontweight="bold", fontsize=12)
fig.tight_layout()
save(fig, "40_2_01_juhi_tasuvus")

print(k[["koridor", "tipp", "ristmikke", "tipuaeg", "viivitus_tipus_min", "saast_varem_max_min", "saast_varem_nihe",
         "saast_hiljem_max_min", "saast_hiljem_nihe", "tasub_varem_kuni_min", "tasub_hiljem_kuni_min",
         "vajalik_kaal_varem_30", "ristmikke_vaja_15min_varem"]].round(2).to_string(index=False))
