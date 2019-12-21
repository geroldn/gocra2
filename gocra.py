#!/Applications/anaconda/anaconda3/bin/python

import os
import xmltodict

class Settings:
    s_home = '/Users/gerold/dev/python/gocra/'
    s_tfile = 'UGC-2019-1.xml'
    s_name_column_width = 32

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
        self.participants = []
        for p in self.doc['Tournament']['IndividualParticipant']:
            if p['PreliminaryRegistration'] == 'false':
                self.participants.append(Participant(
                      p['GoPlayer']['Surname'] + ', '
                    + p['GoPlayer']['FirstName']
                    , p['GoPlayer']['GoLevel']
                    , p['Id']))

    def print(self):
        w = Settings.s_name_column_width
        pstr = '+' + '+'.rjust(w, '-')
        for i in range(self.numberOfRounds):
            pstr = pstr + (' Ronde ' + str(i+1) + ' ').ljust(12, '-') + '+'
        print(pstr)
        for p in self.participants:
            print(('|' + p.name + ' ('+ p.strength + ')').ljust(w) + '|')
        print(pstr)

class Rating:
    def __init__(self, date, rating):
        self.rating = {
                "date": date,
                "rating": rating
                }

class Participant:
    def __init__(self, name, strength, _id):
        self.name = name
        self.strength = strength
        self._id = _id
        self.ratings = []

    def addRating(self, date, rating):
        self.ratings.append(Rating(date, rating))

    def print(self):
        s = self.name.ljust(20)
        for r in self.ratings:
            s = s + r.rating["date"].ljust(9) + str(r.rating["rating"]).ljust(5)
        print(s)

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




