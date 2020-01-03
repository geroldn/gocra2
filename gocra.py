#!/Applications/anaconda/anaconda3/bin/python

import os
import sys
import collections
import xmltodict
from math import exp
import re

class Settings:
    def __init__(self):
        self.gocra_home = os.path.dirname(os.path.realpath(sys.argv[0])) + '/../'
        if self.s_import(self.gocra_home + 'gocrarc.xml'):
            self.reg()

    def s_import(self, file):
        if os.path.exists(file):
            with open(file) as fd:
                self.doc = xmltodict.parse(fd.read())
            return True
        else:
            self.gocra.messages.append('No such file: ' + file)
            return False

    def reg(self):
        self.s_home = self.doc['Settings']['s_home']
        self.s_tfile = self.doc['Settings']['s_tfile']
        self.s_name_column_width = int(self.doc['Settings']['s_name_column_width'])
        self.s_ronde_column_width = int(self.doc['Settings']['s_ronde_column_width'])


class RatingSystem:
    def __init__(self, gocra):
        self.gocra = gocra
        self.rparms = []

    def rpimport(self, file):
        if os.path.exists(file):
            with open(file) as fd:
                self.doc = xmltodict.parse(fd.read())
            return True
        else:
            self.gocra.messages.append('No such file: ' + file)
            return False

    def rpreg(self, gocra):
        self.epsilon = float(self.doc['RatingParameters']['Epsilon'])
        for r in self.doc['RatingParameters']['Conlist']['Conitem']:
            self.rparms.append({
                'Gor': int(r['Gor']),
                'Con': int(r['Con']),
                'A': int(r['A'])
            })

    def getParms(self, rating):
        rp_low = self.rparms[0]
        rp_high = self.rparms[0]
        for rp in self.rparms:
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

    def getGain(self, color, rating, oppRating, handicap, bWin):
        e = self.epsilon
        '''
        if rating < oppRating:
            r = rating
        else:
            r = oppRating
        '''
        r = rating
        c = self.getParms(r)['Con']
        a = self.getParms(r)['A']
        hr = 0.0
        if handicap > 0:
            if color == 'B':
                hr = 100*(handicap - 0.5)
            elif color == 'W':
                hr = 100*(0.5 - handicap)
            else:
                print('Illegal color')
                return None
        diff = oppRating - rating - hr
        return c*(bWin - 1 / (exp(diff/a) + 1) - e/2)

class Serie:
    def __init__(self, gocra):
        self.gocra = gocra

    def timport(self, file):
        if os.path.exists(file):
            with open(file) as fd:
                self.doc = xmltodict.parse(fd.read())
            return True
        else:
            self.gocra.messages.append('No such file: ' + file)
            return False

    def treg(self):
        self.name = self.doc['Tournament']['Name']
        self.year = int(re.split('-', self.name)[1])
        self.snr = int(re.split('-', self.name)[2])
        self.numberOfRounds = int(self.doc['Tournament']['NumberOfRounds'])
        self.currentRoundNumber = int(self.doc['Tournament']['CurrentRoundNumber'])
        self.takeCurrentRoundInAccount = self.doc['Tournament']['TakeCurrentRoundInAccount']
        self.participants = []
        self.results = []
        for p in self.doc['Tournament']['IndividualParticipant']:
            if p['PreliminaryRegistration'] == 'false':
                sParticipant = (Participant(
                      p['GoPlayer']['Surname'] + ', '
                    + p['GoPlayer']['FirstName']
                    , p['GoPlayer']['GoLevel']
                    , int(p['GoPlayer']['Rating'])
                    , int(p['Id'])))
                self.participants.append(sParticipant)
        self.setNr()
        self.calcResultRatings()
        for n, p in enumerate(self.participants):
            self.results.append([])
            for r in range(self.currentRoundNumber):
                self.results[n].append({})
                self.regResult(n, r)

    def setNr(self):
        for n, p in enumerate(self.participants, start=1):
            p.setNr(n)

    def calcResultRatings(self):
        for p in self.participants:
            p.resultRating = p.startRating

    def regResult(self, nParticipant, nRound):
        participant = self.participants[nParticipant]
        result = self.results[nParticipant][nRound]
        result['color'] = None
        for tr in self.doc['Tournament']['TournamentRound']:
            if int(tr['RoundNumber']) == nRound + 1 :
                break
        for tp in tr['Pairing']:
            if tp['PairingWithBye'] == 'true':
                pass
            elif int(tp['Black']) == participant.id:
                result['color'] = 'B'
                result['opponent_nr'] = self.getPNr(int(tp['White']))
                if tp['Result'] == '1-0':
                    result['win'] = '+'
                elif tp['Result'] == '0-1':
                    result['win'] = '-'
                else:
                    result['win'] = '='
                break
            elif int(tp['White']) == participant.id:
                result['color'] = 'W'
                result['opponent_nr'] = self.getPNr(int(tp['Black']))
                if tp['Result'] == '0-1':
                    result['win'] = '+'
                elif tp['Result'] == '1-0':
                    result['win'] = '-'
                else:
                    result['win'] = '='
                break
        if tp['PairingWithBye'] == 'true':
            rstr  = '   ='
        elif result['color'] == None:
            rstr  = '   -'
        elif result['win'] == '=':
            rstr  = '   ='
        else:
            opponent = self.participants[result['opponent_nr']-1]
            result['handicap'] = int(tp['Handicap'])
            #rstr = ' ' + str(result['opponent_nr'])
            rstr = '{0:3d}'.format( result['opponent_nr'])
            print(result)
            rstr = rstr + result['win']
            rstr = rstr + '/' + result['color']
            if result['handicap'] > 0:
                rstr = rstr + str(result['handicap'])
            else:
                rstr = rstr + ' '
            delta = self.gocra.rsys.getGain(result['color'], participant.startRating, opponent.startRating, result['handicap'], result['win'] == '+')
            participant.resultRating = participant.resultRating + delta
            while participant.resultRating > participant.newrank.round_rating() + 100:
                participant.newrank.rankUp()
            while participant.resultRating < participant.newrank.round_rating() - 100:
                participant.newrank.rankDown()
            rstr = rstr + '({0:+5.1f})'.format(delta)
        result['string'] = rstr

    def getPNr(self, _id):
        nr = 0
        for n, p in enumerate(self.participants):
            if p.id == _id:
                nr = p.nr
                break
        return nr

    def print(self):
        nw = self.gocra.settings.s_name_column_width
        rw = self.gocra.settings.s_ronde_column_width
        line1 = '+' + '+'.rjust(nw, '-')
        print(line1)
        line1 = ('| {0}'.format(self.name)).ljust(nw) + '|' + ' {0:4d} {1:3d}'.format(self.year, self.snr)
        print(line1)
        line1 = '+' + '+'.rjust(nw, '-')
        for i in range(self.numberOfRounds):
            line1 = line1 + (' Ronde ' + str(i+1) + ' ').ljust(rw , '-') + '+'
        print(line1)
        for n, p in enumerate(self.participants):
            line2 = ('|' + str(p.nr).rjust(2) + ' ' + p.name + ' ('+ p.rank.rank + ')').ljust(nw) + '|'
            for i in range(self.currentRoundNumber):
                line2 = line2 + self.results[n][i]['string'].ljust(rw) + '|'
            for i in range(self.numberOfRounds - self.currentRoundNumber):
                line2 = line2 + ' '.ljust(rw) + '|'
            line2 = line2 + ' {0:4.0f} -> {1:4.0f}'.format(p.startRating, p.resultRating)
            if p.rank.nValue > p.newrank.nValue:
                line2 = line2 + ' ' + p.newrank.rank + ' :('
            if p.rank.nValue < p.newrank.nValue:
                line2 = line2 + ' ' + p.newrank.rank + ' :)'
            print(line2)
        print(line1)

class Rank:
    def __init__(self, rank):
        self.rank = rank
        self.type = re.split("[1-9]+", rank)[1]
        if self.type == 'd':
            self.nValue = int(re.split("d", rank)[0])
        if self.type == 'k':
            self.nValue = -int(re.split("k", rank)[0])

    def rating2rank(self, rating):
        r = round(rating/100)
        if r > 20:
            self.nValue = r - 20
            self.type = 'd'
        else:
            self.nValue = 21 - r
            self.type = 'k'
        self.rank = str(abs(self.nValue)) + self.type

    def rankUp(self):
        self.nValue = self.nValue + 1
        if self.nValue == 0:
            self.nValue = 1
            self.type = 'd'
        self.rank = str(abs(self.nValue)) + self.type

    def rankDown(self):
        self.nValue = self.nValue - 1
        if self.nValue == 0:
            self.nValue = -1
            self.type = 'k'
        self.rank = str(abs(self.nValue)) + self.type

    def round_rating(self):
        if self.type == 'k':
            rating = (21 + self.nValue) * 100
        else:
            rating = (20 + self.nValue) * 100
        return rating

class Participant:
    def __init__(self, name, rank, rating, _id):
        self.name = name
        self.rank = Rank(rank)
        self.newrank = Rank(rank)
        self.rating = rating
        self.id = _id
        self.nr = 0
        self.startRating = rating
        self.resultRating = rating

    def setNr(self, nr):
        self.nr = nr

class Ratinglist:
    def __init__(self, gocra):
        self.gocra = gocra
        self.members = []
        self.series = []

    def initRatinglist(self):
        file = self.gocra.settings.gocra_home + 'UGC.xml'
        if os.path.exists(file):
            with open(file) as fd:
                self.doc = xmltodict.parse(fd.read())
            print(self.doc)
        else:
            print('Ratingfile ' + file + ' bestaat niet. Aanmaken op basis van huidige serie?')
            cmd = input('j/n : ')
            if cmd == 'j':
               self.firstRatinglist(self.gocra.serie)
            else:
               pass

    def firstRatinglist(self, serie):
        self.doc = collections.OrderedDict()
        self.doc['Club'] = collections.OrderedDict()
        self.doc['Club']['Name'] = 'UGC'
        self.doc['Club']['Member'] = []
        for p in serie.participants:
            self.doc['Club']['Member'].append(collections.OrderedDict([('Name',p.name), ('Id',p.id)]))
        print(self.doc)


    def addSeries(self, name, start, end):
        self.series.append({
                "name": name,
                "start": start,
                "end": end
                })

    def addParticipant(self, name):
        self.participants.append(Participant(name))

    def print(self):
        for p in self.participants:
            p.print()

class Gocra:
    def __init__(self):
        self.settings = Settings()
        self.messages = []
        self.serie = Serie(self)
        self.rsys = RatingSystem(self)
        self.rl = Ratinglist(self)

    def readRParms(self):
        if self.rsys.rpimport(self.settings.gocra_home + 'gocra/ratingParameters.xml'):
            self.rsys.rpreg(self)
            return True
        else:
            return False

    def readSerie(self):
        if self.serie.timport(self.settings.s_home + self.settings.s_tfile):
            self.serie.treg()
            self.serie.print()
            return True
        else:
            return False

    def printMessages(self):
        for line in self.messages:
            print(line)
        self.messages[:] = []

def dispatch(gocra):
    print('\n <q>uit, <s>erie  .....')
    cmd = input('Enter command: ')
    if cmd == 'q':
        return False
    elif cmd == 's':
        if gocra.readSerie():
            return True
        else:
            return False
    else:
        return True

def main():
    gocra = Gocra()
    if (
        gocra.readRParms()
        and gocra.readSerie()
        and gocra.rl.initRatinglist()
    ):
        go_on = True
    else:
        go_on = False
    while go_on :
        go_on = dispatch(gocra)
    if len(gocra.messages) > 0:
        gocra.printMessages()

main()




