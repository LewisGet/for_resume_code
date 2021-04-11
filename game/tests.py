from django.test import TestCase
from django.urls import reverse
from .models import *
from django.contrib.auth.models import User
from django.test import Client
from .views import *
import json


class GameTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="user_1", password="password1")
        self.user2 = User.objects.create(username="user_2", password="password2")

        self.player1 = Player.objects.create(name="player 1", description="player description 1")
        self.player2 = Player.objects.create(name="player 2", description="player description 2")

        self.card = []

        for i in range(24):
            self.card.append(Card.objects.create(name="card %d" % i, description="card description %d" % i))

        self.user1_profile = Profile.objects.create(
            user=self.user1,
            default_player=self.player1
        )

        self.user1_profile.select_cards.add(*self.card[0:12])

        self.user2_profile = Profile.objects.create(
            user=self.user2,
            default_player=self.player2
        )

        self.user2_profile.select_cards.add(*self.card[12:24])

    def test_init_game(self):
        # not found error
        error = False

        try:
            self.client.get(reverse('init_game', args=['32747']))
        except Exception as e:
            error = True

        self.assertTrue(error)

        # ok test
        error = False

        try:
            uids = [self.user1.id, self.user2.id]
            uids_string = ",".join([str(i) for i in uids])
            r = self.client.get(reverse('init_game', args=[uids_string]))
        except Exception as e:
            error = True

        self.assertFalse(error)

        r = json.loads(r.content)
        game = Game.objects.get(pk=r['id'])

        player_status = [ps for ps in game.players.all()]
        users = [ps.user.id for ps in player_status]

        self.assertTrue(self.user1.id in users)
        self.assertTrue(self.user2.id in users)

        first_player_status_id = int(game.players_order.split(",")[0])

        for ps in player_status:
            if ps.player.id == first_player_status_id:
                self.assertEquals(ps.remain_times, 1)
            else:
                self.assertEquals(ps.remain_times, 0)
