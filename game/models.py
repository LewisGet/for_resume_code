from django.db import models
from django.contrib.auth.models import User


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


class Player(Entity):
    resources = models.IntegerField(default=0)


class GamePlayerStatus(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    health = models.IntegerField(default=0)
    resources = models.IntegerField(default=0)
    levels = models.IntegerField(default=0)
    exps = models.IntegerField(default=0)
    remain_times = models.IntegerField(default=0)


class GameCardStatus(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    player = models.ForeignKey(GamePlayerStatus, on_delete=models.CASCADE)
    health = models.IntegerField(default=0)
    attack = models.IntegerField(default=0)
    cost = models.IntegerField(default=0)

    card_at_str = ["hand", "stage", "graveyard"]
    card_at = models.IntegerField(default=0)

    just_deploy = models.BooleanField(default=True)

    def get_card_at_str(self):
        return self.card_at_str[self.card_at]

    def set_card_at_str(self, value):
        self.card_at = self.card_at_str.index(value)


class Game(models.Model):
    id = models.AutoField(primary_key=True)
    players = models.ManyToManyField(GamePlayerStatus, related_name="game_players")
    cards = models.ManyToManyField(GameCardStatus, related_name="game_cards")
    bout = models.IntegerField(default=0)
    players_order = models.TextField()


class Profile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    default_player = models.ForeignKey(Player, on_delete=models.CASCADE)
    select_cards = models.ManyToManyField(Card)

    def __str__(self):
        return self.user.username
