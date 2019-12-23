#!/Applications/anaconda/anaconda3/bin/python

import os
import xmltodict

class Settings:
    s_home = '/Users/gerold/dev/python/gocra/'
    s_tfile = 'UGC-2019-1.xml'
    s_name_column_width = 32
    s_ronde_column_width = 12

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
        self.pairings = []
        pNr = 0
        for p in self.doc['Tournament']['IndividualParticipant']:
            if p['PreliminaryRegistration'] == 'false':
                sParticipant = (Participant(
                      p['GoPlayer']['Surname'] + ', '
                    + p['GoPlayer']['FirstName']
                    , p['GoPlayer']['GoLevel']
                    , int(p['GoPlayer']['Rating'])
                    , p['Id']))
                self.participants.append(sParticipant)
                self.pairings.append([])
                for r in range(self.currentRoundNumber):
                    self.pairings[pNr].append({})
                    self.regPairing(pNr, r)
                pNr = pNr + 1
        self.setNr()
        self.setStartRatings()
        self.calcResultRatings()

    def setNr(self):
        for n, p in enumerate(self.participants, start=1):
            p.setNr(n)

    def setStartRatings(self):
        for p in self.participants:
            p.startRating = p.rating

    def calcResultRatings(self):
        for p in self.participants:
            p.resultRating = p.startRating

    def regPairing(self, nParticipant, nRound):
        self.pairings[nParticipant][nRound]['string'] = '   -'

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
                line2 = line2 + self.pairings[n][i]['string'].ljust(rw) + '|'
            for i in range(self.numberOfRounds - self.currentRoundNumber):
                line2 = line2 + ' '.ljust(rw) + '|'
            line2 = line2 + str(p.startRating).rjust(4) + ' - ' + str(p.resultRating).rjust(4)
            print(line2)
        print(line1)

class Rating:
    def __init__(self, date, rating):
        self.rating = {
                "date": date,
                "rating": rating
                }

class Participant:
    def __init__(self, name, strength, rating, _id):
        self.name = name
        self.strength = strength
        self.rating = rating
        self._id = _id
        self.startRating = 0
        self.resultRating = 0
        self.pairings = []

    def setNr(self, nr):
        self.nr = nr

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

    def readSerie(self):
        self.serie.timport(Settings.s_home + Settings.s_tfile)
        self.serie.treg()
        for k, v in self.serie.doc['Tournament'].items():
            print(k)
        for k in self.serie.doc['Tournament']['IndividualParticipant']:
            print(k)
        for r in self.serie.doc['Tournament']['TournamentRound']:
            print(r)
        print('Number of rounds: ' + str(self.serie.numberOfRounds))
        self.serie.print()

    def printMessages(self):
        for line in self.messages:
            print(line)
        self.messages[:] = []

def dispatch(gocra):
    print('\n <e>dit, <q>uit, <s>erie  .....')
    cmd = input('Enter command: ')
    if cmd == 'q':
        return False
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




