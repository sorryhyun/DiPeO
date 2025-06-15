/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "../packages/ui-kit/src/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    // Animation and state classes that are still used directly
    'animate-pulse', 'animate-ping', 'scale-105', 'bg-green-50', 'bg-green-100', 'opacity-20',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};