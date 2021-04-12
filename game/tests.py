from django.test import TestCase
from django.urls import reverse
from .models import *
from django.contrib.auth.models import User
from django.test import Client
from .views import *
import json


class GameTestCase(TestCase):
    def setUp(self):
        self.init_users()
        self.init_cards()
        self.init_players()
        self.init_user_profile(self.user1, self.player1, self.card[0:12])
        self.init_user_profile(self.user2, self.player2, self.card[12:24])
        self.init_game([self.user1, self.user2])

    def init_users(self):
        self.user1 = User.objects.create(username="user_1", password="password1")
        self.user2 = User.objects.create(username="user_2", password="password2")

    def init_players(self):
        self.player1 = Player.objects.create(name="player 1", description="player description 1")
        self.player2 = Player.objects.create(name="player 2", description="player description 2")

    def init_user_profile(self, user, player, cards):
        self.user1_profile = Profile.objects.create(
            user=user,
            default_player=player
        )

        self.user1_profile.select_cards.add(*cards)

    def init_cards(self):
        self.card = []

        for i in range(24):
            self.card.append(Card.objects.create(name="card %d" % i, description="card description %d" % i))

    def init_game(self, users):
        error = False
        try:
            uids = [u.id for u in users]
            uids_string = ",".join([str(i) for i in uids])
            r = self.client.get(reverse('init_game', args=[uids_string]))
        except Exception as e:
            error = True

        self.assertFalse(error)

        r = json.loads(r.content)
        self.game = Game.objects.get(pk=r['id'])
        self.player_status = [ps for ps in self.game.players.all()]

    def test_error_init_game(self):
        # not found error
        error = False

        try:
            self.client.get(reverse('init_game', args=['32747']))
        except Exception as e:
            error = True

        self.assertTrue(error)

        # not found more then 2 user data
        error = False

        try:
            uids = [u.id for u in [self.user1, self.user1, self.user1]]
            uids_string = ",".join([str(i) for i in uids])
            self.client.get(reverse('init_game', args=[uids_string]))
        except Exception as e:
            error = True

        self.assertTrue(error)

    def test_init_ok_game(self):
        # ok test
        users = [ps.user.id for ps in self.player_status]

        self.assertTrue(self.user1.id in users)
        self.assertTrue(self.user2.id in users)

        first_player_status_id = int(self.game.players_order.split(",")[0])

        # first attack player status have remain times
        for ps in self.player_status:
            if ps.user.id == first_player_status_id:
                self.assertEquals(ps.remain_times, 1)
            else:
                self.assertEquals(ps.remain_times, 0)
