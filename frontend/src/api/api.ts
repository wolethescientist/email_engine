import axios from 'axios'

// Use environment variable for production, fallback to proxy for development
const baseURL = import.meta.env.VITE_API_BASE_URL 
  ? `${import.meta.env.VITE_API_BASE_URL}` 
  : '/api' // Vite proxy rewrites to FastAPI in development

export const api = axios.create({ baseURL })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  const isConnect = config.url?.endsWith('/connect') && config.method?.toLowerCase() === 'post'
  if (token && !isConnect) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    // Auto-logout on 401 (token expired/invalid)
    if (error?.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      if (typeof window !== 'undefined') {
        window.location.href = '/'
      }
    }
    
    // Handle IMAP authentication failures (400 status with specific message)
    if (error?.response?.status === 400 && 
        error?.response?.data?.detail?.includes('IMAP authentication failed')) {
      // Clear stored credentials and redirect to reconnect
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      if (typeof window !== 'undefined') {
        // Show a user-friendly message before redirecting
        alert('Your email connection has expired. Please reconnect your email account.')
        window.location.href = '/connect'
      }
    }
    
    return Promise.reject(error)
  }
)

export interface ConnectRequest {
  email: string
  password: string
  imap_host: string
  imap_port: number
  smtp_host: string
  smtp_port: number
}

export interface ConnectResponse {
  access_token: string
  token_type: 'bearer'
  role: 'admin' | 'user'
}

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

export interface DraftResponse { id: number }

export interface EmailItem {
  id: number
  folder: string
  subject?: string
  from_address?: string
  to_addresses: string[]
  is_read: boolean
  // Optional: if backend adds created_at or date later
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

export const connect = (payload: ConnectRequest) =>
  api.post<ConnectResponse>('/connect', payload)

export const getInbox = (page=1, size=50) =>
  api.get<PaginatedEmails>(`/emails/inbox`, { params: { page, size } })

export const getSent = (page=1, size=50, source: 'db' | 'imap' = 'db') =>
  api.get<PaginatedEmails>(`/emails/sent`, { params: { page, size, source } })

export const getDrafts = (page=1, size=50) =>
  api.get<PaginatedEmails>(`/emails/drafts`, { params: { page, size } })

export const getTrash = (page=1, size=50) =>
  api.get<PaginatedEmails>(`/emails/trash`, { params: { page, size } })

export const getArchive = (page=1, size=50) =>
  api.get<PaginatedEmails>(`/emails/archive`, { params: { page, size } })

export const getSpam = (page=1, size=50) =>
  api.get<PaginatedEmails>(`/emails/spam`, { params: { page, size } })

export const getEmail = (id: number, folder?: string, source?: string) => {
  const params: any = {}
  if (folder) params.folder = folder
  if (source) params.source = source
  return api.get<EmailDetail>(`/emails/${id}`, { params })
}

export const markRead = (id: number, read: boolean) =>
  api.patch(`/emails/${id}/read`, null, { params: { read } })

export const archiveEmail = (id: number) =>
  api.patch(`/emails/${id}/archive`)

export const deleteEmail = (id: number) =>
  api.delete(`/emails/${id}`)

export const saveDraft = (payload: EmailComposeRequest) =>
  api.post<DraftResponse>('/emails/compose', payload)

export const sendEmail = (payload: EmailComposeRequest & { draft_id?: number }) =>
  api.post<EmailDetail>('/emails/send', payload)

export const downloadAttachment = (emailId: number, filename: string) => {
  return api.get(`/emails/${emailId}/attachments/${encodeURIComponent(filename)}`, { responseType: 'blob' })
}
