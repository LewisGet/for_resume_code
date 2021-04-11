import json
from django.http import HttpResponse
from .models import *
from django.contrib.auth.models import User


def index(request):
    return HttpResponse(json.dumps({'message': "working"}), content_type="application/json")


def init_game(request, ids):
    ids = ids.split(",")
    ids = [int(i) for i in ids]
    first_player = ids[0]

    if 2 > len(ids):
        raise Exception("player need to more than 2")

    users = Profile.objects.raw("select * from game_profile where user_id in (%s)" % ",".join([str(int(i)) for i in ids]))

    if 2 > len(users):
        raise Exception("ids have not found 2 players")

    game = Game.objects.create(
        #todo: random it
        players_order=",".join([str(int(i)) for i in ids])
    )

    for u in users:
        ps = GamePlayerStatus.objects.create(
            user_id=u.user,
            player=u.default_player,
            health=u.default_player.health,
            resources=u.default_player.resources
        )

        if u.user.id == first_player:
            ps.remain_times = GamePlayerStatus.levels + 1

        game.players.add(ps)

        for card in u.select_cards.all()[0:12]:
            cs = GameCardStatus.objects.create(
                user_id=u.user,
                card=card,
                player=ps,
                health=card.health,
                attack=card.attack,
                cost=card.cost
            )

            game.cards.add(cs)

    return HttpResponse(json.dumps({'message': [u.user.username for u in users]}), content_type="application/json")


def game_status(request, id):
    try:
        game = Game.objects.get(pk=id)
    except:
        # todo: 500 page
        return HttpResponse(json.dumps({'message': 500}), content_type="application/json")

    return_json = {
        'id': game.id,
        'users': [],
        'cards': [card_status.card.name for card_status in game.cards.all()],
        'players': [player_status.player.name for player_status in game.players.all()]
    }

    for player_status in game.players.all():
        this_status = {
            'name': player_status.user_id.username,
            'cards': [card_status.card.name for card_status in game.cards.all() if card_status.user_id == player_status.user_id],
            'player': player_status.player.name
        }

        return_json['users'].append(this_status)

    return HttpResponse(json.dumps(return_json), content_type="application/json")


def use_card(request, id, card_status_id):
    # todo: login token
    # todo: allow turn owner
    try:
        game = Game.objects.get(pk=id)
        card_status = GameCardStatus.objects.get(pk=card_status_id)

        if card_status.get_card_at_str() == "stage":
            raise Exception("card has been stage")

        cost_resources = card_status.card.cost + card_status.cost
        card_status.player.resources -= cost_resources
        card_status.player.exps += cost_resources

        if card_status.player.resources < 0:
            raise Exception("not enough resources")

        card_status.cost += 1
        card_status.set_card_at_str("stage")
        card_status.just_deploy = True

        game.bout += 1

        card_status.player.save()
        card_status.save()
        game.save()
    except Exception as e:
        # todo: 500 page
        return HttpResponse(json.dumps({'message': str(e)}), content_type="application/json")

    return HttpResponse(json.dumps({'message': card_status.get_card_at_str()}), content_type="application/json")
