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


class GamePlayerStatus(models.Model):
    id = models.IntegerField(primary_key=True, db_index=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    health = models.IntegerField(default=0)
    resources = models.IntegerField(default=0)
    levels = models.IntegerField(default=0)


class Games(models.Model):
    id = models.IntegerField(primary_key=True, db_index=True)
    players = models.ManyToManyField(GamePlayerStatus, related_name="game_players")
    hand_cards = models.ManyToManyField(GameCardStatus, related_name="game_hand_cards")
    stage_cards = models.ManyToManyField(GameCardStatus, related_name="game_stage_cards")
    graveyard_cards = models.ManyToManyField(GameCardStatus, related_name="game_graveyard_cards")
