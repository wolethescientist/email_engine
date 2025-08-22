import React from 'react'
import { Link } from 'react-router-dom'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-emerald-50">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 py-16 sm:py-24">
          <div className="text-center">
            {/* Logo/Brand */}
            <div className="flex items-center justify-center mb-8">
              <div className="w-16 h-16 bg-gradient-green rounded-2xl flex items-center justify-center">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
                  <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
                </svg>
              </div>
              <h1 className="ml-4 text-3xl font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
                ConnexxionEngine
              </h1>
            </div>

            {/* Main Headline */}
            <h2 className="text-4xl sm:text-6xl font-bold text-secondary-800 mb-6 max-w-4xl mx-auto leading-tight">
              Secure, Professional Email Hosting 
              <span className="block text-accent-600">Made Simple</span>
            </h2>

            {/* Subheadline */}
            <p className="text-xl text-secondary-600 mb-12 max-w-2xl mx-auto leading-relaxed">
              Get a custom domain, safe inbox, and professional email tools—no clutter, no ads. 
              Connect your existing email and access everything in one clean dashboard.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
              <Link 
                to="/signup" 
                className="btn-primary px-8 py-4 text-lg font-semibold shadow-green hover:shadow-lg transform hover:scale-105 transition-all duration-200"
              >
                <svg className="w-5 h-5 mr-2 inline" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd"/>
                </svg>
                Sign Up Free
              </Link>
              <Link 
                to="/login" 
                className="btn-secondary px-8 py-4 text-lg font-semibold hover:shadow-soft transform hover:scale-105 transition-all duration-200"
              >
                <svg className="w-5 h-5 mr-2 inline" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 3a1 1 0 011 1v12a1 1 0 102 0V4a1 1 0 011-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clipRule="evenodd"/>
                </svg>
                Log In
              </Link>
            </div>

            {/* Dashboard Preview */}
            <div className="relative max-w-5xl mx-auto">
              <div className="card shadow-2xl overflow-hidden">
                <div className="bg-secondary-50 border-b border-secondary-200 px-6 py-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                    <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                    <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                    <span className="text-sm text-secondary-500 ml-4">ConnexxionEngine Dashboard</span>
                  </div>
                </div>
                <div className="p-6 bg-white">
                  <div className="flex">
                    <div className="w-64 border-r border-secondary-100 pr-4">
                      <h3 className="font-medium text-secondary-800 mb-3">Folders</h3>
                      <div className="space-y-2">
                        {['Inbox', 'Sent', 'Drafts', 'Spam', 'Archive', 'Trash'].map((folder, i) => (
                          <div key={folder} className={`flex items-center px-3 py-2 rounded-lg text-sm ${i === 0 ? 'bg-primary-100 text-primary-800' : 'text-secondary-600'}`}>
                            <div className="w-2 h-2 bg-current rounded-full mr-3"></div>
                            {folder}
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="flex-1 pl-6">
                      <div className="space-y-3">
                        {[1, 2, 3].map((i) => (
                          <div key={i} className="flex items-center p-3 border border-secondary-100 rounded-lg">
                            <div className="w-8 h-8 bg-gradient-green rounded-full mr-3"></div>
                            <div className="flex-1">
                              <div className="h-4 bg-secondary-200 rounded mb-2" style={{width: `${80 - i * 10}%`}}></div>
                              <div className="h-3 bg-secondary-100 rounded" style={{width: `${60 + i * 15}%`}}></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold text-secondary-800 mb-4">Everything You Need</h3>
            <p className="text-xl text-secondary-600 max-w-2xl mx-auto">
              Professional email management with enterprise-grade security and a beautiful interface.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                </svg>
              </div>
              <h4 className="text-xl font-bold text-secondary-800 mb-3">Security & Privacy</h4>
              <p className="text-secondary-600">
                Your data is encrypted and protected with enterprise-grade security. No tracking, no ads.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <h4 className="text-xl font-bold text-secondary-800 mb-3">Custom Domain</h4>
              <p className="text-secondary-600">
                Professional emails with your own domain. Look professional with yourname@yourcompany.com.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
                </svg>
              </div>
              <h4 className="text-xl font-bold text-secondary-800 mb-3">Clean Dashboard</h4>
              <p className="text-secondary-600">
                Inbox, Sent, Drafts, Spam, Archive, Trash—all organized in one beautiful, distraction-free interface.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="py-24 bg-gradient-to-br from-green-50 to-emerald-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold text-secondary-800 mb-4">How It Works</h3>
            <p className="text-xl text-secondary-600 max-w-2xl mx-auto">
              Get started in minutes. Connect your email and access everything in one place.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="w-12 h-12 bg-gradient-green text-white rounded-full flex items-center justify-center mx-auto mb-6 font-bold text-xl">
                1
              </div>
              <h4 className="text-xl font-bold text-secondary-800 mb-3">Sign Up</h4>
              <p className="text-secondary-600">
                Create your account in seconds. No complex setup required.
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-gradient-green text-white rounded-full flex items-center justify-center mx-auto mb-6 font-bold text-xl">
                2
              </div>
              <h4 className="text-xl font-bold text-secondary-800 mb-3">Connect Your Email</h4>
              <p className="text-secondary-600">
                Securely connect your existing email account with our simple setup wizard.
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-gradient-green text-white rounded-full flex items-center justify-center mx-auto mb-6 font-bold text-xl">
                3
              </div>
              <h4 className="text-xl font-bold text-secondary-800 mb-3">Access Your Dashboard</h4>
              <p className="text-secondary-600">
                Manage all your emails in one beautiful, organized dashboard.
              </p>
            </div>
          </div>

          <div className="text-center mt-16">
            <Link 
              to="/signup" 
              className="btn-primary px-8 py-4 text-lg font-semibold shadow-green hover:shadow-lg transform hover:scale-105 transition-all duration-200"
            >
              Get Started Now
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-secondary-800 text-white py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center mb-6 md:mb-0">
              <div className="w-8 h-8 bg-gradient-green rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
                  <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
                </svg>
              </div>
              <span className="ml-3 text-xl font-bold">ConnexxionEngine</span>
            </div>
            
            <div className="flex space-x-8 text-sm">
              <a href="#" className="hover:text-green-400 transition-colors">About</a>
              <a href="#" className="hover:text-green-400 transition-colors">Support</a>
              <a href="#" className="hover:text-green-400 transition-colors">Terms</a>
              <a href="#" className="hover:text-green-400 transition-colors">Privacy</a>
            </div>
          </div>
          
          <div className="border-t border-secondary-700 mt-8 pt-8 text-center text-sm text-secondary-400">
            <p>&copy; 2024 ConnexxionEngine. All rights reserved. Secure, professional email hosting made simple.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}