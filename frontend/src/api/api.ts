import axios, { AxiosHeaders } from 'axios'

// Base URL: env or Vite proxy
const baseURL = import.meta.env.VITE_API_BASE_URL 
  ? `${import.meta.env.VITE_API_BASE_URL}` 
  : '/api'

export const api = axios.create({ baseURL })

// === Credentials handling (stateless) ===
export interface Credentials {
  email: string
  password?: string | null
  access_token?: string | null
  imap_host: string
  imap_port: number
  smtp_host: string
  smtp_port: number
}

let storedCreds: Credentials | null = null

export const getCredentials = (): Credentials | null => {
  if (storedCreds) return storedCreds
  const raw = localStorage.getItem('creds')
  if (!raw) return null
  try { storedCreds = JSON.parse(raw) as Credentials } catch {}
  return storedCreds
}

export const setCredentials = (creds: Credentials | null) => {
  storedCreds = creds
  if (creds) localStorage.setItem('creds', JSON.stringify(creds))
  else localStorage.removeItem('creds')
}

api.interceptors.request.use((config) => {
  const creds = getCredentials()
  if (creds) {
    const headers = AxiosHeaders.from(config.headers || {})
    headers.set('X-IMAP-Host', creds.imap_host)
    headers.set('X-IMAP-Port', String(creds.imap_port))
    headers.set('X-SMTP-Host', creds.smtp_host)
    headers.set('X-SMTP-Port', String(creds.smtp_port))
    headers.set('X-Email', creds.email)
    if (creds.password) headers.set('X-Password', creds.password)
    if (creds.access_token) headers.set('X-Access-Token', creds.access_token)
    config.headers = headers
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error?.response?.status === 400 && 
        typeof error?.response?.data?.detail === 'string' &&
        error.response.data.detail.includes('IMAP authentication failed')) {
      // Clear creds and redirect to connect
      setCredentials(null)
      if (typeof window !== 'undefined') {
        alert('Your email connection failed. Please reconnect your email account.')
        window.location.href = '/connect'
      }
    }
    return Promise.reject(error)
  }
)

// === API types ===
export interface ConnectRequest extends Credentials {}
export interface ConnectResponse { success: boolean; message?: string }

export interface AttachmentIn {
  filename: string
  content_base64: string
  content_type?: string
}

export interface EmailComposeRequest {
  subject?: string
  body?: string
  to: string[]
  cc: string[]
  bcc: string[]
  attachments: AttachmentIn[]
}

export interface DraftResponse { success: boolean; id?: number | null; message?: string }

export interface EmailItem {
  id: number
  folder: string
  subject?: string
  from_address?: string
  to_addresses: string[]
  is_read: boolean
  created_at?: string
}

export interface EmailDetail {
  id: number
  folder: string
  subject?: string
  body?: string
  from_address?: string
  to_addresses: string[]
  cc_addresses: string[]
  bcc_addresses: string[]
  is_read: boolean
  attachments: string[]
}

export interface PaginatedEmails {
  page: number
  size: number
  total: number
  items: EmailItem[]
}

// === API functions ===
export const connect = (payload: ConnectRequest) => api.post<ConnectResponse>('/connect', payload)

// Mailbox listing: POST endpoints, pass page/size via query; credentials via headers
export const getInbox = (page=1, size=50) => api.post<PaginatedEmails>(`/emails/inbox`, undefined, { params: { page, size } })
export const getSent = (page=1, size=50) => api.post<PaginatedEmails>(`/emails/sent`, undefined, { params: { page, size } })
export const getDrafts = (page=1, size=50) => api.post<PaginatedEmails>(`/emails/drafts`, undefined, { params: { page, size } })
export const getTrash = (page=1, size=50) => api.post<PaginatedEmails>(`/emails/trash`, undefined, { params: { page, size } })
export const getArchive = (page=1, size=50) => api.post<PaginatedEmails>(`/emails/archive`, undefined, { params: { page, size } })
export const getSpam = (page=1, size=50) => api.post<PaginatedEmails>(`/emails/spam`, undefined, { params: { page, size } })

// Email detail
export const getEmail = (id: number, folder?: string) => {
  const params: any = {}
  if (folder) params.folder = folder
  return api.post<EmailDetail>(`/emails/${id}`, undefined, { params })
}

// Modify operations
export const markRead = (id: number, read: boolean, folder?: string) => {
  const creds = getCredentials()
  if (!creds) throw new Error('Not connected')
  return api.post(`/emails/${id}/read`, { creds, folder: folder || 'inbox', read })
}

export const archiveEmail = (id: number, folder?: string) => api.post(`/emails/${id}/archive`, undefined, { params: { ...(folder ? { folder } : {}) } })
export const unarchiveEmail = (id: number, folder?: string) => api.post(`/emails/${id}/unarchive`, undefined, { params: { ...(folder ? { folder } : {}) } })
export const deleteEmail = (id: number, folder?: string) => api.post(`/emails/${id}/delete`, undefined, { params: { ...(folder ? { folder } : {}) } })

// Compose / Send — include creds in body
export const saveDraft = (payload: EmailComposeRequest) => {
  const creds = getCredentials()
  if (!creds) throw new Error('Not connected')
  return api.post<DraftResponse>('/emails/compose', { ...payload, creds })
}

export const sendEmail = (payload: EmailComposeRequest & { draft_id?: number }) => {
  const creds = getCredentials()
  if (!creds) throw new Error('Not connected')
  return api.post<EmailDetail>('/emails/send', { ...payload, creds })
}

// Attachments
export const downloadAttachment = (emailId: number, filename: string, folder?: string) => {
  return api.post(`/emails/${emailId}/attachments/${encodeURIComponent(filename)}`,
    undefined,
    { responseType: 'blob', params: { ...(folder ? { folder } : {}) } }
  )
}