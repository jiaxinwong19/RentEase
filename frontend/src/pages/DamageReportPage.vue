<script setup lang="ts">
import DamageReportForm from '../components/DamageReportForm.vue'
import { useRoute } from 'vue-router'
import { ref, onMounted } from 'vue'

// Get route instance to access query parameters
const route = useRoute()

// Extract order ID and product ID from query parameters
const orderID = ref<string>(Array.isArray(route.query.orderID) ? route.query.orderID[0] ?? '' : (route.query.orderID as string) || '')
const productID = ref<string>(Array.isArray(route.query.productID) ? route.query.productID[0] ?? '' : (route.query.productID as string) || '')

// Log the parameters to verify they're being received
onMounted(() => {
  console.log('Received orderID:', orderID.value)
  console.log('Received productID:', productID.value)
})
</script>

<template>
  <div class="py-8">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Submit Damage Report</h1>
    
    <!-- Pass the orderID and productID as props to DamageReportForm -->
    <DamageReportForm 
      :orderID="orderID"
      :productID="productID"
    />
  </div>
</template>
