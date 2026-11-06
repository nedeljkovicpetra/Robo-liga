"""
kako cemo da implementiramo podvojenost uloge, opcije:
-dve razlicite funkcije
-posebni file za G poseban za N

inicijalizacija uloge

"""

#podatki iz streznika gde se nalazi/ gde je orijentisan

#moramo da imamo timer koji odbrojava 3min

#podatki de se nalazi materijal 

#podatki de se nalaze drva

#podatci o poziciji protivnika

#funkcija kretanje(napred-nazad; levo-desno) zavisi od konstrukcije robota

#funkcija koja racuna udljenost izmedju dve tacke

#funkcija koja racuna ugao do cilja

#grid vrednosti koliko poena gubimo ako stanemo na polje(prazno-0; obicno drvo-1; cherry-2)

"""
Gradbenik:

-pronadje sve nedostavljene materijale; prioritet(zlatna/e, najdalja...najbliza)
#cuva tabelu u kojoj su svi nedostavljeni materijali na poligonu 
1)jos jedna tabela za dostavljene
2)samo da ih popujemo 

==
-izracuna put do svake kocke(od njegove pozicije)
-izracuna put od kocke do baze,  uz to proverava prepreke na putu
==

-funkcija koja racuna najbrzi put do do kocke;


//prioritet ima gvozdje (kocka od 4 poena) alio mora da proveri da li vredi (da li ima drveca koja ne mogu da se zaobidju na putu) 

1)najpre trazimo najkraci put;
2)proverimo da li taj put sece polje koje je oznaceno kao nono zone(-1, -2)

// treba da prepozna kad je dosao do kocke -> trazi put do zone
    repeat

    

"""



"""
EV3 ROBOT - GLAVNI PROGRAM

Uloge:
    GRADBENIK       - preuzima materijale i dostavlja ih u bazu
    NARAVOVARSTVENIK - preuzima drveće i sadi ga na poljima

Glavni program:
    1. Povezivanje sa serverom
    2. Inicijalizacija robota i uloge
    3. Čitanje podataka sa servera
    4. Izbor sledeće akcije
    5. Izvršavanje akcije
    6. Ponavljanje dok se igra ne završi
"""

# ============================================================
# 1. IMPORTS
# ============================================================

from connection import Connection
from classes import State
import config
import time
import math


# ============================================================
# 2. KONSTANTE I GLOBALNE PROMENLJIVE
# ============================================================

TRAJANJE_IGRE = 180

GRADBENIK = "gradbenik"
NARAVOVARSTVENIK = "naravovarstvenik"

# Kaznene vrednosti prelaska preko polja
KAZNA_PRAZNO = 0
KAZNA_SMREKA = 1
KAZNA_CERSNJA = 2


# ============================================================
# 3. INICIJALIZACIJA
# ============================================================

def povezi_s_serverom():
    """Vzpostavi povezavo s strežnikom."""
    pass


def inicializuj_robota():
    """Inicializuje motore, senzore i ostale komponente."""
    pass


def inicializuj_ulogу(podatki):
    """Prepoznaje da li smo gradbenik ili naravovarstvenik."""
    pass


# ============================================================
# 4. DOBIJANJE I OBRADA PODATAKA SA SERVERA
# ============================================================

def osvezi_podatke():
    """
    Preuzima najnovije podatke:
        - pozicija i orijentacija našeg robota
        - pozicija protivničkog robota
        - pozicije materijala
        - pozicije drveća
        - stanje igre i preostalo vreme
    """
    pass


def obradi_podatke(podatki):
    """Pretvara podatke servera u format koji koristimo u programu."""
    pass


def proveri_stanje_igre(podatki):
    """Proverava da li je igra aktivna, pauzirana ili završena."""
    pass


# ============================================================
# 5. GEOMETRIJA I NAVIGACIJA
# ============================================================

def izracunaj_udaljenost(tocka1, tocka2):
    """Računa udaljenost između dve tačke."""
    pass


def izracunaj_ugao(tocka1, tocka2):
    """Računa ugao od prve do druge tačke."""
    pass


def izracunaj_razliku_uglova(trenutni_ugao, ciljni_ugao):
    """Računa najmanju razliku između dva ugla."""
    pass


def izracunaj_pot(starost, cilj, podatki):
    """Pronalazi putanju od trenutne pozicije do cilja."""
    pass


def oceni_pot(pot, podatki):
    """
    Ocenjuje putanju na osnovu:
        - dužine
        - kaznenih poena
        - prepreka
        - potrebnog vremena
    """
    pass


def obrni_robota(ugao):
    """Okreće robota ka željenom uglu."""
    pass


def pelji_do_tocke(cilj):
    """Upravlja robotom dok ne stigne do zadate tačke."""
    pass


def zaustavi_robota():
    """Zaustavlja sve motore."""
    pass


# ============================================================
# 6. GRADBENIK
# ============================================================

def najdi_nedostavljene_materiale(podatki):
    """Vraća listu materijala koji još nisu dostavljeni."""
    pass


def izracunaj_vrednost_materiala(material):
    """Vraća broj poena koje donosi materijal."""
    pass


def izberi_naslednji_material(materiali, podatki):
    """Bira materijal koji je najisplativije dostaviti."""
    pass


def prevzemi_material(material):
    """Prilazi materijalu i pokušava da ga preuzme."""
    pass


def dostavi_material(material, baza):
    """Transportuje materijal do baze."""
    pass


def strategija_gradbenik(podatki):
    """
    Glavna strategija gradbenika:
        1. Pronađi nedostavljene materijale.
        2. Izaberi najbolji cilj.
        3. Isplaniraj put do materijala.
        4. Preuzmi materijal.
        5. Isplaniraj put do baze.
        6. Dostavi materijal.
        7. Ponovi.
    """
    pass


# ============================================================
# 7. NARAVOVARSTVENIK
# ============================================================

def najdi_neposajena_drevesa(podatki):
    """Vraća listu drveća koja još nisu posađena."""
    pass


def najdi_prosta_polja(podatki):
    """Pronalazi polja na kojima je dozvoljena sadnja."""
    pass


def izberi_drevo(drevesa, podatki):
    """Bira sledeće drvo za sadnju."""
    pass


def izberi_polje(drevo, polja, podatki):
    """Bira najbolje polje za sadnju."""
    pass


def prevzemi_drevo(drevo):
    """Prilazi drvetu i preuzima ga."""
    pass


def posadi_drevo(drevo, polje):
    """Postavlja drvo na polje i proverava da li je registrovano."""
    pass


def strategija_naravovarstvenik(podatki):
    """
    Glavna strategija naravovarstvenika:
        1. Pronađi neposajena drveća.
        2. Izaberi drvo.
        3. Izaberi dozvoljeno polje.
        4. Isplaniraj putanju.
        5. Preuzmi drvo.
        6. Postavi ga na polje.
        7. Sačekaj najmanje 5 sekundi.
        8. Proveri da li je server registrovao sadnju.
        9. Ponovi.
    """
    pass


# ============================================================
# 8. IZBOR STRATEGIJE
# ============================================================

def izvrsi_strategiju(vloga, podatki):
    """Poziva strategiju odgovarajuće uloge."""

    if vloga == GRADBENIK:
        strategija_gradbenik(podatki)

    elif vloga == NARAVOVARSTVENIK:
        strategija_naravovarstvenik(podatki)


# ============================================================
# 9. GLAVNA PETLJA
# ============================================================

def main():

    povezi_s_serverom()
    inicializuj_robota()

    # Čekamo početak igre i inicijalizujemo ulogu
    # uloga = ...

    while True:

        podatki = osvezi_podatke()

        if podatki == -1:
            zaustavi_robota()
            continue

        if not proveri_stanje_igre(podatki):
            zaustavi_robota()
            break

        izvrsi_strategiju(uloga, podatki)


# ============================================================
# 10. START PROGRAMA
# ============================================================

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        zaustavi_robota()
