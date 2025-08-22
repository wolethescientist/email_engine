import React from 'react'
import { Link, useLocation } from 'react-router-dom'

interface LandingLayoutProps {
  children: React.ReactNode
}

export default function LandingLayout({ children }: LandingLayoutProps) {
  const location = useLocation()
  const isLandingPage = location.pathname === '/'

  // For the main landing page, don't show the header (it's integrated into the page)
  if (isLandingPage) {
    return <div className="min-h-screen">{children}</div>
  }

  // For signup/login pages, show a minimal header
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white/80 backdrop-blur-lg border-b border-secondary-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center space-x-3">
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
            
            <nav className="flex items-center space-x-4">
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
            </nav>
          </div>
        </div>
      </header>
      
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8">
        {children}
      </main>
    </div>
  )
}