"""
08 - Ühe ööpäeva sõidukipõhised loendused (Traffic 24h, kolmapäev 30.09.2026): liikluse jaotus loendurite, suundade ja
ristmike vahel ning 5 min osakaalud 15 min pilu sees. Jooniseid see skript ei tee; 06 ja 07 kasutavad sama 5 min
jaotust (common.five_min_shares), et arvutada tipu algus ja liikluse keskaeg 5 min täpsusega.

SISEND
  common.load_vehicles()     iga sõiduk eraldi rida (import_raw.traffic24h_tallinn): ristmik, kanal, aeg, kiirus, pikkus
  common.load_manoeuvres()   mida iga ristmiku kanal loendab: suund (manööver, T08 "Suund"), lähte- ja sihtharu

ARVUTUS
  a) Osakaalud: sõidukite arv ööpäevas iga loenduri (kanali) kohta; loenduri osakaal oma suunast ja ristmikust, suuna
     osakaal ristmikust ja ristmiku osakaal kõigist ristmikest (%).
  b) 5 min osakaalud: iga ristmiku iga 15 min pilu jagatakse kolmeks 5 min osaks (osa_0, osa_1, osa_2 = pilu
     esimesed, keskmised ja viimased 5 min; summa 100%). Üks päev on mürane, seega saab pilu kõigi ristmike
     koondjaotuse (veerg linna_jaotus), kui ristmikul on pilus alla 30 sõiduki, mõni 5 min osa on tühi või on >= 150
     sõiduki juures tühi minut (lühike rike).
  Kontrolliks trükitakse, kui palju erineb 5 min jaotus tipptundidel ühtlasest (33,3%).

VÄLJUND (kaust valjund/)
  08_osakaalud.csv        read kolmel tasemel (ristmik, suund, loendur): sõidukeid ööpäevas ja osakaalud
  08_5min_osakaalud.csv   ristmik x 15 min pilu: osa_0, osa_1, osa_2 (%), sõidukeid pilus, kas kasutati koondjaotust
"""
import pandas as pd

from common import (load_vehicles, five_min_shares, slot_label, save_table, load_manoeuvres, VEHICLE_DAY)

print("Laen sõidukipõhised loendused...")
v = load_vehicles()
day = v[v["ts"].dt.normalize() == pd.Timestamp(VEHICLE_DAY)]
print(f"{VEHICLE_DAY}: {len(day):,} sõidukit, {day['mp_id'].nunique()} ristmikku")

# --- a) Osakaalud: loendur, suund, ristmik --------------------------------------------------------
dm = load_manoeuvres()
dm = dm.assign(mp_id=dm["mp"].str[2:].astype(int)).rename(columns={"channel": "kanal"})
cols = ["mp_id", "mp", "intersection", "direction_id", "manoeuvre", "from_leg", "to_leg", "traffic_direction"]
ch = (day.groupby(["mp_id", "kanal"]).size().rename("soidukeid").reset_index()
      .merge(dm[cols + ["kanal"]], on=["mp_id", "kanal"], how="left"))
ch["mp"] = "MP" + ch["mp_id"].astype(str).str.zfill(2)
ch["intersection"] = ch.groupby("mp_id")["intersection"].transform("first")
ch["direction_id"] = ch["direction_id"].fillna(-1).astype(int)        # -1 = kanal pole T08 suundades
ch["manoeuvre"] = ch["manoeuvre"].fillna("(kanal pole T08 suundades)")

mp_tot = ch.groupby("mp_id")["soidukeid"].transform("sum")
ch["osakaal_suunast_%"] = ch["soidukeid"] / ch.groupby(["mp_id", "direction_id"])["soidukeid"].transform("sum") * 100
ch["osakaal_ristmikust_%"] = ch["soidukeid"] / mp_tot * 100
sd = (ch.groupby(cols[:5], dropna=False)
      .agg(soidukeid=("soidukeid", "sum"), from_leg=("from_leg", "first"), to_leg=("to_leg", "first"),
           traffic_direction=("traffic_direction", "first"), kanalid=("kanal", lambda s: ", ".join(map(str, s))))
      .reset_index())
sd["osakaal_ristmikust_%"] = sd["soidukeid"] / sd.groupby("mp_id")["soidukeid"].transform("sum") * 100
rm = ch.groupby(["mp_id", "mp", "intersection"])["soidukeid"].sum().reset_index()
rm["osakaal_koigist_%"] = rm["soidukeid"] / rm["soidukeid"].sum() * 100
out = pd.concat([rm.assign(tase="ristmik", _o=0), sd.assign(tase="suund", _o=1), ch.assign(tase="loendur", _o=2)])
out = out.sort_values(["mp_id", "_o", "direction_id", "kanal"])
save_table(out[["tase", "mp", "intersection", "direction_id", "manoeuvre", "kanal", "kanalid", "from_leg", "to_leg",
                "traffic_direction", "soidukeid", "osakaal_suunast_%", "osakaal_ristmikust_%", "osakaal_koigist_%"]]
           .round(2), "08_osakaalud")

# --- b) 5 min osakaalud 15 min pilu sees -------------------------------------------------------------
sh, fb = five_min_shares(v, flags=True)
n = day.groupby([day["mp_id"], (day["ts"].dt.hour * 4 + day["ts"].dt.minute // 15).rename("slot")]).size()
t5 = (sh * 100).round(2).add_prefix("osa_").reset_index()
t5["soidukeid_15min"] = n.reindex(sh.index, fill_value=0).values
t5["linna_jaotus"] = fb.values
t5.insert(1, "mp", "MP" + t5["mp_id"].astype(str).str.zfill(2))
t5.insert(3, "aeg", t5["slot"].map(slot_label))
save_table(t5.drop(columns="mp_id"), "08_5min_osakaalud")

# kontroll: kui palju erineb 5 min jaotus ühtlasest (33,3%) tipptundides, linna kokku
city = day.assign(m5=day["ts"].dt.hour * 12 + day["ts"].dt.minute // 5).groupby("m5").size()
for name, (a, b) in {"hommik": (6, 10), "õhtu": (15, 19)}.items():
    c = city.loc[a * 12:b * 12 - 1]
    s15 = c.groupby(c.index // 3).transform("sum")
    print(f"{name}: 5 min osa 15 min pilust {(c / s15 * 100).min():.1f}...{(c / s15 * 100).max():.1f}% "
          f"(ühtlane = 33,3%)")
print("Valmis.")
