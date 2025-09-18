import { useState, useRef, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion, AnimatePresence } from 'framer-motion';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import {
  X,
  Send,
  Paperclip,
  Minimize2,
  Maximize2,
  Save,
  Loader2
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Credentials, SendEmailRequest, AttachmentIn } from '@/types';
import { EmailApiService, handleApiError } from '@/services/emailApi';
import { parseEmailList, formatFileSize, cn } from '@/utils';

const composeSchema = z.object({
  to: z.string().min(1, 'At least one recipient is required'),
  cc: z.string().optional(),
  bcc: z.string().optional(),
  subject: z.string().optional(),
  body: z.string().optional(),
});

type ComposeFormData = z.infer<typeof composeSchema>;

interface ComposeModalProps {
  credentials: Credentials;
  onClose: () => void;
  replyTo?: {
    subject: string;
    to: string[];
    body: string;
  };
}

export default function ComposeModal({ credentials, onClose, replyTo }: ComposeModalProps) {
  const [isMinimized, setIsMinimized] = useState(false);
  const [showCc, setShowCc] = useState(false);
  const [showBcc, setShowBcc] = useState(false);
  const [attachments, setAttachments] = useState<AttachmentIn[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isDirty }
  } = useForm<ComposeFormData>({
    resolver: zodResolver(composeSchema),
    defaultValues: {
      to: replyTo?.to.join(', ') || '',
      subject: replyTo?.subject ? `Re: ${replyTo.subject}` : '',
      body: replyTo?.body ? `\n\n--- Original Message ---\n${replyTo.body}` : '',
    }
  });

  const watchedBody = watch('body');

  // Auto-save draft every 30 seconds
  useEffect(() => {
    if (!isDirty) return;

    const interval = setInterval(() => {
      saveDraft();
    }, 30000);

    return () => clearInterval(interval);
  }, [isDirty, watchedBody]);

  // Send email mutation
  const sendMutation = useMutation({
    mutationFn: (emailData: SendEmailRequest) => EmailApiService.sendEmail(emailData),
    onSuccess: () => {
      toast.success('Email sent successfully!');
      queryClient.invalidateQueries({ queryKey: ['emails'] });
      onClose();
    },
    onError: (error) => {
      toast.error(handleApiError(error));
    },
  });

  // Save draft mutation
  const draftMutation = useMutation({
    mutationFn: (emailData: SendEmailRequest) => EmailApiService.saveDraft(emailData),
    onSuccess: () => {
      toast.success('Draft saved');
      queryClient.invalidateQueries({ queryKey: ['emails', credentials.email, 'drafts'] });
    },
    onError: (error) => {
      toast.error(handleApiError(error));
    },
  });

  const saveDraft = async () => {
    const formData = watch();
    const emailData: SendEmailRequest = {
      creds: credentials,
      to: parseEmailList(formData.to || ''),
      cc: parseEmailList(formData.cc || ''),
      bcc: parseEmailList(formData.bcc || ''),
      subject: formData.subject,
      body: formData.body,
      attachments,
    };

    if (emailData.to.length > 0 || emailData.subject || emailData.body) {
      draftMutation.mutate(emailData);
    }
  };

  const onSubmit = (data: ComposeFormData) => {
    const emailData: SendEmailRequest = {
      creds: credentials,
      to: parseEmailList(data.to),
      cc: parseEmailList(data.cc || ''),
      bcc: parseEmailList(data.bcc || ''),
      subject: data.subject,
      body: data.body,
      attachments,
    };

    sendMutation.mutate(emailData);
  };

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;

    Array.from(files).forEach(file => {
      if (file.size > 25 * 1024 * 1024) { // 25MB limit
        toast.error(`File ${file.name} is too large. Maximum size is 25MB.`);
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        const base64 = e.target?.result as string;
        const content = base64.split(',')[1]; // Remove data:type;base64, prefix

        const attachment: AttachmentIn = {
          filename: file.name,
          content_base64: content,
          content_type: file.type,
        };

        setAttachments(prev => [...prev, attachment]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };

  // Quill modules configuration
  const quillModules = {
    toolbar: [
      [{ 'header': [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ 'list': 'ordered'}, { 'list': 'bullet' }],
      [{ 'color': [] }, { 'background': [] }],
      ['link'],
      ['clean']
    ],
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-end justify-end p-4"
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ 
            opacity: 1, 
            scale: 1, 
            y: 0,
            height: isMinimized ? 60 : 600,
            width: isMinimized ? 300 : 700
          }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className={cn(
            "bg-card border border-border rounded-lg shadow-2xl flex flex-col overflow-hidden",
            isDragging && "ring-2 ring-primary"
          )}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border bg-muted/30">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold">
                {replyTo ? 'Reply' : 'New Message'}
              </h3>
              {draftMutation.isPending && (
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Saving...
                </div>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="p-1 hover:bg-muted rounded transition-colors"
              >
                {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
              </button>
              <button
                onClick={onClose}
                className="p-1 hover:bg-muted rounded transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {!isMinimized && (
            <form onSubmit={handleSubmit(onSubmit)} className="flex-1 flex flex-col">
              {/* Recipients */}
              <div className="p-4 space-y-3 border-b border-border">
                <div className="flex items-center gap-3">
                  <label className="text-sm font-medium w-12">To:</label>
                  <input
                    {...register('to')}
                    placeholder="Recipients (separate with commas)"
                    className="flex-1 px-3 py-1 border border-border rounded focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
                  />
                  <div className="flex gap-1">
                    {!showCc && (
                      <button
                        type="button"
                        onClick={() => setShowCc(true)}
                        className="text-sm text-muted-foreground hover:text-foreground"
                      >
                        Cc
                      </button>
                    )}
                    {!showBcc && (
                      <button
                        type="button"
                        onClick={() => setShowBcc(true)}
                        className="text-sm text-muted-foreground hover:text-foreground ml-2"
                      >
                        Bcc
                      </button>
                    )}
                  </div>
                </div>
                {errors.to && (
                  <p className="text-sm text-destructive ml-15">{errors.to.message}</p>
                )}

                {showCc && (
                  <div className="flex items-center gap-3">
                    <label className="text-sm font-medium w-12">Cc:</label>
                    <input
                      {...register('cc')}
                      placeholder="Carbon copy recipients"
                      className="flex-1 px-3 py-1 border border-border rounded focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
                    />
                  </div>
                )}

                {showBcc && (
                  <div className="flex items-center gap-3">
                    <label className="text-sm font-medium w-12">Bcc:</label>
                    <input
                      {...register('bcc')}
                      placeholder="Blind carbon copy recipients"
                      className="flex-1 px-3 py-1 border border-border rounded focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
                    />
                  </div>
                )}

                <div className="flex items-center gap-3">
                  <label className="text-sm font-medium w-12">Subject:</label>
                  <input
                    {...register('subject')}
                    placeholder="Email subject"
                    className="flex-1 px-3 py-1 border border-border rounded focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
                  />
                </div>
              </div>

              {/* Attachments */}
              {attachments.length > 0 && (
                <div className="p-4 border-b border-border">
                  <div className="flex items-center gap-2 mb-3">
                    <Paperclip className="w-4 h-4" />
                    <span className="text-sm font-medium">
                      {attachments.length} attachment{attachments.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                  
                  <div className="space-y-2">
                    {attachments.map((attachment, index) => (
                      <div key={index} className="flex items-center gap-3 p-2 bg-muted/50 rounded">
                        <Paperclip className="w-4 h-4 text-muted-foreground" />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium truncate">{attachment.filename}</div>
                          <div className="text-xs text-muted-foreground">
                            {formatFileSize(attachment.content_base64.length * 0.75)} {/* Approximate size */}
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeAttachment(index)}
                          className="p-1 hover:bg-muted rounded transition-colors"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Body */}
              <div className="flex-1 min-h-0">
                <ReactQuill
                  value={watchedBody}
                  onChange={(content) => setValue('body', content, { shouldDirty: true })}
                  modules={quillModules}
                  placeholder="Write your message..."
                  className="h-full [&_.ql-container]:border-0 [&_.ql-toolbar]:border-0 [&_.ql-toolbar]:border-b [&_.ql-toolbar]:border-border"
                />
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between p-4 border-t border-border bg-muted/30">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="p-2 hover:bg-muted rounded-lg transition-colors"
                  >
                    <Paperclip className="w-4 h-4" />
                  </button>
                  
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    className="hidden"
                    onChange={(e) => handleFileSelect(e.target.files)}
                  />
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={saveDraft}
                    disabled={draftMutation.isPending}
                    className="px-4 py-2 text-sm border border-border rounded-lg hover:bg-muted/50 transition-colors flex items-center gap-2"
                  >
                    <Save className="w-3 h-3" />
                    Save Draft
                  </button>
                  
                  <button
                    type="submit"
                    disabled={sendMutation.isPending}
                    className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2 font-medium"
                  >
                    {sendMutation.isPending ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4" />
                        Send
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
