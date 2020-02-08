#!/Applications/anaconda/anaconda3/bin/python
import os
import sys
import shutil
import collections
import xmltodict
from math import exp
import re
import pysftp
from getpass import getpass
from datetime import date

class Settings:
    def __init__(self):
        self.ok = False
        self.gocra_home = os.path.dirname(os.path.realpath(sys.argv[0])) + '/../'
        if self.s_import(self.gocra_home + 'gocrarc.xml'):
            self.reg()
        else:
            print('Iets gaat fout bij inlezen sittings (gocrarc.xml)')
            print('<Enter> om gocra af te sluiten')
            input()
            quit()

    def s_import(self, file):
        if os.path.exists(file):
            with open(file) as fd:
                self.doc = xmltodict.parse(fd.read())
            return True
        else:
            print('No such file: ' + file)
            return False

    def reg(self):
        self.ok = True
        self.s_home = self.doc['Settings']['serie_home']
        self.s_tfile = self.doc['Settings']['serie_file']
        self.s_name_column_width = int(self.doc['Settings']['s_name_column_width'])
        self.s_ronde_column_width = int(self.doc['Settings']['s_ronde_column_width'])
        self.sftp_host = self.doc['Settings']['sftp_host']
        self.sftp_dir = self.doc['Settings']['sftp_dir']
        self.sftp_user = self.doc['Settings']['sftp_user']
        self.sftp_sshkey = self.doc['Settings']['sftp_sshkey']
        self.sftp_askPw = (self.doc['Settings']['sftp_askPw'] == True)

class Uploader:
    def regSettings(s):
        Uploader.host = s.sftp_host
        Uploader.dir = s.sftp_dir
        Uploader.user = s.sftp_user
        Uploader.passwd = None
        Uploader.sshkey = s.sftp_sshkey
        Uploader.askPw = s.sftp_askPw

    def upload(subdir, _file):
        #print('KEY: ' + Uploader.sshkey)
        if Uploader.askPw and Uploader.passwd == None:
            print('password for ' + Uploader.user + ' on ' + Uploader.host)
            Uploader.passwd = getpass()
        try:
            sftp = pysftp.Connection(Uploader.host,
                username=Uploader.user,
                password=Uploader.passwd,
                private_key = Uploader.sshkey,
                port = 2022,
                log=True)
        except:
            print('Fout bij openen sftp-connectie ')
            print("Unexpected error:", sys.exc_info()[0])
        else:
            #print('log: ' + sftp.logfile)
            with sftp:
                with sftp.cd(Uploader.dir + subdir):
                    try:
                        sftp.put(_file)
                    except:
                        print('Fout bij upload {0}'.format(_file))
                        print("Unexpected error:", sys.exc_info()[0])
                    else:
                        print('Uploaded {0} to [webloc]/{1}.'.format(_file, subdir))

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
        if handicap > 0:
            if color == 'B':
                rating = rating + 100*(handicap - 0.5)
            elif color == 'W':
                oppRating = oppRating + 100*(handicap - 0.5)
            else:
                print('Illegal color')
                return None
        if rating < oppRating:
            a = self.getParms(rating)['A']
        else:
            a = self.getParms(oppRating)['A']
        c = self.getParms(rating)['Con']
        diff = oppRating - rating
        se = 1 / (exp(diff/a) + 1)
        #print('rating: {0:4.0f}, oppRating: {4:4.0f}, con: {1:7.3f}, a: {2:7.3f}, se: {3:6.3f}'.format(rating, c, a, se, oppRating))
        return c*(bWin - se - e/2)

class Serie:
    def __init__(self, gocra):
        self.gocra = gocra

    def timport(self, file):
        if os.path.exists(file):
            with open(file) as fd:
                self.doc = xmltodict.parse(fd.read())
            return True
        else:
            print('No such file: ' + file)
            return False

    def comparePosition(self, p):
        tdelta = p.resultRating - p.startRating
        return 100 * p.wins + tdelta

    def treg(self):
        self.name = self.doc['Tournament']['Name']
        self.year = int(re.split('-', self.name)[1])
        self.nr = int(re.split('-', self.name)[2])
        self.numberOfRounds = int(self.doc['Tournament']['NumberOfRounds'])
        self.currentRoundNumber = int(self.doc['Tournament']['CurrentRoundNumber'])
        #self.currentRoundNumber = 3
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
        self.reset()
        for n, p in enumerate(self.participants):
            self.results.append([])
            for r in range(self.currentRoundNumber):
                self.results[n].append({})
                self.regResult(n, r)
        for p in self.participants:
            if p.resultRating < p.startRating - 100:
                p.resultRating = p.startRating - 100
        self.participants.sort(reverse=True, key=self.comparePosition)
        self.results = []
        self.setNr()
        self.reset()
        for n, p in enumerate(self.participants):
            self.results.append([])
            for r in range(self.currentRoundNumber):
                self.results[n].append({})
                self.regResult(n, r)
        for p in self.participants:
            if p.resultRating < p.startRating - 100:
                p.resultRating = p.startRating - 100


    def setNr(self):
        for n, p in enumerate(self.participants, start=1):
            p.setNr(n)

    def reset(self):
        for p in self.participants:
            p.resultRating = p.startRating
            p.wins = 0
            p.games = 0

    def regResult(self, nParticipant, nRound):
        participant = self.participants[nParticipant]
        result = self.results[nParticipant][nRound]
        result['color'] = None
        for tr in self.doc['Tournament']['TournamentRound']:
            if int(tr['RoundNumber']) == nRound + 1 :
                break
        if not 'Pairing' in tr.keys():
            print('No Pairing')
            return
        if not type(tr['Pairing']) is list:
            trlist = [tr['Pairing']]
        else:
            trlist = tr['Pairing']
        for tp in trlist:
            if tp['PairingWithBye'] == 'true':
                if int(tp['Black']) == participant.id:
                    result['color'] = 'B'
                    result['win'] = 'free'
                    print(result)
                    break
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
        delta = 0.0
        if result['color'] == None:
            rstr  = '   -'
        elif result['win'] == 'free':
            rstr  = '   vrij'
            participant.wins = participant.wins + 1
            participant.games = participant.games + 1
        elif result['win'] == '=':
            rstr  = '   ='
        else:
            opponent = self.participants[result['opponent_nr']-1]
            result['handicap'] = int(tp['Handicap'])
            rstr = '{0:3d}'.format( result['opponent_nr'])
            rstr = rstr + result['win']
            rstr = rstr + '/' + result['color']
            if result['handicap'] > 0:
                rstr = rstr + str(result['handicap'])
            else:
                rstr = rstr + ' '
            delta = self.gocra.rsys.getGain(result['color']
                        , participant.startRating
                        , opponent.startRating
                        , result['handicap']
                        , result['win'] == '+')
            participant.resultRating = participant.resultRating + delta
            while participant.resultRating > participant.newRank.round_rating() + 100:
                participant.newRank.rankUp()
            while participant.resultRating < participant.newRank.round_rating() - 100:
                participant.newRank.rankDown()
            participant.games = participant.games + 1
            if result['win'] == '+':
                participant.wins = participant.wins + 1
        result['string'] = rstr
        result['delta'] = delta

    def getPNr(self, _id):
        nr = 0
        for n, p in enumerate(self.participants):
            if p.id == _id:
                nr = p.nr
                break
        return nr

    def participantHtml(self, fd, n, p):
        fd.write('    <tr>\n')
        fd.write('      <td>\n')
        fd.write(str(p.nr) + ' ' + p.name + ' ('+ p.rank.rank + ')')
        fd.write('      </td>\n')
        for i in range(self.currentRoundNumber):
            delta = self.results[n][i]['delta']
            if delta > 0.0:
                fd.write('      <td class="green">')
            elif delta < 0.0:
                fd.write('      <td class="red">')
            else:
                fd.write('      <td class="black">')
            fd.write(self.results[n][i]['string'])
            fd.write('</td>\n')
            if delta > 0.0:
                fd.write('      <td class="black">')
                fd.write('{0:+5.1f}'.format(self.results[n][i]['delta']))
            elif delta < 0.0:
                fd.write('      <td class="black">')
                fd.write('{0:+5.1f}'.format(self.results[n][i]['delta']))
            else:
                fd.write('      <td>')
            fd.write('</td>\n')
        for i in range(self.numberOfRounds - self.currentRoundNumber):
            fd.write('      <td></td>')
            fd.write('      <td></td>')
        fd.write('      <td class="black">')
        fd.write( '{0}/{1}'.format(p.wins, p.games))
        fd.write('</td>\n')
        fd.write('      <td class="black">')
        fd.write( '{0:4.0f}'.format(p.startRating))
        fd.write('</td>\n')
        tdelta = p.resultRating - p.startRating
        if tdelta > 0:
            fd.write('      <td class="green">')
        elif tdelta < 0:
            fd.write('      <td class="red">')
        else:
            fd.write('      <td class="black">')
        fd.write( '{0:4.0f}'.format(tdelta))
        fd.write('</td>\n')
        fd.write('      <td class="black">')
        fd.write( '{0:4.0f}'.format(p.resultRating))
        fd.write('</td>\n')
        if p.rank.nValue > p.newRank.nValue:
            fd.write('      <td class="red">')
            fd.write(' ' + p.newRank.rank + ' :(')
        elif p.rank.nValue < p.newRank.nValue:
            fd.write('      <td class="green">')
            fd.write(' ' + p.newRank.rank + ' :)')
        else:
            fd.write('      <td>')
        fd.write('</td>\n')
        fd.write('    </tr>\n')

    def serieHtml(self, fd):
        fd.write('  <h2>Stand lopende serie</h2>\n')
        fd.write('  <table>\n')
        fd.write('    <tr>\n')
        fd.write('      <th>\n')
        fd.write('        ' + self.name)
        fd.write('      </th>\n')
        for i in range(self.numberOfRounds):
            fd.write('      <th colspan="2">')
            fd.write('Ronde ' + str(i+1))
            fd.write('      </th>\n')
        fd.write('      <th ></th>\n')
        fd.write('      <th colspan="3">Rating</th>\n')
        fd.write('      <th ></th>\n')
        fd.write('    </tr>\n')
        fd.write('    <tr>\n')
        fd.write('      <th>\n')
        fd.write('      </th>\n')
        for i in range(self.numberOfRounds):
            fd.write('      <th>')
            fd.write('Res')
            fd.write('      </th>\n')
            fd.write('      <th>')
            fd.write('+/-')
            fd.write('      </th>\n')
        fd.write('      <th>Score</th>\n')
        fd.write('      <th >Start</th>\n')
        fd.write('      <th >+/-</th>\n')
        fd.write('      <th >Actueel</th>\n')
        fd.write('      <th >Pro/Deg</th>\n')
        fd.write('    </tr>\n')
        for n, p in enumerate(self.participants):
            self.participantHtml(fd, n, p)
        fd.write('  </table>\n')

    def createHtml(self):
        file = self.gocra.settings.gocra_home + 'UGC-stand.html'
        with open(file, 'w') as fd:
            fd.write('<!DOCTYPE html>\n')
            fd.write('<html>\n')
            fd.write('<head>\n')
            fd.write('<style>\n')
            fd.write('.black{\n')
            fd.write('  color: black;\n')
            fd.write('  text-align: center;\n')
            fd.write('}\n')
            fd.write('.blue{\n')
            fd.write('  color: blue;\n')
            fd.write('  text-align: center;\n')
            fd.write('}\n')
            fd.write('.green{\n')
            fd.write('  color: green;\n')
            fd.write('  text-align: center;\n')
            fd.write('}\n')
            fd.write('.red{\n')
            fd.write('  color: red;\n')
            fd.write('  text-align: center;\n')
            fd.write('}\n')
            fd.write('table{\n')
            fd.write('  border-collapse: collapse;\n')
            fd.write('  margin: auto;\n')
            fd.write('}\n')
            fd.write('table, th, td {\n')
            fd.write('  border: 1px solid black;\n')
            fd.write('}\n')
            fd.write('tr:nth-child(even){\n')
            fd.write('  background: #DDD;\n')
            fd.write('}\n')
            fd.write('tr:nth-child(od){\n')
            fd.write('  background: #FFF;\n')
            fd.write('}\n')
            fd.write('h2 {\n')
            fd.write('  text-align: center;\n')
            fd.write('}\n')
            fd.write('th, td {\n')
            fd.write('  padding-left: 4px;\n')
            fd.write('  padding-right: 4px;\n')
            fd.write('}\n')
            fd.write('</style>\n')
            fd.write('</head>\n')
            fd.write('<body>\n')
            self.serieHtml(fd)
            fd.write('</body>\n')
            fd.write('</html>\n')
        return file

    def print(self):
        nw = self.gocra.settings.s_name_column_width
        rw = self.gocra.settings.s_ronde_column_width
        line1 = '+' + '+'.rjust(nw, '-')
        print(line1)
        line1 = ('| {0}'.format(self.name)).ljust(nw) + '|' + ' {0:4d} {1:3d}'.format(self.year, self.nr)
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
            if p.rank.nValue > p.newRank.nValue:
                line2 = line2 + ' ' + p.newRank.rank + ' :('
            if p.rank.nValue < p.newRank.nValue:
                line2 = line2 + ' ' + p.newRank.rank + ' :)'
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
        self.newRank = Rank(rank)
        self.rating = rating
        self.id = _id
        self.nr = 0
        self.startRating = rating
        self.resultRating = rating

    def setNr(self, nr):
        self.nr = nr

class RlResult:
    def set(self, pId, startRating, resultRating, rank, newRank):
        self.pId = pId
        self.startRating = startRating
        self.resultRating = resultRating
        self.rank = Rank(rank)
        self.newRank = Rank(newRank)

class RlSerie:
    def __init__(self, jaar, nr, nMembers):
        self.jaar = jaar
        self.nr = nr
        self.results = []

class Ratinglist:
    def __init__(self, gocra):
        self.gocra = gocra
        self.members = []
        self.series = []

    def initRatinglist(self):
        file = self.gocra.settings.gocra_home + 'UGC.xml'
        if not os.path.exists(file):
            print('Ratingfile ' + file + ' bestaat niet. Initiëren op basis van huidige serie?')
            cmd = input('j/n : ')
            if cmd == 'j':
                self.firstRatinglist(self.gocra.serie, file)
                self.writeRatinglist(file)
            else:
               return False
        self.readRatinglist(file)
        self.rlReg()
        self.rlPrint()
        return True

    def readRatinglist(self, file):
        with open(file) as fd:
            self.doc = xmltodict.parse(fd.read())
        print(self.doc)

    def setNr(self):
        for n, m in enumerate(self.members, start=1):
            m.setNr(n)

    def rlReg(self):
        for m in self.doc['Club']['Member']:
            cMember = (Participant(
                  m['Name']
                , m['Rank']
                , int(m['Rating'])
                , int(m['Id'])))
            self.members.append(cMember)
        self.setNr
        for s in self.doc['Club']['Serie']:
            if int(s['Year']) > 0:
                print(s)
                self.series.append(RlSerie(
                        int(s['Year']),
                        int(s['Nr']),
                        len(self.members)
                        ))

    def rlPrint(self):
        pass

    def writeRatinglist(self, file):
        with open(file, 'w') as fd:
            fd.write(xmltodict.unparse(self.doc, pretty=True))

    def firstRatinglist(self, serie, file):
        self.doc = collections.OrderedDict()
        self.doc['Club'] = collections.OrderedDict()
        self.doc['Club']['Name'] = 'UGC'
        self.doc['Club']['Member'] = []
        for p in serie.participants:
            self.doc['Club']['Member'].append(collections.OrderedDict(
                [
                    ('Name', p.name),
                    ('Id', p.id),
                    ('Rank', p.newRank.rank),
                    ('Rating', p.resultRating)
                ]))
        self.doc['Club']['Serie'] = []
        self.doc['Club']['Serie'].append(collections.OrderedDict(
            [
                ('Year', 0),
                ('Nr', 0),
                ('Dummy', 'Maak Serie langer dan 1!')
            ]))
        self.doc['Club']['Serie'].append(collections.OrderedDict(
            [
                ('Year', serie.year),
                ('Nr', serie.nr),
                ('Result', [])
            ]))
        for p in serie.participants:
            self.doc['Club']['Serie'][1]['Result'].append(collections.OrderedDict(
                [
                    ('Id', p.id),
                    ('Rank', p.rank.rank),
                    ('NewRank', p.newRank.rank),
                    ('StartRating', p.startRating),
                    ('ResultRating', p.resultRating)
                ]))
        self.writeRatinglist(file)
        self.readRatinglist(file)

class Gocra:
    def __init__(self):
        self.settings = Settings()
        self.messages = []
        self.serie = Serie(self)
        self.rsys = RatingSystem(self)
        self.rl = Ratinglist(self)
        Uploader.regSettings(self.settings)

    def cpMmToday(self):
        today = date.today()
        s_today = today.strftime("%Y%m%d")
        fromPath = self.settings.s_home + self.settings.s_tfile
        fBase = re.split('\.', self.settings.s_tfile)[0]
        fExtension = re.split('\.', self.settings.s_tfile)[1]
        toPath = self.settings.s_home + fBase + '_' + s_today + '.' + fExtension
        try:
            shutil.copy(fromPath, toPath)
            return toPath
        except (IOError, os.error) as why:
            print('Fout by backup MM: '+ str(why))
            return None

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
    print('\n <q>uit, <s>erie, <r>atinglist, <u>pload to web  .....')
    cmd = input('Enter command: ')
    print()
    if cmd == 'h':
        html = gocra.serie.createHtml()
    if cmd == 'u':
        html = gocra.serie.createHtml()
        cpMm = gocra.cpMmToday()
        if cpMm:
            Uploader.upload('archief', cpMm)
        if html:
            Uploader.upload('', html)
    if cmd == 'q':
        return False
    elif cmd == 's':
        if not gocra.readSerie():
            print('Iets gaat fout bij lezen serie data')
    elif cmd == 'r':
        if not gocra.rl.initRatinglist():
            print('Iets gaat fout bij lezen rating data')
    return True

def main():
    go_on = True
    gocra = Gocra()
    if not (
        gocra.readRParms()
        and gocra.readSerie()
        ):
        print('Iets gaat fout met inlezen params of serie data')
    while go_on :
        go_on = dispatch(gocra)
    if len(gocra.messages) > 0:
        gocra.printMessages()

main()




