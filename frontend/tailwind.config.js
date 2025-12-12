/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Milling', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      fontWeight: {
        thin: '200',      // Simplex 0.5mm
        light: '300',     // Simplex 0.75mm
        normal: '400',    // Duplex 1mm (primary)
        medium: '500',    // Triplex 1mm
        semibold: '500',  // Triplex 1mm (same as medium)
        bold: '500',      // Triplex 1mm (lighter bold)
      },
      fontSize: {
        // Headline 1
        'h1-desktop': ['64px', { lineHeight: '72px', letterSpacing: '0' }],
        'h1-mobile': ['36px', { lineHeight: '44px', letterSpacing: '0' }],
        // Headline 2
        'h2-desktop': ['56px', { lineHeight: '64px', letterSpacing: '0' }],
        'h2-mobile': ['32px', { lineHeight: '40px', letterSpacing: '0' }],
        // Headline 3
        'h3-desktop': ['48px', { lineHeight: '56px', letterSpacing: '0' }],
        'h3-mobile': ['28px', { lineHeight: '36px', letterSpacing: '0' }],
        // Headline 4
        'h4-desktop': ['40px', { lineHeight: '48px', letterSpacing: '0' }],
        'h4-mobile': ['24px', { lineHeight: '32px', letterSpacing: '0' }],
        // Headline 5
        'h5-desktop': ['32px', { lineHeight: '40px', letterSpacing: '0' }],
        'h5-mobile': ['20px', { lineHeight: '28px', letterSpacing: '0' }],
        // Headline 6
        'h6-desktop': ['24px', { lineHeight: '32px', letterSpacing: '0' }],
        'h6-mobile': ['18px', { lineHeight: '26px', letterSpacing: '0' }],
        // Large Paragraph
        'lg-desktop': ['20px', { lineHeight: '28px', letterSpacing: '0.01em' }],
        'lg-mobile': ['18px', { lineHeight: '26px', letterSpacing: '0.01em' }],
        // Paragraph (default)
        'base': ['16px', { lineHeight: '24px', letterSpacing: '0.015em' }],
        // Small Text
        'sm': ['12px', { lineHeight: '20px', letterSpacing: '0.02em' }],
        // Tag
        'tag': ['12px', { lineHeight: '20px', letterSpacing: 'normal' }],
        // Inline Code
        'code': ['16px', { lineHeight: '24px', letterSpacing: '0' }],
      },
      colors: {
        // Masterbrand - Neutrals
        chalk: '#F4F3F3',
        fog: '#ECECEC',
        smoke: '#D3D1CF',
        ash: '#8F8984',
        shadow: '#45423F',
        charcoal: '#1D1C1B',
        
        // Masterbrand - Primary Colors (Blue)
        blue: {
          DEFAULT: '#366B7F',  // Dark Blue as primary
          light: '#6CD5FD',    // Light Blue (was default)
          dark: '#366B7F',     // Dark Blue
        },
        
        // Masterbrand - Primary Colors (Green)
        green: {
          DEFAULT: '#60E21B',
          light: '#BFF3A4',
          dark: '#30710E',
        },
        
        // Supporting Colors
        'neutral-gray': '#E9E8E7',
        
        // System Colors - Error
        error: {
          dark: '#9D4228',
          DEFAULT: '#E22E22',
          light: '#FFCCC0',
        },
        
        // System Colors - Warning
        warning: {
          dark: '#7D5D0C',
          DEFAULT: '#FABA17',
          light: '#FDE3A2',
        },
        
        // System Colors - Success (using Embed Green)
        success: {
          dark: '#30710E',
          DEFAULT: '#60E21B',
          light: '#BFF3A4',
        },
        
        // System Colors - Info (Blue-based)
        info: {
          dark: '#366B7F',
          DEFAULT: '#366B7F',  // Dark Blue as primary
          light: '#6CD5FD',
        },
        
        // Legacy Primary Scale (mapped to Blue/Green)
        primary: {
          50: '#C4EEFE',   // Light Blue
          100: '#6CD5FD',  // Light Blue
          200: '#BFF3A4',  // Light Green
          300: '#366B7F',  // Dark Blue (primary)
          400: '#60E21B',  // Green
          500: '#30710E',  // Dark Green
          600: '#1D1C1B', // Charcoal
          700: '#1D1C1B', // Charcoal
          DEFAULT: '#366B7F', // Dark Blue as primary
          foreground: '#FFFFFF', // White text on primary
        },
        
        // Semantic UI Colors
        background: '#FFFFFF',
        foreground: '#1D1C1B',
        card: {
          DEFAULT: '#FFFFFF',
          foreground: '#1D1C1B',
        },
        destructive: {
          DEFAULT: '#E22E22',
          foreground: '#FFFFFF',
        },
        muted: {
          DEFAULT: '#ECECEC',
          foreground: '#8F8984',
        },
        accent: {
          DEFAULT: '#ECECEC',
          foreground: '#1D1C1B',
        },
        border: '#D3D1CF',
        input: '#D3D1CF',
        ring: '#366B7F',
        secondary: {
          DEFAULT: '#ECECEC',
          foreground: '#1D1C1B',
        },
      },
      spacing: {
        'xs': '20px',   // Spacer XS - 5 × 4px
        'sm': '40px',   // Spacer SM - 10 × 4px
        'md': '64px',   // Spacer MD - 16 × 4px
        'lg': '96px',   // Spacer LG - 24 × 4px
      },
      borderRadius: {
        'brand': '30%', // Brand radius - 30% of shortest side
      },
      backgroundImage: {
        'gradient-masterbrand': 'linear-gradient(to right, #6CD5FD, #BFF3A4, #60E21B)',
        'gradient-masterbrand-1': 'linear-gradient(to right, #6CD5FD, #C4EEFE, #60E21B)',
        'gradient-masterbrand-2': 'linear-gradient(to right, #C4EEFE, #6CD5FD, #BFF3A4)',
        'gradient-masterbrand-3': 'linear-gradient(to right, #366B7F, #6CD5FD, #BFF3A4)',
        'gradient-masterbrand-4': 'linear-gradient(to right, #60E21B, #BFF3A4, #6CD5FD)',
        'gradient-search-1': 'linear-gradient(to right, #366B7F, #6CD5FD, #C4EEFE)',
        'gradient-search-2': 'linear-gradient(to right, #C4EEFE, #6CD5FD, #E9E8E7)',
        'gradient-search-3': 'linear-gradient(to right, #6CD5FD, #E9E8E7, #C4EEFE)',
        'gradient-search-4': 'linear-gradient(to right, #6CD5FD, #C4EEFE, #BFF3A4)',
        'gradient-generate-1': 'linear-gradient(to right, #30710E, #60E21B, #BFF3A4)',
        'gradient-generate-2': 'linear-gradient(to right, #BFF3A4, #60E21B, #E9E8E7)',
        'gradient-generate-3': 'linear-gradient(to right, #30710E, #BFF3A4, #60E21B)',
        'gradient-generate-4': 'linear-gradient(to right, #60E21B, #BFF3A4, #6CD5FD)',
        'gradient-embed-1': 'linear-gradient(to right, #BFF3A4, #C4EEFE, #E9E8E7)',
        'gradient-embed-2': 'linear-gradient(to right, #30710E, #6CD5FD, #BFF3A4)',
        'gradient-embed-3': 'linear-gradient(to right, #C4EEFE, #BFF3A4, #60E21B)',
        'gradient-embed-4': 'linear-gradient(to right, #60E21B, #6CD5FD, #366B7F)',
      },
    },
  },
  plugins: [],
}
