/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'var(--color-primary)',
          hover: 'var(--color-primary-hover)',
          bg: 'var(--color-primary-bg)',
        },
        surface: {
          layout: 'var(--color-bg-layout)',
          container: 'var(--color-bg-container)',
          elevated: 'var(--color-bg-elevated)',
        },
        text: {
          primary: 'var(--color-text-base)',
          secondary: 'var(--color-text-secondary)',
        },
        border: {
          DEFAULT: 'var(--color-border)',
          secondary: 'var(--color-border-secondary)',
        },
        semantic: {
          success: 'var(--color-success)',
          warning: 'var(--color-warning)',
          error: 'var(--color-error)',
        },
      },
      fontFamily: {
        sans: [
          "'Inter'",
          '-apple-system',
          'BlinkMacSystemFont',
          "'Segoe UI'",
          'sans-serif',
        ],
      },
      borderRadius: {
        DEFAULT: '8px',
        sm: '4px',
        lg: '12px',
      },
    },
  },
  plugins: [],
}
