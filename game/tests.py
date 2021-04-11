from django.test import TestCase
from .models import *
from django.contrib.auth.models import User
from django.test import Client


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

    def test_nothing_yet(self):
        self.assertTrue(True)
