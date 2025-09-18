# ConnexxionEngine Frontend

A modern, secure React TypeScript email client built for the ConnexxionEngine API. Features enterprise-grade security, real-time synchronization, and a beautiful user interface.

## Features

### 🔐 Security First
- AES-256-GCM encrypted credential handling
- Session-only storage (no localStorage)
- Secure HTML email rendering with DOMPurify
- JWT token-based authentication

### ⚡ Performance
- Virtual scrolling for large email lists
- Connection pooling optimization
- Debounced search requests
- Optimistic UI updates
- Code splitting and lazy loading

### 🎨 Modern UI/UX
- Beautiful landing page with smooth animations
- Dark/light theme support
- Responsive design (desktop, tablet, mobile)
- Keyboard shortcuts for power users
- Accessibility features (ARIA labels, screen reader support)

### 📧 Email Features
- Multi-provider support (Gmail, Outlook, Yahoo, Custom)
- Rich text email composition with WYSIWYG editor
- Drag-and-drop file attachments (25MB max)
- Auto-save drafts
- Real-time email synchronization
- Advanced search and filtering
- Bulk email operations

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS with custom design system
- **State Management**: TanStack Query (React Query)
- **Animations**: Framer Motion
- **Forms**: React Hook Form with Zod validation
- **Rich Text**: ReactQuill
- **Icons**: Lucide React
- **Virtual Scrolling**: TanStack Virtual

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- ConnexxionEngine backend running on `http://localhost:8000`

### Installation

1. **Clone and navigate to the frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` if needed:
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api
   VITE_ENABLE_DEBUG=true
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

5. **Open your browser**
   Navigate to `http://localhost:5173`

### Building for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── auth/            # Authentication components
│   ├── email/           # Email-specific components
│   ├── layout/          # Layout components
│   └── ui/              # Basic UI components
├── contexts/            # React contexts
├── hooks/               # Custom React hooks
├── pages/               # Page components
├── services/            # API service layer
├── types/               # TypeScript type definitions
├── utils/               # Utility functions
└── config/              # Configuration files
```

## Key Components

### Authentication
- **ConnectionForm**: Secure email credential setup with provider presets
- **ThemeToggle**: Dark/light mode switcher

### Email Management
- **EmailList**: Virtual scrolling email list with bulk operations
- **EmailReader**: Secure HTML email rendering with attachments
- **ComposeModal**: Rich text email composition with auto-save

### Layout
- **Sidebar**: Collapsible navigation with folder management
- **SearchBar**: Debounced search with keyboard shortcuts

## Configuration

### Email Providers

The app includes presets for popular email providers:

```typescript
const EMAIL_PROVIDERS = {
  gmail: {
    imap_host: 'imap.gmail.com',
    imap_port: 993,
    smtp_host: 'smtp.gmail.com',
    smtp_port: 465,
    oauth_supported: true
  },
  // ... other providers
};
```

### Keyboard Shortcuts

- `c` - Compose new email
- `/` - Focus search
- `j/k` - Navigate emails
- `x` - Select email
- `e` - Archive
- `#` - Delete
- `r` - Reply
- `a` - Reply all
- `f` - Forward

## API Integration

The frontend integrates with the ConnexxionEngine backend through a comprehensive API service layer:

```typescript
// Example API usage
const emails = await EmailApiService.getEmails(credentials, 'inbox', {
  page: 1,
  size: 50,
  search_text: 'important'
});
```

### Supported Operations
- Connection validation
- Folder management
- Email CRUD operations
- Attachment handling
- Bulk operations
- Real-time synchronization

## Security Considerations

### Credential Handling
- Credentials are encrypted using AES-256-GCM
- Stored only in sessionStorage (cleared on browser close)
- Never persisted to localStorage or cookies

### Content Security
- HTML emails are sanitized with DOMPurify
- External content loading is controlled
- XSS protection through proper escaping

### Network Security
- All API calls use HTTPS in production
- CORS properly configured
- Request/response validation

## Performance Optimizations

### Virtual Scrolling
Large email lists use virtual scrolling to maintain 60fps performance:

```typescript
const virtualizer = useVirtualizer({
  count: emails.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 80,
  overscan: 5,
});
```

### Code Splitting
The build is optimized with manual chunks:

```typescript
rollupOptions: {
  output: {
    manualChunks: {
      vendor: ['react', 'react-dom'],
      router: ['react-router-dom'],
      query: ['@tanstack/react-query'],
      motion: ['framer-motion'],
    },
  },
}
```

## Accessibility

### ARIA Support
- Proper ARIA labels on interactive elements
- Screen reader announcements for actions
- Keyboard navigation support

### Visual Accessibility
- High contrast mode support
- Scalable typography
- Focus indicators
- Color-blind friendly design

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development

### Code Style
- ESLint + TypeScript strict mode
- Prettier for formatting
- Conventional commits

### Testing
```bash
npm run test        # Unit tests
npm run test:e2e    # End-to-end tests
npm run lint        # Linting
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000/api` |
| `VITE_ENABLE_DEBUG` | Enable debug logging | `true` in dev |
| `VITE_MAX_ATTACHMENT_SIZE` | Max attachment size in bytes | `26214400` (25MB) |

## Deployment

### Netlify/Vercel
1. Build the project: `npm run build`
2. Deploy the `dist` folder
3. Set environment variables in deployment settings

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "preview"]
```

## Troubleshooting

### Common Issues

**Connection Failed**
- Verify backend is running on correct port
- Check CORS configuration
- Validate email credentials

**Slow Performance**
- Enable virtual scrolling for large lists
- Check network tab for API response times
- Verify connection pooling is working

**Theme Issues**
- Clear localStorage and refresh
- Check CSS custom properties
- Verify TailwindCSS compilation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the ConnexxionEngine email management system.

---

For more information about the backend API, see the [API documentation](../README.md).
