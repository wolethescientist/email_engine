import React from 'react'
import { Link, useRouteError } from 'react-router-dom'

export default function ErrorPage() {
  const err: any = useRouteError()
  const status = err?.status || 500
  const message = err?.statusText || err?.message || 'Unexpected error'

  return (
    <div className="text-center py-20">
      <h1 className="text-3xl font-semibold mb-2">{status} Error</h1>
      <p className="text-gray-600 mb-6">{message}</p>
      <Link to="/mailbox" className="px-4 py-2 bg-indigo-600 text-white rounded">Go to Mailbox</Link>
    </div>
  )
}