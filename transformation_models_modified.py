#! -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from abc import abstractmethod
from scipy import integrate
from scipy.interpolate import splrep, splev, interp1d
from scipy.optimize import root

R = 8.314459
K = 273.15


def FahrenheitToCelsius(TF):
    """
    Converts temperature in Fahrenheit to Celsius
    """
    return (TF - 32.)*5./9.


def FC(**comp):
    """
    Function that expresses the effects of the alloying elements on
    on the kinetics of ferrite transformation
    """
    C = comp.get('C', 0)
    Mn = comp.get('Mn', 0)
    Si = comp.get('Si', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    Mo = comp.get('Mo', 0)
    return np.exp((1.0 + 6.31*C + 1.78*Mn + 0.31*Si + 1.12*Ni + 2.7*Cr + 4.06*Mo))


def PC(**comp):
    """
    Function that expresses the effects of the alloying elements on
    on the kinetics of pearlite transformation
    """
    C = comp.get('C', 0)
    Mn = comp.get('Mn', 0)
    Si = comp.get('Si', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    Mo = comp.get('Mo', 0)
    return np.exp(-4.25 + 4.12*C + 4.36*Mn + 0.44*Si + 1.71*Ni + 3.33*Cr + 5.19*np.sqrt(Mo))


def BC(**comp):
    """
    Function that expresses the effects of the alloying elements on
    on the kinetics of bainite transformation
    """
    C = comp.get('C', 0)
    Mn = comp.get('Mn', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    Mo = comp.get('Mo', 0)
    return np.exp(-10.23 + 10.18*C + 0.85*Mn + 0.55*Ni + 0.9*Cr + 0.36*Mo)


def Ae1_Grange(**comp):
    """
    Grange's equation for Ae1
    """
    Mn = comp.get('Mn', 0)
    Si = comp.get('Si', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    return FahrenheitToCelsius(1333 - 25*Mn + 40*Si - 26*Ni + 42*Cr)


def Ae3_Grange(**comp):
    """
    Grange's equation for Ae3
    """
    C = comp.get('C', 0)
    Mn = comp.get('Mn', 0)
    Si = comp.get('Si', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    return FahrenheitToCelsius(1570 - 323*C - 25*Mn + 80*Si - 32*Ni - 3*Cr)


def Ae1_Andrews(**comp):
    """
    Andrews' equation for Ae1
    """
    Mn = comp.get('Mn', 0)
    Si = comp.get('Si', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    Mo = comp.get('Mo', 0)
    W = comp.get('W', 0)
    As = comp.get('As', 0)
    return 723 - 16.9*Ni + 29.1*Si + 6.38*W - 10.7*Mn + 16.9*Cr + 290*As


def Ae3_Andrews(**comp):
    """
    Andrews' equation for Ae3
    """
    C = comp.get('C', 0)
    Mn = comp.get('Mn', 0)
    Si = comp.get('Si', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    Mo = comp.get('Mo', 0)
    V = comp.get('V', 0)
    W = comp.get('W', 0)
    Cu = comp.get('Cu', 0)
    # P = comp.get('P', 0)
    # Al = comp.get('Al', 0)
    # As = comp.get('As', 0)
    # Ti = comp.get('Ti', 0)
    return 910 - 203*np.sqrt(C) + 44.7*Si - 15.2*Ni + 31.5*Mo + 104*V + 13.1*W - \
        30.0*Mn + 11.0*Cr + 20.0*Cu  # - 700*P - 400*Al - 120*As - 400*Ti


def Bs_Li(**comp):
    """
    Bainite start calculation from Li's work
    """
    C = comp.get('C', 0)
    Mn = comp.get('Mn', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    Mo = comp.get('Mo', 0)
    return 637 - 58*C - 35*Mn - 15*Ni - 34*Cr - 41*Mo


def Bs_VanBohemen(**comp):
    """
    Bainite start calculation from Van Bohemen's work
    [1] S.M.C. van Bohemen, Mater. Sci. Technol. 28 (2012) 487–495.
    """
    C = comp.get('C', 0)
    Mn = comp.get('Mn', 0)
    Si = comp.get('Si', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    Mo = comp.get('Mo', 0)
    return 839 - (86*Mn + 23*Si + 67*Cr + 33*Ni + 75*Mo) - 270*(1 - np.exp(-1.33*C))


def Ms_Andrews(**comp):
    """
    Andrews' equation for Ms
    """
    C = comp.get('C', 0)
    Mn = comp.get('Mn', 0)
    Si = comp.get('Si', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    Mo = comp.get('Mo', 0)
    Co = comp.get('Co', 0)
    return 539 - 423*C - 30.4*Mn - 17.7*Ni - 12.1*Cr - 7.5*Mo + 10*Co - 7.5*Si


def alpha_martensite_VanBohemen(**comp):
    """
    Martensite transformation rate constant
    [1] S.M.C. van Bohemen, Mater. Sci. Technol. 28 (2012) 487–495.
    """
    C = comp.get('C', 0)
    Mn = comp.get('Mn', 0)
    Si = comp.get('Si', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    Mo = comp.get('Mo', 0)
    return 1e-3*(27.2 - (0.14*Mn + 0.21*Si + 0.11*Cr + 0.08*Ni + 0.05*Mo) - 19.8*(1-np.exp(-1.56*C)))


def Ms_VanBohemen(**comp):
    """
    Martensite start temperature
    [1] S.M.C. van Bohemen, Mater. Sci. Technol. 28 (2012) 487–495.
    """
    C = comp.get('C', 0)
    Mn = comp.get('Mn', 0)
    Si = comp.get('Si', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    Mo = comp.get('Mo', 0)
    return 565 - (31*Mn + 13*Si + 10*Cr + 18*Ni + 12*Mo) - 600*(1-np.exp(-0.96*C))


def Hv_martensite(phi700, **comp):
    """
    Martensite Vickers hardness empirical equation
    (Maynier et al.)
    """
    C = comp.get('C', 0)
    Mn = comp.get('Mn', 0)
    Si = comp.get('Si', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    return 127 + 949*C + 27*Si + 11*Mn + 8*Ni + 16*Cr + 21*np.log10(phi700*3600)


def Hv_bainite(phi700, **comp):
    """
    Bainite Vickers hardness empirical equation
    (Maynier et al.)
    """
    C = comp.get('C', 0)
    Mn = comp.get('Mn', 0)
    Si = comp.get('Si', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    Mo = comp.get('Mo', 0)
    return -323 + 185*C + 330*Si + 153*Mn + 65*Ni + 144*Cr + 191*Mo + \
        (89 + 53*C - 55*Si - 22*Mn - 10*Ni - 20*Cr - 33*Mo)*np.log10(phi700*3600)


def Hv_ferrite_pearlite(phi700, **comp):
    """
    Ferrite + pearlite Vickers hardness empirical equation
    (Maynier et al.)
    """
    C = comp.get('C', 0)
    Mn = comp.get('Mn', 0)
    Si = comp.get('Si', 0)
    Ni = comp.get('Ni', 0)
    Cr = comp.get('Cr', 0)
    Mo = comp.get('Mo', 0)
    V = comp.get('V', 0)
    return 42 + 223*C + 53*Si + 30*Mn + 12.6*Ni + 7*Cr + 19*Mo + \
        (10 - 19*Si + 4*Ni + 8*Cr + 130*V)*np.log10(phi700*3600)


class Alloy:
    """
    Alloy properties (composition in wt.% and prior austenite grain size)
    """

    def __init__(self, gs, **w):
        # Grain size
        self.gs = gs

        # Alloy composition
        self.w = w
        # Main elements
        self.C = w.get('C', 0)
        self.Mn = w.get('Mn', 0)
        self.Si = w.get('Si', 0)
        self.Ni = w.get('Ni', 0)
        self.Cr = w.get('Cr', 0)
        self.Mo = w.get('Mo', 0)
        self.Co = w.get('Co', 0)


# Selección del valor de Ms usando múltiples ecuaciones
        ms_options = {
            'Saha': 539 - (423 * self.C) - (30.4 * self.Mn) - (17.7 * self.Ni) - (12.1 * self.Cr) - (7.5 * self.Si) - (7.5 * self.Mo) - (7.5 * w.get('W', 0)),
            'Andrews_Corrected': 512 - (453 * self.C) - (16.9 * self.Ni) + (15 * self.Cr) - (9.5 * self.Mo) + (217 * (self.C ** 2)) - (71.5 * self.C * self.Mn) - (67.6 * self.C * self.Cr),
            'Nehenberg': 500 - (300 * self.C) - (33 * self.Mn) - (17 * self.Ni) - (22 * self.Cr) - (11 * self.Si),
            'Steven_Haynes': 561 - (474 * self.C) - (33 * self.Mn) - (17 * self.Ni) - (17 * self.Cr) - (21 * self.Si),
            'Payson_Savage': ((930 - 570 * self.C - 60 * self.Mn - 50 * self.Cr - 30 * self.Ni - 20 * self.Si - 20 * self.Mo - 20 * w.get('W', 0)) - 32) / 1.8,
            'Rowland': ((930 - 600 * self.C - 60 * self.Mn - 50 * self.Cr - 30 * self.Ni - 20 * self.Si - 20 * self.Mo - 20 * w.get('W', 0)) - 32) / 1.8,
            'Grange_Stewart': ((1000 - 650 * self.C - 70 * self.Mn - 70 * self.Cr - 35 * self.Ni - 50 * self.Mo) - 32) / 1.8,
            'Andrews_Empirical': 539 - 423 * self.C - 30.4 * self.Mn - 12.1 * self.Cr - 17.7 * self.Ni - 7.5 * self.Mo,
            'Steven_Haynes2': 561 - 474 * self.C - 33 * self.Ni - 17 * self.Cr - 17 * self.Ni - 21 * self.Mo,
        }

        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 6))

        bars = plt.bar(ms_options.keys(), ms_options.values(), color='steelblue')

        # Para cada barra, dibujamos un texto encima con su valor:
        for bar in bars:
            height = bar.get_height()
            plt.annotate(
                f"{height:.2f}",              # Formato con 2 decimales
                xy=(bar.get_x() + bar.get_width()/2, height), 
                xytext=(0, 3),               # Desplaza el texto 3 puntos arriba
                textcoords="offset points",
                ha='center', va='bottom'
            )

        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Ms Temperature (°C)')
        plt.title('Seleccione una ecuación para Ms y cierre la ventana')
        plt.tight_layout()
        plt.grid(axis='y')
        plt.show()

        print("Opciones de ecuaciones para calcular Ms:")

        for i, key in enumerate(ms_options.keys(), 1):
            print(f"{i}. {key}")
        choice = input("Ingrese el nombre exacto de la ecuación para usar Ms: ").strip()
        valid_ms = [v.real if isinstance(v, complex) else v for v in ms_options.values()]
        self.Ms = ms_options.get(
            choice,
            Ms_VanBohemen(**w) if Ms_VanBohemen(**w) in ms_options.values() else min(valid_ms)
        )
        print(f"Ms asignado con '{choice}': {self.Ms:.2f} °C")

        # ------------------------------
        # Selección de Bs
        bs_options = {

            'Bohemen': 839 - 86 * self.Mn - 23 * self.Si - 67 * self.Cr - 75 * self.Mo - 33 * self.Ni - 270 * (1 - np.exp(-1.33 * self.C)),
            'Steven_Hyanes': (830 - 270 * self.C - 90 * self.Mn - 37 * self.Ni - 70 * self.Cr - 83 * self.Mo),
            'Lee_Matt': 745 - 110 * self.C - 59 * self.Mn - 39 * self.Ni - 68 * self.Cr - 106 * self.Mo + 17 * self.Ni * self.Mn + 6 * (self.Cr**2) + 29 * (self.Mo**2),
            'Zhao1': 630 - 45 * self.Mn - 40 * w.get('V', 0) - 35 * self.Si - 30 * self.Cr - 25 * self.Mo - 20 * self.Ni - 15 * w.get('W', 0),
            'Bodnaretal': (844 - 597 * self.C - 63 * self.Mn - 16 * self.Ni - 78 * self.Cr),
            'Kirkaldy_Venugopalan': (656 - 57.7 * self.C - 75 * self.Si - 35 * self.Mn - 15.3 * self.Ni - 34 * self.Cr - 41.2 * self.Mo),
            'Lee': (732 - 202 * self.C + 216 * self.Si - 85 * self.Mn - 37 * self.Ni - 47 * self.Cr - 39 * self.Mo),
        }

        plt.figure(figsize=(10, 4))
        
        bars = plt.bar(bs_options.keys(), bs_options.values(), color='seagreen')
        for bar in bars:
            height = bar.get_height()
            plt.annotate(
                f"{height:.2f}",
                xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom'
            )

        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Bs Temperature (°C)')
        plt.title('Seleccione una ecuación para Bs y cierre la ventana')
        plt.tight_layout()
        plt.grid(axis='y')
        plt.show()

        print("\nOpciones para Bs:")
        for i, key in enumerate(bs_options.keys(), 1): print(f"{i}. {key}")
        choice = input("Ingrese el nombre exacto de la ecuación para usar Bs: ").strip()
        valid_bs = [v.real if isinstance(v, complex) else v for v in bs_options.values()]
        self.Bs = bs_options.get(choice, min(valid_bs))
        print(f"Bs asignado con '{choice}': {self.Bs:.2f} °C")

        # ------------------------------
        # Selección de Ac1
        ac1_options = {

            'Grange': (1333 - 25 * self.Mn + 40 * self.Si + 17.9 * self.Cr - 14.2 * self.Ni - 32) / 1.8,
            'Andrews': 723 - 16.9 * self.Ni + 29.1 * self.Si + 6.38 * w.get('W', 0) - 10.7 * self.Mn + 16.9 * self.Cr,
            'Eldis': (712 - 17.8 * self.Mn - 19.1 * self.Ni + 20.1 * self.Si + 11.9 * self.Cr + 9.8 * self.Mo),
            'Hougardy': (739 - 22 * self.C + 2 * self.Si - 7 * self.Mn + 14 * self.Cr + 13 * self.Mo - 13 * self.Ni),
            'Trzaska': 739 - 22.8 * self.C - 6.8 * self.Mn + 18.2 * self.Si + 11.7 * self.Cr - 15 * self.Ni - 6.4 * self.Mo - 5 * w.get('V', 0) - 28 * w.get('Cu', 0),
        }
        plt.figure(figsize=(10, 4))
        bars = plt.bar(ac1_options.keys(), ac1_options.values(), color='orange')

        
        for bar in bars:
            height = bar.get_height()
            plt.annotate(
                f"{height:.2f}",
                xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom'
            )

        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Ac1 Temperature (°C)')
        plt.title('Seleccione una ecuación para Ac1 y cierre la ventana')
        plt.tight_layout()
        plt.grid(axis='y')
        plt.show()
        print("\nOpciones para Ac1:")
        for i, key in enumerate(ac1_options.keys(), 1): print(f"{i}. {key}")
        choice = input("Ingrese el nombre exacto de la ecuación para usar Ac1: ").strip()
        valid_ac1 = [v.real if isinstance(v, complex) else v for v in ac1_options.values()]
        self.Ae1 = ac1_options.get(choice, min(valid_ac1))
        print(f"Ac1 asignado con '{choice}': {self.Ae1:.2f} °C")

        # ------------------------------
        # Selección de Ac3
        ac3_options = {

            'Kirkaldy_Baganis': (1115 - 150.3 * self.C + 216 * (0.765 - self.C) ** 4.26) - 273,
            'Kirkaldy_Baganis3': (1127 - 179 * self.C - 14 * self.Mn - 23 * self.Cr - 15 * self.Ni + 22 * self.Si) - 273,
            'Ouchu_Sampei': 910 - (203 * np.sqrt(abs(self.C))) + (44.7 * self.Si) - (30 * self.Mn) - (11 * self.Cr) + (31.5 * self.Mo) + (104 * w.get('V', 0)) + (400 * w.get('Al', 0)),
            'Andrews': 910 - (203 * np.sqrt(abs(self.C))) + (44.7 * self.Si) - (30 * self.Mn) + (11 * self.Cr) + (31.5 * self.Mo) + (104 * w.get('V', 0)) - (400 * w.get('Al', 0)) - (15.2 * self.Ni) + (13.1 * w.get('W', 0)) + (20 * w.get('Cu', 0)) - (400 * w.get('Ti', 0)),        
        }
        plt.figure(figsize=(10, 4))
        bars = plt.bar(ac3_options.keys(), ac3_options.values(), color='cornflowerblue')

        
        for bar in bars:
            height = bar.get_height()
            plt.annotate(
                f"{height:.2f}",
                xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom'
            )

        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Ac3 Temperature (°C)')
        plt.title('Seleccione una ecuación para Ac3 y cierre la ventana')
        plt.tight_layout()
        plt.grid(axis='y')
        plt.show()
        print("\nOpciones para Ac3:")
        for i, key in enumerate(ac3_options.keys(), 1): print(f"{i}. {key}")
        choice = input("Ingrese el nombre exacto de la ecuación para usar Ac3: ").strip()
        valid_ac3 = [v.real if isinstance(v, complex) else v for v in ac3_options.values()]
        self.Ae3 = ac3_options.get(choice, max(valid_ac3))
        print(f"Ac3 asignado con '{choice}': {self.Ae3:.2f} °C")

        self.FC = FC(**w)
        self.PC = PC(**w)
        self.BC = BC(**w)
        # self.Ae3 = Ae3_Andrews(**w)
        # self.Ae1 = Ae1_Andrews(**w)
        # self.Ae3 = Ae3_Grange(**w)
        # self.Ae1 = Ae1_Grange(**w)
        # self.Bs = Bs_Li(**w)
        # self.Ms = Ms_Andrews(**w)
        # self.Bs = Bs_VanBohemen(**w)
        
        self.alpha_martensite = alpha_martensite_VanBohemen(**w)

        # Hardness
        self.Hv_martensite = lambda phi700: Hv_martensite(phi700, **w)
        self.Hv_bainite = lambda phi700: Hv_bainite(phi700, **w)
        self.Hv_ferrite_pearlite = lambda phi700: Hv_ferrite_pearlite(phi700, **w)

    def format_composition(self, vmin=0):
        fmt = []
        for k, v in self.w.items():
            if v > vmin:
                fmt.append('{:g}{:}'.format(v, k))
        fmt.insert(0, 'Fe')  # assumes it is steel
        fmt = '-'.join(fmt) + ' (wt.%)'
        fmt += '\nASTM grain size {:}'.format(self.gs)
        return fmt


class SigmoidalFunction(object):
    """
    Abstract class for S(X) and I(X) functions. Once initialized,
    calculates values of the function for a given [xmin, xmax]
    interval and then creates a spline interpolator. The returned
    values are calculated by the interpolator. This method has the
    advantage of being able to process x as an array (or any other
    kind of iterator)
    """
    tck = None  # tck spline knots, coefficients and degree
    tck_inv = None  # spline parameters of the inverse function

    def __new__(cls, x):
        """
        __new__ behaviour is modified to return the interpolated
        value of the function
        """
        if cls is SigmoidalFunction:
            raise TypeError("Can't instantiate abstract class SigmoidalFunction")

        # Check for compulsory subclass attributes
        for var in ['xmin', 'xmax', 'ymin', 'ymax', 'n']:
            if not hasattr(cls, var):
                raise NotImplementedError(
                    'Class {} lacks required `{}` class attribute'.format(cls, var))

        # This is were S(X) or I(X) is returned
        return cls.val(x)

    @staticmethod
    def f(x):
        """
        Function to be integrated
        """
        pass

    @classmethod
    def val(cls, x):
        """
        Evaluates SigmoidalFunction(x)
        """
        if hasattr(x, '__iter__') and not isinstance(x, str):
            x = np.array(x)
            xmin = x[x > 0].min()
        else:
            xmin = x
        xmin = min(cls.xmin, xmin)

        # init spline if not initialized yet or if xmin is lower than lower bound
        if xmin < cls.xmin or cls.tck is None:
            cls.xmin = xmin
            cls.init_spline()

        return splev(x, cls.tck)

    @classmethod
    def inv(cls, y):
        """
        Evaluates inverse function SigmoidalFunction^-1(y)
        """
        if hasattr(y, '__iter__') and not isinstance(y, str):
            y = np.array(y)
            ymin, ymax = y.min(), y.max()
        else:
            ymin, ymax = y, y

        if cls.tck_inv is None:
            cls.init_spline()

        if ymin < cls.ymin or ymax > cls.ymax:
            print('Be careful! y value out of bounds [{:g}:{:g}]. '
                  'Returned value is an extrapolation'.format(cls.ymin, cls.ymax))

        return splev(y, cls.tck_inv)

    @classmethod
    def init_spline(cls):
        """
        Initializes spline
        """
        X = np.linspace(cls.xmin, cls.xmax, cls.n)
        Y = np.array([integrate.quad(cls.f, 0, x)[0] for x in X])
        cls.ymin = Y.min()
        cls.ymax = Y.max()
        cls.tck = splrep(X, Y)
        cls.tck_inv = splrep(Y, X)


class S(SigmoidalFunction):
    n = 999
    xmin = 0.001
    xmax = 0.999
    ymin = 0.02638507
    ymax = 2.02537893

    """
    S(X) function calculated using numerical integration and
    spline interpolation
    """
    @staticmethod
    def f(x):
        return 1./(x**(0.4*(1. - x))*(1. - x)**(0.4*x))


class I(SigmoidalFunction):
    """
    I(X) function calculated using numerical integration and
    spline interpolation
    """
    n = 999
    xmin = 0.001
    xmax = 0.999
    ymin = 0.29961765
    ymax = 4.05928646

    @staticmethod
    def f(x):
        return 1./(x**(2.*(1. - x)/3.)*(1. - x)**(2.*x/3.))


class PhaseTransformation(object):
    """
    Abstract class for calculating kinetics of diffusional phase
    transformations
    """

    def __init__(self, alloy):
        self.alloy = alloy
        self.initialize()
        # Check for compulsory object attributes
        for var in ['comp_factor', 'Ts', 'Tf', 'Hv']:
            if not hasattr(self, var):
                raise NotImplementedError(
                    'Object {} lacks required `{}` attribute'.format(self, var))

    @classmethod
    def __init_subclass__(cls):
        # Check for compulsory subclass attributes
        for var in ['Q', 'n1', 'n2']:
            if not hasattr(cls, var):
                raise NotImplementedError(
                    'Class {} lacks required `{}` class attribute'.format(cls, var))

    @abstractmethod
    def initialize(self):
        pass

    def get_transformation_factor(self, T):
        """
        Calculates the transformation factor for a given temperature T

        Parameters
        ----------
        T : float or iterable
            Temperature. It can be provided as an array

        Returns
        -------
        F : float or iterable
            Transformation factor with same shape as T
        """
        return self.comp_factor/(2**(self.n1*self.alloy.gs)*(self.Ts - T)**self.n2*np.exp(-self.Q/(R*(T + K))))

    def get_transformation_time(self, T, f):
        """
        Calculates the time necessary for the material to transform to a
        fraction f at a temperature T

        Parameters
        ----------
        T : float or iterable
            Temperature. It can be provided as an array
        f : float or iterable
            Transformed fraction. If iterable, has to have the same shape
            as T

        Returns
        -------
        t : float or iterable
            Transformation time with same shape as T
        """
        return S(f)*self.get_transformation_factor(T)

    def get_transformation_temperature(self, Tini, Tfin, cooling_rate, f, dT=1.0):
        """
        Calculates the temperature for the material to transform to a
        fraction f during the cooling from Tini to Tfin at a cooling rate
        cooling_rate

        Parameters
        ----------
        Tini : float
            Initial temperature
        Tfin : float
            Final temperature
        cooling_rate : float or iterable
            Cooling rate(s). It can be provided as an array
        f : float or iterable
            Transformed fraction. If iterable, has to have the same shape
            as cooling_rate

        Returns
        -------
        T : float or iterable
            Transformation temperature with same shape as cooling_rate
        """
        dt = dT/np.array(cooling_rate)
        nt = len(dt) if hasattr(dt, '__len__') else 1
        T = np.arange(Tini, Tfin, -dT)
        nucleation_time = np.full((nt, len(T)), 0, dtype=float)

        filtr = T < self.Ts
        nucleation_time[:, filtr] = np.outer(dt, 1./self.get_transformation_factor(T[filtr]))
        nucleation_time = nucleation_time.cumsum(axis=1)

        Tt = np.full(nt, np.nan, dtype=float)  # Transformation temperature for a given fraction f

        # Check for indices of nucleation_time larger than threshold S(f)
        # First occurrence is the transformation temperature
        Sf = S(f)
        for i, n_time in enumerate(nucleation_time):
            idx, = np.where(n_time >= Sf)
            if len(idx) > 0:
                Tt[i] = T[idx[0]]

        return float(Tt) if nt == 1 else Tt

    def get_transformed_fraction(self, t, T, n=1000):
        """
        Calculates the transformed fraction for a given thermal cycle T(t)

        Parameters
        ----------
        t : iterable
            Time
        T : iterable
            Temperatures at the instants of time t
        n : int (optional)
            Number of points at which the transformed fractions are
            calculated
            Default: 1000

        Returns
        -------
        t, T, f : tuple
            Tuple with arrays time, temperature, phase fraction evaluated
            at n points
        """
        if len(t) > 3:
            # Fits T(t) by spline
            def t2T(t_): return splev(t_, splrep(t, T))
        else:
            # Uses linear interpolator
            t2T = interp1d(t, T)

        # To ensure convergence of the algorithm, the T(t) thermal cycle is
        # adjusted by a spline and the nucleation time is calculated by
        # increments dt = (max(t) - min(t))/n
        dt = (max(t) - min(t))/(n - 1)
        t = np.linspace(min(t), max(t), n)
        T = t2T(t)
        nucleation_time = np.full(t.shape, 0, dtype=float)
        f = np.full(T.shape, 0, dtype=float)

        # Calculates nucleation time only for T lower than transformation
        # start temperature and higher than Tf
        filtr = (T < self.Ts) & (T > self.Tf)
        if np.any(filtr):
            nucleation_time[filtr] = dt/self.get_transformation_factor(T[filtr])
            nucleation_time = nucleation_time.cumsum()
            if T[0] < self.Ts:
                # This is the factor corresponding to the transformed fraction at t[0]
                nucleation_time += min(t)/self.get_transformation_factor(T[0])

            # New filter: calculates f only for nucleation_time inside the bounds
            # of S.inv(y)
            filtr = (nucleation_time >= S.ymin) & (nucleation_time <= S.ymax)
            if np.any(filtr):
                f[filtr] = S.inv(nucleation_time[filtr])
                f[nucleation_time < S.ymin] = 0
                f[nucleation_time > S.ymax] = 1

        return t, T, f


class Ferrite(PhaseTransformation):
    """
    Austenite to ferrite phase transformation
    """
    Q = 27500*4.184  # activation energy
    n1 = 0.41  # exponential factor 1
    n2 = 3  # exponential factor 2

    def initialize(self):
        self.comp_factor = self.alloy.FC  # composition factor for calculating transformation time
        self.Ts = self.alloy.Ae3  # transformation start temperature
        self.Tf = self.alloy.Bs  # transformation finish temperature
        self.Hv = self.alloy.Hv_ferrite_pearlite


class Pearlite(PhaseTransformation):
    """
    Austenite to pearlite phase transformation
    """
    Q = 27500*4.184  # activation energy
    n1 = 0.32  # exponential factor 1
    n2 = 3  # exponential factor 2

    def initialize(self):
        self.comp_factor = self.alloy.PC  # composition factor for calculating transformation time
        self.Ts = self.alloy.Ae1  # transformation start temperature
        self.Tf = self.alloy.Bs  # transformation finish temperature
        self.Hv = self.alloy.Hv_ferrite_pearlite


class Bainite(PhaseTransformation):
    """
    Austenite to bainite phase transformation
    """
    Q = 27500*4.184  # activation energy
    n1 = 0.29  # exponential factor 1
    n2 = 2  # exponential factor 2

    def initialize(self):
        self.comp_factor = self.alloy.BC  # composition factor for calculating transformation time
        self.Ts = self.alloy.Bs  # transformation start temperature
        self.Tf = self.alloy.Ms  # transformation finish temperature
        self.Hv = self.alloy.Hv_bainite


class Martensite:
    """
    Athermal austenite to martensite transformation
    """

    def __init__(self, alloy):
        self.alloy = alloy
        self.Ts = self.alloy.Ms
        self.Hv = self.alloy.Hv_martensite

    def get_transformed_fraction(self, t, T, n=1000):
        """
        Calculates the transformed martensite fraction for a given thermal
        cycle T(t) using the Koistinen-Marburger equation

        Parameters
        ----------
        t : iterable
            Time
        T : iterable
            Temperatures at the instants of time t
        n : int (optional)
            Number of points at which the transformed fractions are
            calculated
            Default: 1000

        Returns
        -------
        t, T, f : tuple
            Tuple with arrays time, temperature, phase fraction evaluated
            at n points
        """
        if len(t) > 3:
            # Fits T(t) by spline
            def t2T(t_): return splev(t_, splrep(t, T))
        else:
            # Uses linear interpolator
            t2T = interp1d(t, T)

        t = np.linspace(min(t), max(t), n)
        T = t2T(t)
        f = np.full(T.shape, 0, dtype=float)

        filtr = T < self.alloy.Ms
        if np.any(filtr):
            f[filtr] = 1 - np.exp(-self.alloy.alpha_martensite*(self.alloy.Ms - T[filtr]))
        return t, T, f


class TransformationDiagrams:
    """
    Transformation diagrams class
    """

    colors_dict = dict(ferrite='#1f77b4', pearlite='#ff7f0e', bainite='#2ca02c',
                       martensite='#d62728', austenite='#9467bd')
    columns_label_dict = dict(t='Time (s)', T=u'Temperature (°C)',
                              ferrite='Ferrite', pearlite='Pearlite', bainite='Bainite',
                              martensite='Martensite', austenite='Austenite')

    def __init__(self, alloy):
        self.alloy = alloy

        self.ferrite = Ferrite(self.alloy)
        self.pearlite = Pearlite(self.alloy)
        self.bainite = Bainite(self.alloy)
        self.martensite = Martensite(self.alloy)

        self.df_TTT = None
        self.df_CCT = None

    def get_transformed_fraction(self, t, T, n=1000):
        """
        Calculates transformation curves for a given T(t) thermal cycle

        Parameters
        ----------
        t : iterable
            Time
        T : iterable
            Temperatures at the instants of time t
        n : int (optional)
            Number of points at which the transformed fractions are
            calculated
            Default: 1000

        Returns
        -------
        f : pandas DataFrame
            DataFrame containing the time, temperature, and phase fractions
            of ferrite, pearlite, bainite, martensite, and austenite at n
            points, and also the Vickers hardness for each data point
        """
        # Uncorrected phase fractions
        _, _, f_ferr = self.ferrite.get_transformed_fraction(t, T, n)
        _, _, f_pear = self.pearlite.get_transformed_fraction(t, T, n)
        _, _, f_bain = self.bainite.get_transformed_fraction(t, T, n)
        t, T, f_mart = self.martensite.get_transformed_fraction(t, T, n)

        f_ferr_inc = np.zeros(f_ferr.shape)
        f_pear_inc = np.zeros(f_pear.shape)
        f_bain_inc = np.zeros(f_bain.shape)
        f_mart_inc = np.zeros(f_mart.shape)
        f_ferr_inc[1:] = np.diff(f_ferr)
        f_pear_inc[1:] = np.diff(f_pear)
        f_bain_inc[1:] = np.diff(f_bain)
        f_mart_inc[1:] = np.diff(f_mart)

        f = pd.DataFrame(columns=['t', 'T', 'ferrite', 'pearlite',
                                  'bainite', 'martensite', 'austenite'])
        f['t'] = t
        f['T'] = T
        f.fillna(0, inplace=True)
        f.loc[0, 'ferrite'] = f_ferr[0]
        f.loc[0, 'pearlite'] = f_pear[0]
        f.loc[0, 'bainite'] = f_bain[0]
        f.loc[0, 'martensite'] = f_mart[0]
        f.loc[0, 'austenite'] = 1. - f_ferr[0] - f_pear[0] - f_bain[0] - f_mart[0]

        def f1(i, x, y, z, w):
            if f_ferr[i] < 1:
                return f.loc[i-1, 'ferrite'] + f_ferr_inc[i]*(1 - x - y - z - w)/(1 - f_ferr[i]) - x
            else:
                return f.loc[i-1, 'ferrite'] + f_ferr_inc[i]*(1 - y - z - w) - x

        def f2(i, x, y, z, w):
            if f_pear[i] < 1:
                return f.loc[i-1, 'pearlite'] + f_pear_inc[i]*(1 - x - y - z - w)/(1 - f_pear[i]) - y
            else:
                return f.loc[i-1, 'pearlite'] + f_pear_inc[i]*(1 - x - z - w) - y

        def f3(i, x, y, z, w): return f.loc[i-1, 'bainite'] + f_bain_inc[i]*(1 - x - y - w) - z

        def f4(i, x, y, z, w): return f.loc[i-1, 'martensite'] + f_mart_inc[i]*(1 - x - y - z) - w

        for i in range(len(f))[1:]:
            x0 = [f.loc[i-1, 'ferrite'], f.loc[i-1, 'pearlite'],
                  f.loc[i-1, 'bainite'], f.loc[i-1, 'martensite']]

            # Solves system of non-linear equations to get corrected phase fractions
            res = root(lambda x: [f1(i, *x), f2(i, *x), f3(i, *x), f4(i, *x)], x0=x0)

            f.loc[i, 'ferrite'] = res.x[0]
            f.loc[i, 'pearlite'] = res.x[1]
            f.loc[i, 'bainite'] = res.x[2]
            f.loc[i, 'martensite'] = res.x[3]
            f.loc[i, 'austenite'] = 1. - res.x.sum()

        phi700 = None

        try:
            T2t = interp1d(T, t)
            # Gets cooling rate at 700 oC
            phi700 = 2./(T2t(699.) - T2t(701.))
            if phi700 == 0:
                phi700 = None
        except ValueError:
            # This might happen for isothermal heat treatments
            pass

        if phi700 is not None:
            f['Hv'] = f['martensite']*self.martensite.Hv(phi700) + f['bainite']*self.bainite.Hv(phi700) + \
                (f['ferrite'] + f['pearlite'])*self.ferrite.Hv(phi700)
        else:
            f['Hv'] = np.nan

        return f.round(12)

    def draw_thermal_cycle(self, ax, t, T, n=100, **kwargs):
        """
        Draw thermal cycle (cooling curve) over AxesSubplot object

        Parameters
        ----------
        ax : AxesSubplot object
            Axis where to draw the thermal cycle curve
        t : iterable
            Time
        T : iterable
            Temperatures at the instants of time t
        n : int (optional)
            Number of points at which the T(t) points are evaluated by
            interpolation
            Default: 100

        Returns
        -------
        line : Line2D object
            Line2D object corresponding to drawn curve
        """

        if len(t) > 3:
            # Fits T(t) by spline
            def t2T(t_): return splev(t_, splrep(t, T))
        else:
            # Uses linear interpolator
            t2T = interp1d(t, T)

        t = np.linspace(min(t), max(t), n)
        T = t2T(t)

        kw = dict(color='k', ls='--')
        kw.update(kwargs)

        return ax.plot(t, T, **kw)

    def TTT(self, fs=1e-2, ff=.99, ax=None, **kwargs):
        """
        Plot TTT diagram

        Parameters
        ----------
        fs : float (optional)
            Transformation start phase fraction
            Default: 1e-2 (1%)
        fs : float (optional)
            Transformation finish phase fraction
            Default: .99 (99%)
        ax : AxesSubplot object (optional)
            Axis where to plot the TTT curve. If None, then a new axis is
            created
            Default: None
        **kwargs :
            Optional arguments passed to ax.plot(*args, **kwargs)

        Returns
        -------
        ax : AxesSubplot object
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 6))
        else:
            fig = ax.get_figure()

        # Ferrite
        T = np.arange(self.alloy.Bs, self.alloy.Ae3)
        ts = self.ferrite.get_transformation_time(T, fs)  # start
        tf = self.ferrite.get_transformation_time(T, ff)  # finish
        ax.plot(ts, T, color=self.colors_dict['ferrite'],
                label='Ferrite {:g}%'.format(100*fs), **kwargs)
        ax.plot(tf, T, color=self.colors_dict['ferrite'], ls='--',
                label='Ferrite {:g}%'.format(100*ff), **kwargs)
        df_ferrite = pd.DataFrame(dict(T_ferrite=T, ts_ferrite=ts, tf_ferrite=tf))

        # Pearlite
        T = np.arange(self.alloy.Bs, self.alloy.Ae1)
        ts = self.pearlite.get_transformation_time(T, fs)
        tf = self.pearlite.get_transformation_time(T, ff)
        ax.plot(ts, T, color=self.colors_dict['pearlite'],
                label='Pearlite {:g}%'.format(100*fs), **kwargs)
        ax.plot(tf, T, color=self.colors_dict['pearlite'], ls='--',
                label='Pearlite {:g}%'.format(100*ff), **kwargs)
        df_pearlite = pd.DataFrame(dict(T_pearlite=T, ts_pearlite=ts, tf_pearlite=tf))

        # Bainite
        T = np.arange(self.alloy.Ms, self.alloy.Bs)
        ts = self.bainite.get_transformation_time(T, fs)
        tf = self.bainite.get_transformation_time(T, ff)
        ax.plot(ts, T, color=self.colors_dict['bainite'],
                label='Bainite {:g}%'.format(100*fs), **kwargs)
        ax.plot(tf, T, color=self.colors_dict['bainite'], ls='--',
                label='Bainite {:g}%'.format(100*ff), **kwargs)
        df_bainite = pd.DataFrame(dict(T_bainite=T, ts_bainite=ts, tf_bainite=tf))

        self.df_TTT = pd.concat([df_ferrite, df_pearlite, df_bainite], axis=1)

        # Draws Ae1 and Ae3 lines
        ax.axhline(self.alloy.Ae3, xmax=.1, color=self.colors_dict['ferrite'], ls=':')
        ax.axhline(self.alloy.Ae1, xmax=.1, color=self.colors_dict['pearlite'], ls=':')

        # Draws Bs and Ms lines
        ax.axhline(self.alloy.Bs, color=self.colors_dict['bainite'], ls=':')
        ax.axhline(self.alloy.Ms, color=self.colors_dict['martensite'])

        ax.set_xscale('log')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel(u'Temperature (°C)')
        ax.set_title(self.alloy.format_composition())

        xmin = ax.get_xlim()[0]
        ax.text(xmin*1.5, self.alloy.Ae3, 'Ae3',
                color=self.colors_dict['ferrite'], ha='left', va='bottom')
        ax.text(xmin*1.5, self.alloy.Ae1, 'Ae1',
                color=self.colors_dict['pearlite'], ha='left', va='bottom')
        ax.text(xmin*1.5, self.alloy.Bs, 'Bs',
                color=self.colors_dict['bainite'], ha='left', va='bottom')
        ax.text(xmin*1.5, self.alloy.Ms, 'Ms',
                color=self.colors_dict['martensite'], ha='left', va='bottom')

        ax.legend(loc='upper center', ncol=3, bbox_to_anchor=(0.5, -.15))
        fig.subplots_adjust(bottom=.2)

        return ax

    def CCT(self, Tini=900, fs=1e-2, ff=.99, phi_min=1e-4, phi_max=1e4, phi_steps=420, ax=None, **kwargs):
        """
        Plot CCT diagram

        Parameters
        ----------
        fs : float (optional)
            Transformation start phase fraction
            Default: 1e-2 (1%)
        fs : float (optional)
            Transformation finish phase fraction
            Default: .99 (99%)
        ax : AxesSubplot object (optional)
            Axis where to plot the TTT curve. If None, then a new axis is
            created
            Default: None
        **kwargs :
            Optional arguments passed to ax.plot(*args, **kwargs)

        Returns
        -------
        ax : AxesSubplot object
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 6))
        else:
            fig = ax.get_figure()

        cooling_rates = 10**np.linspace(np.log10(phi_min), np.log10(phi_max), phi_steps)
        draw_cooling = kwargs.get('draw_cooling', True)

        # Ferrite
        Ts = self.ferrite.get_transformation_temperature(
            Tini, self.alloy.Bs, cooling_rates, fs)  # start
        Tf = self.ferrite.get_transformation_temperature(
            Tini, self.alloy.Bs, cooling_rates, ff)  # finish
        ax.plot(Ts/cooling_rates, Ts,
                color=self.colors_dict['ferrite'], label='Ferrite {:g}%'.format(100*fs), **kwargs)
        ax.plot(Tf/cooling_rates, Tf, color=self.colors_dict['ferrite'],
                ls='--', label='Ferrite {:g}%'.format(100*ff), **kwargs)

        # Pearlite
        Ts = self.pearlite.get_transformation_temperature(Tini, self.alloy.Bs, cooling_rates, fs)
        Tf = self.pearlite.get_transformation_temperature(Tini, self.alloy.Bs, cooling_rates, ff)
        ax.plot(Ts/cooling_rates, Ts, color=self.colors_dict['pearlite'],
                label='Pearlite {:g}%'.format(100*fs), **kwargs)
        ax.plot(Tf/cooling_rates, Tf, color=self.colors_dict['pearlite'],
                ls='--', label='Pearlite {:g}%'.format(100*ff), **kwargs)

        # Bainite
        Ts = self.bainite.get_transformation_temperature(Tini, self.alloy.Ms, cooling_rates, fs)
        Tf = self.bainite.get_transformation_temperature(Tini, self.alloy.Ms, cooling_rates, ff)
        ax.plot(Ts/cooling_rates, Ts,
                color=self.colors_dict['bainite'], label='Bainite {:g}%'.format(100*fs), **kwargs)
        ax.plot(Tf/cooling_rates, Tf, color=self.colors_dict['bainite'],
                ls='--', label='Bainite {:g}%'.format(100*ff), **kwargs)

        ax.axhline(self.alloy.Ae3, xmax=.1, color=self.colors_dict['ferrite'], ls=':')
        ax.axhline(self.alloy.Ae1, xmax=.1, color=self.colors_dict['pearlite'], ls=':')

        ax.axhline(self.alloy.Bs, color=self.colors_dict['bainite'], ls=':')
        ax.axhline(self.alloy.Ms, color=self.colors_dict['martensite'])

        # Draw cooling curves
        if draw_cooling:
            for cooling_rate in cooling_rates[::10]:
                T = np.linspace(Tini, 25, 100)
                t = (Tini - T)/cooling_rate
                kw = dict(lw=.5)
                kw.update(kwargs)
                ax.plot(t, T, 'k:', **kw)

        ax.set_xscale('log')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel(u'Temperature (°C)')
        ax.set_title(self.alloy.format_composition())

        xmin = ax.get_xlim()[0]
        ax.text(xmin*1.5, self.alloy.Ae3, 'Ae3',
                color=self.colors_dict['ferrite'], ha='left', va='bottom')
        ax.text(xmin*1.5, self.alloy.Ae1, 'Ae1',
                color=self.colors_dict['pearlite'], ha='left', va='bottom')
        ax.text(xmin*1.5, self.alloy.Bs, 'Bs',
                color=self.colors_dict['bainite'], ha='left', va='bottom')
        ax.text(xmin*1.5, self.alloy.Ms, 'Ms',
                color=self.colors_dict['martensite'], ha='left', va='bottom')

        ax.legend(loc='upper center', ncol=3, bbox_to_anchor=(0.5, -.15))
        fig.subplots_adjust(bottom=.2)

        return ax

    def plot_phase_fraction(self, t, T, n=1000, xaxis='t', ax=None, **kwargs):
        """
        Plot phase fractions for a given thermal cycle T(t)

        Parameters
        ----------
        t : iterable
            Time
        T : iterable
            Temperatures at the instants of time t
        n : int (optional)
            Number of points at which the T(t) points are evaluated by
            interpolation
            Default: 1000
        xaxis : string (optional)
            Variable to be represented on the x-axis. Possible values are:
            'index', t', 'T', 'ferrite', 'pearlite', 'bainite', 'martensite',
            and 'austenite'
            Default: 't'
        ax : AxesSubplot object (optional)
            Axis where to plot the phase fraction curves. If None, then a
            new axis is created
            Default: None

        Returns
        -------
        ax : AxesSubplot object
        """
        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.get_figure()

        if len(t) > 3:
            # Fits T(t) by spline
            def t2T(t_): return splev(t_, splrep(t, T))
        else:
            # Uses linear interpolator
            t2T = interp1d(t, T)

        t = np.linspace(min(t), max(t), n)
        T = t2T(t)

        f = self.get_transformed_fraction(t, T, n)
        if f['ferrite'].max() > 0:
            ax.plot(f[xaxis], f['ferrite'], color=self.colors_dict['ferrite'], label='Ferrite')
        if f['pearlite'].max() > 0:
            ax.plot(f[xaxis], f['pearlite'], color=self.colors_dict['pearlite'], label='Pearlite')
        if f['bainite'].max() > 0:
            ax.plot(f[xaxis], f['bainite'], color=self.colors_dict['bainite'], label='Bainite')
        if f['martensite'].max() > 0:
            ax.plot(f[xaxis], f['martensite'],
                    color=self.colors_dict['martensite'], label='Martensite')
        if f['austenite'].max() > 0:
            ax.plot(f[xaxis], f['austenite'], color=self.colors_dict['austenite'], label='Austenite')

        if not np.isnan(f.iloc[-1]['Hv']):
            T_ref = 25
            try:
                Hv_ref = interp1d(f['T'], f['Hv'])(T_ref)
            except ValueError:
                T_ref, Hv_ref = f.iloc[-1]['T'], f.iloc[-1]['Hv']

            ax.text(.95, .95, u'Hardness for phase fractions at {:.1f} °C: {:.0f} HV'.format(T_ref, Hv_ref),
                    transform=ax.transAxes, ha='right', va='top',
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

        ax.set_xlabel(self.columns_label_dict[xaxis])
        ax.set_ylabel('Phase fraction')
        ax.legend()

        return ax
