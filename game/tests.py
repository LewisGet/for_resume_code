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
        self.users = []
        self.users_raw_pd = []

        for i in range(3):
            un, pd = "user_" + str(i), "password" + str(i)
            self.users.append(User.objects.create_user(username=un, password=pd))
            self.users_raw_pd.append(pd)

        self.user1 = self.users[0]
        self.user2 = self.users[1]

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
        self.card_status = [cs for cs in self.game.cards.all()]

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

    def test_get_game_status_not_found(self):
        # not found error
        error = False

        try:
            self.client.get(reverse('game_status', args=['32747']))
        except Exception as e:
            error = True

        self.assertTrue(error)

    def test_get_game_status(self):
        r = self.client.get(reverse('game_status', args=[self.game.id]))
        r = json.loads(r.content)

        self.assertEquals(r['id'], self.game.id)

    def get_card_purview(self, player_status):
        all_can_use_cards = []
        all_cant_use_cards = []

        for cs in self.card_status:
            is_player = cs.player.id == player_status.id
            is_in_hand = cs.get_card_at_str() == "hand"
            is_affordable = cs.cost <= player_status.resources

            if False not in [is_player, is_in_hand, is_affordable]:
                all_can_use_cards.append(cs)
            else:
                all_cant_use_cards.append(cs)

        return all_can_use_cards, all_cant_use_cards

    def test_use_card(self):
        api_name = 'use_card'

        now_attack_player = GamePlayerStatus.objects.filter(remain_times__gte=1)[0]
        not_use_card_times = now_attack_player.remain_times

        all_can_use_cards, all_cant_use_cards = self.get_card_purview(now_attack_player)

        r = self.client.get(reverse(api_name, args=[self.game.id, all_can_use_cards[0].id]))
        used_card = GameCardStatus.objects.get(pk=all_can_use_cards[0].id)

        self.assertEquals(used_card.get_card_at_str(), "stage")
        self.assertEquals(used_card.player.remain_times, not_use_card_times - 1)

    def test_use_not_player_card(self):
        api_name = 'use_card'

        not_attack_player = GamePlayerStatus.objects.filter(remain_times=0)[0]
        org_remain_times = not_attack_player.remain_times

        not_attack_cards = self.game.cards.filter(player=not_attack_player)

        r = self.client.get(reverse(api_name, args=[self.game.id, not_attack_cards[0].id]))
        used_card = GameCardStatus.objects.get(pk=not_attack_cards[0].id)

        self.assertEquals(used_card.get_card_at_str(), "hand")
        self.assertEquals(used_card.player.remain_times, org_remain_times)

    def test_use_not_affordable_card(self):
        api_name = 'use_card'

        now_attack_player = GamePlayerStatus.objects.filter(remain_times__gte=1)[0]
        not_use_card_times = now_attack_player.remain_times

        all_can_use_cards, all_cant_use_cards = self.get_card_purview(now_attack_player)
        all_can_use_cards[0].cost = 32747
        all_can_use_cards[0].save()

        r = self.client.get(reverse(api_name, args=[self.game.id, all_can_use_cards[0].id]))
        used_card = GameCardStatus.objects.get(pk=all_can_use_cards[0].id)

        self.assertEquals(used_card.get_card_at_str(), "hand")
        self.assertEquals(used_card.player.remain_times, not_use_card_times)

    def test_use_card_has_been_used(self):
        api_name = 'use_card'

        now_attack_player = GamePlayerStatus.objects.filter(remain_times__gte=1)[0]
        now_attack_player.remain_times = 3
        now_attack_player.save()

        not_use_card_times = now_attack_player.remain_times

        all_can_use_cards, all_cant_use_cards = self.get_card_purview(now_attack_player)

        r = self.client.get(reverse(api_name, args=[self.game.id, all_can_use_cards[0].id]))
        used_card = GameCardStatus.objects.get(pk=all_can_use_cards[0].id)

        self.assertEquals(used_card.get_card_at_str(), "stage")
        self.assertEquals(used_card.player.remain_times, not_use_card_times - 1)

        pre_use_second_times = used_card.player.remain_times

        r = self.client.get(reverse(api_name, args=[self.game.id, all_can_use_cards[0].id]))
        used_card = GameCardStatus.objects.get(pk=all_can_use_cards[0].id)

        self.assertEquals(used_card.get_card_at_str(), "stage")
        self.assertEquals(used_card.player.remain_times, pre_use_second_times)
