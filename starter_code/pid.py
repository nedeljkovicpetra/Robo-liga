#!/home/robot/roboliga/bin/python
# -*- coding: utf-8 -*-

from time import time


class PID():
    """
    Implementacija algoritma za regulacijo PID.
    Nekaj virov za razjasnitev osnovnega nac
    ela delovanja:
        - https://en.wikipedia.org/wiki/PID_controller
        - https://www.csimn.com/CSI_pages/PIDforDummies.html
        - https://blog.opticontrols.com/archives/344
        - https://www.youtube.com/watch?v=d2AWIA6j0NU
    """

    def __init__(
            self,
            setpoint: float,
            Kp: float,
            Ki: float = None,
            Kd: float = None,
            integral_limit: float = None):
        """
        Ustvarimo nov regulator PID s pripadajocimi parametri.
        Argumenti:
        setpoint: Ciljna vrednost promenljive koju regulisemo.
        Kp: Koeficijent proporcionalnog dela regulatora.
            Vece vrednosti omogucavaju brzu reakciju sistema,
            ali previsoke vrednosti mogu izazvati oscilacije
            i nestabilnost.
        Ki: Koeficijent integralnog dela regulatora.
            Uklanja gresku u ustaljenom stanju.
            Smanjuje brzinu odziva sistema.
        Kd: Koeficijent diferencijalnog dela regulatora.
            Smanjuje vreme potrebno da se sistem stabilizuje
            i povecava brzinu odziva.
        integral_limit: Maksimalna dozvoljena vrednost integrala
        """
        self._setpoint = setpoint
        self._Kp = Kp
        self._Ki = Ki
        self._Kd = Kd
        self._integral_limit = integral_limit
        self._error = None
        self._time = None
        self._integral = None
        self._value = None

    def reset(
            self,
            setpoint: float = None,
            Kp: float = None,
            Ki: float = None,
            Kd: float = None,
            integral_limit: float = None):
        """
        Ponastavitev regulatorja. 
        Lahko mu tudi spremenimo katero od vrednosti parametrov.
        Napaka, integral napake in c
        as se ponastavijo.
        """
        if setpoint is not None:
            self._setpoint = setpoint
        if Kp is not None:
            self._Kp = Kp
        if Ki is not None:
            self._Ki = Ki
        if Kd is not None:
            self._Kd = Kd
        if integral_limit is not None:
            self._integral_limit = integral_limit
        self._error = None
        self._time = None
        self._integral = None
        self._value = None

    def update(self, measurement: float) -> float:
        """
        Izrac
        unamo vrednost izhoda regulatorja (regulirna velic
        ina) 
        glede na izmerjeno vrednost regulirane velic
        ine (measurement) 
        in ciljno vrednost (setpoint).

        Argumenti:
            measurement: Vrednost regulisane velic
            ine izmerena senzorima.
        Povratna vrednost:
            Upravljacka velicina kojom zelimo da korigujemo rad sistema
            (regulisanu velicinu), kako bi dostigao ciljnu vrednost.
        """
        if self._value is None:
            # Na zacetku še nimamo zgodovine meritev, zato inicializiramo
            # integral in vrnemo samo proporcionalni clen.
            self._value = measurement
            # Zapomnimo si zacetni cas.
            self._time = time()
            # Ponastavimo integral napake.
            self._integral = 0
            # Napaka = ciljna vrednost - izmerjena vrednost regulirane velicine.
            self._error = self._setpoint - measurement
            return self._Kp * self._error
        else:
            # Sprememba casa
            time_now = time()
            delta_time = time_now - self._time
            self._time = time_now
            # Izmerjena vrednost regulirane velicine.
            self._value = measurement
            # Napaka = ciljna vrednost - izmerjena vrednost regulirane velicine.
            error = self._setpoint - self._value

            # Proporcionalni del
            P = self._Kp * error

            # Integralni in odvodni clen sta opcijska.
            if self._Ki is None:
                I = 0
            else:
                # Integral se poveca za (sprememba napake) / (sprememba casa).
                self._integral += error * delta_time
                # Ojacitev integralnega dela.
                I = self._Ki * self._integral
                if self._integral_limit is not None:
                    # Omejimo integralni del.
                    I = max(min(I, self._integral_limit),
                            (-1)*(self._integral_limit))

            if self._Kd is None:
                D = 0
            else:
                # Odvod napake z ojacitvijo.
                D = self._Kd * (error - self._error) / delta_time
            # Posodobimo napako.
            self._error = error
            # Vrnemo regulirno velicino, sestavljeno iz proporcionalnega,
            # integralnega in odvodnega clena.
            return P + I + D

