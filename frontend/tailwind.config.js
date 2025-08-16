/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        sage: {
          50: '#F4F3F3',
          100: '#E5E5E5',
          200: '#D3D1CF',
          300: '#9B9896',
          400: '#1D1C1B',
          500: '#0066FF',
          600: '#0052CC',
          700: '#00CC88',
          800: '#EF4444',
          900: '#F97316',
        }
      }
    },
  },
  plugins: [],
}
