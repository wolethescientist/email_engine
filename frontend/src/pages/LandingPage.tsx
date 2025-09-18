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
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      {/* Header */}
      <header className="relative z-10 px-4 py-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center space-x-2"
          >
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Mail className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold">ConnexxionEngine</span>
          </motion.div>
          
          <div className="flex items-center space-x-4">
            <ThemeToggle />
            <motion.button
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              onClick={() => setShowConnectionForm(true)}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              Get Started
            </motion.button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="px-4 py-20">
        <div className="max-w-7xl mx-auto text-center">
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
                className="px-8 py-4 bg-primary text-primary-foreground rounded-xl text-lg font-semibold hover:bg-primary/90 transition-colors flex items-center gap-2"
              >
                Connect Your Email
                <ArrowRight className="w-5 h-5" />
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-8 py-4 border border-border rounded-xl text-lg font-semibold hover:bg-muted/50 transition-colors"
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
      <section className="px-4 py-20 bg-muted/30">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold mb-4">Why Choose ConnexxionEngine?</h2>
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
                className="bg-card p-6 rounded-xl border border-border hover:shadow-lg transition-shadow"
              >
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary" />
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
                className="mt-8 px-8 py-4 bg-primary text-primary-foreground rounded-xl text-lg font-semibold hover:bg-primary/90 transition-colors"
              >
                Start Using ConnexxionEngine
              </motion.button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="relative"
            >
              {/* Mock Email Interface */}
              <div className="bg-card border border-border rounded-xl overflow-hidden shadow-2xl">
                <div className="bg-muted/50 px-4 py-3 border-b border-border flex items-center gap-2">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>
                  <div className="text-sm text-muted-foreground ml-4">ConnexxionEngine Email Client</div>
                </div>
                
                <div className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
                      <Mail className="w-5 h-5 text-primary-foreground" />
                    </div>
                    <div>
                      <div className="font-semibold">Welcome to ConnexxionEngine</div>
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
              className="px-12 py-4 bg-primary text-primary-foreground rounded-xl text-xl font-semibold hover:bg-primary/90 transition-colors"
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
