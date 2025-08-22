import { Route, Routes, Navigate, Link, useLocation } from 'react-router-dom'
import LandingPage from '@pages/LandingPage'
import SignUpPage from '@pages/SignUpPage'
import LoginPage from '@pages/LoginPage'
import ConnectionPage from '@pages/ConnectionPage'
import MailboxPage from '@pages/MailboxPage'
import EmailDetailPage from '@pages/EmailDetailPage'
import ComposePage from '@pages/ComposePage'
import NotFoundPage from '@pages/NotFoundPage'
import ErrorPage from '@pages/ErrorPage'
import LandingLayout from '@components/LandingLayout'
import { AuthProvider, useAuth } from '@context/AuthContext'

function PrivateRoute({ children }: { children: JSX.Element }) {
  const { token } = useAuth()
  return token ? children : <Navigate to="/" replace />
}

function PublicRoute({ children }: { children: JSX.Element }) {
  const { token } = useAuth()
  return token ? <Navigate to="/mailbox" replace /> : children
}

function AppLayout({ children }: { children: React.ReactNode }) {
  const { token, logout } = useAuth()
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white/80 backdrop-blur-lg border-b border-secondary-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link to={token ? "/mailbox" : "/"} className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-green rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
                  <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
                </svg>
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
                ConnexxionEngine
              </span>
            </Link>
            <nav className="flex items-center space-x-6">
              {token ? (
                <>
                  <Link to="/mailbox" className="btn-ghost">
                    <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
                      <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
                    </svg>
                    Mailbox
                  </Link>
                  <Link to="/compose" className="btn-ghost">
                    <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd"/>
                    </svg>
                    Compose
                  </Link>
                  <button 
                    onClick={logout} 
                    className="text-sm text-red-600 hover:text-red-700 hover:bg-red-50 px-3 py-1.5 rounded-lg transition-colors duration-200"
                  >
                    <svg className="w-4 h-4 mr-2 inline" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clipRule="evenodd"/>
                    </svg>
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link 
                    to="/login" 
                    className="text-sm text-secondary-600 hover:text-secondary-800 hover:bg-secondary-50 px-3 py-1.5 rounded-lg transition-colors duration-200"
                  >
                    Log In
                  </Link>
                  <Link 
                    to="/signup" 
                    className="text-sm bg-gradient-green text-white px-4 py-2 rounded-lg font-medium shadow-green hover:shadow-medium hover:scale-105 transition-all duration-200"
                  >
                    Sign Up Free
                  </Link>
                </>
              )}
            </nav>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8">{children}</main>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public routes with landing layout */}
        <Route path="/" element={<PublicRoute><LandingPage /></PublicRoute>} errorElement={<ErrorPage />} />
        <Route path="/signup" element={<PublicRoute><LandingLayout><SignUpPage /></LandingLayout></PublicRoute>} errorElement={<ErrorPage />} />
        <Route path="/login" element={<PublicRoute><LandingLayout><LoginPage /></LandingLayout></PublicRoute>} errorElement={<ErrorPage />} />
        
        {/* Connection page (accessible by anyone but redirects authenticated users to mailbox) */}
        <Route path="/connect" element={<AppLayout><ConnectionPage /></AppLayout>} errorElement={<ErrorPage />} />
        
        {/* Private routes with app layout */}
        <Route path="/mailbox" element={<PrivateRoute><AppLayout><MailboxPage /></AppLayout></PrivateRoute>} errorElement={<ErrorPage />} />
        <Route path="/emails/:id" element={<PrivateRoute><AppLayout><EmailDetailPage /></AppLayout></PrivateRoute>} errorElement={<ErrorPage />} />
        <Route path="/compose" element={<PrivateRoute><AppLayout><ComposePage /></AppLayout></PrivateRoute>} errorElement={<ErrorPage />} />
        
        {/* Fallback */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AuthProvider>
  )
}