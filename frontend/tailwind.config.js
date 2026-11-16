/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Chrome / Application Background
        ink: {
          base: '#0b1018',      // Deep Ink - primary chrome
          panel: '#121b28',     // Panel background
          border: '#263345',    // Border color
          hover: '#1a2738',     // Hover state
        },
        // Paper / Exhibit Background
        paper: {
          DEFAULT: '#e5e7eb',   // Warm-grey paper tone
          dark: '#d1d5db',      // Darker variant for contrast
        },
        // Primary Interaction (Brand)
        brand: {
          DEFAULT: '#0e9cba',   // Muted Cyan
          hover: '#38bed6',     // Hover variant
          muted: '#164e63',     // Muted brand
          light: '#38bed6',     // Light variant
        },
        // Severity Scale (Risk & Evidence)
        severity: {
          critical: '#f16d79',  // Deliberate Red (#991b1b for dark variant)
          criticalDark: '#991b1b',
          high: '#e7ad53',      // Muted Amber/Ochre
          highDark: '#b45309',  // Dark amber
          verified: '#98b4c8',  // Slate (cleared/authentic state)
          verifiedAlt: '#4b5563', // Mixed slate-green for authenticity
          low: '#10b981',       // Controlled Green (cleared state)
          lowDark: '#059669',   // Dark green
        },
        // Muted text & UI
        muted: {
          DEFAULT: '#94a3b8',
          light: '#dce4ef',
          dark: '#7c8da5',
        },
        // Additional utilities
        surface: {
          base: '#0b1018',
          panel: '#121b28',
          elevated: '#1a2738',
          hover: '#263345',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Roboto Mono', 'monospace'],
        display: ['Manrope', 'Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        // Technical forensic readouts
        'forensic-lg': ['0.875rem', { lineHeight: '1.25rem', letterSpacing: '0.05em' }],
        'forensic-md': ['0.8125rem', { lineHeight: '1.25rem', letterSpacing: '0.08em' }],
        'forensic-sm': ['0.75rem', { lineHeight: '1rem', letterSpacing: '0.1em' }],
      },
      letterSpacing: {
        forensic: '0.1em',
        caseId: '0.05em',
      },
      borderRadius: {
        // Slightly tighter border radius for precision aesthetic
        sm: '0.25rem',
        DEFAULT: '0.375rem',
        md: '0.5rem',
        lg: '0.75rem',
      },
    },
  },
  plugins: [],
}
