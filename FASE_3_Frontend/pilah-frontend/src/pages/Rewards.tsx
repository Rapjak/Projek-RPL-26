import { useState, useEffect } from 'react';
import { useNotification } from '../context/NotificationContext';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Spinner } from '../components/common/Spinner';
import { Modal } from '../components/common/Modal';
import { rewardService } from '../services/rewards';
import { mediaBaseURL } from '../services/api';
import type { Reward } from '../types';

interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export function Rewards() {
  const { user, refreshUser } = useAuth();
  const { addNotification } = useNotification();
  const [rewards, setRewards] = useState<Paginated<Reward> | null>(null);
  const [loading, setLoading] = useState(true);
  const [redeemModal, setRedeemModal] = useState<Reward | null>(null);
  const [redeeming, setRedeeming] = useState(false);
  const [voucher, setVoucher] = useState<string | null>(null);

  useEffect(() => {
    fetchRewards();
  }, []);

  const fetchRewards = async () => {
    try {
      const data = await rewardService.list({ page: 1 });
      setRewards(data);
    } catch (err) {
      addNotification('error', 'Gagal memuat reward');
    } finally {
      setLoading(false);
    }
  };

  const handleRedeem = async (rewardId: string) => {
    setRedeeming(true);
    try {
      const resp = await rewardService.redeem(rewardId);
      addNotification('success', 'Reward berhasil ditukar!');
      setVoucher(resp.kode_reward);
      setRedeemModal(null);
      fetchRewards();
      await refreshUser();
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Gagal menukar reward';
      addNotification('error', msg);
    } finally {
      setRedeeming(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Reward</h2>

      <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200 p-6">
        <p className="text-sm text-emerald-700 font-medium">Poin Anda</p>
        <p className="text-4xl font-bold text-emerald-600 mt-2">
          {(user?.total_poin ?? 0).toLocaleString('id-ID')}
        </p>
      </Card>

      {voucher && (
        <Card className="p-4 bg-yellow-50 border-yellow-300">
          <p className="font-medium text-yellow-900">Kode Voucher Anda:</p>
          <p className="text-2xl font-mono font-bold text-yellow-800 tracking-wider">{voucher}</p>
          <p className="text-xs text-yellow-700 mt-1">Simpan kode ini untuk ditukarkan.</p>
          <Button className="mt-3 bg-yellow-600 hover:bg-yellow-700 text-sm" onClick={() => setVoucher(null)}>
            Tutup
          </Button>
        </Card>
      )}

      <h3 className="text-lg font-semibold text-gray-900">Reward Tersedia</h3>

      {rewards && rewards.results.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {rewards.results.map((reward) => {
            const outOfStock = !reward.ketersediaan || reward.stock <= 0;
            const insufficient = (user?.total_poin ?? 0) < reward.points_required;
            return (
              <Card key={reward.id} className="p-4">
                <div className="flex gap-4">
                  <div className="w-20 h-20 bg-gray-200 rounded-lg flex-shrink-0 overflow-hidden">
                    {reward.image && (
                      <img
                        src={`${mediaBaseURL}${reward.image}`}
                        alt={reward.name}
                        className="w-full h-full object-cover"
                      />
                    )}
                  </div>
                  <div className="flex-1 flex flex-col justify-between">
                    <div>
                      <h4 className="font-semibold text-gray-900">{reward.name}</h4>
                      {reward.description && (
                        <p className="text-xs text-gray-600 mt-1 line-clamp-2">{reward.description}</p>
                      )}
                      <p className="text-sm font-bold text-emerald-600 mt-2">{reward.points_required} poin</p>
                      <p className="text-xs text-gray-500">Stok: {reward.stock} · Berlaku sampai {reward.masa_berlaku}</p>
                    </div>
                  </div>
                  <div className="flex flex-col justify-end">
                    {outOfStock ? (
                      <button
                        disabled
                        className="px-3 py-1 bg-gray-300 text-gray-600 text-xs font-medium rounded cursor-not-allowed"
                      >
                        Stok habis
                      </button>
                    ) : insufficient ? (
                      <button
                        disabled
                        className="px-3 py-1 bg-red-100 text-red-600 text-xs font-medium rounded cursor-not-allowed"
                      >
                        Poin kurang
                      </button>
                    ) : (
                      <Button
                        size="sm"
                        onClick={() => setRedeemModal(reward)}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white"
                      >
                        Tukar
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card className="text-center py-12">
          <p className="text-gray-500">Belum ada reward tersedia.</p>
        </Card>
      )}

      {redeemModal && (
        <Modal isOpen={true} onClose={() => setRedeemModal(null)} title="Konfirmasi Penukaran">
          <div className="space-y-4">
            <p className="text-gray-700">
              Tukar <strong>{redeemModal.name}</strong> dengan <strong>{redeemModal.points_required}</strong> poin?
            </p>
            <div className="flex gap-3">
              <Button
                variant="outline"
                className="flex-1 border-gray-300"
                onClick={() => setRedeemModal(null)}
              >
                Batal
              </Button>
              <Button
                className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                loading={redeeming}
                onClick={() => handleRedeem(redeemModal.id)}
              >
                Tukar
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
