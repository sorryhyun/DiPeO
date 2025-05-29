/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "../packages/ui-kit/src/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    // Colors used in BaseNode.tsx colorMappings
    'border-gray-400', 'ring-gray-300', 'bg-gray-500', 'shadow-gray-200',
    'border-blue-400', 'ring-blue-300', 'bg-blue-500', 'shadow-blue-200',
    'border-green-400', 'ring-green-300', 'bg-green-500', 'shadow-green-200',
    'border-red-400', 'ring-red-300', 'bg-red-500', 'shadow-red-200',
    'border-purple-400', 'ring-purple-300', 'bg-purple-500', 'shadow-purple-200',
    'border-yellow-400', 'ring-yellow-300', 'bg-yellow-500', 'shadow-yellow-200',
    
    // Running state classes
    'border-green-500', 'ring-4', 'ring-green-300', 'animate-pulse', 'shadow-lg', 'shadow-green-200',
    'scale-105', 'bg-green-50', 'animate-ping', 'bg-green-100', 'opacity-20',
    
    // Hover states
    'hover:border-gray-400', 'hover:shadow-gray-200',
    'hover:border-blue-400', 'hover:shadow-blue-200',
    'hover:border-green-400', 'hover:shadow-green-200',
    'hover:border-red-400', 'hover:shadow-red-200',
    'hover:border-purple-400', 'hover:shadow-purple-200',
    'hover:border-yellow-400', 'hover:shadow-yellow-200',
    
    // Special handle colors for specific node types
    '!bg-purple-500', '!bg-teal-500', '!bg-orange-500',
    
    // Generic utility classes
    'border-gray-300', 'ring-2',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};