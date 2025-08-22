import React, { useState } from 'react'
import { saveDraft, sendEmail, AttachmentIn, EmailComposeRequest } from '@api/api'

function toList(s: string): string[] {
  return s.split(',').map(x => x.trim()).filter(Boolean)
}

export default function ComposePage() {
  const [to, setTo] = useState('')
  const [cc, setCc] = useState('')
  const [bcc, setBcc] = useState('')
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [attachments, setAttachments] = useState<AttachmentIn[]>([])
  const [info, setInfo] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const onFiles = async (files: FileList | null) => {
    if (!files) return
    const items: AttachmentIn[] = []
    for (const f of Array.from(files)) {
      console.log(`Processing file: ${f.name}, size: ${f.size} bytes, type: ${f.type}`)
      const buf = await f.arrayBuffer()
      
      // Use a more reliable method for base64 encoding
      const bytes = new Uint8Array(buf)
      let binary = ''
      const chunkSize = 8192 // Process in chunks to avoid call stack issues
      for (let i = 0; i < bytes.length; i += chunkSize) {
        const chunk = bytes.slice(i, i + chunkSize)
        binary += String.fromCharCode.apply(null, Array.from(chunk))
      }
      const b64 = btoa(binary)
      
      console.log(`Encoded ${f.name}: original ${f.size} bytes -> base64 ${b64.length} chars`)
      items.push({ filename: f.name, content_base64: b64, content_type: f.type || 'application/octet-stream' })
    }
    console.log(`Total attachments prepared: ${items.length}`)
    setAttachments(items)
  }

  const buildPayload = (): EmailComposeRequest => ({
    subject,
    body,
    to: toList(to),
    cc: toList(cc),
    bcc: toList(bcc),
    attachments,
  })

  const doDraft = async () => {
    setLoading(true); setError(null); setInfo(null)
    try {
      const res = await saveDraft(buildPayload())
      setInfo(`Draft saved with id ${res.data.id}`)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to save draft')
    } finally { setLoading(false) }
  }

  const doSend = async () => {
    setLoading(true); setError(null); setInfo(null)
    try {
      await sendEmail(buildPayload())
      setInfo('Email sent')
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to send email')
    } finally { setLoading(false) }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-secondary-800">Compose Email</h1>
        <p className="text-secondary-600 mt-1">Create and send a new message</p>
      </div>

      {info && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-green-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
            </svg>
            <p className="text-sm font-medium text-green-800">{info}</p>
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
            </svg>
            <p className="text-sm font-medium text-red-800">{error}</p>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-body space-y-6">
          <div className="grid gap-4">
            <div>
              <label className="form-label">To</label>
              <input 
                value={to} 
                onChange={(e) => setTo(e.target.value)} 
                placeholder="recipient@example.com (comma-separated for multiple)" 
                className="form-input" 
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">CC</label>
                <input 
                  value={cc} 
                  onChange={(e) => setCc(e.target.value)} 
                  placeholder="cc@example.com (optional)" 
                  className="form-input" 
                />
              </div>
              <div>
                <label className="form-label">BCC</label>
                <input 
                  value={bcc} 
                  onChange={(e) => setBcc(e.target.value)} 
                  placeholder="bcc@example.com (optional)" 
                  className="form-input" 
                />
              </div>
            </div>

            <div>
              <label className="form-label">Subject</label>
              <input 
                value={subject} 
                onChange={(e) => setSubject(e.target.value)} 
                placeholder="Enter email subject" 
                className="form-input" 
              />
            </div>

            <div>
              <label className="form-label">Message</label>
              <textarea 
                value={body} 
                onChange={(e) => setBody(e.target.value)} 
                placeholder="Write your message here..." 
                rows={12} 
                className="form-input resize-none"
              />
            </div>

            <div>
              <label className="form-label">Attachments</label>
              <div className="relative">
                <input 
                  type="file" 
                  multiple 
                  onChange={(e) => onFiles(e.target.files)} 
                  className="form-input file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 file:font-medium"
                />
              </div>
              
              {attachments.length > 0 && (
                <div className="mt-3 p-3 bg-primary-50 rounded-lg border border-primary-200">
                  <h4 className="text-sm font-medium text-primary-800 mb-2">Attached Files:</h4>
                  <div className="space-y-2">
                    {attachments.map((attachment, index) => (
                      <div key={attachment.filename} className="flex items-center justify-between text-sm">
                        <div className="flex items-center space-x-2">
                          <svg className="w-4 h-4 text-primary-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd"/>
                          </svg>
                          <span className="text-primary-700">{attachment.filename}</span>
                        </div>
                        <button
                          onClick={() => setAttachments(prev => prev.filter((_, i) => i !== index))}
                          className="text-red-600 hover:text-red-700 p-1"
                        >
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"/>
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 pt-6 border-t border-secondary-200">
            <button 
              disabled={loading} 
              onClick={doSend} 
              className="btn-primary flex-1 sm:flex-initial py-3"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <svg className="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                  Sending...
                </div>
              ) : (
                <div className="flex items-center justify-center">
                  <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
                  </svg>
                  Send Email
                </div>
              )}
            </button>
            
            <button 
              disabled={loading} 
              onClick={doDraft} 
              className="btn-secondary py-3"
            >
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/>
              </svg>
              Save Draft
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}