"""
42 - Hooajad: tööpäeva liiklus talvel, kevadel, suvel ja sügisel Tallinna ristmikel ja Tallinna lähedastel
maanteeloenduritel. Võrdluseks arengustrateegia „Tallinn 2035“ liikuvusmõõdikutega (arvudes.tallinn.ee): Tallinna
elanike küsitlus küsib alates 2023. aastast peamist liikumisviisi tööpäeval eraldi „talve perioodil“ ning „kevade, suve
ja sügise perioodil“. Ühistranspordi mõõdik on talve vastustest, ratta ning „ühistranspordi, ratta või jalgsi“ mõõdik
kevade-suve-sügise vastustest, jalgsi mõõdik mõlemast. Joonised näitavad, kui palju autoliiklus nende perioodide vahel
erineb.

SISEND
  common.load_tallinn()        ristmike 15 min loendused ja päevasummad puhastatult (tallinn.count_15min)
  common.maantee_suunad()      maanteeloendurite suunad ja 15 min loendused (highway.count_15min); kahtlase mahuga
                               loendur-kuud ja rikkis rajaga suunapäevad on väljas
  common.day_calendar()        päevatüüp (tööpäev, riigipüha, lühendatud päev); load_tallinn ja maantee_suunad lisavad
  common.load_daily(), counter_month(), ilma_vigaste_kuudeta()
                               42_04: maanteeloendurite päevasummad tunniloendustest (highway.count_hourly, 2019-...),
                               kahtlase mahuga loendur-kuud välja
  highway.counter_channel, common.rikkis_suunapaevad()
                               42_04: suund raja nime järgi ja rikkis rajaga suunapäevad välja (nagu maantee_suunad)

ARVUTUS
  Periood ALGUS (01.12.2024) kuni andmete lõpuni, nii on iga hooaeg sees vähemalt kaks korda (talv 2024/25 ja 2025/26).
  Hooaeg kuu järgi (meteoroloogiline): talv = detsember-veebruar, kevad = märts-mai, suvi = juuni-august, sügis =
    september-november. Küsitlus kuid ei määra, seega on see autori valik.
  Päevad: tööpäevad (E-R, mitte riigipüha ega lühendatud päev), ka koolivaheajal, sest küsimus on tööpäeva liikumise
    kohta kogu perioodil. Suve tööpäevad on peaaegu kõik koolivaheajal.
  Kohad:
    ristmik    kehtivad päevad (load_tallinn); ööpäev = puhastatud 15 min väärtuste summa (puuduv pilu = tavaväärtus).
    maantee    loenduri suund kuni MAX_KM km Tallinna keskusest; raja nime sihtkoht Tallinn = sisse, lähtekoht Tallinn =
               välja (nagu 13); päev arvesse, kui kõik 96 veerandtundi on olemas.
    Koht läheb arvesse, kui tal on igas hooajas vähemalt MIN_PAEVI tööpäeva.
  Koha hooaja ööpäev = hooaja tööpäevade ööpäevade keskmine; koha aastatase = nelja hooaja ööpäeva keskmine (iga hooaeg
    sama kaaluga, ka kui päevi on eri arv).
  Ööpäeva indeks = 100 x koha hooaja ööpäev / koha aastatase. Rühma (ristmikud, maantee sisse, maantee välja) väärtus =
    mediaan üle kohtade: kohtade maht erineb kümneid kordi ja üks rikkis loendur ei muuda tulemust.
  Profiil = iga 15 min pilu keskmine hooaja tööpäevadel. Profiili indeks = 100 x pilu keskmine / koha aasta profiili
    (nelja hooaja profiilide keskmine) suurim pilu; rühma profiil = mediaan üle kohtade iga pilu kohta.
  Tipptund (common.peak_hour) koha hooaja profiilist: hommikul 06:00-09:59 ja õhtul 14:00-18:59 algav suurima mahuga
    60 min. Tipptunni indeks = 100 x hooaja tipptunni maht / aasta profiili tipptunni maht.
  Küsitluse perioodid: talv = talv; kevad-suvi-sügis = koha kolme hooaja väärtuste keskmine (sama kaaluga), siis
    mediaan üle kohtade.
  Kuu indeks: 100 x koha kuu tööpäevade keskmine ööpäev (sama kuu eri aastad koos) / koha aastatase; kuu arvesse, kui
    tööpäevi on vähemalt MIN_KUU_PAEVI.
  Aastakasv (42_04), kogu andmeperiood: ristmikud 07.2024-..., maanteed tunniloendustest 2019-... (sama suunavalik kui
    ülal; päev arvesse, kui suuna kõik rajad on kehtivad, 23-25 eri tundi). Hooaasta = hooaja viimase kuu aasta (talv
    detsember 2025-veebruar 2026 = 2026).
    Koha kuu = kuu tööpäevade ööpäevade keskmine, kui tööpäevi on vähemalt MIN_KUU_PAEVI. Koha hooaja kasv = 100 x
      (hooaja kuude summa / eelmise hooaasta samade kalendrikuude summa - 1), ainult kuud, mis on mõlemal aastal olemas;
      kasv arvesse, kui ühiseid kuid on vähemalt MIN_KUID (nii ei võrrelda nt ainult septembrit kogu sügisega).
    Rühma (ristmikud, maanteed: mõlemad suunad koos) kasv = mediaan üle kohtade, kui kohti on vähemalt MIN_KOHTI;
      vahemik = kohtade 25. ja 75. protsentiil. Osaline hooaeg = ühiseid kuid on mediaankohal alla kolme.

CALCULATION IN PLAIN ENGLISH
  Season by month: winter = Dec-Feb, spring = Mar-May, summer = Jun-Aug, autumn = Sep-Nov. Days = Monday-Friday
    workdays that are not public holidays or shortened days, from 1 Dec 2024 on (school holidays included).
  For each place (junction, or highway counter direction within MAX_KM km of Tallinn): season daily traffic = average
    of its daily totals on the season's workdays. Year level = average of the four season values (each season counts
    once). Daily index = 100 x season daily traffic / year level. Group value = median of the places' indices.
  Profile index = 100 x average vehicles in a 15-minute slot in that season / the largest slot of the place's year
    profile (average of the four season profiles). Peak-hour index = 100 x the season's busiest 60 minutes (morning
    start 06:00-09:59, evening 14:00-18:59) / the same for the year profile.
  Survey periods: winter = the winter value; spring-summer-autumn = average of the three season values per place, then
    the median over places. Month index = 100 x average workday daily total in that calendar month / year level.
  Year-on-year growth (42_04): place month value = average workday daily total of that month. Season growth = 100 x
    (sum of the season's month values / sum of the same calendar months one season-year earlier - 1), using only months
    present in both years and at least MIN_KUID of them. Group growth = median over places (at least MIN_KOHTI), range
    = 25th-75th percentile of places. Highways here come from the hourly counts (2019 on), both directions.

VÄLJUND (joonised kaustas Graafikud/, tabelid kaustas valjund/)
  42_01_hooaja_profiilid.png
      Näitab: tavalise tööpäeva liikluse kulg talvel, kevadel, suvel ja sügisel Tallinna ristmikel ning Tallinna
      lähedastel maanteedel linna poole ja linnast välja.
      Kuidas: kolm paneeli kõrvuti (ristmikud, maantee sisse, maantee välja). x-telg = kellaaeg, y-telg = sõidukeid 15
      min kohta, % koha aasta keskmise tööpäeva suurimast 15 minutist (mediaan üle kohtade). Joon = hooaeg: sinine talv,
      türkiis kevad, oranž suvi, lilla sügis. Kast all keskel: hommiku ja õhtu tipptunni indeks hooaegade kaupa (aasta
      = 100).
  42_02_kuude_tase.png
      Näitab: tööpäeva ööpäevane liiklus kuude kaupa ja küsitluse kahe perioodi keskmine.
      Kuidas: x-telg = kuu detsembrist novembrini (talv on vasakul koos), y-telg = tööpäeva ööpäev, % koha aastatasemest
      (mediaan üle kohtade). Must pidev joon = ristmikud, tumehall katkendjoon = maantee sisse, hall punktiirjoon =
      maantee välja. Taustavärv = hooaeg (sama mis 42_01); ülal klamber = küsitluse periood (talv; kevad-suvi-sügis)
      ning selle perioodi keskmine indeks rühmade kaupa.
  42_03_kuude_tase_hooajad.png
      Näitab: sama mis 42_02, aga ilma küsitluse perioodideta (ainult hooajad).
      Kuidas: nagu 42_02, ülal klambrite ja küsitluse perioodi keskmisteta.
  42_04_hooaja_kasv.png
      Näitab: kui palju tööpäeva liiklus kasvas või vähenes võrreldes eelmise aasta sama hooajaga, linnas ja Tallinna
      lähedastel maanteedel.
      Kuidas: neli paneeli (talv, kevad, suvi, sügis; värviline ruut pealkirjas = hooaja värv nagu 42_01). x-telg =
      hooaasta (talv: 2025/26 = detsember 2025-veebruar 2026), y-telg = kasv, %. Tumehall tulp = Tallinna ristmikud,
      helehall tulp = maanteeloendurid (ainult maanteedega aastal keskel); must püstjoon = kohtade 25.-75. protsentiil,
      nool = joon jätkub väljaspool -18...+14%; arv = mediaankasv. Viirutatud tulp = osaline hooaeg (alla kolme
      võrreldava kuu).
  42_hooajad.csv   rühm x hooaeg (ja küsitluse periood): kohti, tööpäevi, ööpäeva indeks (mediaan, kvartiilid),
                   hommiku ja õhtu tipptunni indeks ja algus (mediaan)
  42_kuud.csv      rühm x kuu: kohti, kuu indeks (mediaan)
  42_kasv.csv      rühm x hooaeg x hooaasta: kohti, võrreldud kuid (mediaan), kasv % (mediaan, 25. ja 75. protsentiil)
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from common import (load_tallinn, maantee_suunad, paeva_maatriks, peak_hour, slot_label, km, set_style, save,
                    save_table, load_daily, counter_month, ilma_vigaste_kuudeta, rikkis_suunapaevad, tabel, ends,
                    day_calendar, AM_WINDOW, PM_WINDOW, TEXT, TEXT2, GRID, C_BLUE, C_AQUA, C_ORANGE, C_VIOLET, C_GRAY)

ALGUS = "2024-12-01"          # esimese talve algus: iga hooaeg on andmetes vähemalt kaks korda
MAX_KM = 25                   # maanteeloendurid kuni 25 km Tallinna keskusest (nagu 13 eelhoiatus)
MIN_PAEVI = 20                # koht arvesse, kui igas hooajas on vähemalt nii palju tööpäevi
MIN_KUU_PAEVI = 8             # kuu arvesse, kui koha kuus on vähemalt nii palju tööpäevi
MIN_KUID = 2                  # 42_04: hooaja kasv arvesse, kui mõlemal aastal on vähemalt nii palju samu kalendrikuid
MIN_KOHTI = 5                 # 42_04: rühma kasv joonisele, kui kohti on vähemalt nii palju
TALLINN_XY = (59.4372, 24.7454)
TALLINN = ("tallinn", "talinn")
HOOAEG = {12: "talv", 1: "talv", 2: "talv", 3: "kevad", 4: "kevad", 5: "kevad", 6: "suvi", 7: "suvi", 8: "suvi",
          9: "sügis", 10: "sügis", 11: "sügis"}
HOOAJAD = ["talv", "kevad", "suvi", "sügis"]
VARV = {"talv": C_BLUE, "kevad": C_AQUA, "suvi": C_ORANGE, "sügis": C_VIOLET}
KSS = "kevad-suvi-sügis"      # küsitluse teine periood
RUHMAD = {"ristmikud": "Tallinna ristmikud", "sisse": "Maantee Tallinna poole", "välja": "Maantee Tallinnast välja"}
JOON = {"ristmikud": dict(color=TEXT, ls="-"), "sisse": dict(color=TEXT2, ls="--"), "välja": dict(color=C_GRAY, ls=":")}
KUUD = [12] + list(range(1, 12))
KUU_NIMI = {1: "jaan", 2: "veebr", 3: "märts", 4: "apr", 5: "mai", 6: "juuni", 7: "juuli", 8: "aug", 9: "sept",
            10: "okt", 11: "nov", 12: "dets"}


def hooaja_naitajad(M, oo):
    """M = 15 min maatriks (indeks koht, paev; veerud pilud 0..95), oo = ööpäev sama indeksiga. Tagastab (ix, prof, kuu):
      ix    koht x hooaeg: paevi, ooopaev (indeks), hommik / ohtu (tipptunni indeks), hommik_algus / ohtu_algus (pilu)
      prof  (koht, hooaeg) x pilu: profiili indeks (100 = koha aasta profiili suurim pilu)
      kuu   koht x kuu: kuu indeks (100 = koha aastatase), ainult kuud, kus tööpäevi >= MIN_KUU_PAEVI
    Ainult kohad, millel igas hooajas on vähemalt MIN_PAEVI tööpäeva."""
    paev = M.index.get_level_values("paev")
    h = pd.Index(paev.month.map(HOOAEG), name="hooaeg")
    koht = M.index.get_level_values(0)
    n = pd.Series(1, index=M.index).groupby([koht, h]).sum().unstack().reindex(columns=HOOAJAD)
    alles = n.index[(n.fillna(0) >= MIN_PAEVI).all(axis=1)]
    vali = koht.isin(alles)
    M, oo, h, koht, paev = M[vali], oo[vali], h[vali], koht[vali], paev[vali]
    hoo = oo.groupby([koht, h]).mean().unstack()[HOOAJAD]
    tase = hoo.mean(axis=1)                                                     # iga hooaeg sama kaaluga
    p = M.groupby([koht, h]).mean()
    aasta = p.groupby(level=0).mean()
    prof = p.div(aasta.max(axis=1), axis=0, level=0) * 100
    rida = []
    for (k, s), v in p.iterrows():
        r = {"koht": k, "hooaeg": s, "paevi": n.loc[k, s], "ooopaev": hoo.loc[k, s] / tase[k] * 100}
        for nimi, aken in (("hommik", AM_WINDOW), ("ohtu", PM_WINDOW)):
            a, maht = peak_hour(v.values, aken)
            r[nimi] = maht / peak_hour(aasta.loc[k].values, aken)[1] * 100
            r[f"{nimi}_algus"] = a
        rida.append(r)
    ix = pd.DataFrame(rida)
    kk = oo.groupby([koht, pd.Index(paev.month, name="kuu")]).agg(["mean", "size"])
    kk = kk[kk["size"] >= MIN_KUU_PAEVI]
    kuu = (kk["mean"] / kk.index.get_level_values(0).map(tase).values * 100).unstack()
    return ix, prof, kuu


def hooaja_kasv(oo):
    """oo = tööpäevade ööpäevad, indeks (koht, paev). Koha kuu = kuu tööpäevade ööpäevade keskmine (kuus vähemalt
    MIN_KUU_PAEVI tööpäeva). Kasv eelmise hooaasta sama hooaja suhtes ainult kalendrikuudest, mis on mõlemal aastal
    olemas (vähemalt MIN_KUID): 100 x (kuude summa / eelmise aasta samade kuude summa - 1). Hooaasta = hooaja viimase
    kuu aasta (detsember läheb järgmise aasta talve). Tagastab tabeli: koht, hooaeg, hooaasta, kuid, see, eelmine, kasv."""
    p = oo.index.get_level_values("paev")
    g = oo.groupby([oo.index.get_level_values(0).rename("koht"), pd.Index(p.year, name="aasta"),
                    pd.Index(p.month, name="kuu")]).agg(["mean", "size"])
    g = g.loc[g["size"] >= MIN_KUU_PAEVI, "mean"].rename("see").reset_index()
    g["hooaeg"] = g["kuu"].map(HOOAEG)
    g["hooaasta"] = g["aasta"] + (g["kuu"] == 12)
    eel = g[["koht", "kuu", "hooaasta", "see"]].assign(hooaasta=g["hooaasta"] + 1).rename(columns={"see": "eelmine"})
    r = (g.merge(eel, on=["koht", "kuu", "hooaasta"]).groupby(["koht", "hooaeg", "hooaasta"])
         .agg(kuid=("kuu", "size"), see=("see", "sum"), eelmine=("eelmine", "sum")).reset_index())
    r = r[r["kuid"] >= MIN_KUID]
    return r.assign(kasv=(r["see"] / r["eelmine"] - 1) * 100)


def kasv_ruhm(r):
    """Kohtade kasvud -> hooaeg x hooaasta: kohti, kuid (mediaan), kasv (mediaan), q25, q75; ainult >= MIN_KOHTI kohta."""
    g = r.groupby(["hooaeg", "hooaasta"])["kasv"]
    t = pd.DataFrame({"kohti": g.size(), "kuid": r.groupby(["hooaeg", "hooaasta"])["kuid"].median(), "kasv": g.median(),
                      "q25": g.quantile(0.25), "q75": g.quantile(0.75)})
    return t[t["kohti"] >= MIN_KOHTI]


# kontroll: kasv ainult mõlemal aastal olemas kuudest (2025 veebruar puudub -> talv välja, sest ühiseid kuid on 1)
_p = pd.to_datetime([f"{y}-{m:02d}-{d:02d}" for y in (2024, 2025) for m in range(1, 13) for d in range(1, 21)
                     if (y, m) != (2025, 2)])
_k = hooaja_kasv(pd.Series(np.where(_p.year == 2025, 110.0, 100.0),
                           index=pd.MultiIndex.from_arrays([["a"] * len(_p), _p], names=["koht", "paev"]))).set_index("hooaeg")
assert sorted(_k.index) == ["kevad", "suvi", "sügis"] and np.allclose(_k["kasv"], 10) and _k["kuid"].eq(3).all() \
    and _k["hooaasta"].eq(2025).all()
# kontroll: kuu -> hooaeg ja koha nelja hooaja ööpäeva indeksite keskmine on 100 (aastatase = hooaegade keskmine)
_i = pd.MultiIndex.from_product([["a"], pd.to_datetime([f"2025-{m:02d}-{d:02d}" for m in range(1, 13) for d in range(1, 21)])],
                                names=["koht", "paev"])
_M = pd.DataFrame(np.tile(np.r_[np.ones(28), 3 * np.ones(8), np.ones(60)], (len(_i), 1)), index=_i)
_M = _M.mul(np.where(_i.get_level_values(1).month.isin([6, 7, 8]), 0.8, 1.0), axis=0)
_ix = hooaja_naitajad(_M, _M.sum(axis=1))[0].set_index("hooaeg")
assert HOOAEG[12] == HOOAEG[2] == "talv" and HOOAEG[9] == "sügis" and abs(_ix["ooopaev"].mean() - 100) < 1e-9 \
    and abs(_ix.loc["suvi", "ooopaev"] / _ix.loc["talv", "ooopaev"] - 0.8) < 1e-9 and _ix["hommik_algus"].eq(28).all()

set_style()
# --- Tallinna ristmikud: kehtivad tööpäevad alates ALGUS ---------------------------------------------------------
t, d0 = load_tallinn()
d0 = d0[d0["kehtiv"] & (d0["paevatyyp"] == "tööpäev")].set_index(["mp_id", "paev"])      # 42_04: kogu periood
d = d0[d0.index.get_level_values("paev") >= ALGUS]
t = t[(t["paev"] >= ALGUS) & (t["paevatyyp"] == "tööpäev")]
M_r = paeva_maatriks(t).reindex(d.index)
# --- Maanteed kuni MAX_KM km Tallinnast, suund raja nime järgi; ainult täis päevad (96 veerandtundi) ----------------
ds, dq = maantee_suunad(ALGUS)
ds["km"] = km(ds["lat"], ds["lon"], *TALLINN_XY)
ds["suund"] = np.select([ds["siht"].isin(TALLINN), ds["lahte"].isin(TALLINN)], ["sisse", "välja"], default="")
ds = ds[(ds["km"] <= MAX_KM) & (ds["suund"] != "")]
dq = dq[dq["site"].isin(ds.index) & dq["argipaev"]]
M_m = paeva_maatriks(dq, "c", ("site", "paev"))
M_m = M_m[M_m.notna().all(axis=1)]
# --- 42_04: samade suundade tööpäeva ööpäevad tunniloendustest (2019-...); suuna kõik rajad kehtivad, rikked välja ---
dd = load_daily()
chn = tabel("highway.counter_channel", dtype={"id": str})
chn[["lahte", "siht"]] = pd.DataFrame([ends(x) for x in chn["channel_label"]], index=chn.index)
chn["site"] = chn["id"] + " | " + chn["lahte"] + " - " + chn["siht"]
m = (ilma_vigaste_kuudeta(dd[dd["kehtiv"]], counter_month(dd), aeg="paev")
     .merge(chn.loc[chn["site"].isin(ds.index), ["id", "kanal", "site"]], on=["id", "kanal"]))
n = m.groupby(["site", "paev"])["kokku"].transform("size")
m = m[n == n.groupby(m["site"]).transform("max")]
halb = rikkis_suunapaevad(m.rename(columns={"paev": "ts", "kokku": "v"})[["site", "kanal", "ts", "v"]])
m = m[~pd.MultiIndex.from_arrays([m["site"], m["paev"]]).isin(halb)]
oo_t = m.groupby(["site", "paev"])["kokku"].sum()
tyyp = day_calendar(oo_t.index.get_level_values("paev")).set_index("paev")["paevatyyp"]
oo_t = oo_t[oo_t.index.get_level_values("paev").map(tyyp) == "tööpäev"]

ix, prof, kuu = {}, {}, {}
ix["ristmikud"], prof["ristmikud"], kuu["ristmikud"] = hooaja_naitajad(M_r, d["summa"])
for s in ("sisse", "välja"):
    M = M_m[M_m.index.get_level_values("site").isin(ds.index[ds["suund"] == s])]
    ix[s], prof[s], kuu[s] = hooaja_naitajad(M, M.sum(axis=1))

# --- Tabelid: hooajad ja küsitluse periood kevad-suvi-sügis (koha kolme hooaja keskmine) ----------------------------
rida = []
for g, x in ix.items():
    x = pd.concat([x, x[x["hooaeg"] != "talv"].groupby("koht", as_index=False)
                   .agg(paevi=("paevi", "sum"), ooopaev=("ooopaev", "mean"), hommik=("hommik", "mean"),
                        ohtu=("ohtu", "mean"), hommik_algus=("hommik_algus", "mean"), ohtu_algus=("ohtu_algus", "mean"))
                   .assign(hooaeg=KSS)])
    for s, y in x.groupby("hooaeg", sort=False):
        rida.append({"ruhm": g, "hooaeg": s, "kohti": len(y), "toopaevi_kohal_mediaan": y["paevi"].median(),
                     "ooopaev_indeks": y["ooopaev"].median(), "ooopaev_q25": y["ooopaev"].quantile(0.25),
                     "ooopaev_q75": y["ooopaev"].quantile(0.75), "hommik_tipptund_indeks": y["hommik"].median(),
                     "hommik_tipptunni_algus": slot_label(y["hommik_algus"].median()),
                     "ohtu_tipptund_indeks": y["ohtu"].median(), "ohtu_tipptunni_algus": slot_label(y["ohtu_algus"].median())})
T = pd.DataFrame(rida).set_index(["ruhm", "hooaeg"])
save_table(T.round(1).reset_index(), "42_hooajad")
K = pd.concat({g: pd.DataFrame({"kohti": k.notna().sum(), "indeks": k.median()}) for g, k in kuu.items()},
              names=["ruhm", "kuu"])
save_table(K.round(1).reset_index(), "42_kuud")

# --- 42_01: hooaja profiilid ---------------------------------------------------------------------------------
koma = lambda x: f"{x:.0f}"
kell = (np.arange(96) + 0.5) / 4
fig, axes = plt.subplots(1, 3, figsize=(14, 4.6), sharey=True)
for ax, g in zip(axes, RUHMAD):
    P = prof[g].groupby(level="hooaeg").median()
    for s in HOOAJAD:
        ax.plot(kell, P.loc[s].values, color=VARV[s], lw=2, label=s.capitalize())
    tekst = "Tipptund (aasta = 100)\n" + "\n".join(
        f"{s:<6} hommik {koma(T.loc[(g, s), 'hommik_tipptund_indeks'])}, õhtu {koma(T.loc[(g, s), 'ohtu_tipptund_indeks'])}"
        for s in HOOAJAD)
    ax.text(0.52, 0.03, tekst, transform=ax.transAxes, va="bottom", ha="center", fontsize=7.8, color=TEXT,
            family="DejaVu Sans Mono", multialignment="left",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=GRID))
    ax.set_title(f"{RUHMAD[g]} ({T.loc[(g, 'talv'), 'kohti']} kohta)", fontsize=11)
    ax.set_xlim(4, 23)
    ax.set_xticks(range(4, 24, 2))
    ax.set_xticklabels([f"{h:02d}" for h in range(4, 24, 2)])
    ax.set_xlabel("Kellaaeg")
axes[0].set_ylabel("Sõidukeid 15 min kohta,\n% aasta tööpäeva suurimast 15 minutist")
axes[0].set_ylim(0, None)
fig.suptitle("Tööpäeva liikluse kulg hooaegade kaupa", x=0.01, ha="left", fontweight="bold", fontsize=13)
fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", bbox_to_anchor=(0.5, -0.0), ncol=4, fontsize=10)
fig.text(0.01, -0.10, f"Tööpäevad (E-R, mitte püha ega lühendatud päev) {pd.Timestamp(ALGUS):%d.%m.%Y} kuni andmete lõpp, "
         f"ka koolivaheajal. Talv XII-II, kevad III-V, suvi VI-VIII, sügis IX-XI. Maanteeloendurid kuni {MAX_KM} km "
         "Tallinna keskusest; mediaan üle kohtade.", fontsize=8, color=TEXT2, ha="left")
fig.tight_layout()
save(fig, "42_01_hooaja_profiilid")

# --- 42_02 ja 42_03: kuude tase; 42_02 koos küsitluse perioodidega, 42_03 ilma ---------------------------------------
def kuude_joonis(kysitlus, nimi):
    """Tööpäeva ööpäev kuude kaupa (K). kysitlus=True: ülal klambrid küsitluse perioodidega ja nende keskmine."""
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(12)
    for i, m in enumerate(KUUD):
        ax.axvspan(i - 0.5, i + 0.5, color=VARV[HOOAEG[m]], alpha=0.10, lw=0)
    for g in RUHMAD:
        y = K.loc[g, "indeks"].reindex(KUUD).values
        ax.plot(x, y, marker="o", ms=5, lw=2, label=RUHMAD[g], **JOON[g])
    lo = np.nanmin([K.loc[g, "indeks"].min() for g in RUHMAD])
    hi = np.nanmax([K.loc[g, "indeks"].max() for g in RUHMAD])
    ax.set_ylim(lo - 4, hi + (13 if kysitlus else 4))
    if kysitlus:
        yk = hi + 4
        for (a, b), s in (((0, 2), "talv"), ((3, 11), KSS)):
            ax.plot([a - 0.4, a - 0.4, b + 0.4, b + 0.4], [yk - 1, yk, yk, yk - 1], color=TEXT2, lw=1)
            vaartus = ", ".join(f"{n} {koma(T.loc[(g, s), 'ooopaev_indeks'])}"
                                for g, n in (("ristmikud", "ristmikud"), ("sisse", "sisse"), ("välja", "välja")))
            ax.text((a + b) / 2, yk + 1, f"Küsitluse periood: {s}\n{vaartus}", ha="center", va="bottom", fontsize=8.5,
                    color=TEXT)
    ax.axhline(100, color=TEXT2, lw=0.8, zorder=0)
    ax.set_xticks(x)
    ax.set_xticklabels([KUU_NIMI[m] for m in KUUD])
    ax.set_xlim(-0.5, 11.5)
    ax.set_ylabel("Tööpäeva ööpäev, % koha aastatasemest")
    ax.set_title("Tööpäeva liiklus kuude kaupa" + (" ja küsitluse perioodid" if kysitlus else ""))
    hooaja_kast = [Patch(color=VARV[s], alpha=0.25, label=s.capitalize()) for s in HOOAJAD]
    ax.legend(handles=ax.get_legend_handles_labels()[0] + hooaja_kast, loc="upper center", bbox_to_anchor=(0.5, -0.08),
              ncol=4, fontsize=9)
    fig.text(0.01, -0.12, "Aastatase = nelja hooaja ööpäeva keskmine (iga hooaeg sama kaaluga)."
             + (" Küsitlus: Tallinna elanike küsitlus, „talve perioodil“ ja „kevade, suve ja sügise perioodil“; kuude "
                "piire küsitlus ei määra." if kysitlus else ""), fontsize=8, color=TEXT2, ha="left")
    save(fig, nimi)


kuude_joonis(True, "42_02_kuude_tase")
kuude_joonis(False, "42_03_kuude_tase_hooajad")

# --- 42_04: hooaja kasv eelmise aasta sama hooajaga võrreldes -----------------------------------------------------
KASV = pd.concat({"ristmikud": kasv_ruhm(hooaja_kasv(d0["summa"])), "maanteed": kasv_ruhm(hooaja_kasv(oo_t))},
                 names=["ruhm"])
KASV["osaline"] = KASV["kuid"] < 3
save_table(KASV.round(2).reset_index(), "42_kasv")
RUHM3 = {"ristmikud": ("Tallinna ristmikud", TEXT2), "maanteed": (f"Maanteeloendurid kuni {MAX_KM} km", "#b9b8b3")}
pluss = lambda x: f"{x:+.1f}".replace(".", ",").replace("-", "−")
a0, a1 = KASV.index.get_level_values("hooaasta").min(), KASV.index.get_level_values("hooaasta").max()
w = 0.38
LO, HI = -18, 14              # protsentiilijoon lõigatakse siin (noolega), et üksikud suured vahemikud skaalat ei venitaks
fig, axes = plt.subplots(2, 2, figsize=(12, 7.6), sharey=True)
for ax, s in zip(axes.flat, HOOAJAD):
    k = KASV[KASV.index.get_level_values("hooaeg") == s].droplevel("hooaeg")
    paar = k.index.get_level_values("hooaasta").value_counts()            # aastad, kus on mõlemad rühmad
    for j, (g, (nimi, varv)) in enumerate(RUHM3.items()):
        if g not in k.index.get_level_values("ruhm"):
            continue
        for a, r in k.loc[g].iterrows():
            xi = a + ((j - 0.5) * w if paar[a] == 2 else 0)
            ax.bar(xi, r["kasv"], width=w, color=varv, alpha=0.5 if r["osaline"] else 1,
                   hatch="///" if r["osaline"] else None, edgecolor="white", lw=0.8)
            lo, hi = max(r["q25"], LO), min(r["q75"], HI)
            ax.plot([xi, xi], [lo, hi], color=TEXT, lw=0.9)
            for piir, otsa, mark in ((r["q25"], lo, "v"), (r["q75"], hi, "^")):
                if piir != otsa:
                    ax.plot(xi, otsa, marker=mark, ms=4, color=TEXT)
            y = hi + 0.5 if r["kasv"] >= 0 else lo - 0.5
            ax.text(xi, y, pluss(r["kasv"]), ha="center", va="bottom" if r["kasv"] >= 0 else "top", fontsize=6.8, color=TEXT)
    ax.axhline(0, color=TEXT2, lw=0.8)
    ax.set_ylim(LO - 3, HI + 3)
    ax.set_xticks(range(a0, a1 + 1))
    ax.set_xticklabels([f"{a - 1}/{a % 100:02d}" if s == "talv" else str(a) for a in range(a0, a1 + 1)], fontsize=8.5)
    ax.set_xlim(a0 - 0.6, a1 + 0.6)
    kuud = "XII-II" if s == "talv" else "-".join(["III", "V"] if s == "kevad" else ["VI", "VIII"] if s == "suvi" else ["IX", "XI"])
    ax.set_title(f"   {s.capitalize()} ({kuud})", fontsize=11)
    ax.text(0, 1.035, "■", transform=ax.transAxes, color=VARV[s], fontsize=13, va="center", ha="left")
for ax in axes[:, 0]:
    ax.set_ylabel("Kasv eelmise aasta\nsama hooajaga võrreldes, %")
fig.suptitle("Tööpäeva liikluse aastakasv hooaegade kaupa", x=0.01, ha="left", fontweight="bold", fontsize=13)
kast = [Patch(color=v, label=n) for n, v in RUHM3.values()] + \
       [Patch(facecolor="#b9b8b3", alpha=0.5, hatch="///", edgecolor="white", label="Osaline hooaeg (alla 3 kuu)"),
        plt.Line2D([], [], color=TEXT, lw=1, marker="^", ms=4, label="Kohtade 25.-75. protsentiil (nool = jätkub)")]
fig.legend(handles=kast, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=4, fontsize=9)
fig.text(0.01, -0.07, "Tööpäevad (E-R, mitte püha ega lühendatud päev). Kasv = hooaja kuude tööpäeva ööpäev / eelmise "
         "aasta samade kuude ööpäev - 1, mediaan üle kohtade. Maanteed: tunniloendused, mõlemad suunad, loendurid kuni "
         f"{MAX_KM} km Tallinna keskusest.\nRistmike andmed algavad 29.07.2024, seega on ristmike kasv olemas alates "
         "2025. aasta sügisest.", fontsize=8, color=TEXT2, ha="left", va="top")
fig.tight_layout()
save(fig, "42_04_hooaja_kasv")
print("Aastakasv (mediaan, %):", "; ".join(f"{g} {s} {a}: {pluss(r['kasv'])} ({r['kohti']:.0f} kohta)"
                                          for (g, s, a), r in KASV.iterrows() if a >= 2025))

for g in RUHMAD:
    r = T.loc[g]
    print(f"{RUHMAD[g]}: {r.loc['talv', 'kohti']} kohta; ööpäev talv {r.loc['talv', 'ooopaev_indeks']:.1f}, "
          f"kevad {r.loc['kevad', 'ooopaev_indeks']:.1f}, suvi {r.loc['suvi', 'ooopaev_indeks']:.1f}, "
          f"sügis {r.loc['sügis', 'ooopaev_indeks']:.1f}, {KSS} {r.loc[KSS, 'ooopaev_indeks']:.1f}; hommikutipp talv "
          f"{r.loc['talv', 'hommik_tipptund_indeks']:.1f}, {KSS} {r.loc[KSS, 'hommik_tipptund_indeks']:.1f}")
