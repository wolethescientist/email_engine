import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import DOMPurify from 'dompurify'
import { archiveEmail, deleteEmail, getEmail, markRead, EmailDetail, downloadAttachment } from '@api/api'
import { Loading, ErrorState } from '@components/States'

export default function EmailDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [email, setEmail] = useState<EmailDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams(window.location.search)
      const folder = params.get('folder') || undefined
      const source = params.get('source') || undefined
      const res = await getEmail(Number(id), folder, source)
      setEmail(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to load email')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  const doMarkRead = async (read: boolean) => {
    if (!id) return
    await markRead(Number(id), read)
    load()
  }

  const doArchive = async () => {
    if (!id) return
    await archiveEmail(Number(id))
    navigate('/mailbox')
  }

  const doDelete = async () => {
    if (!id) return
    await deleteEmail(Number(id))
    navigate('/mailbox')
  }

  const safeHtml = useMemo(() => DOMPurify.sanitize(email?.body || ''), [email?.body])

  if (loading) return <Loading />
  if (error) return <ErrorState message={error} />
  if (!email) return null

  return (
    <div className="bg-white rounded shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold">{email.subject || '(No subject)'}</h1>
        <div className="space-x-2">
          <button onClick={() => doMarkRead(!email.is_read)} className="px-3 py-1 rounded border">
            {email.is_read ? 'Mark Unread' : 'Mark Read'}
          </button>
          <button onClick={doArchive} className="px-3 py-1 rounded border">Archive</button>
          <button onClick={doDelete} className="px-3 py-1 rounded border text-red-600">Delete</button>
        </div>
      </div>

      <div className="mb-2 text-sm text-gray-600">
        <div><span className="font-medium">From:</span> {email.from_address || 'Unknown'}</div>
        <div><span className="font-medium">To:</span> {email.to_addresses?.join(', ') || '-'}</div>
        <div><span className="font-medium">CC:</span> {email.cc_addresses?.join(', ') || '-'}</div>
        <div><span className="font-medium">BCC:</span> {email.bcc_addresses?.join(', ') || '-'}</div>
      </div>

      {/* Render either HTML (sanitized) or plain text */}
      {email.body && email.body.includes('<') ? (
        <div className="prose max-w-none mb-4" dangerouslySetInnerHTML={{ __html: safeHtml }} />
      ) : (
        <div className="prose max-w-none mb-4">
          <pre className="whitespace-pre-wrap">{email.body || ''}</pre>
        </div>
      )}

      {email.attachments?.length > 0 && (
        <div>
          <div className="font-medium mb-2">Attachments</div>
          <ul className="list-disc ml-5">
            {email.attachments.map((a) => (
              <li key={a} className="flex items-center gap-2">
                <span>{a}</span>
                <button
                  className="text-sm text-indigo-600 hover:text-indigo-700"
                  onClick={async () => {
                    if (!id) return
                    try {
                      const res = await downloadAttachment(Number(id), a)
                      const blob = new Blob([res.data])
                      const url = window.URL.createObjectURL(blob)
                      const link = document.createElement('a')
                      link.href = url
                      link.download = a
                      document.body.appendChild(link)
                      link.click()
                      link.remove()
                      window.URL.revokeObjectURL(url)
                    } catch (e) {
                      alert('Failed to download attachment')
                    }
                  }}
                >
                  Download
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}