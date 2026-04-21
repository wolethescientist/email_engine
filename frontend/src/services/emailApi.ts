import axios, { AxiosResponse } from 'axios';
import { config } from '@/config';
import {
  AIDraftRequest,
  AIGenerationResponse,
  AIReplySuggestionRequest,
  Credentials,
  ConnectResponse,
  FoldersResponse,
  PaginatedEmails,
  EmailDetail,
  EmailComposeRequest,
  SendEmailRequest,
  DraftResponse,
  ModifyEmailRequest,
  ListRequest,
} from '@/types';

const api = axios.create({
  baseURL: config.API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      console.log('API Request:', config.method?.toUpperCase(), config.url);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (import.meta.env.DEV) {
      console.error('API Error:', error.response?.status, error.response?.data);
    }
    return Promise.reject(error);
  }
);

export class EmailApiService {
  // Connection validation
  static async validateConnection(credentials: Credentials): Promise<ConnectResponse> {
    const response: AxiosResponse<ConnectResponse> = await api.post('/connect', credentials);
    return response.data;
  }

  // Get available folders
  static async getFolders(credentials: Credentials): Promise<FoldersResponse> {
    const response: AxiosResponse<FoldersResponse> = await api.post('/emails/folders', {
      creds: credentials,
    });
    return response.data;
  }

  // Get emails from specific folder
  static async getEmails(
    credentials: Credentials,
    folder: string,
    params?: Partial<ListRequest>
  ): Promise<PaginatedEmails> {
    const requestData: ListRequest = {
      creds: credentials,
      page: params?.page || 1,
      size: params?.size || config.DEFAULT_PAGE_SIZE,
      ...params,
    };

    const response: AxiosResponse<PaginatedEmails> = await api.post(
      `/emails/${folder}`,
      requestData
    );
    return response.data;
  }

  // Get email details
  static async getEmailDetail(
    credentials: Credentials,
    emailId: number,
    folder: string = 'inbox'
  ): Promise<EmailDetail> {
    const response: AxiosResponse<EmailDetail> = await api.post(
      `/emails/${emailId}`,
      {
        creds: credentials,
        folder,
      }
    );
    return response.data;
  }

  // Compose/save draft
  static async saveDraft(emailData: EmailComposeRequest): Promise<DraftResponse> {
    const response: AxiosResponse<DraftResponse> = await api.post('/emails/compose', emailData);
    return response.data;
  }

  static async generateAIDraft(request: AIDraftRequest): Promise<AIGenerationResponse> {
    const response: AxiosResponse<AIGenerationResponse> = await api.post('/emails/ai/draft', request);
    return response.data;
  }

  static async generateAIReplySuggestion(request: AIReplySuggestionRequest): Promise<AIGenerationResponse> {
    const response: AxiosResponse<AIGenerationResponse> = await api.post('/emails/ai/reply-suggestion', request);
    return response.data;
  }

  // Send email
  static async sendEmail(emailData: SendEmailRequest): Promise<EmailDetail> {
    const response: AxiosResponse<EmailDetail> = await api.post('/emails/send', emailData);
    return response.data;
  }

  // Mark email as read/unread
  static async markAsRead(
    credentials: Credentials,
    emailId: number,
    folder: string,
    read: boolean
  ): Promise<void> {
    const requestData: ModifyEmailRequest = {
      creds: credentials,
      folder,
      read,
    };

    await api.post(`/emails/${emailId}/read`, requestData);
  }

  // Star/unstar email
  static async starEmail(
    credentials: Credentials,
    emailId: number,
    folder: string,
    starred: boolean
  ): Promise<void> {
    const requestData: ModifyEmailRequest = {
      creds: credentials,
      folder,
      starred,
    };

    await api.post(`/emails/${emailId}/star`, requestData);
  }

  // Delete email (move to trash)
  static async deleteEmail(
    credentials: Credentials,
    emailId: number,
    folder: string
  ): Promise<void> {
    await api.post(`/emails/${emailId}/delete`, {
      creds: credentials,
      folder,
    });
  }

  // Archive email
  static async archiveEmail(
    credentials: Credentials,
    emailId: number,
    folder: string
  ): Promise<void> {
    await api.post(`/emails/${emailId}/archive`, {
      creds: credentials,
      folder,
    });
  }

  // Unarchive email
  static async unarchiveEmail(
    credentials: Credentials,
    emailId: number,
    folder: string
  ): Promise<void> {
    await api.post(`/emails/${emailId}/unarchive`, {
      creds: credentials,
      folder,
    });
  }

  // Mark as spam
  static async markAsSpam(
    credentials: Credentials,
    emailId: number,
    folder: string
  ): Promise<void> {
    await api.post(`/emails/${emailId}/spam`, {
      creds: credentials,
      folder,
    });
  }

  // Remove from spam
  static async unmarkAsSpam(
    credentials: Credentials,
    emailId: number,
    folder: string
  ): Promise<void> {
    await api.post(`/emails/${emailId}/unspam`, {
      creds: credentials,
      folder,
    });
  }

  // Restore from trash
  static async restoreEmail(
    credentials: Credentials,
    emailId: number,
    folder: string
  ): Promise<void> {
    await api.post(`/emails/${emailId}/restore`, {
      creds: credentials,
      folder,
    });
  }

  // Download attachment
  static async downloadAttachment(
    credentials: Credentials,
    emailId: number,
    filename: string,
    folder: string
  ): Promise<Blob> {
    const encodedFilename = encodeURIComponent(filename);
    const response: AxiosResponse<Blob> = await api.post(
      `/emails/${emailId}/attachments/${encodedFilename}`,
      {
        creds: credentials,
        folder,
      },
      {
        responseType: 'blob',
      }
    );
    return response.data;
  }

  // Bulk operations
  static async bulkMarkAsRead(
    credentials: Credentials,
    emailIds: number[],
    folder: string,
    read: boolean
  ): Promise<void> {
    const promises = emailIds.map(id => 
      this.markAsRead(credentials, id, folder, read)
    );
    await Promise.all(promises);
  }

  static async bulkDelete(
    credentials: Credentials,
    emailIds: number[],
    folder: string
  ): Promise<void> {
    const promises = emailIds.map(id => 
      this.deleteEmail(credentials, id, folder)
    );
    await Promise.all(promises);
  }

  static async bulkArchive(
    credentials: Credentials,
    emailIds: number[],
    folder: string
  ): Promise<void> {
    const promises = emailIds.map(id => 
      this.archiveEmail(credentials, id, folder)
    );
    await Promise.all(promises);
  }

  static async bulkStar(
    credentials: Credentials,
    emailIds: number[],
    folder: string,
    starred: boolean
  ): Promise<void> {
    const promises = emailIds.map(id => 
      this.starEmail(credentials, id, folder, starred)
    );
    await Promise.all(promises);
  }
}

// Error handler utility
export function handleApiError(error: any): string {
  if (error.response?.status === 400) {
    return error.response.data?.detail || 'Invalid request. Please check your input.';
  } else if (error.response?.status === 404) {
    return error.response?.data?.detail || 'Resource not found.';
  } else if (error.response?.status === 502) {
    return 'Connection error. Please check your email server settings.';
  } else if (error.response?.status === 503) {
    return error.response.data?.detail || 'AI service is not configured.';
  } else if (error.response?.status >= 500) {
    return 'Server error. Please try again later.';
  } else if (error.code === 'NETWORK_ERROR' || !error.response) {
    return 'Network error. Please check your internet connection.';
  }
  
  return error.response?.data?.detail || 'An unexpected error occurred.';
}
