import { useState, useEffect } from 'react';
import { useNotification } from '../context/NotificationContext';
import { Card } from '../components/common/Card';
import { Spinner } from '../components/common/Spinner';
import { rewardService } from '../services/rewards';
import type { LeaderboardResponse, LeaderboardUserEntry, LeaderboardBuildingEntry } from '../types';

export function Leaderboard() {
  const { addNotification } = useNotification();
  const [activeTab, setActiveTab] = useState<'user' | 'building'>('user');
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLeaderboard();
  }, [activeTab]);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const resp = await rewardService.getLeaderboard({ type: activeTab, page: 1, limit: 10 });
      setData(resp);
    } catch (err) {
      addNotification('error', 'Gagal memuat leaderboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  const isUser = activeTab === 'user';
  const entries = (data?.data || []) as Array<LeaderboardUserEntry | LeaderboardBuildingEntry>;
  const myRank = isUser
    ? (data as any)?.user_rank
    : (data as any)?.user_building_rank;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Peringkat</h2>

      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('user')}
          className={`px-4 py-3 font-medium border-b-2 transition-colors ${
            activeTab === 'user'
              ? 'border-emerald-600 text-emerald-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Pengguna
        </button>
        <button
          onClick={() => setActiveTab('building')}
          className={`px-4 py-3 font-medium border-b-2 transition-colors ${
            activeTab === 'building'
              ? 'border-emerald-600 text-emerald-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Unit/Gedung
        </button>
      </div>

      {myRank != null && (
        <Card className="p-4 bg-emerald-50 border-emerald-200">
          <p className="text-sm text-emerald-700">
            {isUser ? 'Peringkat Anda' : 'Peringkat unit/gedung Anda'}:{' '}
            <span className="font-bold">#{myRank}</span>
          </p>
        </Card>
      )}

      <div className="space-y-3">
        {entries.map((entry: any) => {
          const rank = entry.rank;
          const name = isUser ? (entry as LeaderboardUserEntry).name : (entry as LeaderboardBuildingEntry).unit_gedung;
          const points = entry.total_poin;
          const isTopThree = rank <= 3;
          const rankColors: Record<number, string> = {
            1: 'bg-yellow-100 text-yellow-800',
            2: 'bg-gray-100 text-gray-800',
            3: 'bg-orange-100 text-orange-800',
          };

          return (
            <Card key={rank} className="p-4">
              <div className="flex items-center gap-4">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 font-bold text-lg ${
                    isTopThree ? rankColors[rank] : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {rank === 1 && '🥇'}
                  {rank === 2 && '🥈'}
                  {rank === 3 && '🥉'}
                  {rank > 3 && rank}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 truncate">{name}</h3>
                  {isUser && (entry as LeaderboardUserEntry).unit_gedung && (
                    <p className="text-xs text-gray-500">{(entry as LeaderboardUserEntry).unit_gedung}</p>
                  )}
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="font-bold text-emerald-600 text-lg">{points.toLocaleString('id-ID')}</p>
                  <p className="text-xs text-gray-500">poin</p>
                </div>
              </div>
            </Card>
          );
        })}
        {entries.length === 0 && (
          <Card className="text-center py-12">
            <p className="text-gray-500">Belum ada data peringkat.</p>
          </Card>
        )}
      </div>
    </div>
  );
}
