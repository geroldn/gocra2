""" Diverse classes not ORM """
from datetime import datetime
import xmltodict
import re
from django.contrib.auth import models as auth_models
from .models import Series, Participant, Player, Result

def get_handicap(mm_b, mm_w):
    return int((mm_w - mm_b) // 1)

def rank2rating(rank):
    rating = None
    dk_char = re.split("[0-9]+", rank)[1]
    r_num = int(re.split(dk_char, rank)[0])
    if dk_char == 'd':
        rating = 2000 + r_num * 100
    if dk_char == 'k':
        rating = 2100 - r_num * 100
    return rating

def rating2rank(rating):
    n_value = int(round(rating / 100, 0))
    if n_value > 20:
        rank = '{:d}d'.format(n_value - 20)
    else:
        rank = '{:d}k'.format(21 - n_value)
    return rank

class ExternalMacMahon:
    """ Representation of external macmahon xml file (Gerlach) """
    def __init__(self):
        self.doc = []

    def s_import(self, file):
        """ Upload macmahon xml file and parse into dictionary """
        self.doc = xmltodict.parse(file.read())
        return self.doc

    def xml_import(self, memfile, club):
        """ Concert dictionary into (ORM) objects """
        self.s_import(memfile)
        name = self.doc['Tournament']['Name']
        qset = Series.objects.filter(name=name).order_by('version').reverse()
        if qset.count() > 0:
            new_version = qset[0].version + 1
        else:
            new_version = 0
        series = Series()
        self.series = series
        series.club = club
        series.name = name
        series.version = new_version
        series.numberOfRounds = int(self.doc['Tournament']['NumberOfRounds'])
        series.currentRoundNumber = int(self.doc['Tournament']['CurrentRoundNumber'])
        series.takeCurrentRoundInAccount = True
        series.seriesIsOpen = False
        series.save()
        series.participants = []
        series.results = []
        for participant in self.doc['Tournament']['IndividualParticipant']:
            self.reg_participant(series, participant)
        for n_part, part in enumerate(series.participants):
            series.results.append([])
            for n_round in range(series.currentRoundNumber):
                result = Result()
                series.results[n_part].append(result)
                result.participant = part
                result.color = None
                result.round = n_round + 1
                result.game = 1
                result.win = ' '
                result.save()
                if n_round <= series.currentRoundNumber:
                    self.reg_result(series, n_part, n_round)
            for n_round in range(series.currentRoundNumber,
                                 series.numberOfRounds):
                result = Result()
                series.results[n_part].append(result)
                result.participant = part
                result.color = None
                result.round = n_round + 1
                result.win = ' '
                result.save()
        return series.pk

    def reg_participant(self, series, participant):
        """ Get participant info from macmahon structure """
        if participant['PreliminaryRegistration'] == 'false':
            fname = participant['GoPlayer']['FirstName']
            lname = participant['GoPlayer']['Surname']

            spart = Participant()
            spart.player = self.get_player(fname, lname)
            rank = participant['GoPlayer']['GoLevel']
            spart.rank = rank
            rating = int(participant['GoPlayer']['Rating'])
            if rating == 0:
                rating = rank2rating(rank)
            spart.rating = rating
            spart.mm_id = int(participant['Id'])
            spart.series = series
            spart.save()
            series.participants.append(spart)

    def get_player(self, fname, lname):
        qset = Player.objects.filter(
            first_name=fname
        ).filter(
            last_name=lname
        )
        if qset.count() > 0:
            player = qset[0]
            if not player.account:
                player.account = self.get_account(player)
                player.save()
        else:
            player = Player()
            player.first_name = fname
            player.last_name = lname
            player.reg_date = datetime.now()
            player.account = self.get_account(player)
            player.save()
        return player

    def get_account(self, player):
        #import pdb; pdb.set_trace()
        username = re.split("_", player.first_name)[0].lower() + \
                player.last_name[:1].lower()
        qset = auth_models.User.objects.filter(
            username=username
        )
        if qset:
            return qset[0]
        else:
            user = auth_models.User()
            user.username = username
            user.save()
            return user

    def reg_result(self, series, n_participant, n_round):
        """ Get result info from macmahon structure """
        participant = series.participants[n_participant]
        result = series.results[n_participant][n_round]
        t_round = None
        for t_round in self.doc['Tournament']['TournamentRound']:
            if int(t_round['RoundNumber']) == n_round + 1:
                break
        #import pdb; pdb.set_trace()
        if not 'Pairing' in t_round.keys():
            print('No Pairing')
            return
        if not isinstance(t_round['Pairing'], list):
            trlist = [t_round['Pairing']]
        else:
            trlist = t_round['Pairing']
        for t_pairing in trlist:
            if t_pairing['PairingWithBye'] == 'true':
                if int(t_pairing['Black']) == participant.mm_id:
                    result.color = 'B'
                    result.win = 'free'
                    result.save()
                    break
            elif int(t_pairing['Black']) == participant.mm_id:
                result.color = 'B'
                result.handicap = int(t_pairing['Handicap'])
                result.opponent = get_participant_by_id(
                    series,
                    int(t_pairing['White']))
                if t_pairing['Result'] == '1-0':
                    result.win = '+'
                elif t_pairing['Result'] == '0-1':
                    result.win = '-'
                else:
                    result.win = '?'
                result.save()
                break
            elif int(t_pairing['White']) == participant.mm_id:
                result.color = 'W'
                result.handicap = int(t_pairing['Handicap'])
                result.opponent = get_participant_by_id(
                    series,
                    int(t_pairing['Black']))
                if t_pairing['Result'] == '0-1':
                    result.win = '+'
                elif t_pairing['Result'] == '1-0':
                    result.win = '-'
                else:
                    result.win = '?'
                result.save()
                break

def get_participant_by_id(series, _id):
    """Get the participant instance from its mcmahon Id """
    participant = None
    for part in series.participants:
        if part.mm_id == _id:
            participant = part
            break
    return participant
