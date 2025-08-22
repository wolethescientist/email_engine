import React from 'react'

interface TabItem {
  key: string
  label: string
}

interface TabsProps {
  items: TabItem[]
  activeKey: string
  onChange: (key: string) => void
}

const Tabs: React.FC<TabsProps> = ({ items, activeKey, onChange }) => {
  return (
    <div className="border-b border-secondary-200 bg-white/50 backdrop-blur-sm rounded-t-xl">
      <nav className="-mb-px flex space-x-1 px-4" aria-label="Tabs">
        {items.map((t) => (
          <button
            key={t.key}
            onClick={() => onChange(t.key)}
            className={`whitespace-nowrap py-3 px-4 border-b-2 text-sm font-medium rounded-t-lg transition-all duration-200 ${
              activeKey === t.key 
                ? 'border-primary-500 text-primary-600 bg-primary-50/50' 
                : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300 hover:bg-secondary-50/50'
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  )
}

export default Tabs