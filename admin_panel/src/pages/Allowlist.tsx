import { useEffect, useState } from 'react';
import { db } from '../firebase';
import { collection, deleteDoc, doc, getDocs, setDoc } from 'firebase/firestore';

export default function Allowlist() {
  const [ids, setIds] = useState<{ id: string }[]>([]);
  const [newId, setNewId] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const snap = await getDocs(collection(db, 'allowlist'));
    const rows: { id: string }[] = [];
    snap.forEach(d => rows.push({ id: d.id }));
    setIds(rows);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const add = async () => {
    const id = newId.trim();
    if (!id) return;
    await setDoc(doc(db, 'allowlist', id), { approved: true });
    setNewId('');
    await load();
  };

  const remove = async (id: string) => {
    await deleteDoc(doc(db, 'allowlist', id));
    await load();
  };

  if (loading) return <div style={{ padding: 16 }}>Loading allowlist...</div>;

  return (
    <div style={{ padding: 16 }}>
      <h2>Allowlist</h2>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <input value={newId} onChange={e => setNewId(e.target.value)} placeholder="Telegram User ID" />
        <button onClick={add}>Add</button>
      </div>
      <ul>
        {ids.map(item => (
          <li key={item.id} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <code>{item.id}</code>
            <button onClick={() => remove(item.id)}>Remove</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
