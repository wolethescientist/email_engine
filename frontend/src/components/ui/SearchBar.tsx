import { useState, useRef, useEffect } from 'react';
import { Search, X, Filter } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { debounce } from '@/utils';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  onFilterClick?: () => void;
  showFilters?: boolean;
}

export default function SearchBar({ 
  value, 
  onChange, 
  placeholder = "Search emails...",
  onFilterClick,
  showFilters = false
}: SearchBarProps) {
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounced search to avoid too many API calls
  const debouncedOnChange = debounce(onChange, 300);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    debouncedOnChange(newValue);
  };

  const handleClear = () => {
    onChange('');
    inputRef.current?.focus();
  };

  // Keyboard shortcut to focus search (/)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="relative flex-1 max-w-md">
      <div className={`relative flex items-center transition-all duration-200 ${
        isFocused ? 'ring-2 ring-primary ring-offset-2 ring-offset-background' : ''
      }`}>
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            ref={inputRef}
            data-search-input
            type="text"
            placeholder={placeholder}
            defaultValue={value}
            onChange={handleInputChange}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            className="w-full pl-10 pr-10 py-2 bg-muted/50 border border-border rounded-lg focus:outline-none focus:bg-background transition-colors"
          />
          
          <AnimatePresence>
            {value && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                onClick={handleClear}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 hover:bg-muted rounded-full transition-colors"
              >
                <X className="w-3 h-3 text-muted-foreground" />
              </motion.button>
            )}
          </AnimatePresence>
        </div>

        {showFilters && (
          <button
            onClick={onFilterClick}
            className="ml-2 p-2 border border-border rounded-lg hover:bg-muted/50 transition-colors"
          >
            <Filter className="w-4 h-4 text-muted-foreground" />
          </button>
        )}
      </div>

      {/* Search shortcut hint */}
      {!isFocused && !value && (
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
          /
        </div>
      )}
    </div>
  );
}
