# Robo liga FRI 2026 – Gradbišče

Razširjena Python-koda za EV3 robota, ki se prek igralnega strežnika orientira
na podlagi kamere in v času tekme opravlja eno od dveh vlog:

- **Gradbenik:** potiska opeke oziroma železo v polje `construction_site`.
- **Naravovarstvenik:** potiska drevesa na prosta polja in po postavitvi počaka
  najmanj 5 sekund, da strežnik drevo potrdi kot posajeno.

Robot se premika samo, ko je `game_on == true`, `game_paused == false`, ima
veljaven položaj na sledilniku in je preostali čas pozitiven. Ob napaki pri
povezavi ali neznani vrsti objektov se motorji ustavijo.

## 1. Kaj je vključeno

- `robot/main.py` – glavna zanka, prepoznavanje začetne vloge in varno ustavljanje.
- `robot/data.py` – normalizacija JSON-a (`robots`, `objects`, `fields`).
- `robot/navigation.py` – geometrija, obvoz ovir in PID-krmiljenje motorjev.
- `robot/gradbenik.py` – izbira materiala glede na vrednost in dolžino poti.
- `robot/naravovarstvenik.py` – izbira drevesa in prostega polja za sajenje.
- `robot/tasks.py` – izvajanje zaporedja približevanje–poravnava–potiskanje.
- `robot/hardware.py` – EV3 motorji in lažni motorji za testiranje.
- `starter_code/config.py` – nastavitve, ki jih morate prilagoditi.

## 2. Obvezne nastavitve pred zagonom

Odprite `starter_code/config.py` in preverite:

```python
ROBOT_ID = "25"                  # številka vaše značke ArUco
GAME_ID = "VASE_ID_IGRE"          # ID aktivne igre iz monitorja
SERVER_URL = "http://192.168.1.137:8088"
MOTOR_LEFT_PORT = "outC"
MOTOR_RIGHT_PORT = "outB"
ROBOT_ROLE = "auto"
```

Vrednosti lahko določite tudi z okoljskimi spremenljivkami `ROBOT_ID`,
`GAME_ID`, `SERVER_URL` in `ROBOT_ROLE`. `GAME_ID` je namenoma nastavljen na
`CHANGE_ME`, zato program brez pravega ID-ja ne bo začel.

Strežnik je v predstavitvi izziva naveden na naslovu `192.168.1.137:8088`.
Če organizatorji na poligonu podajo drug naslov, uporabite njihovega.

## 3. Strojna oprema in umerjanje

Ta program predpostavlja diferencialni pogon z dvema velikima motorjema na
izhodih B/C ter sprednji potiskač/plužno ploščico, s katero robot premika
kocke 10 × 10 × 8 cm. Program ne upravlja prijemala ali dodatnega motorja.

Pred tekmo umerite predvsem:

- `INVERT_LEFT_MOTOR` / `INVERT_RIGHT_MOTOR`: nastavite na `1`, če se kolo
  vrti v napačno smer.
- `PUSH_STANDOFF_MM`: razdalja med središčema značke robota in kocke, ko je
  potiskač v stiku s kocko. Privzeta vrednost 115 mm je začetna ocena, ne
  univerzalna vrednost.
- `ROBOT_CLEARANCE_MM`: varnostni odmik pri izračunu poti.
- `SPEED_DRIVE` in `SPEED_PUSH`: zmanjšajte, če robot preveč drsi ali potiska
  kocke mimo cilja.
- `DRIVE_KP/KI/KD` in `TURN_KP/KI/KD`: nastavitve PID za vožnjo in obračanje.
  Začnite z `KI=0` in `KD=0`; integrirni in diferencialni člen vključite šele
  po meritvah na poligonu.

Za prvo testiranje uporabljajte nizke hitrosti in poligon brez ljudi ali
predmetov v območju gibanja. Ne začnite s polno hitrostjo.

## 4. Namestitev na EV3

Program je namenjen sistemu ev3dev z `ev3dev2`. Na EV3 potrebujete tudi paketa
`python3-pycurl` in `python3-ujson` (če sta na vaši sliki sistema na voljo):

```bash
sudo apt-get update
sudo apt-get install python3-pycurl python3-ujson
```

Prenesite celotno mapo projekta na EV3, odprite terminal v njej in zaženite:

```bash
python3 main.py
```

Program uporablja samo HTTP GET na igralni strežnik. Med tekmo ne uporablja
zunanjih storitev.

## 5. Preverjanje na računalniku

Na računalniku brez EV3 lahko preverite sintakso in logiko:

```bash
python3 -m unittest discover -s tests -v
python3 main.py --inspect-json tests/sample_construction_game.json
```

`--dry-run` nadomesti fizične motorje z navideznimi, vendar še vedno bere
podatke s strežnika. Pred tem nastavite `GAME_ID` in po potrebi `SERVER_URL`:

```bash
python3 main.py --dry-run
```

`--inspect-json` ne vzpostavi povezave in ne premika motorjev.

## 6. Podatki strežnika in vrste objektov

Osnovna oblika podatkov sledi navodilom izziva: `game_on`, `game_paused`,
`time_left`, `robots[ROBOT_ID].position`, `robots[ROBOT_ID].dir`, `objects` in
`fields`. Vloga se privzeto prepozna po začetnem položaju robota v polju
`construction_site` (gradbenik) ali `environmentalists` (naravovarstvenik).

Parser prepozna tudi objekte, ki jih strežnik vrne kot ločeni skupini
`construction_material` in `trees`, ali prek polj `type`, `kind`, `category`,
`species`, `marker_id`, `aruco_id` in podobnih. V konfiguraciji so vključeni
ID-ji značk iz konfiguracije konstrukcijske igre. Če strežnik vrne samo naključni
ID in položaj brez vrste oziroma ID-ja značke, je vrsta objekta objektivno ni
mogoče ugotoviti iz samega JSON-a. V tem primeru program izpiše ključe
neznanih objektov in ostane ustavljen; ustrezno polje dodajte v
`OBJECT_TYPE_FIELD_CANDIDATES` ali `OBJECT_MARKER_FIELD_CANDIDATES` šele po
preverjanju dejanskega JSON-a s testnega strežnika.

Če strežnik pošlje samo `game_field` in obe bazi, se mreža polj za drevesa
izpelje iz štirih oglišč `game_field` v mrežo 7 × 4. Če so posamezna polja
poslana v `fields`, imajo ta prednost.

## 7. Točkovanje in vir pravil

Vrednosti točk so nastavljive v `starter_code/config.py`. Privzeto sledijo
priloženi predstavitvi izziva: opeka 2, železo 4, smreka 1, japonska češnja 2.
Opomba: konfiguracija `game_config.yaml` v uradnem repozitoriju strežnika, ki
je bila pregledana ob pripravi te različice, navaja `pine: 2` in `cherry: 4`.
Pred tekmo zato preverite trenutno konfiguracijo in po potrebi spremenite
`POINTS_PINE` ter `POINTS_CHERRY`. Strežnik je tisti, ki dejansko določa in
prišteva točke.

Priložena predstavitev določa še: 5 sekund mirovanja drevesa na istem polju,
material šteje, ko je središče značke znotraj baze, ter gradbenik izgublja
točke pri vožnji čez polje z drevesom. Gradbenik se zato izogiba celotnemu
polju, na katerem je drevo, ne le sami kocki; ne poskuša izkoriščati kazenskih
situacij.

## 8. Pomembna omejitev

Koda je sintaktično in logično preverjena z lokalnimi testnimi podatki, ni pa
bila fizično preizkušena na vašem EV3 robotu ali uradnem testnem poligonu.
Mehanska geometrija potiskača, polariteta motorjev, dejanski JSON podključi in
natančne koordinate polj se morajo potrditi na testnem strežniku. Pred tekmo
naredite več kratkih voženj z nizko hitrostjo in spremljajte izpis ter položaje
na monitorju.
