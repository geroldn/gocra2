""" Rating system class """
import os
from math import exp
import xmltodict


class RatingSystem:
    """ Rating system class """

    epsilon = 0.016
    rparms = [
        {'Gor':-2000, 'Con':116, 'A':200, },
        {'Gor':100, 'Con':116, 'A':200, },
        {'Gor':200, 'Con':110, 'A':195, },
        {'Gor':300, 'Con':105, 'A':190, },
        {'Gor':400, 'Con':100, 'A':185, },
        {'Gor':500, 'Con':95, 'A':180, },
        {'Gor':600, 'Con':90, 'A':175, },
        {'Gor':700, 'Con':85, 'A':170, },
        {'Gor':800, 'Con':80, 'A':165, },
        {'Gor':900, 'Con':75, 'A':160, },
        {'Gor':1000, 'Con':70, 'A':155, },
        {'Gor':1100, 'Con':65, 'A':150, },
        {'Gor':1200, 'Con':60, 'A':145, },
        {'Gor':1300, 'Con':55, 'A':140, },
        {'Gor':1400, 'Con':51, 'A':135, },
        {'Gor':1500, 'Con':47, 'A':130, },
        {'Gor':1600, 'Con':43, 'A':125, },
        {'Gor':1700, 'Con':39, 'A':120, },
        {'Gor':1800, 'Con':35, 'A':115, },
        {'Gor':1900, 'Con':31, 'A':110, },
        {'Gor':2000, 'Con':27, 'A':105, },
        {'Gor':2100, 'Con':24, 'A':100, },
        {'Gor':2200, 'Con':21, 'A':95, },
        {'Gor':2300, 'Con':18, 'A':90, },
        {'Gor':2400, 'Con':15, 'A':85, },
        {'Gor':2500, 'Con':13, 'A':80, },
        {'Gor':2600, 'Con':11, 'A':75, },
        {'Gor':2700, 'Con':10, 'A':70, },
    ]


    @classmethod
    def get_parms(cls, rating):
        """ Get parameters for rating calculation """
        rp_low = cls.rparms[0]
        rp_high = cls.rparms[0]
        for rp in cls.rparms:
            if rating < rp['Gor']:
                rp_high = rp
                break
            rp_low = rp
        if rp_high == None:
            rp_high = rp_low
        r1 = rp_low['Gor']
        r2 = rp_high['Gor']
        c1 = rp_low['Con']
        c2 = rp_high['Con']
        a1 = rp_low['A']
        a2 = rp_high['A']
        c = c1 + (rating - r1) * (c2 - c1) / (r2 - r1)
        a = a1 + (rating - r1) * (a2 - a1) / (r2 - r1)
        return {'Con': c, 'A': a}

    @classmethod
    def calculate_gain(cls, color, rating, oppRating, handicap, bWin):
        """ Calculate rating gain from game result """
        e = cls.epsilon
        adjRating = rating
        adjOppRating = oppRating
        if handicap > 0:
            if color == 'B':
                adjRating = rating + 100*(handicap - 0.5)
            elif color == 'W':
                adjOppRating = oppRating + 100*(handicap - 0.5)
            else:
                print('Illegal color')
                return None
        if adjRating < adjOppRating:
            a = cls.get_parms(adjRating)['A']
        else:
            a = cls.get_parms(adjOppRating)['A']
        c = cls.get_parms(rating)['Con']
        diff = adjOppRating - adjRating
        se = max(0.0, 1 / (exp(diff/a) + 1) - e/2)
        gain = c*(bWin - se)
        #print('rating: {0:4.0f}, oppRating: {4:4.0f}, con: {1:7.3f}, a: {2:7.3f}, se: {3:6.3f}, epsilon: {5:6.3f}, gain: {6:6.1f}'.format(adjRating, c, a, se, adjOppRating, e, gain))
        return gain
