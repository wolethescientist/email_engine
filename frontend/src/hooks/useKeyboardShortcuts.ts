import { useEffect } from 'react';
import { KEYBOARD_SHORTCUTS } from '@/config';

interface KeyboardShortcutsOptions {
  onCompose?: () => void;
  onSearch?: () => void;
  onNextEmail?: () => void;
  onPrevEmail?: () => void;
  onSelectEmail?: () => void;
  onArchive?: () => void;
  onDelete?: () => void;
  onReply?: () => void;
  onReplyAll?: () => void;
  onForward?: () => void;
  onMarkRead?: () => void;
  onStar?: () => void;
}

export function useKeyboardShortcuts(options: KeyboardShortcutsOptions) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      // Don't trigger when modifier keys are pressed (except for specific combinations)
      if (event.ctrlKey || event.metaKey || event.altKey) {
        return;
      }

      const key = event.key.toLowerCase();

      switch (key) {
        case KEYBOARD_SHORTCUTS.COMPOSE:
          event.preventDefault();
          options.onCompose?.();
          break;
        case KEYBOARD_SHORTCUTS.SEARCH:
          event.preventDefault();
          options.onSearch?.();
          break;
        case KEYBOARD_SHORTCUTS.NEXT_EMAIL:
          event.preventDefault();
          options.onNextEmail?.();
          break;
        case KEYBOARD_SHORTCUTS.PREV_EMAIL:
          event.preventDefault();
          options.onPrevEmail?.();
          break;
        case KEYBOARD_SHORTCUTS.SELECT:
          event.preventDefault();
          options.onSelectEmail?.();
          break;
        case KEYBOARD_SHORTCUTS.ARCHIVE:
          event.preventDefault();
          options.onArchive?.();
          break;
        case KEYBOARD_SHORTCUTS.DELETE:
          event.preventDefault();
          options.onDelete?.();
          break;
        case KEYBOARD_SHORTCUTS.REPLY:
          event.preventDefault();
          options.onReply?.();
          break;
        case KEYBOARD_SHORTCUTS.REPLY_ALL:
          event.preventDefault();
          options.onReplyAll?.();
          break;
        case KEYBOARD_SHORTCUTS.FORWARD:
          event.preventDefault();
          options.onForward?.();
          break;
        case KEYBOARD_SHORTCUTS.MARK_READ:
          event.preventDefault();
          options.onMarkRead?.();
          break;
        case KEYBOARD_SHORTCUTS.STAR:
          event.preventDefault();
          options.onStar?.();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [options]);
}
