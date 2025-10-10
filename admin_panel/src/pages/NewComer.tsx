import { useState, useEffect } from 'react';

interface NewUser {
  id: string;
  username: string;
  telegramId: string;
  firstName: string;
  lastName?: string;
  timestamp: string;
  status: 'pending' | 'approved' | 'rejected';
}

export default function NewComer() {
  const [newUsers, setNewUsers] = useState<NewUser[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch real data from API
  useEffect(() => {
    const fetchNewUsers = async () => {
      try {
        setLoading(true);
        const baseUrl = (import.meta.env.VITE_API_URL as string) || 'http://localhost:5000';
        console.log('Fetching from:', `${baseUrl}/api/new-users`);
        const response = await fetch(`${baseUrl}/api/new-users`);
        console.log('Response status:', response.status);
        if (!response.ok) {
          throw new Error('Failed to fetch users');
        }
        const users = await response.json();
        console.log('Fetched users:', users);
        setNewUsers(users);
      } catch (error) {
        console.error('Error fetching users:', error);
        // Fallback to empty array on error
        setNewUsers([]);
      } finally {
        setLoading(false);
      }
    };

    fetchNewUsers();
  }, []);

  const handleApprove = async (userId: string) => {
    try {
      const baseUrl = (import.meta.env.VITE_API_URL as string) || 'http://localhost:5000';
      const response = await fetch(`${baseUrl}/api/users/${userId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        setNewUsers(users => 
          users.map(user => 
            user.id === userId ? { ...user, status: 'approved' as const } : user
          )
        );
      } else {
        console.error('Failed to approve user');
      }
    } catch (error) {
      console.error('Error approving user:', error);
    }
  };

  const handleReject = async (userId: string) => {
    try {
      const baseUrl = (import.meta.env.VITE_API_URL as string) || 'http://localhost:5000';
      const response = await fetch(`${baseUrl}/api/users/${userId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        setNewUsers(users => 
          users.map(user => 
            user.id === userId ? { ...user, status: 'rejected' as const } : user
          )
        );
      } else {
        console.error('Failed to reject user');
      }
    } catch (error) {
      console.error('Error rejecting user:', error);
    }
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString()
    };
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return '#f59e0b';
      case 'approved': return '#10b981';
      case 'rejected': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending': return 'Pending';
      case 'approved': return 'Approved';
      case 'rejected': return 'Rejected';
      default: return 'Unknown';
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
        <div style={{ color: '#6b7280' }}>Loading new users...</div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ margin: 0, color: '#0f172a' }}>New Comers</h2>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
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
            {newUsers.filter(u => u.status === 'pending').length} pending
          </div>
        </div>
      </div>

      {newUsers.length === 0 ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px', 
          color: '#6b7280',
          background: '#f8fafc',
          borderRadius: '12px',
          border: '1px solid #e2e8f0'
        }}>
          <div style={{ fontSize: '18px', marginBottom: '8px' }}>No new users</div>
          <div>New users will appear here when they start the bot</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '16px' }}>
          {newUsers.map((user) => {
            const { date, time } = formatDate(user.timestamp);
            return (
              <div key={user.id} style={{
                background: 'white',
                border: '1px solid #e2e8f0',
                borderRadius: '12px',
                padding: '20px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '16px', alignItems: 'start' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                      <div style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '50%',
                        background: '#3b82f6',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontWeight: '600',
                        fontSize: '16px'
                      }}>
                        {user.firstName[0]}{user.lastName?.[0] || ''}
                      </div>
                      <div>
                        <div style={{ fontWeight: '600', color: '#0f172a', marginBottom: '4px' }}>
                          {user.firstName} {user.lastName}
                        </div>
                        <div style={{ color: '#6b7280', fontSize: '14px' }}>@{user.username}</div>
                      </div>
                    </div>
                    
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', marginBottom: '16px' }}>
                      <div>
                        <div style={{ color: '#6b7280', fontSize: '12px', marginBottom: '4px' }}>Telegram ID</div>
                        <div style={{ color: '#0f172a', fontWeight: '500' }}>{user.telegramId}</div>
                      </div>
                      <div>
                        <div style={{ color: '#6b7280', fontSize: '12px', marginBottom: '4px' }}>Joined</div>
                        <div style={{ color: '#0f172a', fontWeight: '500' }}>{date} at {time}</div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ 
                        background: getStatusColor(user.status),
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: '500'
                      }}>
                        {getStatusText(user.status)}
                      </div>
                    </div>
                  </div>

                  {user.status === 'pending' && (
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => handleApprove(user.id)}
                        style={{
                          background: '#10b981',
                          color: 'white',
                          border: 'none',
                          borderRadius: '8px',
                          padding: '8px 16px',
                          fontSize: '14px',
                          fontWeight: '500',
                          cursor: 'pointer',
                          transition: 'background 0.2s'
                        }}
                        onMouseOver={(e) => e.currentTarget.style.background = '#059669'}
                        onMouseOut={(e) => e.currentTarget.style.background = '#10b981'}
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(user.id)}
                        style={{
                          background: '#ef4444',
                          color: 'white',
                          border: 'none',
                          borderRadius: '8px',
                          padding: '8px 16px',
                          fontSize: '14px',
                          fontWeight: '500',
                          cursor: 'pointer',
                          transition: 'background 0.2s'
                        }}
                        onMouseOver={(e) => e.currentTarget.style.background = '#dc2626'}
                        onMouseOut={(e) => e.currentTarget.style.background = '#ef4444'}
                      >
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


