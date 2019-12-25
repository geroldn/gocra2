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
        result['color'] = 'X'
        for tr in self.doc['Tournament']['TournamentRound']:
            if int(tr['RoundNumber']) == nRound + 1 :
                break
        for tp in tr['Pairing']:
            if int(tp['Black']) == participant.id:
                result['color'] = 'B'
                result['opponent_nr'] = self.getPNr(int(tp['White']))
                break
            if int(tp['White']) == participant.id:
                result['color'] = 'W'
                result['opponent_nr'] = self.getPNr(int(tp['Black']))
                break
        if result['color'] == 'X':
            result['string']  = '   -'
        else:
            result['string'] = ' ' + str(result['opponent_nr']) + '/' + result['color']



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




