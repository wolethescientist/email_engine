import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Mail, 
  Send, 
  FileText, 
  Trash2, 
  Archive, 
  ShieldAlert,
  Plus,
  Settings,
  LogOut,
  User,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { FolderType, Folder } from '@/types';
import { cn } from '@/utils';
import ThemeToggle from '@/components/ui/ThemeToggle';


interface SidebarProps {
  folders: Folder[];
  currentFolder: FolderType;
  onFolderSelect: (folder: FolderType) => void;
  onCompose: () => void;
  onDisconnect: () => void;
  userEmail: string;
}

const folderIcons = {
  inbox: Mail,
  sent: Send,
  drafts: FileText,
  trash: Trash2,
  archive: Archive,
  spam: ShieldAlert,
};

const folderLabels = {
  inbox: 'Inbox',
  sent: 'Sent',
  drafts: 'Drafts',
  trash: 'Trash',
  archive: 'Archive',
  spam: 'Spam',
};

export default function Sidebar({
  folders,
  currentFolder,
  onFolderSelect,
  onCompose,
  onDisconnect,
  userEmail
}: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Mock unread counts - in real app, this would come from API
  const unreadCounts = {
    inbox: 12,
    sent: 0,
    drafts: 3,
    trash: 0,
    archive: 0,
    spam: 2,
  };

  const handleFolderClick = (folder: string) => {
    if (folder in folderLabels) {
      onFolderSelect(folder as FolderType);
    }
  };

  return (
    <motion.div
      initial={{ width: 280 }}
      animate={{ width: isCollapsed ? 80 : 280 }}
      className="bg-card border-r border-border flex flex-col h-full"
    >
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
            <Mail className="w-4 h-4 text-primary-foreground" />
          </div>
          {!isCollapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 min-w-0"
            >
              <h1 className="font-semibold text-sm truncate">ConnexxionEngine</h1>
              <p className="text-xs text-muted-foreground truncate">{userEmail}</p>
            </motion.div>
          )}
        </div>
      </div>

      {/* Compose Button */}
      <div className="p-4">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onCompose}
          className={cn(
            "w-full bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors flex items-center justify-center gap-2",
            isCollapsed ? "p-3" : "py-3 px-4"
          )}
        >
          <Plus className="w-4 h-4" />
          {!isCollapsed && <span>Compose</span>}
        </motion.button>
      </div>

      {/* Folders */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-2">
          {!isCollapsed && (
            <div className="px-2 py-2">
              <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Folders
              </h2>
            </div>
          )}
          
          <div className="space-y-1">
            {folders.map((folder) => {
              const folderType = folder.type as FolderType;
              const isActive = folderType === currentFolder;
              const Icon = folderIcons[folderType as keyof typeof folderIcons] || Mail;
              const label = folderLabels[folderType as keyof typeof folderLabels] || folder.display_name;
              const unreadCount = unreadCounts[folderType as keyof typeof unreadCounts] || 0;

              return (
                <motion.button
                  key={folder.name}
                  whileHover={{ x: 2 }}
                  onClick={() => handleFolderClick(folderType)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors text-left",
                    isActive 
                      ? "bg-primary/10 text-primary font-medium" 
                      : "hover:bg-muted/50 text-muted-foreground hover:text-foreground"
                  )}
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  
                  {!isCollapsed && (
                    <>
                      <span className="flex-1 truncate">{label}</span>
                      {unreadCount > 0 && (
                        <span className="bg-primary text-primary-foreground text-xs px-2 py-0.5 rounded-full min-w-[20px] text-center">
                          {unreadCount > 99 ? '99+' : unreadCount}
                        </span>
                      )}
                    </>
                  )}
                </motion.button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Bottom Section */}
      <div className="border-t border-border p-2">
        {/* User Menu */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm hover:bg-muted/50 transition-colors",
              isCollapsed ? "justify-center" : ""
            )}
          >
            <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
              <User className="w-3 h-3 text-primary" />
            </div>
            
            {!isCollapsed && (
              <>
                <span className="flex-1 text-left truncate text-muted-foreground">
                  {userEmail.split('@')[0]}
                </span>
                <ChevronDown className={cn(
                  "w-4 h-4 text-muted-foreground transition-transform",
                  showUserMenu && "rotate-180"
                )} />
              </>
            )}
          </button>

          {/* User Menu Dropdown */}
          {showUserMenu && !isCollapsed && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute bottom-full left-0 right-0 mb-2 bg-card border border-border rounded-lg shadow-lg overflow-hidden"
            >
              <button className="w-full flex items-center gap-3 px-3 py-2 text-sm hover:bg-muted/50 transition-colors">
                <Settings className="w-4 h-4" />
                <span>Settings</span>
              </button>
              
              <div className="flex items-center justify-between px-3 py-2">
                <span className="text-sm text-muted-foreground">Theme</span>
                <ThemeToggle />
              </div>
              
              <div className="border-t border-border">
                <button
                  onClick={onDisconnect}
                  className="w-full flex items-center gap-3 px-3 py-2 text-sm text-destructive hover:bg-destructive/10 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Disconnect</span>
                </button>
              </div>
            </motion.div>
          )}
        </div>

        {/* Collapse Toggle */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="w-full flex items-center justify-center p-2 mt-2 rounded-lg hover:bg-muted/50 transition-colors"
        >
          <ChevronRight className={cn(
            "w-4 h-4 text-muted-foreground transition-transform",
            !isCollapsed && "rotate-180"
          )} />
        </button>
      </div>
    </motion.div>
  );
}
