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
    def init_game(request, ids):
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

    def game_status(request, id):
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

    def use_card(request, id, card_status_id):
        # todo: allow turn owner
        token = request.GET.get('token')

        if token is None:
            raise Exception("you need to login with token")

        try:
            user = Token.objects.get(key=token).user
            game = Game.objects.get(pk=id)
            card_status = GameCardStatus.objects.get(pk=card_status_id)

            if card_status.user.id != user.id:
                raise Exception("this not your card")

            if card_status.get_card_at_str() == "stage":
                raise Exception("card has been stage")

            if card_status.player.remain_times <= 0:
                raise Exception("not your attack round")

            if "event" != card_status.card.get_type_str():
                your_stage_cards = GameCardStatus.objects.filter(user=user, card_at=card_status.get_card_at_id("stage"))

                if 5 <= len(your_stage_cards):
                    raise Exception("your stage is full")

            card_status.player.remain_times -= 1
            cost_resources = card_status.card.cost + card_status.cost
            card_status.player.resources -= cost_resources
            card_status.player.exps += cost_resources

            if card_status.player.resources < 0:
                raise Exception("not enough resources")

            card_status.cost += 1
            card_status.set_card_at_str("stage")
            card_status.just_deploy = True

            if "event" == card_status.card.get_type_str():
                card_status.set_card_at_str("graveyard")
                card_status.just_deploy = False

            game.bout += 1

            card_status.player.save()
            card_status.save()
            game.save()
        except Exception as e:
            # todo: 500 page
            return HttpResponse(json.dumps({'message': str(e)}), content_type="application/json")

        return HttpResponse(json.dumps({'message': card_status.get_card_at_str()}), content_type="application/json")
