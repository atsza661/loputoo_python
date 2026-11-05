"""
Käivitab kõik analüüsiskriptid õiges järjekorras. Tulemused (joonised .png ja tabelid .csv) lähevad kausta valjund/.

JÄRJEKORD
  01-05              maanteeloendurid ja kütusemüük (üksteisest sõltumatud)
  07 enne 06         06 kasutab 07 maanteeprofiile (07_maantee_profiilid.csv)
  08, 09, 10         sõidukipõhised loendused; 10 kasutab 09 väljundit
  12, 13             kasutavad 06 ja 09 väljundit
  14                 pikkusrühmad kooliajal ja koolivaheajal (teistest sõltumatu)
  20                 kõik 15 min andmepunktid kaardil: maanteede suunad ja ristmikud (teistest sõltumatu)
  21                 tipptunni algus ja liikluse keskaeg kaardil 15 min andmetest (kasutab 20 tabelit)
  22                 sama nädalavahetuse pärastlõuna ja õhtu kohta (kasutab 20 tabelit)
  23                 21 tipuajad soojuskaardina: silutud värvipind ja samaaja jooned (kasutab 21 tabelit)
  24                 logija nädala ristmike koormusaste 5 min kaupa: kaardid, GIF, MP4 (teistest sõltumatu; pikk)
  25                 sama päevatüübi kaupa (T-N, E, R, L, P) 23 kujundusega (kasutab 24 tabelit; pikk)
  26                 ajanihke tundlikkus: tipptunni maht ja aeg, kui 1-15% sõitjatest nihkub +-15...60 min
  27                 läbilaskevõime: ristmike ja sissesõiduteede piir, Tallinna hommikuse sissesõidu piir (kasutab 24)
  28                 koridorid (Tartu, Paldiski, Tammsaare, Sõpruse): ummiku aja-ruumi muster (kasutab 24 ja 27)
  29                 kalender: linna liiklus iga päeva kohta 2024-2026, % tavalisest tööpäevast
  30                 aastavõrdlus: sama sügis 2025 vs 2026 iga ristmiku kohta
  31                 tipptunni näitajad ristmike kaupa: K-tegur, PHF, hommiku- ja õhtutipu maht
  32                 sisse- ja väljasõidu tasakaal kellaaja järgi (maanteed ja logija nädala ristmikud)
  33                 mõõdetud küllastusvoog vs 27 eeldus 1800 ja rohelise osa g/C (kasutab 10, 24 ja 27 tabelit)
  34                 ristmike profiilitüübid (tööpäeva kuju klasterdamine) kaardil
  35                 kas tipp hajub: tipptunni osakaal, keskaeg ja teravus kuude kaupa õppeaastate võrdluses
  36                 liikluse lagundamine kalendritunnusteks (regressioon) ja erandpäevad (kasutab 29 tabelit)
  37                 tipu ennustatavus: linna tööpäeva lehvikdiagramm, ristmike tipu kõikumine päevast päeva
  38                 ristmike korrelatsioonivõrk: päevast päeva kõrvalekallete seos ja kaugus
  39                 pöörded tipptundidel (Sankey) neljal ristmikul
  40_0               murdepunkt: mitu % autodest peab tipust kaduma või nihkuma, et ristmikel oleks märgatavalt kiirem
                     (mudel A viivitus, mudel B ummikuosa, maanteekontroll; kasutab 09, 24, 27 ja 33 tabelit)
  40_1 - 40_3        suurim nihe, mis veel aitab; juhi tasuvus koridoridel; vähim nihe täisvõiduks (kasutavad 40_0 ja
                     34 tabelit)
  07_2, 06_2         07 ja 06 teine versioon: muutuva pikkusega tipuaeg (sama aeglane või sama tihe kui tavalises
                     tipus); 07_2 kasutab 07 tabeleid, 06_2 07 ja 07_2 tabeleid; mõlemad mudelit A (09, 27, 33)
  07 ja 06 uuesti    suunaanalüüs: SUUND=LSS (linna sisse) ja LVS (linnast välja), kumbki 5 min ja 15 min sammuga
                     -> valjund/LSS ja valjund/LVS (15 min failidel lõpp _15min)
  11                 arvukontrollid kõige lõpus (kasutab ka LSS/LVS väljundit)
  Kui mõni skript ebaõnnestub, jääb käivitus seisma ja näitab, milline.

EELDUSED
  1) Andmed on PostgreSQL andmebaasis (tabelid: vt common.py). Ühenduse andmed on failis db_yhendus.txt selle faili
     kõrval (üks rida kujul host=... port=5432 dbname=... user=...) või libpq keskkonnamuutujates PGHOST, PGPORT,
     PGDATABASE, PGUSER. Piisab lugemisõigusega kasutajast; parool on libpq paroolifailis (~/.pgpass), mitte koodis.
     Suured päringud jäävad kohalikku puhvrisse db_cache/ ja uuenevad ise, kui tabel on muutunud.
  2) Debianil (süsteemi Pythonisse pip ei paigalda) virtuaalkeskkond, nt repo kõrval:
       python3 -m venv ../.venv && ../.venv/bin/pip install pandas numpy matplotlib seaborn scipy statsmodels pillow \
           psycopg2-binary python-dateutil imageio-ffmpeg
     ja skriptid käsuga ../.venv/bin/python (imageio-ffmpeg annab 24-le ffmpeg-i MP4 jaoks)
  3) Kaartide satelliit-/ortofototaust (04, 07, 10, 13) laetakse esimesel käivitusel internetist ja hoitakse kaustas
     tile_cache/. Internetita joonistatakse kaardid ilma taustata. Välja lülitamine: common.py -> SATELLIIT = False
  4) 09 teeb joonise iga ristmiku ja päeva kohta (kaust valjund/09_04_loendurid/); mitme päeva andmetega võtab see
     minuteid. Välja lülitamine: 09_fooritsuklid.py -> RISTMIKU_JOONISED = False

KÄIVITAMINE
  Kõik:                 python3 run_all.py
  Üks skript:           python3 02_riik.py
  Üks suunaanalüüs:     keskkonnamuutujad SUUND=LSS ja RES=15, siis python3 07_tallinn_maanteed.py ja python3 06_tallinn.py
"""
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = ["01_kvaliteet.py", "02_riik.py", "03_maakond.py", "04_tee.py", "05_kutusekulu_mudel.py",
           "07_tallinn_maanteed.py", "06_tallinn.py",                       # 06 kasutab 07 maanteeprofiile
           "08_ristmikud_24h.py", "09_fooritsuklid.py", "10_ummikute_lisaanaluus.py",   # 10 kasutab 09 väljundit
           "12_loomulikud_katsed.py",                                        # pärast 06 ja 09
           "13_maanteelaine.py",                                             # pärast 09
           "14_pikkusruhmad_vaheaeg.py", "20_kaardid_15min.py", "21_tipuajad_kaardil.py",   # 21 ja 22 kasutavad 20 tabelit
           "22_nadalavahetuse_ohtu.py", "23_soojuskaart_tipuajad.py",                  # 23 kasutab 21 tabelit
           "24_soojus_ajatelg.py", "25_soojus_paevatyybid.py",                 # 25 kasutab 24 tabelit
           "26_ajanihe_tundlikkus.py",
           "27_labilaskevoime.py", "28_koridorid.py",                         # 27 ja 28 kasutavad 24, 28 ka 27 tabelit
           "29_kalender.py", "30_aastavordlus.py", "31_tipu_naitajad.py", "32_suunad_tunniti.py",
           "33_kullastusvoog_eeldus.py",                                       # 33 kasutab 10, 24 ja 27 tabelit
           "34_profiilituubid.py", "35_tipu_hajumine.py",
           "36_lagundus.py",                                                   # 36 kasutab 29 tabelit
           "37_ennustatavus.py", "38_korrelatsioonivork.py", "39_poorded.py",
           "40_0_murdepunkt.py",                                               # 40_0 kasutab 09, 24, 27 ja 33 tabelit
           "40_1_suurim_nihe.py", "40_2_juhi_tasuvus.py", "40_3_vahim_nihe.py",   # 40_1 ja 40_3 kasutavad 40_0 ja 34
           "07_2_tallinn_maanteed.py", "06_2_tallinn.py"]                     # 06_2 kasutab 07_2 tabelit

env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONWARNINGS="ignore")
env.pop("SUUND", None)
env.pop("RES", None)
RUNS = [(s, env) for s in SCRIPTS]
# Suunaanalüüs: 07 ja 06 eraldi LSS (linna sisse, hommik) ja LVS (linnast välja, õhtu) -> valjund/LSS, valjund/LVS,
# kumbki 5 min (arvutatud) ja 15 min (toorandmed, *_15min) sammuga
RUNS += [(s, dict(env, SUUND=d, RES=r)) for d in ["LSS", "LVS"] for r in ["5", "15"]
         for s in ["07_tallinn_maanteed.py", "06_tallinn.py"]]
RUNS += [("11_kontrollid.py", env)]          # arvukontrollid kõige lõpus (kasutab ka LSS/LVS väljundit)
for s, e in RUNS:
    print(f"\n=== {s} {e.get('SUUND', '')} {e.get('RES', '')} ===", flush=True)
    t = time.time()
    r = subprocess.run([sys.executable, str(HERE / s)], cwd=HERE, env=e)
    if r.returncode != 0:
        sys.exit(f"{s} ebaõnnestus (kood {r.returncode})")
    print(f"({time.time() - t:.0f} s)", flush=True)
print(f"\nValmis. Tulemused: {HERE / 'valjund'}")
