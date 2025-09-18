import { useState} from 'react';
import { useQuery } from '@tanstack/react-query';
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
import Checkbox from '@/components/ui/Checkbox';
import { Credentials, EmailItem, FolderType } from '@/types';
import { EmailApiService } from '@/services/emailApi';
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

  // Fetch emails
  const { data: emailsData, isLoading, error } = useQuery({
    queryKey: ['emails', credentials.email, folder, searchQuery],
    queryFn: () => EmailApiService.getEmails(credentials, folder, {
      search_text: searchQuery || undefined,
      size: 100, // Load more emails for better UX
    }),
    staleTime: 2 * 60 * 1000, // 2 minutes
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
      <div className="border-b border-border p-3 bg-card/50 flex-shrink-0">
        <div className="flex items-center gap-3">
          <Checkbox
            checked={selectedEmails.size === emails.length && emails.length > 0}
            onCheckedChange={selectAllEmails}
            className="data-[state=checked]:bg-primary data-[state=checked]:border-primary"
          />
          
          <span className="text-sm text-muted-foreground">
            {selectedEmails.size > 0 
              ? `${selectedEmails.size} selected` 
              : `${emails.length} emails`
            }
          </span>

          {selectedEmails.size > 0 && (
            <div className="flex items-center gap-2 ml-auto">
              <button className="p-2 hover:bg-muted rounded-lg transition-colors">
                <Archive className="w-4 h-4" />
              </button>
              <button className="p-2 hover:bg-muted rounded-lg transition-colors">
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
      <div className="flex-1 overflow-auto">
        <div className="space-y-0">
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
                    "flex items-center gap-3 p-3 border-b border-border cursor-pointer transition-colors hover:bg-muted/50",
                    isActive && "bg-primary/5 border-primary/20",
                    !email.is_read && "bg-muted/20"
                  )}
                >
                  {/* Checkbox */}
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => toggleEmailSelection(email.id)}
                    onClick={(e) => e.stopPropagation()}
                    className="data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                  />

                  {/* Star */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      // TODO: Implement star functionality
                    }}
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
                  <div className="w-8 h-8 rounded-full overflow-hidden flex-shrink-0">
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
      </div>
    </div>
  );
}
