import { useEffect, useState } from 'react';
import { db } from '../firebase';
import { doc, getDoc, setDoc } from 'firebase/firestore';

export default function Settings() {
  const [start, setStart] = useState('09:00');
  const [end, setEnd] = useState('17:00');
  const [requireApproval, setRequireApproval] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      const ref = doc(db, 'settings', 'global');
      const snap = await getDoc(ref);
      if (snap.exists()) {
        const d: any = snap.data();
        if (d.operatingStartHHMM) setStart(d.operatingStartHHMM);
        if (d.operatingEndHHMM) setEnd(d.operatingEndHHMM);
        if (typeof d.requireAfterHoursApproval === 'boolean') setRequireApproval(d.requireAfterHoursApproval);
      }
      setLoading(false);
    })();
  }, []);

  const save = async () => {
    setSaving(true);
    const ref = doc(db, 'settings', 'global');
    await setDoc(ref, {
      operatingStartHHMM: start,
      operatingEndHHMM: end,
      requireAfterHoursApproval: requireApproval,
    }, { merge: true });
    setSaving(false);
    alert('Settings saved');
  };

  if (loading) return <div style={{ padding: 16 }}>Loading settings...</div>;

  return (
    <div style={{ padding: 16 }}>
      <h2>Settings</h2>
      <div style={{ display: 'grid', gap: 12, maxWidth: 400 }}>
        <label>
          Operating start (HH:MM)
          <input value={start} onChange={e => setStart(e.target.value)} placeholder="09:00" style={{ display: 'block', padding: 8, width: '100%' }} />
        </label>
        <label>
          Operating end (HH:MM)
          <input value={end} onChange={e => setEnd(e.target.value)} placeholder="17:00" style={{ display: 'block', padding: 8, width: '100%' }} />
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input type="checkbox" checked={requireApproval} onChange={e => setRequireApproval(e.target.checked)} />
          Require after-hours admin approval
        </label>
        <button disabled={saving} onClick={save} style={{ padding: '8px 12px' }}>{saving ? 'Saving...' : 'Save'}</button>
      </div>
    </div>
  );
}
