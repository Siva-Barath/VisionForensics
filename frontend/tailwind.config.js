/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Main App Canvas & Surfaces
        canvas: '#F8F9FF',        // Soft white / lavender canvas
        surface: {
          DEFAULT: '#FFFFFF',     // Pure white card surfaces
          panel: '#FFFFFF',
          secondary: '#F0EBFF',   // Light violet accent surface
          muted: '#F4F5FB',       // Subtle input/panel fill
        },
        // Borders
        border: {
          DEFAULT: '#E6E5F0',     // Soft lavender-gray border
          light: '#F0EFF8',
          violet: '#DDD5F9',
        },
        // Typography
        navy: {
          DEFAULT: '#17172F',     // Deep navy main text
          dark: '#0F0F23',
          light: '#2E2E4A',
        },
        slate: {
          DEFAULT: '#73758B',     // Muted slate secondary text
          muted: '#9E9FB1',
          subtle: '#B8B9C9',
        },
        // Primary Brand Accent (Violet)
        violet: {
          50: '#F5F2FF',
          100: '#F0EBFF',
          200: '#DDD5F9',
          300: '#C2B3F5',
          400: '#9B7EF0',
          500: '#7045E8',         // Primary Accent
          600: '#5F33DB',
          700: '#4D24BF',
          800: '#3D1B99',
          900: '#261163',
          DEFAULT: '#7045E8',
        },
        brand: {
          DEFAULT: '#7045E8',     // Primary violet
          hover: '#5F33DB',       // Hover violet
          light: '#F0EBFF',       // Soft violet background
          border: '#DDD5F9',
          dark: '#171335',        // Sidebar dark violet
        },
        // Semantic Forensic Status
        emerald: {
          50: '#F0FBF5',
          100: '#EBF9F1',         // Soft emerald verdict background
          500: '#159B55',         // Primary emerald success
          600: '#118247',
          DEFAULT: '#159B55',
        },
        amber: {
          50: '#FFFDF7',
          100: '#FFF8EC',         // Soft amber review background
          200: '#FFF3D6',
          500: '#E9A12A',         // Primary amber warning
          600: '#C68218',
          DEFAULT: '#E9A12A',
        },
        red: {
          50: '#FEF7F7',
          100: '#FDF2F2',         // Soft red high-risk background
          500: '#DC4545',         // Primary red high-risk
          600: '#B83232',
          DEFAULT: '#DC4545',
        },
        // Legacy compatibility mappings
        ink: {
          base: '#F8F9FF',
          panel: '#FFFFFF',
          border: '#E6E5F0',
          hover: '#F0EBFF',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Roboto Mono', 'SFMono-Regular', 'Menlo', 'monospace'],
        display: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        subtle: '0 1px 3px 0 rgba(23, 23, 47, 0.05), 0 1px 2px -1px rgba(23, 23, 47, 0.05)',
        card: '0 2px 8px -2px rgba(23, 23, 47, 0.06), 0 1px 4px -1px rgba(23, 23, 47, 0.04)',
        elevated: '0 10px 25px -5px rgba(23, 23, 47, 0.08), 0 8px 10px -6px rgba(23, 23, 47, 0.04)',
        violet: '0 4px 14px 0 rgba(112, 69, 232, 0.25)',
      },
      borderRadius: {
        xl: '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
    },
  },
  plugins: [],
};
