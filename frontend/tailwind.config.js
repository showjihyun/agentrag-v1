/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './contexts/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  safelist: [
    // Color variations for dynamic classes
    'bg-purple-100', 'bg-purple-900', 'text-purple-600', 'text-purple-400',
    'bg-blue-100', 'bg-blue-900', 'text-blue-600', 'text-blue-400',
    'bg-red-100', 'bg-red-900', 'text-red-600', 'text-red-400',
    'bg-green-100', 'bg-green-900', 'text-green-600', 'text-green-400',
    'bg-orange-100', 'bg-orange-900', 'text-orange-600', 'text-orange-400',
    'bg-emerald-100', 'bg-emerald-900', 'text-emerald-600', 'text-emerald-400',
    'bg-gray-100', 'bg-gray-900', 'text-gray-600', 'text-gray-400',
    'bg-yellow-100', 'bg-yellow-900', 'text-yellow-600', 'text-yellow-400',
    // Button variations
    'bg-purple-600', 'hover:bg-purple-700',
    'bg-blue-600', 'hover:bg-blue-700',
    'bg-red-600', 'hover:bg-red-700',
    'bg-green-600', 'hover:bg-green-700',
    // Border variations
    'border-purple-500', 'border-blue-500', 'border-red-500', 'border-green-500',
    // Status colors
    'text-red-500', 'text-green-500', 'text-yellow-500',
    // Background variations for cards
    'bg-purple-50', 'bg-blue-50', 'bg-red-50', 'bg-green-50', 'bg-orange-50', 'bg-emerald-50',
    'dark:bg-purple-950', 'dark:bg-blue-950', 'dark:bg-red-950', 'dark:bg-green-950', 'dark:bg-orange-950', 'dark:bg-emerald-950',
    // Text color variations
    'text-purple-700', 'text-blue-700', 'text-red-700', 'text-green-700', 'text-orange-700', 'text-emerald-700',
    'dark:text-purple-300', 'dark:text-blue-300', 'dark:text-red-300', 'dark:text-green-300', 'dark:text-orange-300', 'dark:text-emerald-300',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ['var(--font-geist-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-geist-mono)', 'monospace'],
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}