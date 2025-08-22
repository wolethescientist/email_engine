import React, { useEffect, useState } from 'react'
import Tabs from '@components/Tabs'
import Pagination from '@components/Pagination'
import { Loading, ErrorState, EmptyState } from '@components/States'
import { Link } from 'react-router-dom'
import { getInbox, getSent, getDrafts, getTrash, getArchive, getSpam, PaginatedEmails } from '@api/api'

const tabDefs = [
  { key: 'inbox', label: 'Inbox' },
  { key: 'sent', label: 'Sent' },
  { key: 'drafts', label: 'Drafts' },
  { key: 'spam', label: 'Spam' },
  { key: 'trash', label: 'Trash' },
  { key: 'archive', label: 'Archive' },
]

type TabKey = 'inbox' | 'sent' | 'drafts' | 'spam' | 'trash' | 'archive'

export default function MailboxPage() {
  const [active, setActive] = useState<TabKey>('inbox')
  const [data, setData] = useState<PaginatedEmails | null>(null)
  const [page, setPage] = useState(1)
  const [size] = useState(10)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = async (key: TabKey, p: number) => {
    setLoading(true)
    setError(null)
    try {
      let res
      if (key === 'inbox') res = await getInbox(p, size)
      else if (key === 'sent') res = await getSent(p, size, 'imap') // switch between 'db' or 'imap' as you prefer
      else if (key === 'drafts') res = await getDrafts(p, size)
      else if (key === 'spam') res = await getSpam(p, size)
      else if (key === 'trash') res = await getTrash(p, size)
      else res = await getArchive(p, size)
      setData(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to fetch mailbox')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { setPage(1) }, [active])
  useEffect(() => { load(active, page) }, [active, page])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-secondary-800">Mailbox</h1>
          <p className="text-secondary-600 mt-1">Manage your emails</p>
        </div>
        <Link to="/compose" className="btn-primary">
          <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd"/>
          </svg>
          Compose
        </Link>
      </div>

      <div className="card overflow-hidden">
        <Tabs items={tabDefs} activeKey={active} onChange={(k) => setActive(k as TabKey)} />

        <div className="bg-white">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="flex items-center space-x-3">
                <svg className="w-5 h-5 animate-spin text-primary-600" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
                <span className="text-secondary-600">Loading emails...</span>
              </div>
            </div>
          )}
          
          {error && (
            <div className="p-6">
              <div className="flex items-center p-4 bg-red-50 border border-red-200 rounded-lg">
                <svg className="w-5 h-5 text-red-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                </svg>
                <div>
                  <p className="font-medium text-red-800">Error loading emails</p>
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div className="divide-y divide-secondary-100">
            {data?.items.map((item) => {
              // For sent emails, we need to pass the source parameter to match how we fetched them
              const linkParams = active === 'sent' 
                ? `folder=${active}&source=imap` 
                : `folder=${active}`
              
              return (
                <Link 
                  key={item.id} 
                  to={`/emails/${item.id}?${linkParams}`} 
                  className="block px-6 py-4 hover:bg-primary-50/30 transition-colors duration-200 group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3">
                        <div className="flex-shrink-0">
                          <div className="w-10 h-10 bg-gradient-to-r from-primary-400 to-accent-400 rounded-full flex items-center justify-center">
                            <span className="text-white font-medium text-sm">
                              {(item.from_address || 'U').charAt(0).toUpperCase()}
                            </span>
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <p className="text-sm font-medium text-secondary-900 truncate">
                              {item.from_address || 'Unknown sender'}
                            </p>
                            {!item.is_read && (
                              <span className="badge badge-primary">New</span>
                            )}
                          </div>
                          <p className={`text-base mt-1 truncate ${!item.is_read ? 'font-medium text-secondary-900' : 'text-secondary-600'}`}>
                            {item.subject || '(No subject)'}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex-shrink-0 text-right ml-4">
                      {item?.created_at && (
                        <p className="text-sm text-secondary-500 group-hover:text-secondary-600">
                          {new Date(item.created_at).toLocaleDateString()}
                        </p>
                      )}
                      <svg className="w-5 h-5 text-secondary-400 mt-1 group-hover:text-primary-500 transition-colors duration-200" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"/>
                      </svg>
                    </div>
                  </div>
                </Link>
              )
            })}
            
            {!loading && !error && (data?.items.length ?? 0) === 0 && (
              <div className="px-6 py-12 text-center">
                <svg className="w-12 h-12 mx-auto text-secondary-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 48 48">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M34 40h10v-4a6 6 0 00-10.712-3.714M34 40H14m20 0v-4a9.971 9.971 0 00-.712-3.714M14 40H4v-4a6 6 0 0110.712-3.714M14 40v-4a9.971 9.971 0 01.712-3.714M22 12h12l8 8v16a4 4 0 01-4 4H22a4 4 0 01-4-4V16a4 4 0 014-4z"/>
                </svg>
                <p className="text-lg font-medium text-secondary-600 mb-1">No emails found</p>
                <p className="text-secondary-500">This folder is empty</p>
              </div>
            )}
          </div>
        </div>

        {data && data.total > data.size && (
          <div className="border-t border-secondary-100 bg-secondary-50/30 px-6 py-4">
            <Pagination page={data.page} size={data.size} total={data.total} onChange={setPage} />
          </div>
        )}
      </div>
    </div>
  )
}