import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import DOMPurify from 'dompurify';
import { 
  X, 
  Reply, 
  ReplyAll, 
  Forward, 
  Archive, 
  Trash2, 
  Star, 
  Download,
  Paperclip,
  Calendar,
  MoreHorizontal,
  Mail
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Credentials, FolderType } from '@/types';
import { EmailApiService, handleApiError } from '@/services/emailApi';
import { formatRelativeTime, generateAvatarUrl, isImageFile, cn } from '@/utils';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

interface EmailReaderProps {
  credentials: Credentials;
  emailId: number;
  folder: FolderType;
  onClose: () => void;
  onReply: () => void;
  onCompose: () => void;
}

export default function EmailReader({
  credentials,
  emailId,
  folder,
  onClose,
  onReply,
  onCompose
}: EmailReaderProps) {
  const [showAllRecipients, setShowAllRecipients] = useState(false);
  const queryClient = useQueryClient();

  // Fetch email details
  const { data: email, isLoading, error } = useQuery({
    queryKey: ['email', emailId, folder],
    queryFn: () => EmailApiService.getEmailDetail(credentials, emailId, folder),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Mark as read mutation
  const markAsReadMutation = useMutation({
    mutationFn: (read: boolean) => EmailApiService.markAsRead(credentials, emailId, folder, read),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emails'] });
    },
    onError: (error) => {
      toast.error(handleApiError(error));
    },
  });

  // Star mutation
  const starMutation = useMutation({
    mutationFn: (starred: boolean) => EmailApiService.starEmail(credentials, emailId, folder, starred),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emails'] });
      queryClient.invalidateQueries({ queryKey: ['email', emailId] });
    },
    onError: (error) => {
      toast.error(handleApiError(error));
    },
  });

  // Archive mutation
  const archiveMutation = useMutation({
    mutationFn: () => EmailApiService.archiveEmail(credentials, emailId, folder),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emails'] });
      toast.success('Email archived');
      onClose();
    },
    onError: (error) => {
      toast.error(handleApiError(error));
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: () => EmailApiService.deleteEmail(credentials, emailId, folder),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emails'] });
      toast.success('Email moved to trash');
      onClose();
    },
    onError: (error) => {
      toast.error(handleApiError(error));
    },
  });

  // Mark as read when opening
  useEffect(() => {
    if (email && !email.is_read) {
      markAsReadMutation.mutate(true);
    }
  }, [email?.id]);

  const handleDownloadAttachment = async (filename: string) => {
    try {
      const blob = await EmailApiService.downloadAttachment(credentials, emailId, filename, folder);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Attachment downloaded');
    } catch (error) {
      toast.error(handleApiError(error));
    }
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !email) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center">
          <Mail className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <div className="text-lg font-medium mb-2">Failed to load email</div>
          <div className="text-sm text-muted-foreground">Please try again</div>
        </div>
      </div>
    );
  }

  const allRecipients = [...email.to_addresses, ...email.cc_addresses];
  const displayRecipients = showAllRecipients ? allRecipients : allRecipients.slice(0, 3);
  const hasMoreRecipients = allRecipients.length > 3;

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="h-full flex flex-col bg-background"
    >
      {/* Header */}
      <div className="border-b border-border p-4 bg-card/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
            <h2 className="font-semibold truncate">{email.subject || '(no subject)'}</h2>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => starMutation.mutate(!email.is_flagged)}
              disabled={starMutation.isPending}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <Star 
                className={cn(
                  "w-4 h-4",
                  email.is_flagged 
                    ? "fill-yellow-400 text-yellow-400" 
                    : "text-muted-foreground"
                )} 
              />
            </button>
            
            <button
              onClick={() => archiveMutation.mutate()}
              disabled={archiveMutation.isPending}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <Archive className="w-4 h-4" />
            </button>
            
            <button
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
              className="p-2 hover:bg-muted rounded-lg transition-colors text-destructive"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            
            <button className="p-2 hover:bg-muted rounded-lg transition-colors">
              <MoreHorizontal className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={onReply}
            className="px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-muted/50 transition-colors flex items-center gap-2"
          >
            <Reply className="w-3 h-3" />
            Reply
          </button>
          
          <button
            onClick={onReply}
            className="px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-muted/50 transition-colors flex items-center gap-2"
          >
            <ReplyAll className="w-3 h-3" />
            Reply All
          </button>
          
          <button
            onClick={onCompose}
            className="px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-muted/50 transition-colors flex items-center gap-2"
          >
            <Forward className="w-3 h-3" />
            Forward
          </button>
        </div>
      </div>

      {/* Email Content */}
      <div className="flex-1 overflow-auto">
        <div className="p-6">
          {/* Sender Info */}
          <div className="flex items-start gap-4 mb-6">
            <div className="w-12 h-12 rounded-full overflow-hidden flex-shrink-0">
              <img
                src={generateAvatarUrl(email.from_address || '')}
                alt=""
                className="w-full h-full object-cover"
              />
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-semibold">
                  {email.from_address?.split('@')[0] || 'Unknown Sender'}
                </span>
                <span className="text-sm text-muted-foreground">
                  &lt;{email.from_address}&gt;
                </span>
              </div>
              
              <div className="text-sm text-muted-foreground mb-2">
                <div className="flex items-center gap-1 mb-1">
                  <span>to</span>
                  {displayRecipients.map((recipient, index) => (
                    <span key={recipient}>
                      {recipient.split('@')[0]}
                      {index < displayRecipients.length - 1 && ', '}
                    </span>
                  ))}
                  {hasMoreRecipients && !showAllRecipients && (
                    <button
                      onClick={() => setShowAllRecipients(true)}
                      className="text-primary hover:underline ml-1"
                    >
                      +{allRecipients.length - 3} more
                    </button>
                  )}
                </div>
                
                {email.cc_addresses.length > 0 && (
                  <div className="flex items-center gap-1">
                    <span>cc</span>
                    {email.cc_addresses.map((cc, index) => (
                      <span key={cc}>
                        {cc.split('@')[0]}
                        {index < email.cc_addresses.length - 1 && ', '}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {formatRelativeTime(email.timestamp)}
                </div>
                
                {email.has_attachments && (
                  <div className="flex items-center gap-1">
                    <Paperclip className="w-3 h-3" />
                    {email.attachments.length} attachment{email.attachments.length !== 1 ? 's' : ''}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Attachments */}
          {email.attachments.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                <Paperclip className="w-4 h-4" />
                Attachments ({email.attachments.length})
              </h3>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {email.attachments.map((filename) => (
                  <div
                    key={filename}
                    className="flex items-center gap-3 p-3 border border-border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="w-8 h-8 bg-primary/10 rounded flex items-center justify-center flex-shrink-0">
                      {isImageFile(filename) ? (
                        <img src="/api/placeholder/32/32" alt="" className="w-6 h-6 rounded" />
                      ) : (
                        <Paperclip className="w-4 h-4 text-primary" />
                      )}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{filename}</div>
                      <div className="text-xs text-muted-foreground">
                        {/* File size would come from API in real implementation */}
                        Unknown size
                      </div>
                    </div>
                    
                    <button
                      onClick={() => handleDownloadAttachment(filename)}
                      className="p-2 hover:bg-muted rounded-lg transition-colors"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Email Body */}
          <div className="prose prose-sm max-w-none">
            {email.body ? (
              <div
                className="email-content"
                dangerouslySetInnerHTML={{
                  __html: DOMPurify.sanitize(email.body, {
                    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
                    ALLOWED_ATTR: ['href', 'target'],
                  })
                }}
              />
            ) : (
              <div className="text-muted-foreground italic">
                This email has no content.
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
