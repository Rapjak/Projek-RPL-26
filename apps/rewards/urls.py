"""Rewards URLs - API-010..API-013 + API-018.

Routes (mounted at /api/v1/):
- GET  /rewards                     -> API-012 daftar reward
- POST /rewards/{reward_id}/redeem  -> API-013 tukar reward
- GET  /rewards/redemptions         -> daftar penukaran user
- GET  /points/transactions         -> API-010 riwayat transaksi poin
- GET  /leaderboard                 -> API-011 leaderboard
"""
from django.urls import path
from .views import (
    RewardListView, RedeemRewardView, RedemptionListView,
    PointTransactionListView, LeaderboardView,
)

urlpatterns = [
    path('rewards', RewardListView.as_view(), name='reward-list'),
    path('rewards/<uuid:reward_id>/redeem', RedeemRewardView.as_view(), name='reward-redeem'),
    path('rewards/redemptions', RedemptionListView.as_view(), name='reward-redemptions'),
    path('points/transactions', PointTransactionListView.as_view(), name='point-transactions'),
    path('leaderboard', LeaderboardView.as_view(), name='leaderboard'),
]
