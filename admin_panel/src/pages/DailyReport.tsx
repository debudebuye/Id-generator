import { useState, useEffect } from 'react'

interface UserReport {
  user_id: number
  username: string
  count: number
  paid: number
  unpaid: number
  payment_due: number
}

interface UserStatus {
  status: 'active' | 'paused'
  paused_at?: string
  paused_by?: string
  resumed_at?: string
  resumed_by?: string
}

interface BotStatus {
  paused: boolean
  paused_by?: string
  paused_at?: string
  resumed_by?: string
  resumed_at?: string
}

interface DailyReport {
  date: string
  total_users: number
  total_generated: number
  users: UserReport[]
}

export default function DailyReport() {
  const [reports, setReports] = useState<Record<string, DailyReport>>({})
  const [selectedDate, setSelectedDate] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [userStatuses, setUserStatuses] = useState<Record<string, UserStatus>>({})
  const [activeTab, setActiveTab] = useState<'overall' | 'individual'>('overall')
  const [botStatus, setBotStatus] = useState<BotStatus>({ paused: false })

  useEffect(() => {
    fetchDailyReports()
    fetchUserStatuses()
    fetchBotStatus()
  }, [])

  const fetchDailyReports = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:5000/api/daily-reports')
      const data = await response.json()
      
      if (data.success) {
        setReports(data.reports)
        // Set today as default selected date
        const today = new Date().toISOString().split('T')[0]
        setSelectedDate(today)
      } else {
        setError(data.error || 'Failed to fetch reports')
      }
    } catch (err) {
      setError('Failed to fetch daily reports')
      console.error('Error fetching reports:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchUserStatuses = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/user-statuses')
      const data = await response.json()
      
      if (data.success) {
        setUserStatuses(data.statuses)
      }
    } catch (err) {
      console.error('Error fetching user statuses:', err)
    }
  }

  const pauseUser = async (userId: number) => {
    try {
      const response = await fetch(`http://localhost:5000/api/users/${userId}/pause`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ paused_by: 'admin' }),
      })
      
      const data = await response.json()
      
      if (data.success) {
        await fetchUserStatuses()
      } else {
        setError(data.error || 'Failed to pause user')
      }
    } catch (err) {
      setError('Failed to pause user')
      console.error('Error pausing user:', err)
    }
  }

  const resumeUser = async (userId: number) => {
    try {
      const response = await fetch(`http://localhost:5000/api/users/${userId}/resume`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ resumed_by: 'admin' }),
      })
      
      const data = await response.json()
      
      if (data.success) {
        await fetchUserStatuses()
      } else {
        setError(data.error || 'Failed to resume user')
      }
    } catch (err) {
      setError('Failed to resume user')
      console.error('Error resuming user:', err)
    }
  }

  const markPaymentPaid = async (userId: number, date?: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/users/${userId}/mark-paid`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ date }),
      })
      
      const data = await response.json()
      
      if (data.success) {
        await fetchDailyReports()
      } else {
        setError(data.error || 'Failed to mark payment as paid')
      }
    } catch (err) {
      setError('Failed to mark payment as paid')
      console.error('Error marking payment as paid:', err)
    }
  }

  const generateReport = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/generate-daily-report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ date: selectedDate || undefined }),
      })
      
      const data = await response.json()
      
      if (data.success) {
        // Refresh reports
        await fetchDailyReports()
      } else {
        setError(data.error || 'Failed to generate report')
      }
    } catch (err) {
      setError('Failed to generate report')
      console.error('Error generating report:', err)
    }
  }

  const fetchBotStatus = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/bot/status')
      const data = await response.json()
      
      if (data.success) {
        setBotStatus(data.status)
      }
    } catch (err) {
      console.error('Error fetching bot status:', err)
    }
  }

  const pauseBot = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/bot/pause', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ paused_by: 'admin' }),
      })
      
      const data = await response.json()
      
      if (data.success) {
        await fetchBotStatus() // Refresh bot status
      } else {
        setError(data.error || 'Failed to pause bot')
      }
    } catch (err) {
      setError('Failed to pause bot')
      console.error('Error pausing bot:', err)
    }
  }

  const resumeBot = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/bot/resume', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ resumed_by: 'admin' }),
      })
      
      const data = await response.json()
      
      if (data.success) {
        await fetchBotStatus() // Refresh bot status
      } else {
        setError(data.error || 'Failed to resume bot')
      }
    } catch (err) {
      setError('Failed to resume bot')
      console.error('Error resuming bot:', err)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-ET', {
      style: 'currency',
      currency: 'ETB',
      minimumFractionDigits: 0
    }).format(amount)
  }

  const selectedReport = selectedDate ? reports[selectedDate] : null
  const totalRevenue = selectedReport?.users.reduce((sum, user) => sum + user.payment_due, 0) || 0

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
        <div>Loading daily reports...</div>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ marginTop: 0 }}>Daily Report</h2>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {/* Bot Control Section */}
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            padding: '8px 12px',
            backgroundColor: botStatus.paused ? '#fef2f2' : '#f0f9ff',
            border: `1px solid ${botStatus.paused ? '#fecaca' : '#bae6fd'}`,
            borderRadius: '6px'
          }}>
            <div style={{ 
              width: '8px', 
              height: '8px', 
              borderRadius: '50%', 
              backgroundColor: botStatus.paused ? '#ef4444' : '#10b981' 
            }}></div>
            <span style={{ fontSize: '14px', fontWeight: '500' }}>
              Bot: {botStatus.paused ? 'Paused' : 'Active'}
            </span>
            {botStatus.paused ? (
              <button
                onClick={resumeBot}
                style={{
                  backgroundColor: '#10b981',
                  color: 'white',
                  border: 'none',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
              >
                Resume
              </button>
            ) : (
              <button
                onClick={pauseBot}
                style={{
                  backgroundColor: '#ef4444',
                  color: 'white',
                  border: 'none',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
              >
                Pause
              </button>
            )}
          </div>
          
          <button
            onClick={generateReport}
            style={{
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Generate Today's Report
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0' }}>
          <button
            onClick={() => setActiveTab('overall')}
            style={{
              padding: '12px 24px',
              border: 'none',
              backgroundColor: 'transparent',
              borderBottom: activeTab === 'overall' ? '2px solid #3b82f6' : '2px solid transparent',
              color: activeTab === 'overall' ? '#3b82f6' : '#6b7280',
              cursor: 'pointer',
              fontWeight: activeTab === 'overall' ? '600' : '400'
            }}
          >
            Overall Report
          </button>
          <button
            onClick={() => setActiveTab('individual')}
            style={{
              padding: '12px 24px',
              border: 'none',
              backgroundColor: 'transparent',
              borderBottom: activeTab === 'individual' ? '2px solid #3b82f6' : '2px solid transparent',
              color: activeTab === 'individual' ? '#3b82f6' : '#6b7280',
              cursor: 'pointer',
              fontWeight: activeTab === 'individual' ? '600' : '400'
            }}
          >
            Individual Users
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          color: '#dc2626',
          padding: '12px',
          borderRadius: '6px',
          marginBottom: '16px'
        }}>
          {error}
        </div>
      )}

      <div style={{ marginBottom: '24px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
          Select Date:
        </label>
        <select
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          style={{
            padding: '8px 12px',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            minWidth: '200px'
          }}
        >
          <option value="">Select a date</option>
          {Object.keys(reports).sort().reverse().map(date => (
            <option key={date} value={date}>
              {formatDate(date)}
            </option>
          ))}
        </select>
      </div>

      {activeTab === 'overall' ? (
        selectedReport ? (
          <div>
            <div style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              padding: '20px',
              marginBottom: '24px'
            }}>
              <h3 style={{ marginTop: 0, marginBottom: '16px' }}>Report Summary - {formatDate(selectedReport.date)}</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3b82f6' }}>
                    {selectedReport.total_users}
                  </div>
                  <div style={{ color: '#6b7280' }}>Active Users</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>
                    {selectedReport.total_generated}
                  </div>
                  <div style={{ color: '#6b7280' }}>IDs Generated</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>
                    {formatCurrency(totalRevenue)}
                  </div>
                  <div style={{ color: '#6b7280' }}>Total Revenue</div>
                </div>
              </div>
            </div>

            <div style={{
              backgroundColor: 'white',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <div style={{
                backgroundColor: '#f8fafc',
                padding: '16px',
                borderBottom: '1px solid #e2e8f0',
                fontWeight: '600'
              }}>
                User Details
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f8fafc' }}>
                      <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e2e8f0' }}>User</th>
                      <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e2e8f0' }}>Total IDs</th>
                      <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e2e8f0' }}>Paid</th>
                      <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e2e8f0' }}>Unpaid</th>
                      <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #e2e8f0' }}>Payment Due</th>
                      <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e2e8f0' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedReport.users.map((user, index) => (
                      <tr key={user.user_id} style={{ borderBottom: index < selectedReport.users.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                        <td style={{ padding: '12px' }}>
                          <div>
                            <div style={{ fontWeight: '500' }}>{user.username}</div>
                            <div style={{ fontSize: '14px', color: '#6b7280' }}>ID: {user.user_id}</div>
                          </div>
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          <span style={{
                            backgroundColor: '#dbeafe',
                            color: '#1e40af',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '14px',
                            fontWeight: '500'
                          }}>
                            {user.count}
                          </span>
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          <span style={{
                            backgroundColor: '#d1fae5',
                            color: '#065f46',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '14px',
                            fontWeight: '500'
                          }}>
                            {user.paid}
                          </span>
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          <span style={{
                            backgroundColor: '#fee2e2',
                            color: '#991b1b',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '14px',
                            fontWeight: '500'
                          }}>
                            {user.unpaid}
                          </span>
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right', fontWeight: '500' }}>
                          {formatCurrency(user.payment_due)}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          {user.unpaid > 0 && (
                            <button
                              onClick={() => markPaymentPaid(user.user_id, selectedDate)}
                              style={{
                                backgroundColor: '#10b981',
                                color: 'white',
                                border: 'none',
                                padding: '6px 12px',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '14px'
                              }}
                              title="Mark payment as paid"
                            >
                              Paid
                            </button>
                          )}
                          {user.unpaid === 0 && (
                            <span style={{
                              backgroundColor: '#d1fae5',
                              color: '#065f46',
                              padding: '4px 8px',
                              borderRadius: '4px',
                              fontSize: '12px',
                              fontWeight: '500'
                            }}>
                              ✓ Paid
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : (
          <div style={{
            backgroundColor: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            padding: '40px',
            textAlign: 'center',
            color: '#6b7280'
          }}>
            {Object.keys(reports).length === 0 ? (
              <div>
                <div style={{ fontSize: '18px', marginBottom: '8px' }}>No reports available</div>
                <div>Generate a report to see daily statistics</div>
              </div>
            ) : (
              <div>
                <div style={{ fontSize: '18px', marginBottom: '8px' }}>Select a date to view report</div>
                <div>Choose a date from the dropdown above</div>
              </div>
            )}
          </div>
        )
      ) : (
        <div>
          <div style={{
            backgroundColor: 'white',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            <div style={{
              backgroundColor: '#f8fafc',
              padding: '16px',
              borderBottom: '1px solid #e2e8f0',
              fontWeight: '600'
            }}>
              Individual User Management
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8fafc' }}>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e2e8f0' }}>User</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e2e8f0' }}>Status</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e2e8f0' }}>Today's IDs</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e2e8f0' }}>Paid</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e2e8f0' }}>Unpaid</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #e2e8f0' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(userStatuses).map(([userId, status], index) => {
                    const userReport = selectedReport?.users.find(u => u.user_id === parseInt(userId))
                    return (
                      <tr key={userId} style={{ borderBottom: index < Object.keys(userStatuses).length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                        <td style={{ padding: '12px' }}>
                          <div>
                            <div style={{ fontWeight: '500' }}>User {userId}</div>
                            <div style={{ fontSize: '14px', color: '#6b7280' }}>ID: {userId}</div>
                          </div>
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          <span style={{
                            backgroundColor: status.status === 'active' ? '#d1fae5' : '#fee2e2',
                            color: status.status === 'active' ? '#065f46' : '#991b1b',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '14px',
                            fontWeight: '500'
                          }}>
                            {status.status === 'active' ? 'Active' : 'Paused'}
                          </span>
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          {userReport?.count || 0}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          <span style={{
                            backgroundColor: '#d1fae5',
                            color: '#065f46',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '14px',
                            fontWeight: '500'
                          }}>
                            {userReport?.paid || 0}
                          </span>
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          <span style={{
                            backgroundColor: '#fee2e2',
                            color: '#991b1b',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '14px',
                            fontWeight: '500'
                          }}>
                            {userReport?.unpaid || 0}
                          </span>
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          <div style={{ display: 'flex', gap: '4px', justifyContent: 'center', flexWrap: 'wrap' }}>
                            {status.status === 'active' ? (
                              <button
                                onClick={() => pauseUser(parseInt(userId))}
                                style={{
                                  backgroundColor: '#ef4444',
                                  color: 'white',
                                  border: 'none',
                                  padding: '4px 8px',
                                  borderRadius: '4px',
                                  cursor: 'pointer',
                                  fontSize: '12px'
                                }}
                              >
                                Pause
                              </button>
                            ) : (
                              <button
                                onClick={() => resumeUser(parseInt(userId))}
                                style={{
                                  backgroundColor: '#10b981',
                                  color: 'white',
                                  border: 'none',
                                  padding: '4px 8px',
                                  borderRadius: '4px',
                                  cursor: 'pointer',
                                  fontSize: '12px'
                                }}
                              >
                                Resume
                              </button>
                            )}
                            {userReport && userReport.unpaid > 0 && (
                              <button
                                onClick={() => markPaymentPaid(parseInt(userId), selectedDate)}
                                style={{
                                  backgroundColor: '#3b82f6',
                                  color: 'white',
                                  border: 'none',
                                  padding: '4px 8px',
                                  borderRadius: '4px',
                                  cursor: 'pointer',
                                  fontSize: '12px'
                                }}
                                title="Mark payment as paid"
                              >
                                Paid
                              </button>
                            )}
                            {userReport && userReport.unpaid === 0 && (
                              <span style={{
                                backgroundColor: '#d1fae5',
                                color: '#065f46',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                fontSize: '10px',
                                fontWeight: '500'
                              }}>
                                ✓ Paid
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


