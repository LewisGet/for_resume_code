from django.urls import path

from game import views

urlpatterns = [
    path('', views.index, name='index'),

    # view game
    path('<int:id>/', views.game_status, name='game_status'),

    # use cards, 使用卡片
    #path('', views.index, name='use_cards'),
    # send cards to graveyard, 丟棄卡片到墓地
    #path('', views.index, name='throw_cards'),
    # revival cards, 復活卡片
    #path('', views.index, name='revival_cards'),
    # Get information about the card in hand, 取得手牌資訊
    #path('', views.index, name='get_cards_in_hand'),
    # Get information about the card on stage, 取得場上卡片資訊
    #path('', views.index, name='get_cards_on_stage'),
    # Get information about the card in graveyard, 取得墓地卡片資訊
    #path('', views.index, name='get_cards_in_graveyard'),
    # Get send information end round, 送出結束回合訊息
    #path('', views.index, name='end_round'),
    # Get health, 取得腳色血量
    #path('', views.index, name='get health'),
    # Set health, 設定腳色血量
    #path('', views.index, name='set health'),
    # Get levels, 取得腳色等級
    #path('', views.index, name='get levels'),
    # Set levels, 設定腳色等級
    #path('', views.index, name='set levels'),
    # Get resources, 取得資源狀況
    #path('', views.index, name='get resources'),
    # Set resources, 設定資源狀況
    #path('', views.index, name='set resources'),
]
