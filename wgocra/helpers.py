""" Diverse classes not ORM """
from datetime import datetime
import xmltodict
from gocra.gocra import Rank
from .models import Series, Participant, Player, Result

def get_handicap(mm_b, mm_w):
    return int((mm_w - mm_b) // 1)

class ExternalMacMahon:
    """ Representation of external macmahon xml file (Gerlach) """
    def __init__(self):
        self.doc = []

    def s_import(self, file):
        """ Upload macmahon xml file and parse into dictionary """
        self.doc = xmltodict.parse(file.read())
        return self.doc

    def xml_import(self, memfile):
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
            qset = Player.objects.filter(
                first_name=fname
            ).filter(
                last_name=lname
            )
            if qset.count() > 0:
                player = qset[0]
            else:
                player = Player()
                player.first_name = fname
                player.last_name = lname
                player.reg_date = datetime.now()
                player.save()
            spart = Participant()
            rank = participant['GoPlayer']['GoLevel']
            spart.rank = rank
            rating = int(participant['GoPlayer']['Rating'])
            if rating == 0:
                rating = spart.init_rank.round_rating()
            spart.rating = rating
            spart.mm_id = int(participant['Id'])
            spart.series = series
            spart.player = player
            spart.save()
            series.participants.append(spart)

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
