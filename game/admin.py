from django.contrib import admin

from .models import *

admin.site.register(Card)
admin.site.register(Player)
admin.site.register(Game)
admin.site.register(GameCardStatus)
admin.site.register(GamePlayerStatus)
