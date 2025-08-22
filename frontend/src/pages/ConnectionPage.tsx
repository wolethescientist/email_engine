import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@context/AuthContext'

export default function ConnectionPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    email: '', password: '',
    imap_host: '', imap_port: 993,
    smtp_host: '', smtp_port: 465,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const formRef = useRef<HTMLFormElement>(null)

  // Detect autofilled values and sync with React state
  useEffect(() => {
    const checkAutofill = () => {
      if (!formRef.current) return
      
      const inputs = formRef.current.querySelectorAll('input')
      const updates: any = {}
      let hasUpdates = false

      inputs.forEach((input) => {
        const name = input.name
        const value = input.value
        
        if (value && !form[name as keyof typeof form]) {
          if (name.includes('port')) {
            updates[name] = Number(value)
          } else {
            updates[name] = value
          }
          hasUpdates = true
        }
      })

      if (hasUpdates) {
        setForm(prev => ({ ...prev, ...updates }))
      }
    }

    // Check immediately and after a short delay for autofill
    checkAutofill()
    const timer = setTimeout(checkAutofill, 100)
    
    return () => clearTimeout(timer)
  }, [])

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setForm((f) => ({ ...f, [name]: name.includes('port') ? Number(value) : value }))
  }

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(form)
      navigate('/mailbox')
    } catch (err: any) {
      let msg = err?.response?.data?.detail || 'Connection failed. Check credentials and servers.'
      
      // Provide more user-friendly error messages
      if (msg.includes('IMAP authentication failed') || msg.includes('IMAP login failed')) {
        msg = 'Email authentication failed. Please check your email and password, and ensure IMAP is enabled for your account.'
      } else if (msg.includes('SMTP login failed')) {
        msg = 'SMTP authentication failed. Please check your email and password, and ensure SMTP is enabled for your account.'
      } else if (msg.includes('connection failed') || msg.includes('timeout')) {
        msg = 'Connection failed. Please check your server settings and internet connection.'
      }
      
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-gradient-green rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
            <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
          </svg>
        </div>
        <h1 className="text-3xl font-bold text-secondary-800 mb-2">Connect Your Email</h1>
        <p className="text-secondary-600">Enter your email credentials to get started</p>
      </div>

      <div className="card">
        <div className="card-body">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start">
                <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                </svg>
                <div>
                  <p className="text-sm font-medium text-red-800">Connection Failed</p>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          <form ref={formRef} onSubmit={onSubmit} className="space-y-6" autoComplete="off">
            <div className="space-y-4">
              <div>
                <label className="form-label">Email Address</label>
                <input 
                  name="email" 
                  type="email" 
                  required 
                  value={form.email} 
                  onChange={onChange} 
                  autoComplete="username" 
                  className="form-input" 
                  placeholder="your.email@example.com"
                />
              </div>
              <div>
                <label className="form-label">Password</label>
                <input 
                  name="password" 
                  type="password" 
                  required 
                  value={form.password} 
                  onChange={onChange} 
                  autoComplete="new-password" 
                  className="form-input" 
                  placeholder="Your email password"
                />
              </div>
            </div>

            <div className="border-t border-secondary-200 pt-6">
              <h3 className="text-lg font-medium text-secondary-800 mb-4">Server Settings</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="form-label">IMAP Host</label>
                  <input 
                    name="imap_host" 
                    required 
                    value={form.imap_host} 
                    onChange={onChange} 
                    className="form-input" 
                    placeholder="imap.gmail.com"
                  />
                </div>
                <div>
                  <label className="form-label">IMAP Port</label>
                  <input 
                    name="imap_port" 
                    type="number" 
                    required 
                    value={form.imap_port} 
                    onChange={onChange} 
                    className="form-input" 
                    placeholder="993"
                  />
                </div>
                <div>
                  <label className="form-label">SMTP Host</label>
                  <input 
                    name="smtp_host" 
                    required 
                    value={form.smtp_host} 
                    onChange={onChange} 
                    className="form-input" 
                    placeholder="smtp.gmail.com"
                  />
                </div>
                <div>
                  <label className="form-label">SMTP Port</label>
                  <input 
                    name="smtp_port" 
                    type="number" 
                    required 
                    value={form.smtp_port} 
                    onChange={onChange} 
                    className="form-input" 
                    placeholder="587"
                  />
                </div>
              </div>
            </div>

            <button disabled={loading} className="w-full btn-primary py-3 text-base">
              {loading ? (
                <div className="flex items-center justify-center">
                  <svg className="w-5 h-5 mr-3 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                  Connecting...
                </div>
              ) : (
                <div className="flex items-center justify-center">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.293l-3-3a1 1 0 00-1.414-1.414L9 5.586 7.707 4.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4a1 1 0 00-1.414-1.414L9 5.586z" clipRule="evenodd"/>
                  </svg>
                  Connect Account
                </div>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
