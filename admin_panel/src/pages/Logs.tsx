import { useEffect, useState } from 'react';
import { db } from '../firebase';
import { collection, getDocs, limit, orderBy, query } from 'firebase/firestore';

interface LogItem {
  id: string;
  userId: number;
  username?: string;
  idType?: string;
  variant?: string;
  afterHours?: boolean;
  approved?: boolean;
  timestamp?: any;
}

export default function Logs() {
  const [items, setItems] = useState<LogItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const q = query(collection(db, 'generation_logs'), orderBy('timestamp', 'desc'), limit(50));
      const snap = await getDocs(q);
      const rows: LogItem[] = [];
      snap.forEach(d => {
        const data: any = d.data();
        rows.push({ id: d.id, ...data });
      });
      setItems(rows);
      setLoading(false);
    })();
  }, []);

  if (loading) return <div style={{ padding: 16 }}>Loading logs...</div>;

  return (
    <div style={{ padding: 16 }}>
      <h2>Generation Logs</h2>
      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead>
          <tr>
            <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: 8 }}>Time (UTC)</th>
            <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: 8 }}>User</th>
            <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: 8 }}>Type</th>
            <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: 8 }}>Variant</th>
            <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: 8 }}>After-hours</th>
            <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: 8 }}>Approved</th>
          </tr>
        </thead>
        <tbody>
          {items.map(it => (
            <tr key={it.id}>
              <td style={{ padding: 8 }}>{it.timestamp?.toDate ? it.timestamp.toDate().toISOString() : '-'}</td>
              <td style={{ padding: 8 }}>{it.userId} {it.username ? `(${it.username})` : ''}</td>
              <td style={{ padding: 8 }}>{it.idType || '-'}</td>
              <td style={{ padding: 8 }}>{it.variant || '-'}</td>
              <td style={{ padding: 8 }}>{it.afterHours ? 'Yes' : 'No'}</td>
              <td style={{ padding: 8 }}>{it.approved ? 'Yes' : 'No'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
