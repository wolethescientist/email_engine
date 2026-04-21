import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion} from 'framer-motion';
import { 
  Star, 
  Paperclip, 
  MoreHorizontal,
  Archive,
  Trash2,
  Mail,
  MailOpen
} from 'lucide-react';
import toast from 'react-hot-toast';
import Checkbox from '@/components/ui/Checkbox';
import { Credentials, EmailItem, FolderType } from '@/types';
import { EmailApiService, handleApiError } from '@/services/emailApi';
import { formatEmailDate, generateAvatarUrl, cn } from '@/utils';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

interface EmailListProps {
  credentials: Credentials;
  folder: FolderType;
  searchQuery: string;
  selectedEmailId: number | null;
  onEmailSelect: (emailId: number) => void;
}

export default function EmailList({
  credentials,
  folder,
  searchQuery,
  selectedEmailId,
  onEmailSelect
}: EmailListProps) {
  const [selectedEmails, setSelectedEmails] = useState<Set<number>>(new Set());
  const [currentEmailIndex, setCurrentEmailIndex] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const queryClient = useQueryClient();

  useEffect(() => {
    setPage(1);
    setSelectedEmails(new Set());
  }, [folder, searchQuery]);

  // Fetch emails
  const { data: emailsData, isLoading, error } = useQuery({
    queryKey: ['emails', credentials.email, folder, searchQuery, page],
    queryFn: () => EmailApiService.getEmails(credentials, folder, {
      search_text: searchQuery || undefined,
      size: pageSize,
      page: page,
    }),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  const starMutation = useMutation({
    mutationFn: ({ emailId, starred }: { emailId: number; starred: boolean }) => 
      EmailApiService.starEmail(credentials, emailId, folder, starred),
    onMutate: async ({ emailId, starred }) => {
      await queryClient.cancelQueries({ queryKey: ['emails', credentials.email, folder, searchQuery, page] });
      const previousData = queryClient.getQueryData(['emails', credentials.email, folder, searchQuery, page]);
      
      queryClient.setQueryData(['emails', credentials.email, folder, searchQuery, page], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          items: old.items.map((item: any) => 
            item.id === emailId ? { ...item, is_flagged: starred } : item
          )
        };
      });
      return { previousData };
    },
    onError: (err, variables, context: any) => {
      if (context?.previousData) {
        queryClient.setQueryData(['emails', credentials.email, folder, searchQuery, page], context.previousData);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['emails', credentials.email, folder, searchQuery, page] });
      queryClient.invalidateQueries({ queryKey: ['emails'] }); // Invalidate all email queries to reflect stare state change everywhere.
    }
  });

  const handleStarClick = (e: React.MouseEvent, email: EmailItem) => {
    e.stopPropagation();
    starMutation.mutate({ emailId: email.id, starred: !email.is_flagged });
  };

  const bulkDeleteMutation = useMutation({
    mutationFn: () => EmailApiService.bulkDelete(credentials, Array.from(selectedEmails), folder),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emails'] });
      toast.success(`${selectedEmails.size} emails moved to trash`);
      setSelectedEmails(new Set());
    },
    onError: (err) => {
      toast.error(handleApiError(err));
    }
  });

  const bulkArchiveMutation = useMutation({
    mutationFn: () => EmailApiService.bulkArchive(credentials, Array.from(selectedEmails), folder),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emails'] });
      toast.success(`${selectedEmails.size} emails archived`);
      setSelectedEmails(new Set());
    },
    onError: (err) => {
      toast.error(handleApiError(err));
    }
  });

  // Sort emails by timestamp (newest first) to ensure proper ordering
  const emails = (emailsData?.items || []).sort((a, b) => {
    if (!a.timestamp && !b.timestamp) return 0;
    if (!a.timestamp) return 1;
    if (!b.timestamp) return -1;
    
    const dateA = new Date(a.timestamp);
    const dateB = new Date(b.timestamp);
    return dateB.getTime() - dateA.getTime(); // Newest first
  });

  // Removed virtual scrolling for simpler layout

  // Keyboard shortcuts
  useKeyboardShortcuts({
    onNextEmail: () => {
      if (currentEmailIndex < emails.length - 1) {
        const nextIndex = currentEmailIndex + 1;
        setCurrentEmailIndex(nextIndex);
        onEmailSelect(emails[nextIndex].id);
      }
    },
    onPrevEmail: () => {
      if (currentEmailIndex > 0) {
        const prevIndex = currentEmailIndex - 1;
        setCurrentEmailIndex(prevIndex);
        onEmailSelect(emails[prevIndex].id);
      }
    },
    onSelectEmail: () => {
      if (emails[currentEmailIndex]) {
        toggleEmailSelection(emails[currentEmailIndex].id);
      }
    },
  });

  const toggleEmailSelection = (emailId: number) => {
    setSelectedEmails(prev => {
      const newSet = new Set(prev);
      if (newSet.has(emailId)) {
        newSet.delete(emailId);
      } else {
        newSet.add(emailId);
      }
      return newSet;
    });
  };

  const selectAllEmails = () => {
    if (selectedEmails.size === emails.length) {
      setSelectedEmails(new Set());
    } else {
      setSelectedEmails(new Set(emails.map(email => email.id)));
    }
  };

  const handleEmailClick = (email: EmailItem, index: number) => {
    setCurrentEmailIndex(index);
    onEmailSelect(email.id);
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center">
          <div className="text-muted-foreground mb-2">Failed to load emails</div>
          <div className="text-sm text-destructive">Please check your connection</div>
        </div>
      </div>
    );
  }

  if (emails.length === 0) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center">
          <Mail className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <div className="text-lg font-medium mb-2">No emails found</div>
          <div className="text-sm text-muted-foreground">
            {searchQuery ? 'Try adjusting your search terms' : `Your ${folder} is empty`}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Toolbar */}
      <div className="glass-subtle border-b border-border/50 p-3 flex-shrink-0 z-10 sticky top-0">
        <div className="flex items-center gap-3">
          <Checkbox
            checked={selectedEmails.size === emails.length && emails.length > 0}
            onCheckedChange={selectAllEmails}
            className="data-[state=checked]:bg-accent-cta data-[state=checked]:border-accent-cta rounded-lg transition-colors"
          />
          
          <span className="text-sm text-muted-foreground">
            {selectedEmails.size > 0 
              ? `${selectedEmails.size} selected` 
              : `${emails.length} emails`
            }
          </span>

          {selectedEmails.size > 0 && (
            <div className="flex items-center gap-2 ml-auto">
              <button 
                onClick={() => bulkArchiveMutation.mutate()}
                disabled={bulkArchiveMutation.isPending}
                className="p-2 hover:bg-muted rounded-lg transition-colors disabled:opacity-50"
                title="Archive selected"
              >
                <Archive className="w-4 h-4" />
              </button>
              <button 
                onClick={() => bulkDeleteMutation.mutate()}
                disabled={bulkDeleteMutation.isPending}
                className="p-2 hover:bg-muted rounded-lg transition-colors disabled:opacity-50 text-destructive"
                title="Delete selected"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <button className="p-2 hover:bg-muted rounded-lg transition-colors">
                <MoreHorizontal className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Email List */}
      <div className="flex-1 overflow-auto flex flex-col min-h-0">
        <div className="space-y-0 flex-1">
          {emails.map((email, index) => {
            const isSelected = selectedEmails.has(email.id);
            const isActive = email.id === selectedEmailId;

            return (
              <motion.div
                key={email.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.02 }}
                className="w-full"
              >
                <div
                  onClick={() => handleEmailClick(email, index)}
                  className={cn(
                    "flex items-center gap-3 p-3 border-b border-border/50 cursor-pointer transition-all hover:bg-primary/5",
                    isActive && "glass-strong border-primary/20 shadow-sm rounded-lg my-1",
                    !email.is_read && "bg-muted/30"
                  )}
                >
                  {/* Checkbox */}
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => toggleEmailSelection(email.id)}
                    onClick={(e) => e.stopPropagation()}
                    className="data-[state=checked]:bg-accent-cta data-[state=checked]:border-accent-cta rounded-lg transition-colors"
                  />

                  {/* Star */}
                  <button
                    onClick={(e) => handleStarClick(e, email)}
                    className="p-1 hover:bg-muted rounded transition-colors"
                  >
                    <Star 
                      className={cn(
                        "w-4 h-4",
                        email.is_flagged 
                          ? "fill-yellow-400 text-yellow-400" 
                          : "text-muted-foreground hover:text-foreground"
                      )} 
                    />
                  </button>

                  {/* Avatar */}
                  <div className="w-8 h-8 rounded-full overflow-hidden flex-shrink-0 bg-muted flex items-center justify-center">
                    <img
                      src={generateAvatarUrl(email.from_address || '')}
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  </div>

                  {/* Email Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={cn(
                        "font-medium truncate",
                        !email.is_read && "font-semibold"
                      )}>
                        {email.from_address?.split('@')[0] || 'Unknown'}
                      </span>
                      
                      <div className="flex items-center gap-1 ml-auto flex-shrink-0">
                        {email.has_attachments && (
                          <Paperclip className="w-3 h-3 text-muted-foreground" />
                        )}
                        {!email.is_read ? (
                          <Mail className="w-3 h-3 text-primary" />
                        ) : (
                          <MailOpen className="w-3 h-3 text-muted-foreground" />
                        )}
                      </div>
                    </div>
                    
                    <div className={cn(
                      "text-sm mb-1 truncate",
                      !email.is_read ? "font-medium" : "text-muted-foreground"
                    )}>
                      {email.subject || '(no subject)'}
                    </div>
                  </div>

                  {/* Timestamp */}
                  <div className="text-xs text-muted-foreground flex-shrink-0">
                    {formatEmailDate(email.timestamp)}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Pagination Controls */}
        {emailsData && emailsData.total > 0 && (
          <div className="glass-subtle border-t border-border/50 p-3 flex items-center justify-between flex-shrink-0 sticky bottom-0 z-10">
            <div className="text-sm text-muted-foreground">
              Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, emailsData.total)} of {emailsData.total}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1 || isLoading}
                className="px-3 py-1.5 text-sm border border-border rounded hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page * pageSize >= emailsData.total || isLoading}
                className="px-3 py-1.5 text-sm border border-border rounded hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
