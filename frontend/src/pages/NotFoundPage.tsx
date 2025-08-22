import React from 'react'
import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="text-center py-20">
      <h1 className="text-3xl font-semibold mb-2">404 - Page Not Found</h1>
      <p className="text-gray-600 mb-6">The page you are looking for does not exist.</p>
      <Link to="/mailbox" className="px-4 py-2 bg-indigo-600 text-white rounded">Go to Mailbox</Link>
    </div>
  )
}