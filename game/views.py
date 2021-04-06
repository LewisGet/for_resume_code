import json
from django.http import HttpResponse
from .models import *
from django.contrib.auth.models import User


def index(request):
    return HttpResponse(json.dumps({'message': "working"}), content_type="application/json")


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

        if card_status.player.resources < 0:
            raise Exception("not enough resources")

        card_status.cost += 1
        card_status.set_card_at_str("stage")

        card_status.player.save()
        card_status.save()
    except Exception as e:
        # todo: 500 page
        return HttpResponse(json.dumps({'message': str(e)}), content_type="application/json")

    return HttpResponse(json.dumps({'message': card_status.get_card_at_str()}), content_type="application/json")
