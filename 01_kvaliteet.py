"""
01 - Andmete kvaliteet: kui suur osa maanteede püsiloendurite andmetest on kasutatav
(lõputöö ptk 2.3 "Andmete ettevalmistamine ja piirangud").

SISEND
  common.load_daily()      maanteeloendurite tunniloendustest (andmebaasi tabel import_raw.hourly_count_csv) liidetud
                           päevasummad iga loenduri iga kanali (sõiduraja) kohta: tunniridade arv päevas (hours) ning
                           sõidukid 10 sõidukiklassi ja 11 kiirusvahemiku kaupa
  common.load_locations()  loendurite nimed, maakonnad ja teenumbrid (traffic.counter_location)

ARVUTUS
  1) Tunniridade arv ööpäevas. Iga kanal-päev liigitatakse tunniridade arvu järgi: <= 22 = osaline päev,
     23-25 = täispäev (23 ja 25 on kellakeeramise päevad), 26-43 = segane, 44-50 = sama päev on imporditud kaks
     korda, > 50 = muu. Iga aasta kohta leitakse, mitu % kanal-päevadest igasse liiki kuulub.
  2) Liigi- ja kiirussumma kooskõla. Sama kanal-päeva sõidukid on loetud kaks korda - klasside ja kiirusvahemike
     kaupa. Leitakse ridade osakaal, kus need summad erinevad üle 0,5 sõiduki, ja erinevuse suurus protsendina
     kõigist sõidukitest.
  3) Kehtivad loendurid (common.counter_month). Päev kehtib, kui tunniridu on 23-25 (või 44-50; siis teisendatakse
     summad 24 tunnile) ja sõidukeid on üle nulli. Kanal-kuu kehtib, kui kehtivaid päevi on >= 15. Loendur-kuu
     kehtib, kui kehtivate kanalite arv ei ole väiksem loenduri tavalisest kanalite arvust (ühe raja väljalangemine
     ei tohi paista liikluse langusena). Iga kuu kohta loetakse kehtivate loendurite arv.
  4) Kahtlased loendur-kuud: maht erineb sama loenduri sama kalendrikuu mediaanist üle 1,75 korra või alla
     0,4 korra (common.volume_anomaly) või mõne sõidukiklassi osakaal erineb loenduri enda mediaanist üle
     25 protsendipunkti (common.class_anomaly).

VÄLJUND (kaust valjund/)
  01_tunnid_paevas.png
      Näitab: kui suur osa iga aasta kanal-päevadest on täielikud, osalised või topelt imporditud (arvutus 1).
      Kuidas: rõhtsad virnastatud tulbad, üks tulp aasta kohta (varaseim üleval); x-telg = osakaal kanal-päevadest, %.
      Punane = osaline päev, sinine = täispäev, oranž = topelt imporditud, hall = muud.
  01_loendurid_kuus.png
      Näitab: mitu loendurit annab igas kuus kasutatavaid andmeid (arvutus 3).
      Kuidas: joondiagramm; x-telg = aeg (märgid aastate kaupa), y-telg = kehtivate loendurite arv (algab nullist).
  01_kaetus_heatmap.png
      Näitab: millistel kuudel on iga loenduri andmed kasutatavad.
      Kuidas: ruudustik; rida = loendur (silt "maakond · nimi", järjestatud maakonna ja teenumbri järgi), veerg = kuu
      analüüsiakna algusest lõpuni (x-teljel aastad). Sinine ruut = kehtiv loendur-kuu, hele ruut = andmeid pole või
      need ei kehti.
  01_kvaliteet_loendurid.csv     iga loenduri kanal-päevade arv, kehtivate osakaal, topeltpäevad, esimene ja viimane
                                 päev, kehtivate kuude arv
  01_kahtlased_loendurkuud.csv   kahtlase mahu või klassijaotusega loendur-kuud (arvutus 4)
  01_kvaliteet_kokkuvote.csv     peamised arvud tekstis kasutamiseks (trükitakse ka ekraanile)
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import (load_daily, load_locations, counter_month, set_style, save, save_table,
                    CLASS_COLS, SPEED_COLS, C_BLUE, C_ORANGE, C_AQUA, C_RED, C_GRAY, TEXT2,
                    START, END, month_axis)

set_style()
print("Laen andmeid...")
d = load_daily()
loc = load_locations()

# 1) Tunnid päevas ---------------------------------------------------------------
d["aasta"] = d["paev"].dt.year
bins = [0, 22, 25, 43, 50, 1000]
labels = ["Osaline päev (≤22 h)", "Täispäev (23-25 h)", "26-43 h",
          "Topelt imporditud (44-50 h)", ">50 h"]
d["tunnid_kl"] = pd.cut(d["hours"], bins=bins, labels=labels)
ct = pd.crosstab(d["aasta"], d["tunnid_kl"], normalize="index") * 100
ct = ct.loc[:, (ct > 0).any()]

fig, ax = plt.subplots(figsize=(8, 4))
colors = {labels[0]: C_RED, labels[1]: C_BLUE, labels[2]: C_GRAY,
          labels[3]: C_ORANGE, labels[4]: C_GRAY}
left = np.zeros(len(ct))
for col in ct.columns:
    ax.barh(ct.index.astype(str), ct[col], left=left, color=colors[col], label=col,
            edgecolor="white", linewidth=1.5)
    left += ct[col].values
ax.invert_yaxis()
ax.set_xlabel("Osakaal kanal-päevadest, %")
ax.set_title("Tunniridade arv ööpäevas kanali kohta")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3, fontsize=9)
save(fig, "01_tunnid_paevas")

# 2) Liigi- ja kiirussumma kooskõla ---------------------------------------------
tot_c = d[CLASS_COLS].sum(axis=1)
tot_s = d[SPEED_COLS].sum(axis=1)
mismatch_share = (np.abs(tot_c - tot_s) > 0.5).mean() * 100
mismatch_rel = np.abs(tot_c - tot_s).sum() / tot_c.sum() * 100

# 3) Kehtivad loendurid kuus ----------------------------------------------------
cm = counter_month(d)
cm = cm.merge(loc[["id", "maakond", "nimi", "tee_nr"]], on="id", how="left")
n_month = cm.groupby("kuu")["id"].nunique()

fig, ax = plt.subplots(figsize=(9, 3.8))
ax.plot(n_month.index.to_timestamp(), n_month.values, color=C_BLUE)
ax.set_ylim(0, None)
ax.set_ylabel("Loendureid")
ax.set_title("Kehtivate loendurite arv kuus (≥15 täispäeva, kõik suunad)")
month_axis(ax)
save(fig, "01_loendurid_kuus")

# 4) Heatmap: loendur x kuu -------------------------------------------------------
months = pd.period_range(START, END, freq="M")
valid = (cm.assign(v=1).pivot_table(index="id", columns="kuu", values="v", aggfunc="max")
         .reindex(columns=months).fillna(0))
order = (loc.set_index("id").loc[valid.index, ["maakond", "tee_nr"]]
         .sort_values(["maakond", "tee_nr"]).index)
valid = valid.loc[order]
fig, ax = plt.subplots(figsize=(10, 14))
ax.imshow(valid.values, aspect="auto", cmap=plt.matplotlib.colors.ListedColormap(["#f0efec", C_BLUE]),
          interpolation="nearest")
ax.set_yticks(range(len(valid)))
lab = loc.set_index("id").loc[valid.index]
ax.set_yticklabels([f"{m} · {n}" for m, n in zip(lab["maakond"], lab["nimi"])], fontsize=5.5)
xt = [i for i, m in enumerate(months) if m.month == 1]
ax.set_xticks(xt)
ax.set_xticklabels([months[i].year for i in xt])
ax.grid(False)
ax.set_title("Loendurite kehtivad kuud (sinine = kasutatav)")
save(fig, "01_kaetus_heatmap")

# 5) Tabelid -----------------------------------------------------------------------
per = (d.groupby("id").agg(kanal_paevi=("paev", "size"),
                           kehtivaid=("kehtiv", "sum"),
                           duplikaat_paevi=("duplikaat", "sum"),
                           esimene=("paev", "min"), viimane=("paev", "max"))
       .reset_index())
per["kehtiv_%"] = per["kehtivaid"] / per["kanal_paevi"] * 100
per = per.merge(cm.groupby("id")["kuu"].nunique().rename("kehtivaid_kuid").reset_index(),
                on="id", how="left").fillna({"kehtivaid_kuid": 0})
per = loc[["id", "nimi", "maakond", "tee_nr", "tee_nimi", "liik"]].merge(per, on="id", how="right")
save_table(per.sort_values(["maakond", "tee_nr"]), "01_kvaliteet_loendurid")

# Kahtlased loendur-kuud (vt common.volume_anomaly ja class_anomaly)
flag = cm[cm["maht_kahtlane"] | cm["klass_kahtlane"]].copy()
flag["kuu"] = flag["kuu"].astype(str)
save_table(flag[["id", "nimi", "maakond", "tee_nr", "kuu", "kokku", "raske",
                 "maht_kahtlane", "klass_kahtlane"]].sort_values(["id", "kuu"]),
           "01_kahtlased_loendurkuud")

summary = pd.DataFrame([
    ("Loendureid andmetes", d["id"].nunique()),
    ("Loendureid asukohatabelis", len(loc)),
    ("Kanal-päevi kokku", len(d)),
    ("Kehtivaid kanal-päevi, %", d["kehtiv"].mean() * 100),
    ("Topelt imporditud kanal-päevi (44-50 h)", int(d["duplikaat"].sum())),
    ("2019 osaliste päevade osakaal, %", (d.loc[d.aasta == 2019, "hours"] <= 22).mean() * 100),
    ("Liigi- ja kiirussumma erinevad, % ridadest", mismatch_share),
    ("Liigi- ja kiirussumma erinevus, % sõidukitest", mismatch_rel),
    ("Loendur-kuid kokku", len(cm)),
    ("Kahtlane maht (välja jäetud)", int(cm["maht_kahtlane"].sum())),
    ("Kahtlane klassijaotus (välja klassianalüüsist)", int(cm["klass_kahtlane"].sum())),
    ("Kehtivaid loendureid kuus, min", n_month.min()),
    ("Kehtivaid loendureid kuus, max", n_month.max()),
    ("Analüüsiaken", f"{START} ... {END}"),
], columns=["näitaja", "väärtus"])
save_table(summary, "01_kvaliteet_kokkuvote")
print(summary.to_string(index=False))
