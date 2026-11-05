"""
09 - Fooritsüklid, ummikud ja seisakud sõidukipõhistest loendustest: mitu sõidukit läbib manöövri igas fooritsüklis,
millal on tsükkel täis (ummik), millal läbilase langeb, sest liiklus seisab (seisak), millal ummik laheneb ning kui
palju kiirust ja aega võidab 15/30/45/60 min enne ummiku algust või pärast selle lõppu sõites. Vaba vooluga radadel
(fooritsüklit pole) on ummik kiiruse langus.

SISEND
  common.load_vehicles(None, koik=True)   kõik sõidukipõhised kirjed (tallinn.vehicle_passage): ristmik, kanal,
                                          aeg, kiirus ja loenduril oldud aeg (occ) iga sõiduki kohta; 30.09.2026 ööpäev
                                          ja logija nädal, kui see on andmebaasi laetud
  common.load_manoeuvres()                kanal -> manööver (T08 "Suund"), nt "Tulika VS → PP Endla LVS"
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
  3) "vaba" - vaba vool (Laagna tee, viaduktid, vabad parempöörded jm): 60 s aknad.
  Ummik fooriga manöövril (kindel, paus; common.ummikumask). Läbilase = sõidukit tunnis (n x 3600 / T, võrreldav ka
     foorikava vahetumisel), silutud 5 tsükli liikuva mediaaniga. Täistase = selle tipuakna (hommik 06-11, õhtu 14-20)
     suurim väärtus (päevade mediaan). Ummik = silutud läbilase on vähemalt 80% täistasemest. Lühike vajumine - kuni 2
     järjestikust andmepunkti (tsüklit), mitte alla 75% täistasemest -, mille järel läbilase tõuseb tagasi 80% peale,
     ei katkesta ummikut; pikem või sügavam vajumine lõpetab selle (liiklus on rahunenud). Tipuakna ummik = lõik, mis
     katab akent kõige rohkem (võib ulatuda aknast välja); lahenemine = esimene tsükkel pärast seda.
     Kiirustest "lõigu keskmine kiirus on alla manöövri keskmise" on seadena olemas (KIIRUSTEST), kuid vaikimisi
     väljas: loendurid on stoppjoonel, kus täis tsüklis ületab järjekord loenduri hooga ja kiirus on pigem veidi üle
     päeva keskmise (30.09.2026 kaoks testiga 83 stabiilsest ummikust 21, nende seas selgeimad platood) - kiirus ei
     erista seal ummikut.
     "Stabiilne" (kindel tsükkel) = sõidukite arv tsüklis on ummiku ajal ühtlane (hajuvus/keskmine <= 0,5; juhuslikul
     liiklusel ~1) ja lõik on >= 5 tsüklit. Adaptiivsel fooril muutub tsükli pikkus koos nõudlusega, seal on
     "stabiilne" = ummik kestab >= 10 min.
  Ummik vabal voolul: silutud kiirus <= 70% vabast kiirusest (manöövri silutud kiiruse 85. protsentiil); algus = kiirus
     langeb, lahenemine = kiirus taastub; "stabiilne" = kestab >= 10 min.
  Seisak või roomav liiklus (seisakumask; kõik meetodid) - ummikuaeg, mil läbilase on VÄIKE, sest sõidukid seisavad:
     hõivatus H = tsükli sõidukite loenduril oldud aegade summa / (tsükli pikkus x radade arv) ehk osa ajast, mil loendur
                  on sõidukiga kaetud (tiheduse mõõt; ühe sõiduki aeg arvesse kuni 60 s), silutud 5 tsükli mediaaniga
     H_täis     = sama manöövri silutud hõivatuse mediaan täistaseme tsüklites (läbilase >= 80% täistasemest), sama
                  poolpäev (enne või pärast 12:30)
     seisak     = läbilase < 80% täistasemest  JA  H >= max(H_täis, 10%)
     Loendur on kaetud vähemalt sama palju kui täistasemel, aga läbi pääseb vähem - sõidukid roomavad või seisavad
     loenduril (nt väljasõit on kinni). Kui liiklust on lihtsalt vähe, on väike ka hõivatus ja tsükkel ei ole seisak.
     Lõik = järjestikused seisakutsüklid (kuni 2 tsükli pikkune vahe loetakse sisse), arvesse alates 10 minutist; "tipp"
     näitab, kas lõik jääb tavalisele ummikuajale (hommik 06-11, õhtu 14-20). Koormatud aeg = ummik ja seisak kokku
     (järjestikused tsüklid, mis on üks või teine): nii kaua kestab häiritud liiklus tegelikult. Aeglane sõiduk =
     kiirus <= 10 km/h või seisis loenduril (kiirus 0, loenduril >= 5 s).
  Kiirus ummiku ümber: 15 min aknad 0-15, 15-30, 30-45, 45-60 min enne ummiku algust ja pärast lõppu (nihe -15 = 0-15
     min enne, +15 = 0-15 min pärast jne). Kiiruse võit = akna keskmine kiirus - kiirus ummikus. Ajavõit sõiduki
     kohta = 3600/kiirus ummikus - 3600/kiirus aknas (s/km); tsükli kohta = x sõidukeid täis tsüklis.
  ponytail: kiirus on loenduri punktkiirus (mitte sõiduaeg) ja "täis" tuletatakse ainult loendusest; täpsem oleks
  rohelise lõpuni kestev küllastusvoog või foorikavad.

VÄLJUND (kaust valjund/)
  09_01_naited.png (kindel tsükkel), 09_02_naited_adaptiivne.png (adaptiivne foor)
      Näitab: kuni kuue manöövri pikimat stabiilset tööpäeva-ummikut - kuidas sõidukite arv tsüklis tõuseb täistasemele,
      püsib seal ja langeb.
      Kuidas: paneel manöövri kohta; x-telg = kellaaeg (1,5 h enne ummikut kuni 1,5 h pärast). Vasak y-telg = sõidukeid
      tsüklis: hallid punktid = iga tsükkel, sinine joon = 5 tsükli liikuv mediaan; sinine katkendjoon = 80% ja
      punktiir = 75% täistasemest (ainult kindla tsükliga). Parem y-telg = kiirus, km/h: oranž joon = silutud kiirus,
      oranž katkendjoon = manöövri keskmine kiirus. Tume hall vöönd = tipuakna ummik, hele hall = muud ummikulõigud,
      punane = seisak. Pealkirjas ristmik, manööver, päev, sõidukeid tsüklis ummiku ajal, tsükli pikkus ja ummiku
      kellaajad.
  09_03_seisakud.png
      Näitab: kuni kaheksa manöövri pikimat tipuaegset seisakut - läbilase ja kiirus langevad koos, kuigi on ummikuaeg.
      Kuidas: nagu 09_01_naited (paneel manöövri kohta, 1,5 h enne ja pärast); punane vöönd = seisak või roomav liiklus,
      hall = ummik täistasemel. Pealkirjas seisaku kellaajad ja kestus, läbilase % täistasemest ning kiirus seisaku
      ajal ja manöövri keskmine kiirus.
  09_04_loendurid/MPxx_AAAA-KK-PP.png (üks fail iga ristmiku ja päeva kohta)
      Näitab: ühe ristmiku kõiki manöövreid terve päeva jooksul (kell 5-21).
      Kuidas: paneel manöövri kohta, sama kujundus kui 09_01_naited (vabal voolul vasakul teljel sõidukeid minutis ja oranž
      punktiir = ummiku kiiruslävi). Paneeli pealkirjas manööver, meetod, radade arv ning minutid ummikus ja seisakus.
      Välja lülitamine (kiirem käivitus): RISTMIKU_JOONISED = False.
  09_05_vaba_vool.png
      Näitab: kümne suurima vaba vooluga manöövri liiklust ja kiirust päeva jooksul.
      Kuidas: paneel manöövri kohta; x-telg = kellaaeg 5-21. Sinine = sõidukeid minutis (tööpäevade mediaan), oranž
      peen joon = iga päeva kiirus, oranž jäme = päevade mediaan (5 min liikuv mediaan); katkendjoon = 70% vabast
      kiirusest; hall vöönd = ummik (mediaankiirus alla selle vähemalt 10 min).
  09_06_kiirus_ummiku_umber.png
      Näitab: kui palju kiirem on liiklus vahetult enne ummikut ja pärast seda.
      Kuidas: rida rühma kohta (foor, vaba vool); vasakul kiiruse võit võrreldes ummikuga (km/h), paremal ajavõit
      sõiduki kohta (s/km). x-telg = 15 min aknad: 45-60 ... 0-15 min enne ummiku algust | 0-15 ... 45-60 min pärast
      lahenemist; hall püstriba = ummik. Punkt = stabiilsete tööpäeva-ummikute mediaan, vurrud = kvartiilid; sinine =
      hommik, oranž = õhtu, hall = terve päeva ummik.
  09_tsuklid.csv            iga tsükkel või aken: algus, pikkus T, sõidukeid n, kiirus, täistase, kas ummikus, hõivatus,
                            kas seisak
  09_manoovrid.csv          manöövri meetod, selguse näitajad, keskmine ja vaba kiirus, radade arv, tippude mediaanid,
                            seisakupäevade arv ja seisakuminutid tööpäeva kohta (tipuaegadel)
  09_seisakud.csv           iga seisakulõik: algus, lõpp, kestus, läbilase % täistasemest, hõivatus ja täistaseme
                            hõivatus, kiirus, aeglaste sõidukite osakaal ning ümbritsev koormatud aeg (ummik + seisak)
  09_ummikud.csv            iga ummik (manööver x päev x tipp): algus, lahenemine, kestus, tsüklite arv, sõidukeid täis
                            tsüklis, täistase, hajuvus, stabiilsus, kiirus ummikus
  09_ummiku_umber.csv       kiirus ja ajavõit igas 15 min aknas ummiku ümber
  09_nihked_kokkuvote.csv   eelmise mediaanid ja kvartiilid rühma, tipu ja nihke kaupa
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import (load_vehicles, save, save_table, set_style, short_name, slot_label, loigud, ummiku_loik, ummikumask,
                    load_manoeuvres, OUT_DIR, C_BLUE, C_ORANGE, C_GRAY, C_RED, TEXT2)

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
VABA_KIIRUS = 0.7                # vaba vool: ummik, kui silutud kiirus <= 70% vabast kiirusest
ALGUS = 0.80                     # ummikus: silutud läbilase (sõidukeid tsüklis) >= 80% täistasemest
PUSIB = 0.75                     # lühike vajumine kuni 75% täistasemeni ei katkesta ummikut ...
VAJUMINE = 2                     # ... kui see kestab kuni 2 andmepunkti ja läbilase tõuseb siis tagasi >= 80%
KIIRUSTEST = False               # True: lõik on ummik ainult siis, kui selle keskmine kiirus < manöövri keskmine kiirus
                                 # (11 künnise tundlikkus arvutatakse alati ilma kiirustestita)
SEISAK_H = 0.10                  # seisak: loendur on kaetud >= 10% ajast (raja kohta) ja vähemalt sama palju kui täistasemel
OCC_MAX = 60                     # ühe sõiduki loenduril oldud aeg arvesse kuni 60 s (kinni jäänud loendur ei tohi domineerida)
AEGLANE = 10                     # aeglane sõiduk: kiirus <= 10 km/h või seisis loenduril (kiirus 0, loenduril >= 5 s)
STABIILNE_D = 0.5                # ummiku ajal sõidukite arvu hajuvus/keskmine <= 0,5
MIN_TSUKLEID = 5                 # lühim stabiilne ummik tsüklites (kindel tsükkel); ka akna väikseim tsüklite arv
MIN_KESTUS = 10                  # adaptiivse foori ja vaba voolu ummik loetakse arvesse alates 10 minutist
AUK = 3                          # vaba vool: nii mitu järjestikust kiiremat akent loetakse veel ummiku sisse
KATVUS = 0.8                     # tipuaknast peab tsüklitega kaetud olema vähemalt 80%
TIPUD = {"hommik": (6, 11), "õhtu": (14, 20)}
RISTMIKU_JOONISED = True         # joonis iga ristmiku ja päeva kohta (kaust 09_04_loendurid/); False = jäta vahele (kiirem)
NIHKED = [15, 30, 45, 60]
MEETOD = {"kindel": "kindel tsükkel", "paus": "adaptiivne foor", "vaba": "vaba vool"}

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


def seisakumask(labilase, taistase, hoivatus, hoivatus_tais, algus=ALGUS, h_min=SEISAK_H):
    """Seisak või roomav liiklus tsüklite kaupa: loendur on sõidukitega kaetud vähemalt sama suure osa ajast kui
    täistasemel töötades (hoivatus >= hoivatus_tais ja >= h_min), aga läbi pääseb alla algus x täistase. Sama palju
    või rohkem sõidukeid loenduril ja vähem läbi = sõidukid seisavad või roomavad (vähe liiklust annaks väikese
    hõivatuse). Kõik sisendid silutud; puuduv täistase või hõivatus -> False."""
    return ((np.asarray(hoivatus, float) >= np.maximum(np.asarray(hoivatus_tais, float), h_min))
            & (np.asarray(labilase, float) < algus * np.asarray(taistase, float)))


# enesekontroll: sünteetiline 90 s tsükkel (roheline 30 s) leitakse üles; pausid; lõigu valik ja augu sulgemine
_r = np.random.default_rng(0)
_t = np.sort(np.concatenate([k * 90 + _r.uniform(5, 35, 12) for k in range(40)]))
assert TS[kontrast(_t).argmax()] == 90 and len(pausitsuklid(_t)) == 40 and pausi_selgus([_t + 3600]) > PAUS_E
assert pausitsuklid(np.array([0, 1, 2, 20, 21, 30, 60, 61.])).tolist() == [0, 30, 60]
assert ummiku_loik([1, 1, 0, 1, 1, 0, 0, 0, 0, 1], 0, 10) == (0, 5) and ummiku_loik([1, 1, 0, 0, 0, 0, 1], 5, 7) == (6, 7)
# vajumised: 1 punkt 76 -> jätkub; 76, 74 (alla 75) -> katkeb; 3 punkti 76 (üle 2 punkti) -> katkeb
_q = np.array([50, 70, 79, 82, 76, 90, 76, 74, 82, 76, 76, 76, 82.])
assert ummikumask(_q, 100).tolist() == [0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 1]
assert ummikumask(_q, 100, kiirus=np.full(13, 20.), kaal=np.ones(13), v_kesk=30).sum() == 5      # kiirus alla keskmise
assert not ummikumask(_q, 100, kiirus=np.full(13, 40.), kaal=np.ones(13), v_kesk=30).any()       # üle keskmise: pole ummik
# seisak: väike läbilase + suur hõivatus; väike hõivatus = vähe liiklust; täistasemel = ummik, mitte seisak; täistase puudu
assert seisakumask([50, 50, 90, 50, 50], [100, 100, 100, 100, np.nan], [.2, .05, .3, .12, .2], .15).tolist() == [1, 0, 0, 0, 0]

set_style()
print("Laen sõidukipõhised loendused...")
v = load_vehicles(None, koik=True)
dm = load_manoeuvres()
dm = dm.assign(mp_id=dm["mp"].str[2:].astype(int)).rename(columns={"channel": "kanal"})
v = v.merge(dm[VOTI + ["kanal"]], on=["mp_id", "kanal"]).dropna(subset=["direction_id"])
v["direction_id"] = v["direction_id"].astype(int)
v["paev"] = v["ts"].dt.normalize()
v["t"] = (v["ts"] - v["paev"]).dt.total_seconds()
v = v[(v["t"] >= KELL[0] * 3600) & (v["t"] < KELL[1] * 3600)].sort_values(VOTI + ["ts"]).reset_index(drop=True)
v["plokk"] = (v["t"] // BLOKK).astype(int)
print(f"{len(v):,} sõidukit kell {KELL[0]}-{KELL[1]}, {v['paev'].nunique()} päeva, "
      f"{v.groupby(VOTI).ngroups} manöövrit")

T_ARR, KM = v["t"].values, v["kiirus"].values
OCC = v["occ"].clip(upper=OCC_MAX).values                                 # loenduril oldud aeg, s
AEGL = ((v["kiirus"] <= AEGLANE) & ~((v["kiirus"] == 0) & (v["occ"] < 5))).values   # roomas või seisis (kiirus 0 lühikese
                                                                          # ajaga = kiirus mõõtmata, ei loe)
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
        "aegl": np.bincount(k, weights=AEGL[i], minlength=m)})[kehtiv]


# --- 1) Kindel tsükkel: kontrast iga manöövri-ploki kohta, kandidaadid ristmiku kaupa ------------------
kon = {k: kontrast(T_ARR[i]) for k, i in grupid.items() if len(i) >= MIN_N}
haal = pd.DataFrame([(k[0], TS[c.argmax()], len(grupid[k])) for k, c in kon.items()], columns=["mp_id", "T", "n"])
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
c["sile"] = c.groupby(VOTI + ["paev"])["q"].transform(sile)
c["kiirus_sile"] = c.groupby(VOTI + ["paev"])["kiirus"].transform(sile)
# hõivatus: osa tsükli ajast, mil loendur on sõidukiga kaetud (raja kohta) - tiheduse mõõt
c["hoivatus"] = c["occ"] / (c["T"] * man["radu"].reindex(pd.MultiIndex.from_frame(c[VOTI])).values)
c["hoivatus_sile"] = c.groupby(VOTI + ["paev"])["hoivatus"].transform(sile)
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
for (mp, did, paev), ix in c.groupby(VOTI + ["paev"]).indices.items():
    if c["meetod"].values[ix[0]] != "vaba":
        ummikus[ix] = ummikumask(c["sile"].values[ix], c["taistase"].values[ix], ALGUS, PUSIB, VAJUMINE, c["kiirus"].values[ix],
                                 c["kn"].values[ix], man.at[(mp, did), "kiirus_keskmine"] if KIIRUSTEST else None)
c["ummikus"] = ummikus
# seisak või roomav liiklus (seisakumask): hõivatus vähemalt nagu sama manöövri täistaseme tsüklites (läbilase >= 80%
# täistasemest, sama poolpäev), aga läbilase alla 80% täistasemest. Kehtib kõigi meetodite kohta.
tais = c[c["sile"] >= ALGUS * c["taistase"]].groupby(VOTI + ["tyyp", "pool"])["hoivatus_sile"].median().rename("hoivatus_tais")
c = c.join(tais, on=VOTI + ["tyyp", "pool"])
c["seisak"] = seisakumask(c["sile"], c["taistase"], c["hoivatus_sile"], c["hoivatus_tais"])
save_table(c.assign(algus=(c["paev"] + pd.to_timedelta(c["t"].round(), unit="s")).dt.strftime("%Y-%m-%d %H:%M:%S"),
                    mp="MP" + c["mp_id"].astype(str).str.zfill(2), t=np.floor(c["t"] * 1000) / 1000)
           [["mp", "direction_id", "meetod", "algus", "t", "T", "n", "kiirus", "taistase", "ummikus", "hoivatus", "seisak"]]
           .round({"T": 1, "kiirus": 1, "taistase": 1, "hoivatus": 3}), "09_tsuklid")

hms = lambda t: slot_label(t / 60, 60)
ummikud, umber, seisakud = [], [], []
for (mp, did, paev), d in c.groupby(VOTI + ["paev"]):
    t, T, n, q, qs, vs, ks, kn = (d[x].values for x in ["t", "T", "n", "q", "sile", "kiirus_sile", "ks", "kn"])
    meetod, tyyp, leitud = d["meetod"].iloc[0], d["tyyp"].iloc[0], {}    # lõik -> [(tipp, täistase)]
    for tipp, (a, b) in TIPUD.items():
        key = (mp, did, tyyp, tipp)
        if key + (paev,) in aken.index:
            mask = (vs <= VABA_KIIRUS * man.at[(mp, did), "vaba_kiirus"] if meetod == "vaba" else
                    ummikumask(qs, tase[key], ALGUS, PUSIB, VAJUMINE, ks / np.where(kn > 0, kn, np.nan), kn,
                               man.at[(mp, did), "kiirus_keskmine"] if KIIRUSTEST else None))
            loik = ummiku_loik(mask, *np.searchsorted(t, [a * 3600, b * 3600]), AUK if meetod == "vaba" else 0)
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
            stabiilne=bool(i1 - i0 >= MIN_TSUKLEID and D <= STABIILNE_D if meetod == "kindel"
                           else t1 - t0 >= MIN_KESTUS * 60), kiirus_ummikus=v_um,
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
    koormus = loigud(sk | d["ummikus"].values, VAJUMINE)
    for i0, i1 in loigud(sk, VAJUMINE):
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
man["seisak_min_paevas"] = seit.groupby(VOTI)["kestus_min"].sum() / c.loc[c["tyyp"] == "tööpäev", "paev"].nunique()
save_table(man.reset_index().drop(columns="mp_id").round(2), "09_manoovrid")
pikim, kaua = sei.loc[sei["kestus_min"].idxmax()], sei.loc[sei["koormus_min"].idxmax()]
print(f"\nSeisakuid (>= {MIN_KESTUS} min; hõivatus >= täistaseme oma ja >= {SEISAK_H:.0%}, läbilase < {ALGUS:.0%}): {len(sei)}, "
      f"{sei.groupby(VOTI).ngroups} manöövril, kokku {sei['kestus_min'].sum():.0f} min, neist tipuaegadel "
      f"{sei.loc[sei['tipp'] != 'muu aeg', 'kestus_min'].sum():.0f} min. Mediaan: läbilase {sei['labilase_pct'].median():.0f}% "
      f"täistasemest, kiirus {sei['kiirus'].median():.0f} km/h (manöövri keskmine {sei['kiirus_keskmine'].median():.0f}), "
      f"aeglasi sõidukeid {sei['aeglasi_pct'].median():.0f}%")
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
SELGITUS = (f"hall = ummik (läbilase >= {ALGUS:.0%} täistasemest), punane = seisak või roomav liiklus (läbilase alla selle, aga "
            f"loendur on kaetud vähemalt nagu täistasemel);\nsinine = sõidukeid tsüklis, 5 tsükli mediaan (kindel tsükkel: "
            f"katkendjoon = {ALGUS:.0%}, punktiir = {PUSIB:.0%} täistasemest); oranž = kiirus, katkendjoon = manöövri keskmine kiirus")


def paneel(ax, d, pealkiri, tume=None):
    """Ühe manöövri ühe päeva tsüklid d teljele ax. Vasak telg: hallid punktid = sõidukeid igas tsüklis (vabal voolul
    minutis), sinine joon = selle 5 tsükli liikuv mediaan; kindla tsükliga lisaks katkendjoon = ALGUS ja punktiir =
    PUSIB x täistase. Parem telg: oranž = silutud kiirus, katkendjoon = manöövri keskmine kiirus, vabal voolul punktiir
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
        for k, ls in [(ALGUS, "--"), (PUSIB, ":")]:
            ax.plot(h, k * d["taistase"] * d["T"] / 3600, color=C_BLUE, lw=0.8, ls=ls)
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

# Näited: pikimad seisakud tipuaegadel (üks manöövri kohta)
naited = sei[sei["tipp"] != "muu aeg"].sort_values("kestus_min", ascending=False).drop_duplicates(VOTI).head(8)
if len(naited):
    fig, axes = plt.subplots(len(naited), 1, figsize=(12, 2.6 * len(naited)), squeeze=False)
    for ax, r in zip(axes.flat, naited.itertuples()):
        paneel(ax, paeva_osa(r, r.algus_h - 1.5, r.lopp_h + 1.5),
               f"{r.mp} {short_name(r.manoeuvre, 34)}, {r.paev:%d.%m.%Y}: seisak {r.algus}–{r.lopp} ({r.kestus_min:.0f} min), läbilase "
               f"{r.labilase_pct:.0f}% täistasemest, kiirus {r.kiirus:.0f} km/h (keskmine {r.kiirus_keskmine:.0f})")
    axes.flat[-1].set_xlabel("Kellaaeg (" + SELGITUS + ")")
    fig.tight_layout()
    save(fig, "09_03_seisakud")

# Iga ristmik eraldi: kõik manöövrid terve päeva jooksul (üks fail ristmiku ja päeva kohta, kaust 09_04_loendurid/)
if RISTMIKU_JOONISED:
    (OUT_DIR / "09_04_loendurid").mkdir(exist_ok=True)
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
