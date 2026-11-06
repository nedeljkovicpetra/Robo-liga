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