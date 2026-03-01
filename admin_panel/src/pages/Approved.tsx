import React, { useState, useEffect } from 'react';

interface ApprovedUser {
  id: string;
  telegramId: string;
  username: string;
  firstName: string;
  lastName: string;
  approved_at: string;
  status: string;
}

export default function Approved() {
  const [approvedUsers, setApprovedUsers] = useState<ApprovedUser[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch approved users from API
  useEffect(() => {
    const fetchApprovedUsers = async () => {
      try {
        setLoading(true);
        const baseUrl = (import.meta.env.VITE_API_URL as string) || 'http://localhost:5000';
        console.log('🔍 Fetching approved users from:', `${baseUrl}/api/approved-users`);
        
        const response = await fetch(`${baseUrl}/api/approved-users`);
        console.log('📡 Response status:', response.status);
        console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('❌ API Error Response:', errorText);
          throw new Error(`Failed to fetch approved users: ${response.status} ${errorText}`);
        }
        
        const users = await response.json();
        console.log('✅ Fetched approved users from API:', users);
        console.log('📊 Number of users from API:', users.length);
        console.log('📍 Data source: Flask API → Firebase Service → Local JSON file');
        
        if (Array.isArray(users)) {
          setApprovedUsers(users);
        } else {
          console.error('❌ Invalid data format - expected array, got:', typeof users);
          setApprovedUsers([]);
        }
      } catch (error) {
        console.error('❌ Error fetching approved users:', error);
        console.error('❌ Error details:', {
          name: error.name,
          message: error.message,
          stack: error.stack
        });
        
        // Fallback: Try to load from local data
        console.log('🔄 Attempting fallback data loading...');
        await loadFromLocalData();
      } finally {
        setLoading(false);
      }
    };

    fetchApprovedUsers();
  }, []);

  const handleRevoke = async (userId: string) => {
    if (!confirm('Are you sure you want to revoke this user\'s access? This will remove them from the bot allowlist and notify them.')) {
      return;
    }

    try {
      const baseUrl = (import.meta.env.VITE_API_URL as string) || 'http://localhost:5000';
      const response = await fetch(`${baseUrl}/api/users/${userId}/revoke`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to revoke user');
      }

      // Remove user from local state
      setApprovedUsers(prev => prev.filter(user => user.id !== userId));
      console.log('User access revoked successfully');
    } catch (error) {
      console.error('Error revoking user:', error);
      alert('Failed to revoke user access. Please try again.');
    }
  };

  const syncFromFirebase = async () => {
    try {
      const baseUrl = (import.meta.env.VITE_API_URL as string) || 'http://localhost:5000';
      console.log('🔄 Attempting to sync from Firebase...');
      
      const response = await fetch(`${baseUrl}/api/sync-approved-users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Firebase sync successful:', result);
        alert(`Successfully synced ${result.count} users from Firebase`);
        // Refresh the list
        window.location.reload();
      } else {
        const errorText = await response.text();
        console.error('❌ Firebase sync failed:', errorText);
        alert(`Failed to sync from Firebase: ${response.status} ${errorText}`);
      }
    } catch (error) {
      console.error('❌ Error syncing from Firebase:', error);
      alert(`Error syncing from Firebase: ${error.message}`);
    }
  };

  const loadFromLocalData = async () => {
    try {
      console.log('🔄 Attempting to load from local data...');
      
      // Try to fetch from the API first
      const baseUrl = (import.meta.env.VITE_API_URL as string) || 'http://localhost:5000';
      const response = await fetch(`${baseUrl}/api/approved-users`);
      
      if (response.ok) {
        const users = await response.json();
        console.log('✅ Loaded from API:', users);
        console.log('📍 Data source: Flask API → Firebase Service → Local JSON file');
        setApprovedUsers(users);
        return;
      }
    } catch (error) {
      console.log('⚠️ API not available, using fallback data');
    }
    
    // Fallback to static data that matches the local JSON file
    const localData = [
      {
        id: "1929170431",
        telegramId: "1929170431",
        username: "Crypto_seller_man",
        firstName: "Debians",
        lastName: "",
        approved_at: "2025-10-12T04:34:46.785299Z",
        status: "approved"
      },
      {
        id: "7083945790",
        telegramId: "7083945790",
        username: "Unknown",
        firstName: "Unknown",
        lastName: "",
        approved_at: "2025-10-12T04:34:46.785299Z",
        status: "approved"
      }
    ];
    
    console.log('🔄 Using local data fallback:', localData);
    console.log('📍 Data source: Hardcoded fallback data (matches telegram_bot/data/approved_users.json)');
    console.log('⚠️ Note: This is NOT real-time data. Start Flask server for live data.');
    setApprovedUsers(localData);
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '200px',
        fontSize: '16px',
        color: '#64748b'
      }}>
        Loading approved users...
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ margin: 0, color: '#0f172a' }}>Approved Users</h2>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button
            onClick={loadFromLocalData}
            style={{
              background: '#f59e0b',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 12px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            Load Local Data
          </button>
          <button
            onClick={syncFromFirebase}
            style={{
              background: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 12px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            Sync from Firebase
          </button>
          <button
            onClick={() => window.location.reload()}
            style={{
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 12px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            Refresh
          </button>
          <div style={{ 
            background: '#f1f5f9', 
            padding: '8px 12px', 
            borderRadius: '8px', 
            fontSize: '14px',
            color: '#475569'
          }}>
            {approvedUsers.length} approved
          </div>
        </div>
      </div>

      {approvedUsers.length === 0 ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px', 
          background: '#f8fafc', 
          borderRadius: '12px',
          border: '1px solid #e2e8f0'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>✅</div>
          <h3 style={{ margin: '0 0 8px 0', color: '#334155' }}>No Approved Users</h3>
          <p style={{ margin: 0, color: '#64748b' }}>Users will appear here after being approved from the New Comer page.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '16px' }}>
          {approvedUsers.map((user) => (
            <div
              key={user.id}
              style={{
                background: 'white',
                border: '1px solid #e2e8f0',
                borderRadius: '12px',
                padding: '20px',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <div>
                  <h3 style={{ margin: '0 0 4px 0', color: '#0f172a', fontSize: '18px' }}>
                    {user.firstName} {user.lastName}
                  </h3>
                  <p style={{ margin: '0 0 8px 0', color: '#64748b', fontSize: '14px' }}>
                    @{user.username || 'no username'}
                  </p>
                </div>
                <div style={{
                  background: '#dcfce7',
                  color: '#166534',
                  padding: '4px 8px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontWeight: '500'
                }}>
                  ✅ Approved
                </div>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                <div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '2px' }}>Telegram ID</div>
                  <div style={{ fontSize: '14px', color: '#0f172a', fontFamily: 'monospace' }}>
                    {user.telegramId}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '2px' }}>Approved At</div>
                  <div style={{ fontSize: '14px', color: '#0f172a' }}>
                    {formatDate(user.approved_at)}
                  </div>
                </div>
              </div>
              
              <div style={{ 
                background: '#f8fafc', 
                padding: '12px', 
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                marginBottom: '16px'
              }}>
                <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Status</div>
                <div style={{ fontSize: '14px', color: '#059669', fontWeight: '500' }}>
                  🎉 User has full access to the bot
                </div>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  onClick={() => handleRevoke(user.id)}
                  style={{
                    background: '#dc2626',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '8px 16px',
                    fontSize: '14px',
                    fontWeight: '500',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.background = '#b91c1c'}
                  onMouseOut={(e) => e.currentTarget.style.background = '#dc2626'}
                >
                  🚫 Revoke Access
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
