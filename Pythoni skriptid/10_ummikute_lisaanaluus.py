"""
10 - Lisaanalüüsid fooritsüklitest ja ummikutest: vaba ruum ummiku ümber, küllastus, päevade võrdlus, vool ja kiirus,
järjekorra tühjenemine, pikad sõidukid, hooga läbijad, linna koonddiagramm, põhidiagramm manöövri kaupa ja teisene seisakukontroll järjekorrast.

SISEND
  valjund/09_tsuklid.csv, 09_ummikud.csv, 09_ummiku_umber.csv, 09_manoovrid.csv   skripti 09 väljund (09 käib enne)
  common.load_vehicles(None), load_manoeuvres()   sõidukipõhised kirjed: aeg, kiirus, pikkus, loenduril oldud
                                                             aeg (occ), ajavahe (gap), loenduri järjekorranumber (life)
  common.load_junctions(), add_basemap()                     ristmike koordinaadid ja kaardi taust
  Kõik tööpäevade kohta, kell 05-21; ummikutest ainult stabiilsed (vt 09).

ANALÜÜSID: ARVUTUS JA VÄLJUND (joonised kaustas Graafikud/, tabelid kaustas valjund/)
  1) Vaba ruum ummiku ümber (fooriga manöövrid). Iga 15 min akna kohta enne ummiku algust ja pärast lahenemist: vaba
     ruum = täistase x (1 - täituvus) / 4 sõidukit, kus täituvus = akna keskmine läbilase / täistase - nii palju
     sõidukeid mahuks veel aknasse, enne kui tsüklid täis saavad. Võrdluseks ummiku ajal 15 min jooksul läbiv sõidukite
     arv (täistase / 4): nii palju sõite peaks nihkuma, et ummik 15 min lüheneks. Manöövri väärtus = päevade mediaan.
     10_01_vaba_ruum.png   soojuskaart; rida = manööver ja tipp (22 pikimat ummikut; sildis ummiku kestus ja sõidukeid
                        15 min jooksul ummiku ajal), veerg = aken (45-60 ... 0-15 min enne | 0-15 ... 45-60 min pärast;
                        must joon = ummik). Ruudus vaba ruum sõidukites; värv = vaba ruum % ummikuaegsest läbilaskest.
     10_vaba_ruum.csv
  2) Küllastus. Iga ristmiku iga veerandtunni kohta: täis tsüklites (vabal voolul ummikukiirusel) liikunud sõidukite
     osakaal ristmiku kõigist sõidukitest, %.
     10_02_kullastus.png         soojuskaart; rida = ristmik (järjestatud keskmise küllastuse järgi), veerg = veerandtund
                              06-20; värv = osakaal 0-100% (tumedam oranž = rohkem liiklust täis tsüklites).
     10_02b_linna_kullastus.png   joondiagramm: ristmike keskmine täis tsüklites liikuvate sõidukite osakaal veerandtunni
                           kaupa, märgitud hommiku ja õhtu suurim väärtus.
     10_03_kullastus_kaart.png   kaks kaarti ortofototaustal (hommik, õhtu). Värviline ring = ristmik, selle pikim
                              stabiilne ummik: värv = ummiku algus (hilisem = tumedam), suurus = kestus (tööpäevade
                              mediaan). Väike valge ring = stabiilset ummikut pole. Pealkirjas kõigi kindla tsükliga
                              manöövrite stabiilse ummiku kestuse mediaan (tööpäevad).
     10_kullastus.csv
  3) Päevade võrdlus. Manöövri ummiku alguse ja lahenemise vähim, mediaan, suurim ja standardhälve (min) üle tööpäevade.
     10_04_paevade_vordlus.png   (vajab >= 2 tööpäeva) rida = manööver ja tipp, x-telg = kellaaeg. Sinine punkt = ummiku
                              algus igal päeval, oranž punkt = lahenemine, hall riba = mediaanalgusest
                              mediaanlahenemiseni.
     10_paevade_vordlus.csv
  4) Vool ja kiirus vaba vooluga radadel (5 min aknad): vool = sõidukeid x 12 (sõidukit tunnis), kiirus = kiirusega
     sõidukite keskmine (09 kiiruste summa / kiirusega sõidukid; mitte kõigi sõidukitega kaalutud). Läbilaskevõime = voolu 99. protsentiil; kiirus läbilaskevõimel = mediaankiirus, kui vool on >= 95% sellest.
     10_05_vool_kiirus.png   hajuvusdiagrammid kuni 9 suurima manöövri kohta; punkt = 5 min, x = vool, y = kiirus, värv =
                          kellaaeg. Püstine katkendjoon = läbilaskevõime, oranž katkendjoon = 70% vabast kiirusest.
     10_vool_kiirus.csv
  5) Järjekorra tühjenemine (kindla tsükliga manöövrite täis tsüklid, raja kaupa). Vahe esiotsast esiotsani = eelmise
     sõiduki loenduril oldud aeg (occ) + ajavahe (gap), mõlemad loenduri enda mõõdetud, järjestus loenduri
     järjekorranumbri (life) järgi - sündmuse aeg (ts) on ainult kontrolleri küsitluse aeg ega sobi vahede mõõtmiseks.
     Sõiduk on järjekorras seni, kuni vahe eelmisega on <= 3,9 s (HCM 2000 lk 8-27: küllastusvahe 1,9 s + stardikadu kuni
     2 s). Küllastusvahe = järjekorra 5. ja tagumiste sõidukite
     vahede mediaan; küllastusvoog rajal = 3600 / küllastusvahe; stardikadu = 2.-4. sõiduki vahede ja küllastusvahe
     erinevuste summa.
     10_06_kullastusvoog.png   vasakul vahe eelmise sõidukiga järjekorra koha (2-12) järgi: sinine joon = manöövrite
                            mediaan, vöönd = kvartiilid, oranž katkendjoon = küllastusvahe. Paremal rõhtsad tulbad =
                            küllastusvoog raja kohta 25 kõige sagedamini täis manöövril; katkendjoon = kõigi mediaan.
     10_kullastusvoog.csv
  6) Transpordiameti pikkusklassid (common.PIKKUS_KLASS; Kaal jt 2020, lk 2): SAPA kuni 6 m, VAAB 6-12 m, AR üle 12 m
     (mõõdetud pikkus; pikkuseta sõidukid välja). VAAB ja AR osakaal 30 min kaupa. Mõju täis tsüklile vahedest: klassi k
     sõiduki kulutatud aeg = tema vahe eelneva SAPA-ga + järgmise SAPA vahe temaga, võrreldes SAPA-SAPA vahega; SAPA
     ekvivalent = (vahe k-l SAPA järel + vahe SAPA-l k järel) / vahe SAPA-l SAPA järel - 1. (Tsüklite loenduse võrdlus
     eksitaks: tihedamas tsüklis on juhuslikult ka rohkem veokeid.)
     10_07_pikad_soidukid.png   vasakul joondiagramm: VAAB (sinine) ja AR (oranž) osakaal, % kellaaja järgi. Paremal
                             tulbad: vahe mediaan täis tsüklis - SAPA SAPA järel, VAAB SAPA järel, SAPA VAAB järel, AR
                             SAPA järel, SAPA AR järel; pealkirjas, mitme SAPA aja üks VAAB ja üks AR kulutab.
     10_pikad_soidukid.csv, 10_pikad_moju.csv
  7) Hooga läbijad: sõidukite osakaal, kes läbivad loenduri üle 70% manöövri vabast kiirusest (kiiruste 85.
     protsentiil), ehk kiiremini kui liiklus läbilaskevõimel (HCM 2000: 72-97% vabast kiirusest), ehk ei alusta paigalt - näitab, kui hästi saabutakse rohelise ajal. Kindla tsükliga manöövrid.
     10_08_hooga.png   soojuskaart; rida = ristmik, veerg = pooltund 06-20; värv = hooga läbijate osakaal, % (0-100).
     10_hooga.csv   sama manöövri ja tunni kaupa
  8) Linna koonddiagramm (kogu linn ühe punktina, 5 min aknad, kell 6-20).
     a) Klassikaline vool vs tihedus: vool = sõidukit tunnis raja kohta, tihedus = summa(1 / kiirus) ajaühikus raja
        kohta (sõidukit km kohta). Loendurid on stoppjoonel ja järjekorda ei näe, seega murdepunkti ei teki.
     b) Linna läbilase (kõik manöövrid kokku, % 99. protsentiilist) vs täis tsüklites liikuvate sõidukite osakaal.
        Murdepunkt = läbilaske tase, millest alates küllastus kasvama hakkab (murtud joone sobitus vähimruutudega:
        tasane kuni murdepunktini, sealt lineaarne), ja mitu tundi tööpäevas ollakse sellest üle.
     10_09_linna_koonddiagramm.png   kaks hajuvusdiagrammi; punkt = 5 min ühel tööpäeval, värv = kellaaeg. Vasakul x =
                                  tihedus, y = vool, katkendjoon = võrdeline seos. Paremal x = linna läbilase, %
                                  suurimast, y = täis tsüklite osakaal, %; oranž murdjoon = sobitus, püstine
                                  katkendjoon = murdepunkt.
     10_linna_koonddiagramm.csv
     Tunni kaupa: sama murdepunkt kõigil tundidel, igal kellatunnil (06-19) oma tase ja tõus (y = a + b x max(x - x0, 0),
        vähimruutudega selle tunni 5 min punktidest). Prognoos = tunni joone väärtus linna läbilaskel 100% (99. protsentiil),
        kõige rohkem 100%. Tõusu hinnatakse, kui tunnil on üle murdepunkti vähemalt MIN_ULE punkti; muidu jääb tunni joon
        tasaseks (selle tunni liiklus ei ületanud murdepunkti) ja prognoosi ei tehta. Prognoosi 95% vahemik tuleb
        sobituse jääkhajuvusest; järjestikused 5 min punktid on omavahel seotud, seega on vahemik pigem liiga kitsas.
        Mida kaugemale tunni andmetest prognoos ulatub, seda laiem on vahemik (nt tund, mis ületas murdepunkti napilt).
     10_10_murdepunkt_tunniti.png   vasakul 10_09 parem paneel (murdepunkt). Paremal sama telgedega joon iga kellatunni
                                  kohta (värv = kellaaeg, nagu punktidel), pikendatud linna läbilaskeni 100%; punkt ja
                                  silt = prognoositud täis tsüklite osakaal 100% juures (püstine joon); katkendjoon = tund,
                                  mis murdepunkti ei ületanud.
     10_murdepunkt_tunniti.csv     tund: punkte, punkte üle murdepunkti, tase a, tõus b, prognoos 100% juures ja selle
                                  95% vahemiku poollaius
  9) Põhidiagramm manöövri kaupa (fooriga manöövrid, 5 min aknad tööpäevadel): vool raja kohta = sõidukid x 3600 /
     tsüklite aeg / radu; hõivatus = tsüklite hõivatuse (09, raja kohta) ajaga kaalutud keskmine, mis on tihedusega
     võrdeline (vt [Knoop 2020] lk 4-6). Aken on seisakus, kui üle poole selle tsüklite ajast on seisak (09). Kriitiline
     hõivatus = akende mediaanhõivatus, kui vool on >= 95% manöövri voolu 99. protsentiilist.
     10_11_pohidiagramm.png   hajuvusdiagrammid kuue manöövri kohta, kus seisakuaknaid on kõige rohkem; punkt = 5 min,
                           x = hõivatus raja kohta, %, y = vool raja kohta, sõid/h. Sinine = muu aeg, punane = seisak;
                           katkendjoon = 85% täistasemest (seisaku läbilaske piir, HCM 2000 läbilaskevõime lähedal).
     10_11b_kaks_olekut.png   üks manööver (kõige rohkem seisakuaknaid): sama sagedus vabas voolus ja seisakus; hall
                           vöönd = seisakuakende sageduse kvartiilid, sildis kummagi oleku mediaanhõivatus selles vöös.
                           Ülemine telg = tihedus (hõivatus / sõiduki pikkus 5 m). Katkendjoon = kolmnurkne põhidiagramm
                           [Knoop 2020] selle manöövri mõõtudes: tipp = (kriitiline hõivatus, voolu 99. protsentiil),
                           sagedus 0 ummikutihedusel 125 sõidukit km kohta. Allika enda arvud (2400 sõidukit tunnis,
                           80 km/h) on foorita maanteeraja omad ja siia ei sobi. x-telg ulatub ummikutiheduseni
                           (hõivatus 62,5%), et ummikuharu jõuaks teljeni pildi sees; mõõdetud aknad on vasakus
                           kolmandikus ja sildid halli vööndi paremas otsas.
     10_13_pohidiagramm_skeem.png   skeem ilma andmeteta (lõputöö 1.2): kolmnurkne põhidiagramm [Knoop 2020, lk 21-22],
                           kriitiline ja suurim hõivatus, 85% läbilaskevõimest ja ala, mille töö reegel loeb seisakuks.
                           Hõivatuse 10% alampiiri (2.11) skeemil ei ole.
     10_14_pohidiagramm_kolmik.png   kolm paneeli kõrvuti: vasakul 10_11b aknad ilma põhidiagrammita mõõdetud hõivatuse
                           ulatuses, keskel 10_13 skeem, paremal 10_11b (aknad, tiheduse telg ja põhidiagramm).
     10_pohidiagramm.csv      manööver: aknaid, seisakuaknaid, voolu 99. protsentiil, kriitiline hõivatus, seisakuakende
                           mediaanhõivatus ja -vool
  10) Teisene seisakukontroll järjekorrast (kindla tsükliga manöövrid; hõivatuse reegel 9 jääb samaks). Hõivatus näeb
     ainult loenduril seisvat sõidukit; kes peatub loenduri ees, seda ei tõsta. Raja tsükli järjekord = sõidukid
     esimesest kuni esimese tühja ajani > 3,9 s (loendur tühi eelmisest sõidukist selleni; mitte vahe nagu 5, sest
     loenduril seisnud sõiduki aeg sisaldab punast). Järjekord kestis läbi rohelise, kui järjekorras on kõik raja tsükli
     sõidukid (vähemalt 2) ja tühi aeg viimasest sõidukist järgmise tsükli esimeseni on kuni punane + 3,9 s (punane =
     raja tühja aja 5. protsentiil sama tsükli pikkusega tsüklites). 5 min aken on järjekorra seisakus, kui järjekord
     kestis läbi rohelise üle poole raja-tsüklite ajast ja läbilase on <= 85% täistasemest (nagu 9). Järjekorra esimene
     sõiduauto (SAPA) seisis punase ajal: peatumiskaugus loenduri ees = v^2 / (2a), v = mediaankiirus loenduril, a = 1,97
     m/s2 (kvartiilid 1,33-2,62; Micucci jt 2025, tabel 4: paigalt kiirendus ristmikul otse). Kiirus 0 ja loenduril
     >= 5 s = seisis loenduril (kaugus 0); kiirus 0 lühema ajaga = mõõtmata, välja.
     10_12_seisak_jarjekord.png   vasakul rõhtsad tulbad kuni 20 manöövrile: seisakuaknad mõlema reegliga (punane), ainult
                               hõivatusest (sinine), ainult järjekorrast (oranž). Paremal tulpdiagramm: radade arv
                               peatumiskauguse järgi (raja mediaan, 0,5 m kaupa); joon = kõigi radade mediaan kiirendusel
                               1,97 m/s2, katkendjooned = 2,62 ja 1,33 m/s2.
     10_seisak_jarjekord.csv   manööver: aknaid, järjekord läbi rohelise, seisak kummagi reegliga, mõlemad, ainult üks,
                               esimese sõiduki kiirus ja peatumiskaugus
     10_peatumiskaugus.csv     sama raja kaupa (vähemalt 30 täis tsüklit)
  ponytail: rohelise algust ei tea, seega stardikadu on ilma esimese sõiduki reageerimisajata ja "hooga" on suhteline
  (manöövri enda kiirete sõidukite suhtes); täpsemaks on vaja foorikavasid.

CALCULATION IN PLAIN ENGLISH
  1) Free room around congestion: free room = full level x (1 - fill) / 4 vehicles, fill = the 15-minute window's
     average throughput / full level; compared with full level / 4 = vehicles passing in 15 minutes of congestion.
  2) Saturation per junction and quarter hour = vehicles that moved in full cycles / all vehicles x 100.
  3) Day comparison: minimum, median, maximum and standard deviation of congestion start and end over workdays.
  4) Free-flow lanes, 5-minute windows: flow = vehicles x 12 (per hour); speed = sum of measured speeds / vehicles with
     a speed. Capacity = 99th percentile of flow; speed at capacity = median speed when flow >= 95% of capacity.
  5) Queue discharge: headway = previous vehicle's time on the detector + the gap to it, in detector-number order; a
     vehicle is in the queue while its headway is <= 3.9 s (HCM 2000: saturation headway 1.9 s + largest start-up loss 2 s). Saturation headway = median headway of the 5th and later queue
     positions; saturation flow per lane = 3600 / saturation headway; start-up loss = sum over vehicles 2-4 of (their
     headway - saturation headway).
  6) Transport Administration length classes: SAPA up to 6 m, VAAB 6-12 m, AR over 12 m (measured length). VAAB and AR
     share per 30 minutes. Car equivalent of class k = (headway of k behind SAPA + headway of SAPA behind k) /
     SAPA-behind-SAPA headway - 1.
  7) "With momentum" = share of vehicles that pass at above 70% of the movement's free speed (85th percentile speed),
     i.e. faster than traffic at capacity (HCM 2000: 72-97% of free speed).
  8) City as one point (5-minute windows 06-20): flow per lane per hour vs density from the vehicles' 1/speed per unit
     time and lane; city throughput as % of its 99th percentile vs share of vehicles in full cycles. Per clock hour:
     the same break point x0, each hour's own level a and slope b (least squares on that hour's points); prediction =
     a + b x (100 - x0), capped at 100%, only for hours with at least MIN_ULE points above x0; 95% interval from the
     fit's residual spread (consecutive 5-minute points are correlated, so the interval is rather too narrow).
  9) Fundamental diagram per signalised movement (5-minute windows on workdays): flow per lane = vehicles x 3600 /
     cycle time / lanes; occupancy = cycle occupancy per lane (09) weighted by cycle time. A window is a standstill
     when more than half of its cycle time is a standstill (09). Critical occupancy = median occupancy of windows
     whose flow is >= 95% of the movement's 99th percentile flow.
  10) Queue-based second stoppage check (fixed-cycle movements): a lane's queue in a cycle = vehicles from the first
     one until the detector is first empty > 3.9 s (gap, not headway: a car standing on the detector would break it); the queue lasted through green when it holds all of the lane's vehicles in
     that cycle (at least 2) and the empty time to the next cycle's first vehicle is at most red + 3.9 s (red = the
     lane's 5th percentile empty time at that cycle length). A 5-minute window is a queue stoppage when the queue lasted
     through green for more than half of the lane-cycle time and throughput <= 85% of the full level. Stop distance of
     the queue's first car before the detector = v^2 / (2a), v = its median speed on the detector, a = 1.97 m/s^2
     (quartiles 1.33-2.62; Micucci et al. 2025).
  Only complete junction-days (every port recorded 05-23).
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

from common import (tervetel_paevadel, load_vehicles, load_junctions, add_basemap, to_merc, save, save_table, set_style, short_name,
                    slot_label, OUT_DIR, load_manoeuvres, X_LAHEDAL, KIIRUS_YLE, PIKKUS, PIKKUS_PIIRID, PIKKUS_KLASS, PIKKUS_LABEL,
                    C_BLUE, C_ORANGE, C_AQUA, C_GRAY, C_RED, TEXT, TEXT2)

HOOGA = KIIRUS_YLE    # hooga läbija: kiirus üle 70% manöövri kiiruste 85. protsentiilist (üle kiiruse läbilaskevõimel, HCM)
JARJEKORD_VAHE = 1.9 + 2.0   # järjekorras seni, kuni vahe eelmisega <= küllastusvahe + suurim stardikadu (HCM 2000 lk 8-27)
KELL = (5, 21)
MIN_VAATLUSI = 30     # väikseim tsüklite / sõidukite arv, millest näitajat arvutatakse
KEY = ["mp", "direction_id"]
NIHKED = [-60, -45, -30, -15, 15, 30, 45, 60]
NIHE_SILT = [f"{abs(x) - 15}–{abs(x)}\n{'enne' if x < 0 else 'pärast'}" for x in NIHKED]
KLASSID = list(PIKKUS_KLASS.values())       # SAPA, VAAB, AR
MIN_ULE = 6           # tunni tõus (10_10) arvutatakse, kui tunnil on üle murdepunkti vähemalt 6 viie minuti punkti (30 min)
KIIRENDUS = (1.97, 1.33, 2.62)   # paigalt kiirendus ristmikul otse, m/s2: hübriid- ja sisepõlemismootoriga auto keskmine,
                                 # 1. ja 3. kvartiil (Micucci jt 2025, tabel 4, doi:10.3390/su17209332)
SOIDUK_M = 5          # sõiduki pikkus tiheduse teljel (10_11b): hõivatus = tihedus x sõiduki pikkus (Knoop lk 5, 21-22)
K_UMMIK = 125         # ummikutihedus, sõidukit km raja kohta ehk 8 m sõiduki kohta (Knoop, joonis "Basic shape of the
                      # fundamental diagram")
HALO = [pe.withStroke(linewidth=2.2, foreground="white")]
hhmm = lambda h: slot_label(h * 60, 60)
ramp = lambda name: LinearSegmentedColormap.from_list(name + "_t", plt.get_cmap(name)(np.linspace(0.3, 1, 256)))


def tsukli_indeks(st, T, t):
    """Iga aja t tsükli järjekorranumber (algused st, pikkused T) või -1, kui t ei jää ühtegi tsüklisse."""
    k = np.clip(np.searchsorted(st, t, side="right") - 1, 0, None)
    return np.where((t >= st[k]) & (t < st[k] + T[k]), k, -1)


def murdepunkt(x, y):
    """Murtud joon y = a (x <= x0), a + b (x - x0) (x > x0): väikseima ruutveaga (x0, a, b)."""
    parim = None
    for x0 in np.arange(np.percentile(x, 10), np.percentile(x, 95), 0.5):
        z = np.clip(x - x0, 0, None)
        b, a = np.polyfit(z, y, 1)
        viga = ((a + b * z - y) ** 2).sum()
        if parim is None or viga < parim[0]:
            parim = (viga, x0, a, b)
    return parim[1:]


def jarjekord(z):
    """Raja tsükli järjekord. z = sõidukid loenduri järjestuses (veerud cyc, kanal, tyhi = loendur tühi eelmisest
    sõidukist selleni, s); iga (cyc, kanal) kohta sõidukeid n ja järjekorras k = sõidukid esimesest kuni esimese tühja
    ajani > JARJEKORD_VAHE (puuduv ei katkesta, nagu 5)). Tühi aeg, mitte vahe (occ + gap): loenduril seisnud sõiduki
    occ sisaldab punast ja katkestaks järjekorra just seisakus."""
    g = z.groupby(["cyc", "kanal"], sort=False)
    sees = ((z["tyhi"] > JARJEKORD_VAHE) & (g.cumcount() > 0)).groupby([z["cyc"], z["kanal"]], sort=False).cumsum() == 0
    return pd.DataFrame({"n": g.size(), "k": sees.groupby([z["cyc"], z["kanal"]], sort=False).sum()})


peatus = lambda kmh, a: (kmh / 3.6) ** 2 / (2 * a)     # paigalt ühtlase kiirendusega a läbitud teekond kiiruseni kmh, m
_j = jarjekord(pd.DataFrame({"cyc": [0, 0, 0, 1, 1], "kanal": [1] * 5, "tyhi": [50, 2, 5, 40, np.nan]}))
assert _j["n"].tolist() == [3, 2] and _j["k"].tolist() == [2, 2] and peatus(36, 2) == 25
assert tsukli_indeks(np.array([0., 90]), np.array([90., 90]), np.array([5, 89.9, 90, 200])).tolist() == [0, 0, 1, -1]
assert abs(murdepunkt(np.arange(100.), np.clip(np.arange(100.) - 70, 0, None) * 2)[0] - 70) < 1

set_style()
loe = lambda nimi, **kw: pd.read_csv(OUT_DIR / f"{nimi}.csv", encoding="utf-8-sig", **kw)
c = loe("09_tsuklid", parse_dates=["algus"])
c["paev"] = c["algus"].dt.normalize()
c = c[c["paev"].dt.dayofweek < 5].sort_values(KEY + ["paev", "t"]).reset_index(drop=True)
um = loe("09_ummikud", parse_dates=["paev"])
um = um[um["stabiilne"] & (um["tyyp"] == "tööpäev")]
ub = loe("09_ummiku_umber", parse_dates=["paev"])
ub = ub[ub["stabiilne"] & (ub["tyyp"] == "tööpäev")]
man = loe("09_manoovrid")
man["silt"] = man["mp"] + " " + man["manoeuvre"].map(lambda s: short_name(s, 38))
silt = man.set_index(KEY)["silt"]
jn = load_junctions()
rsilt = (jn["code"] + " " + jn["name"].map(lambda s: short_name(s, 34, compact=True))).set_axis(jn["code"])
PAEVI = c["paev"].nunique()
print(f"Tööpäevi: {PAEVI}, tsükleid {len(c):,}, stabiilseid ummikuid {len(um)}")

# --- 1) Vaba ruum ummiku ümber -------------------------------------------------------------------------
x = ub[ub["meetod"] != "vaba"].merge(um[KEY + ["paev", "tipp", "taistase_soid_h", "kestus_min"]], on=KEY + ["paev", "tipp"])
x["ruum_15min"] = (x["taistase_soid_h"] * (1 - x["taituvus"] / 100) / 4).clip(lower=0)
x["ummikus_15min"] = x["taistase_soid_h"] / 4
ruum = (x.groupby(KEY + ["manoeuvre", "tipp", "nihe_min"])
        .agg(paevi=("paev", "nunique"), kestus_min=("kestus_min", "median"), ummikus_15min=("ummikus_15min", "median"),
             taituvus=("taituvus", "median"), ruum_15min=("ruum_15min", "median")).reset_index())
ruum["ruum_%"] = ruum["ruum_15min"] / ruum["ummikus_15min"] * 100
save_table(ruum.round(1), "10_vaba_ruum")
kokku = ruum.groupby("nihe_min")[["ruum_15min", "ruum_%"]].median().reindex(NIHKED)
print("\n1) Vaba ruum 15 min aknas (mediaan üle manöövrite): sõidukit / % ummikuaegsest läbilaskest")
print("   " + "; ".join(f"{n:+d} min: {r.ruum_15min:.0f} / {r['ruum_%']:.0f}%" for n, r in kokku.iterrows()))
RK = KEY + ["manoeuvre", "tipp"]
P = ruum.pivot(index=RK, columns="nihe_min", values="ruum_15min").reindex(columns=NIHKED)
Pp = ruum.pivot(index=RK, columns="nihe_min", values="ruum_%").reindex(columns=NIHKED)
info = ruum.drop_duplicates(RK).set_index(RK)
top = info["kestus_min"].nlargest(22).index
fig, ax = plt.subplots(figsize=(12, 0.42 * len(top) + 2.2))
sns.heatmap(Pp.loc[top], annot=P.loc[top], fmt=".0f", cmap=sns.light_palette(C_AQUA, as_cmap=True), vmin=0, vmax=60,
            annot_kws=dict(fontsize=8), cbar_kws=dict(label="Vaba ruum, % ummiku ajal läbivast sõidukite arvust", shrink=0.7),
            linewidths=0.5, linecolor="white", ax=ax)
ax.set_yticklabels([f"{k[0]} {short_name(k[2], 34)} ({k[3]}; {info.at[k, 'kestus_min']:.0f} min; "
                    f"{info.at[k, 'ummikus_15min']:.0f})" for k in top], fontsize=8, rotation=0)
ax.set_xticklabels(NIHE_SILT, rotation=0, fontsize=8)
ax.set_xlabel("min ummiku algusest / lahenemisest")
ax.set_ylabel("")
ax.axvline(4, color="black", lw=1.5)
ax.set_title("Vaba ruum ummiku ümber: mitu sõidukit mahuks veel 15 min aknasse, enne kui tsüklid täis saavad\n"
             "(rea järel: tipp; ummiku kestus; sõidukeid 15 min jooksul ummiku ajal)", fontsize=10)
save(fig, "10_01_vaba_ruum")

# --- 2) Küllastus: soojuskaart ja kaart ----------------------------------------------------------------
c["veerand"] = (c["t"] // 900).astype(int)
k = c.assign(tn=c["n"] * c["ummikus"]).groupby(["mp", "veerand"])[["tn", "n"]].sum()
K = (k["tn"] / k["n"] * 100).unstack("veerand").reindex(columns=range(24, 80)).fillna(0)       # 06:00-20:00
K = K.loc[K.mean(axis=1).sort_values(ascending=False).index]
save_table(K.rename(columns=lambda q: hhmm(q / 4)).rename_axis(columns=None).reset_index().round(1), "10_kullastus")
print(f"\n2) Küllastus: kõige rohkem liiklust täis tsüklites kell {hhmm(K.mean().idxmax() / 4)} "
      f"(ristmike keskmine {K.mean().max():.0f}%); ristmikke, kus mõnel veerandtunnil üle 50%: {(K.max(axis=1) > 50).sum()}")
fig, ax = plt.subplots(figsize=(12, 0.27 * len(K) + 1.8))
sns.heatmap(K, cmap=sns.light_palette(C_ORANGE, as_cmap=True), vmin=0, vmax=100, ax=ax, yticklabels=False,
            cbar_kws=dict(label="% ristmiku sõidukitest täis tsüklites / ummikukiirusel", shrink=0.6))
ax.set_yticks(np.arange(len(K)) + 0.5)
ax.set_yticklabels([rsilt.get(m, m) for m in K.index], fontsize=7, rotation=0)
ax.set_xticks(np.arange(0, 57, 4))
ax.set_xticklabels([f"{h:02d}" for h in range(6, 21)], rotation=0)
ax.set_xlabel("Kellaaeg")
ax.set_ylabel("")
ax.set_title(f"Küllastus ristmiku ja kellaaja kaupa ({PAEVI} tööpäeva keskmine): kui suur osa liiklusest liigub täis tsüklites")
save(fig, "10_02_kullastus")
lk = K.mean()                                                   # 10_02b: linna keskmine veerandtunni kaupa
fig, ax = plt.subplots(figsize=(11, 4.6))
ax.plot(lk.index / 4, lk.values, color=C_ORANGE, lw=2)
for a, b in [(6, 12), (12, 20)]:
    q = lk[(lk.index / 4 >= a) & (lk.index / 4 < b)].idxmax()
    ax.plot(q / 4, lk[q], "o", color=C_ORANGE, mec="white", ms=8, zorder=3)
    ax.annotate(f"{hhmm(q / 4)}: {lk[q]:.0f}%", (q / 4, lk[q]), xytext=(0, 8), textcoords="offset points", ha="center",
                fontsize=9)
ax.set_xlim(6, 20)
ax.set_ylim(0, lk.max() * 1.2)
ax.set_xticks(range(6, 21))
ax.set_xlabel("Kellaaeg")
ax.set_ylabel("% sõidukitest täis tsüklites\n(ristmike keskmine)")
ax.set_title(f"Küllastus kogu linnas: kui suur osa ristmiku liiklusest liigub täis tsüklites ({PAEVI} tööpäeva keskmine)",
             fontsize=10, loc="left")
fig.tight_layout()
save(fig, "10_02b_linna_kullastus")

u2 = um.groupby(KEY + ["tipp"]).agg(algus_h=("algus_h", "median"), kestus_min=("kestus_min", "median")).reset_index()
jk = jn.dropna(subset=["lat"])
lon0, lon1, lat0, lat1 = jk["lon"].min(), jk["lon"].max(), jk["lat"].min(), jk["lat"].max()
dx, dy = (lon1 - lon0) * 0.06, (lat1 - lat0) * 0.06
lon0, lon1, lat0, lat1 = lon0 - dx, lon1 + dx, lat0 - 2 * dy, lat1 + dy
(mx0, my0), (mx1, my1) = to_merc(lon0, lat0), to_merc(lon1, lat1)
fig, axes = plt.subplots(1, 2, figsize=(15, 6.3 * (my1 - my0) / (mx1 - mx0) + 1.1), layout="constrained")
for ax, (tipp, cmap) in zip(axes, [("hommik", "Blues"), ("õhtu", "Oranges")]):
    s = u2[u2["tipp"].str.contains(tipp)]
    d = jk.merge(s.loc[s.groupby("mp")["kestus_min"].idxmax()], left_on="code", right_on="mp", how="left")
    add_basemap(ax, lon0, lat0, lon1, lat1)
    px, py = to_merc(d["lon"].values, d["lat"].values)
    on = d["kestus_min"].notna().values
    ax.scatter(px[~on], py[~on], s=16, c="white", edgecolor="black", linewidth=0.6, zorder=4)
    if on.any():
        vmin, vmax = np.floor(d["algus_h"].min() * 2) / 2, np.ceil(d["algus_h"].max() * 2) / 2
        sc = ax.scatter(px[on], py[on], c=d["algus_h"][on], s=25 + d["kestus_min"][on] * 3, cmap=ramp(cmap),
                        vmin=vmin, vmax=vmax, edgecolor="black", linewidth=0.7, zorder=5)
        for xx, yy, code in zip(px[on], py[on], d["code"][on]):
            ax.annotate(code, (xx, yy), xytext=(5, 4), textcoords="offset points", fontsize=6.5, zorder=6,
                        path_effects=HALO)
        cb = fig.colorbar(sc, ax=ax, shrink=0.75)
        ticks = np.arange(vmin, vmax + 0.01, 0.5 if vmax - vmin <= 3 else 1)
        cb.set_ticks(ticks)
        cb.set_ticklabels([hhmm(q) for q in ticks])
        cb.set_label("Ummiku algus (hilisem = tumedam)")
    for m in (15, 60, 120):
        ax.scatter([], [], s=25 + m * 3, c="white", edgecolor="black", linewidth=0.7, label=f"{m} min")
    ax.scatter([], [], s=16, c="white", edgecolor="black", linewidth=0.6, label="stabiilset ummikut pole")
    ax.legend(loc="upper left", fontsize=8, title="Ummiku kestus", title_fontsize=8, frameon=True, framealpha=0.85,
              labelspacing=1.1, borderpad=0.9)
    kmed = um.loc[um["tipp"].str.contains(tipp) & (um["meetod"] == "kindel"), "kestus_min"].median()
    ax.set_title(f"{tipp.capitalize()}: {int(on.sum())} ristmikul stabiilne ummik\nkindla tsükliga manöövri ummik "
                 f"mediaanina {kmed:g} min".replace(".", ","), fontsize=11)
fig.suptitle("Iga ristmiku pikim ummik: värv = algus, suurus = kestus (tööpäevade mediaan)", x=0.01, ha="left",
             fontweight="bold")
save(fig, "10_03_kullastus_kaart")

# --- 3) Päevade võrdlus: ummiku alguse ja lahenemise kõikumine --------------------------------------------
p = (um.groupby(KEY + ["manoeuvre", "meetod", "tipp"])
     .agg(paevi=("paev", "nunique"), algus_min=("algus_h", "min"), algus_med=("algus_h", "median"),
          algus_max=("algus_h", "max"), lahenes_min=("lahenes_h", "min"), lahenes_med=("lahenes_h", "median"),
          lahenes_max=("lahenes_h", "max"), kestus_med=("kestus_min", "median"),
          algus_hajuvus_min=("algus_h", lambda s: s.std() * 60), lahenes_hajuvus_min=("lahenes_h", lambda s: s.std() * 60))
     .reset_index())
p["osa_paevadest_%"] = p["paevi"] / PAEVI * 100
save_table(p.assign(**{f"{a}_{b}": p[f"{a}_{b}"].map(hhmm) for a in ["algus", "lahenes"] for b in ["min", "med", "max"]})
           .round(1), "10_paevade_vordlus")
pt = p[p["paevi"] >= 2].sort_values(["paevi", "kestus_med"], ascending=False).head(25)
if len(pt):
    print(f"\n3) Päevade võrdlus: {len(p[p['paevi'] >= 2])} manöövril ummik vähemalt 2 päeval; alguse hajuvus (mediaan) "
          f"{p['algus_hajuvus_min'].median():.0f} min, lahenemise {p['lahenes_hajuvus_min'].median():.0f} min")
    fig, ax = plt.subplots(figsize=(11, 0.34 * len(pt) + 1.8))
    for i, r in enumerate(pt.iloc[::-1].itertuples()):
        d = um[(um["mp"] == r.mp) & (um["direction_id"] == r.direction_id) & (um["tipp"] == r.tipp)]
        ax.plot([r.algus_med, r.lahenes_med], [i, i], color=C_GRAY, lw=8, alpha=0.3, solid_capstyle="butt")
        ax.plot(d["algus_h"], [i] * len(d), "o", color=C_BLUE, ms=4.5, label="ummiku algus (iga päev)" if i == 0 else None)
        ax.plot(d["lahenes_h"], [i] * len(d), "o", color=C_ORANGE, ms=4.5, label="lahenemine (iga päev)" if i == 0 else None)
    ax.set_yticks(range(len(pt)))
    ax.set_yticklabels([f"{r.mp} {short_name(r.manoeuvre, 34)} ({r.tipp}, {r.paevi}/{PAEVI} p)"
                        for r in pt.iloc[::-1].itertuples()], fontsize=8)
    ax.set_xlabel("Kellaaeg (hall riba = mediaanalgusest mediaanlahenemiseni)")
    ax.xaxis.set_major_formatter(lambda q, _: hhmm(q))
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=2)
    ax.set_title(f"Kui korrapärane on ummik: algus ja lahenemine tööpäevade kaupa ({PAEVI} päeva)")
    save(fig, "10_04_paevade_vordlus")
else:
    print("\n3) Päevade võrdlus: tabel tehtud; joonis vajab vähemalt 2 tööpäeva sama manöövri ummikuga.")

# --- 4) Vool ja kiirus vaba vooluga radadel ---------------------------------------------------------------
f = c[c["meetod"] == "vaba"].assign(viis=lambda q: (q["t"] // 300).astype(int))
f["kv"], f["nk"] = f["ks"].fillna(0), f["kn"].fillna(0)          # kiiruste summa ja kiirusega sõidukid (09)
f5 = f.groupby(KEY + ["paev", "viis"])[["n", "kv", "nk"]].sum().reset_index()
f5["voog"], f5["kiirus"] = f5["n"] * 12, f5["kv"] / f5["nk"].where(f5["nk"] > 0)
f5 = f5.dropna(subset=["kiirus"])
rows = []
for key, g in f5.groupby(KEY):
    cap = g["voog"].quantile(0.99)
    rows.append(dict(mp=key[0], direction_id=key[1], labilaskevoime_soid_h=cap,
                     kiirus_labilaskevoimel=g.loc[g["voog"] >= 0.95 * cap, "kiirus"].median(),
                     vaikseim_kiirus=g["kiirus"].quantile(0.01),
                     voog_vaikseimal_kiirusel=g.loc[g["kiirus"] <= g["kiirus"].quantile(0.02), "voog"].median()))
vk = pd.DataFrame(rows).merge(man[KEY + ["manoeuvre", "soidukeid", "vaba_kiirus"]], on=KEY)
save_table(vk.sort_values("soidukeid", ascending=False).round(1), "10_vool_kiirus")
valik = vk[vk["vaba_kiirus"] >= 45] if (vk["vaba_kiirus"] >= 45).sum() >= 3 else vk
valik = valik.nlargest(9, "soidukeid")
print(f"\n4) Vool ja kiirus: {len(vk)} vaba vooluga manöövrit; suurim läbilaskevõime "
      f"{vk['labilaskevoime_soid_h'].max():.0f} sõid/h ({silt.get(tuple(vk.loc[vk['labilaskevoime_soid_h'].idxmax(), KEY]))})")
ncol = 3
fig, axes = plt.subplots(int(np.ceil(len(valik) / ncol)), ncol, figsize=(13, 3.6 * int(np.ceil(len(valik) / ncol))),
                         squeeze=False, layout="constrained")
for ax, r in zip(axes.flat, valik.itertuples()):
    g = f5[(f5["mp"] == r.mp) & (f5["direction_id"] == r.direction_id)]
    sc = ax.scatter(g["voog"], g["kiirus"], c=g["viis"] / 12, cmap="viridis", vmin=KELL[0], vmax=KELL[1], s=9, alpha=0.8)
    ax.axvline(r.labilaskevoime_soid_h, color=TEXT2, lw=0.8, ls="--")
    ax.axhline(KIIRUS_YLE * r.vaba_kiirus, color=C_ORANGE, lw=0.8, ls="--")
    ax.set_title(f"{r.mp} {short_name(r.manoeuvre, 34)}\nläbilaskevõime ~{r.labilaskevoime_soid_h:.0f} sõid/h, "
                 f"seal kiirus {r.kiirus_labilaskevoimel:.0f} km/h", fontsize=9)
    ax.set_xlim(0, None)
    ax.set_ylim(0, None)
for ax in axes.flat[len(valik):]:
    ax.axis("off")
fig.colorbar(sc, ax=axes, shrink=0.6, label="Kellaaeg", ticks=range(KELL[0], KELL[1] + 1, 2))
fig.supxlabel("Sagedus, sõidukit tunnis (5 min aken)", color=TEXT2)
fig.supylabel("Kiirus, km/h", color=TEXT2)
fig.suptitle("Sagedus ja kiirus vaba vooluga radadel (punkt = 5 min; püstjoon = läbilaskevõime, oranž = 70% vabast kiirusest)",
             x=0.01, ha="left", fontweight="bold")
save(fig, "10_05_vool_kiirus")

# --- Sõidukid tsüklitesse (5-7) ---------------------------------------------------------------------------
print("\nLaen sõidukipõhised loendused...")
v = tervetel_paevadel(load_vehicles(None))      # ristmiku terved päevad
dm = load_manoeuvres()
dm = dm.assign(mp_id=dm["mp"].str[2:].astype(int)).rename(columns={"channel": "kanal"})
v = v.merge(dm[["mp_id", "kanal", "mp", "direction_id"]], on=["mp_id", "kanal"]).dropna(subset=["direction_id"])
v["direction_id"] = v["direction_id"].astype(int)
v["paev"] = v["ts"].dt.normalize()
v["t"] = (v["ts"] - v["paev"]).dt.total_seconds()
v = v[(v["paev"].dt.dayofweek < 5) & (v["t"] >= KELL[0] * 3600) & (v["t"] < KELL[1] * 3600)]
v = v.sort_values(KEY + ["paev", "t"]).reset_index(drop=True)
v["klass"] = pd.cut(v["pikkus"], PIKKUS_PIIRID, labels=KLASSID).astype(object)     # pikkuseta (0 m) = NaN
v["hooga"] = v["kiirus"] > HOOGA * v.join(v[v["kiirus"] > 0].groupby(KEY)["kiirus"].quantile(0.85).rename("v85"), on=KEY)["v85"]

# 6a) VAAB ja AR osakaal päeva jooksul (mõõdetud pikkusega sõidukid, 30 min)
mk = v[v["klass"].notna()]
pikad = pd.DataFrame({k: mk["klass"].eq(k).groupby(mk["t"] // 1800 / 2).mean() * 100 for k in KLASSID[1:]})
save_table(pikad.rename_axis("kell_h").reset_index().round(2), "10_pikad_soidukid")

ct, cT, ci = c["t"].values, c["T"].values, c.groupby(KEY + ["paev"]).indices
vt, cyc = v["t"].values, np.full(len(v), -1)
for key, iv in v.groupby(KEY + ["paev"]).indices.items():
    ic = ci.get(key)
    if ic is not None:
        kk = tsukli_indeks(ct[ic], cT[ic], vt[iv])
        cyc[iv[kk >= 0]] = ic[kk[kk >= 0]]
v = v.assign(cyc=cyc)[cyc >= 0]
for veerg, kaal in [("hooga", v["hooga"]), ("kiirusega", v["kiirus"] > 0)]:
    c[veerg] = np.bincount(v["cyc"], weights=kaal, minlength=len(c))
tais = (c["ummikus"] & (c["meetod"] == "kindel")).values                # täis tsüklid kindla tsükliga manöövritel

# --- 5) Järjekorra tühjenemine: vahed raja kaupa täis tsüklites ---------------------------------------------
q = v[tais[v["cyc"].values]].sort_values(["mp", "kanal", "life"])       # loenduri õige järjestus
eel = q.groupby(["mp", "kanal"])
jarjest = eel["life"].diff() == 1                                        # eelmine rida on tõesti eelmine sõiduk
q = q.assign(vahe=(eel["occ"].shift() + q["gap"]).where(jarjest), eel_klass=eel["klass"].shift().where(jarjest))
q["koht"] = q.groupby(["cyc", "kanal"]).cumcount() + 1
q["katkes"] = (((eel["occ"].shift() + q["gap"]) > JARJEKORD_VAHE) & (q["koht"] > 1)).astype(int)
q = q[(q.groupby(["cyc", "kanal"])["katkes"].cumsum() == 0) & q["vahe"].notna() & (q["koht"] > 1)]
H = q[q["koht"] <= 12].groupby(KEY + ["koht"])["vahe"].agg(["median", "size"])
H = H["median"].where(H["size"] >= MIN_VAATLUSI).unstack("koht")
kyll = q[q["koht"] >= 5]
ks = pd.DataFrame({"tais_tsukleid": c[tais].groupby(KEY).size(), "radu": q.groupby(KEY)["kanal"].nunique(),
                   "vaatlusi": kyll.groupby(KEY).size(), "kullastusvahe_s": kyll.groupby(KEY)["vahe"].median()})
ks = ks[ks["vaatlusi"] >= MIN_VAATLUSI]
ks["kullastusvoog_soid_h_rajal"] = 3600 / ks["kullastusvahe_s"]
ks["stardikadu_s"] = H.reindex(ks.index)[[2, 3, 4]].sub(ks["kullastusvahe_s"], axis=0).sum(axis=1, min_count=3)
ks = ks.join(H.add_prefix("vahe_koht_"))
ks.insert(0, "manoeuvre", man.set_index(KEY)["manoeuvre"].reindex(ks.index))
save_table(ks.reset_index().sort_values("tais_tsukleid", ascending=False).round(2), "10_kullastusvoog")
print(f"\n5) Järjekorra tühjenemine ({len(ks)} manöövrit): küllastusvahe mediaan {ks['kullastusvahe_s'].median():.2f} s -> "
      f"{ks['kullastusvoog_soid_h_rajal'].median():.0f} sõid/h rajal; stardikadu mediaan {ks['stardikadu_s'].median():.1f} s")
fig, axes = plt.subplots(1, 2, figsize=(14, 0.3 * min(len(ks), 25) + 2.5), gridspec_kw=dict(width_ratios=[1, 1.25]))
ax = axes[0]
Hk = H.reindex(ks.index)
ax.fill_between(Hk.columns, Hk.quantile(0.25), Hk.quantile(0.75), color=C_BLUE, alpha=0.2, lw=0,
                label="manöövrite kvartiilid")
ax.plot(Hk.columns, Hk.median(), "o-", color=C_BLUE, lw=2.2, label="manöövrite mediaan")
ax.axhline(ks["kullastusvahe_s"].median(), color=C_ORANGE, lw=1, ls="--",
           label=f"küllastusvahe {ks['kullastusvahe_s'].median():.2f} s")
ax.set_ylim(0, None)
ax.set_xticks(Hk.columns)
ax.set_xlabel("Sõiduki koht järjekorras (rajal)")
ax.set_ylabel("Vahe eelmise sõidukiga, s (esiotsast esiotsani)")
ax.set_title("Vahed täis tsüklites järjekorra koha järgi", fontsize=10)
ax.legend(fontsize=8)
ax = axes[1]
kt = ks.nlargest(25, "tais_tsukleid").sort_values("kullastusvoog_soid_h_rajal")
ax.barh(range(len(kt)), kt["kullastusvoog_soid_h_rajal"], color=C_BLUE, alpha=0.85)
ax.axvline(ks["kullastusvoog_soid_h_rajal"].median(), color=C_ORANGE, lw=1, ls="--")
ax.set_yticks(range(len(kt)))
ax.set_yticklabels([silt.get(k, str(k)) for k in kt.index], fontsize=7.5)
ax.set_xlabel("Küllastusvoog, sõidukit tunnis raja kohta (katkendjoon = kõigi mediaan)")
ax.set_title("Küllastusvoog: 25 kõige sagedamini täis manöövrit", fontsize=10)
fig.tight_layout()
save(fig, "10_06_kullastusvoog")

# --- 6) Pikad sõidukid: mõju täis tsükli sõidukite arvule (vahedest) ----------------------------------------
kv = kyll[kyll["klass"].notna() & kyll["eel_klass"].notna()]


def ekvivalent(z):
    """VAAB ja AR SAPA ekvivalent täis tsüklis tabelist z (veerud eel_klass, klass, vahe): klassi k ekvivalent =
    (vahe k-l SAPA järel + vahe SAPA-l k järel) / vahe SAPA-l SAPA järel - 1. NaN, kui paaris on alla MIN_VAATLUSI vahe."""
    h = z.groupby(["eel_klass", "klass"])["vahe"].agg(["median", "size"])
    g = lambda a, b: h["median"].where(h["size"] >= MIN_VAATLUSI).get((a, b), np.nan)
    out = {"vahe_SAPA_SAPA": g("SAPA", "SAPA")}
    for k in KLASSID[1:]:
        out |= {f"vahe_{k}_SAPA_jarel": g("SAPA", k), f"vahe_SAPA_{k}_jarel": g(k, "SAPA"),
                f"{k}_ekvivalent": (g("SAPA", k) + g(k, "SAPA")) / g("SAPA", "SAPA") - 1}
    return pd.Series(out)


_z = pd.DataFrame({"eel_klass": ["SAPA"] * 60 + ["VAAB"] * 30, "klass": ["SAPA"] * 30 + ["VAAB"] * 30 + ["SAPA"] * 30,
                   "vahe": [2.0] * 30 + [3.0] * 30 + [2.5] * 30})
assert ekvivalent(_z)["VAAB_ekvivalent"] == (3.0 + 2.5) / 2.0 - 1 and np.isnan(ekvivalent(_z)["AR_ekvivalent"])
EKV = [f"{k}_ekvivalent" for k in KLASSID[1:]]
moju = kv.groupby(KEY).apply(ekvivalent)
moju = moju[moju[EKV].notna().any(axis=1)]
kogu = ekvivalent(kv)
moju.insert(0, "manoeuvre", man.set_index(KEY)["manoeuvre"].reindex(moju.index))
save_table(pd.concat([moju.reset_index(), pd.DataFrame([dict(kogu, mp="KÕIK", manoeuvre="kõik manöövrid koos")])]).round(2),
           "10_pikad_moju")
print("\n6) Pikkusklassid: " + ", ".join(f"{k} {mk['klass'].eq(k).mean() * 100:.1f}%" for k in KLASSID)
      + "; täis tsüklis võtab " + ", ".join(
          f"{k} {kogu[k + '_ekvivalent']:.1f} SAPA aega (manöövrite kvartiilid {moju[k + '_ekvivalent'].quantile(.25):.1f}–"
          f"{moju[k + '_ekvivalent'].quantile(.75):.1f}, {moju[k + '_ekvivalent'].notna().sum()} manöövrit)" for k in KLASSID[1:]))
fig, axes = plt.subplots(1, 2, figsize=(13, 4.4))
for col, cl in zip(pikad, [C_BLUE, C_ORANGE]):
    axes[0].plot(pikad.index + 0.25, pikad[col], color=cl, lw=1.8, label=PIKKUS_LABEL[dict(zip(KLASSID, PIKKUS))[col]])
axes[0].set_xticks(range(KELL[0], KELL[1] + 1, 2))
axes[0].set_xlabel("Kellaaeg")
axes[0].set_ylabel("Osakaal mõõdetud pikkusega sõidukitest, %")
axes[0].set_ylim(0, None)
axes[0].legend(fontsize=8)
axes[0].set_title("Veokite ja busside (VAAB) ning autorongide (AR) osakaal päeva jooksul", fontsize=10)
vahed = kogu[["vahe_SAPA_SAPA", "vahe_VAAB_SAPA_jarel", "vahe_SAPA_VAAB_jarel", "vahe_AR_SAPA_jarel", "vahe_SAPA_AR_jarel"]]
axes[1].bar(["SAPA\nSAPA järel", "VAAB\nSAPA järel", "SAPA\nVAAB järel", "AR\nSAPA järel", "SAPA\nAR järel"], vahed.values,
            color=[C_GRAY, C_BLUE, C_BLUE, C_ORANGE, C_ORANGE], alpha=0.9)
for i, h in enumerate(vahed.values):
    axes[1].text(i, h + 0.05, f"{h:.2f} s", ha="center", fontsize=9)
axes[1].set_ylabel("Vahe eelmise sõidukiga täis tsüklis, s (mediaan)")
axes[1].set_ylim(0, vahed.max() * 1.18)
axes[1].set_title(f"Täis tsüklis kulutab 1 VAAB {kogu['VAAB_ekvivalent']:.1f} ja 1 AR {kogu['AR_ekvivalent']:.1f} SAPA aega"
                  .replace(".", ","), fontsize=10)
fig.tight_layout()
save(fig, "10_07_pikad_soidukid")

# --- 7) Hooga läbijad (rohelisel saabumine) -------------------------------------------------------------------
s7 = c[c["meetod"] == "kindel"].assign(pool=lambda z: (z["t"] // 1800).astype(int), tund=lambda z: (z["t"] // 3600).astype(int))
hm = s7.groupby(KEY + ["tund"])[["hooga", "kiirusega"]].sum()
hm["osakaal_%"] = hm["hooga"] / hm["kiirusega"].where(hm["kiirusega"] >= MIN_VAATLUSI) * 100
save_table(hm.reset_index().merge(man[KEY + ["manoeuvre"]], on=KEY)[KEY + ["manoeuvre", "tund", "kiirusega", "osakaal_%"]]
           .rename(columns={"kiirusega": "soidukeid"}).round(1), "10_hooga")
hj = s7.groupby(["mp", "pool"])[["hooga", "kiirusega"]].sum()
Hj = (hj["hooga"] / hj["kiirusega"].where(hj["kiirusega"] >= MIN_VAATLUSI) * 100).unstack("pool").reindex(columns=range(12, 40))
Hj = Hj.loc[Hj.mean(axis=1).sort_values(ascending=False).index]
linn = s7.groupby("pool")[["hooga", "kiirusega"]].sum()
linn = (linn["hooga"] / linn["kiirusega"] * 100).reindex(range(12, 40))
print(f"\n7) Hooga läbijaid kokku {s7['hooga'].sum() / s7['kiirusega'].sum() * 100:.0f}%; madalaim kell "
      f"{hhmm(linn.idxmin() / 2)} ({linn.min():.0f}%), kõrgeim kell {hhmm(linn.idxmax() / 2)} ({linn.max():.0f}%)")
fig, ax = plt.subplots(figsize=(12, 0.27 * len(Hj) + 1.8))
sns.heatmap(Hj, cmap=sns.light_palette(C_AQUA, as_cmap=True), vmin=0, vmax=100, ax=ax, yticklabels=False,
            cbar_kws=dict(label="% sõidukitest läbib hooga (üle 70% manöövri vabast kiirusest)", shrink=0.6))
ax.set_yticks(np.arange(len(Hj)) + 0.5)
ax.set_yticklabels([rsilt.get(m, m) for m in Hj.index], fontsize=7, rotation=0)
ax.set_xticks(np.arange(0, 29, 2))
ax.set_xticklabels([f"{h:02d}" for h in range(6, 21)], rotation=0)
ax.set_xlabel("Kellaaeg")
ax.set_ylabel("")
ax.set_title("Hooga läbijate osakaal ristmiku ja kellaaja kaupa (kindla tsükliga manöövrid, tööpäevad)")
save(fig, "10_08_hooga")

# --- 8) Linna koonddiagramm: kas kogu linnal on murdepunkt? --------------------------------------------------
v8 = v[v["kiirus"] > 0]
radu = v8.groupby(["mp", "kanal"]).ngroups
kd = (v8.assign(viis=(v8["t"] // 300).astype(int), inv=1 / v8["kiirus"]).groupby(["paev", "viis"])["inv"]
      .agg(voog="size", tihedus="sum") * 12 / radu)                      # sõid/h ja sõid/km raja kohta
k8 = c.assign(viis=(c["t"] // 300).astype(int), tn=c["n"] * c["ummikus"]).groupby(["paev", "viis"])[["n", "tn"]].sum()
kd = kd.join(pd.DataFrame({"labilase_soid_h": k8["n"] * 12, "tais_%": k8["tn"] / k8["n"] * 100})).dropna().reset_index()
kd = kd[kd["viis"].between(72, 239)]                                     # 06:00-20:00 (servades on tsükleid vähe)
kd["labilase_%"] = kd["labilase_soid_h"] / kd["labilase_soid_h"].quantile(0.99) * 100
kd["kiirus"] = kd["voog"] / kd["tihedus"]
x0, a0, b0 = murdepunkt(kd["labilase_%"].values, kd["tais_%"].values)
ule = (kd["labilase_%"] > x0).groupby(kd["paev"]).sum() * 5 / 60
r_vk = np.corrcoef(kd["voog"], kd["tihedus"])[0, 1]
save_table(kd.assign(kell=kd["viis"].map(lambda q: hhmm(q / 12)), paev=kd["paev"].dt.date).drop(columns="viis").round(2),
           "10_linna_koonddiagramm")
print(f"\n8) Linna koonddiagramm: vool ja tihedus on lõpuni võrdelised (r = {r_vk:.3f}, kiirus {kd['kiirus'].quantile(.05):.0f}–"
      f"{kd['kiirus'].quantile(.95):.0f} km/h) - klassikalist murdepunkti loendurid ei näe. Täis tsüklite osakaal hakkab "
      f"kasvama, kui linna läbilase ületab {x0:.0f}% suurimast (iga +1% lisab {b0:.1f} protsendipunkti); üle selle "
      f"ollakse {ule.mean():.1f} h tööpäevas")
fig, axes = plt.subplots(1, 2, figsize=(14, 5.8), layout="constrained")
sc = axes[0].scatter(kd["tihedus"], kd["voog"], c=kd["viis"] / 12, cmap="viridis", vmin=6, vmax=20, s=12, alpha=0.8)
axes[0].plot([0, kd["tihedus"].max()], [0, kd["tihedus"].max() * kd["voog"].sum() / kd["tihedus"].sum()], color=TEXT2,
             lw=0.8, ls="--")
axes[0].set_xlim(0, None)
axes[0].set_ylim(0, None)
axes[0].set_xlabel("Tihedus, sõidukit km kohta rajal (punktkiirustest)")
axes[0].set_ylabel("Sagedus, sõidukit tunnis rajal")
axes[0].set_title(f"Klassikaline diagramm: sagedus kasvab tihedusega lõpuni\n(r = {str(round(r_vk, 3)).replace('.', ',')}; loendurid on stoppjoonel ja "
                  "järjekorda ei näe)", fontsize=10)
axes[1].scatter(kd["labilase_%"], kd["tais_%"], c=kd["viis"] / 12, cmap="viridis", vmin=6, vmax=20, s=12, alpha=0.8)
xx = np.array([kd["labilase_%"].min(), x0, kd["labilase_%"].max()])
axes[1].plot(xx, a0 + b0 * np.clip(xx - x0, 0, None), color=C_ORANGE, lw=2)
axes[1].axvline(x0, color=C_ORANGE, lw=0.8, ls="--")
axes[1].set_ylim(0, None)
axes[1].set_xlabel("Linna läbilase, % suurimast (kõik manöövrid kokku)")
axes[1].set_ylabel("Täis tsüklites liikuvate sõidukite osakaal, %")
axes[1].set_title(f"Küllastuse murdepunkt: {x0:.0f}% suurimast läbilaskest ({ule.mean():.1f} h tööpäevas üle selle)\n"
                  f"sealt edasi lisab iga +1% liiklust {b0:.1f} protsendipunkti täis tsükleid", fontsize=10)
fig.colorbar(sc, ax=axes, shrink=0.8, label="Kellaaeg")
fig.suptitle(f"Kogu linn ühe punktina (5 min, {PAEVI} tööpäeva, kell 6–20)", x=0.01, ha="left", fontweight="bold")
save(fig, "10_09_linna_koonddiagramm")


def tunni_joon(x, y, x0, min_ule=MIN_ULE):
    """Tunni murtud joon kindla murdepunktiga x0: (a, b, prognoos x = 100 juures, selle 95% vahemiku poollaius);
    vähe punkte üle x0 -> tasane joon, b ja prognoos NaN."""
    z = np.clip(np.asarray(x, float) - x0, 0, None)
    y = np.asarray(y, float)
    if (z > 0).sum() < min_ule:
        return y.mean(), np.nan, np.nan, np.nan
    (b, a), cov = np.polyfit(z, y, 1, cov="unscaled")
    jaak = ((a + b * z - y) ** 2).sum() / (len(y) - 2)
    d = 100 - x0
    return a, b, min(a + b * d, 100.0), 1.96 * np.sqrt(jaak * (d * d * cov[0, 0] + cov[1, 1] + 2 * d * cov[0, 1]))


_x = np.arange(50., 100.)
_a, _b, _p, _u = tunni_joon(_x, 10 + 2 * np.clip(_x - 70, 0, None) + np.tile([-1., 1.], 25), 70)
assert abs(_b - 2) < 0.05 and abs(_p - 70) < 1.5 and 0 < _u < 3 and np.isnan(tunni_joon([10., 20.], [1., 2.], 70)[1])

kd["tund"] = kd["viis"] // 12
tj = pd.DataFrame([(h, len(g), int((g["labilase_%"] > x0).sum()), *tunni_joon(g["labilase_%"], g["tais_%"], x0))
                   for h, g in kd.groupby("tund")], columns=["tund", "punkte", "ule_murdepunkti", "tase_a", "tous_b",
                                                             "prognoos_100_pct", "uv95_pooll"])
save_table(tj.round(2), "10_murdepunkt_tunniti")
pr = tj.dropna(subset=["prognoos_100_pct"])
print(f"   Tunniti (murdepunkt {x0:.0f}%): prognoos 100% läbilaskel " + ", ".join(
    f"{int(r.tund):02d} {r.prognoos_100_pct:.0f}% (±{r.uv95_pooll:.0f})" for r in pr.itertuples()) + f"; murdepunkti ei ületanud "
      f"{len(tj) - len(pr)} tundi")
fig, axes = plt.subplots(1, 2, figsize=(15, 6.2), sharey=True, layout="constrained")
for ax in axes:
    sc = ax.scatter(kd["labilase_%"], kd["tais_%"], c=kd["viis"] / 12, cmap="viridis", vmin=6, vmax=20, s=10,
                    alpha=0.8 if ax is axes[0] else 0.25, lw=0)
    ax.axvline(x0, color=C_ORANGE, lw=0.8, ls="--")
    ax.set_xlabel("Linna läbilase, % suurimast (kõik manöövrid kokku)")
xx = np.array([kd["labilase_%"].min(), x0, kd["labilase_%"].max()])
axes[0].plot(xx, a0 + b0 * np.clip(xx - x0, 0, None), color=C_ORANGE, lw=2)
axes[0].set_ylabel("Täis tsüklites liikuvate sõidukite osakaal, %")
axes[0].set_title(f"Kõik tunnid koos: murdepunkt {x0:.0f}% suurimast läbilaskest,\n"
                  f"sealt edasi iga +1% läbilaset = +{b0:.1f} protsendipunkti täis tsükleid", fontsize=10)
cmap = plt.get_cmap("viridis")
silt_y = []
for r in tj.sort_values("prognoos_100_pct", ascending=False).itertuples():
    varv = cmap((r.tund + 0.5 - 6) / 14)
    g = kd[kd["tund"] == r.tund]
    if np.isnan(r.tous_b):
        axes[1].plot([g["labilase_%"].min(), g["labilase_%"].max()], [r.tase_a] * 2, color=varv, lw=1.2, ls="--")
        continue
    xs = np.linspace(g["labilase_%"].min(), 100, 60)
    axes[1].plot(xs, np.minimum(r.tase_a + r.tous_b * np.clip(xs - x0, 0, None), 100), color=varv, lw=1.6)
    axes[1].errorbar([100], [r.prognoos_100_pct], yerr=[[min(r.uv95_pooll, r.prognoos_100_pct)], [r.uv95_pooll]],
                     fmt="o", color=varv, ms=6, mec="white", mew=0.8, capsize=3, lw=1.2, zorder=4)
    y = min(r.prognoos_100_pct, silt_y[-1] - 3.2) if silt_y else r.prognoos_100_pct    # sildid ei kattu
    silt_y.append(y)
    axes[1].annotate(f"{int(r.tund):02d}: {r.prognoos_100_pct:.0f}% (±{r.uv95_pooll:.0f})", (100, r.prognoos_100_pct),
                     xytext=(112, y), textcoords="data", fontsize=8, va="center", color=TEXT2,
                     arrowprops=dict(arrowstyle="-", color=C_GRAY, lw=0.6))
axes[1].axvline(100, color=TEXT2, lw=0.8)
axes[1].set_xlim(right=135)
axes[1].set_title(f"Tunni kaupa: sama murdepunkt, igal tunnil oma tõus, prognoos läbilaskel 100%\n"
                  f"vurrud = 95% vahemik; katkendjoon = alla {MIN_ULE * 5} min üle murdepunkti, prognoosi pole",
                  fontsize=10)
fig.colorbar(sc, ax=axes, shrink=0.8, label="Kellaaeg")
fig.suptitle(f"Linna küllastuse murdepunkt ja selle prognoos tunniti (5 min, {PAEVI} tööpäeva, kell 6–20)", x=0.01,
             ha="left", fontweight="bold")
save(fig, "10_10_murdepunkt_tunniti")

# --- 9) Põhidiagramm manöövri kaupa: vool ja hõivatus ---------------------------------------------------------
p9 = c[c["meetod"] != "vaba"].merge(man[KEY + ["radu"]], on=KEY)
p9 = p9.assign(viis=(p9["t"] // 300).astype(int), hT=p9["hoivatus"] * p9["T"], sT=p9["T"] * p9["seisak"])
p5 = p9.groupby(KEY + ["paev", "viis"]).agg(n=("n", "sum"), T=("T", "sum"), hT=("hT", "sum"), sT=("sT", "sum"),
                                            radu=("radu", "first")).reset_index()
p5 = p5[p5["T"] >= 240]                                                   # aknas vähemalt 4 min tsükleid
p5["vool"] = p5["n"] * 3600 / p5["T"] / p5["radu"]                        # sõid/h raja kohta
p5["hoivatus_%"] = p5["hT"] / p5["T"] * 100                               # 09 hõivatus on juba raja kohta
p5["seisak"] = p5["sT"] > p5["T"] / 2
rows = []
for key, g in p5.groupby(KEY):
    q99 = g["vool"].quantile(0.99)
    s9 = g[g["seisak"]]
    rows.append(dict(mp=key[0], direction_id=key[1], aknaid=len(g), seisakuaknaid=len(s9), vool_q99=q99,
                     kriitiline_hoivatus_pct=g.loc[g["vool"] >= 0.95 * q99, "hoivatus_%"].median(),
                     seisak_hoivatus_pct=s9["hoivatus_%"].median(), seisak_vool_pct=(s9["vool"] / q99 * 100).median()))
pd9 = pd.DataFrame(rows).merge(man[KEY + ["manoeuvre"]], on=KEY)
save_table(pd9.sort_values("seisakuaknaid", ascending=False).round(1), "10_pohidiagramm")
valik9 = pd9[pd9["seisakuaknaid"] > 0].nlargest(6, "seisakuaknaid")
v9 = valik9[valik9["seisakuaknaid"] >= 10]
print(f"\n9) Põhidiagramm: {len(pd9)} fooriga manöövrit, seisakuaknaid {int(pd9['seisakuaknaid'].sum())}; joonisel kuus "
      f"manöövrit, kus neid on kõige rohkem: seisakuaknas on hõivatus mediaanina {v9['seisak_hoivatus_pct'].median():.0f}% "
      f"(kriitiline {v9['kriitiline_hoivatus_pct'].median():.0f}%) ja vool {v9['seisak_vool_pct'].median():.0f}% suurimast")
fig, axes = plt.subplots(2, 3, figsize=(14, 8), squeeze=False, layout="constrained")
for ax, r in zip(axes.flat, valik9.itertuples()):
    g = p5[(p5["mp"] == r.mp) & (p5["direction_id"] == r.direction_id)]
    ax.scatter(g.loc[~g["seisak"], "hoivatus_%"], g.loc[~g["seisak"], "vool"], s=6, color=C_BLUE, alpha=0.3, lw=0)
    ax.scatter(g.loc[g["seisak"], "hoivatus_%"], g.loc[g["seisak"], "vool"], s=12, color=C_RED, alpha=0.8, lw=0)
    tc = p9[(p9["mp"] == r.mp) & (p9["direction_id"] == r.direction_id)]
    ax.axhline(X_LAHEDAL * (tc["taistase"] / tc["radu"]).median(), color=TEXT2, lw=0.8, ls="--")   # täistase raja kohta
    ax.set_title(f"{r.mp} {short_name(r.manoeuvre, 34)}\nseisakuaknaid {r.seisakuaknaid} / {r.aknaid}", fontsize=9)
    ax.set_xlim(0, g["hoivatus_%"].quantile(0.999) * 1.05)
    ax.set_ylim(0, None)
for ax in axes.flat[len(valik9):]:
    ax.axis("off")
axes.flat[0].legend(handles=[plt.Line2D([], [], marker="o", ls="", color=C_BLUE, label="muu aeg"),
                             plt.Line2D([], [], marker="o", ls="", color=C_RED, label="seisak (üle poole akna ajast)"),
                             plt.Line2D([], [], color=TEXT2, lw=0.8, ls="--", label=f"{X_LAHEDAL:.0%} täistasemest")],
                    loc="upper left", fontsize=8)
fig.supxlabel("Hõivatus raja kohta, % (5 min aken)", color=TEXT2)
fig.supylabel("Sagedus, sõidukit tunnis raja kohta", color=TEXT2)
fig.suptitle(f"Põhidiagramm manöövri kaupa: sagedus ja hõivatus (punkt = 5 min, {PAEVI} tööpäeva)", x=0.01, ha="left",
             fontweight="bold")
save(fig, "10_11_pohidiagramm")
r = valik9.iloc[0]                                              # 10_11b, 10_14: sama sagedus kahes olekus
g = p5[(p5["mp"] == r.mp) & (p5["direction_id"] == r.direction_id)]
s9 = g[g["seisak"]]
lo, hi = s9["vool"].quantile([0.25, 0.75])
H_UMMIK = K_UMMIK * SOIDUK_M / 10                               # ummikutihedus hõivatusena, %


def kaks_olekut(ax, teooria):
    """Manöövri r 5 min aknad, seisakute tavaline sagedus halli vööndina. teooria = lisaks tiheduse telg ja kolmnurkne
    põhidiagramm; x-telg ulatub siis ummikutiheduseni, et ummikuharu jõuaks teljeni pildi sees."""
    ax.axhspan(lo, hi, color=C_GRAY, alpha=0.15, lw=0)
    ax.scatter(g.loc[~g["seisak"], "hoivatus_%"], g.loc[~g["seisak"], "vool"], s=8, color=C_BLUE, alpha=0.35, lw=0,
               label="muu aeg")
    ax.scatter(s9["hoivatus_%"], s9["vool"], s=14, color=C_RED, alpha=0.8, lw=0, label="seisak")
    if teooria:
        ax.plot([0, r.kriitiline_hoivatus_pct, H_UMMIK], [0, r.vool_q99, 0], color=TEXT2, lw=1.2, ls="--",
                label=f"kolmnurkne põhidiagramm: tipp =\nraja läbilaskevõime, sagedus 0\ntihedusel {K_UMMIK} sõidukit "
                      "km kohta")
        ax.secondary_xaxis("top", functions=(lambda h: h * 10 / SOIDUK_M, lambda k: k * SOIDUK_M / 10)).set_xlabel(
            f"Tihedus, sõidukit km kohta\n(hõivatus / sõiduki pikkus {SOIDUK_M} m)", color=TEXT2)
    for i, (d, col, nimi) in enumerate([(g[~g["seisak"] & g["vool"].between(lo, hi)], C_BLUE, "vaba vool"),
                                        (s9[s9["vool"].between(lo, hi)], C_RED, "seisak")]):
        if len(d):
            m, kw = d["hoivatus_%"].median(), dict(fontsize=9, color=col, fontweight="bold")
            if teooria:                 # punktid on pildi vasakus kolmandikus: sildid halli vööndi tühja ossa
                ax.text(H_UMMIK, hi - (0.28 + 0.44 * i) * (hi - lo), f"{nimi}: hõivatus {m:.0f}%", ha="right",
                        va="center", **kw)
            else:                       # sildid punktipilve kohal; seisaku silt algab mediaanist, et sildid ei kattuks
                ax.annotate(f"{nimi}: hõivatus {m:.0f}%", (m, hi), xytext=(0, 6), textcoords="offset points",
                            ha=["center", "left"][i], bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none",
                                                                alpha=0.85), **kw)
    ax.set_xlim(0, H_UMMIK * 1.04 if teooria else None)
    ax.set_ylim(0, None)
    ax.set_xlabel("Hõivatus raja kohta, % (5 min aken)")
    ax.set_ylabel("Sagedus, sõidukit tunnis raja kohta")
    ax.legend(fontsize=9, loc="upper right" if teooria else "lower right")


def skeem(ax):
    """Põhidiagrammi skeem (10_13) suhtelistes ühikutes, andmeid ei kasuta."""
    kk, kj, q = 1, 4.5, 0.6                                     # kriitiline ja suurim hõivatus, näitesagedus
    x2 = kj - q * (kj - kk)
    ax.fill_between([kk, kj], 0, X_LAHEDAL, color=C_RED, alpha=0.12, lw=0)
    ax.plot([0, kk], [0, 1], color=C_BLUE)
    ax.plot([kk, kj], [1, 0], color=C_RED)
    ax.axhline(X_LAHEDAL, color=TEXT2, lw=0.8, ls="--")
    ax.axvline(kk, color=TEXT2, lw=0.8, ls=":")
    ax.plot([q * kk, x2], [q, q], color=C_GRAY, lw=0.8)
    ax.scatter([q * kk, x2], [q, q], s=50, color=[C_BLUE, C_RED], edgecolor="white", zorder=3)
    for x, y, tekst, nurk in [(0.3 * kk - 0.05, 0.3, "vaba voolu haru", 1 / kk),  # sildid joone kõrval, mitte peal
                              (kj - 0.3 * (kj - kk), 0.33, "tihe haru", -1 / (kj - kk))]:
        ax.text(x, y, tekst, rotation=np.degrees(np.arctan(nurk)), transform_rotates_text=True,
                rotation_mode="anchor", ha="center", va="bottom", fontsize=9, color=TEXT2)
    ax.annotate("sama sagedus", ((kk + x2) / 2, q), xytext=(0, 4), textcoords="offset points", ha="center",
                fontsize=9, color=TEXT2)
    ax.text(kj - 0.1, X_LAHEDAL - 0.04, f"seisak töö reegli järgi:\nhõivatus vähemalt kriitiline,\nsagedus kuni "
            f"{X_LAHEDAL:.0%} läbilaskevõimest", fontsize=9, color=TEXT2, ha="right", va="top")
    ax.set_xticks([0, kk, kj], ["0", "kriitiline\nhõivatus", "suurim hõivatus\n(liiklus seisab)"])
    ax.text(kj * 1.1, X_LAHEDAL, f"{X_LAHEDAL:.0%} läbilaskevõimest", fontsize=9, color=TEXT2, ha="right",
            va="bottom")                                        # 85% silt joonel pildi sees, mitte teljel
    ax.set_yticks([0, 1], ["0", "läbilaskevõime"])
    plt.setp(ax.get_yticklabels(), rotation=90, va="center")    # püstine nagu teiste paneelide telje tekst
    ax.get_yticklabels()[1].set_va("top")                       # ülemine silt ei ulatu pealkirja alla
    ax.grid(False)
    ax.set_xlim(0, kj * 1.12)                                   # ummikuharu jõuab teljeni pildi sees
    ax.set_ylim(0, 1.1)
    ax.set_xlabel("Hõivatus (võrdeline tihedusega)")
    ax.set_ylabel("Sagedus")


voond = f"hall vöönd = seisakute tavaline sagedus {lo:.0f}–{hi:.0f} sõidukit tunnis raja kohta"
nimi9 = silt.get((r.mp, r.direction_id), r.mp)
fig, ax = plt.subplots(figsize=(9, 6))
kaks_olekut(ax, True)
ax.set_title(f"Sama sagedus kahes olekus: {nimi9}\n({voond})", fontsize=10, loc="left")
fig.tight_layout()
save(fig, "10_11b_kaks_olekut")
fig, ax = plt.subplots(figsize=(8, 5))
skeem(ax)
ax.set_title("Põhidiagrammi skeem ja töö seisakureegel")
fig.tight_layout()
save(fig, "10_13_pohidiagramm_skeem")
fig, axes = plt.subplots(1, 3, figsize=(16, 5.6), layout="constrained")     # 10_14: aknad, skeem ja mõlemad koos
kaks_olekut(axes[0], False)
skeem(axes[1])
kaks_olekut(axes[2], True)
for ax, t in zip(axes, ["Mõõdetud 5 min aknad", "Põhidiagrammi skeem ja töö seisakureegel",
                        "Mõõdetud aknad ja kolmnurkne põhidiagramm"]):
    ax.set_title(t, fontsize=10)
fig.suptitle(f"Sama sagedus kahes olekus ja põhidiagramm: {nimi9}\n({voond})", x=0.01, ha="left", fontweight="bold")
save(fig, "10_14_pohidiagramm_kolmik")

# --- 10) Teisene seisakukontroll järjekorrast (hõivatuse reegel 9 jääb samaks) ----------------------------------------
# Hõivatus näeb ainult loenduril seisvat sõidukit; kes peatub loenduri ees, seda ei tõsta. Järjekorra kestus ja esimese
# sõiduki kiirus ei sõltu sellest, kus järjekord seisis.
z = v[(c["meetod"] == "kindel").values[v["cyc"].values]].sort_values(["mp", "kanal", "life"])
eel = z.groupby(["mp", "kanal"])
z = z.assign(tyhi=z["gap"].where(eel["life"].diff() == 1),
             jargmise_vahe=eel["gap"].shift(-1).where(eel["life"].diff(-1) == -1))    # tühi aeg järgmise sõidukini, s
ots = lambda keep: z.drop_duplicates(["cyc", "kanal"], keep=keep).set_index(["cyc", "kanal"])
rj = (jarjekord(z).join(ots("last")[KEY + ["jargmise_vahe"]])
      .join(ots("first")[["kiirus", "occ", "klass"]].add_prefix("esimese_")).reset_index())
rj["T"] = c["T"].values[rj["cyc"]]
# punane = raja lühim tühi aeg tsüklite vahel (5. protsentiil, sama tsükli pikkus ehk sama foorikava); järjekord kestis
# rohelise lõpuni, kui pärast tsükli viimast sõidukit oli tühja aega kuni ühe järjekorravahe võrra rohkem
rj["punane"] = rj.groupby(["mp", "kanal", "T"])["jargmise_vahe"].transform(
    lambda s: s.quantile(0.05) if s.notna().sum() >= MIN_VAATLUSI else np.nan)
rj["labi_rohelise"] = (rj["k"] == rj["n"]) & (rj["k"] >= 2) & (rj["jargmise_vahe"] <= rj["punane"] + JARJEKORD_VAHE)
cj = c.loc[c["meetod"] == "kindel", KEY + ["paev", "t", "T", "n", "ks", "kn", "taistase"]].join(
    rj.groupby("cyc")["labi_rohelise"].sum().rename("radu_j")).merge(man[KEY + ["radu"]], on=KEY)
cj["jT"] = cj["radu_j"].fillna(0) / cj["radu"] * cj["T"]                   # raja-tsüklite aeg, kui järjekord ei tühjenenud
w = (cj.assign(viis=(cj["t"] // 300).astype(int)).groupby(KEY + ["paev", "viis"])
     .agg(n=("n", "sum"), T=("T", "sum"), jT=("jT", "sum"), ks=("ks", "sum"), kn=("kn", "sum"),
          taistase=("taistase", "median")).reset_index())
w = w[w["T"] >= 240].merge(p5[KEY + ["paev", "viis", "seisak"]], on=KEY + ["paev", "viis"])
w["labilase_%"] = w["n"] * 3600 / w["T"] / w["taistase"] * 100
w["kiirus"] = w["ks"] / w["kn"].where(w["kn"] > 0)                         # kiirusega sõidukite keskmine, km/h
w["jarjekord"] = w["jT"] > w["T"] / 2                                       # üle poole ajast järjekord läbi rohelise
w["seisak_j"] = w["jarjekord"] & (w["labilase_%"] <= X_LAHEDAL * 100)
w["molemad"] = w["seisak"] & w["seisak_j"]
vrd = w.groupby(KEY).agg(aknaid=("seisak", "size"), jarjekord_labi_rohelise=("jarjekord", "sum"),
                         seisak_hoivatus=("seisak", "sum"), seisak_jarjekord=("seisak_j", "sum"), molemad=("molemad", "sum"))
vrd["ainult_hoivatus"] = vrd["seisak_hoivatus"] - vrd["molemad"]
vrd["ainult_jarjekord"] = vrd["seisak_jarjekord"] - vrd["molemad"]
# järjekorra esimene sõiduauto täis tsüklis seisis punase ajal: tema kiirus loenduril näitab, kui kaugelt ta kiirendas
es = rj[rj["labi_rohelise"] & rj["esimese_klass"].eq("SAPA") & ~((rj["esimese_kiirus"] == 0) & (rj["esimese_occ"] < 5))]


def kaugus(g):
    """Esimese sõiduki mediaankiirus loenduril ja sellest peatumiskaugus loenduri ees (KIIRENDUS keskmine ja kvartiilid)."""
    vm = g["esimese_kiirus"].median()
    return pd.Series({"esimesi": len(g), "kiirus_kmh": vm, "loenduril_seisis_%": g["esimese_kiirus"].eq(0).mean() * 100,
                      "peatumiskaugus_m": peatus(vm, KIIRENDUS[0]), "kaugus_min_m": peatus(vm, KIIRENDUS[2]),
                      "kaugus_max_m": peatus(vm, KIIRENDUS[1])})


pk = es.groupby(KEY + ["kanal"]).apply(kaugus)
pk = pk[pk["esimesi"] >= MIN_VAATLUSI]
km = es.groupby(KEY).apply(kaugus)
vrd = vrd.join(km[km["esimesi"] >= MIN_VAATLUSI])
vrd.insert(0, "manoeuvre", man.set_index(KEY)["manoeuvre"].reindex(vrd.index))
save_table(vrd.reset_index().sort_values("seisak_jarjekord", ascending=False).round(1), "10_seisak_jarjekord")
save_table(pk.reset_index().merge(man[KEY + ["manoeuvre"]], on=KEY).round(1), "10_peatumiskaugus")
kok = w[["seisak", "seisak_j", "molemad", "jarjekord"]].sum()
vm = es["esimese_kiirus"].median()
nk = vrd.dropna(subset=["peatumiskaugus_m"]).query("seisak_jarjekord > 0")
rho = nk["peatumiskaugus_m"].corr(nk["ainult_jarjekord"] / nk["seisak_jarjekord"], method="spearman")
print(f"\n10) Teisene seisakukontroll ({len(w):,} kindla tsükliga 5 min akent): järjekord ei tühjenenud üle poole ajast "
      f"{kok.jarjekord} aknas; seisak hõivatusest {kok.seisak}, järjekorrast {kok.seisak_j}, mõlemast {kok.molemad}. "
      f"Täis tsükli esimene sõiduauto läbib loenduri {vm:.0f} km/h ({len(es):,} tsüklit, raja mediaanide kvartiilid "
      f"{pk['kiirus_kmh'].quantile(.25):.0f}–{pk['kiirus_kmh'].quantile(.75):.0f} km/h) -> peatus {peatus(vm, KIIRENDUS[0]):.1f} m "
      f"enne loendurit ({peatus(vm, KIIRENDUS[2]):.1f}–{peatus(vm, KIIRENDUS[1]):.1f} m); loenduril seisis "
      f"{es['esimese_kiirus'].eq(0).mean() * 100:.0f}%. Peatumiskaugus vs hõivatusest puudu jäänud osa: Spearman "
      f"{rho:.2f} ({len(nk)} manöövrit)")
vj = vrd.assign(koik=vrd["seisak_hoivatus"] + vrd["ainult_jarjekord"]).query("koik > 0").nlargest(20, "koik").iloc[::-1]
fig, axes = plt.subplots(1, 2, figsize=(15, 0.3 * len(vj) + 2.6), gridspec_kw=dict(width_ratios=[1.3, 1]))
ax, vasak = axes[0], np.zeros(len(vj))
for veerg, col, nimi in [("molemad", C_RED, "mõlemad reeglid"), ("ainult_hoivatus", C_BLUE, "ainult hõivatusest"),
                         ("ainult_jarjekord", C_ORANGE, "ainult järjekorrast")]:
    ax.barh(range(len(vj)), vj[veerg], left=vasak, color=col, height=0.7, label=nimi, edgecolor="white", lw=1)
    vasak += vj[veerg].values
ax.set_yticks(range(len(vj)))
ax.set_yticklabels([silt.get(k, str(k)) for k in vj.index], fontsize=7.5)
ax.set_xlabel(f"Seisakuaknaid (5 min, {PAEVI} tööpäeva)")
ax.legend(fontsize=8, loc="lower right")
ax.set_title("Seisak kahe reegliga: hõivatus (9) ja järjekord läbi rohelise", fontsize=10)
ax = axes[1]
ax.hist(pk["peatumiskaugus_m"], bins=np.arange(0, pk["peatumiskaugus_m"].quantile(0.98) + 1, 0.5), color=C_ORANGE, alpha=0.85,
        edgecolor="white", lw=1)
for a, ls in zip(KIIRENDUS, ["-", "--", "--"]):
    ax.axvline(peatus(pk["kiirus_kmh"], a).median(), color=TEXT2, lw=1 if ls == "-" else 0.8, ls=ls)
ax.set_xlim(0, None)
ax.set_xlabel(f"Järjekorra esimese sõiduauto peatumiskaugus loenduri ees, m (raja mediaan)\njoon = kiirendusel "
              f"{KIIRENDUS[0]:.2f} m/s², katkendjoon = {KIIRENDUS[2]:.2f} ja {KIIRENDUS[1]:.2f} m/s²".replace(".", ","))
ax.set_ylabel("Radu")
ax.set_title(f"Järjekorra esimene sõiduauto peatub {peatus(vm, KIIRENDUS[0]):.0f} m enne loendurit "
             f"({peatus(vm, KIIRENDUS[2]):.0f}–{peatus(vm, KIIRENDUS[1]):.0f} m; {len(pk)} rada);\nloenduril seisis "
             f"{es['esimese_kiirus'].eq(0).mean() * 100:.0f}% (kiirus loenduril {vm:.0f} km/h)", fontsize=10)
fig.tight_layout()
save(fig, "10_12_seisak_jarjekord")
print("Valmis.")

# --- Lihtsad joonised (<nr>_10yo, vt 47): samad andmed, üks sõnum, suur kiri ------------------------------------------
plt.rcParams.update({"font.size": 13, "axes.titlesize": 15, "axes.labelsize": 13, "xtick.labelsize": 12,
                     "ytick.labelsize": 12})
X_SILT, Y_SILT = "kui palju autosid linnas liigub, % suurimast", "autosid täis ristmikul, %"
fig, ax = plt.subplots(figsize=(10, 5.2))
ax.scatter(kd["labilase_%"], kd["tais_%"], s=10, color=C_GRAY, alpha=0.5, lw=0)
xx = np.array([kd["labilase_%"].min(), x0, kd["labilase_%"].max()])
ax.plot(xx, a0 + b0 * np.clip(xx - x0, 0, None), color=C_ORANGE, lw=3)
ax.axvline(x0, color=C_ORANGE, lw=1.2, ls="--")
ax.text(x0 - 1, kd["tais_%"].max() * 0.9, f"{x0:.0f}%", ha="right", fontsize=15, color=C_ORANGE, fontweight="bold")
ax.set_ylim(0, None)
ax.set_xlabel(X_SILT)
ax.set_ylabel(Y_SILT)
ax.set_title(f"Millal hakkab linn täis saama?\nKuni {x0:.0f}% on ristmikud enamasti vabad, siis täituvad kiiresti",
             loc="left")
save(fig, "10_09_10yo")

fig, ax = plt.subplots(figsize=(10, 5.2))
louna = next((h for h in (12, 13, 11) if h in tj["tund"].values and tj.set_index("tund").notna().at[h, "tous_b"]), 12)
xs = np.linspace(kd["labilase_%"].min(), 100, 60)
for h, col, nimi in [(8, C_BLUE, "hommikul kell 8"), (louna, C_GRAY, f"päeval kell {louna}"), (17, C_ORANGE, "õhtul kell 17")]:
    r_ = tj.set_index("tund").loc[h]
    y_ = np.full_like(xs, r_.tase_a) if np.isnan(r_.tous_b) else np.minimum(r_.tase_a + r_.tous_b * np.clip(xs - x0, 0, None), 100)
    ax.plot(xs, y_, color=col, lw=3)
    ax.text(101, y_[-1], nimi, color=col, fontsize=14, fontweight="bold", va="center")
ax.set_xlim(right=125)
ax.set_ylim(0, None)
ax.set_xlabel(X_SILT)
ax.set_ylabel(Y_SILT)
ax.set_title("Kas hommikul saavad ristmikud kiiremini täis?\nJah: sama liikluse juures on hommikul rohkem autosid täis "
             "ristmikul", loc="left")
save(fig, "10_10_10yo")

fig, ax = plt.subplots(figsize=(10, 5.5))
ax.axhspan(lo, hi, color=C_GRAY, alpha=0.2, lw=0)
ax.scatter(g.loc[~g["seisak"], "hoivatus_%"], g.loc[~g["seisak"], "vool"], s=14, color=C_BLUE, alpha=0.35, lw=0)
ax.scatter(s9["hoivatus_%"], s9["vool"], s=22, color=C_RED, alpha=0.8, lw=0)
mv = g[~g["seisak"] & g["vool"].between(lo, hi)]["hoivatus_%"].median()
ms = s9[s9["vool"].between(lo, hi)]["hoivatus_%"].median()
for m_, col, tekst in [(mv, C_BLUE, "autod sõidavad\nvabalt"), (ms, C_RED, "autod seisavad\njärjekorras")]:
    ax.annotate(tekst, (m_, hi), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=14, color=col,
                fontweight="bold", bbox=dict(fc="white", ec="none", alpha=0.85))
ax.set_ylim(0, g["vool"].max() * 1.3)
ax.set_xlim(0, g["hoivatus_%"].quantile(0.999) * 1.05)
ax.set_xlabel("kui suure osa ajast oli loenduri all auto, %")
ax.set_ylabel("autosid tunnis")
ax.set_title(f"Sama palju autosid, kaks eri olukorda (hall triip)\n{nimi9}", loc="left")
save(fig, "10_11b_10yo")

fig, ax = plt.subplots(figsize=(10, 5.5))
ax.plot([0, 1], [0, 1], color=C_BLUE, lw=4)
ax.plot([1, 4.5], [1, 0], color=C_RED, lw=4)
ax.scatter([1], [1], s=150, color=TEXT2, zorder=3)
ax.annotate("kõige rohkem autosid\nmahub läbi siin", (1, 1), xytext=(15, 5), textcoords="offset points", fontsize=14,
            color=TEXT2)
ax.text(0.6, 0.25, "tee on vaba:\nautod sõidavad kiiresti", fontsize=14, color=C_BLUE, fontweight="bold")
ax.text(3.0, 0.62, "ummik: autod on tihedalt\nja liiguvad aeglaselt", fontsize=14, color=C_RED, fontweight="bold")
ax.set_xlim(0, 4.9)
ax.set_ylim(0, 1.25)
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel("kui tihedalt autod teel on →")
ax.set_ylabel("mitu autot tunnis läbi sõidab →")
ax.set_title("Kui autosid on liiga palju, sõidab läbi vähem autosid\nSama arvu autosid võib näha nii vabal teel kui "
             "ummikus", loc="left")
save(fig, "10_13_10yo")

d_ = peatus(vm, KIIRENDUS[0])
fig, ax = plt.subplots(figsize=(11, 4))
ax.axhspan(-1, 1, color="#d9d8d3", lw=0)
ax.axvline(0, color=C_RED, lw=4)
ax.text(0, 1.15, "loendur (radar)\nja foor", ha="center", va="bottom", fontsize=13, color=TEXT2)
ax.add_patch(plt.Rectangle((-d_ - 4.5, -0.45), 4.5, 0.9, color=C_BLUE))
ax.annotate("", (-0.3, -0.75), (-d_, -0.75), arrowprops=dict(arrowstyle="<->", color=TEXT, lw=1.5))
ax.text(-d_ / 2, -0.95, f"umbes {d_:.0f} m", ha="center", va="top", fontsize=14, color=TEXT)
ax.text(-d_ - 2.25, 0.6, "esimene auto", ha="center", va="bottom", fontsize=13, color=C_BLUE)
ax.set_xlim(-d_ - 12, 6)
ax.set_ylim(-1.8, 2.3)
ax.axis("off")
ax.set_title(f"Kus seisab järjekorra esimene auto punase tule ajal?\nUmbes {d_:.0f} m enne loendurit. Rohelise tulega "
             f"jõuab ta loendurini juba {vm:.0f} km/h kiirusega", loc="left")
save(fig, "10_12_10yo")
