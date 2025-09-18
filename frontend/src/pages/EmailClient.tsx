import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Credentials, FolderType } from '@/types';
import { EmailApiService } from '@/services/emailApi';
import Sidebar from '@/components/layout/Sidebar';
import EmailList from '@/components/email/EmailList';
import EmailReader from '@/components/email/EmailReader';
import ComposeModal from '@/components/email/ComposeModal';
import SearchBar from '@/components/ui/SearchBar';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorBoundary from '@/components/ui/ErrorBoundary';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

interface EmailClientProps {
  credentials: Credentials;
  onDisconnect: () => void;
}

export default function EmailClient({ credentials, onDisconnect }: EmailClientProps) {
  const [currentFolder, setCurrentFolder] = useState<FolderType>('inbox');
  const [selectedEmailId, setSelectedEmailId] = useState<number | null>(null);
  const [showCompose, setShowCompose] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch available folders
  const { data: foldersData, isLoading: foldersLoading } = useQuery({
    queryKey: ['folders', credentials.email],
    queryFn: () => EmailApiService.getFolders(credentials),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });


  // Set up keyboard shortcuts
  useKeyboardShortcuts({
    onCompose: () => setShowCompose(true),
    onSearch: () => {
      const searchInput = document.querySelector('[data-search-input]') as HTMLInputElement;
      searchInput?.focus();
    },
  });

  // Reset selected email when folder changes
  useEffect(() => {
    setSelectedEmailId(null);
  }, [currentFolder]);

  if (foldersLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="h-screen flex bg-background">
        {/* Sidebar */}
        <Sidebar
          folders={foldersData?.folders || []}
          currentFolder={currentFolder}
          onFolderSelect={setCurrentFolder}
          onCompose={() => setShowCompose(true)}
          onDisconnect={onDisconnect}
          userEmail={credentials.email}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Header */}
          <header className="border-b border-border bg-card/50 backdrop-blur-sm">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-4 flex-1">
                <h1 className="text-xl font-semibold capitalize">{currentFolder}</h1>
                <SearchBar
                  value={searchQuery}
                  onChange={setSearchQuery}
                  placeholder={`Search in ${currentFolder}...`}
                />
              </div>
            </div>
          </header>

          {/* Email Content */}
          <div className="flex-1 flex min-h-0">
            {/* Email List */}
            <div className={`${selectedEmailId ? 'w-1/3' : 'flex-1'} border-r border-border transition-all duration-200`}>
              <EmailList
                credentials={credentials}
                folder={currentFolder}
                searchQuery={searchQuery}
                selectedEmailId={selectedEmailId}
                onEmailSelect={setSelectedEmailId}
              />
            </div>

            {/* Email Reader */}
            {selectedEmailId && (
              <div className="flex-1 min-w-0">
                <EmailReader
                  credentials={credentials}
                  emailId={selectedEmailId}
                  folder={currentFolder}
                  onClose={() => setSelectedEmailId(null)}
                  onReply={() => {
                    // TODO: Implement reply functionality
                    setShowCompose(true);
                  }}
                  onCompose={() => setShowCompose(true)}
                />
              </div>
            )}
          </div>
        </div>

        {/* Compose Modal */}
        {showCompose && (
          <ComposeModal
            credentials={credentials}
            onClose={() => setShowCompose(false)}
          />
        )}
      </div>
    </ErrorBoundary>
  );
}
