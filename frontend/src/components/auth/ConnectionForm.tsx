import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { 
  X, 
  Mail, 
  Lock, 
  Server, 
  Eye, 
  EyeOff, 
  Loader2,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Credentials } from '@/types';
import { EMAIL_PROVIDERS } from '@/config';
import { EmailApiService, handleApiError } from '@/services/emailApi';
import { getEmailProvider } from '@/utils';

const connectionSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
  provider: z.string().min(1, 'Please select a provider'),
  imap_host: z.string().min(1, 'IMAP host is required'),
  imap_port: z.number().min(1).max(65535, 'Invalid port number'),
  smtp_host: z.string().min(1, 'SMTP host is required'),
  smtp_port: z.number().min(1).max(65535, 'Invalid port number'),
});

type ConnectionFormData = z.infer<typeof connectionSchema>;

interface ConnectionFormProps {
  onConnect: (credentials: Credentials) => void;
  onClose: () => void;
}

export default function ConnectionForm({ onConnect, onClose }: ConnectionFormProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isValid }
  } = useForm<ConnectionFormData>({
    resolver: zodResolver(connectionSchema),
    mode: 'onChange',
    defaultValues: {
      provider: '',
      imap_port: 993,
      smtp_port: 465,
    }
  });

  const watchedEmail = watch('email');
  const watchedProvider = watch('provider');

  // Auto-detect provider when email changes
  useState(() => {
    if (watchedEmail && !watchedProvider) {
      const detectedProvider = getEmailProvider(watchedEmail);
      if (detectedProvider !== 'custom') {
        setValue('provider', detectedProvider);
        handleProviderChange(detectedProvider);
      }
    }
  });

  const handleProviderChange = (providerKey: string) => {
    const provider = EMAIL_PROVIDERS[providerKey];
    if (provider) {
      setValue('imap_host', provider.imap_host);
      setValue('imap_port', provider.imap_port);
      setValue('smtp_host', provider.smtp_host);
      setValue('smtp_port', provider.smtp_port);
    }
  };

  const testConnection = async (data: ConnectionFormData) => {
    setConnectionStatus('testing');
    
    try {
      const credentials: Credentials = {
        email: data.email,
        password: data.password,
        imap_host: data.imap_host,
        imap_port: data.imap_port,
        smtp_host: data.smtp_host,
        smtp_port: data.smtp_port,
      };

      const response = await EmailApiService.validateConnection(credentials);
      
      if (response.success) {
        setConnectionStatus('success');
        toast.success('Connection successful!');
        return credentials;
      } else {
        setConnectionStatus('error');
        toast.error(response.message || 'Connection failed');
        return null;
      }
    } catch (error) {
      setConnectionStatus('error');
      const errorMessage = handleApiError(error);
      toast.error(errorMessage);
      return null;
    }
  };

  const onSubmit = async (data: ConnectionFormData) => {
    setIsConnecting(true);
    
    const credentials = await testConnection(data);
    
    if (credentials) {
      setTimeout(() => {
        onConnect(credentials);
        onClose();
      }, 1000);
    }
    
    setIsConnecting(false);
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                <Mail className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Connect Your Email</h2>
                <p className="text-sm text-muted-foreground">Enter your email credentials to get started</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
            {/* Email */}
            <div>
              <label className="block text-sm font-medium mb-2">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  {...register('email')}
                  type="email"
                  placeholder="your.email@example.com"
                  className="w-full pl-10 pr-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>
              {errors.email && (
                <p className="text-sm text-destructive mt-1">{errors.email.message}</p>
              )}
            </div>

            {/* Provider Selection */}
            <div>
              <label className="block text-sm font-medium mb-2">Email Provider</label>
              <select
                {...register('provider')}
                onChange={(e) => {
                  setValue('provider', e.target.value);
                  handleProviderChange(e.target.value);
                }}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="">Select a provider</option>
                {Object.entries(EMAIL_PROVIDERS).map(([key, provider]) => (
                  <option key={key} value={key}>
                    {provider.name}
                  </option>
                ))}
              </select>
              {errors.provider && (
                <p className="text-sm text-destructive mt-1">{errors.provider.message}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  className="w-full pl-10 pr-12 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-sm text-destructive mt-1">{errors.password.message}</p>
              )}
            </div>

            {/* Advanced Settings */}
            {watchedProvider === 'custom' && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="space-y-4 border-t border-border pt-4"
              >
                <h3 className="text-sm font-medium flex items-center gap-2">
                  <Server className="w-4 h-4" />
                  Server Settings
                </h3>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">IMAP Host</label>
                    <input
                      {...register('imap_host')}
                      placeholder="imap.example.com"
                      className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
                    />
                    {errors.imap_host && (
                      <p className="text-xs text-destructive mt-1">{errors.imap_host.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">IMAP Port</label>
                    <input
                      {...register('imap_port', { valueAsNumber: true })}
                      type="number"
                      placeholder="993"
                      className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
                    />
                    {errors.imap_port && (
                      <p className="text-xs text-destructive mt-1">{errors.imap_port.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">SMTP Host</label>
                    <input
                      {...register('smtp_host')}
                      placeholder="smtp.example.com"
                      className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
                    />
                    {errors.smtp_host && (
                      <p className="text-xs text-destructive mt-1">{errors.smtp_host.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">SMTP Port</label>
                    <input
                      {...register('smtp_port', { valueAsNumber: true })}
                      type="number"
                      placeholder="465"
                      className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
                    />
                    {errors.smtp_port && (
                      <p className="text-xs text-destructive mt-1">{errors.smtp_port.message}</p>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {/* Connection Status */}
            {connectionStatus !== 'idle' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex items-center gap-2 p-3 rounded-lg ${
                  connectionStatus === 'testing' ? 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300' :
                  connectionStatus === 'success' ? 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300' :
                  'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300'
                }`}
              >
                {connectionStatus === 'testing' && <Loader2 className="w-4 h-4 animate-spin" />}
                {connectionStatus === 'success' && <CheckCircle className="w-4 h-4" />}
                {connectionStatus === 'error' && <AlertCircle className="w-4 h-4" />}
                <span className="text-sm">
                  {connectionStatus === 'testing' && 'Testing connection...'}
                  {connectionStatus === 'success' && 'Connection successful!'}
                  {connectionStatus === 'error' && 'Connection failed. Please check your credentials.'}
                </span>
              </motion.div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!isValid || isConnecting}
              className="w-full py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {isConnecting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Connecting...
                </>
              ) : (
                'Connect Email'
              )}
            </button>

            {/* Security Note */}
            <div className="text-xs text-muted-foreground text-center space-y-1">
              <p>🔒 Your credentials are encrypted and stored securely in your session only.</p>
              <p>We never store your password permanently.</p>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
