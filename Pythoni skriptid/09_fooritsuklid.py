"""
09 - Fooritsüklid, ummikud ja seisakud sõidukipõhistest loendustest: mitu sõidukit läbib manöövri igas fooritsüklis,
millal on tsükkel täis (ummik), millal läbilase langeb, sest liiklus seisab (seisak), millal ummik laheneb ning kui
palju kiirust ja aega võidab 15/30/45/60 min enne ummiku algust või pärast selle lõppu sõites. Vaba vooluga radadel
(fooritsüklit pole) on ummik kiiruse langus.

SISEND
  common.load_vehicles(None)   kõik sõidukipõhised kirjed (tallinn.vehicle_passage): ristmik, kanal,
                                          aeg, kiirus ja loenduril oldud aeg (occ) iga sõiduki kohta; logija nädal
                                          16.-22.10.2026
  common.load_manoeuvres()                kanal -> manööver (T08 "Suund"), nt "Tulika VS → PP Endla LVS"
  common.ristmike_harud()                 lähteharu lubatud suurim kiirus (OSM maxspeed; märketa 50 km/h)
  Kasutatakse kellaaega 05-21. Kõik künnised on koodi alguses seadetena.

ARVUTUS
  Tsüklid (veerg "meetod")
  1) "kindel" - kindel fooritsükkel. Fooriandmeid loendustes pole, aga enamik foore töötab täissekundilise kindla
     tsükliga, mis vahetub kellaaja järgi (nt 60/90/72 s). Iga manöövri iga 30 min ploki sõidukite ajad volditakse
     (t mod T) iga T = 40...180 s jaoks; õige T annab kõige ebaühtlasema jaotuse (kontrast). Valik tehakse ristmikul
     tegelikult kasutatavate tsüklite seast (>= 2% häältest; +-2 s naabritest suurim). Punane = volditud jaotuse
     vaikseim 10 s aken; tsükli piir on selle keskel, seega jääb iga roheline tervikuna ühte tsüklisse. Kui vaikseimas
     aknas on üle 30% ühtlase liikluse mahust, kindlat tsüklit pole.
  2) "paus" - adaptiivne foor (tsükli pikkus muutub). Kui punase pausid on selged - pausi (>= 8 s vahe kõigil manöövri
     radadel) mediaanpikkus tihedaimal 2 tunnil on vähemalt 4x see, mida annaks sama tihe juhuslik liiklus -, on
     tsükkel pausist pausini (30...240 s).
  3) "vaba" - vaba vool (Laagna tee, viaduktid, vabad parempöörded jm): 60 s aknad. Oma foorita kanalid
     (ILMA_FOORITA, autori kohapealne kontroll) on alati vaba vool: nende liiklus võib saabuda ülesvoolu fooride tsükliga.
     Oma fooriga kanalid, mille punane andmetes ei paista (FOORIGA), saavad vaba voolu asemel kindla tsükli.
  Kontroll (09_07b): kontrast = volditud jaotuse hajuvus / keskmine, juhuslikul liiklusel ~1. Tegeliku ploki suurimat
     kontrasti võrreldakse sama arvu juhuslike aegadega samas plokis; sama ristmiku manöövrid (üks kontroller) peavad
     samas plokis leidma sama T sagedamini kui eri ristmike manöövrid.
  Andmed: ainult ristmiku terved päevad (kõik pordid kaetud 05-23, common.tervetel_paevadel).
  Ummik fooriga manöövril (kindel, paus; common.ummikumask). Läbilase = sõidukit tunnis (n x 3600 / T, võrreldav ka
     foorikava vahetumisel), silutud 5 tsükli liikuva mediaaniga. Silumine, ummik ja seisak ei ulatu üle augu: kui
     eelmise tsükli lõpust järgmise alguseni on üle 60 s (puuduv 30 min plokk, eemaldatud pikk tsükkel), algab uus
     lõik (veerg loik); lühem vahe (nt eemaldatud lühike üleminekutsükkel) lõiku ei katkesta. Täistase = selle
     tipuakna (hommik 06-11, õhtu 14-20) suurim väärtus (päevade mediaan) ehk vaadeldud läbilaskevõime. Ummik = silutud
     läbilase on üle 85% täistasemest: HCM 2000 järgi on koormusaste X = v/c üle 0,85 läbilaskevõime lähedal ja kuni
     0,85 alla läbilaskevõime (lk 10-46, Exhibit A10-9). Kuni 2 andmepunkti (tsükli) pikkune vahe kahe ummikulõigu
     vahel loetakse sisse (nagu seisakulõikudel). Tipuakna ummik = lõik, mis
     katab akent kõige rohkem (võib ulatuda aknast välja); lahenemine = esimene tsükkel pärast seda.
     Kiirustest "lõigu keskmine kiirus on alla manöövri keskmise" on seadena olemas (KIIRUSTEST), kuid vaikimisi
     väljas: loendurid on stoppjoonel, kus täis tsüklis ületab järjekord loenduri hooga ja kiirus on pigem veidi üle
     päeva keskmise (testi järel kaoks ka selgeimaid platoosid) - kiirus ei
     erista seal ummikut.
     "Stabiilne" = ummik kestab vähemalt HCM-i analüüsiperioodi 15 min (HCM 2000 lk 2-3); kindla tsükliga lisaks on
     sõidukite arv tsüklis ühtlane: hajuvus/keskmine on kuni 0,41 ehk nii palju, kui HCM 2000 annab foori taga
     koormusastmel 0,85 (lk 15-8, Exhibit 15-7: I = 1 - 0,91 X^2,68; juhuslikul liiklusel 1). Adaptiivsel fooril muutub
     tsükli pikkus koos nõudlusega, seal hajuvust ei kontrollita.
  Ummik vabal voolul: silutud kiirus <= 70% vabast kiirusest (manöövri silutud kiiruse 85. protsentiil). HCM 2000 järgi
     on kiirus läbilaskevõimel 72-97% vabast kiirusest (lk 13-4, 21-3), seega alla 70% on liiklus põhidiagrammi aeglasel
     ja tihedal harul (teenindustase F, lk 7-6; Knoop lk 21-22). Algus = kiirus
     langeb, lahenemine = kiirus taastub; "stabiilne" = kestab >= 15 min (HCM 2000 lk 2-3).
  Seisak või roomav liiklus (seisakumask; kõik meetodid) - ummikuaeg, mil läbilase on VÄIKE, sest sõidukid seisavad:
     hõivatus H = tsükli sõidukite loenduril oldud aegade summa / (tsükli pikkus x radade arv) ehk osa ajast, mil loendur
                  on sõidukiga kaetud (tiheduse mõõt; ühe sõiduki aeg arvesse kuni 60 s), silutud 5 tsükli mediaaniga
     H_täis     = sama manöövri silutud hõivatuse mediaan täistaseme tsüklites (läbilase > 85% täistasemest), sama
                  poolpäev (enne või pärast 12:30): hõivatus läbilaskevõimel ehk kriitiline hõivatus
     seisak     = läbilase <= 85% täistasemest  JA  H >= max(H_täis, 10%)
     Põhidiagrammi järgi on liiklus ülekoormatud, kui tihedus on üle kriitilise (Knoop lk 21-22): loendur on kaetud
     vähemalt sama palju kui läbilaskevõimel, aga läbi pääseb vähem - sõidukid roomavad või seisavad loenduril (nt
     väljasõit on kinni). 10% = kriitilise tiheduse alampiir 20 sõidukit km raja kohta x sõiduki pikkus 5 m (Knoop
     lk 21-22; hõivatus = tihedus x pikkus, lk 5, valem 1.4). Kui liiklust on lihtsalt vähe, on väike ka hõivatus ja tsükkel ei ole seisak.
     Lõik = järjestikused seisakutsüklid (kuni 2 tsükli pikkune vahe loetakse sisse), arvesse alates 15 minutist (HCM-i analüüsiperiood); "tipp"
     näitab, kas lõik jääb tavalisele ummikuajale (hommik 06-11, õhtu 14-20). Koormatud aeg = ummik ja seisak kokku
     (järjestikused tsüklid, mis on üks või teine): nii kaua kestab häiritud liiklus tegelikult. Aeglane sõiduk =
     kiirus alla 65% lähteharu lubatud suurimast kiirusest (CREATE D3.4 lk 57: ummik = kiirus alla 65% piirkiirusest;
     65% on ametkondade 50-75% vahemiku keskpunkt, lk 24). Seisev sõiduk = kiirus alla 15 km/h (CREATE D3.4 lk 32:
     jalgratta ja linnabussi tavaline kiirus, "väga aeglane") või seisis loenduril (kiirus 0, loenduril >= 5 s).
     Lubatud kiirus: OSM maxspeed haru tänaval, märketa 50 km/h (Liiklusseadus § 15 lg 1 p 2), common.ristmike_harud.
     NB! CREATE künnised on lõigu sõidukiirusele (GPS); loendur mõõdab punktkiirust stoppjoonel, kus ka vaba tsükli
     järjekorrast startiv sõiduk on aeglane, seega on osakaal ka seisakuta tsüklites suur ja loeb võrdlus.
  Kiirus ummiku ümber: 15 min aknad 0-15, 15-30, 30-45, 45-60 min enne ummiku algust ja pärast lõppu (nihe -15 = 0-15
     min enne, +15 = 0-15 min pärast jne). Kiiruse võit = akna keskmine kiirus - kiirus ummikus. Ajavõit sõiduki
     kohta = 3600/kiirus ummikus - 3600/kiirus aknas (s/km); tsükli kohta = x sõidukeid täis tsüklis. Kiirused on
     punktkiiruste keskmised ja keskmise kiiruse pöördväärtus ei ole keskmine sõiduaeg, seega on ajavõit hinnang.
  Seisakuminutid päevas (09_manoovrid) = manöövri seisakuminutid / manöövri enda mõõdetud tööpäevade arv.
  ponytail: kiirus on loenduri punktkiirus (mitte sõiduaeg) ja "täis" tuletatakse ainult loendusest; täpsem oleks
  rohelise lõpuni kestev küllastusvoog või foorikavad.

CALCULATION IN PLAIN ENGLISH
  Only junction-days on which every port of the junction was recorded 05-23.
  Cycles: the vehicle times of a movement are folded by each candidate cycle length T = 40-180 s (time modulo T); the T
    with the most uneven folded pattern is the fixed signal cycle. Adaptive signals: a cycle runs from one red pause (a
    gap of at least 8 s on all lanes) to the next. Free-flow lanes: 60-second windows. Channels without their own
    signal (ILMA_FOORITA, the author's site check) are always free flow: they may arrive in the upstream signals' cycle.
  Check (09_07b): contrast = variance / mean of the folded pattern, about 1 for random traffic. Each block's highest
    contrast is compared with random times (same vehicle count, same block); movements of one junction (one
    controller) should find the same cycle in a block more often than movements of different junctions.
  Throughput = vehicles in the cycle x 3600 / cycle length (vehicles per hour), smoothed by the median of 5 cycles in a
    row; more than 60 s between the end of one cycle and the start of the next starts a new stretch, and neither the
    smoothing nor a congestion or stoppage episode crosses it (a shorter gap, e.g. a removed short cycle, does not).
  Full level = the largest smoothed throughput in the peak window (morning 06-11, evening 14-20), median over days.
  Congestion (signal) = smoothed throughput above 85% of full level (HCM 2000: v/c above 0.85 = near capacity); a gap
    of up to 2 cycles between two congested stretches is bridged. Free flow: congestion = smoothed speed <= 70% of free
    speed (85th percentile of smoothed speed); HCM 2000 puts the speed at capacity at 72-97% of free speed.
  Occupancy H = time vehicles spent on the detector in the cycle (each at most 60 s) / (cycle length x lanes).
    Stoppage = throughput <= 85% of full level AND H >= max(H at full level, 10%), stretches of at least 15 minutes (the HCM analysis period)
    (10% = lowest critical density 20 veh/km/lane x 5 m vehicle, Knoop).
    Stoppage minutes per day = the movement's stoppage minutes / the movement's own measured workdays.
    Slow vehicle = speed below 65% of the approach leg's speed limit (CREATE D3.4 p. 57); standing vehicle = below
    15 km/h (CREATE D3.4 p. 32) or stood on the detector. Speed limit = OSM maxspeed, 50 km/h where untagged (Traffic
    Act § 15(1)2). CREATE uses link travel speeds; at the stop line even a free cycle's queue starts slowly.
  Around congestion: speed gain = average speed in a 15-minute window before or after - speed in congestion; time gain
    per vehicle = 3600 / congestion speed - 3600 / window speed (s per km). Speeds are averages of point speeds at the
    stop line, so the time gain is an estimate, not a measured travel time.

VÄLJUND (joonised kaustas Graafikud/, tabelid kaustas valjund/)
  09_01_naited.png (kindel tsükkel), 09_02_naited_adaptiivne.png (adaptiivne foor)
      Näitab: kuni kuue manöövri pikimat stabiilset tööpäeva-ummikut - kuidas sõidukite arv tsüklis tõuseb täistasemele,
      püsib seal ja langeb.
      Kuidas: paneel manöövri kohta; x-telg = kellaaeg (1,5 h enne ummikut kuni 1,5 h pärast). Vasak y-telg = sõidukeid
      tsüklis: hallid punktid = iga tsükkel, sinine joon = 5 tsükli liikuv mediaan; sinine katkendjoon = 85%
      täistasemest (ainult kindla tsükliga). Parem y-telg = kiirus, km/h: oranž joon = silutud kiirus,
      oranž katkendjoon = manöövri keskmine kiirus. Tume hall vöönd = tipuakna ummik, hele hall = muud ummikulõigud,
      punane = seisak. Pealkirjas ristmik, manööver, päev, sõidukeid tsüklis ummiku ajal, tsükli pikkus ja ummiku
      kellaajad.
  09_01b_ummik_naide.png
      Näitab: üks 09_01 paneel (pikim kindla tsükliga stabiilne ummik): ummik = 5 tsükli mediaan üle 85% täistasemest.
  09_03_seisakud.png
      Näitab: kuni kaheksa manöövri pikimat tipuaegset seisakut - läbilase ja kiirus langevad koos, kuigi on ummikuaeg.
      Kuidas: nagu 09_01_naited (paneel manöövri kohta, 1,5 h enne ja pärast); punane vöönd = seisak või roomav liiklus,
      hall = ummik täistasemel. Pealkirjas seisaku kellaajad ja kestus, läbilase % täistasemest, kiirus seisaku
      ajal ja manöövri keskmine kiirus ning aeglaste (alla 65% lubatud kiirusest) ja seisvate (alla 15 km/h) osakaal.
  09_03b_pikim_seisak.png
      Näitab: 09_03 esimene paneel eraldi (pikim tipuaegne seisak).
  09_04_loendurid/MPxx_AAAA-KK-PP.png (üks fail iga ristmiku ja päeva kohta)
      Näitab: ühe ristmiku kõiki manöövreid terve päeva jooksul (kell 5-21).
      Kuidas: paneel manöövri kohta, sama kujundus kui 09_01_naited (vabal voolul vasakul teljel sõidukeid minutis ja oranž
      punktiir = ummiku kiiruslävi). Paneeli pealkirjas manööver, meetod, radade arv ning minutid ummikus ja seisakus.
      Välja lülitamine (kiirem käivitus): RISTMIKU_JOONISED = False.
  09_05_vaba_vool.png
      Näitab: kümne suurima vaba vooluga manöövri liiklust ja kiirust päeva jooksul.
      Kuidas: paneel manöövri kohta; x-telg = kellaaeg 5-21. Sinine = sõidukeid minutis (tööpäevade mediaan), oranž
      peen joon = iga päeva kiirus, oranž jäme = päevade mediaan (5 min liikuv mediaan); katkendjoon = 70% vabast
      kiirusest; hall vöönd = ummik (mediaankiirus alla selle vähemalt 15 min).
  09_06_kiirus_ummiku_umber.png
      Näitab: kui palju kiirem on liiklus vahetult enne ummikut ja pärast seda.
      Kuidas: rida rühma kohta (foor, vaba vool); vasakul kiiruse võit võrreldes ummikuga (km/h), paremal ajavõit
      sõiduki kohta (s/km). x-telg = 15 min aknad: 45-60 ... 0-15 min enne ummiku algust | 0-15 ... 45-60 min pärast
      lahenemist; hall püstriba = ummik. Punkt = stabiilsete tööpäeva-ummikute mediaan, vurrud = kvartiilid; sinine =
      hommik, oranž = õhtu, hall = terve päeva ummik.
  09_07_tsukli_tuvastus.png
      Näitab: kuidas kindla tsükli pikkus leitakse (voltimine), ühe näiteploki peal.
      Kuidas: tüüpiline tipuaja plokk (7-9, kontrasti mediaanile lähim) lõigatakse ridadeks pikkusega a) T + 7 s (vale)
      ja b) T (õige); rida = üks tsükkel, kriips = üks sõiduk, x = aeg tsükli algusest (tsükli piir on vaikseima 10 s
      akna keskel). Õige T korral on sõidukid igas reas samas kohas (roheline) ja mõlemal pool on tühi (punane), vale
      T korral nihkuvad sõidukid reast reale.
  09_07b_tsukli_kontroll.png
      Näitab: et kindla tsükli otsing leiab tegeliku foori tsükli (fooriprogramme töös pole, seega kontroll andmetest).
      Kuidas: a) kahe manöövri iseseisvalt leitud T samas 30 min plokis: sinine = sama ristmiku manöövrid (üks
      kontroller), hall = eri ristmikud; sama, +-1-2 s, kordne (2x, 3x +-2 s) või muu. b) plokkide suurim kontrast:
      sinine = tegelikud kindla tsükliga plokid (3000 juhuvalimit), hall = sama arv juhuslikke aegu samas plokis,
      katkendjoon = juhusliku 99. protsentiil; x logaritmiline.
  09_tsukli_kontroll.csv    09_07b arvud: näiteplokk, kontrastide mediaanid, osakaal üle juhusliku 99. protsentiili,
                            manöövripaaride tsüklite võrdlus (sama ristmik, eri ristmikud)
  09_tsuklid.csv            iga tsükkel või aken: algus, pikkus T, lõigu number loik (päeva sees; uus lõik pärast üle 60 s
                            auku), sõidukeid n, kiirus, täistase, kas ummikus, hõivatus, kas seisak
  09_manoovrid.csv          manöövri meetod, selguse näitajad, keskmine ja vaba kiirus, radade arv, tippude mediaanid,
                            seisakupäevade arv ja seisakuminutid tööpäeva kohta (tipuaegadel)
  09_seisakud.csv           iga seisakulõik: algus, lõpp, kestus, läbilase % täistasemest, hõivatus ja täistaseme
                            hõivatus, kiirus, aeglaste (alla 65% piirkiirusest) ja seisvate (alla 15 km/h) sõidukite
                            osakaal ning ümbritsev koormatud aeg (ummik + seisak)
  09_ummikud.csv            iga ummik (manööver x päev x tipp): algus, lahenemine, kestus, tsüklite arv, sõidukeid täis
                            tsüklis, täistase, hajuvus, stabiilsus, kiirus ummikus
  09_ummiku_umber.csv       kiirus ja ajavõit igas 15 min aknas ummiku ümber
  09_nihked_kokkuvote.csv   eelmise mediaanid ja kvartiilid rühma, tipu ja nihke kaupa
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import (tervetel_paevadel, load_vehicles, save, save_table, set_style, short_name, slot_label, hhmm, loigud, ummiku_loik, ummikumask,
                    seisakumask, X_LAHEDAL, KIIRUS_YLE, H_KRIITILINE_MIN,
                    load_manoeuvres, ristmike_harud, haru, LINNA_KIIRUS, C_BLUE, C_ORANGE, C_GRAY, C_RED, C_GREEN, TEXT2)

# --- Seaded (kalibreeritavad) --------------------------------------------------------------------------
TS = np.arange(40, 181)          # võimalikud kindla tsükli pikkused, s
BLOKK = 1800                     # tsükkel ja punase asukoht leitakse 30 min plokkide kaupa
KELL = (5, 21)                   # analüüsitav kellaaeg
MIN_N = 30                       # plokis vähemalt nii palju sõidukeid, muidu tsüklit ei otsita
W = 10                           # punase otsimise akna laius, s
HAALI = 0.02                     # tsükli pikkus on ristmikul kasutusel, kui see saab >= 2% (sõidukitega kaalutud) häältest
SELGUS_MAX = 0.3                 # vaikseima akna liiklus / ühtlase liikluse korral oodatav; suurem = kindlat tsüklit pole
PAUS = 8                         # adaptiivne foor: punane = vähemalt nii pikk vahe kõigil manöövri radadel, s
PAUS_E = 4                       # pausi mediaan (üle PAUS) >= 4x juhusliku liikluse ootus -> pausid on punased
TSUKKEL_PIIR = (30, 240)         # pausidest leitud tsükli lubatud pikkus, s
VABA_AKEN = 60                   # vaba voolu akna pikkus, s
VABA_KIIRUS = KIIRUS_YLE         # vaba vool: ummik, kui silutud kiirus <= 70% vabast kiirusest (alla kiiruse läbilaskevõimel, HCM)
ALGUS = X_LAHEDAL                # ummikus: silutud läbilase > 85% täistasemest (läbilaskevõime lähedal, HCM 2000 lk 10-46)
VAJUMINE = 2                     # ummiku- ja seisakulõigu sees kuni 2 andmepunkti pikkune vahe loetakse sisse
KIIRUSTEST = False               # True: lõik on ummik ainult siis, kui selle keskmine kiirus < manöövri keskmine kiirus
                                 # (11 künnise tundlikkus arvutatakse alati ilma kiirustestita)
SEISAK_H = H_KRIITILINE_MIN      # seisak: loendur on kaetud >= 10% ajast (kriitiline tihedus, Knoop) ja >= täistasemel
OCC_MAX = 60                     # ühe sõiduki loenduril oldud aeg arvesse kuni 60 s (kinni jäänud loendur ei tohi domineerida)
AEGLANE_PIIR = 0.65              # aeglane sõiduk: kiirus alla 65% lähteharu lubatud kiirusest (CREATE D3.4 lk 57, 24)
SEISEV = 15                      # seisev sõiduk: kiirus alla 15 km/h (CREATE D3.4 lk 32) või seisis loenduril
# stabiilne ummik: sõidukite arvu hajuvus/keskmine tsüklis kuni nii palju, kui HCM 2000 annab foori taga koormusastmel
# X_LAHEDAL (lk 15-8, Exhibit 15-7: I = 1 - 0,91 X^2,68; juhuslikul liiklusel 1)
STABIILNE_D = 1 - 0.91 * X_LAHEDAL ** 2.68
MIN_TSUKLEID = 5                 # 15 min aknas vähemalt nii palju tsükleid, muidu akna kiirust ei arvutata
MIN_KESTUS = 15                  # ummik ja seisak arvesse alates HCM-i analüüsiperioodist 15 min (HCM 2000 lk 2-3)
AUK = 3                          # vaba vool: nii mitu järjestikust kiiremat akent loetakse veel ummiku sisse
KATVUS = 0.8                     # tipuaknast peab tsüklitega kaetud olema vähemalt 80%
TIPUD = {"hommik": (6, 11), "õhtu": (14, 20)}
RISTMIKU_JOONISED = True         # joonis iga ristmiku ja päeva kohta (kaust 09_04_loendurid/); False = jäta vahele (kiirem)
NIHKED = [15, 30, 45, 60]
MEETOD = {"kindel": "kindel tsükkel", "paus": "adaptiivne foor", "vaba": "vaba vool"}
# Oma foorita kanalid {ristmik: [kanalid]}, autori kohapealne kontroll 19.11.2026 (eraldi parempöörderajad ülekäiguraja
# ja anna-teed-märgiga, pöörde lõpu loendurid, foorist üle 100 m loendurid): liiklus võib saabuda ülesvoolu fooride
# tsükliga salkadena, kuid oma punast pole -> alati vaba vool ega hääleta ristmiku tsükli pikkuse üle
ILMA_FOORITA = {1: [1, 19], 2: [6, 15], 5: [5, 6], 6: [1], 7: [1, 5], 8: [10, 15], 9: [1, 8],
                10: [6, 10, 14, 18, 19, 20, 21, 22], 11: [1, 2], 12: [6, 7, 8, 13, 14, 26], 15: [14], 18: [1, 3],
                19: [1, 4], 20: [9], 21: [6], 22: [5, 6], 24: [1, 2, 3, 4], 26: [1, 2], 27: [1, 2], 33: [6],
                34: [1, 5], 39: [2], 43: [1, 5, 6, 10], 45: [1, 4, 8, 11], 47: [1]}
# Oma fooriga kanalid, mille punane andmetes selgelt ei paista (sama kontroll): kui andmete järgi on vaba vool, siis
# kindel tsükkel ristmiku tsüklipikkustega (kui ristmikul neid pole, adaptiivne). MP48 kanalid 19, 20 = skeemil A1, A2.
FOORIGA = {12: [24, 25], 20: [6], 21: [1, 2, 3, 4, 5], 23: [3], 48: [19, 20]}

OFS = np.r_[0, np.cumsum(TS)]    # iga T volditud histogrammi algus ühises massiivis
VOTI = ["mp_id", "direction_id"]


def kontrast(t):
    """Iga T kohta volditud (t mod T) 1 s histogrammi hajuvus/keskmine: suur = liiklus kordub perioodiga T."""
    h = np.bincount(((t[:, None] % TS).astype(int) + OFS[:-1]).ravel(), minlength=OFS[-1]).astype(float)
    m = len(t) / TS
    return (np.add.reduceat(h * h, OFS[:-1]) / TS - m * m) / m


def pausitsuklid(t):
    """Tsüklite algused adaptiivsel fooril: esimene sõiduk pärast >= PAUS s pausi. Algus loetakse ainult siis,
    kui eelmisest algusest on möödas lühim tsükkel (hõreda liikluse juhuslikud vahed ei tükelda tsüklit)."""
    st = [t[0]]
    for x in t[1:][np.diff(t) >= PAUS]:
        if x - st[-1] >= TSUKKEL_PIIR[0]:
            st.append(x)
    return np.array(st)


def pausi_selgus(paevad):
    """(Pausi mediaanpikkus - PAUS) / sama tiheda juhusliku liikluse ootus, iga päeva tihedaimal 2 tunnil.
    Juhuslikul liiklusel ~1 (pausid napilt üle läve), fooril palju suurem (paus = punane)."""
    pikad, n = [], 0
    for t in paevad:
        tunnid = np.bincount((t // 3600).astype(int), minlength=25)
        h = int(np.argmax(tunnid[:-1] + tunnid[1:]))
        x = t[(t >= h * 3600) & (t < (h + 2) * 3600)]
        vahed = np.diff(x)
        pikad.append(vahed[vahed >= PAUS])
        n += len(x)
    pikad = np.concatenate(pikad)
    return (np.median(pikad) - PAUS) * n / (7200 * len(paevad)) / np.log(2) if len(pikad) >= 20 else np.nan


# enesekontroll: sünteetiline 90 s tsükkel (roheline 30 s) leitakse üles; pausid; lõigu valik ja augu sulgemine
_r = np.random.default_rng(0)
_t = np.sort(np.concatenate([k * 90 + _r.uniform(5, 35, 12) for k in range(40)]))
assert TS[kontrast(_t).argmax()] == 90 and len(pausitsuklid(_t)) == 40 and pausi_selgus([_t + 3600]) > PAUS_E
assert pausitsuklid(np.array([0, 1, 2, 20, 21, 30, 60, 61.])).tolist() == [0, 30, 60]
assert ummiku_loik([1, 1, 0, 1, 1, 0, 0, 0, 0, 1], 0, 10) == (0, 5) and ummiku_loik([1, 1, 0, 0, 0, 0, 1], 5, 7) == (6, 7)
# ummik: üle 85%; 1 punkti vahe loetakse sisse, 3 punkti vahe katkestab; täpselt 85% ei ole ummik
_q = np.array([50, 70, 86, 90, 60, 90, 70, 70, 70, 90, 85.])
assert ummikumask(_q, 100).tolist() == [0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0]
assert ummikumask(_q, 100, kiirus=np.full(11, 20.), kaal=np.ones(11), v_kesk=30).sum() == 5      # kiirus alla keskmise
assert not ummikumask(_q, 100, kiirus=np.full(11, 40.), kaal=np.ones(11), v_kesk=30).any()       # üle keskmise: pole ummik

set_style()
print("Laen sõidukipõhised loendused...")
v = tervetel_paevadel(load_vehicles(None))      # ristmiku terved päevad (kõik pordid kaetud 05-23)
dm = load_manoeuvres()
dm = dm.assign(mp_id=dm["mp"].str[2:].astype(int), haru=dm["from_leg"].map(lambda s: haru(s)[1]))
dm = dm.rename(columns={"channel": "kanal"}).merge(ristmike_harud()[["mp_id", "haru", "kiirus_piir"]], how="left")
_ilma = sorted((mp, k) for mp, ks in ILMA_FOORITA.items() for k in ks)
VABA_MAN = {(mp, int(d)) for (mp, _), d in                             # KeyError, kui kanalit pole
            dm.set_index(["mp_id", "kanal"]).loc[_ilma, "direction_id"].items()}
_seg = dm[[(m, d) in VABA_MAN and (m, k) not in _ilma for m, d, k in zip(dm["mp_id"], dm["direction_id"], dm["kanal"])]]
assert _seg.empty, f"foorita kanal jagab manöövrit fooriga kanaliga (anna kanalile oma direction_id): {_seg[['mp', 'kanal']].values.tolist()}"
FOORI_MAN = {(mp, int(d)) for (mp, _), d in dm.set_index(["mp_id", "kanal"])
             .loc[sorted((mp, k) for mp, ks in FOORIGA.items() for k in ks), "direction_id"].items()}
assert not FOORI_MAN & VABA_MAN, f"kanal on nii foorita kui ka fooriga: {sorted(FOORI_MAN & VABA_MAN)}"
v = v.merge(dm[VOTI + ["kanal", "kiirus_piir"]], on=["mp_id", "kanal"]).dropna(subset=["direction_id"])
v["direction_id"] = v["direction_id"].astype(int)
v["paev"] = v["ts"].dt.normalize()
v["t"] = (v["ts"] - v["paev"]).dt.total_seconds()
v = v[(v["t"] >= KELL[0] * 3600) & (v["t"] < KELL[1] * 3600)].sort_values(VOTI + ["ts"]).reset_index(drop=True)
v["plokk"] = (v["t"] // BLOKK).astype(int)
print(f"{len(v):,} sõidukit kell {KELL[0]}-{KELL[1]}, {v['paev'].nunique()} päeva, "
      f"{v.groupby(VOTI).ngroups} manöövrit")

T_ARR, KM = v["t"].values, v["kiirus"].values
OCC = v["occ"].clip(upper=OCC_MAX).values                                 # loenduril oldud aeg, s
MOODETUD = ~((v["kiirus"] == 0) & (v["occ"] < 5))      # kiirus 0 lühikese ajaga = kiirus mõõtmata, ei loe
AEGL = ((v["kiirus"] < AEGLANE_PIIR * v["kiirus_piir"].fillna(LINNA_KIIRUS)) & MOODETUD).values   # haruta: 50 km/h
SEIS = ((v["kiirus"] < SEISEV) & MOODETUD).values
grupid = v.groupby(VOTI + ["paev", "plokk"]).indices
paevad = v.groupby(VOTI + ["paev"]).indices


def tabel(mp, did, paev, meetod, st, T, i, kehtiv):
    """Tsüklite tabel: algused st (pikkus T), sõidukid i (T_ARR/KM positsioonid) jaotatud tsüklitesse."""
    k = np.searchsorted(st, T_ARR[i], side="right") - 1
    i = i[k >= 0]
    k, km, m = k[k >= 0], KM[i], len(st)
    return pd.DataFrame({
        "mp_id": mp, "direction_id": did, "paev": paev, "meetod": meetod, "t": st, "T": T,
        "n": np.bincount(k, minlength=m), "ks": np.bincount(k, weights=km, minlength=m),
        "kn": np.bincount(k, weights=km > 0, minlength=m), "occ": np.bincount(k, weights=OCC[i], minlength=m),
        "aegl": np.bincount(k, weights=AEGL[i], minlength=m), "seis": np.bincount(k, weights=SEIS[i], minlength=m)})[kehtiv]


# --- 1) Kindel tsükkel: kontrast iga manöövri-ploki kohta, kandidaadid ristmiku kaupa ------------------
kon = {k: kontrast(T_ARR[i]) for k, i in grupid.items() if len(i) >= MIN_N}
haal = pd.DataFrame([(k[0], TS[c.argmax()], len(grupid[k])) for k, c in kon.items() if k[:2] not in VABA_MAN],
                    columns=["mp_id", "T", "n"])
haal = haal.groupby(["mp_id", "T"])["n"].sum()
haal = haal / haal.groupby("mp_id").transform("sum")
kandidaadid = {}
for mp, g in haal[haal >= HAALI].groupby("mp_id"):
    hea = []                                   # +-2 s naabritest jääb enim hääli saanu (89/91 on 90 müra)
    for T in g.sort_values(ascending=False).index.get_level_values("T"):
        if all(abs(T - x) > 2 for x in hea):
            hea.append(T)
    kandidaadid[mp] = np.array(sorted(hea)) - TS[0]

volt, selg = {}, {}
plokid = pd.DataFrame(list(kon), columns=VOTI + ["paev", "plokk"])
for (mp, did, paev), bl in plokid.groupby(VOTI + ["paev"])["plokk"]:
    if mp not in kandidaadid:
        continue
    cand, algused, idx, eelmine = kandidaadid[mp], [], [], (None, None)
    for b in sorted(bl):
        i = grupid[(mp, did, paev, b)]
        T = int(TS[cand[kon[(mp, did, paev, b)][cand].argmax()]])
        faas = T_ARR[i] % T
        h = np.bincount(faas.astype(int), minlength=T)
        s = np.convolve(np.r_[h, h[:W - 1]], np.ones(W), "valid")      # ringjas W s summa
        vaiksed = np.flatnonzero(s <= s.min() + 1)                     # pika punase sees on võrdseid aknaid palju:
        vastas = np.angle(-np.exp(2j * np.pi * faas / T).sum()) / (2 * np.pi) * T - W / 2   # rohelise raskuskeskme vastas
        p = int(vaiksed[np.abs((vaiksed - vastas + T / 2) % T - T / 2).argmin()])
        if eelmine[0] == T and s[eelmine[1]] <= s.min() + 1:           # sama hea eelmine aken jääb -> ühtlased tsüklid
            p = eelmine[1]
        eelmine = (T, p)
        a = selg.setdefault((mp, did), [0.0, 0.0])
        a[0] += s[p]
        a[1] += len(i) * W / T
        f = p + W / 2                                                  # tsükli piir punase keskel
        st = f + T * np.arange(np.ceil((b * BLOKK - f) / T), np.ceil(((b + 1) * BLOKK - f) / T))
        algused.append(np.c_[st, np.full(len(st), T)])
        idx.append(i)
    st = np.vstack(algused)                                            # üleminekutsüklid (kava vahetus, auk) välja
    volt[(mp, did, paev)] = tabel(mp, did, paev, "kindel", st[:, 0], st[:, 1], np.concatenate(idx),
                                  np.abs(np.diff(st[:, 0], append=np.inf) - st[:, 1]) <= 0.25 * st[:, 1])

# --- 2) Meetod manöövri kaupa; adaptiivse foori ja vaba voolu tsüklid ------------------------------------
man = dm.drop_duplicates(VOTI).set_index(VOTI)[["mp", "intersection", "manoeuvre"]]
man = man.join(v.groupby(VOTI).size().rename("soidukeid"), how="inner")
man["kiirus_keskmine"] = v[v["kiirus"] > 0].groupby(VOTI)["kiirus"].mean()
man["radu"] = v.groupby(VOTI)["kanal"].nunique()
man["selgus"] = pd.Series({k: a / b for k, (a, b) in selg.items()}).rename_axis(VOTI)
paevad_m = {}
for (mp, did, paev), i in paevad.items():
    paevad_m.setdefault((mp, did), []).append(T_ARR[i])
man["pausi_selgus"] = pd.Series({k: pausi_selgus(x) for k, x in paevad_m.items()}).rename_axis(VOTI)
man["meetod"] = np.select([man["selgus"] <= SELGUS_MAX, man["pausi_selgus"] >= PAUS_E], ["kindel", "paus"], "vaba")
man.loc[man.index.isin(list(VABA_MAN)), "meetod"] = "vaba"
_sund = man.index.isin(list(FOORI_MAN)) & (man["meetod"] == "vaba")      # foor on, kuigi punane andmetes ei paista
man.loc[_sund, "meetod"] = ["kindel" if mp in kandidaadid else "paus" for mp, _ in man.index[_sund]]

osad = []
for (mp, did, paev), i in paevad.items():
    meetod = man.at[(mp, did), "meetod"]
    if meetod == "kindel":
        osad.append(volt.get((mp, did, paev)))
    elif meetod == "paus":
        st = pausitsuklid(T_ARR[i])
        T = np.diff(st, append=np.inf)
        osad.append(tabel(mp, did, paev, meetod, st, T, i, T <= TSUKKEL_PIIR[1]))
    else:
        st = np.arange(KELL[0] * 3600, KELL[1] * 3600, VABA_AKEN, dtype=float)
        osad.append(tabel(mp, did, paev, meetod, st, float(VABA_AKEN), i, slice(None)))
c = pd.concat(osad, ignore_index=True)
c["kiirus"] = c["ks"] / c["kn"].where(c["kn"] > 0)
c["q"] = c["n"] * 3600 / c["T"]                                        # läbilase, sõidukit tunnis
sile = lambda s: s.rolling(5, center=True, min_periods=3).median()
# järjestikused tsüklid ühes lõigus; auk (eemaldatud tsükkel või andmelünk üle 60 s) alustab uue lõigu, et silumine ega
# ummik ei ulatuks üle mõõtmata aja
c["loik"] = (c["t"] - c.groupby(VOTI + ["paev"])["t"].shift() - c.groupby(VOTI + ["paev"])["T"].shift()).gt(60) \
    .groupby([c[k] for k in VOTI + ["paev"]]).cumsum()
c["sile"] = c.groupby(VOTI + ["paev", "loik"])["q"].transform(sile)
c["kiirus_sile"] = c.groupby(VOTI + ["paev", "loik"])["kiirus"].transform(sile)
# hõivatus: osa tsükli ajast, mil loendur on sõidukiga kaetud (raja kohta) - tiheduse mõõt
c["hoivatus"] = c["occ"] / (c["T"] * man["radu"].reindex(pd.MultiIndex.from_frame(c[VOTI])).values)
c["hoivatus_sile"] = c.groupby(VOTI + ["paev", "loik"])["hoivatus"].transform(sile)
c["tyyp"] = np.where(c["paev"].dt.dayofweek < 5, "tööpäev", "nädalavahetus")
man["vaba_kiirus"] = c[c["meetod"] == "vaba"].groupby(VOTI)["kiirus_sile"].quantile(0.85)
for tipp, (a, b) in TIPUD.items():
    man[f"{tipp}_T"] = c[(c["t"] >= a * 3600) & (c["t"] < b * 3600)].groupby(VOTI)["T"].median().round()
print("Ristmike kindlad tsüklid (s):", "; ".join(
    f"MP{mp:02d} {'/'.join(map(str, TS[k]))}" for mp, k in kandidaadid.items()
    if (man.loc[mp, "meetod"] == "kindel").any()))
for m, g in man.groupby("meetod"):
    print(f"  {MEETOD[m]}: {len(g)} manöövrit, {g['soidukeid'].sum() / man['soidukeid'].sum() * 100:.0f}% sõidukitest")

# --- 3) Täistase ja ummik tipuakna kaupa ------------------------------------------------------------------
c["tipp"] = np.select([(c["t"] >= a * 3600) & (c["t"] < b * 3600) for a, b in TIPUD.values()], list(TIPUD), "")
aken = c[c["tipp"] != ""].groupby(VOTI + ["tyyp", "tipp", "paev"]).agg(C=("sile", "max"), kaetud=("T", "sum"))
kestus = aken.index.get_level_values("tipp").map(lambda x: (TIPUD[x][1] - TIPUD[x][0]) * 3600)
aken = aken[aken["kaetud"] >= KATVUS * kestus]
tase = aken.groupby(VOTI + ["tyyp", "tipp"])["C"].median()

# iga tsükli olek (10 kasutab): fooril ummikus = common.ummikumask oma poolpäeva tipu täistaseme järgi (enne 12:30
# hommikune, pärast õhtune); vabal voolul ummikus = silutud kiirus <= 70% vabast kiirusest
c["pool"] = np.where(c["t"] < 12.5 * 3600, *TIPUD)
c = c.merge(tase.rename("taistase").reset_index().rename(columns={"tipp": "pool"}), on=VOTI + ["tyyp", "pool"], how="left")
c = c.merge(man[["vaba_kiirus"]], left_on=VOTI, right_index=True, how="left")
ummikus = (c["kiirus_sile"] <= VABA_KIIRUS * c["vaba_kiirus"]).to_numpy(copy=True)
for (mp, did, paev, _), ix in c.groupby(VOTI + ["paev", "loik"]).indices.items():      # ummik ei ulatu üle augu
    if c["meetod"].values[ix[0]] != "vaba":
        ummikus[ix] = ummikumask(c["sile"].values[ix], c["taistase"].values[ix], ALGUS, VAJUMINE, c["kiirus"].values[ix],
                                 c["kn"].values[ix], man.at[(mp, did), "kiirus_keskmine"] if KIIRUSTEST else None)
c["ummikus"] = ummikus
# seisak või roomav liiklus (common.seisakumask): hõivatus vähemalt nagu sama manöövri täistaseme tsüklites (läbilase
# > 85% täistasemest, sama poolpäev), aga läbilase kuni 85% täistasemest. Kehtib kõigi meetodite kohta.
tais = c[c["sile"] > ALGUS * c["taistase"]].groupby(VOTI + ["tyyp", "pool"])["hoivatus_sile"].median().rename("hoivatus_tais")
c = c.join(tais, on=VOTI + ["tyyp", "pool"])
c["seisak"] = seisakumask(c["sile"], c["taistase"], c["hoivatus_sile"], c["hoivatus_tais"])
save_table(c.assign(algus=(c["paev"] + pd.to_timedelta(c["t"].round(), unit="s")).dt.strftime("%Y-%m-%d %H:%M:%S"),
                    mp="MP" + c["mp_id"].astype(str).str.zfill(2), t=np.floor(c["t"] * 1000) / 1000)
           [["mp", "direction_id", "meetod", "algus", "t", "T", "loik", "n", "ks", "kn", "kiirus", "taistase", "ummikus",
             "hoivatus", "seisak"]]
           .round({"T": 1, "ks": 1, "kiirus": 1, "taistase": 1, "hoivatus": 3}), "09_tsuklid")

hms = lambda t: slot_label(t / 60, 60)
ummikud, umber, seisakud = [], [], []
for (mp, did, paev), d in c.groupby(VOTI + ["paev"]):
    t, T, n, q, qs, vs, ks, kn, lk = (d[x].values for x in ["t", "T", "n", "q", "sile", "kiirus_sile", "ks", "kn", "loik"])
    meetod, tyyp, leitud = d["meetod"].iloc[0], d["tyyp"].iloc[0], {}    # lõik -> [(tipp, täistase)]
    for tipp, (a, b) in TIPUD.items():
        key = (mp, did, tyyp, tipp)
        if key + (paev,) in aken.index:                                 # ummik ei ulatu üle augu (loik), nagu ummikus
            mask = (vs <= VABA_KIIRUS * man.at[(mp, did), "vaba_kiirus"] if meetod == "vaba" else
                    ummikumask(qs, tase[key], ALGUS, VAJUMINE, ks / np.where(kn > 0, kn, np.nan), kn,
                               man.at[(mp, did), "kiirus_keskmine"] if KIIRUSTEST else None, loik=lk))
            loik = ummiku_loik(mask, *np.searchsorted(t, [a * 3600, b * 3600]), AUK if meetod == "vaba" else 0, loik=lk)
            if loik:
                leitud.setdefault(loik, []).append((tipp, tase[key]))
    for (i0, i1), tipud in leitud.items():     # sama lõik mõlemas tipus = üks terve päeva ummik ("hommik+õhtu")
        tipp, C = "+".join(x for x, _ in tipud), tipud[0][1]
        t0, t1 = t[i0], t[i1 - 1] + T[i1 - 1]
        Tm = float(pd.Series(T[i0:i1]).mode().iloc[0]) if meetod == "kindel" else float(np.median(T[i0:i1]))
        nn = n[i0:i1][T[i0:i1] == Tm] if meetod == "kindel" else n[i0:i1]
        D = nn.var(ddof=1) / nn.mean() if len(nn) > 1 and nn.mean() > 0 else np.nan
        v_um = ks[i0:i1].sum() / kn[i0:i1].sum() if kn[i0:i1].sum() else np.nan
        x0, x1 = np.searchsorted(t, [t0 - 3600, t1 + 3600])
        ummikud.append(dict(
            mp_id=mp, direction_id=did, meetod=meetod, paev=paev, tyyp=tyyp, tipp=tipp, algus=hms(t0),
            lahenes=hms(t1), algus_h=t0 / 3600, lahenes_h=t1 / 3600, kestus_min=(t1 - t0) / 60, tsukleid=i1 - i0,
            T=round(Tm), soid_tais_tsuklis=float(np.median(nn)), taistase_soid_h=C, hajuvus=D,
            stabiilne=bool(t1 - t0 >= MIN_KESTUS * 60 and (D <= STABIILNE_D or meetod != "kindel")), kiirus_ummikus=v_um,
            r_labilase_kiirus=pd.Series(q[x0:x1]).corr(pd.Series(ks[x0:x1] / np.where(kn[x0:x1] > 0, kn[x0:x1], np.nan)))))
        for k in NIHKED:
            for mark, w0 in ((-1, t0 - k * 60), (1, t1 + (k - 15) * 60)):
                j0, j1 = np.searchsorted(t, [w0, w0 + 900])
                if j1 - j0 < MIN_TSUKLEID or kn[j0:j1].sum() == 0 or not v_um > 0:
                    continue
                kiirus = ks[j0:j1].sum() / kn[j0:j1].sum()
                umber.append(dict(
                    mp_id=mp, direction_id=did, paev=paev, tipp=tipp, nihe_min=mark * k, kiirus=kiirus,
                    voit_kmh=kiirus - v_um, aeg_s_km=3600 / v_um - 3600 / kiirus,
                    aeg_tsukli_kohta=(3600 / v_um - 3600 / kiirus) * float(np.median(nn)),
                    soid_tsuklis=n[j0:j1].mean(), taituvus=q[j0:j1].mean() / C * 100))
    # seisakulõigud (kuni VAJUMINE tsükli pikkune vahe loetakse sisse; arvesse alates MIN_KESTUS minutist) ja neid
    # ümbritsev koormatud aeg = ummik ja seisak kokku
    sk, hs = d["seisak"].values, d["hoivatus_sile"].values
    koormus = loigud(sk | d["ummikus"].values, VAJUMINE, lk)
    for i0, i1 in loigud(sk, VAJUMINE, lk):
        t0, t1 = t[i0], t[i1 - 1] + T[i1 - 1]
        if t1 - t0 < MIN_KESTUS * 60:
            continue
        k0, k1 = next((a, b) for a, b in koormus if a <= i0 < b)
        seisakud.append(dict(
            mp_id=mp, direction_id=did, meetod=meetod, paev=paev, tyyp=tyyp,
            tipp="+".join(x for x, (a, b) in TIPUD.items() if t0 < b * 3600 and t1 > a * 3600) or "muu aeg",
            algus=hms(t0), lopp=hms(t1), algus_h=t0 / 3600, lopp_h=t1 / 3600, kestus_min=(t1 - t0) / 60, tsukleid=i1 - i0,
            soid_tsuklis=n[i0:i1].mean(), labilase_pct=np.nanmean(qs[i0:i1]) / d["taistase"].values[i0] * 100,
            hoivatus_pct=np.nanmean(hs[i0:i1]) * 100, hoivatus_tais_pct=d["hoivatus_tais"].values[i0] * 100,
            kiirus=ks[i0:i1].sum() / kn[i0:i1].sum() if kn[i0:i1].sum() else np.nan,
            aeglasi_pct=d["aegl"].values[i0:i1].sum() / max(n[i0:i1].sum(), 1) * 100,
            seisvaid_pct=d["seis"].values[i0:i1].sum() / max(n[i0:i1].sum(), 1) * 100,
            koormus_algus=hms(t[k0]), koormus_lopp=hms(t[k1 - 1] + T[k1 - 1]), koormus_min=(t[k1 - 1] + T[k1 - 1] - t[k0]) / 60))
um = pd.DataFrame(ummikud).merge(man[["mp", "manoeuvre"]], left_on=VOTI, right_index=True)
um["ryhm"] = np.where(um["meetod"] == "vaba", "vaba vool", "foor")
ub = pd.DataFrame(umber).merge(
    um[VOTI + ["paev", "tipp", "tyyp", "meetod", "ryhm", "stabiilne", "kestus_min", "mp", "manoeuvre"]],
    on=VOTI + ["paev", "tipp"])
ees = ["mp", "direction_id", "manoeuvre", "meetod", "paev", "tyyp", "tipp"]
save_table(um[ees + [x for x in um.columns if x not in ees + ["mp_id", "ryhm"]]].assign(paev=um["paev"].dt.date).round(2),
           "09_ummikud")
save_table(ub[ees + ["stabiilne", "nihe_min", "kiirus", "voit_kmh", "aeg_s_km", "aeg_tsukli_kohta", "soid_tsuklis",
                     "taituvus"]].assign(paev=ub["paev"].dt.date).round(2), "09_ummiku_umber")

# manöövri kokkuvõte: tööpäevade mediaanid tipu kaupa
tp = um[um["tyyp"] == "tööpäev"]
for tipp in TIPUD:
    g = tp[tp["tipp"].str.contains(tipp)].groupby(VOTI)
    med = g[["algus_h", "lahenes_h", "kestus_min", "soid_tais_tsuklis", "kiirus_ummikus"]].median()
    man[f"{tipp}_ummik_algus"] = med["algus_h"].map(lambda h: slot_label(h * 60, 60))
    man[f"{tipp}_ummik_lahenes"] = med["lahenes_h"].map(lambda h: slot_label(h * 60, 60))
    man[f"{tipp}_kestus_min"], man[f"{tipp}_soid_tais_tsuklis"] = med["kestus_min"], med["soid_tais_tsuklis"]
    man[f"{tipp}_kiirus_ummikus"] = med["kiirus_ummikus"]
    man[f"{tipp}_stabiilseid_paevi"], man[f"{tipp}_paevi"] = g["stabiilne"].sum(), g.size()

# seisakud: tabel ja manöövri kokkuvõte (tööpäevade tipuaegadel)
sei = pd.DataFrame(seisakud).merge(man[["mp", "manoeuvre", "kiirus_keskmine"]], left_on=VOTI, right_index=True)
save_table(sei[ees + [x for x in sei.columns if x not in ees + ["mp_id"]]].assign(paev=sei["paev"].dt.date).round(2), "09_seisakud")
seit = sei[(sei["tyyp"] == "tööpäev") & (sei["tipp"] != "muu aeg")]
man["seisakupaevi"] = seit.groupby(VOTI)["paev"].nunique()
man["seisak_min_paevas"] = (seit.groupby(VOTI)["kestus_min"].sum()                 # manöövri enda mõõdetud tööpäevad
                            / c[c["tyyp"] == "tööpäev"].groupby(VOTI)["paev"].nunique()).fillna(0)
save_table(man.reset_index().drop(columns="mp_id").round(2), "09_manoovrid")
pikim, kaua = sei.loc[sei["kestus_min"].idxmax()], sei.loc[sei["koormus_min"].idxmax()]
print(f"\nSeisakuid (>= {MIN_KESTUS} min; hõivatus >= täistaseme oma ja >= {SEISAK_H:.0%}, läbilase <= {ALGUS:.0%}): {len(sei)}, "
      f"{sei.groupby(VOTI).ngroups} manöövril, kokku {sei['kestus_min'].sum():.0f} min, neist tipuaegadel "
      f"{sei.loc[sei['tipp'] != 'muu aeg', 'kestus_min'].sum():.0f} min. Mediaan: läbilase {sei['labilase_pct'].median():.0f}% "
      f"täistasemest, kiirus {sei['kiirus'].median():.0f} km/h (manöövri keskmine {sei['kiirus_keskmine'].median():.0f}), "
      f"aeglasi sõidukeid (alla {AEGLANE_PIIR:.0%} piirkiirusest) {sei['aeglasi_pct'].median():.0f}%, seisvaid (alla "
      f"{SEISEV} km/h) {sei['seisvaid_pct'].median():.0f}%")
print(f"  pikim seisak: {pikim.mp} {pikim.manoeuvre} {pikim.algus}–{pikim.lopp} ({pikim.kestus_min:.0f} min); pikim koormatud aeg "
      f"(ummik + seisak): {kaua.mp} {kaua.manoeuvre} {kaua.koormus_algus}–{kaua.koormus_lopp} ({kaua.koormus_min:.0f} min)")
print("  algustund -> minuteid:", sei.groupby(sei["algus"].str[:2])["kestus_min"].sum().round().astype(int).to_dict())

# --- 4) Kiiruse võit ummiku ümber: stabiilsed ummikud tööpäevadel ----------------------------------------
st = ub[ub["stabiilne"] & (ub["tyyp"] == "tööpäev")]
RN = ["ryhm", "tipp", "nihe_min"]
kokku = (st.groupby(RN)
         .agg(ummikuid=("voit_kmh", "size"), kiirus=("kiirus", "median"), voit_kmh=("voit_kmh", "median"),
              voit_q25=("voit_kmh", lambda s: s.quantile(.25)), voit_q75=("voit_kmh", lambda s: s.quantile(.75)),
              aeg_s_km=("aeg_s_km", "median"), aeg_q25=("aeg_s_km", lambda s: s.quantile(.25)),
              aeg_q75=("aeg_s_km", lambda s: s.quantile(.75)), aeg_tsukli_kohta=("aeg_tsukli_kohta", "median"),
              taituvus=("taituvus", "median")))
kokku["r_kestus_voit"] = st.groupby(RN).apply(lambda g: g["kestus_min"].corr(g["voit_kmh"]))
save_table(kokku.reset_index().round(2), "09_nihked_kokkuvote")
stab = um[um["stabiilne"] & (um["tyyp"] == "tööpäev")]
print(f"\nUmmikuid (manööver x päev x tipp): {len(um)}, neist stabiilseid tööpäevadel {len(stab)}")
print(stab.groupby(["ryhm", "tipp"])[["algus_h", "lahenes_h", "kestus_min", "soid_tais_tsuklis", "kiirus_ummikus",
                                      "r_labilase_kiirus"]].median().round(2).to_string())
print("\nKiirus ja ajavõit ummiku ümber (mediaanid; nihe < 0 = enne ummiku algust):")
print(kokku[["ummikuid", "kiirus", "voit_kmh", "aeg_s_km", "aeg_tsukli_kohta", "taituvus", "r_kestus_voit"]]
      .round(1).to_string())

X = [-k for k in NIHKED[::-1]] + NIHKED
ryhmad = [r for r in ["foor", "vaba vool"] if r in kokku.index.get_level_values("ryhm")]
if ryhmad:
    fig, axes = plt.subplots(len(ryhmad), 2, figsize=(13, 4.4 * len(ryhmad)), squeeze=False)
    for rida, ryhm in zip(axes, ryhmad):
        for ax, (col, lo, hi, lab) in zip(rida, [("voit_kmh", "voit_q25", "voit_q75", "Kiiruse võit võrreldes ummikuga, km/h"),
                                                 ("aeg_s_km", "aeg_q25", "aeg_q75", "Ajavõit sõiduki kohta, s/km")]):
            for nr, (tipp, col_) in enumerate(zip(["hommik", "õhtu", "+".join(TIPUD)], [C_BLUE, C_ORANGE, C_GRAY])):
                if tipp in kokku.loc[ryhm].index.get_level_values("tipp"):
                    k = kokku.loc[(ryhm, tipp)].reindex(X)
                    ax.errorbar(np.arange(len(X)) + (nr - 1) * 0.1, k[col], yerr=[k[col] - k[lo], k[hi] - k[col]],
                                fmt="o-", color=col_, capsize=3, lw=1.6, label=f"{tipp} ({int(k['ummikuid'].max())} ummikut)")
            ax.axvline(3.5, color=C_GRAY, lw=6, alpha=0.3)
            ax.axhline(0, color=TEXT2, lw=0.6)
            ax.set_xticks(range(len(X)))
            ax.set_xticklabels([f"{abs(x) - 15}–{abs(x)}" for x in X])
            ax.set_xlabel("min enne ummiku algust   |   min pärast ummiku lahenemist")
            ax.set_ylabel(lab)
            ax.set_title({"foor": "Fooriga manöövrid (ummik = läbilase püsib tipu lähedal)",
                          "vaba vool": "Vaba vool (ummik = kiirus <= 70% vabast kiirusest)"}[ryhm], fontsize=10)
            ax.legend(fontsize=8)
    fig.suptitle("Kiirus ummiku ümber: mediaan ja kvartiilid (stabiilsed ummikud, tööpäevad; hall = ummik)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    save(fig, "09_06_kiirus_ummiku_umber")

# --- Joonised manöövri kaupa: sõidukeid tsüklis ja kiirus, ummik ja seisak ---------------------------------
SELGITUS = (f"hall = ummik (läbilase üle {ALGUS:.0%} täistasemest), punane = seisak või roomav liiklus (läbilase kuni selle, aga "
            f"loendur on kaetud vähemalt nagu täistasemel);\nsinine = sõidukeid tsüklis, 5 tsükli mediaan (kindel tsükkel: "
            f"katkendjoon = {ALGUS:.0%} täistasemest); oranž = kiirus, katkendjoon = manöövri keskmine kiirus")


def paneel(ax, d, pealkiri, tume=None):
    """Ühe manöövri ühe päeva tsüklid d teljele ax. Vasak telg: hallid punktid = sõidukeid igas tsüklis (vabal voolul
    minutis), sinine joon = selle 5 tsükli liikuv mediaan; kindla tsükliga lisaks katkendjoon = ALGUS x täistase.
    Parem telg: oranž = silutud kiirus, katkendjoon = manöövri keskmine kiirus, vabal voolul punktiir
    = ummiku kiiruslävi. Hall vöönd = ummikus tsüklid, punane = seisak. tume = (algus_h, lõpp_h): see lõik tumedamalt."""
    h, lopp, meetod = d["t"] / 3600, (d["t"] + d["T"]) / 3600, d["meetod"].iloc[0]
    voti = (d["mp_id"].iloc[0], d["direction_id"].iloc[0])
    for veerg, col, alpha in [("ummikus", C_GRAY, 0.15), ("seisak", C_RED, 0.28)]:
        for a, b in loigud(d[veerg].values, 0):
            ax.axvspan(h.iloc[a], lopp.iloc[b - 1], color=col, alpha=alpha, lw=0)
    if tume:
        ax.axvspan(*tume, color=C_GRAY, alpha=0.15, lw=0)
    ax.plot(h, d["n"], ".", color=C_GRAY, ms=3)
    ax.plot(h, sile(d["n"]), color=C_BLUE, lw=1.6)
    if meetod == "kindel":
        ax.plot(h, ALGUS * d["taistase"] * d["T"] / 3600, color=C_BLUE, lw=0.8, ls="--")
    ax.set_ylabel("sõidukeid minutis" if meetod == "vaba" else "sõidukeid tsüklis")
    ax.set_ylim(0, None)
    ax2 = ax.twinx()
    ax2.plot(h, d["kiirus_sile"], color=C_ORANGE, lw=1.3)
    ax2.axhline(man.at[voti, "kiirus_keskmine"], color=C_ORANGE, lw=0.8, ls="--")
    if meetod == "vaba":
        ax2.axhline(VABA_KIIRUS * man.at[voti, "vaba_kiirus"], color=C_ORANGE, lw=0.8, ls=":")
    ax2.set_ylabel("kiirus, km/h", color=C_ORANGE)
    ax2.set_ylim(0, None)
    ax2.grid(False)
    ax.xaxis.set_major_formatter(lambda x, _: slot_label(x * 60, 60))
    ax.set_title(pealkiri, fontsize=10)


def paeva_osa(r, a, b):
    """Manöövri r (mp_id, direction_id, paev) tsüklid kellaajavahemikus a...b (tundides)."""
    d = c[(c["mp_id"] == r.mp_id) & (c["direction_id"] == r.direction_id) & (c["paev"] == r.paev)]
    return d[(d["t"] >= a * 3600) & (d["t"] < b * 3600)]


# Näited: pikimad stabiilsed ummikud fooriga manöövritel (üks manöövri kohta)
for fail, meetod in [("09_01_naited", "kindel"), ("09_02_naited_adaptiivne", "paus")]:
    naited = stab[stab["meetod"] == meetod].sort_values("kestus_min", ascending=False).drop_duplicates(VOTI).head(6)
    if not len(naited):
        continue
    fig, axes = plt.subplots(len(naited), 1, figsize=(12, 2.6 * len(naited)), squeeze=False)
    for ax, r in zip(axes.flat, naited.itertuples()):
        paneel(ax, paeva_osa(r, r.algus_h - 1.5, r.lahenes_h + 1.5),
               f"{r.mp} {short_name(r.manoeuvre, 40)}, {r.paev:%d.%m.%Y} ({MEETOD[r.meetod]}): ummiku ajal "
               f"{r.soid_tais_tsuklis:.0f} sõidukit tsüklis (~{r.T} s), ummik {r.algus}–{r.lahenes}", tume=(r.algus_h, r.lahenes_h))
    axes.flat[-1].set_xlabel("Kellaaeg (tume hall = tipuakna ummik; " + SELGITUS + ")")
    fig.tight_layout()
    save(fig, fail)

r = stab[stab["meetod"] == "kindel"].sort_values("kestus_min", ascending=False).iloc[0]       # 09_01b: üks näide
fig, ax = plt.subplots(figsize=(12, 3.4))
paneel(ax, paeva_osa(r, r.algus_h - 1.5, r.lahenes_h + 1.5),
       f"{r.mp} {short_name(r.manoeuvre, 40)}, {r.paev:%d.%m.%Y}: ummik {r.algus}–{r.lahenes} = aeg, mil 5 tsükli mediaan "
       f"(sinine) on üle {X_LAHEDAL:.0%} täistasemest (katkendjoon)", tume=(r.algus_h, r.lahenes_h))
ax.set_xlabel("Kellaaeg (tume hall = tipuakna ummik; " + SELGITUS + ")")
fig.tight_layout()
save(fig, "09_01b_ummik_naide")

# Näited: pikimad seisakud tipuaegadel (üks manöövri kohta)
naited = sei[sei["tipp"] != "muu aeg"].sort_values("kestus_min", ascending=False).drop_duplicates(VOTI).head(8)
if len(naited):
    fig, axes = plt.subplots(len(naited), 1, figsize=(12, 2.6 * len(naited)), squeeze=False)
    for ax, r in zip(axes.flat, naited.itertuples()):
        paneel(ax, paeva_osa(r, r.algus_h - 1.5, r.lopp_h + 1.5),
               f"{r.mp} {short_name(r.manoeuvre, 34)}, {r.paev:%d.%m.%Y}: seisak {r.algus}–{r.lopp} ({r.kestus_min:.0f} min), läbilase "
               f"{r.labilase_pct:.0f}% täistasemest, kiirus {r.kiirus:.0f} km/h (keskmine {r.kiirus_keskmine:.0f}), aeglasi "
               f"{r.aeglasi_pct:.0f}% ja seisvaid {r.seisvaid_pct:.0f}%")
    axes.flat[-1].set_xlabel("Kellaaeg (" + SELGITUS + ")")
    fig.suptitle(f"Pikimad seisakud; kõigi {len(sei)} seisaku mediaan: läbilase {sei['labilase_pct'].median():.0f}% täistasemest, "   # tekstis toodud mediaanid
                 f"kiirus {sei['kiirus'].median():.0f} km/h (manöövri keskmine {sei['kiirus_keskmine'].median():.0f}), aeglasi "
                 f"{sei['aeglasi_pct'].median():.0f}% ja seisvaid {sei['seisvaid_pct'].median():.0f}%", x=0.01, ha="left",
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.5 / fig.get_figheight()))       # ruum kaherealisele pealkirjale
    save(fig, "09_03_seisakud")
    r = naited.iloc[0]                                          # 09_03b: pikim seisak eraldi
    fig, ax = plt.subplots(figsize=(12, 3.4))
    paneel(ax, paeva_osa(r, r.algus_h - 1.5, r.lopp_h + 1.5),
           f"{r.mp} {short_name(r.manoeuvre, 34)}, {r.paev:%d.%m.%Y}: seisak {r.algus}–{r.lopp} ({r.kestus_min:.0f} min), "
           f"läbilase {r.labilase_pct:.0f}% täistasemest, kiirus {r.kiirus:.0f} km/h (keskmine {r.kiirus_keskmine:.0f}), "
           f"aeglasi {r.aeglasi_pct:.0f}% ja seisvaid {r.seisvaid_pct:.0f}%")
    ax.set_xlabel("Kellaaeg (" + SELGITUS + ")")
    fig.tight_layout()
    save(fig, "09_03b_pikim_seisak")

# Iga ristmik eraldi: kõik manöövrid terve päeva jooksul (üks fail ristmiku ja päeva kohta, kaust 09_04_loendurid/)
if RISTMIKU_JOONISED:
    minuteid = lambda d, veerg: (d["T"] * d[veerg]).sum() / 60
    for (mp, paev), dd in c.groupby(["mp_id", "paev"]):
        osad = [d for _, d in dd.groupby("direction_id")]
        korgus = 2.3 * len(osad) + 1.2
        fig, axes = plt.subplots(len(osad), 1, figsize=(13, korgus), squeeze=False, sharex=True)
        for ax, d in zip(axes.flat, osad):
            r = man.loc[(mp, d["direction_id"].iloc[0])]
            paneel(ax, d, f"{short_name(r['manoeuvre'], 60)} ({MEETOD[r['meetod']]}, radu {r['radu']}): ummikus "
                          f"{minuteid(d, 'ummikus'):.0f} min, seisakus {minuteid(d, 'seisak'):.0f} min")
        axes.flat[-1].set_xlim(*KELL)
        axes.flat[-1].set_xticks(range(KELL[0], KELL[1] + 1))
        axes.flat[-1].set_xlabel("Kellaaeg (" + SELGITUS + ")")
        fig.suptitle(f"{r['mp']} {short_name(r['intersection'], 70)}, {paev:%d.%m.%Y}: sõidukeid tsüklis ja kiirus manöövrite kaupa",
                     x=0.01, y=1 - 0.1 / korgus, ha="left", va="top", fontweight="bold")
        fig.tight_layout(rect=(0, 0, 1, 1 - 0.3 / korgus))      # pealkirjale 0,3 tolli ülal
        save(fig, f"09_04_loendurid/{r['mp']}_{paev:%Y-%m-%d}")

# --- Vaba vool: sõidukeid minutis ja kiirus terve päeva jooksul (tööpäevad; peen joon = päev, jäme = mediaan) --
vabad = man[man["meetod"] == "vaba"].sort_values("soidukeid", ascending=False).head(10)
if len(vabad):
    fig, axes = plt.subplots(len(vabad), 1, figsize=(12, 2.4 * len(vabad)), squeeze=False, sharex=True)
    for ax, (key, r) in zip(axes.flat, vabad.iterrows()):
        d = c[(c["mp_id"] == key[0]) & (c["direction_id"] == key[1])]
        d = d[d["tyyp"] == "tööpäev"] if (d["tyyp"] == "tööpäev").any() else d
        voog = d.pivot(index="t", columns="paev", values="sile") / 60
        kiirus = d.pivot(index="t", columns="paev", values="kiirus_sile")
        h, med = kiirus.index / 3600, kiirus.median(axis=1)
        for a, b in loigud(med <= VABA_KIIRUS * r["vaba_kiirus"], AUK):     # ainult vähemalt MIN_KESTUS min aeglased lõigud
            if (b - a) * VABA_AKEN >= MIN_KESTUS * 60:
                ax.axvspan(h[a], h[b - 1] + VABA_AKEN / 3600, color=C_GRAY, alpha=0.25, lw=0)
        ax.plot(h, voog.median(axis=1), color=C_BLUE, lw=1.6)
        ax.set_ylabel("sõidukeid minutis")
        ax.set_ylim(0, None)
        ax2 = ax.twinx()
        ax2.plot(h, kiirus, color=C_ORANGE, lw=0.6, alpha=0.35)
        ax2.plot(h, med, color=C_ORANGE, lw=1.6)
        ax2.axhline(VABA_KIIRUS * r["vaba_kiirus"], color=C_ORANGE, lw=0.8, ls="--")
        ax2.set_ylabel("kiirus, km/h", color=C_ORANGE)
        ax2.set_ylim(0, None)
        ax2.grid(False)
        ax.set_title(f"{r['mp']} {short_name(r['manoeuvre'], 60)}: vaba kiirus {r['vaba_kiirus']:.0f} km/h, "
                     f"{r['soidukeid'] / d['paev'].nunique() / 1000:.1f} tuh sõidukit päevas (kell {KELL[0]}-{KELL[1]})",
                     fontsize=10)
    axes.flat[-1].set_xticks(range(KELL[0], KELL[1] + 1))
    axes.flat[-1].set_xlabel("Kellaaeg (sinine = sõidukeid minutis; oranž = kiirus; katkendjoon = 70% vabast kiirusest; "
                             f"hall = ummik, kiirus alla selle vähemalt {MIN_KESTUS} min)")
    fig.suptitle("Vaba vooluga manöövrid: liiklus ja kiirus päeva jooksul (5 min liikuv mediaan, tööpäevad)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    save(fig, "09_05_vaba_vool")
print("Valmis.")

# --- Tsükli tuvastus ja kontroll (joonised 09_07, 09_07b) ------------------------------------------------------
# 09_07 näitab meetodit tüüpilisel tipuaja plokil. Fooriprogramme pole, seega kontrollib 09_07b meetodit andmetest:
# (a) sama ristmiku manöövrid valivad samas plokis sama tsükli (üks kontroller), eri ristmikel harvem, (b) juhuslik
# liiklus sama sõidukite arvuga ei anna nii suurt kontrasti.
kb = pd.DataFrame([(*k, TS[c.argmax()], c.max(), len(grupid[k])) for k, c in kon.items()],
                  columns=VOTI + ["paev", "plokk", "T", "kontrast", "n"]).join(man["meetod"], on=VOTI)
kk = kb[kb["meetod"] == "kindel"].reset_index(drop=True)
tp = kk[kk["plokk"].between(7 * 3600 // BLOKK, 9 * 3600 // BLOKK - 1) & (kk["n"] >= 100)]
naide = tp.iloc[int((tp["kontrast"] - tp["kontrast"].median()).abs().argmin())]
nk = tuple(naide[VOTI + ["paev", "plokk"]])
t_n = T_ARR[grupid[nk]]
c_n = kon[nk]
cand = kandidaadid[naide["mp_id"]]
T_n = int(TS[cand[c_n[cand].argmax()]])                               # nagu 1): ristmiku kandidaatide seast
faas = t_n % T_n
h = np.bincount(faas.astype(int), minlength=T_n)
s = np.convolve(np.r_[h, h[:W - 1]], np.ones(W), "valid")
vaiksed = np.flatnonzero(s <= s.min() + 1)
vastas = np.angle(-np.exp(2j * np.pi * faas / T_n).sum()) / (2 * np.pi) * T_n - W / 2
p_n = int(vaiksed[np.abs((vaiksed - vastas + T_n / 2) % T_n - T_n / 2).argmin()])
VALE = 7                                                               # vale pikkus = õige ± 7 s (näitlik)


def klass(a, b):
    """Kahe ploki tsüklite võrdlus: sama, +-1...2 s, kordne (2x, 3x +-2 s) või muu."""
    d = abs(a - b)
    if d == 0:
        return "sama"
    if d <= 2:
        return "±1–2 s"
    r = max(a, b) / min(a, b)
    return "kordne (2× või 3×)" if min(abs(max(a, b) - k * min(a, b)) for k in (2, 3)) <= 2 else "muu"


KLASSID = ["sama", "±1–2 s", "kordne (2× või 3×)", "muu"]
rng = np.random.default_rng(9)
sama_r, eri_r = [], []
for (paev, plokk), g in kk.groupby(["paev", "plokk"]):
    for mp, gg in g.groupby("mp_id"):
        x = gg["T"].values
        sama_r += [klass(x[i], x[j]) for i in range(len(x)) for j in range(i + 1, len(x))]
        muud = g.loc[g["mp_id"] != mp, "T"].values
        if len(muud):                                                    # sama arv paare teiste ristmikega
            eri_r += [klass(a, b) for a, b in zip(rng.choice(x, len(x)), rng.choice(muud, len(x)))]
osa = pd.DataFrame({"sama ristmik": pd.Series(sama_r).value_counts(normalize=True),
                    "eri ristmikud": pd.Series(eri_r).value_counts(normalize=True)}).reindex(KLASSID).fillna(0)
valim = kk.sample(min(len(kk), 3000), random_state=1)
juhus = np.array([kontrast(np.sort(rng.uniform(b * BLOKK, (b + 1) * BLOKK, n))).max()
                  for b, n in zip(valim["plokk"], valim["n"])])
kontroll = pd.DataFrame({
    "naitaja": ["kindla tsükliga manöövri-plokke", "näite ristmik", "näite manööver", "näite päev ja kell",
                "näite tsükkel, s", "näite kontrast", "plokkide kontrasti mediaan", "juhusliku liikluse kontrasti mediaan",
                "juhusliku liikluse kontrasti 99. protsentiil", "plokke üle juhusliku 99. protsentiili, %",
                "paare sama ristmik", "paare eri ristmikud"]
                + [f"sama ristmik: {k}, %" for k in KLASSID] + [f"eri ristmikud: {k}, %" for k in KLASSID],
    "vaartus": [len(kk), man.at[(naide["mp_id"], naide["direction_id"]), "intersection"],
                man.at[(naide["mp_id"], naide["direction_id"]), "manoeuvre"],
                f"{naide['paev']:%d.%m.%Y} kell {hhmm(naide['plokk'] * BLOKK / 3600)}", T_n, round(c_n.max(), 2),
                round(kk["kontrast"].median(), 2), round(np.median(juhus), 2), round(np.quantile(juhus, 0.99), 2),
                round(100 * (valim["kontrast"].values > np.quantile(juhus, 0.99)).mean(), 1), len(sama_r), len(eri_r)]
               + list((100 * osa["sama ristmik"]).round(1)) + list((100 * osa["eri ristmikud"]).round(1))})
print(kontroll.to_string(index=False))
save_table(kontroll, "09_tsukli_kontroll")

# 09_07: sama ploki sõidukid lõigatuna tsükli pikkusteks ridadeks (rida = üks tsükkel), vale ja õige pikkusega
piir = p_n + W / 2                                                     # tsükli piir punase keskel, nagu 1)
b0 = naide["plokk"] * BLOKK
kell = f"{b0 // 3600}.{b0 % 3600 // 60:02d}–{(b0 + BLOKK) // 3600}.{(b0 + BLOKK) % 3600 // 60:02d}"
fig, ax = plt.subplots(1, 2, figsize=(12, 6.5))
for a, (T, pealkiri) in zip(ax, [(T_n + VALE, f"a) Vale pikkus {T_n + VALE} s: sõidukid on igas reas eri kohas"),
                                 (T_n, f"b) Õige pikkus {T_n} s: sõidukid on igas reas samas kohas")]):
    x, rida = (t_n - piir) % T, (t_n - piir) // T
    rida = rida - rida.min() + 1
    a.scatter(x, rida, marker="|", s=70, lw=1.4, color=C_BLUE)
    a.set_xlim(0, T)
    a.set_xticks(np.arange(0, T + 1, 10))
    a.set_ylim(rida.max() + 0.8, -0.8)                                 # ülemine rida jääb sildile "roheline"
    a.set_yticks(np.arange(1, rida.max() + 1, 5))
    a.grid(axis="y", visible=False)
    a.set_title(pealkiri, loc="left")
    a.set_xlabel("aeg tsükli algusest, s")
lo, hi = np.percentile(x, [1, 99])                                     # õige pikkuse roheline (sõidukite tulp)
a.text((lo + hi) / 2, -0.2, "roheline", ha="center", fontsize=10, color=TEXT2)
for xx in (lo / 2, (hi + T_n) / 2):                                    # tühjad osad mõlemal pool = punane
    a.text(xx, (rida.max() + 1) / 2, "punane", ha="center", va="center", fontsize=10, color=TEXT2)
ax[0].set_ylabel("tsükkel (üks rida = üks tsükkel)")
fig.suptitle(f"Fooritsükli pikkus: {naide['n']} sõidukit lõigatakse ridadeks, kriips = üks sõiduk\n"
             f"{man.at[(naide['mp_id'], naide['direction_id']), 'manoeuvre']}, "
             f"{naide['paev']:%d.%m.%Y} kell {kell}", x=0.01, ha="left", fontsize=12, fontweight="bold")
fig.tight_layout()
save(fig, "09_07_tsukli_tuvastus")

fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
a = ax[0]
y = np.arange(len(KLASSID))
a.barh(y - 0.2, 100 * osa["sama ristmik"], height=0.38, color=C_BLUE, label=f"sama ristmik ({len(sama_r):,} paari)".replace(",", " "))
a.barh(y + 0.2, 100 * osa["eri ristmikud"], height=0.38, color=C_GRAY, label=f"eri ristmikud ({len(eri_r):,} paari)".replace(",", " "))
for yy, (s1, s2) in zip(y, osa.values):
    a.text(100 * s1 + 1, yy - 0.2, f"{100 * s1:.0f}%", va="center", fontsize=8, color=TEXT2)
    a.text(100 * s2 + 1, yy + 0.2, f"{100 * s2:.0f}%", va="center", fontsize=8, color=TEXT2)
a.set_yticks(y, KLASSID)
a.invert_yaxis()
a.set_xlim(0, 105)
a.set_xlabel("% manöövripaaridest samas 30 min plokis")
a.legend(fontsize=8, loc="center right")
a.set_title("a) Kahe manöövri iseseisvalt leitud tsükkel", loc="left", fontweight="bold", fontsize=10)
a = ax[1]
bins = np.logspace(np.log10(min(juhus.min(), valim["kontrast"].min())), np.log10(valim["kontrast"].max()), 50)
a.hist(juhus, bins=bins, color=C_GRAY, alpha=0.8, label="juhuslik liiklus (sama sõidukite arv)")
a.hist(valim["kontrast"], bins=bins, color=C_BLUE, alpha=0.8, label="tegelikud kindla tsükliga plokid")
a.axvline(np.quantile(juhus, 0.99), color=TEXT2, lw=0.8, ls="--", label="juhusliku liikluse 99. protsentiil")
a.set_xscale("log")
a.set_xlabel("ploki suurim kontrast (T = 40–180 s), logaritmiline skaala")
a.set_ylabel("plokke")
a.legend(fontsize=8, loc="upper right")
a.set_title(f"b) Tegelikud plokid vs juhuslik liiklus ({len(valim):,} plokki)".replace(",", " "), loc="left", fontweight="bold",
            fontsize=10)
fig.tight_layout()
save(fig, "09_07b_tsukli_kontroll")

# --- Lihtsad joonised (<nr>_10yo, vt 47): samad andmed, üks sõnum, suur kiri ------------------------------------------
plt.rcParams.update({"font.size": 13, "axes.titlesize": 15, "axes.labelsize": 13, "xtick.labelsize": 12,
                     "ytick.labelsize": 12})
VARVID = "roheline = autod mahuvad läbi, hall = ristmik on täis (ummik), punane = autod seisavad"
kellaks = lambda ax: ax.xaxis.set_major_formatter(lambda x, _: slot_label(x * 60, 60))


def triibud(ridu, fail, kysimus, xlim=None):
    """Iga rida = üks manööver ja päev: tsüklid kellaaja teljel värvitud olekuga (vaba, täis, seisak)."""
    fig, ax = plt.subplots(figsize=(12, 0.7 * len(ridu) + 2.2))
    for i, (d, _) in enumerate(ridu):
        h, pikk = d["t"].to_numpy() / 3600, d["T"].to_numpy() / 3600
        sei_, umm = d["seisak"].to_numpy(bool), d["ummikus"].to_numpy(bool)
        for m, col, al in [(~sei_ & ~umm, C_GREEN, 0.35), (umm & ~sei_, C_GRAY, 0.9), (sei_, C_RED, 0.9)]:
            ax.barh(np.full(m.sum(), i), pikk[m], left=h[m], color=col, alpha=al, height=0.7, lw=0)
    ax.set_yticks(range(len(ridu)), [s for _, s in ridu], fontsize=10)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    if xlim:
        ax.set_xlim(*xlim)
    kellaks(ax)
    ax.set_title(f"{kysimus}\n{VARVID}", loc="left", fontsize=13)
    fig.tight_layout()
    save(fig, fail)


silt = lambda r: f"{r.mp} {short_name(r.manoeuvre, 24)}\n{r.paev:%d.%m.%Y}"
for fail, meetod, k in [("09_01_10yo", "kindel", "kindla tsükliga foor"), ("09_02_10yo", "paus", "nutifoor")]:
    naited = stab[stab["meetod"] == meetod].sort_values("kestus_min", ascending=False).drop_duplicates(VOTI).head(6)
    if len(naited):
        triibud([(paeva_osa(r, r.algus_h - 1.5, r.lahenes_h + 1.5), silt(r)) for r in naited.itertuples()], fail,
                f"Millal olid ristmikud täis? Pikimad ummikud ({k})")
naited = sei[sei["tipp"] != "muu aeg"].sort_values("kestus_min", ascending=False).drop_duplicates(VOTI).head(8)
if len(naited):
    triibud([(paeva_osa(r, r.algus_h - 1.5, r.lopp_h + 1.5), silt(r)) for r in naited.itertuples()], "09_03_10yo",
            "Millal autod seisid? Pikimad seisakud")

r1 = stab[stab["meetod"] == "kindel"].sort_values("kestus_min", ascending=False).iloc[0]   # sama näide nagu 09_01b
dd = c[(c["mp_id"] == r1.mp_id) & (c["paev"] == r1.paev)]
triibud([(d, short_name(man.at[(r1.mp_id, did), "manoeuvre"], 34)) for did, d in dd.groupby("direction_id")],
        "09_04_10yo", f"Üks ristmik terve päeva: {short_name(man.at[(r1.mp_id, r1.direction_id), 'intersection'], 40)}, "
                      f"{r1.paev:%d.%m.%Y}. Iga rida on üks sõidusuund", xlim=KELL)

d = paeva_osa(r1, r1.algus_h - 1.5, r1.lahenes_h + 1.5)
h = d["t"] / 3600
fig, ax = plt.subplots(figsize=(11, 5))
for a, b in loigud(d["ummikus"].values, 0):
    ax.axvspan(h.iloc[a], h.iloc[b - 1] + d["T"].iloc[b - 1] / 3600, color=C_GRAY, alpha=0.3, lw=0)
ax.plot(h, sile(d["n"]), color=C_BLUE, lw=2.5)
taid = ALGUS * d["taistase"] * d["T"] / 3600
ax.plot(h, taid, color=TEXT2, lw=1.5, ls="--")
ax.text(h.iloc[-1], taid.iloc[-1] * 1.03, f"peaaegu täis ({ALGUS:.0%})", ha="right", va="bottom", color=TEXT2, fontsize=13)
ax.text(r1.algus_h + (r1.lahenes_h - r1.algus_h) / 2, 0.08 * taid.max(), "ummik", ha="center", fontsize=16,
        fontweight="bold", color=TEXT2)
ax.set_ylim(0, max(sile(d["n"]).max(), taid.max()) * 1.25)
ax.set_ylabel("autosid ühe rohelise tule ajal")
kellaks(ax)
ax.set_title(f"Millal on ristmik ummikus? Näide: {r1.mp}, {r1.paev:%d.%m.%Y}\nKui igal rohelisel sõidab läbi peaaegu "
             "nii palju autosid kui mahub (sinine joon)", loc="left")
save(fig, "09_01b_10yo")

r3 = naited.iloc[0]                                                     # sama näide nagu 09_03b
d = paeva_osa(r3, r3.algus_h - 1.5, r3.lopp_h + 1.5)
h = d["t"] / 3600
fig, ax = plt.subplots(figsize=(11, 5))
for a, b in loigud(d["seisak"].values, 0):
    ax.axvspan(h.iloc[a], h.iloc[b - 1] + d["T"].iloc[b - 1] / 3600, color=C_RED, alpha=0.25, lw=0)
ax.plot(h, d["kiirus_sile"], color=C_ORANGE, lw=2.5)
ax.axhline(r3.kiirus_keskmine, color=TEXT2, lw=1.5, ls="--")
ax.text(h.iloc[0], r3.kiirus_keskmine * 1.03, "tavaline kiirus", va="bottom", color=TEXT2, fontsize=13)
ax.set_ylim(0, max(d["kiirus_sile"].max(), r3.kiirus_keskmine) * 1.3)
ax.set_ylabel("kiirus, km/h")
kellaks(ax)
ax.set_title(f"Kõige pikem seisak: autod liikusid aeglaselt (punane)\n{r3.mp}, {r3.paev:%d.%m.%Y} kell {r3.algus}–{r3.lopp}: "
             f"kiirus {r3.kiirus:.0f} km/h tavalise {r3.kiirus_keskmine:.0f} km/h asemel", loc="left")
save(fig, "09_03b_10yo")

if len(vabad):
    key, r5 = next(iter(vabad.iterrows()))                              # sama näide nagu 09_05 esimene rida
    d = c[(c["mp_id"] == key[0]) & (c["direction_id"] == key[1])]
    d = d[d["tyyp"] == "tööpäev"] if (d["tyyp"] == "tööpäev").any() else d
    kiirus = d.pivot(index="t", columns="paev", values="kiirus_sile").median(axis=1)
    h = kiirus.index / 3600
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(h, kiirus, color=C_ORANGE, lw=2.5)
    ax.axhline(VABA_KIIRUS * r5["vaba_kiirus"], color=TEXT2, lw=1.5, ls="--")
    ax.text(h[-1], VABA_KIIRUS * r5["vaba_kiirus"] * 0.95, "allpool on aeglane", ha="right", va="top", color=TEXT2,
            fontsize=13)
    ax.set_ylim(0, kiirus.max() * 1.25)
    ax.set_xticks(range(KELL[0], KELL[1] + 1, 2))
    ax.set_ylabel("kiirus, km/h")
    ax.set_xlabel("kell")
    ax.set_title(f"Kas autod saavad sõita ilma foorita?\n{r5['mp']} {short_name(r5['manoeuvre'], 50)}: tavalise "
                 "tööpäeva kiirus", loc="left")
    save(fig, "09_05_10yo")

if ryhmad:
    fig, ax = plt.subplots(figsize=(11, 5))
    for ryhm, col, nimi_ in [("foor", C_BLUE, "fooriga suund"), ("vaba vool", C_GREEN, "vaba vooluga suund")]:
        if ryhm in ryhmad:
            k = kokku.loc[(ryhm, "hommik")].reindex(X)["voit_kmh"]
            ax.plot(range(len(X)), k.values, "o-", color=col, lw=2.5, ms=7)
            ax.text(len(X) - 0.9, k.values[-1], nimi_, color=col, fontsize=14, fontweight="bold", va="center")
    ax.axvspan(3.3, 3.7, color=C_GRAY, alpha=0.5, lw=0)
    ax.text(3.5, ax.get_ylim()[1] * 0.97, "ummik", ha="center", va="top", fontsize=13, color=TEXT2,
            bbox=dict(fc="white", ec="none", alpha=0.85))
    ax.axhline(0, color=TEXT2, lw=0.8)
    ax.set_xticks(range(len(X)), [f"{abs(x)} min\nenne" if x < 0 else f"{x} min\npärast" for x in X])
    ax.set_xlim(-0.5, len(X) + 1.9)
    ax.set_ylabel("kiiremini kui ummikus, km/h")
    ax.set_title("Kas loenduri kiirus näitab ummikut? (hommik)\nFooriga suunal on kiirus enne, ajal ja pärast "
                 "ummikut peaaegu sama", loc="left")
    save(fig, "09_06_10yo")

x, rida = (t_n - piir) % T_n, (t_n - piir) // T_n                      # 09_07 õige pikkus, esimesed 12 tsüklit
rida = rida - rida.min() + 1
m = rida <= 12
lo, hi = np.percentile(x, [1, 99])
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.axvspan(lo, hi, color=C_GREEN, alpha=0.15, lw=0)
for a, b in [(0, lo), (hi, T_n)]:
    ax.axvspan(a, b, color=C_RED, alpha=0.15, lw=0)
ax.scatter(x[m], rida[m], marker="|", s=160, lw=2, color=C_BLUE)
ax.text((lo + hi) / 2, 0.2, "roheline tuli", ha="center", fontsize=14, color=TEXT2)
for xx in (lo / 2, (hi + T_n) / 2):
    ax.text(xx, 0.2, "punane", ha="center", fontsize=14, color=TEXT2)
ax.set_xlim(0, T_n)
ax.set_ylim(12.8, -0.6)
ax.set_yticks(range(1, 13))
ax.grid(axis="y", visible=False)
ax.set_xlabel("sekundit tsükli algusest")
ax.set_ylabel("tsükkel")
ax.set_title(f"Kuidas leida foori tsükkel? Autod tulevad salkadena ({T_n} s tagant)\nIga rida on üks tsükkel, kriips = üks "
             "auto. Tühi koht = punane tuli", loc="left")
save(fig, "09_07_10yo")

v = [100 * osa.at["sama", "sama ristmik"], 100 * osa.at["sama", "eri ristmikud"],
     100 * (valim["kontrast"].values > np.quantile(juhus, 0.99)).mean()]
fig, ax = plt.subplots(figsize=(11, 4.8))
ax.barh(range(3), v, color=[C_BLUE, C_GRAY, C_BLUE], height=0.55)
for i, x_ in enumerate(v):
    ax.text(x_ + 1, i, f"{x_:.0f} korda 100-st", va="center", fontsize=14)
ax.set_yticks(range(3), ["sama ristmiku kaks suunda\nleidsid sama tsükli", "eri ristmike kaks suunda\nleidsid sama tsükli",
                         "tsükkel oli selgem kui\njuhuslikul liiklusel"])
ax.invert_yaxis()
ax.set_xlim(0, 125)
ax.grid(axis="y", visible=False)
ax.set_title("Kas tsükli leidmine töötab?\nÜhel ristmikul on üks foorikell, seega peaks tsükkel olema sama", loc="left")
save(fig, "09_07b_10yo")
