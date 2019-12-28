#!/Applications/anaconda/anaconda3/bin/python

import os
import xmltodict
from math import exp

class Settings:
    s_home = '/Users/gerold/dev/python/gocra/'
    s_tfile = 'UGC-2019-1.xml'
    s_name_column_width = 32
    s_ronde_column_width = 15

class RatingSystem:
    def __init__(self, gocra):
        self.gocra = gocra
        self.rparms = []

    def rpimport(self, file):
        if os.path.exists(file):
            with open(file) as fd:
                self.doc = xmltodict.parse(fd.read())
        else:
            self.gocra.messages.append('No such file: ' + file)

    def rpreg(self, gocra):
        self.epsilon = float(self.doc['RatingParameters']['Epsilon'])
        for r in self.doc['RatingParameters']['Conlist']['Conitem']:
            self.rparms.append({
                'Gor': int(r['Gor']),
                'Con': int(r['Con']),
                'A': int(r['A'])
            })
        print(self.rparms)

    def getGain(self, color, rating, oppRating, handicap, bWin):
        e = 0.016
        if rating < oppRating:
            r = rating
        else:
            r = oppRating
        c = 70
        a = 155
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
        print('Diff: ' + str(diff))
        return c*(bWin - 1 / (exp(diff/a) + 1) - e/2)

class Serie:
    def __init__(self, gocra):
        self.gocra = gocra

    def timport(self, file):
        if os.path.exists(file):
            with open(file) as fd:
                self.doc = xmltodict.parse(fd.read())
        else:
            self.gocra.messages.append('No such file: ' + file)

    def treg(self):
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
        self.setStartRatings()
        self.calcResultRatings()
        for n, p in enumerate(self.participants):
            self.results.append([])
            for r in range(self.currentRoundNumber):
                self.results[n].append({})
                self.regResult(n, r)

    def setNr(self):
        for n, p in enumerate(self.participants, start=1):
            p.setNr(n)

    def setStartRatings(self):
        for p in self.participants:
            p.startRating = p.rating

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
            if int(tp['Black']) == participant.id:
                result['color'] = 'B'
                result['opponent_nr'] = self.getPNr(int(tp['White']))
                if tp['Result'] == '1-0':
                    result['win'] = True
                else:
                    result['win'] = False
                break
            if int(tp['White']) == participant.id:
                result['color'] = 'W'
                result['opponent_nr'] = self.getPNr(int(tp['Black']))
                if tp['Result'] == '0-1':
                    result['win'] = True
                else:
                    result['win'] = False
                break
        if result['color'] == None:
            rstr  = '   -'
        else:
            print(result)
            opponent = self.participants[result['opponent_nr']-1]
            result['handicap'] = int(tp['Handicap'])
            #rstr = ' ' + str(result['opponent_nr'])
            rstr = '{0:3d}'.format( result['opponent_nr'])
            if result['win']:
                rstr = rstr + '+'
            else:
                rstr = rstr + '-'
            rstr = rstr + '/' + result['color']
            if result['handicap'] > 0:
                rstr = rstr + str(result['handicap'])
            delta = self.gocra.rsys.getGain(result['color'], participant.startRating, opponent.startRating, result['handicap'], result['win'])
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
        nw = Settings.s_name_column_width
        rw = Settings.s_ronde_column_width
        line1 = '+' + '+'.rjust(nw, '-')
        for i in range(self.numberOfRounds):
            line1 = line1 + (' Ronde ' + str(i+1) + ' ').ljust(rw , '-') + '+'
        print(line1)
        for n, p in enumerate(self.participants):
            line2 = ('|' + str(p.nr).rjust(2) + ' ' + p.name + ' ('+ p.strength + ')').ljust(nw) + '|'
            for i in range(self.currentRoundNumber):
                line2 = line2 + self.results[n][i]['string'].ljust(rw) + '|'
            for i in range(self.numberOfRounds - self.currentRoundNumber):
                line2 = line2 + ' '.ljust(rw) + '|'
            line2 = line2 + str(p.startRating).rjust(5) + ' - ' + str(p.resultRating).rjust(4)
            print(line2)
        print(line1)

class Participant:
    def __init__(self, name, strength, rating, _id):
        self.name = name
        self.strength = strength
        self.rating = rating
        self.id = _id
        self.nr = 0
        self.startRating = 0
        self.resultRating = 0

    def setNr(self, nr):
        self.nr = nr

class Rating:
    def __init__(self, date, rating):
        self.rating = {
                "date": date,
                "rating": rating
                }

class Ratinglist:
    def __init__(self):
        self.participants = []
        self.series = []

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
        self.rl = Ratinglist()
        self.messages = []
        self.serie = Serie(self)
        self.rsys = RatingSystem(self)

    def readRParms(self):
        self.rsys.rpimport(Settings.s_home + 'gocra/ratingParameters.xml')
        self.rsys.rpreg(self)
        print('Epsilon:')
        print(self.rsys.epsilon)
        print(self.rsys.getGain('B', 1000, 1100, 0, True))
        print(self.rsys.getGain('B', 1000, 1100, 1, True))
        print(self.rsys.getGain('B', 1000, 1100, 2, True))
        print(self.rsys.getGain('B', 1100, 1000, 0, True))
        print(self.rsys.getGain('B', 1100, 1000, 1, True))
        print(self.rsys.getGain('B', 1100, 1000, 2, True))

    def readSerie(self):
        self.serie.timport(Settings.s_home + Settings.s_tfile)
        self.serie.treg()
        '''
        for k, v in self.serie.doc['Tournament'].items():
            print(k)
        for k in self.serie.doc['Tournament']['IndividualParticipant']:
            print(k)
        for r in self.serie.doc['Tournament']['TournamentRound']:
            print(r)
        '''
        print('Number of rounds: ' + str(self.serie.numberOfRounds))
        self.serie.print()



    def printMessages(self):
        for line in self.messages:
            print(line)
        self.messages[:] = []

def dispatch(gocra):
    print('\n <r>ating, <q>uit, <s>erie  .....')
    cmd = input('Enter command: ')
    if cmd == 'q':
        return False
    elif cmd == 'r':
        gocra.readRParms()
        return True
    elif cmd == 's':
        gocra.readSerie()
        return True
    else:
        return True

def main():
    gocra = Gocra()
    go_on = True
    while go_on :
        gocra.rl.print()
        if len(gocra.messages) > 0:
            gocra.printMessages()
        go_on = dispatch(gocra)

main()




