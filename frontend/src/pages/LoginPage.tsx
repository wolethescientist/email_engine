import React from 'react'
import { Link } from 'react-router-dom'

export default function LoginPage() {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-gradient-green rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 3a1 1 0 011 1v12a1 1 0 102 0V4a1 1 0 011-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clipRule="evenodd"/>
          </svg>
        </div>
        <h1 className="text-3xl font-bold text-secondary-800 mb-2">Welcome Back</h1>
        <p className="text-secondary-600">Connect to your email account to access your dashboard</p>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="space-y-6">
            {/* Quick access info */}
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-green-800 mb-2">Quick Access</h3>
              <p className="text-green-700 text-sm mb-3">
                Connect your email account to access your secure dashboard with organized folders and professional tools.
              </p>
              <div className="flex items-center text-sm text-green-600">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                </svg>
                Works with Gmail, Outlook, and custom domains
              </div>
            </div>

            {/* Features reminder */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-start">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                  <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
                  </svg>
                </div>
                <div>
                  <h4 className="font-medium text-secondary-800 text-sm">Organized Folders</h4>
                  <p className="text-xs text-secondary-600">Inbox, Sent, Drafts, Spam, Archive, Trash</p>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
                  <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                  </svg>
                </div>
                <div>
                  <h4 className="font-medium text-secondary-800 text-sm">Secure & Private</h4>
                  <p className="text-xs text-secondary-600">Encrypted connections, no ads</p>
                </div>
              </div>
            </div>

            {/* CTA */}
            <div className="pt-6 border-t border-secondary-200">
              <Link 
                to="/connect" 
                className="w-full btn-primary py-3 text-base inline-flex items-center justify-center"
              >
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 3a1 1 0 011 1v12a1 1 0 102 0V4a1 1 0 011-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clipRule="evenodd"/>
                </svg>
                Connect Email Account
              </Link>
              
              <p className="text-center text-sm text-secondary-600 mt-4">
                Don't have an account yet?{' '}
                <Link to="/signup" className="text-primary-600 hover:text-primary-700 font-medium">
                  Get started free
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Help text */}
      <div className="mt-8">
        <div className="bg-secondary-50 border border-secondary-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-secondary-800 mb-2">Need help connecting?</h3>
          <p className="text-sm text-secondary-600 mb-3">
            We support most email providers. You'll need your email address, password, and server settings (IMAP/SMTP).
          </p>
          <div className="text-xs text-secondary-500">
            Common providers like Gmail and Outlook work automatically. For custom domains, you may need to configure server settings.
          </div>
        </div>
      </div>
    </div>
  )
}