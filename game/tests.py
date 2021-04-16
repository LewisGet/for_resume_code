from django.test import TestCase
from django.urls import reverse
from .models import *
from django.contrib.auth.models import User
from django.test import Client
from rest_framework.authtoken.models import Token
from .views import *
import json


class AutoTakeTokenClient(Client):
    default_setup = []

    def check_default_setup(self, data, default_index, data_index):
        if hasattr(self, default_index):
            if data is None:
                data = {data_index: eval("self." + default_index)}
            elif data_index not in data:
                data[data_index] = eval("self." + default_index)

            return data

        return data

    def get(self, path, data=None, follow=False, secure=False, **extra):
        for i in self.default_setup:
            default_index, data_index = i
            data = self.check_default_setup(data, default_index, data_index)

        if hasattr(self, "default_token"):
            if data is None:
                data = {'token': self.default_token}
            elif 'token' not in data:
                data['token'] = self.default_token

        return super().get(path, data=data, follow=follow, secure=secure, **extra)


class GameTestCase(TestCase):
    def setUp(self):
        self.init_users()
        self.init_cards()
        self.init_players()
        self.init_user_profile(self.user1, self.player1, self.card[0:12])
        self.init_user_profile(self.user2, self.player2, self.card[12:24])
        self.init_game([self.user1, self.user2])
        self.init_login_token()
        self.init_default_login_token_by_first_attacker()
        self.init_default_use_card_position_at_3()

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

    def init_login_token(self):
        self.token = []
        api_name = 'login'

        for i in range(3):
            r = self.client.get(reverse(api_name), data={'username': self.users[i].username, 'password': self.users_raw_pd[i]})
            self.token.append(json.loads(r.content)['token'])

    def init_default_login_token_by_first_attacker(self):
        self.client = AutoTakeTokenClient()
        self.now_attacker_ps = GamePlayerStatus.objects.filter(remain_times__gte=1)[0]
        self.default_token = Token.objects.get(user=self.now_attacker_ps.user).key
        self.client.default_token = self.default_token

    def init_default_use_card_position_at_3(self):
        self.client._use_card_position = 3
        self.client.default_setup.append(("_use_card_position", "position"))

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

    def test_use_card_when_not_you_time(self):
        api_name = 'use_card'

        not_attack_player = GamePlayerStatus.objects.filter(remain_times=0)[0]
        org_remain_times = not_attack_player.remain_times

        not_attack_cards = self.game.cards.filter(player=not_attack_player)

        r = self.client.get(reverse(api_name, args=[self.game.id, not_attack_cards[0].id]))
        used_card = GameCardStatus.objects.get(pk=not_attack_cards[0].id)

        self.assertEquals(used_card.get_card_at_str(), "hand")
        self.assertEquals(used_card.player.remain_times, org_remain_times)

    def test_use_not_player_card(self):
        api_name = 'use_card'

        not_attack_player = None

        # make sure all users have attack times, that test player can send this request
        for ps in GamePlayerStatus.objects.all():
            ps.remain_times = 3
            ps.save()

        for user in User.objects.all():
            if user != self.now_attacker_ps.user:
                not_attack_player = GamePlayerStatus.objects.get(user=user)
                break

        not_player_cards = self.game.cards.filter(player=not_attack_player)

        org_login_player_remain_times = GamePlayerStatus.objects.get(pk=self.now_attacker_ps.id).remain_times
        org_not_attack_player_remain_times = not_attack_player.remain_times

        r = self.client.get(reverse(api_name, args=[self.game.id, not_player_cards[0].id]))
        used_card = GameCardStatus.objects.get(pk=not_player_cards[0].id)

        self.assertEquals(used_card.get_card_at_str(), "hand")
        self.assertEquals(used_card.player.remain_times, org_login_player_remain_times)
        self.assertEquals(used_card.player.remain_times, org_not_attack_player_remain_times)

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

    def test_login_token(self):
        api_name = 'login'
        r = self.client.get(reverse(api_name), data={'username': self.users[0].username, 'password': self.users_raw_pd[0]})
        token = json.loads(r.content)['token']

        db_token = Token.objects.get(user=self.users[0])

        self.assertEquals(db_token.key, token)

    def test_login_by_token(self):
        api_name = 'login'
        r = self.client.get(reverse(api_name), data={'username': self.users[0].username, 'password': self.users_raw_pd[0]})
        token = json.loads(r.content)['token']

        api_name = 'token_login'
        r = self.client.get(reverse(api_name), data={'token': token})
        uid = json.loads(r.content)['id']

        self.assertEquals(self.users[0].id, uid)

    def test_card_type(self):
        self.assertEquals(self.card[0].get_type_str(), "entity")
        self.card[0].set_type_str("event")
        self.assertEquals(self.card[0].get_type_str(), "event")

    def test_stage_full_use_event_card(self):
        api_name = 'use_card'
        attacker_available_cards, _ = self.get_card_purview(self.now_attacker_ps)

        for i in range(5):
            cs = attacker_available_cards[i]
            cs.set_card_at_str("stage")
            cs.save()

        # update cs
        self.card_status = [cs for cs in self.game.cards.all()]
        attacker_available_cards, _ = self.get_card_purview(self.now_attacker_ps)

        event_card = attacker_available_cards[0]
        event_card.card.set_type_str("event")
        event_card.card.save()

        r = self.client.get(reverse(api_name, args=[self.game.id, event_card.id]))
        used_card = GameCardStatus.objects.get(pk=event_card.id)

        self.assertEquals(used_card.get_card_at_str(), "graveyard")
        self.assertEquals(used_card.player.remain_times, self.now_attacker_ps.remain_times - 1)

    def test_stage_full_use_entity_card(self):
        api_name = 'use_card'
        attacker_available_cards, _ = self.get_card_purview(self.now_attacker_ps)

        for i in range(5):
            cs = attacker_available_cards[i]
            cs.set_card_at_str("stage")
            cs.save()

        # update cs
        self.card_status = [cs for cs in self.game.cards.all()]
        attacker_available_cards, _ = self.get_card_purview(self.now_attacker_ps)

        r = self.client.get(reverse(api_name, args=[self.game.id, attacker_available_cards[0].id]))
        used_card = GameCardStatus.objects.get(pk=attacker_available_cards[0].id)

        self.assertEquals(used_card.get_card_at_str(), "hand")
        self.assertEquals(used_card.player.remain_times, self.now_attacker_ps.remain_times)

    def test_one_player_stage_full_other_player_use_entity_card(self):
        api_name = 'use_card'

        not_attack_player = None

        for user in User.objects.all():
            if user != self.now_attacker_ps.user:
                not_attack_player = GamePlayerStatus.objects.get(user=user)
                break

        other_player_available_cards, _ = self.get_card_purview(not_attack_player)

        for i in range(5):
            cs = other_player_available_cards[i]
            cs.set_card_at_str("stage")
            cs.save()

        # update cs
        self.card_status = [cs for cs in self.game.cards.all()]
        attacker_available_cards, _ = self.get_card_purview(self.now_attacker_ps)

        r = self.client.get(reverse(api_name, args=[self.game.id, attacker_available_cards[0].id]))
        used_card = GameCardStatus.objects.get(pk=attacker_available_cards[0].id)

        self.assertEquals(used_card.get_card_at_str(), "stage")
        self.assertEquals(used_card.player.remain_times, self.now_attacker_ps.remain_times - 1)

    def test_card_stage_position(self):
        errors = False
        try:
            self.card_status[0].set_stage_position(30)
        except Exception as e:
            errors = True

        self.assertTrue(errors)
        self.assertEquals(self.card_status[0].stage_position, 0)

        errors = False

        self.card_status[0].set_card_at_str("hand")
        try:
            self.card_status[0].set_stage_position(3)
        except Exception as e:
            errors = True

        self.assertTrue(errors)
        self.assertEquals(self.card_status[0].stage_position, 0)

        errors = False

        self.card_status[0].set_card_at_str("graveyard")
        try:
            self.card_status[0].set_stage_position(3)
        except Exception as e:
            errors = True

        self.assertTrue(errors)
        self.assertEquals(self.card_status[0].stage_position, 0)

        errors = False

        self.card_status[0].set_card_at_str("stage")
        try:
            self.card_status[0].set_stage_position(3)
        except Exception as e:
            errors = True

        self.assertFalse(errors)
        self.assertEquals(self.card_status[0].stage_position, 3)

    def test_event_card_stage_position(self):
        test_cs = self.card_status[0]
        test_cs.card.set_type_str("event")

        try:
            test_cs.set_card_at_str("hand")
            test_cs.set_stage_position(3)
        except Exception as e:
            pass

        self.assertEquals(test_cs.stage_position, 0)

        try:
            test_cs.set_card_at_str("graveyard")
            test_cs.set_stage_position(3)
        except Exception as e:
            pass

        self.assertEquals(test_cs.stage_position, 0)

        try:
            test_cs.set_card_at_str("stage")
            test_cs.set_stage_position(3)
        except Exception as e:
            pass

        self.assertEquals(test_cs.stage_position, 3)

    def test_position_has_been_used(self):
        api_name = 'use_card'
        set_position = 2
        cs_can_use, cs_cant_use = self.get_card_purview(self.now_attacker_ps)
        self.now_attacker_ps.remain_times = 3
        self.now_attacker_ps.save()

        cs_can_use[2].card.set_type_str("event")
        cs_can_use[2].card.save()

        done_r = self.client.get(reverse(api_name, args=[self.game.id, cs_can_use[0].id]), data={'position': set_position})
        not_r = self.client.get(reverse(api_name, args=[self.game.id, cs_can_use[1].id]), data={'position': set_position})
        done_r2 = self.client.get(reverse(api_name, args=[self.game.id, cs_can_use[2].id]), data={'position': set_position})

        used_card = GameCardStatus.objects.get(pk=cs_can_use[0].id)
        not_used_card = GameCardStatus.objects.get(pk=cs_can_use[1].id)
        used_card_2 = GameCardStatus.objects.get(pk=cs_can_use[2].id)

        self.assertEquals(used_card.get_card_at_str(), "stage")
        self.assertEquals(used_card.stage_position, set_position)
        self.assertEquals(used_card.player.remain_times, 1)

        self.assertEquals(not_used_card.get_card_at_str(), "hand")
        self.assertEquals(not_used_card.stage_position, 0)
        self.assertEquals(not_used_card.player.remain_times, 1)

        self.assertEquals(used_card_2.get_card_at_str(), "graveyard")
        self.assertEquals(used_card_2.stage_position, set_position)
        self.assertEquals(used_card_2.player.remain_times, 1)
