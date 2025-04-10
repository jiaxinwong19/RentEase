<template>

  <nav class="bg-gray-900 fixed w-full z-20 top-0 start-0">
    <div class="max-w-screen-xl flex items-center justify-between mx-auto p-4">
      <a href="#" class="flex items-center space-x-3 rtl:space-x-reverse">
        <svg class="h-8" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="rentEaseGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#3b82f6"/>
              <stop offset="100%" style="stop-color:#6366f1"/>
            </linearGradient>
          </defs>
          <!-- Main circle -->
          <circle cx="20" cy="20" r="18" fill="url(#rentEaseGradient)" />
          
          <!-- Exchange arrows -->
          <path d="M12,15 L24,15 L20,11 M28,25 L16,25 L20,29" 
                stroke="white" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          
          <!-- Central diamond/package -->
          <rect x="15" y="17" width="10" height="6" fill="white" transform="rotate(45, 20, 20)" />
        </svg>
        <span class="self-center text-2xl font-semibold whitespace-nowrap text-white">RentEase</span>
      </a>
      <div class="flex items-center">
        <ul class="flex space-x-8 rtl:space-x-reverse font-medium">
          <li>
            <a href="/" class="text-white hover:text-blue-500" aria-current="page">Home</a>
          </li>
          <li>
            <a href="/damage-report" class="text-white hover:text-blue-500">Damage Report</a>
          </li>
          <li>
            <a href="/orders" class="text-white hover:text-blue-500">Orders</a>
          </li>
          <li>
            <a href="/user-orders" class="text-white hover:text-blue-500">User Orders</a>
          </li>
        </ul>
      </div>
      <div class="flex items-center space-x-4">
        <!-- Profile Icon -->
        <router-link to="/profile" class="text-white hover:text-blue-500">
          <div class="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center hover:bg-blue-700 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
        </router-link>
        <!-- Logout Button -->
        <button type="button"
          @click="handleLogout"
          class="text-white bg-blue-600 hover:bg-blue-700 focus:ring-4 focus:outline-none focus:ring-blue-800 font-medium rounded-lg text-sm px-5 py-2.5 text-center">Logout</button>
      </div>
    </div>
  </nav>

</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const handleLogout = () => {
  // Clear all authentication-related data from localStorage
  localStorage.removeItem('isAuthenticated')
  localStorage.removeItem('userId')
  localStorage.removeItem('userEmail')
  localStorage.removeItem('cart')
  
  // Redirect to login page
  router.push('/login')
}
</script>
