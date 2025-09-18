import { Routes, Route } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Credentials } from '@/types';
import LandingPage from '@/pages/LandingPage';
import EmailClient from '@/pages/EmailClient';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AuthProvider } from '@/contexts/AuthContext';

function App() {
  const [credentials, setCredentials] = useState<Credentials | null>(null);

  // Check for existing session on app load
  useEffect(() => {
    const savedCredentials = sessionStorage.getItem('email_credentials');
    if (savedCredentials) {
      try {
        setCredentials(JSON.parse(savedCredentials));
      } catch (error) {
        console.error('Failed to parse saved credentials:', error);
        sessionStorage.removeItem('email_credentials');
      }
    }
  }, []);

  const handleConnect = (creds: Credentials) => {
    setCredentials(creds);
    // Store in session storage (not localStorage for security)
    sessionStorage.setItem('email_credentials', JSON.stringify(creds));
  };

  const handleDisconnect = () => {
    setCredentials(null);
    sessionStorage.removeItem('email_credentials');
  };

  return (
    <ThemeProvider>
      <AuthProvider>
        <div className="min-h-screen bg-background text-foreground">
          <Routes>
            <Route 
              path="/" 
              element={
                credentials ? (
                  <EmailClient 
                    credentials={credentials} 
                    onDisconnect={handleDisconnect}
                  />
                ) : (
                  <LandingPage onConnect={handleConnect} />
                )
              } 
            />
            <Route 
              path="/client" 
              element={
                credentials ? (
                  <EmailClient 
                    credentials={credentials} 
                    onDisconnect={handleDisconnect}
                  />
                ) : (
                  <LandingPage onConnect={handleConnect} />
                )
              } 
            />
          </Routes>
        </div>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
