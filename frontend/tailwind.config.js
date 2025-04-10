/** @type {import('tailwindcss').Config} */
export default {
    content: [
      "./index.html",
      "./src/**/*.{vue,js,ts,jsx,tsx}",
      "./node_modules/flowbite/**/*.js"  // ✅ Required for Flowbite components
    ],
    theme: {
      extend: {},
    },
    plugins: [
      require('flowbite/plugin')  // ✅ This loads Flowbite's plugin
    ],
  }
  