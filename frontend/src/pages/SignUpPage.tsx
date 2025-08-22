import React from 'react'
import { Link } from 'react-router-dom'

export default function SignUpPage() {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-gradient-green rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd"/>
          </svg>
        </div>
        <h1 className="text-3xl font-bold text-secondary-800 mb-2">Get Started Free</h1>
        <p className="text-secondary-600">Connect your existing email to access our professional dashboard</p>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="space-y-6">
            {/* Benefits */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-green-800 mb-3">What you'll get:</h3>
              <ul className="space-y-2 text-green-700">
                <li className="flex items-center">
                  <svg className="w-5 h-5 text-green-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                  </svg>
                  Secure, encrypted email management
                </li>
                <li className="flex items-center">
                  <svg className="w-5 h-5 text-green-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                  </svg>
                  Clean, organized dashboard with folders
                </li>
                <li className="flex items-center">
                  <svg className="w-5 h-5 text-green-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                  </svg>
                  Works with your existing email provider
                </li>
                <li className="flex items-center">
                  <svg className="w-5 h-5 text-green-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                  </svg>
                  No ads, no tracking, no clutter
                </li>
              </ul>
            </div>

            {/* How it works */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-secondary-800">How it works:</h3>
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="w-8 h-8 bg-gradient-green text-white rounded-full flex items-center justify-center mr-4 mt-1 text-sm font-bold">
                    1
                  </div>
                  <div>
                    <h4 className="font-medium text-secondary-800">Connect Your Email</h4>
                    <p className="text-sm text-secondary-600">Securely connect your Gmail, Outlook, or any IMAP/SMTP email account</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-8 h-8 bg-gradient-green text-white rounded-full flex items-center justify-center mr-4 mt-1 text-sm font-bold">
                    2
                  </div>
                  <div>
                    <h4 className="font-medium text-secondary-800">Access Your Dashboard</h4>
                    <p className="text-sm text-secondary-600">View and manage all your emails in our clean, organized interface</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-8 h-8 bg-gradient-green text-white rounded-full flex items-center justify-center mr-4 mt-1 text-sm font-bold">
                    3
                  </div>
                  <div>
                    <h4 className="font-medium text-secondary-800">Enjoy Professional Email</h4>
                    <p className="text-sm text-secondary-600">Send, receive, and organize emails with our professional tools</p>
                  </div>
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
                  <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
                  <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
                </svg>
                Connect Your Email Account
              </Link>
              
              <p className="text-center text-sm text-secondary-600 mt-4">
                Already have an account?{' '}
                <Link to="/login" className="text-primary-600 hover:text-primary-700 font-medium">
                  Sign in here
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Security note */}
      <div className="mt-8 text-center">
        <div className="inline-flex items-center px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg">
          <svg className="w-5 h-5 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
          </svg>
          <span className="text-sm text-blue-800">
            Your credentials are encrypted and never stored on our servers
          </span>
        </div>
      </div>
    </div>
  )
}