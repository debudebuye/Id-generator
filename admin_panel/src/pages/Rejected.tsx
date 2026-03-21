import { useState, useEffect } from 'react'

interface RejectedUser {
  id: string
  telegramId: string
  username: string
  firstName: string
  lastName: string
  timestamp: string
  status: string
}

function Rejected() {
  const [rejectedUsers, setRejectedUsers] = useState<RejectedUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchRejectedUsers()
  }, [])

  const fetchRejectedUsers = async () => {
    try {
      setLoading(true)
      // TODO: Replace with actual API endpoint
      // const response = await fetch('/api/rejected-users')
      // const data = await response.json()
      // setRejectedUsers(data)
      
      // Placeholder data for now
      setRejectedUsers([
        {
          id: '1',
          telegramId: '123456789',
          username: 'rejected_user1',
          firstName: 'John',
          lastName: 'Doe',
          timestamp: '2024-01-15T10:30:00Z',
          status: 'rejected'
        }
      ])
    } catch (err) {
      setError('Failed to fetch rejected users')
      console.error('Error fetching rejected users:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleReactivate = async (userId: string) => {
    try {
      // TODO: Implement reactivation API call
      console.log('Reactivating user:', userId)
      // After successful reactivation, refresh the list
      fetchRejectedUsers()
    } catch (err) {
      console.error('Error reactivating user:', err)
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <div>Loading rejected users...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ color: 'red', textAlign: 'center', padding: '20px' }}>
        {error}
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ margin: 0 }}>Rejected Users</h2>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={fetchRejectedUsers}
            style={{ 
              background: '#3b82f6', 
              color: 'white', 
              border: 'none', 
              padding: '8px 16px', 
              borderRadius: '6px', 
              cursor: 'pointer' 
            }}
          >
            Refresh
          </button>
        </div>
        <span style={{ color: '#666', fontSize: '14px' }}>
          {rejectedUsers.length} rejected
        </span>
      </div>

      {rejectedUsers.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          No rejected users found
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '16px' }}>
          {rejectedUsers.map((user) => (
            <div
              key={user.id}
              style={{
                background: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '16px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 style={{ margin: '0 0 8px 0', fontSize: '18px' }}>
                    {user.firstName} {user.lastName}
                  </h3>
                  <div style={{ color: '#666', fontSize: '14px', marginBottom: '4px' }}>
                    @{user.username}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '12px' }}>
                    <div>
                      <strong>Telegram ID</strong>
                      <div style={{ color: '#666' }}>{user.telegramId}</div>
                    </div>
                    <div>
                      <strong>Rejected At</strong>
                      <div style={{ color: '#666' }}>
                        {new Date(user.timestamp).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ 
                    background: '#fef2f2', 
                    color: '#dc2626', 
                    padding: '4px 8px', 
                    borderRadius: '4px', 
                    fontSize: '12px',
                    fontWeight: '500'
                  }}>
                    Rejected
                  </span>
                </div>
              </div>
              
              <div style={{ 
                marginTop: '16px', 
                padding: '12px', 
                background: '#f9fafb', 
                borderRadius: '6px',
                fontSize: '14px',
                color: '#666'
              }}>
                🚫 User access has been rejected and cannot use the bot
              </div>

              <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  onClick={() => handleReactivate(user.id)}
                  style={{
                    background: '#10b981',
                    color: 'white',
                    border: 'none',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  ↻ Reactivate User
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Rejected