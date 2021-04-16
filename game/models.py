from django.db import models
from django.contrib.auth.models import User


# todo: create setup database for testing

class Entity(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    health = models.IntegerField(default=20)
    description = models.TextField(max_length=80)
    # todo: ability callback in here?
    ability_id = models.IntegerField(default=0)

    def __str__(self):
        return str(self.id) + " - " + self.name


class Card(Entity):
    attack = models.IntegerField(default=0)
    cost = models.IntegerField(default=0)

    type_str = ["entity", "event"]
    type = models.IntegerField(default=0)

    def get_type_str(self):
        return self.type_str[self.type]

    def set_type_str(self, value):
        self.type = self.type_str.index(value)


class Player(Entity):
    resources = models.IntegerField(default=0)


class GameStatusEntity(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    health = models.IntegerField(default=0)
    levels = models.IntegerField(default=0)


class GamePlayerStatus(GameStatusEntity):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    resources = models.IntegerField(default=0)
    exps = models.IntegerField(default=0)
    remain_times = models.IntegerField(default=0)


class GameCardStatus(GameStatusEntity):
    player = models.ForeignKey(GamePlayerStatus, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    attack = models.IntegerField(default=0)
    cost = models.IntegerField(default=0)

    card_at_str = ["hand", "stage", "graveyard"]
    card_at = models.IntegerField(default=0)

    just_deploy = models.BooleanField(default=True)
    stage_position = models.IntegerField(default=0)

    def get_card_at_id(self, value):
        return self.card_at_str.index(value)

    def get_card_at_str(self):
        return self.card_at_str[self.card_at]

    def set_card_at_str(self, value):
        self.card_at = self.card_at_str.index(value)

    def set_stage_position(self, value):
        if "stage" != self.get_card_at_str():
            raise Exception("card can\'t set position when its not in stage")

        if 5 < value:
            raise Exception("card position only have 5 places")

        self.stage_position = value


class Game(models.Model):
    id = models.AutoField(primary_key=True)
    players = models.ManyToManyField(GamePlayerStatus, related_name="game_players")
    cards = models.ManyToManyField(GameCardStatus, related_name="game_cards")
    bout = models.IntegerField(default=0)
    players_order = models.TextField()

    def get_players_order(self):
        return [int(i) for i in self.players_order.split(",")]

    def set_players_order(self, value):
        self.players_order = ",".join(value)

    def next_player(self, uid):
        orders = self.get_players_order()
        start_index = orders.index(uid) + 1
        if start_index == len(orders):
            start_index = 0

        return orders[start_index]

class Profile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    default_player = models.ForeignKey(Player, on_delete=models.CASCADE)
    select_cards = models.ManyToManyField(Card)

    def __str__(self):
        return self.user.username
