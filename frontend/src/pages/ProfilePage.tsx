import { useEffect, useState } from 'react';
import { getProfile } from '../api/endpoints';
import type { ProfileIn } from '../api/types';
import { TransactionImport } from '../features/ingestion/TransactionImport';
import { ProfileBuilder } from '../features/profile/ProfileBuilder';
import './ProfilePage.css';

type View = 'main' | 'import' | 'import-review' | 'edit';

interface Props {
  profileId: string;
  onLogout: () => void;
  onProfileUpdated: () => void;
}

export function ProfilePage({ profileId, onLogout, onProfileUpdated }: Props) {
  const [profile, setProfile] = useState<ProfileIn | null>(null);
  const [view, setView] = useState<View>('main');
  const [importedProfile, setImportedProfile] = useState<ProfileIn | null>(null);

  useEffect(() => {
    getProfile(profileId).then(setProfile).catch(console.error);
  }, [profileId]);

  if (view === 'import') {
    return (
      <div className="profile-flow">
        <div className="flow-header">
          <button className="flow-back" onClick={() => setView('main')}>← Quay lại</button>
          <span>Nhập file giao dịch</span>
        </div>
        <div className="flow-body">
          <TransactionImport
            onExtracted={(p) => {
              setImportedProfile({
                ...p, id: profileId,
                assets: p.assets ?? [], goals: p.goals ?? [],
                debts: p.debts ?? [], expenses: p.expenses ?? [],
                emergency_fund: p.emergency_fund ?? 0, risk: p.risk ?? 'MEDIUM',
              });
              setView('import-review');
            }}
          />
        </div>
      </div>
    );
  }

  if (view === 'import-review' && importedProfile) {
    return (
      <div className="profile-flow">
        <div className="flow-header">
          <button className="flow-back" onClick={() => setView('import')}>← Nhập lại</button>
          <span>Xem lại hồ sơ</span>
        </div>
        <div className="flow-body">
          <ProfileBuilder
            initialProfile={importedProfile}
            mode="update"
            onSaved={(saved) => {
              setProfile(saved);
              setView('main');
              onProfileUpdated();
            }}
          />
        </div>
      </div>
    );
  }

  if (view === 'edit' && profile) {
    return (
      <div className="profile-flow">
        <div className="flow-header">
          <button className="flow-back" onClick={() => setView('main')}>← Quay lại</button>
          <span>Chỉnh sửa hồ sơ</span>
        </div>
        <div className="flow-body">
          <ProfileBuilder
            initialProfile={profile}
            mode="update"
            onSaved={(saved) => {
              setProfile(saved);
              setView('main');
              onProfileUpdated();
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="profile-hero">
        <div className="avatar">M</div>
        <h2>Minh</h2>
        <p>Khách hàng Demo</p>
      </div>

      <div className="page-body">
        <div className="pf-card">
          <div className="pf-card-title">Cập nhật hồ sơ</div>
          <button className="pf-action-btn" onClick={() => setView('import')}>
            <div className="pf-action-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="20" height="20">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
            </div>
            <div className="pf-action-text">
              <span>Nhập file giao dịch</span>
              <small>CSV hoặc Excel từ ngân hàng</small>
            </div>
            <span className="pf-action-arrow">›</span>
          </button>
          <button className="pf-action-btn" onClick={() => setView('edit')}>
            <div className="pf-action-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="20" height="20">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </div>
            <div className="pf-action-text">
              <span>Chỉnh sửa thủ công</span>
              <small>Cập nhật thu nhập, chi phí, mục tiêu</small>
            </div>
            <span className="pf-action-arrow">›</span>
          </button>
        </div>

        <button className="logout-btn" onClick={onLogout}>Đăng xuất</button>
      </div>
    </div>
  );
}
