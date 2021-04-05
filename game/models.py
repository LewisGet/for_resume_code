from django.db import models


class Entity(models.Model):
    id = models.IntegerField(primary_key=True, db_index=True)
    name = models.CharField(max_length=20)
    health = models.IntegerField(default=20)
    description = models.TextField(max_length=80)
    # todo: ability callback in here?
    ability_id = models.IntegerField(default=0)


class Card(Entity):
    attack = models.IntegerField(default=0)


class Player(Entity):
    resources = models.IntegerField(default=0)


class GameCardStatus(models.Model):
    id = models.IntegerField(primary_key=True, db_index=True)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    health = models.IntegerField(default=0)
    attack = models.IntegerField(default=0)
    cost = models.IntegerField(default=0)

    card_at_str = ["hand", "stage", "graveyard"]
    card_at = models.IntegerField(default=0)

    def get_card_at_str(self):
        return self.card_at_str[self.card_at]

    def set_card_at_str(self, value):
        self.card_at = self.card_at_str.index(value)


class GamePlayerStatus(models.Model):
    id = models.IntegerField(primary_key=True, db_index=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    health = models.IntegerField(default=0)
    resources = models.IntegerField(default=0)
    levels = models.IntegerField(default=0)


class Game(models.Model):
    id = models.IntegerField(primary_key=True, db_index=True)
    players = models.ManyToManyField(GamePlayerStatus, related_name="game_players")
    cards = models.ManyToManyField(GameCardStatus, related_name="game_cards")
