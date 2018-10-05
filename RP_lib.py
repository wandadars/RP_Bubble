#!python
"""
my starting point: http://pastebin.com/JvzaaUGm

integrating the equation system
Rdot = vdot
vdot = f(R,v)

the Rayleigh-Plesset equation:
    R*ddR + 3dR^2/2 = 1/rho ( ...... )
turns into
    Rdotdot = vdot = -3dR^2/(2R) + 1/(rho*R) * ( ...... )

dynamic viscosity eta = nu * rho   with nu the kinematic viscosity

now producing a nice plot for a bubble in acetone at different driving amplitudes

Turning off and on the radiation loss shows how important it is: without it
there is no abrupt decay in the rebounding amplitude for the first rebound.

Markus Stokmaier, Weimar, March 2018
"""
import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt
from cPickle import Pickler, Unpickler

def sphere_volume(r):
    return (4./3.)*np.pi*r**3

class Bubble(object):
    def __init__(self):
        """
        now own shit
        """
        self.R0 = 0.5e-4       # equilibrium radius
        self.R_start = 0.5e-4       # initial radius
        self.dR_start = 0.          # initial interface speed
        #self.Tamb = 298.       # ambient temperature
        self.p0 = 101325.      # ambient pressure = p_inf, i.e.pressure far away where r--> inf
        #self.pvap = 31.7e2     # vapour pressure in Pa (water) 31.7 hPa at 25 C
        #self.s = 0.0728        # surface tension in N/m (water)
        #self.rho = 998.2071    # density in kg per cubic metre (water)
        #self.nu = 1.5e-3       # viscosity in Pa s (water)  see: https://en.wikipedia.org/wiki/Water_%28data_page%29    https://en.wikipedia.org/wiki/Water_(data_page)
        #self.c = 1435.         # speed of sound in m/s
        self.pvap = 0.093*1e5  # vapour pressure in Pa (acetone)  246 hPa at 20 C
        self.s = (25.2+25*0.1120)*1e-3       # surface tension in N/m (acetone) 25.2mN/m at 25 C with T-coeff -0.1120 according to http://www.surface-tension.de/
        self.rho = 790.        # density in kg per cubic metre (acetone)
        self.nu = 0.4*1e-3        # viscosity in Pa s (acetone) 0.4 mPa s at 10 C according to http://chemister.ru/Database/properties-en.php?dbid=1&id=27
        self.c = 1174.         # speed of sound in m/s
        self.kappa = 1.4 #1.4       # polytropic index 
        self.amp = 0.6*self.p0        # amplitude of acoustic forcing
        self.f = 2e4           # acoustic driving frequency in Hz
        self.t = []  # timegrid
        self.R = []  # will contain the time series of R and dR --> 2D array
        self.Pg = [] # for time series of gas pressure
        self.t_start=0.
        self.dt_coarse=1e-9
        self.dt_fine=1e-12
        self.t_run=19e-6
        self.bubble_radiates=True

    def p_acoustic(self,t):
        return -self.amp*np.sin(2*np.pi*self.f*t)

    def dR(self, r, t):
        R = r[0]
        dR = r[1]
        p_gas = (self.p0 + 2*self.s/self.R0 - self.pvap) * (self.R0/R)**(3*self.kappa)
        p_surf = 2*self.s/R
        p_liq = p_gas + self.pvap - p_surf
        p_ext =  self.p0 + self.p_acoustic(t)
        if self.bubble_radiates and (len(self.t)>2):
            Pgdot = (self.Pg[-1]-self.Pg[-2]) / (self.t[-1]-self.t[-2])
            radiation_loss = Pgdot * R/self.c
            ddR = -3*dR**2/(2*R) + 1/(self.rho*R) * ( p_liq - 4*self.nu*dR/R - p_ext + radiation_loss)
        else:
            ddR = -3*dR**2/(2*R) + 1/(self.rho*R) * ( p_liq - 4*self.nu*dR/R - p_ext )
        return np.array([dR, ddR])

    def calculate_Pgas(self,r):
        return (self.p0 + 2*self.s/self.R0 - self.pvap) * (self.R0/r)**(3*self.kappa)

    def integrate_RK4(self):
        """fourth order Runge-Kutta scheme for time-integration"""
        func=self.dR
        t=self.t; t.append(self.t_start)
        w=self.R; w.append(np.array([self.R_start, self.dR_start]))
        self.Pg.append(self.calculate_Pgas(self.R_start))
        while t[-1]<self.t_start+self.t_run:
            if w[-1][0]<0.6*self.R0:
                if w[-1][0]<0.06*self.R0:
                    t.append(t[-1]+0.02*self.dt_fine)
                else:
                    t.append(t[-1]+self.dt_fine)
            else:
                t.append(t[-1]+self.dt_coarse)
            h=t[-1]-t[-2]
            k1=func(w[-1],t[-2])
            k2=func(w[-1]+0.5*h*k1,t[-2]+0.5*h)
            k3=func(w[-1]+0.5*h*k2,t[-2]+0.5*h)
            k4=func(w[-1]+h*k3,t[-1])
            w.append(w[-1]+(h*k1+2*h*k2+2*h*k3+h*k4)/6.)
            self.Pg.append(self.calculate_Pgas(w[-1][0]))

    def list2array(self):
        self.t=np.array(self.t)
        self.R=np.array(self.R)
        self.Pg=np.array(self.Pg)

    def pickle_self(self,suffix):
        ofile=open('pickled_bubble'+suffix+'.txt','w')
        container=Pickler(ofile)
        container.dump(self)
        ofile.close()

def unpickle_thing(path):
    ifile=open(path,'r')
    container=Unpickler(ifile)
    thing=container.load()
    ifile.close()
    return thing


