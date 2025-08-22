import React from 'react'

interface Props {
  page: number
  size: number
  total: number
  onChange: (page: number) => void
}

const Pagination: React.FC<Props> = ({ page, size, total, onChange }) => {
  const totalPages = Math.max(1, Math.ceil(total / size))
  const canPrev = page > 1
  const canNext = page < totalPages

  return (
    <div className="flex items-center justify-between">
      <div className="text-sm text-secondary-600">
        <span className="font-medium text-secondary-800">{total}</span> items • Page <span className="font-medium text-secondary-800">{page}</span> of <span className="font-medium text-secondary-800">{totalPages}</span>
      </div>
      <div className="flex items-center space-x-2">
        <button 
          disabled={!canPrev} 
          onClick={() => onChange(page - 1)} 
          className="flex items-center px-3 py-1.5 text-sm font-medium text-secondary-600 border border-secondary-300 rounded-lg hover:bg-secondary-50 hover:text-secondary-800 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-secondary-600 transition-colors duration-200"
        >
          <svg className="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd"/>
          </svg>
          Previous
        </button>
        <button 
          disabled={!canNext} 
          onClick={() => onChange(page + 1)} 
          className="flex items-center px-3 py-1.5 text-sm font-medium text-secondary-600 border border-secondary-300 rounded-lg hover:bg-secondary-50 hover:text-secondary-800 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-secondary-600 transition-colors duration-200"
        >
          Next
          <svg className="w-4 h-4 ml-1.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"/>
          </svg>
        </button>
      </div>
    </div>
  )
}

export default Pagination