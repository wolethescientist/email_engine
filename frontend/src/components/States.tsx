import React from 'react'

export const Loading: React.FC<{ text?: string }> = ({ text = 'Loading...' }) => (
  <div className="py-6 text-gray-600">{text}</div>
)

export const EmptyState: React.FC<{ text?: string }> = ({ text = 'No data' }) => (
  <div className="py-10 text-center text-gray-500">{text}</div>
)

export const ErrorState: React.FC<{ message?: string }> = ({ message = 'Something went wrong' }) => (
  <div className="py-6 text-red-600">{message}</div>
)