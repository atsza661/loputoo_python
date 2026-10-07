"""
Käivitab kõik analüüsiskriptid õiges järjekorras. Tulemused (joonised .png ja tabelid .csv) lähevad kausta valjund/.

JÄRJEKORD
  01-05              maanteeloendurid ja kütusemüük (üksteisest sõltumatud)
  07 enne 06         06 kasutab 07 maanteeprofiile (07_maantee_profiilid.csv)
  08, 09, 10         sõidukipõhised loendused; 10 kasutab 09 väljundit
  12, 13             kasutavad 06 ja 09 väljundit
  07 ja 06 uuesti    suunaanalüüs: SUUND=LSS (linna sisse) ja LVS (linnast välja), kumbki 5 min ja 15 min sammuga
                     -> valjund/LSS ja valjund/LVS (15 min failidel lõpp _15min)
  11                 arvukontrollid kõige lõpus (kasutab ka LSS/LVS väljundit)
  Kui mõni skript ebaõnnestub, jääb käivitus seisma ja näitab, milline.

EELDUSED
  1) Andmed on PostgreSQL andmebaasis (tabelid: vt common.py). Ühenduse andmed on failis db_yhendus.txt selle faili
     kõrval (üks rida kujul host=... port=5432 dbname=... user=...) või libpq keskkonnamuutujates PGHOST, PGPORT,
     PGDATABASE, PGUSER. Piisab lugemisõigusega kasutajast; parool on libpq paroolifailis (pgpass.conf), mitte koodis.
     Suured päringud jäävad kohalikku puhvrisse db_cache/ ja uuenevad ise, kui tabel on muutunud.
  2) pip install pandas numpy matplotlib seaborn scipy statsmodels pillow psycopg2-binary python-dateutil
  3) Kaartide satelliit-/ortofototaust (04, 07, 10, 13) laetakse esimesel käivitusel internetist ja hoitakse kaustas
     tile_cache/. Internetita joonistatakse kaardid ilma taustata. Välja lülitamine: common.py -> SATELLIIT = False

KÄIVITAMINE
  Kõik:                 python run_all.py
  Üks skript:           python 02_riik.py
  Üks suunaanalüüs:     keskkonnamuutujad SUUND=LSS ja RES=15, siis python 07_tallinn_maanteed.py ja python 06_tallinn.py
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
           "13_maanteelaine.py"]                                             # pärast 09

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
