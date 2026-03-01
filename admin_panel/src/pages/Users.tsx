import { useState, useEffect } from 'react'
import { collection, getDocs } from 'firebase/firestore'
import { db } from '../firebase'

interface User {
  id: string
  telegramId: string
  username: string
  firstName: string
  lastName?: string
  timestamp: string
  status: string
  totalGenerated?: number
  todayGenerated?: number
  totalUnpaid?: number
  lastActivity?: string
  paymentStatus?: 'paid' | 'unpaid' | 'partial'
}

function Users() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'active' | 'inactive' | 'unpaid'>('all')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch users from Firebase Firestore
      const usersCollection = collection(db, 'users')
      const querySnapshot = await getDocs(usersCollection)
      
      const fetchedUsers: User[] = []
      
      querySnapshot.forEach((doc) => {
        const data = doc.data()
        const userId = doc.id
        
        // Map Firebase data to User interface
        const user: User = {
          id: userId,
          telegramId: data.telegramId || userId,
          username: data.username || '',
          firstName: data.firstName || '',
          lastName: data.lastName || '',
          timestamp: data.created_at || data.timestamp || new Date().toISOString(),
          status: data.access_status || data.status || 'not approved',
          totalGenerated: data.total_ids || data.totalGenerated || 0,
          todayGenerated: data.today_ids || data.todayGenerated || 0,
          totalUnpaid: data.unpaid || data.totalUnpaid || 0,
          lastActivity: data.lastActivity || data.updated_at || data.created_at || '',
          paymentStatus: (() => {
            const unpaid = data.unpaid || data.totalUnpaid || 0
            const paid = data.paid || 0
            if (unpaid === 0 && paid > 0) return 'paid'
            if (unpaid > 0 && paid === 0) return 'unpaid'
            if (unpaid > 0 && paid > 0) return 'partial'
            return 'paid'
          })()
        }
        
        fetchedUsers.push(user)
      })
      
      // Sort by timestamp (most recent first)
      fetchedUsers.sort((a, b) => {
        const timeA = new Date(a.timestamp).getTime()
        const timeB = new Date(b.timestamp).getTime()
        return timeB - timeA
      })
      
      setUsers(fetchedUsers)
    } catch (err) {
      setError('Failed to fetch users from Firebase')
      console.error('Error fetching users:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleStatusChange = async (userId: string, newStatus: string) => {
    try {
      const baseUrl = (import.meta.env.VITE_API_URL as string) || 'http://localhost:5000'
      const response = await fetch(`${baseUrl}/api/users/${userId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus })
      })
      
      if (response.ok) {
        // After successful status change, refresh the list
        await fetchUsers()
      } else {
        const error = await response.json()
        console.error('Failed to update user status:', error)
        setError(`Failed to update status: ${error.error || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Error changing user status:', err)
      setError('Failed to update user status. Please try again.')
    }
  }

  const handleSendReport = async (userId: string) => {
    try {
      // TODO: Implement send report API call
      console.log('Sending report to user:', userId)
    } catch (err) {
      console.error('Error sending report:', err)
    }
  }

  const handleMarkAsPaid = async (userId: string) => {
    try {
      // TODO: Implement mark as paid API call
      console.log('Marking user as paid:', userId)
      // After successful payment marking, refresh the list
      fetchUsers()
    } catch (err) {
      console.error('Error marking user as paid:', err)
    }
  }

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.firstName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.lastName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.telegramId.includes(searchTerm)
    
    const matchesFilter = filter === 'all' || 
                         (filter === 'active' && user.status === 'approved') ||
                         (filter === 'inactive' && user.status !== 'approved') ||
                         (filter === 'unpaid' && user.paymentStatus === 'unpaid')
    
    return matchesSearch && matchesFilter
  })

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <div>Loading users...</div>
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
        <h2 style={{ margin: 0 }}>Users Management</h2>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={fetchUsers}
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
          {filteredUsers.length} users
        </span>
      </div>

      {/* Filters and Search */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '20px', alignItems: 'center' }}>
        <input
          type="text"
          placeholder="Search users..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{
            padding: '8px 12px',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            fontSize: '14px',
            minWidth: '200px'
          }}
        />
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as any)}
          style={{
            padding: '8px 12px',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            fontSize: '14px'
          }}
        >
          <option value="all">All Users</option>
          <option value="active">Active Users</option>
          <option value="inactive">Inactive Users</option>
          <option value="unpaid">Unpaid Users</option>
        </select>
      </div>

      {filteredUsers.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          No users found
        </div>
      ) : (
        <div style={{ 
          background: '#fff',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          overflow: 'hidden',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          {/* Table Header */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 1fr 2fr',
            gap: '16px',
            padding: '16px 20px',
            background: '#f8fafc',
            borderBottom: '1px solid #e5e7eb',
            fontWeight: '600',
            fontSize: '14px',
            color: '#374151'
          }}>
            <div>User</div>
            <div>Status</div>
            <div>Today's IDs</div>
            <div>Total IDs</div>
            <div>Paid</div>
            <div>Unpaid</div>
            <div>Actions</div>
          </div>

          {/* Table Body */}
          {filteredUsers.map((user, index) => (
            <div
              key={user.id}
              style={{
                display: 'grid',
                gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 1fr 2fr',
                gap: '16px',
                padding: '16px 20px',
                borderBottom: index < filteredUsers.length - 1 ? '1px solid #f1f5f9' : 'none',
                alignItems: 'center',
                fontSize: '14px'
              }}
            >
              {/* User Column */}
              <div>
                <div style={{ fontWeight: '600', marginBottom: '4px' }}>
                  {user.firstName} {user.lastName}
                </div>
                <div style={{ color: '#666', fontSize: '12px' }}>
                  @{user.username}
                </div>
                <div style={{ color: '#666', fontSize: '12px' }}>
                  ID: {user.telegramId}
                </div>
              </div>

              {/* Status Column */}
              <div>
                <span style={{ 
                  background: (() => {
                    if (user.status === 'approved') return '#dcfce7'
                    if (user.status === 'pending' || user.status === 'not approved') return '#fef3c7'
                    if (user.status === 'paused') return '#fef3c7'
                    return '#fef2f2'
                  })(),
                  color: (() => {
                    if (user.status === 'approved') return '#16a34a'
                    if (user.status === 'pending' || user.status === 'not approved') return '#d97706'
                    if (user.status === 'paused') return '#d97706'
                    return '#dc2626'
                  })(),
                  padding: '4px 8px', 
                  borderRadius: '4px', 
                  fontSize: '12px',
                  fontWeight: '500',
                  textTransform: 'capitalize'
                }}>
                  {user.status === 'not approved' ? 'Not Approved' : user.status}
                </span>
              </div>

              {/* Today's IDs Column */}
              <div style={{ 
                fontWeight: '600',
                color: (user.todayGenerated || 0) > 0 ? '#059669' : '#6b7280'
              }}>
                {user.todayGenerated || 0}
              </div>

              {/* Total IDs Column */}
              <div style={{ 
                fontWeight: '600',
                color: (user.totalGenerated || 0) > 0 ? '#0369a1' : '#6b7280'
              }}>
                {user.totalGenerated || 0}
              </div>

              {/* Paid Column */}
              <div style={{ 
                fontWeight: '600',
                color: '#059669'
              }}>
                {((user.totalGenerated || 0) - (user.totalUnpaid || 0))}
              </div>

              {/* Unpaid Column */}
              <div style={{ 
                fontWeight: '600',
                color: (user.totalUnpaid || 0) > 0 ? '#dc2626' : '#6b7280'
              }}>
                {user.totalUnpaid || 0}
                {(user.totalUnpaid || 0) > 0 && (
                  <div style={{ fontSize: '11px', color: '#dc2626', marginTop: '2px' }}>
                    {(user.totalUnpaid || 0) * 50} birr
                  </div>
                )}
              </div>

              {/* Actions Column */}
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                <button
                  onClick={() => handleStatusChange(user.telegramId, user.status === 'approved' ? 'paused' : 'approved')}
                  style={{
                    background: user.status === 'approved' ? '#f59e0b' : '#10b981',
                    color: 'white',
                    border: 'none',
                    padding: '6px 10px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: '500'
                  }}
                  title={user.status === 'approved' ? 'Pause User' : 'Resume User'}
                >
                  {user.status === 'approved' ? '⏸️' : '▶️'}
                </button>
                
                <button
                  onClick={() => handleSendReport(user.id)}
                  style={{
                    background: '#6366f1',
                    color: 'white',
                    border: 'none',
                    padding: '6px 10px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: '500'
                  }}
                  title="Send Report"
                >
                  📊
                </button>
                
                {(user.totalUnpaid || 0) > 0 && (
                  <button
                    onClick={() => handleMarkAsPaid(user.id)}
                    style={{
                      background: '#059669',
                      color: 'white',
                      border: 'none',
                      padding: '6px 10px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px',
                      fontWeight: '500'
                    }}
                    title="Mark as Paid"
                  >
                    💳
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Users