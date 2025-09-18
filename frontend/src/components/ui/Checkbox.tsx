import React from 'react';
import { Check } from 'lucide-react';
import { cn } from '@/utils';

interface CheckboxProps {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
  onClick?: (e: React.MouseEvent) => void;
}

export default function Checkbox({ 
  checked = false, 
  onCheckedChange, 
  disabled = false, 
  className,
  onClick 
}: CheckboxProps) {
  const handleClick = (e: React.MouseEvent) => {
    if (onClick) {
      onClick(e);
    }
    if (!disabled && onCheckedChange) {
      onCheckedChange(!checked);
    }
  };

  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      disabled={disabled}
      onClick={handleClick}
      className={cn(
        "w-4 h-4 border border-border rounded flex items-center justify-center transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
        checked ? "bg-primary border-primary text-primary-foreground" : "bg-background hover:bg-muted",
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
    >
      {checked && <Check className="w-3 h-3" />}
    </button>
  );
}
