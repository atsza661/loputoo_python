"""
Ühised funktsioonid kõigile analüüsiskriptidele (01-13): andmete lugemine andmebaasist, puhastamine, liiklusindeksid,
tipptunni ja ummiku näitajad, kaartide taust ja jooniste stiil. Iga skript impordib siit vajaliku; iga funktsiooni
juures on kirjas, mida see võtab, mida tagastab ja kuidas arvutab.

ANDMED
  Kõik andmed loetakse PostgreSQL andmebaasist (funktsioonid sql, tabel, puhver); kohalikke andmefaile ei loeta.
  Ühenduse andmed ei ole koodis: fail db_yhendus.txt või libpq keskkonnamuutujad (vt allpool osa "Andmebaas").
  Tabelid:
    import_raw.hourly_count_csv          maanteede püsiloendurite tunniloendused (sõidukiklassid 1-10, kiirusvahemikud)
    import_raw."15m_count"               samade loendurite 15 min loendused
    traffic.counter_location,            loendurite asukohad ja radade nimed
    traffic.counter_channel
    import_raw.jaemuuk_tanklast_monthly, kütuse jaemüük tanklatest kuu ja poolkuu kaupa
    import_raw.jaemuuk_tanklast_biweekly
    import_raw.bensiin_maakond_monthly,  kütusemüük maakonniti
    import_raw.diisel_maakond_monthly
    import_raw.labisoit                  põhimaanteede aastane läbisõit
    import_raw.traffic_15min_tallinn     Tallinna ristmike 15 min loendused (seire.tallinn.ee, aruanne T09)
    import_raw.tallinn_junction,         ristmikud; mida iga kanal loendab; kontrolleri pordi ja ristmiku vastavus
    import_raw.tallinn_detector_manoeuvre,
    import_raw.tallinn_serial_port
    import_raw.traffic24h_tallinn        ristmike sõidukipõhised kirjed (iga sõiduk eraldi rida)
    import_raw.datex_site,               DATEX II loenduskohad ja nende 15 min vood
    import_raw.datex_15min
  Suurte päringute tulemus hoitakse kohalikus puhvris db_cache/ ja uuendatakse ise, kui tabel on muutunud (puhver).

SEADED KESKKONNAMUUTUJATEGA (skriptid 06 ja 07)
  SUUND=LSS|LVS   ainult linna sisse (LSS) või linnast välja (LVS) suunduv liiklus; väljund kausta valjund/LSS või
                  valjund/LVS ja joonise alla suuna märge
  RES=5|15        ristmike ajasamm: 5 min (vaikimisi; 15 min loendused jagatud sõidukipõhise ööpäeva järgi) või toored
                  15 min loendused (failinimede lõppu _15min)

VÄLJUND
  save() ja save_table() kirjutavad joonised (.png) ja tabelid (.csv, UTF-8) kausta valjund/.

FAILI OSAD
  sõidukiklassid ja värvid; jooniste stiil; andmebaas; maanteeloendurite laadimine ja puhastus (load_daily,
  counter_month, traffic_index); kütusemüük; aegridade abifunktsioonid (yoy, stl_resid, corr_pair); Tallinna ristmikud
  (kalender, load_tallinn, sõidukipõhised kirjed, 5 min jaotus, DATEX); tipptunnid, hajutamine ja ummiku määratlus
  (peak_metrics, shift_peak, ummikumask); stsenaariumid 40_* jaoks (foori viivitus hcm_viivitus, ummikuosa seos pav,
  sts_andmed, sts_naitajad, sts_nihete_voit, päevast päeva kõikumine paeva_mura); muutuva pikkusega tipuaeg 06_2 ja
  07_2 jaoks (tipuaja_lavi, tipuaeg, tipuaja_naitajad, ristmike_tipumura); satelliitaluskaart (add_basemap).
"""
import contextlib
import functools
import inspect
import os
import tempfile
import re
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
import seaborn as sns

DATA_DIR = Path(__file__).resolve().parent
# Suunaanalüüs (06, 07): keskkonnamuutuja SUUND=LSS (ainult linna sisse) või LVS (ainult linnast välja)
# -> ristmikel ainult selle suuna kanalid, maanteedel sisse/välja suund, väljund kausta valjund/LSS|LVS
SUUND = (os.environ.get("SUUND") or "").upper() or None
OUT_DIR = DATA_DIR / "valjund" / (SUUND or "")
OUT_DIR.mkdir(parents=True, exist_ok=True)
SUUND_TXT = {"LSS": "Ainult LSS: linna sisse suunduv liiklus (fookus hommikul)",
             "LVS": "Ainult LVS: linnast välja suunduv liiklus (fookus õhtul)"}.get(SUUND, "")
SUUND_MAANTEE = {"LSS": "sisse", "LVS": "välja"}.get(SUUND)
# Ristmike ajasamm (06, 07): RES=5 (vaikimisi) = 15 min loendused jagatud 5 min osadeks sõidukipõhise
# ööpäeva järgi; RES=15 = toored 15 min loendused, failinimede lõppu _15min
RES = int(os.environ.get("RES") or 5)
SUFFIX = "_15min" if RES == 15 else ""
RES_TXT = {5: "5 min samm (arvutatud)", 15: "15 min samm (toorandmed)"}[RES]

# Analüüsiaken: 2019. a liiklusandmed on katkendlikud (enamikul päevadel 1-3 tundi),
# kütuse andmed lõpevad 2026-08.
START = pd.Period("2020-01", "M")
END = pd.Period("2026-08", "M")
BASE_YEAR = 2023  # liiklusindeksi baasaasta (kõige parem loendurite kaetus)

# --- Sõidukiklassid (README-ll-AA.md) ---------------------------------------
CLASS_COLS = [str(i) for i in range(1, 11)]
CLASS_NAMES = {
    "1": "Mootorratas", "2": "Sõiduauto", "3": "Sõiduauto + haagis",
    "4": "Pakiauto", "5": "Väike veoauto", "6": "Veoauto",
    "7": "Veoauto + haagis", "8": "Sadulrong", "9": "Väikebuss", "10": "Buss",
}
# Rühmad kütuseliigiga võrdlemiseks
GROUPS = {
    "kerge": ["1", "2", "3"],          # valdavalt bensiin (+ osa diisel-sõiduautosid)
    "raske": ["4", "5", "6", "7", "8", "9", "10"],  # valdavalt diisel
    "veok": ["6", "7", "8"],           # rasked veokid
}
GROUP_LABEL = {"kokku": "Kõik sõidukid", "kerge": "Kerged (kl 1-3)",
               "raske": "Kaubikud, veokid, bussid (kl 4-10)", "veok": "Rasked veokid (kl 6-8)"}
# Pikkusrühmad (14). Ristmike sõidukikirjetes on pikkus mõõdetud (PIKKUS_PIIRID, m). Maanteeloendur annab ainult klassi,
# seega on klasside jaotus pikkusrühmadesse hinnang: sõiduauto, pakiauto ja väikebuss alla 6 m; haagisega sõiduauto,
# veoauto ja buss 6-12 m (liinibuss on piiril); haagisega veoauto ja sadulrong üle 12 m.
PIKKUS = {"luhike": ["1", "2", "4", "9"], "keskmine": ["3", "5", "6", "10"], "pikk": ["7", "8"]}
PIKKUS_PIIRID = [0, 6, 12, np.inf]
PIKKUS_LABEL = {"luhike": "Lühikesed (alla 6 m)", "keskmine": "Keskmised (6-12 m)", "pikk": "Pikad, autorongid (üle 12 m)"}

SPEED_COLS = ["<40Kph", "40-<50", "50-<60", "60-<70", "70-<80", "80-<90",
              "90-<100", "100-<110", "110-<120", "120-<130", "=>130"]
# kiirusvahemiku keskpunkt (km/h), kasutatakse kütusekulu mudelis
SPEED_MID = dict(zip(SPEED_COLS, [30, 45, 55, 65, 75, 85, 95, 105, 115, 125, 135]))

# --- Joonise stiil ------------------------------------------------------------
C_BLUE, C_ORANGE, C_AQUA, C_YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
C_MAGENTA, C_GREEN, C_VIOLET, C_RED = "#e87ba4", "#008300", "#4a3aa7", "#e34948"
C_GRAY = "#8a8984"
TEXT, TEXT2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
DIVERGING = sns.blend_palette(["#1c5cab", "#f0efec", "#b3302f"], as_cmap=True)
FUEL_COLOR = {"bensiin": C_BLUE, "diisel": C_ORANGE}
FUEL_LABEL = {"bensiin": "Bensiin", "diisel": "Diisel"}


def set_style():
    """Kõigi jooniste ühine stiil: valge taust ruudustikuga, pealkiri vasakul paksus kirjas, salvestus 200 dpi."""
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight",
        "axes.edgecolor": GRID, "axes.labelcolor": TEXT2, "axes.titlecolor": TEXT,
        "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlelocation": "left",
        "grid.color": GRID, "grid.linewidth": 0.6,
        "xtick.color": TEXT2, "ytick.color": TEXT2,
        "lines.linewidth": 2, "legend.frameon": False,
        "font.family": "DejaVu Sans",
    })


def otsamargid(cb, fmt=None):
    """Värviskaala otstesse märgid (skaala vähim ja suurim väärtus). Otsale lähemal kui 6% skaalast olev vahemärk
    jäetakse välja, et sildid ei kattuks. fmt = funktsioon väärtus -> silt (nt kellaaeg)."""
    lo, hi = cb.mappable.get_clim()
    t = np.asarray(cb.get_ticks(), float)
    t = np.r_[lo, t[(t > lo + 0.06 * (hi - lo)) & (t < hi - 0.06 * (hi - lo))], hi]
    cb.set_ticks(t)
    if fmt:
        cb.set_ticklabels([fmt(x) for x in t])


def save(fig, name):
    """Salvestab joonise fig faili valjund/<name>.png (RES=15 korral <name>_15min.png) ja sulgeb selle.
    Suunaanalüüsis (SUUND) lisab joonise alla punase märke suuna ja ajasammu kohta."""
    path = OUT_DIR / f"{name}{SUFFIX}.png"
    if SUUND_TXT:                                   # suunaanalüüsi joonistel alati suuna ja ajasammu märge
        fig.text(0.995, 0.002, f"{SUUND_TXT} · {RES_TXT}", ha="right", va="bottom", fontsize=9, color=C_RED,
                 fontweight="bold")
    fig.savefig(path)
    plt.close(fig)
    print(f"  -> {path.relative_to(DATA_DIR)}")


def save_table(df, name, index=False):
    """Salvestab tabeli df faili valjund/<name>.csv (UTF-8 koos BOM-iga, et Excel avaks täpitähed õigesti;
    murdarvud 4 komakohaga)."""
    path = OUT_DIR / f"{name}{SUFFIX}.csv"
    df.to_csv(path, index=index, encoding="utf-8-sig", float_format="%.4f")
    print(f"  -> {path.relative_to(DATA_DIR)}")


# --- Andmebaas ------------------------------------------------------------------
# Ühenduse andmed ei ole koodis. Fail db_yhendus.txt (selle faili kõrval, repost väljas) sisaldab libpq võtmeid kujul
#   host=... port=5432 dbname=... user=...
# Faili puudumisel kasutab libpq keskkonnamuutujaid PGHOST, PGPORT, PGDATABASE, PGUSER. Kasutajal piisab
# lugemisõigusest; parool tuleb libpq paroolifailist (~/.pgpass), mitte koodist ega sellest failist.
_YHENDUS = DATA_DIR / "db_yhendus.txt"
DB = dict(x.split("=", 1) for x in _YHENDUS.read_text(encoding="utf-8").split()) if _YHENDUS.exists() else {}
CACHE = DATA_DIR / "db_cache"       # suurte päringute kohalik puhver (vt puhver); võib alati kustutada


def sql(query, **kw):
    """Andmebaasi päringu tulemus DataFrame'ina (COPY -> ajutine fail -> pandas.read_csv; kw = read_csv argumendid)."""
    import psycopg2
    buf = tempfile.TemporaryFile()                       # baitidena: psycopg2 kirjutab COPY väljundi baitidena
    with buf, contextlib.closing(psycopg2.connect(**DB, connect_timeout=10)) as conn:
        conn.cursor().copy_expert(f"COPY ({query}) TO STDOUT WITH (FORMAT csv, HEADER true)", buf)
        buf.seek(0)
        return pd.read_csv(buf, **kw)


def tabel(nimi, **kw):
    """Terve tabel, nt tabel("import_raw.labisoit")."""
    return sql(f"SELECT * FROM {nimi}", **kw)


def puhver(nimi, tabelid, f, *a, **kw):
    """f(*a, **kw) tulemus kohalikust puhvrist (db_cache/<nimi>.pkl), kui andmebaasi tabelid, funktsiooni kood ja
    argumendid pole pärast salvestamist muutunud; muidu arvutab uuesti ja salvestab. Tabelite muutumist näitab
    pg_stat_user_tables (lisatud, muudetud ja kustutatud ridade loendurid)."""
    nimed = ", ".join(f"'{t}'" for t in tabelid)
    jalg = (sql("SELECT relname, n_tup_ins, n_tup_upd, n_tup_del FROM pg_stat_user_tables WHERE schemaname IN "
                f"('import_raw', 'traffic') AND relname IN ({nimed}) ORDER BY 1").to_csv(index=False),
            inspect.getsource(f), repr((a, kw)))
    fail = CACHE / f"{nimi}.pkl"
    if fail.exists():
        vana, tulem = pd.read_pickle(fail)
        if vana == jalg:
            return tulem
    tulem = f(*a, **kw)
    CACHE.mkdir(exist_ok=True)
    pd.to_pickle((jalg, tulem), fail)
    return tulem


# --- Laadimine ----------------------------------------------------------------
def load_locations():
    """Maanteeloendurite asukohad (traffic.counter_location): id, nimi, maakond, tee_nr, tee_nimi, tee_km, latitude,
    longitude. Lisab veeru maakond_full (nt 'Harjumaa'), mille järgi seotakse kütusemüügi tabelitega."""
    loc = tabel("traffic.counter_location", dtype={"id": str})
    # counter_location: 'Harju' -> kütusetabelis 'Harjumaa'
    loc["maakond_full"] = loc["maakond"].str.strip() + "maa"
    loc["tee_nimi"] = loc["tee_nimi"].str.replace("�", "-", regex=False)
    return loc


_SUMMAD = ", ".join(f'SUM("{c}") AS "{c}"' for c in CLASS_COLS + SPEED_COLS)     # tunniloenduste liitmine päringus


def load_hourly_profile():
    """Tunniprofiil loenduri, kanali, kuu ja päevatüübi (toopaev = E-R) kaupa: n_hours ja loenduste summad."""
    return puhver("hourly_profile", ["hourly_count_csv"], sql,
                  "SELECT id, kanal, EXTRACT(YEAR FROM aeg)::int AS aasta, EXTRACT(MONTH FROM aeg)::int AS kuu, "
                  "(EXTRACT(ISODOW FROM aeg) <= 5) AS toopaev, EXTRACT(HOUR FROM aeg)::int AS tund, COUNT(*) AS n_hours, "
                  f"{_SUMMAD} FROM import_raw.hourly_count_csv GROUP BY 1, 2, 3, 4, 5, 6 ORDER BY 1, 2, 3, 4, 5, 6",
                  dtype={"id": str})


def load_daily():
    """Päevased summad kanali kaupa (tunniloendustest, import_raw.hourly_count_csv), parandatud duplikaattundide jaoks.

    'hours' = mitu tunnirida päeval oli. 24 = korras. 2021. aastal on osa tunde
    imporditud kaks korda (46-48 rida) -> jagame summad hours/24-ga.
    23/25 = suveaja vahetuse päevad, jäävad nii nagu on.
    """
    d = puhver("daily_count", ["hourly_count_csv"], sql,
               f"SELECT id, kanal, aeg::date AS paev, COUNT(*) AS hours, {_SUMMAD} FROM import_raw.hourly_count_csv "
               "GROUP BY id, kanal, aeg::date ORDER BY id, kanal, paev", dtype={"id": str}, parse_dates=["paev"])
    dup = d["hours"] >= 44
    scale = np.where(dup, 24 / d["hours"], 1.0)
    num = CLASS_COLS + SPEED_COLS
    d[num] = d[num].mul(scale, axis=0)
    d["duplikaat"] = dup
    d["kehtiv"] = d["hours"].between(23, 25) | d["hours"].between(44, 50)
    d["kokku"] = d[CLASS_COLS].sum(axis=1)
    for g, cols in GROUPS.items():
        d[g] = d[cols].sum(axis=1)
    d.loc[d["kokku"] <= 0, "kehtiv"] = False
    d["kuu"] = d["paev"].dt.to_period("M")
    return d


def counter_month(d, min_days=15, key="kuu"):
    """Loenduri perioodi (vaikimisi kuu) keskmine ööpäevane liiklus, kõik suunad kokku.

    Kanal-periood kehtib, kui kehtivaid päevi >= min_days. Loendur-periood kehtib,
    kui kehtivate kanalite arv ei ole väiksem kui selle loenduri tavaline kanalite
    arv (nii ei tekita ühe raja väljalangemine vale langust).
    """
    v = d[d["kehtiv"]]
    cols = ["kokku", *GROUPS, *CLASS_COLS, *SPEED_COLS]
    ch = v.groupby(["id", "kanal", key]).agg(
        paevi=("paev", "nunique"), aasta=("paev", lambda s: s.iloc[0].year),
        **{c: (c, "mean") for c in cols})
    ch = ch[ch["paevi"] >= min_days].reset_index()
    cm = ch.groupby(["id", key]).agg(kanaleid=("kanal", "nunique"),
                                      paevi=("paevi", "min"), aasta=("aasta", "first"),
                                      **{c: (c, "sum") for c in cols}).reset_index()
    typical = cm.groupby("id")["kanaleid"].agg(lambda s: s.mode().max())
    cm = cm[cm["kanaleid"] >= cm["id"].map(typical)]
    kuu = cm[key] if key == "kuu" else pd.PeriodIndex(pd.to_datetime(cm[key]), freq="M")
    cm = cm[(kuu >= START) & (kuu <= END)].copy()
    cm["klass_kahtlane"] = class_anomaly(cm)
    cm["maht_kahtlane"] = volume_anomaly(cm, key)
    return cm


def volume_anomaly(cm, key="kuu", hi=1.75, lo=0.4):
    """Märgib loendur-perioodid, mille liiklusmaht erineb sama loenduri sama
    kalendrikuu mediaanist (üle aastate) üle 1,75 korra või alla 0,4 korra.

    Näited: Kodasoo 2025-10...2026-04 (~10-19x tavalisest), Maetaguse 2025-07 (15x),
    Pikakula 2022-08...10 (~2% tavalisest). Need perioodid jäetakse kõigist
    analüüsidest välja.
    """
    kuu = cm[key] if key == "kuu" else pd.PeriodIndex(pd.to_datetime(cm[key]), freq="M")
    cal = kuu.dt.month if hasattr(kuu, "dt") else kuu.month
    med = cm.groupby([cm["id"], np.asarray(cal)])["kokku"].transform("median")
    r = cm["kokku"] / med
    return (r > hi) | (r < lo)


def clean(cm, klass=True):
    """Eemalda kahtlased loendur-perioodid (maht alati, klassijaotus kui klass=True)."""
    bad = cm["maht_kahtlane"] | (cm["klass_kahtlane"] if klass else False)
    return cm[~bad]


def class_anomaly(cm, threshold=0.25):
    """Märgib loendur-perioodid, kus mõne sõidukiklassi osakaal erineb loenduri enda
    mediaanist rohkem kui `threshold` (25 protsendipunkti).

    Näide: Kodasoo (077a6) loendas 2025-10...2026-04 enamiku sõiduautosid klassi 7
    (veoauto + haagis). Kogumaht on korras, klassijaotus mitte -> need perioodid
    jäetakse klassipõhistest analüüsidest välja, koguliiklusest mitte.
    """
    sh = cm[CLASS_COLS].div(cm["kokku"], axis=0)
    med = sh.groupby(cm["id"]).transform("median")
    return (sh - med).abs().max(axis=1) > threshold


def traffic_index(cm, value="kokku", by=None, key="kuu", base_year=BASE_YEAR, min_counters=3):
    """Mahuga kaalutud liiklusindeks (baasaasta = 100).

    Iga perioodi jaoks: sum(ADT loendurid, millel on andmed selles perioodis) /
    sum(nende samade loendurite baasaasta keskmine ADT) * 100.
    Nii ei tekita loendurite lisandumine/kadumine hüppeid.
    """
    cm = clean(cm, klass=(value != "kokku"))  # vigane maht/klassijaotus välja
    base = cm[cm["aasta"] == base_year].groupby("id")[value].mean().rename("base")
    x = cm.join(base, on="id").dropna(subset=["base"])
    keys = [key] + ([by] if by else [])
    out = x.groupby(keys).agg(v=(value, "sum"), b=("base", "sum"),
                              loendureid=("id", "nunique")).reset_index()
    out = out[out["loendureid"] >= min_counters]
    out["indeks"] = out["v"] / out["b"] * 100
    return out.drop(columns=["v", "b"])


def to_period(year, month):
    """Aasta + kuu -> pandas Period (M). Töötab ka vanemate pandas versioonidega."""
    dt = pd.to_datetime(pd.DataFrame({"year": pd.Series(year).astype(int).to_numpy(),
                                      "month": pd.Series(month).astype(int).to_numpy(), "day": 1}))
    return pd.PeriodIndex(dt, freq="M").to_numpy()


def _county_fuel(col):
    """Ühe kütuse (col = 'bensiin' või 'diisel') kuumüük maakonniti laiast tabelist pikaks: kuu, maakond_full, liitrid."""
    f = tabel(f"import_raw.{col}_maakond_monthly")
    f = f.melt(id_vars=["Aasta", "Kuu"], var_name="maakond_full", value_name=col)
    f["kuu"] = to_period(f["Aasta"], f["Kuu"])
    return f[["kuu", "maakond_full", col]]


def load_fuel_county():
    """Maakonna kütusemüük, liitrit päevas (kuu summa / päevade arv)."""
    f = _county_fuel("bensiin").merge(_county_fuel("diisel"), on=["kuu", "maakond_full"])
    days = f["kuu"].dt.days_in_month
    f["bensiin"] /= days
    f["diisel"] /= days
    return f[(f["kuu"] >= START) & (f["kuu"] <= END)]


def load_fuel_national():
    """Jaemüük tanklatest, liitrit päevas. Bensiin = <98 + >98."""
    r = tabel("import_raw.jaemuuk_tanklast_monthly").dropna()
    r["kuu"] = to_period(r["Aasta"], r["Kuu"])
    days = r["kuu"].dt.days_in_month
    out = pd.DataFrame({"kuu": r["kuu"],
                        "bensiin": (r["Bensiin < 98"] + r["Bensiin > 98"]) / days,
                        "diisel": r["Diisel"] / days})
    return out[(out["kuu"] >= START) & (out["kuu"] <= END)].reset_index(drop=True)


# --- Aegridade abifunktsioonid ---------------------------------------------------
def yoy(s, periods=12):
    """Aastane muutus log-skaalas (~%), eemaldab hooajalisuse."""
    return np.log(s).diff(periods) * 100


def stl_resid(s, period=12):
    """STL jääk (log-skaalas), eemaldab trendi ja hooajalisuse."""
    from statsmodels.tsa.seasonal import STL
    s = s.dropna()
    res = STL(np.log(s), period=period, robust=True).fit()
    return pd.Series(res.resid * 100, index=s.index)


def corr_pair(a, b):
    """Pearson r, Spearman rho, p-väärtused, n."""
    from scipy import stats
    m = pd.concat([a, b], axis=1).dropna()
    if len(m) < 6:
        return dict(n=len(m), r=np.nan, p=np.nan, rho=np.nan, p_rho=np.nan)
    r, p = stats.pearsonr(m.iloc[:, 0], m.iloc[:, 1])
    rho, pr = stats.spearmanr(m.iloc[:, 0], m.iloc[:, 1])
    return dict(n=len(m), r=r, p=p, rho=rho, p_rho=pr)


def mediaani_uv(x, n=2000):
    """Mediaani 95% usaldusvahemik (bootstrap)."""
    x = np.asarray(x, float)
    m = np.median(np.random.default_rng(0).choice(x, (n, len(x))), axis=1)
    return np.percentile(m, [2.5, 97.5])


KOHANIMI_VEAD = {"talinn": "tallinn", "kanam": "kanama"}     # kirjavead radade nimedes (Kodasoo, Juuliku 1)


def ends(label):
    """Maanteeloenduri raja nimi (traffic.counter_channel) -> (lähtekoht, sihtkoht): '3: Tartu - Tallinn 1' -> ('tartu', 'tallinn').
    Kirjavead parandatakse (KOHANIMI_VEAD), et sama suuna rajad tuleksid kokku."""
    body = re.sub(r"^\s*\d+\s*:\s*", "", str(label)).lower()
    parts = [p.strip() for p in body.split(" - ")]
    if len(parts) != 2:
        return "", ""
    clean = lambda p: (lambda q: KOHANIMI_VEAD.get(q, q))(re.sub(r"\s+(l?\d+|i+)$", "", p).strip())
    return clean(parts[0]), clean(parts[1])


assert ends("3: Narva - Talinn 2") == ("narva", "tallinn") and ends("1: Luige - Kanam") == ("luige", "kanama")


def load_15m(algus="2024-08-01"):
    """Maanteeloendurite 15 min loendused (import_raw."15m_count") alates kuupäevast, rida = loendur, kanal (rada) ja
    veerandtund: id, kanal, ts (veerandtunni algus) ja sõidukite arvud
      v                       kõik klassid kokku
      luhike, keskmine, pikk  pikkusrühmade kaupa (PIKKUS: klassid -> < 6 m, 6-12 m, >= 12 m)
      alla40                  kiirusega alla 40 km/h (väikseim kiirusvahemik)
      ks, kn                  kiiruste summa (vahemike keskpunktid x sõidukite arv) ja kiirusega sõidukite arv;
                              keskmine kiirus = ks / kn (enne jagamist võib radu ja veerandtunde liita)
    Sama veerandtund kaks korda (kordusimport, kellakeeramine) = keskmine. Pikk ajalugu on Harjumaa loenduritel;
    teistel ainult üksikud päevad."""
    summa = lambda veerud, kaal=None: " + ".join(f'"{c}"' + (f" * {kaal[c]}" if kaal else "") for c in veerud)
    veerud = {"v": summa(CLASS_COLS), **{g: summa(k) for g, k in PIKKUS.items()}, "alla40": f'"{SPEED_COLS[0]}"',
              "ks": summa(SPEED_COLS, SPEED_MID), "kn": summa(SPEED_COLS)}
    return puhver("15m_count", ["15m_count"], sql,
                  "SELECT id, kanal, aeg AS ts, " + ", ".join(f"AVG({s}) AS {n}" for n, s in veerud.items())
                  + f" FROM import_raw.\"15m_count\" WHERE aeg >= '{algus}' GROUP BY id, kanal, aeg ORDER BY id, kanal, aeg",
                  dtype={"id": str, **dict.fromkeys(list(veerud)[1:], "float32")}, parse_dates=["ts"])    # v jääb täpseks


def ilma_vigaste_kuudeta(x, cm, aeg="ts"):
    """Jätab tabelist x (veerud id ja aeg) välja loendur-kuud, mille maht on kahtlane (counter_month: maht_kahtlane),
    nt Kodasoo 2025-09...2026-05 (~10x tavalisest). Hinnang tuleb tunniloendustest, seega ainult kuni kuuni END."""
    halb = cm.loc[cm["maht_kahtlane"], ["id", "kuu"]]
    halb = pd.MultiIndex.from_arrays([halb["id"], halb["kuu"].dt.year * 100 + halb["kuu"].dt.month])
    return x[~pd.MultiIndex.from_arrays([x["id"], x[aeg].dt.year * 100 + x[aeg].dt.month]).isin(halb)]


def maantee_suunad(algus):
    """Maanteeloendurite suunad ja nende 15 min loendused alates kuupäevast `algus` (13, 20).
    Suund (site) = loendur + raja nime otspunktid (traffic.counter_channel, nt '3: Tartu - Tallinn 1' -> 'tartu - tallinn');
    suuna rajad liidetakse ja alles jäävad veerandtunnid, kus kõik suuna rajad on olemas. Kahtlase mahuga loendur-kuud
    on väljas (ilma_vigaste_kuudeta). Tagastab (ds, dq):
      ds  site -> id, lahte, siht, nimi, tee_nr, tee_km, lat, lon
      dq  site, start (veerandtunni algus), c (sõidukeid), n (radu), alla40, ks, kn (vt load_15m), paev, slot (0..95),
          kool (õppetöö), argipaev (tööpäev, ka vaheajal), toopaev (tavaline tööpäev = mõlemad), dow (0 = esmaspäev)"""
    chn = tabel("traffic.counter_channel", dtype={"id": str})
    chn[["lahte", "siht"]] = pd.DataFrame([ends(x) for x in chn["channel_label"]], index=chn.index)
    chn = chn[chn["lahte"] != ""]
    chn["site"] = chn["id"] + " | " + chn["lahte"] + " - " + chn["siht"]
    loc = load_locations().set_index("id").rename(columns={"latitude": "lat", "longitude": "lon"})
    ds = chn.groupby("site").agg(id=("id", "first"), lahte=("lahte", "first"), siht=("siht", "first"))
    ds = ds.join(loc[["nimi", "tee_nr", "tee_km", "lat", "lon"]], on="id")
    m = ilma_vigaste_kuudeta(load_15m(), counter_month(load_daily()))
    m = m[m["ts"] >= algus].merge(chn[["id", "kanal", "site"]], on=["id", "kanal"])
    dq = (m.groupby(["site", "ts"]).agg(c=("v", "sum"), n=("v", "size"), alla40=("alla40", "sum"), ks=("ks", "sum"), kn=("kn", "sum"))
          .reset_index().rename(columns={"ts": "start"}))
    dq = dq[dq["n"] == dq.groupby("site")["n"].transform("max")]          # ainult veerandtunnid, kus kõik suuna rajad on olemas
    dq["paev"] = dq["start"].dt.normalize()
    dq["slot"] = dq["start"].dt.hour * 4 + dq["start"].dt.minute // 15
    kal = day_calendar(dq["paev"]).set_index("paev")
    dq["kool"] = dq["paev"].map(kal["vaheaeg"]) == "kool"
    dq["argipaev"] = dq["paev"].map(kal["paevatyyp"]) == "tööpäev"
    dq["toopaev"] = dq["kool"] & dq["argipaev"]
    dq["dow"] = dq["paev"].dt.dayofweek
    return ds, dq


def km(lat1, lon1, lat2, lon2):
    """Kaugus linnulennult, km (väikeste vahemaade lähend)."""
    kx = 111.32 * np.cos(np.deg2rad((lat1 + lat2) / 2))
    return np.hypot((lon1 - lon2) * kx, (lat1 - lat2) * 110.57)


def month_axis(ax):
    """Ajatelje märgid aastate kaupa (silt = aasta)."""
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


# ==============================================================================
# Tallinna ristmikud (seire.tallinn.ee, aruanne T09)
# ==============================================================================
TALLINN_DIR = DATA_DIR / "db"   # kohalikud failid enne andmebaasi laadimist (ainult db_laadimine.py)
MIN_EXPECTED_FOR_ZERO = 20  # 0 loetakse rikkeks, kui sama ajapilu tavaline maht >= 20 sõidukit/15 min
BAD_DAY_RATIO = 0.6         # päev välja, kui päevasumma < 60% sama nädalapäeva mediaanist
TALLINN_BASE_YEAR = 2025    # ristmike andmed algavad 2024-07 -> baasaasta 2025

# Koolivaheajad: RT I, 19.03.2025, 5 ("2024/2025., 2025/2026. ja 2026/2027. õppeaasta koolivaheajad")
SCHOOL_BREAKS = [
    ("2024-07-01", "2024-09-01", "suvi"),    # 2023/24 suvevaheaeg (andmed algavad 29.07.2024)
    ("2024-10-21", "2024-10-27", "lühike"),
    ("2024-12-23", "2025-01-05", "jõulud"),
    ("2025-02-24", "2025-03-02", "lühike"),
    ("2025-04-14", "2025-04-20", "lühike"),
    ("2025-06-10", "2025-08-31", "suvi"),
    ("2025-10-20", "2025-10-26", "lühike"),
    ("2025-12-22", "2026-01-04", "jõulud"),
    ("2026-02-23", "2026-03-01", "lühike"),
    ("2026-04-13", "2026-04-19", "lühike"),
    ("2026-06-10", "2026-08-31", "suvi"),
    ("2026-10-26", "2026-11-01", "lühike"),
    ("2026-12-21", "2027-01-03", "jõulud"),
]
VAHEAEG_LABEL = {"kool": "Õppetöö", "lühike": "Lühike koolivaheaeg (sügis, veebr, kevad)",
                 "jõulud": "Jõuluvaheaeg", "suvi": "Suvevaheaeg"}


def public_holidays(years):
    """Eesti riigipühad (pühade ja tähtpäevade seadus): {kuupäev: nimi}."""
    from dateutil.easter import easter
    out = {}
    for y in years:
        e = pd.Timestamp(easter(y))
        for d, name in [(f"{y}-01-01", "uusaasta"), (f"{y}-02-24", "iseseisvuspäev"),
                        (e - pd.Timedelta(days=2), "suur reede"), (e, "ülestõusmispühade 1. püha"),
                        (f"{y}-05-01", "kevadpüha"), (e + pd.Timedelta(days=49), "nelipühade 1. püha"),
                        (f"{y}-06-23", "võidupüha"), (f"{y}-06-24", "jaanipäev"),
                        (f"{y}-08-20", "taasiseseisvumispäev"), (f"{y}-12-24", "jõululaupäev"),
                        (f"{y}-12-25", "esimene jõulupüha"), (f"{y}-12-26", "teine jõulupüha")]:
            out[pd.Timestamp(d)] = name
    return out


def shortened_days(holidays):
    """Tööpäevad, mis on 3 h lühemad (TLS § 53 lg 2): uusaasta, iseseisvuspäeva,
    võidupüha ja jõululaupäeva eelne tööpäev."""
    out = set()
    for d, name in holidays.items():
        if name in ("uusaasta", "iseseisvuspäev", "võidupüha", "jõululaupäev"):
            p = d - pd.Timedelta(days=1)
            while p.dayofweek >= 5 or p in holidays:
                p -= pd.Timedelta(days=1)
            out.add(p)
    return out


def dst_days(years):
    """Suveaja vahetuse pühapäevad (märtsi ja oktoobri viimane pühapäev)."""
    out = []
    for y in years:
        for m in (3, 10):
            last = pd.Timestamp(y, m, 31)
            out.append(last - pd.Timedelta(days=(last.dayofweek - 6) % 7))
    return out


def day_calendar(dates):
    """Päevatüüp ja koolivaheaeg iga kuupäeva kohta."""
    d = pd.DatetimeIndex(pd.to_datetime(pd.Series(dates).unique())).normalize().unique().sort_values()
    years = range(d.year.min() - 1, d.year.max() + 2)
    hol = public_holidays(years)
    short = shortened_days(hol)
    cal = pd.DataFrame({"paev": d})
    cal["nadalapaev"] = cal["paev"].dt.dayofweek          # 0 = esmaspäev
    cal["puha"] = cal["paev"].map(hol)
    cal["vaheaeg"] = "kool"
    for a, b, kind in SCHOOL_BREAKS:
        cal.loc[cal["paev"].between(a, b), "vaheaeg"] = kind
    cal["paevatyyp"] = np.select(
        [cal["puha"].notna(), cal["paev"].isin(short), cal["nadalapaev"] == 5, cal["nadalapaev"] == 6],
        ["riigipüha", "lühendatud", "laupäev", "pühapäev"], "tööpäev")
    return cal


def load_tallinn():
    """Tallinna ristmike 15 min andmed puhastatult.

    Tagastab (t, paevad):
      t      - mp_id, ts, paev, slot (0..95), v (sõidukeid 15 min kohta, NaN = puudu) + kalender
      paevad - mp_id, paev, summa (puuduvad pilud täidetud tavaväärtusega), puudu, suhe, kehtiv
    Puhastus:
      1) suveaja vahetuse ööd kell 02-05 -> NaN (märtsis võltsnullid, oktoobris topelttund)
      2) 0, kus sama pilu tavaline maht >= 20 -> NaN (rike on salvestatud nullina)
      3) päev välja, kui > 2 h puudu (v.a suveaja öö) või kui ristmiku päevasumma suhe
         oma nädalapäeva mediaani on < 60% linna ülejäänud ristmike samal päeval nähtud
         suhtest. Nii ei visata välja pühi (terve linn langeb koos), aga leitakse
         ühe ristmiku rikked ka pühade ajal (pühadel ja jõuluvaheajal lävi 30%).
    """
    t = read_tallinn_raw()
    t["paev"] = t["ts"].dt.normalize()
    t["slot"] = t["ts"].dt.hour * 4 + t["ts"].dt.minute // 15
    t["v"] = t["vehicles"].astype(float)
    t = t.merge(day_calendar(t["paev"]), on="paev", how="left")
    years = range(t["paev"].dt.year.min(), t["paev"].dt.year.max() + 1)
    t["dst"] = t["paev"].isin(dst_days(years)) & t["slot"].between(8, 19)
    t.loc[t["dst"], "v"] = np.nan

    grp = np.select([t["nadalapaev"] < 5, t["nadalapaev"] == 5], ["E-R", "L"], "P")
    exp = t.assign(_g=grp).groupby(["mp_id", "_g", "slot"])["v"].transform("median")
    t["rike"] = (t["v"] == 0) & (exp >= MIN_EXPECTED_FOR_ZERO)
    t.loc[t["rike"], "v"] = np.nan

    day = (t.assign(_f=t["v"].fillna(exp), _m=t["v"].isna() & ~t["dst"])
           .groupby(["mp_id", "paev"])
           .agg(summa=("_f", "sum"), puudu=("_m", "sum"),
                rikkeid=("rike", "sum"), nadalapaev=("nadalapaev", "first"),
                paevatyyp=("paevatyyp", "first"), vaheaeg=("vaheaeg", "first"))
           .reset_index().sort_values(["mp_id", "paev"]))
    day["mediaan"] = (day.groupby(["mp_id", "nadalapaev"])["summa"]
                      .transform(lambda s: s.rolling(9, center=True, min_periods=4).median()))
    day["suhe"] = day["summa"] / day["mediaan"]
    day["suhe_linn"] = day.groupby("paev")["suhe"].transform("median")
    day["suhe_suhteline"] = day["suhe"] / day["suhe_linn"]
    # pühade ajal langevad tööstusalade ristmikud linnast rohkem -> seal lubame suuremat langust
    normaalne = ~day["paevatyyp"].isin(["riigipüha", "lühendatud"]) & (day["vaheaeg"] != "jõulud")
    lavi = np.where(normaalne, BAD_DAY_RATIO, 0.3)
    day["kehtiv"] = (day["puudu"] <= 8) & (day["suhe_suhteline"] >= lavi)
    bad = day.loc[~day["kehtiv"], ["mp_id", "paev"]].assign(_bad=True)
    t = t.merge(bad, on=["mp_id", "paev"], how="left")
    t.loc[t["_bad"].eq(True), "v"] = np.nan
    t = t.drop(columns="_bad")
    if SUUND:     # suunaanalüüs: 15 min summa x suuna osakaal samas pilus (sõidukipõhise ööpäeva järgi)
        osa, daily = direction_share(load_vehicles(None))
        t = t.merge(osa, on=["mp_id", "slot"])
        t["v"] = t["v"] * t.pop("osa")
        day = day[day["mp_id"].isin(daily.index)].assign(summa=lambda x: x["summa"] * x["mp_id"].map(daily))
    return t, day


def read_tallinn_raw():
    """Toorandmed (import_raw.traffic_15min_tallinn): mp_id, ts (15 min intervalli algus), vehicles.
    Tühje ristmikke tabelis pole."""
    return puhver("tallinn_15min", ["traffic_15min_tallinn"], sql,
                  "SELECT mp_id, ts, vehicles FROM import_raw.traffic_15min_tallinn ORDER BY mp_id, ts", parse_dates=["ts"])


def load_junctions():
    """Kõigi ristmike (MP01...MP50) koodid, nimed ja koordinaadid (import_raw.tallinn_junction).
    Mitte-tühjade ristmike valik tehakse andmete järgi."""
    return sql("SELECT mp_id, code, name, lat, lon FROM import_raw.tallinn_junction ORDER BY mp_id")


def load_manoeuvres():
    """Mida iga ristmiku kanal loendab (import_raw.tallinn_detector_manoeuvre): mp, channel, direction_id, manoeuvre jm."""
    return sql("SELECT mp, intersection, schema_file AS schema, channel, detector_id, detector_name, schema_label, "
               "direction_id, manoeuvre, from_leg, to_leg, turn, traffic_direction, vehicles_in_hour, note "
               "FROM import_raw.tallinn_detector_manoeuvre ORDER BY mp, channel")


VEHICLE_DAY = "2026-09-30"   # ainus täielik ööpäev sõidukipõhistes loendustes (Traffic 24h, kolmapäev)
FIVE_MIN_MIN_N = 30          # 5 min jaotus ristmiku enda andmetest alles alates 30 sõidukist 15 min pilus


# Ristmikud, mille manöövrinimedes pole LSS/LVS: kasutaja määratud kanalid (kanal võib olla mõlemas).
# MP30: ülejäänud kanalid on muu liikumine; MP46: kvartalisisene liikumine, suunaanalüüsis ei loeta.
SUUND_KANALID = {13: {"LSS": {1, 2, 6, 7, 8, 9, 10, 11}, "LVS": {3, 4, 10, 11}},
                 30: {"LSS": {3, 5, 14}, "LVS": set()},
                 46: {"LSS": set(), "LVS": set()}}


def channel_direction():
    """Ristmiku kanali suunad (veerud LSS, LVS = True/False) manöövri nime järgi (load_manoeuvres):
    LSS (linna sisse) või LVS (linnast välja). Otsustab lähtesuund (enne noolt); kõrvaltänavalt (VS) tulev
    liiklus saab sihtsuuna, nt 'Tulika VS -> PP Endla LVS' = LVS. Ilma LSS/LVS-ta manöövrid (nt
    'Ahtri -> PP Jõe') ei kuulu kumbagi, v.a SUUND_KANALID ristmikel."""
    dm = load_manoeuvres()
    pick = lambda name: next((m.group(1) for part in str(name).partition("→")[::2]
                              for m in [re.search(r"\b(LSS|LVS)\d?\b", part)] if m), None)
    out = pd.DataFrame({"mp_id": dm["mp"].str[2:].astype(int), "kanal": dm["channel"]})
    nimi = dm["manoeuvre"].map(pick)
    for s in ["LSS", "LVS"]:
        kasutaja = [k in SUUND_KANALID.get(m, {}).get(s, ()) for m, k in zip(out["mp_id"], out["kanal"])]
        out[s] = np.where(out["mp_id"].isin(SUUND_KANALID), kasutaja, nimi == s)
    return out


PUHASTUS = {}      # koik (False/True) -> mitu rida loeti ja mitu eemaldati (11_kontrollid näitab)


def _soidukid(koik):
    """Puhastatud sõidukikirjed (suunata) ja puhastuse arvud. koik=False: ainult sõidukipõhine ööpäev (VEHICLE_DAY,
    25 h nagu algsed osafailid). Elumärgid (kiirus, pikkus ja eluaegne loendur 0) jäetakse välja juba päringus."""
    aken = "" if koik else (f" AND event_time >= '{VEHICLE_DAY}' AND event_time < '{VEHICLE_DAY}'::timestamp "
                            "+ interval '25 hours'")
    v = sql("SELECT port, detector_id AS kanal, speed_kmh AS kiirus, length_m AS pikkus, occupancy_s AS occ, "
            "time_gap_s AS gap, lifetime_counter AS life, event_time AS ts FROM import_raw.traffic24h_tallinn "
            f"WHERE (speed_kmh > 0 OR length_m > 0 OR lifetime_counter > 0){aken} "
            "ORDER BY event_time, port, detector_id, lifetime_counter, speed_kmh DESC, length_m DESC")   # kindel järjekord
    v["ts"] = pd.to_datetime(v["ts"], format="ISO8601")
    v = v.drop_duplicates(["port", "kanal", "ts"])
    # Sama järjekorranumbri (life) kordus ei ole sõiduk: loenduri arvesti ei liigu, gap = 0 ja väärtused on
    # juhuslikud (30.09.2026: 0,57% ridadest, mõnel loenduril kuni 40%) - ametlik T08 loendus neid ei sisalda.
    # Kiirus 255 = mõõtmata (kood), loetakse kiiruseta sõidukiks (0). Read on päringust aja järjekorras.
    n0 = len(v)
    v = v.drop_duplicates(["port", "kanal", "life"])
    arvud = dict(ridu=n0, korduv_number=n0 - len(v), kiirus_255=int((v["kiirus"] == 255).sum()))
    v.loc[v["kiirus"] == 255, "kiirus"] = 0
    v = v.merge(sql("SELECT port, mp_id FROM import_raw.tallinn_serial_port"), on="port")
    return v[["mp_id", "kanal", "ts", "kiirus", "pikkus", "occ", "gap", "life"]], arvud


@functools.lru_cache(maxsize=2)
def _vehicles_all(koik=False):
    """Puhastatud sõidukikirjed (_soidukid, kohalikust puhvrist) koos kanali suunaga (veerud LSS, LVS). Tulemus jääb
    mällu, et sama käivituse jooksul ei loetaks kaks korda; puhastuse arvud lähevad sõnastikku PUHASTUS."""
    v, PUHASTUS[koik] = puhver("soidukid_koik" if koik else f"soidukid_{VEHICLE_DAY}",
                               ["traffic24h_tallinn", "tallinn_serial_port"], _soidukid, koik)
    if v.empty:
        return None
    v = v.merge(channel_direction(), on=["mp_id", "kanal"], how="left")
    v[["LSS", "LVS"]] = v[["LSS", "LVS"]].fillna(False).astype(bool)
    return v


def load_vehicles(suund=SUUND, koik=False):
    """Traffic 24h toorandmed, iga sõiduk eraldi rida: mp_id, kanal, ts, kiirus, pikkus, occ, gap, life, LSS, LVS.

    ts = aeg, mil kontroller sõiduki edastas (küsitlus iga ~0,4...5 s, ühe küsitluse sõidukid saavad sama aja
    ja on vastupidises järjekorras) - tsüklite ja pauside jaoks piisav. Täpsed vahed annab loendur ise:
    gap = ajavahe eelmise sõiduki lahkumisest (s), occ = loenduril oldud aeg (s), life = loenduri
    järjekorranumber (õige järjestus). Sõidukite vahe esiotsast esiotsani = eelmise occ + gap.

    Allikas import_raw.traffic24h_tallinn. koik=False: ainult sõidukipõhine ööpäev (VEHICLE_DAY); koik=True: kõik
    päevad (ka logija nädal). 'Serial port Id' -> ristmik: import_raw.tallinn_serial_port (leitud T08
    tunniloenduste võrdlusest); 'Detector ID' = ristmiku kanal (T08 "Suunad"). suund = LSS/LVS -> ainult selle
    suuna kanalid (vaikimisi SUUND; None = kõik). Tagastab None, kui kirjeid pole.
    """
    v = _vehicles_all(koik)
    return v if v is None or suund is None else v[v[suund]]


def direction_share(v, suund=SUUND, day=VEHICLE_DAY, min_n=FIVE_MIN_MIN_N):
    """Suuna osakaal ristmiku iga 15 min pilu liiklusest sõidukipõhise ööpäeva järgi -> (pilud, ööpäev):
    pilud = mp_id, slot, osa; vaikne pilu (< min_n sõidukit) saab ristmiku ööpäeva osakaalu.
    Ristmikud, kus selle suuna kanaleid pole, puuduvad."""
    x = v[v["ts"].dt.normalize() == pd.Timestamp(day)]
    key = [x["mp_id"], (x["ts"].dt.hour * 4 + x["ts"].dt.minute // 15).rename("slot")]
    n, d = x.groupby(key).size(), x[suund].groupby(key).sum()
    daily = d.groupby("mp_id").sum() / n.groupby("mp_id").sum()
    daily = daily[daily > 0]
    idx = pd.MultiIndex.from_product([daily.index, range(96)], names=["mp_id", "slot"])
    n, d = n.reindex(idx, fill_value=0), d.reindex(idx, fill_value=0)
    osa = (d / n).where(n >= min_n, daily.reindex(idx.get_level_values("mp_id")).values)
    return osa.rename("osa").reset_index(), daily


def five_min_shares(v, day=VEHICLE_DAY, min_n=FIVE_MIN_MIN_N, flags=False, outage_from=None):
    """Iga ristmiku iga 15 min pilu (0..95) jaotus kolmeks 5 min osaks (veerud 0, 1, 2 =
    :00-:05, :05-:10, :10-:15 pilu algusest), osakaalud summas 1. Ühe päeva põhjal.
    Kõigi ristmike koondjaotuse saab pilu, kus ristmikul on alla min_n sõiduki (öö müra), mõni 5 min osa
    on tühi või on >= 150 sõiduki juures tühi minut (lühike rike, nt MP14 30.09 kell 10:25-10:32).
    flags=True: tagastab (osakaalud, koondjaotuse lipp). outage_from = kõik sõidukid, kui v on ühe suuna
    alamhulk (ühe suuna tühi minut võib olla foori punane faas, mitte rike)."""
    x = v[v["ts"].dt.normalize() == pd.Timestamp(day)]
    o = x if outage_from is None else outage_from[outage_from["ts"].dt.normalize() == pd.Timestamp(day)]
    mi = o["ts"].dt.hour * 60 + o["ts"].dt.minute
    empty = o.groupby([o["mp_id"], mi]).size().unstack(fill_value=0).reindex(columns=range(1440), fill_value=0) == 0
    gap = empty.T.groupby(empty.columns // 15).any().T.stack().rename_axis(["mp_id", "slot"])
    m5 = x["ts"].dt.hour * 12 + x["ts"].dt.minute // 5
    n = x.groupby([x["mp_id"], (m5 // 3).rename("slot"), (m5 % 3).rename("osa")]).size().unstack(fill_value=0)
    n = n.reindex(pd.MultiIndex.from_product([n.index.levels[0], range(96)], names=["mp_id", "slot"]),
                  fill_value=0)
    city = n.groupby("slot").sum()
    city = city.div(city.sum(axis=1), axis=0)
    total = n.sum(axis=1)
    sh = n.div(total.where(total > 0), axis=0)
    fallback = (total < min_n) | (n.min(axis=1) == 0) | ((total >= 150) & gap.reindex(n.index, fill_value=False))
    sh.loc[fallback] = city.reindex(n.index.get_level_values("slot")).values[fallback.values]
    return (sh, fallback) if flags else sh


def to_5min(prof15, shares):
    """15 min profiil (read = mp_id, veerud = pilu 0..95) -> 5 min profiil (veerud 0..287).
    Ristmik, millel oma sõidukipõhist päeva pole (nt MP02), saab ristmike keskmise jaotuse."""
    s = prof15.stack().rename_axis(["mp_id", "slot"])
    mean = shares.groupby("slot").mean().reindex(s.index.get_level_values("slot")).set_axis(s.index)
    p = shares.reindex(s.index).fillna(mean).mul(s, axis=0).stack()
    p.index = pd.MultiIndex.from_arrays([p.index.get_level_values(0),
                                         p.index.get_level_values(1) * 3 + p.index.get_level_values(2)])
    return p.unstack().reindex(columns=range(288))


def load_datex_sites():
    """DATEX II loenduskohad (import_raw.datex_site): site (UUID-1 = forwards, -2 = backwards), nimi, radu, lat, lon."""
    return sql("SELECT site, nimi, radu, lat, lon FROM import_raw.datex_site ORDER BY site")


def load_datex_quarters():
    """DATEX II 15 min aknad (import_raw.datex_15min: Tark Tee hetktõmmised ja datex_kogumine.py) -> kella veerandtunnid:
    site (UUID-1/-2 = suund), start (:00, :15, :30, :45), c (sõidukeid veerandtunnis).

    Iga tõmmis annab loenduri viimase 15 min akna (voog sõid/h, sõidukeid = voog/4). Aknad on loenduriti
    0...5 min nihkes (lõpp nt :10, :25...), seega jagatakse need kellaveerandtundideks kumulatiivse summa
    lineaarse interpoleerimisega (eeldus: ühtlane voog akna sees). Ainult katkematud aknajadad; tühimiku
    servades olevad osalised veerandtunnid jäetakse välja. Tagastab None, kui faile pole."""
    d = sql('SELECT site, aeg AS "end", voog_h / 4.0 AS c FROM import_raw.datex_15min WHERE voog_h IS NOT NULL '
            "ORDER BY site, aeg", parse_dates=["end"])
    if d.empty:
        return None
    q, out = pd.Timedelta(minutes=15), []
    for site, g in d.groupby("site"):
        for _, r in g.groupby((g["end"].diff() != q).cumsum()):
            tb = np.r_[r["end"].iloc[0] - q, r["end"]].astype("datetime64[s]").astype(float)
            qs = pd.date_range((r["end"].iloc[0] - q).ceil("15min"), r["end"].iloc[-1].floor("15min"), freq="15min")
            n = np.interp(qs.values.astype("datetime64[s]").astype(float), tb, np.r_[0, r["c"].cumsum()])
            out.append(pd.DataFrame({"site": site, "start": qs[:-1], "c": np.diff(n)}))
    return pd.concat(out, ignore_index=True)


def slot_label(slot, per_hour=4):
    """Pilu järjekorranumber -> kellaaeg 'HH:MM' (per_hour = pilusid tunnis: 4 = 15 min, 12 = 5 min, 60 = minutid)."""
    m = int(round(slot * 60 / per_hour))
    return f"{m // 60:02d}:{m % 60:02d}"


def short_name(name, n=None, compact=False):
    """Ristmiku nimi joonisele. compact=True: eraldaja ' - ' -> '–' (tänavanimede sidekriipsud,
    nt Suur-Ameerika, jäävad). n = suurim pikkus: pikem nimi lõigatakse eraldaja või tühiku
    kohalt ja lõppu lisatakse '…'."""
    s = re.sub(r"\s+", " ", str(name)).strip()
    if compact:
        s = re.sub(r"\s+-\s*|\s*-\s+", "–", s)
    if n and len(s) > n:
        cut = s[:n - 1]
        k = max(cut.rfind("–"), cut.rfind(" "))
        if k >= n // 2:
            cut = cut[:k]
        s = cut.rstrip(" -–") + "…"
    return s


# --- Tipptunnid ja hajutamine (töötab 15 min ja tunniandmetega) --------------------------
AM_WINDOW = (6, 10)    # hommikuse tipptunni ALGUS vahemikus 06:00...09:59
PM_WINDOW = (14, 19)   # õhtuse tipptunni algus 14:00...18:59
CENTROID_WINDOWS = {"hommik": (6, 10), "ohtu": (15, 19)}   # liikluse keskaja aknad


def peak_hour(v, window, per_hour=4):
    """Suurima liikuva tunni algus (pilu) ja maht. v = päeva profiil (24*per_hour väärtust)."""
    v = np.asarray(v, dtype=float)
    lo, hi = window[0] * per_hour, window[1] * per_hour
    sums = np.array([v[s:s + per_hour].sum() for s in range(lo, hi)])
    k = int(np.nanargmax(sums))
    return lo + k, float(sums[k])


def peak_metrics(v, per_hour=4):
    """Tipptunni näitajad: algus, maht (sõid/h), osakaal ööpäevast, PHF, tipu laius."""
    v = np.asarray(v, dtype=float)
    out = {"ooopaev": float(np.nansum(v))}
    for name, win in [("hommik", AM_WINDOW), ("ohtu", PM_WINDOW)]:
        s, vol = peak_hour(v, win, per_hour)
        seg = v[s:s + per_hour]
        out[f"{name}_algus"] = slot_label(s, per_hour)
        out[f"{name}_algus_h"] = s / per_hour
        out[f"{name}_soid_h"] = vol
        out[f"{name}_osakaal_%"] = vol / out["ooopaev"] * 100
        # PHF alati 15 min plokkidest (tavapärane definitsioon), ka 5 min andmetega
        out[f"{name}_phf"] = (vol / (4 * seg.reshape(-1, per_hour // 4).sum(axis=1).max())
                              if per_hour % 4 == 0 else np.nan)
        # tipu laius: minutid, mil maht >= 90% tipu suurimast pilust (hommik 5-11, õhtu 13-20)
        a, b = (5, 11) if name == "hommik" else (13, 20)
        part = v[a * per_hour:b * per_hour]
        out[f"{name}_laius_min"] = int((part >= 0.9 * seg.max()).sum() * 60 / per_hour)
        # teoreetiline hajutamise potentsiaal: kui liiklus tipptunnist +-1 h oleks täiesti ühtlane
        # (negatiivne = selget tippu pole, naabertund on suurem)
        w = v[max(s - per_hour, 0):s + 2 * per_hour]
        out[f"{name}_max_potentsiaal_%"] = (1 - (w.sum() / (len(w) / per_hour)) / vol) * 100
        # liikluse keskaeg: mahuga kaalutud keskmine kellaaeg aknas (hommik 06-10, õhtu 15-19)
        a, b = CENTROID_WINDOWS[name]
        idx = np.arange(a * per_hour, b * per_hour)
        mid = (idx + 0.5) / per_hour
        out[f"{name}_keskaeg_h"] = float(np.nansum(mid * v[idx]) / np.nansum(v[idx]))
        out[f"{name}_keskaeg"] = slot_label(out[f"{name}_keskaeg_h"] * per_hour, per_hour)
    return out


def loigud(mask, auk=3):
    """Järjestikused True-lõigud [(a, b), ...]; kuni `auk` pikkune vahe lõikude vahel loetakse sisse."""
    m = np.asarray(mask, bool).copy()
    e = np.flatnonzero(np.diff(np.r_[0, m.astype(int), 0]))
    for a, b in zip(e[1:-1:2], e[2::2]):
        if b - a <= auk:
            m[a:b] = True
    e = np.flatnonzero(np.diff(np.r_[0, m.astype(int), 0]))
    return list(zip(e[::2].tolist(), e[1::2].tolist()))


def ummiku_loik(mask, lo, hi, auk=3):
    """Lõik [a, b), mis katab akent [lo, hi) kõige rohkem (võib ulatuda aknast välja); None, kui aknas pole (09, 11)."""
    kate = [(min(b, hi) - max(a, lo), a, b) for a, b in loigud(mask, auk)]
    parim = max(kate, key=lambda x: x[0], default=(0,))
    return parim[1:] if parim[0] > 0 else None


def ummikumask(labilase, taistase, algus=0.8, pusib=0.75, auk=2, kiirus=None, kaal=None, v_kesk=None):
    """Ummiku tsüklid fooriga manöövril (09, 11): silutud läbilase on vähemalt algus x täistase. Lühike vajumine -
    kuni `auk` järjestikust andmepunkti, ükski neist alla pusib x täistase -, mille järel läbilase tõuseb tagasi
    tasemeni algus, ei katkesta ummikut; pikem või sügavam vajumine lõpetab selle.
    Kiirustest (ainult kui v_kesk on antud): lõik on ummik ainult siis, kui selle keskmine kiirus (tsüklite kiirus,
    kaalud `kaal`) on alla manöövri keskmise kiiruse v_kesk."""
    r = np.asarray(labilase, float) / taistase
    mask = r >= algus
    l = loigud(mask, 0)
    for (_, a), (b, _) in zip(l[:-1], l[1:]):                 # vajumine kahe ummikulõigu vahel: [a, b)
        if b - a <= auk and (r[a:b] >= pusib).all():
            mask[a:b] = True
    if v_kesk is not None:
        kiirus = np.asarray(kiirus, float)
        kaal = np.where(np.isnan(kiirus), 0, np.asarray(kaal, float))
        for a, b in loigud(mask, 0):
            if not (kaal[a:b].sum() > 0 and np.nansum(kiirus[a:b] * kaal[a:b]) / kaal[a:b].sum() < v_kesk):
                mask[a:b] = False
    return mask


def shift_peak(v, start, share, shift, mode, per_hour=4, pikkus=None):
    """Nihuta osa `share` tipptunni liiklusest `shift` pilu võrra. pikkus = nihutatavate pilude arv alates `start`
    (vaikimisi üks tund; 06_2: kogu tipuaeg).
    mode: "varem", "hiljem", "mõlemad" (pooleks +-shift) või "ühtlane" (laiali vahemikku +-shift)."""
    v = np.asarray(v, dtype=float).copy()
    w = np.arange(start, start + (pikkus or per_hour))
    assert w[0] - shift >= 0 and w[-1] + shift < len(v), "nihe läheb päevast välja"
    moved = v[w] * share
    v[w] -= moved
    if mode == "varem":
        v[w - shift] += moved
    elif mode == "hiljem":
        v[w + shift] += moved
    elif mode == "ühtlane":        # jaotub ühtlaselt kõigile piludele -shift...+shift (v.a oma pilu)
        offs = [o for o in range(-shift, shift + 1) if o != 0]
        for o in offs:
            v[w + o] += moved / len(offs)
    else:                          # "mõlemad": pool täpselt shift võrra varem, pool hiljem
        v[w - shift] += moved / 2
        v[w + shift] += moved / 2
    return v


def spread_reduction(v, window, share, shift_min, mode="mõlemad", per_hour=4):
    """Tipptunni mahu vähenemine (%), kui osa tipptunni liiklusest nihkub. Uut tippu
    otsitakse laiendatud aknast (tipp võib nihkuda)."""
    s, vol = peak_hour(v, window, per_hour)
    shift = int(round(shift_min * per_hour / 60))
    new = shift_peak(v, s, share, shift, mode, per_hour)
    lo = max(window[0] - 2, 0)
    hi = min(window[1] + 2, 24 - 1)
    _, new_vol = peak_hour(new, (lo, hi), per_hour)
    return (1 - new_vol / vol) * 100


# --- Stsenaariumid: kui palju autosid peab tipust ära minema (40_0 ... 40_3) -----------------------------------------
# Kaks mudelit ajaloolistele 15 min profiilidele: A = foori viivitus (HCM valem) -> kiirus ristmiku ees oleval lõigul;
# B = ummikuosa (täis või seisakus radade osa) logija nädala seose järgi. Mõlema skaala jaoks on päevast päeva kõikumine.
STS_ALGUS = "2025-09-01"              # ajaloolised tavalised tööpäevad alates (kuni T09 andmete lõpuni)
STS_QREF = "2026-09-01"               # B: T09 tavaline tipptund 2026. a sügisest (logija nädalaga sama hooaeg)
LOIK_M, V_VABA = 500, 50              # A: ristmiku ees olev lõik (m) ja vaba kiirus (km/h)
HCM_T, HCM_K = 0.25, 0.5              # A: HCM valemi periood (h, = 15 min pilu) ja kindla tsükliga foori tegur k
TSYKKEL_VAIKE, GC_VAIKE, S_VAIKE = 90, 0.28, 1818     # A: kui ristmikul mõõtmist pole (09, 33 linna mediaanid)
LOGIJA_NADAL = pd.to_datetime(["2026-10-16", "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"])
STS_AKNAD = {"hommik": AM_WINDOW, "ohtu": PM_WINDOW}  # halvima tunni algus nagu tipptunnil
STS_MIN_VOIT = 1.0                    # märgatav võit vähemalt 1% (kiirus) või 1 protsendipunkt (ummikuosa)


def hcm_viivitus(X, tsykkel, gC, c_rada):
    """Foori keskmine viivitus sõiduki kohta (s), HCM 2010 valem ilma algjärjekorrata (I = 1):
      d1 = 0.5 C (1 - g/C)^2 / (1 - min(X, 1) g/C)                ühtlane viivitus (ootamine punase tule ajal)
      d2 = 900 T [(X - 1) + sqrt((X - 1)^2 + 8 k X / (c T))]       juhuslik ja üleküllastuse viivitus
    X = koormusaste (voog / läbilaskevõime), C = tsükli pikkus (s), c = raja läbilaskevõime (sõid/h), T = HCM_T."""
    X = np.asarray(X, dtype=float)
    d1 = 0.5 * tsykkel * (1 - gC) ** 2 / (1 - np.minimum(X, 1) * gC)
    d2 = 900 * HCM_T * ((X - 1) + np.sqrt((X - 1) ** 2 + 8 * HCM_K * X / (c_rada * HCM_T)))
    return d1 + d2


def kiirus_viivitusest(d):
    """Keskmine kiirus (km/h) LOIK_M pikkusel lõigul, kui vaba kiirusega sõidule lisandub viivitus d (s)."""
    return 3.6 * LOIK_M / (LOIK_M / (V_VABA / 3.6) + np.asarray(d, dtype=float))


def pav(x, y, kasvav=True):
    """Monotoonne regressioon (pool-adjacent-violators): x järgi mittekahanev (kasvav=False: mittekasvav) y.
    Tagastab sõlmed (xk, yk): iga ploki x-ide keskmine ja y keskmine, xk kasvavas järjekorras (np.interp jaoks)."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    j = np.argsort(x[ok], kind="stable")
    xs, ys = x[ok][j], y[ok][j] * (1 if kasvav else -1)
    plokid = []                                     # [y summa, arv, esimene, viimane]
    for i, v in enumerate(ys):
        plokid.append([v, 1, i, i])
        while len(plokid) > 1 and plokid[-2][0] / plokid[-2][1] > plokid[-1][0] / plokid[-1][1]:
            s, n, _, b = plokid.pop()
            plokid[-1][0] += s
            plokid[-1][1] += n
            plokid[-1][3] = b
    xk = np.array([xs[a:b + 1].mean() for _, _, a, b in plokid])
    yk = np.array([s / n for s, n, _, _ in plokid]) * (1 if kasvav else -1)
    return xk, yk


def tooaeva_profiilid(algus=STS_ALGUS, min_pilu=88):
    """Tavaliste tööpäevade (E-R, õppetöö, mitte püha ega lühendatud päev) ristmike 15 min profiilid alates `algus`.
    Tagastab (ix, V): ix = DataFrame mp_id, paev (rida = ristmiku päev); V = massiiv (ridu, 96), sõidukeid 15 min.
    Päev jääb välja, kui andmeid on alla min_pilu pilu; lühemad augud täidetakse lineaarselt."""
    t, d = load_tallinn()
    d = d[d["kehtiv"] & (d["paevatyyp"] == "tööpäev") & (d["vaheaeg"] == "kool") & (d["paev"] >= algus)]
    t = t.merge(d[["mp_id", "paev"]], on=["mp_id", "paev"])
    w = t.groupby(["mp_id", "paev", "slot"])["v"].sum(min_count=1).unstack("slot").reindex(columns=range(96))
    w = w[w.notna().sum(axis=1) >= min_pilu]
    V = w.T.interpolate(limit_direction="both").T.to_numpy()
    return w.index.to_frame(index=False), V


def tunni_keskmine(M, W=None, per_hour=4):
    """Liikuv tunnikeskmine iga rea kohta: veerg s = pilude s ... s+3 keskmine (W-ga kaalutud); kuju (ridu, 93)."""
    W = np.ones_like(M) if W is None else W
    a = np.cumsum(np.pad(M * W, ((0, 0), (1, 0))), axis=1)
    b = np.cumsum(np.pad(W, ((0, 0), (1, 0))), axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):          # tühi tund (öösel 0 sõidukit) -> NaN
        return (a[:, per_hour:] - a[:, :-per_hour]) / (b[:, per_hour:] - b[:, :-per_hour])


def halvim_tund(M, aken, W=None, per_hour=4):
    """Halvima tunni väärtus igas reas: tunnikeskmise (W-ga kaalutud) suurim väärtus, tunni algus aknas `aken` (h)."""
    return tunni_keskmine(M, W, per_hour)[:, aken[0] * per_hour:aken[1] * per_hour].max(axis=1)


def stsenaarium(V, tyyp, p, aken=None, nihe_min=0, per_hour=4):
    """Profiilid V (ridu, 96) pärast muutust:
      tyyp="yt"     osa p kõigist autodest kaob kogu päevaks (läheb ühistransporti): V (1 - p)
      tyyp="nihe"   osa p iga rea tipptunni (suurim liikuv tunnisumma, algus aknas `aken`) autodest nihkub: pool
                    nihe_min võrra varem, pool hiljem (nagu shift_peak "mõlemad"); muu liiklus jääb paigale."""
    if tyyp == "yt":
        return V * (1 - p)
    k = int(round(nihe_min * per_hour / 60))
    S = tunni_keskmine(V, per_hour=per_hour)[:, aken[0] * per_hour:aken[1] * per_hour]
    s = aken[0] * per_hour + np.argmax(S, axis=1)
    assert (s - k).min() >= 0 and (s + per_hour - 1 + k).max() < V.shape[1], "nihe läheb päevast välja"
    r, w = np.arange(len(V))[:, None], s[:, None] + np.arange(per_hour)
    V2 = V.copy()
    m = V2[r, w] * p
    V2[r, w] -= m
    V2[r, w - k] += m / 2
    V2[r, w + k] += m / 2
    return V2


def mudeli_parameetrid():
    """Mudelite A ja B parameetrid ristmike kaupa varasemate skriptide tabelitest (kaust valjund/):
      A  C = eeldatav piir, sõid/h (27_ristmikud_piir.csv); tsükkel = kindla tsükliga manöövrite hommiku- ja õhtutsükli
         mediaan (09_manoovrid.csv); g/C ja küllastusvoog s rajal = ristmiku manöövrite mediaanid
         (33_kullastusvoog_eeldus.csv); puuduvad -> TSYKKEL_VAIKE, GC_VAIKE, S_VAIKE. Raja läbilaskevõime c = s g/C.
      B  logija nädala tööpäevade (LOGIJA_NADAL) 15 min pilud kell 06-19 (24_koormus_5min.csv, 3 x 5 min): voog
         x = sõidukeid 15 min / (Qref / 4), Qref = tavaline tipptund (suurim liikuv tunnisumma, päevade mediaan);
         ummikuosa y = täis ja seisakus kanalite osa ristmiku täistasemest (tais_pct + seisak_pct, pilu keskmine), %.
         Seos y(x) = kasvav monotoonne regressioon (pav). Kaal = kanalite täistasemete summa (24_kanalid.csv).
    Tagastab (pa, sb): pa = DataFrame (indeks mp_id) kood, C, olek, tsykkel, gC, s, c_rada; sb = dict mp_id ->
    dict(xk, yk, qref, kaal, punkte)."""
    o = DATA_DIR / "valjund"
    pa = pd.read_csv(o / "27_ristmikud_piir.csv").set_index("mp_id")[["kood", "eeldatav", "olek"]]
    pa = pa.rename(columns={"eeldatav": "C"})
    m9 = pd.read_csv(o / "09_manoovrid.csv")
    m9 = m9[m9["meetod"] == "kindel"]
    tsykkel = pd.concat([m9[["mp", "hommik_T"]].set_axis(["mp", "T"], axis=1),
                         m9[["mp", "õhtu_T"]].set_axis(["mp", "T"], axis=1)]).groupby("mp")["T"].median()
    m33 = pd.read_csv(o / "33_kullastusvoog_eeldus.csv").groupby("mp")[["g_C", "kullastusvoog_soid_h_rajal"]].median()
    pa["tsykkel"] = pa["kood"].map(tsykkel).fillna(TSYKKEL_VAIKE)
    pa["gC"] = pa["kood"].map(m33["g_C"]).fillna(GC_VAIKE)
    pa["s"] = pa["kood"].map(m33["kullastusvoog_soid_h_rajal"]).fillna(S_VAIKE)
    pa["c_rada"] = pa["s"] * pa["gC"]

    z = pd.read_csv(o / "24_soojus_ajatelg" / "24_koormus_5min.csv", parse_dates=["paev"])
    z = z[z["paev"].isin(LOGIJA_NADAL)]
    z["slot"] = z["kell"].str[:2].astype(int) * 4 + z["kell"].str[3:5].astype(int) // 15
    z["y"] = z["tais_pct"] + z["seisak_pct"]
    q = z.groupby(["kood", "paev", "slot"]).agg(q=("soidukeid", "sum"), y=("y", "mean"), n=("y", "count")).reset_index()
    q = q[q["n"] == 3]
    kaal = pd.read_csv(o / "24_soojus_ajatelg" / "24_kanalid.csv").groupby("kood")["taistase_soid_h"].sum()
    mp_id = pa.reset_index().set_index("kood")["mp_id"]
    sb = {}
    for kood, g in q.groupby("kood"):
        if kood not in mp_id.index or kood not in kaal.index:
            continue
        w = g.pivot(index="paev", columns="slot", values="q").reindex(columns=range(24, 76))
        qref = np.nanmedian(np.nanmax(w.T.rolling(4).sum().T.to_numpy(), axis=1))
        xk, yk = pav(g["q"] / (qref / 4), g["y"])
        sb[int(mp_id[kood])] = dict(xk=xk, yk=yk, qref=qref, kaal=float(kaal[kood]), punkte=len(g))
    return pa, sb


def tavaline_tipp(ix, V, algus=STS_QREF):
    """Ristmike tavaline tipptund (sõid/h) alates `algus`: iga päeva suurim liikuv tunnisumma (algus 06:00-18:45),
    päevade mediaan. Tagastab dict mp_id -> sõid/h (mudeli B voo ühik)."""
    r = (ix["paev"] >= algus).to_numpy()
    tipp = 4 * tunni_keskmine(V[r])[:, 24:76].max(axis=1)
    return pd.Series(tipp).groupby(ix.loc[r, "mp_id"].to_numpy()).median().to_dict()


def viivitus(ix, V, pa):
    """Mudel A: foori viivitus (s/sõiduk) igas pilus, koormusaste X = 4 x 15 min voog / C."""
    p = pa.loc[ix["mp_id"]]
    col = lambda c: p[c].to_numpy()[:, None]
    return hcm_viivitus(4 * V / col("C"), col("tsykkel"), col("gC"), col("c_rada"))


def ummikuosa(ix, V, sb, qref):
    """Mudel B: ummikuosa (%) igas pilus, y = y_j(V / (qref_j / 4)) ristmiku j seose järgi; qref = ristmiku T09
    tavaline tipptund (tavaline_tipp). Ristmikud, millel seost pole, jäävad NaN."""
    Y = np.full(V.shape, np.nan)
    for mp, rows in ix.groupby("mp_id").indices.items():
        if mp in sb and mp in qref:
            Y[rows] = np.interp(V[rows] / (qref[mp] / 4), sb[mp]["xk"], sb[mp]["yk"])
    return Y


def sts_andmed(paneel_osa=0.85):
    """40_* ühised andmed: mudelite parameetrid, ajaloolised profiilid (ainult ristmikud, millel on 27 piir) ja linna
    kindel valim (ristmikud, millel on mõlemad mudelid ja vähemalt paneel_osa päevadest). Tagastab dict:
      pa, sb, ix, V, qref   mudeli_parameetrid, tooaeva_profiilid, tavaline_tipp
      paneel, iv            linna valimi ristmikud ja nende read (bool)
      kood, paevad, kaal    valimi rea päeva number, päevad, B kaal (täistase) valimi ridadele
      taisi                 linna päevad, kus on vähemalt 90% valimist (bool päevade kohta)"""
    pa, sb = mudeli_parameetrid()
    ix, V = tooaeva_profiilid()
    hoia = ix["mp_id"].isin(pa.index).to_numpy()
    ix, V = ix[hoia].reset_index(drop=True), V[hoia]
    osa = ix.groupby("mp_id").size() / ix["paev"].nunique()
    paneel = [m for m in osa[osa >= paneel_osa].index if m in sb]
    iv = ix["mp_id"].isin(paneel).to_numpy()
    kood, paevad = pd.factorize(ix.loc[iv, "paev"])
    kaal = ix.loc[iv, "mp_id"].map({m: sb[m]["kaal"] for m in paneel}).to_numpy()[:, None]
    taisi = np.bincount(kood, minlength=len(paevad)) >= 0.9 * len(paneel)
    return dict(pa=pa, sb=sb, ix=ix, V=V, qref=tavaline_tipp(ix, V), paneel=paneel, iv=iv, kood=kood,
                paevad=pd.DatetimeIndex(paevad), kaal=kaal, taisi=taisi)


def sts_naitajad(a, Vx, aken):
    """Mudelite A ja B näitajad profiilidele Vx (read nagu a["ix"]; a = sts_andmed()):
      A, B                  ristmiku päeva halvim tund: viivitus (s/sõiduk, sõidukitega kaalutud), ummikuosa (%)
      linnA, linnB          linna päeva halvim tund (kindel valim; A sõidukitega, B täistasemega kaalutud)
      paevA, paevB          ristmiku päev kokku: viivitus x sõidukid (sõiduk-s), ummikuosa pilude summa
      linn_paevA, linn_paevB  sama linna kohta (valimi summa)
    Linna väärtused on päevade kaupa (a["paevad"])."""
    D, Y = viivitus(a["ix"], Vx, a["pa"]), ummikuosa(a["ix"], Vx, a["sb"], a["qref"])
    s = lambda M: pd.DataFrame(M).groupby(a["kood"]).sum().to_numpy()
    Vi, VDi, YKi = Vx[a["iv"]], (Vx * D)[a["iv"]], Y[a["iv"]] * a["kaal"]
    Wl, K = s(Vi), s(np.isfinite(Y[a["iv"]]) * a["kaal"])
    return dict(A=halvim_tund(D, aken, Vx), B=halvim_tund(Y, aken), linnA=halvim_tund(s(VDi) / Wl, aken, Wl),
                linnB=halvim_tund(s(YKi) / K, aken), paevA=(Vx * D).sum(axis=1), paevB=Y.sum(axis=1),
                linn_paevA=s(VDi).sum(axis=1), linn_paevB=(s(YKi) / K).sum(axis=1))


def sts_voit(mudel, alg, uus):
    """Võit: A = kiiruse kasv (%) viivitustest alg -> uus; B = ummikuosa vähenemine (protsendipunkti)."""
    if mudel == "A":
        return 100 * (kiirus_viivitusest(uus) / kiirus_viivitusest(alg) - 1)
    return alg - uus


def sts_nihete_voit(a, p, aken, nihked):
    """Nihke pikkuse mõju (40_1, 40_3): osa p iga päeva tipptunni autodest nihkub pool varem, pool hiljem iga nihke
    (min) võrra; võrdluseks samad autod kaovad (yt, nihe_min = 0). Tagastab (linn, rist):
      linn  mudel, stsenaarium, nihe_min, tipu_voit (halvim tund, sts_voit, linna päevade mediaan), paeva_voit (kogu
            päeva viivituse (A) või ummikuosa summa (B) vähenemine, %, päevade mediaan; miinus = päev läks halvemaks)
      rist  sama ristmike kaupa (mp_id, ristmiku päevade mediaan)"""
    alg = sts_naitajad(a, a["V"], aken)
    t, mp_id = a["taisi"], a["ix"]["mp_id"].to_numpy()
    pv = lambda x0, x1: 100 * (1 - x1 / np.where(x0 > 0, x0, np.nan))
    linn, rist = [], []
    for sk, nihe in [("yt", 0)] + [("nihe", n) for n in nihked]:
        uus = sts_naitajad(a, stsenaarium(a["V"], sk, p, aken, nihe), aken)
        for m in "AB":
            linn.append(dict(mudel=m, stsenaarium=sk, nihe_min=nihe,
                             tipu_voit=np.nanmedian(sts_voit(m, alg[f"linn{m}"][t], uus[f"linn{m}"][t])),
                             paeva_voit=np.nanmedian(pv(alg[f"linn_paev{m}"][t], uus[f"linn_paev{m}"][t]))))
            g = pd.DataFrame(dict(mp_id=mp_id, tipu_voit=sts_voit(m, alg[m], uus[m]),
                                  paeva_voit=pv(alg[f"paev{m}"], uus[f"paev{m}"])))
            rist.append(g.groupby("mp_id").median().reset_index().assign(mudel=m, stsenaarium=sk, nihe_min=nihe))
    return pd.DataFrame(linn), pd.concat(rist, ignore_index=True)


def sts_osakaal(tabel):
    """40_1 ja 40_3 nihkujate osakaal (%) tipu kaupa 40_0_murdepunkt.csv järgi: suurem mudelite A ja B linna
    murdepunktist stsenaariumis "pool 60 min varem, pool hiljem" (siis on nihe mõlema mudeli järgi märgatav);
    kui murdepunkti pole, 30%."""
    z = tabel[tabel["margatav"] & (tabel["stsenaarium"] == "nihe60")].groupby(["tipp", "mudel"])["p"].min()
    return {t: float(z.xs(t, level="tipp").reindex(["A", "B"]).fillna(30).max()) if t in z.index.get_level_values(0)
            else 30.0 for t in STS_AKNAD}


def paeva_mura(paev, m, parem="suurem", aken=21):
    """Päevast päeva kõikumine: päevade väärtus m võrreldes `aken` päeva liikuva mediaaniga (tase ja aeglased muutused
    välja, nagu 37). parem="suurem" (kiirus): kerge päev = 90. protsentiil, mura = q90 / q50 - 1 (osa);
    parem="vaiksem" (ummikuosa): kerge päev = 10. protsentiil, mura = q50 - q10 (samas ühikus kui m)."""
    s = pd.Series(np.asarray(m, dtype=float), index=pd.to_datetime(paev)).sort_index().dropna()
    tase = s.rolling(aken, center=True, min_periods=7).median()
    if parem == "suurem":
        r = s / tase
        return r.quantile(0.9) / r.quantile(0.5) - 1
    r = s - tase
    return r.quantile(0.5) - r.quantile(0.1)


# --- Muutuva pikkusega tipuaeg (06_2, 07_2) ---------------------------------------------------------------------------
# Tipuaeg ei ole alati 60 min: see kestab seni, kuni liiklus on sama aeglane või sama tihe kui koha tavalises tipus.
# "Sama" = päevast päeva kõikumise piires (nagu 40_0 märgatavus). Profiilid on 15 min sammuga.
TIPUAJA_ALA = {"hommik": (5, 12), "ohtu": (12, 21)}   # tipuaeg otsitakse sellest alast (h); serva puudutamine = servas
TIPUAJA_AUK = 1                       # kuni 1 madalam pilu (15 min) tipuaja sees loetakse sisse (nagu 13 aeglane lõik)
TIPUAJA_KIIRUSE_VOOG = 0.5            # kiirus loeb ainult pilus, kus voog >= pool tipu voost: vähese liiklusega aeglus
                                      # (varahommikul pimedas, veokite suurem osa) ei ole liiklusest tingitud


def voo_mura(paev, m, aken=21):
    """Voo päevast päeva kõikumine suhtena (tase ja aeglased muutused välja nagu paeva_mura): päevade väärtus m jagatud
    `aken` päeva liikuva mediaaniga; mura = 1 - q10 / q50 ehk kui palju väiksem on tavaline kerge päev (10. protsentiil)."""
    s = pd.Series(np.asarray(m, dtype=float), index=pd.to_datetime(paev)).sort_index().dropna()
    r = s / s.rolling(aken, center=True, min_periods=7).median()
    return 1 - r.quantile(0.1) / r.quantile(0.5)


def tipu_mura(paev, Q, S=None, per_hour=4):
    """Ühe koha tipu päevast päeva kõikumine. Q (päevi, 96) = päevade 15 min vood, S = sama kujuga kiirused (km/h, NaN =
    kiirus puudub) või None. Päeva tipp aknas STS_AKNAD[tipp]: suurim 15 min voog ja aeglaseim kiirus.
    Tagastab dict tipp -> (mura_q, mura_s): mura_q = voo_mura, mura_s = paeva_mura(kiirus, "suurem") (NaN, kui S puudub)."""
    out = {}
    for tipp, (a, b) in STS_AKNAD.items():
        with warnings.catch_warnings():            # päev ilma andmeteta aknas -> NaN
            warnings.simplefilter("ignore", RuntimeWarning)
            q = np.nanmax(Q[:, a * per_hour:b * per_hour], axis=1)
            s = np.nanmin(S[:, a * per_hour:b * per_hour], axis=1) if S is not None else None
        out[tipp] = (voo_mura(paev, q), paeva_mura(paev, s, "suurem") if s is not None else np.nan)
    return out


def tipuaja_lavi(v, tipp, mura_q, s=None, mura_s=np.nan, per_hour=4):
    """Tipuaja lävendid koha tavalise päeva profiilist v (15 min voog) ja kiirusest s (km/h; None = kiirust pole).
    Tipu pilu k = suurima vooga pilu aknas STS_AKNAD[tipp]. Pilu on tipuaja tasemel, kui
      voog >= q = v[k] (1 - mura_q)            sama tihe kui tavaline tipp (kerge päeva tipu tasemel), või
      voog >= q_s = TIPUAJA_KIIRUSE_VOOG v[k] ja
      kiirus <= s = min(s[ks] (1 + mura_s),    sama aeglane kui tavaline tipp (ks = aeglaseim pilu aknas nende pilude
                                               seas, kus voog >= q_s) ja ühtlasi
                        tavakiirus (1 - mura_s))  märgatavalt aeglasem kui tavaliselt (tavakiirus = pilude mediaan kell
                                               06-20). Kiiruse tingimus kehtib ainult siis, kui tipp ise on märgatavalt
                                               aeglasem: s[ks] <= tavakiirus (1 - mura_s); muidu (nt vaba vooga
                                               maanteel) loeb ainult voog.
    Tagastab dict(k, q, q_s, ks, s, s_tava, s_tipp); ks ja s on None, kui kiiruse tingimust pole."""
    a, b = (h * per_hour for h in STS_AKNAD[tipp])
    v = np.asarray(v, dtype=float)
    k = a + int(np.nanargmax(v[a:b]))
    out = dict(k=k, q=v[k] * (1 - mura_q), q_s=v[k] * TIPUAJA_KIIRUSE_VOOG, ks=None, s=None, s_tava=np.nan,
               s_tipp=np.nan)
    s = None if s is None else np.asarray(s, dtype=float)
    sw = np.where(v[a:b] >= out["q_s"], s[a:b], np.nan) if s is not None else None
    if s is not None and np.isfinite(mura_s) and np.isfinite(sw).any():
        ks = a + int(np.nanargmin(sw))
        out.update(s_tava=float(np.nanmedian(s[6 * per_hour:20 * per_hour])), s_tipp=float(s[ks]))
        if s[ks] <= out["s_tava"] * (1 - mura_s):
            out.update(ks=ks, s=min(s[ks] * (1 + mura_s), out["s_tava"] * (1 - mura_s)))
    return out


def tipuaja_mask(v, lavi, s=None):
    """Pilud, kus liiklus on tipuaja tasemel: voog >= lavi["q"] või (kiiruse tingimusega) voog >= lavi["q_s"] ja
    kiirus <= lavi["s"]."""
    v = np.asarray(v, dtype=float)
    m = v >= lavi["q"]
    if lavi["s"] is not None and s is not None:
        m |= (np.nan_to_num(np.asarray(s, dtype=float), nan=np.inf) <= lavi["s"]) & (v >= lavi["q_s"])
    return m


def tipuaeg(v, tipp, lavi, s=None, per_hour=4):
    """Muutuva pikkusega tipuaeg: tipuaja tasemel pilude (tipuaja_mask) lõigud otsingualas TIPUAJA_ALA[tipp] (kuni
    TIPUAJA_AUK madalamat pilu lõigu sees loetakse sisse); tipuaeg = lõik, kus on tipu pilu k (suurim voog). Kiiruse
    tingimus pikendab tipuaega ainult siis, kui aeglane aeg on tipuga kokku. Tagastab dict:
      a, b        tipuaeg = pilud [a, b); kui k ise pole tipuaja tasemel (nt pärast nihet), a = b = k
      kestus_min  tipuaja pikkus, min
      minuteid    kõik tipuaja tasemel minutid otsingualas (ka teistes lõikudes, madalamaid vahepilusid sisse
                  lugemata; hajutamise ja koolivaheaja mõõt)
      servas      tipuaeg puudutab otsinguala serva (selget algust või lõppu pole)"""
    lo, hi = (h * per_hour for h in TIPUAJA_ALA[tipp])
    m = tipuaja_mask(v, lavi, s)[lo:hi]
    loik = [(a + lo, b + lo) for a, b in loigud(m, TIPUAJA_AUK)]
    a, b = next(((a, b) for a, b in loik if a <= lavi["k"] < b), (lavi["k"], lavi["k"]))
    return dict(a=a, b=b, kestus_min=(b - a) * 60 // per_hour, minuteid=int(m.sum()) * 60 // per_hour,
                servas=b > a and (a == lo or b == hi))


def tipuaja_naitajad(v, lavid, s=None, per_hour=4):
    """Tipuaja näitajad mõlema tipu kohta (nagu peak_metrics), lavid = dict tipp -> tipuaja_lavi:
      ooopaev; {hommik,ohtu}_ algus, algus_h, lopp, lopp_h, kestus_min, minuteid, servas; soidukeid (tipuajal kokku),
      osakaal_% (ööpäevast), soid_h (keskmine voog tipuajal, sõid/h), tipp15_soid_h (suurim 15 min x 4); kestus_voog_min
      (tipuaeg ainult voo tingimusega); kiirus_tingimus (kas kiiruse tingimus kehtib), lavi_q (sõid/15 min), lavi_kmh,
      tavakiirus_kmh, tipu_kiirus_kmh."""
    v = np.asarray(v, dtype=float)
    out = {"ooopaev": float(np.nansum(v))}
    for tipp, lv in lavid.items():
        t = tipuaeg(v, tipp, lv, s, per_hour)
        tv = tipuaeg(v, tipp, {**lv, "ks": None, "s": None}, None, per_hour)
        n = float(v[t["a"]:t["b"]].sum())
        out.update({f"{tipp}_algus": slot_label(t["a"], per_hour), f"{tipp}_algus_h": t["a"] / per_hour,
                    f"{tipp}_lopp": slot_label(t["b"], per_hour), f"{tipp}_lopp_h": t["b"] / per_hour,
                    f"{tipp}_kestus_min": t["kestus_min"], f"{tipp}_minuteid": t["minuteid"],
                    f"{tipp}_servas": t["servas"], f"{tipp}_soidukeid": n, f"{tipp}_osakaal_%": n / out["ooopaev"] * 100,
                    f"{tipp}_soid_h": n / max(t["b"] - t["a"], 1) * per_hour,
                    f"{tipp}_tipp15_soid_h": v[lv["k"]] * per_hour, f"{tipp}_kestus_voog_min": tv["kestus_min"],
                    f"{tipp}_kiirus_tingimus": lv["s"] is not None, f"{tipp}_lavi_q": lv["q"],
                    f"{tipp}_lavi_kmh": lv["s"], f"{tipp}_tavakiirus_kmh": lv["s_tava"],
                    f"{tipp}_tipu_kiirus_kmh": lv["s_tipp"]})
    return out


def ristmike_kiirus(mp_ids, V, pa):
    """Mudel A kiirus (km/h) ristmike profiilidele V (read = mp_ids); ristmik ilma parameetriteta (pa) -> NaN rida."""
    mp_ids = np.asarray(mp_ids)
    S = np.full(np.shape(V), np.nan)
    ok = np.isin(mp_ids, pa.index)
    if ok.any():
        S[ok] = kiirus_viivitusest(viivitus(pd.DataFrame(dict(mp_id=mp_ids[ok])), np.asarray(V, dtype=float)[ok], pa))
    return S


def ristmike_tipumura(pa):
    """Ristmike tipu päevast päeva kõikumine (tipu_mura) kõigi tavaliste tööpäevade järgi (tooaeva_profiilid alates
    andmete algusest), kiirus mudelist A (ristmike_kiirus). Tagastab DataFrame (indeks mp_id, tipp): mura_q, mura_s, paevi."""
    ix, V = tooaeva_profiilid(algus="2000-01-01")
    S = ristmike_kiirus(ix["mp_id"], V, pa)
    rows = []
    for mp, r in ix.groupby("mp_id").indices.items():
        for tipp, (mq, ms) in tipu_mura(ix["paev"].iloc[r], V[r], S[r]).items():
            rows.append(dict(mp_id=mp, tipp=tipp, mura_q=mq, mura_s=ms, paevi=len(r)))
    return pd.DataFrame(rows).set_index(["mp_id", "tipp"])


def ratio_index(df, value, period="kuu", site="id", base_year=TALLINN_BASE_YEAR, by=None, min_sites=3):
    """Mahuga kaalutud indeks (baasaasta = 100) suvaliste loenduskohtade jaoks."""
    base = df[df[period].dt.year == base_year].groupby(site)[value].mean().rename("_base")
    x = df.join(base, on=site).dropna(subset=["_base", value])
    keys = [period] + ([by] if by else [])
    out = x.groupby(keys).agg(_v=(value, "sum"), _b=("_base", "sum"),
                              kohti=(site, "nunique")).reset_index()
    out = out[out["kohti"] >= min_sites]
    out["indeks"] = out["_v"] / out["_b"] * 100
    return out.drop(columns=["_v", "_b"])


# ==============================================================================
# Satelliitaluskaart kaartidele (Web Mercator plaadid, vahemälu kaustas tile_cache/)
# ==============================================================================
SATELLIIT = True                     # False = kaardid ilma taustapildita
TILE_CACHE = DATA_DIR / "tile_cache"
_R = 6378137.0
TILE_SOURCES = [
    # Maa- ja Ruumiameti ortofoto, Google Mercator (foto@GMC), TMS-teenus: rida loetakse alt.
    # Litsents CC BY 4.0, viide nõutud.
    dict(key="maaamet", flip=True, attribution="Ortofoto: Maa- ja Ruumiamet (CC BY 4.0)",
         url="https://tiles.maaamet.ee/tm/tms/1.0.0/foto@GMC/{z}/{x}/{yy}.jpg"),
    dict(key="maaamet_jpeg", flip=True, attribution="Ortofoto: Maa- ja Ruumiamet (CC BY 4.0)",
         url="https://tiles.maaamet.ee/tm/tms/1.0.0/foto@GMC/{z}/{x}/{yy}.jpeg"),
    dict(key="maaamet_xyz", flip=False, attribution="Ortofoto: Maa- ja Ruumiamet (CC BY 4.0)",
         url="https://tiles.maaamet.ee/tm/tms/1.0.0/foto@GMC/{z}/{x}/{yy}.jpg"),
    # varuvariant
    dict(key="esri", flip=False, attribution="Satelliitpilt: Esri, Maxar, Earthstar Geographics",
         url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{yy}/{x}"),
]
_SOURCE_STATUS = {}                  # allika key -> True/False (proovitakse üks kord käivituse kohta)


def to_merc(lon, lat):
    """Pikkus/laius (kraadid) -> Web Mercator (EPSG:3857) meetrid."""
    lon, lat = np.asarray(lon, float), np.asarray(lat, float)
    return _R * np.radians(lon), _R * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))


def _tile_xy(lon, lat, z):
    """Murdosaline XYZ plaadiindeks (x paremale, y alla)."""
    n = 2 ** z
    lat_r = np.radians(lat)
    return ((lon + 180) / 360 * n,
            (1 - np.log(np.tan(lat_r) + 1 / np.cos(lat_r)) / np.pi) / 2 * n)


def _fetch_tile(src, z, x, y, timeout=12):
    """Üks plaat (PIL Image). Vahemälu: tile_cache/<allikas>/<z>/<x>/<y>.img"""
    from io import BytesIO
    from urllib.request import Request, urlopen
    from PIL import Image
    path = TILE_CACHE / src["key"] / str(z) / str(x) / f"{y}.img"
    if path.exists():
        return Image.open(path).convert("RGB")
    yy = (2 ** z - 1 - y) if src["flip"] else y
    req = Request(src["url"].format(z=z, x=x, yy=yy),
                  headers={"User-Agent": "loputoo-liiklusanalyys/1.0 (Python urllib)"})
    with urlopen(req, timeout=timeout) as r:
        data = r.read()
    img = Image.open(BytesIO(data)).convert("RGB")
    a = np.asarray(img)
    if a.std() < 2 and (a.mean() > 235 or a.mean() < 20):   # ühtlane valge/must = pilti pole
        raise ValueError("tühi plaat")                       # (ühtlane meri jääb alles)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return img


@functools.lru_cache(maxsize=8)          # sama kaardiala mitmel paneelil (20): pilt pannakse kokku üks kord
def satellite_image(lon0, lat0, lon1, lat1, target_px=2200, max_tiles=160):
    """Liidab ala (lon0, lat0) ... (lon1, lat1) plaadid üheks pildiks.

    Tagastab (pilt RGB-massiivina, (x_vasak, x_parem, y_all, y_üla) meetrites, viide) või None,
    kui SATELLIIT = False või ükski allikas ei vasta (nt internetita).
    """
    if not SATELLIIT:
        return None
    for z in range(17, 4, -1):                      # suurim suum, mis mahub piiridesse
        xa, ya = _tile_xy(lon0, lat1, z)            # loode nurk
        xb, yb = _tile_xy(lon1, lat0, z)            # kagu nurk
        tx0, tx1, ty0, ty1 = int(xa), int(xb), int(ya), int(yb)
        if (xb - xa) * 256 <= target_px and (tx1 - tx0 + 1) * (ty1 - ty0 + 1) <= max_tiles:
            break
    n = 2 ** z
    world = 2 * np.pi * _R
    ext = (tx0 / n * world - world / 2, (tx1 + 1) / n * world - world / 2,
           world / 2 - (ty1 + 1) / n * world, world / 2 - ty0 / n * world)
    n_tiles = (tx1 - tx0 + 1) * (ty1 - ty0 + 1)
    best = None                                     # (puuduvate osakaal, pilt, viide)
    tried_groups = set()
    for src in TILE_SOURCES:
        group = src["key"].split("_")[0]            # maaamet, maaamet_jpeg, maaamet_xyz = sama pilt
        if _SOURCE_STATUS.get(src["key"]) is False or group in tried_groups:
            continue
        try:
            first = _fetch_tile(src, z, (tx0 + tx1) // 2, (ty0 + ty1) // 2)
            _SOURCE_STATUS[src["key"]] = True
            tried_groups.add(group)
        except Exception as e:
            from urllib.error import HTTPError
            if isinstance(e, ValueError) or (isinstance(e, HTTPError) and e.code in (400, 404)):
                print(f"  (aluskaart: {src['key']} - selle ala/suumi plaati pole)")
            else:                                   # võrk kinni, aegumine, keelatud ...
                _SOURCE_STATUS[src["key"]] = False
                print(f"  (aluskaart: {src['key']} ei vasta - {type(e).__name__})")
            continue
        size = first.size[0]
        canvas = np.full(((ty1 - ty0 + 1) * size, (tx1 - tx0 + 1) * size, 3), 200, dtype=np.uint8)
        missing = 0
        for tx in range(tx0, tx1 + 1):
            for ty in range(ty0, ty1 + 1):
                try:
                    tile = _fetch_tile(src, z, tx, ty)
                    if tile.size != (size, size):
                        tile = tile.resize((size, size))
                    canvas[(ty - ty0) * size:(ty - ty0 + 1) * size,
                           (tx - tx0) * size:(tx - tx0 + 1) * size] = np.asarray(tile)
                except Exception:
                    missing += 1                    # puuduv plaat jääb halliks
        frac = missing / n_tiles
        if best is None or frac < best[0]:
            best = (frac, canvas, src["attribution"])
        if frac <= 0.05:                            # piisavalt täielik - järgmist allikat ei proovi
            break
        print(f"  (aluskaart: {src['key']} - {frac:.0%} plaatidest puudu, proovin järgmist allikat)")
    if best is None:
        return None
    return best[1], ext, best[2]


def add_basemap(ax, lon0, lat0, lon1, lat1, wash=0.3):
    """Satelliit-/ortofototaust teljele (teljed EPSG:3857 meetrites). Punktid joonista
    to_merc()-iga teisendatult. Tagastab kasutatud allika viite või None."""
    x0, y0 = to_merc(lon0, lat0)
    x1, y1 = to_merc(lon1, lat1)
    res = satellite_image(lon0, lat0, lon1, lat1)
    attribution = None
    if res is not None:
        img, ext, attribution = res
        ax.imshow(img, extent=ext, origin="upper", interpolation="bilinear", zorder=0)
        if wash:                                    # hele loor, et punktid paistaksid
            ax.imshow(np.full((2, 2, 3), 255, dtype=np.uint8), extent=ext, alpha=wash, zorder=0.5)
        ax.text(0.995, 0.005, attribution, transform=ax.transAxes, ha="right", va="bottom",
                fontsize=6.5, color="black", zorder=10,
                bbox=dict(facecolor="white", alpha=0.75, edgecolor="none", pad=1.5))
    else:
        ax.set_facecolor("#ecebe7")
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    _scalebar(ax, (lat0 + lat1) / 2)
    return attribution


def _scalebar(ax, lat):
    """Mõõtkava vasakusse alanurka (Mercatori mastaabitegur 1/cos(lat) arvestatud)."""
    import matplotlib.patheffects as pe
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    ground_km = (x1 - x0) * np.cos(np.radians(lat)) / 1000
    km = min([1, 2, 5, 10, 20, 50], key=lambda k: abs(k - ground_km * 0.18))
    length = km * 1000 / np.cos(np.radians(lat))
    bx, by = x0 + 0.03 * (x1 - x0), y0 + 0.04 * (y1 - y0)
    ax.plot([bx, bx + length], [by, by], color="black", lw=5, solid_capstyle="butt", zorder=10)
    ax.plot([bx, bx + length], [by, by], color="white", lw=3, solid_capstyle="butt", zorder=11)
    ax.text(bx + length / 2, by + 0.015 * (y1 - y0), f"{km} km", ha="center", va="bottom",
            fontsize=8, zorder=12, path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])


# ==============================================================================
# Ajastuskaardid (07, 21): värv = kellaaeg, suurus = ööpäevane liiklus
# ==============================================================================
def bbox(df, pad=0.06):
    """Punktide (veerud lon, lat) ümbris (lon0, lat0, lon1, lat1), igas servas lisatud `pad` osa ulatusest."""
    lo0, lo1, la0, la1 = df.lon.min(), df.lon.max(), df.lat.min(), df.lat.max()
    dx, dy = (lo1 - lo0) * pad, (la1 - la0) * pad
    return lo0 - dx, la0 - dy, lo1 + dx, la1 + dy


HALO = [pe.withStroke(linewidth=2.2, foreground="white")]


def ramp(name):
    """Ühe tooniga skaala heledast tumedani, kõige heledam osa välja (satelliidil nähtav)."""
    return LinearSegmentedColormap.from_list(name + "_t", plt.get_cmap(name)(np.linspace(0.3, 1, 256)))


def map_extent(df, pad=0.06):
    """Kaardi ulatus (lon0, lat0, lon1, lat1): punktid + äär, all lisaruum mõõtkavale."""
    lon0, lat0, lon1, lat1 = bbox(df, pad)
    return lon0, lat0 - 0.06 * (lat1 - lat0), lon1, lat1


def hhmm(h):
    """Kellaaeg tundides (nt 7.5) -> 'HH:MM' ('07:30')."""
    m = int(round(h * 60))
    return f"{m // 60:02d}:{m % 60:02d}"


def time_ticks(vmin, vmax):
    """Värviskaala märgid: samm 1/2/5/10/15/30 min nii, et märke oleks kuni 7."""
    span = (vmax - vmin) * 60
    step = next((st for st in (1, 2, 5, 10, 15, 30) if span / st <= 6), 60)
    return np.arange(np.ceil(vmin * 60 / step) * step, vmax * 60 + 1e-6, step) / 60


def place_labels(ax, xs, ys, texts, fontsize=6.5, order=None, obstacles=None):
    """Lihtne siltide paigutus: iga punkti jaoks proovitakse 8 suunda ja valitakse esimene,
    mis ei kattu juba paigutatud siltide ega markeritega (ekraanikoordinaatides).
    obstacles = (x, y, s) massiivid: markerite asukohad ja scatter-suurused (pt^2)."""
    fig = ax.figure
    fig.canvas.draw()
    to_px = ax.transData.transform
    pts = to_px(np.column_stack([xs, ys]))
    placed = []
    dpi_k = fig.dpi / 72
    if obstacles is not None:
        ox, oy, os_ = obstacles
        for (px_, py_), sz in zip(to_px(np.column_stack([ox, oy])), os_):
            r = np.sqrt(sz) / 2 * dpi_k * 0.9
            placed.append((px_ - r, py_ - r, px_ + r, py_ + r))
    offsets = [(6, 5), (6, -11), (-6, 5), (-6, -11), (9, -3), (-9, -3), (0, 9), (0, -15)]
    idx = order if order is not None else range(len(texts))
    for i in idx:
        w, h = len(texts[i]) * fontsize * 0.62 * dpi_k, fontsize * 1.25 * dpi_k
        best = None
        for dx, dy in offsets:
            x0 = pts[i, 0] + dx * dpi_k - (w if dx < 0 else (w / 2 if dx == 0 else 0))
            y0 = pts[i, 1] + dy * dpi_k
            box = (x0, y0, x0 + w, y0 + h)
            hit = any(not (box[2] < b[0] or box[0] > b[2] or box[3] < b[1] or box[1] > b[3]) for b in placed)
            if not hit:
                best = (dx, dy, box)
                break
        if best is None:
            best = (offsets[0][0], offsets[0][1], None)
        dx, dy, box = best
        if box is not None:
            placed.append(box)
        ha = "left" if dx > 0 else ("right" if dx < 0 else "center")
        ax.annotate(texts[i], (xs[i], ys[i]), xytext=(dx, dy), textcoords="offset points", fontsize=fontsize,
                    ha=ha, va="bottom", color="black", zorder=6, path_effects=HALO)


def timing_map(df, fname, title, label_junctions, size_k, label_fs=6.5, pad=0.06, zoom_box=None,
               zoom_label="", naitaja="keskaeg", paneelid=None):
    """Kaardid satelliittaustal (07, 21, 22), vaikimisi kaks: hommik ja õhtu. df = kohad: tyyp (ristmik / maantee),
    suund (maanteel sisse / välja), koht, id, lon, lat, ooopaev ja veerud {hommik,ohtu}_{naitaja}_h (kellaaeg tundides;
    naitaja = kestus: {hommik,ohtu}_kestus_min, minutid). Värv = naitaja (keskaeg = liikluse keskaeg, algus = tipptunni
    algus, kestus = tipuaja kestus 07_2; skaala otstes vähim ja suurim), suurus = ööpäevane liiklus
    (ruutjuure skaalas), ruut = ristmik, ring = maantee suund (hommikul sisse-, õhtul väljasuund). zoom_box =
    (lon0, lat0, lon1, lat1): lähivaate ala katkendliku raamina; selle sees olevaid ristmikke ei nimetata.
    paneelid = [(veeru eesliide, maantee suund, värviskaala, pealkiri), ...] - muud kaardid (22: nädalavahetus),
    kaks kaarti reas."""
    lon0, lat0, lon1, lat1 = map_extent(df, pad)
    (mx0, my0), (mx1, my1) = to_merc(lon0, lat0), to_merc(lon1, lat1)
    ratio = (mx1 - mx0) / (my1 - my0)
    paneelid = paneelid or [
            ("hommik", "sisse", ramp("Blues"), {"keskaeg": "Hommik 06-10", "algus": "Hommik, tipptunni algus 06.00-09.59",
                                                "kestus": "Hommikune tipuaeg"}[naitaja]
             + " (maanteel: sissesõit linna)"),
            ("ohtu", "välja", ramp("Oranges"), {"keskaeg": "Õhtu 15-19", "algus": "Õhtu, tipptunni algus 14.00-18.59",
                                                "kestus": "Õhtune tipuaeg"}[naitaja]
             + " (maanteel: väljasõit linnast)")]
    veerg = (lambda name: f"{name}_kestus_min") if naitaja == "kestus" else (lambda name: f"{name}_{naitaja}_h")
    nr = (len(paneelid) + 1) // 2
    fig, axes = plt.subplots(nr, 2, figsize=(15, nr * 6.3 / ratio + 1.1), layout="constrained", squeeze=False)
    attribution = None
    for ax, (name, suund, cmap, lab) in zip(axes.flat, paneelid):
        attribution = add_basemap(ax, lon0, lat0, lon1, lat1)
        sub = df[(df.tyyp == "ristmik") | (df.suund == (SUUND_MAANTEE or suund))]
        lab = f"{lab.split(' (')[0]} ({SUUND}, maanteel {SUUND_MAANTEE})" if SUUND else lab
        vmin, vmax = sub[veerg(name)].min(), sub[veerg(name)].max()     # skaala otsad = vähim ja suurim
        for tyyp, marker in [("maantee", "o"), ("ristmik", "s")]:
            s2 = sub[sub.tyyp == tyyp]
            mx, my = to_merc(s2.lon.values, s2.lat.values)
            sc = ax.scatter(mx, my, c=s2[veerg(name)], cmap=cmap, vmin=vmin, vmax=vmax,
                            s=np.sqrt(s2.ooopaev) * size_k, marker=marker, edgecolor="black",
                            linewidth=0.7, zorder=5)
        named = sub[(sub.tyyp == "maantee") | label_junctions]
        if zoom_box is not None:
            zx0, zy0, zx1, zy1 = zoom_box
            inside = named.lon.between(zx0, zx1) & named.lat.between(zy0, zy1) & (named.tyyp == "ristmik")
            named = named[~inside]
            (rx0, ry0), (rx1, ry1) = to_merc(zx0, zy0), to_merc(zx1, zy1)
            ax.add_patch(Rectangle((rx0, ry0), rx1 - rx0, ry1 - ry0, fill=False, ls="--", lw=1.2,
                                   ec="black", zorder=4))
            ax.annotate(zoom_label, (rx0, ry1), xytext=(2, 3), textcoords="offset points", fontsize=7,
                        ha="left", va="bottom", zorder=6, path_effects=HALO)
        lbl = named.sort_values("ooopaev", ascending=False)
        lx, ly = to_merc(lbl.lon.values, lbl.lat.values)
        texts = [r.koht.split(" (")[0] if r.tyyp == "maantee" else r.id for r in lbl.itertuples()]
        ox, oy = to_merc(sub.lon.values, sub.lat.values)
        place_labels(ax, lx, ly, texts, fontsize=label_fs,
                     obstacles=(ox, oy, np.sqrt(sub.ooopaev.values) * size_k))
        ax.set_title(lab, fontsize=11)
        cb = fig.colorbar(sc, ax=ax, shrink=0.75)
        if naitaja == "kestus":
            otsamargid(cb, lambda x: f"{x:.0f} min")
            cb.set_label("Tipuaja kestus (pikem = tumedam)")
        else:
            cb.set_ticks(time_ticks(vmin, vmax))
            otsamargid(cb, hhmm)
            cb.set_label({"keskaeg": "Liikluse keskaeg", "algus": "Tipptunni algus"}[naitaja] + " (hilisem = tumedam)")
    handles = [Line2D([], [], marker="s", ls="", color=C_GRAY, markeredgecolor="black", ms=8, label="linna ristmik")]
    if (df.tyyp == "maantee").any():
        handles.append(Line2D([], [], marker="o", ls="", color=C_GRAY, markeredgecolor="black", ms=8,
                              label="maantee loendur (suund)"))
    fig.suptitle(title, x=0.01, ha="left", fontweight="bold")
    fig.canvas.draw()                               # paigutus valmis -> legend otse kaartide alla
    bottom = min(a.get_position().y0 for a in axes.flat)
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, bottom - 0.005), ncol=len(handles),
               fontsize=9)
    save(fig, fname)
    return attribution
