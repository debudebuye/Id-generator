import { useEffect, useState } from 'react';
import { db } from '../firebase';
import { collection, getDocs, orderBy, query, updateDoc, doc, where } from 'firebase/firestore';

interface Approval {
  id: string;
  userId: number;
  username?: string;
  status: 'pending' | 'approved' | 'denied';
}

export default function Approvals() {
  const [items, setItems] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const q = query(collection(db, 'approvals'), where('status', '==', 'pending'));
    const snap = await getDocs(q);
    const rows: Approval[] = [];
    snap.forEach(d => {
      const data: any = d.data();
      rows.push({ id: d.id, userId: data.userId, username: data.username, status: data.status });
    });
    setItems(rows);
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const act = async (id: string, status: 'approved' | 'denied') => {
    await updateDoc(doc(db, 'approvals', id), { status });
    await load();
  };

  if (loading) return <div style={{ padding: 16 }}>Loading approvals...</div>;

  return (
    <div style={{ padding: 16 }}>
      <h2>Approvals</h2>
      {items.length === 0 ? (
        <div>No pending approvals.</div>
      ) : (
        <table style={{ borderCollapse: 'collapse', width: '100%' }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: 8 }}>User ID</th>
              <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: 8 }}>Username</th>
              <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: 8 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map(it => (
              <tr key={it.id}>
                <td style={{ padding: 8 }}>{it.userId}</td>
                <td style={{ padding: 8 }}>{it.username || '-'}</td>
                <td style={{ padding: 8, display: 'flex', gap: 8 }}>
                  <button onClick={() => act(it.id, 'approved')}>Approve</button>
                  <button onClick={() => act(it.id, 'denied')}>Deny</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
