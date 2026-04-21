import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Mail, 
  Shield, 
  Zap, 
  Server, 
  ArrowRight,
  CheckCircle,
  Globe
} from 'lucide-react';
import { Credentials } from '@/types';
import ConnectionForm from '@/components/auth/ConnectionForm';
import ThemeToggle from '@/components/ui/ThemeToggle';

interface LandingPageProps {
  onConnect: (credentials: Credentials) => void;
}

export default function LandingPage({ onConnect }: LandingPageProps) {
  const [showConnectionForm, setShowConnectionForm] = useState(false);

  const features = [
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'AES-256-GCM encryption, JWT tokens, and secure credential handling ensure your data stays protected.',
    },
    {
      icon: Zap,
      title: 'Lightning Fast',
      description: 'Optimized connection pooling and real-time IMAP IDLE for instant email notifications.',
    },
    {
      icon: Globe,
      title: 'Universal Compatibility',
      description: 'Works with Gmail, Outlook, Yahoo, and any custom IMAP/SMTP server with OAuth2 support.',
    },
    {
      icon: Server,
      title: 'Stateless Architecture',
      description: 'No database required. Direct IMAP/SMTP integration with intelligent folder detection.',
    },
  ];

  const benefits = [
    'Secure encrypted email management',
    'Real-time notifications via WebSocket',
    'Multi-provider support (Gmail, Outlook, Yahoo)',
    'Professional REST API interface',
    'Advanced attachment handling',
    'Intelligent folder classification',
  ];

  return (
    <div className="min-h-screen bg-aurora">
      {/* Header */}
      <header className="relative z-10 px-4 py-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between glass-subtle px-6 py-4 rounded-2xl">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center space-x-2"
          >
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Mail className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold brand-gradient-text">wolemail</span>
          </motion.div>
          
          <div className="flex items-center space-x-4">
            <ThemeToggle />
            <motion.button
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              onClick={() => setShowConnectionForm(true)}
              className="btn-primary"
            >
              Get Started
            </motion.button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="px-4 py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-grid opacity-30"></div>
        <div className="max-w-7xl mx-auto w-full text-center relative z-10 flex flex-col items-center justify-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              Secure Email
              <br />
              <span className="text-primary">Reimagined</span>
            </h1>
            
            <p className="text-xl md:text-2xl text-muted-foreground mb-8 max-w-3xl mx-auto">
              Professional email client with enterprise-grade security, 
              real-time synchronization, and seamless multi-provider support.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setShowConnectionForm(true)}
                className="btn-cta text-lg px-8 py-4"
              >
                Connect Your Email
                <ArrowRight className="w-5 h-5" />
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="btn-ghost text-lg px-8 py-4"
              >
                View Demo
              </motion.button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-2xl mx-auto">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="text-center"
              >
                <div className="text-3xl font-bold text-primary">256-bit</div>
                <div className="text-muted-foreground">AES Encryption</div>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="text-center"
              >
                <div className="text-3xl font-bold text-primary">Real-time</div>
                <div className="text-muted-foreground">Synchronization</div>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="text-center"
              >
                <div className="text-3xl font-bold text-primary">Universal</div>
                <div className="text-muted-foreground">Compatibility</div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-4 py-20 relative">
        <div className="max-w-7xl mx-auto relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16 glass px-8 py-10 rounded-3xl"
          >
            <h2 className="text-4xl font-bold mb-4">Why Choose wolemail?</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Built for professionals who demand security, performance, and reliability in their email infrastructure.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="glass p-8 rounded-2xl hover:glass-strong transition-all duration-300 transform hover:-translate-y-2 group"
              >
                <div className="w-14 h-14 bg-primary/10 rounded-xl flex items-center justify-center mb-6 group-hover:bg-primary/20 transition-colors">
                  <feature.icon className="w-7 h-7 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="px-4 py-20">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <h2 className="text-4xl font-bold mb-6">
                Everything You Need for
                <span className="text-primary"> Professional Email</span>
              </h2>
              
              <div className="space-y-4">
                {benefits.map((benefit, index) => (
                  <motion.div
                    key={benefit}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center gap-3"
                  >
                    <CheckCircle className="w-5 h-5 text-primary flex-shrink-0" />
                    <span className="text-lg">{benefit}</span>
                  </motion.div>
                ))}
              </div>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setShowConnectionForm(true)}
                className="mt-8 btn-primary px-8 py-4 text-lg"
              >
                Start Using wolemail
              </motion.button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="relative"
            >
              {/* Mock Email Interface */}
              <div className="glass-strong rounded-2xl overflow-hidden shadow-2xl relative">
                <div className="absolute inset-0 bg-gradient-to-tr from-primary/5 to-transparent mix-blend-overlay"></div>
                <div className="glass-subtle px-4 py-3 border-b flex items-center gap-2 relative z-10">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>
                  <div className="text-sm font-medium text-muted-foreground ml-4">wolemail Client</div>
                </div>
                
                <div className="p-8 relative z-10 glass-subtle m-4 rounded-xl border border-border/50">
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-12 h-12 rounded-xl brand-gradient flex items-center justify-center shadow-lg relative">
                      <div className="absolute inset-0 rounded-xl animate-pulse-ring"></div>
                      <Mail className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <div className="font-bold text-lg">Welcome to wolemail</div>
                      <div className="text-sm text-muted-foreground">Your secure email client is ready</div>
                    </div>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-primary rounded-full"></div>
                      <span>Encrypted connection established</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-primary rounded-full"></div>
                      <span>Real-time sync enabled</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-primary rounded-full"></div>
                      <span>All folders synchronized</span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-4 py-20 bg-primary/5">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl font-bold mb-4">Ready to Get Started?</h2>
            <p className="text-xl text-muted-foreground mb-8">
              Connect your email account and experience the future of secure email management.
            </p>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowConnectionForm(true)}
              className="btn-cta text-xl px-12 py-4"
            >
              Connect Your Email Now
            </motion.button>
          </motion.div>
        </div>
      </section>

      {/* Connection Form Modal */}
      {showConnectionForm && (
        <ConnectionForm
          onConnect={onConnect}
          onClose={() => setShowConnectionForm(false)}
        />
      )}
    </div>
  );
}
