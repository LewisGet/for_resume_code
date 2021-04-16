import json, random
from django.http import HttpResponse
from .models import *
from .serializers import *
from django.contrib.auth.models import User
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView


class ObtainToken(ObtainAuthToken):
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return HttpResponse(json.dumps({'token': token.key}), content_type="application/json")


class LoginToken(APIView):
    def get(self, request):
        serializer = LoginSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return HttpResponse(json.dumps({'id': user.id}), content_type="application/json")


def index(request):
    return HttpResponse(json.dumps({'message': "working"}), content_type="application/json")


class GameView:
    def init_game(self, request, ids):
        ids = ids.split(",")
        ids = [int(i) for i in ids]

        if 2 > len(ids):
            raise Exception("player need to more than 2")

        users = Profile.objects.raw("select * from game_profile where user_id in (%s)" % ",".join([str(int(i)) for i in ids]))

        if 2 > len(users):
            raise Exception("ids have not found 2 players")

        order_ids = ids[:]
        random.shuffle(order_ids)
        first_player = order_ids[0]

        game = Game.objects.create(
            players_order=",".join([str(i) for i in order_ids])
        )

        for u in users:
            ps = GamePlayerStatus.objects.create(
                user=u.user,
                player=u.default_player,
                health=u.default_player.health,
                resources=u.default_player.resources
            )

            if u.user.id == first_player:
                ps.remain_times = ps.levels + 1
                ps.save()

            game.players.add(ps)

            for card in u.select_cards.all()[0:12]:
                cs = GameCardStatus.objects.create(
                    user=u.user,
                    card=card,
                    player=ps,
                    health=card.health,
                    attack=card.attack,
                    cost=card.cost
                )

                game.cards.add(cs)

        return HttpResponse(json.dumps({'id': game.id, 'message': [u.user.username for u in users]}), content_type="application/json")

    def game_status(self, request, id):
        game = Game.objects.get(pk=id)

        return_json = {
            'id': game.id,
            'users': [],
            'cards': [card_status.card.name for card_status in game.cards.all()],
            'players': [player_status.player.name for player_status in game.players.all()]
        }

        for player_status in game.players.all():
            this_status = {
                'name': player_status.user.username,
                'cards': [card_status.card.name for card_status in game.cards.all() if card_status.user == player_status.user],
                'player': player_status.player.name
            }

            return_json['users'].append(this_status)

        return HttpResponse(json.dumps(return_json), content_type="application/json")

    def use_card(self, request, id, card_status_id):
        # todo: allow turn owner
        # todo: split event card and entity card function
        self.pre_use_card()
        token = request.GET.get('token')
        position = request.GET.get('position')

        if token is None:
            raise Exception("you need to login with token")

        if position in range(5):
            raise Exception("position must in 0~4")

        position = int(position)

        try:
            user = Token.objects.get(key=token).user
            game = Game.objects.get(pk=id)
            card_status = GameCardStatus.objects.get(pk=card_status_id)

            self.verify_data(user, card_status, position)
            card_status = self.pay_resources(card_status)
            card_status = self.deploy_card(card_status, position)
            game.bout += 1

            self.db_update(card_status, game)


        except Exception as e:
            # todo: 500 page
            return HttpResponse(json.dumps({'message': str(e)}), content_type="application/json")

        if card_status.player.remain_times == 0:
            self.end_round(user, game)

        self.post_use_card()

        return HttpResponse(json.dumps({'message': card_status.get_card_at_str()}), content_type="application/json")

    def pre_use_card(self):
        pass

    def post_use_card(self):
        pass

    def verify_data(self, user, cs, position):
        if cs.user.id != user.id:
            raise Exception("this not your card")

        if cs.get_card_at_str() == "stage":
            raise Exception("card has been stage")

        if cs.player.remain_times <= 0:
            raise Exception("not your attack round")

        if "event" != cs.card.get_type_str():
            your_stage_cards = GameCardStatus.objects.filter(user=user, card_at=cs.get_card_at_id("stage"))

            if 5 <= len(your_stage_cards):
                raise Exception("your stage is full")

            for ycs in your_stage_cards:
                if position == ycs.stage_position:
                    raise Exception("position has been used")

    def pay_resources(self, cs):
        cs.player.remain_times -= 1
        cost_resources = cs.cost
        cs.player.resources -= cost_resources
        cs.player.exps += cost_resources
        cs.cost += 1

        if cs.player.resources < 0:
            raise Exception("not enough resources")

        return cs

    def deploy_card(self, cs, position):
        cs.set_card_at_str("stage")
        cs.set_stage_position(position)
        cs.just_deploy = True

        if "event" == cs.card.get_type_str():
            cs.set_card_at_str("graveyard")
            cs.just_deploy = False

        return cs

    def db_update(self, cs, game):
        cs.player.save()
        cs.save()
        game.save()

    def end_round(self, user, game):
        #todo: card battle

        attack_ps = game.players.get(user=user)
        target_ps = attack_ps.target

        uids = [attack_ps.user.id, target_ps.user.id]
        uids_sql = ",".join([str(i) for i in uids])
        stage_id = GameCardStatus.card_at_str.index("stage")
        css = GameCardStatus.objects.raw("""
        select * from game_gamecardstatus
        left join game_gamestatusentity
        on game_gamecardstatus.gamestatusentity_ptr_id = game_gamestatusentity.id
        where
            user_id in (%s)
        and
            card_at = %d order by stage_position
        """ % (uids_sql, stage_id))
        attack_stage_cards, target_stage_cards = [], []
        attack_stage_cards_sort, target_stage_cards_sort = {}, {}

        for cs in css:
            if cs.user.id == attack_ps.user.id:
                attack_stage_cards.append(cs)
                attack_stage_cards_sort[cs.stage_position] = cs
            else:
                target_stage_cards.append(cs)
                target_stage_cards_sort[cs.stage_position] = cs

        for acs in attack_stage_cards:
            attack_position = acs.stage_position
            if attack_position in target_stage_cards_sort:
                bcs = target_stage_cards_sort[attack_position]
                bcs.health -= acs.attack

                if 0 >= bcs.health:
                    bcs.set_card_at_str("graveyard")

                bcs.save()
            else:
                target_ps.health -= acs.attack
                target_ps.save()

        next_uid = game.next_player(user.id)
        ps = game.players.get(user=next_uid)
        ps.remain_times = ps.levels + 1
        ps.save()
