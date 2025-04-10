<template>
    <div class="min-h-screen bg-gray-50 py-8 pt-24">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 class="text-2xl font-bold text-gray-900 mb-6">My Orders</h1>

            <!-- Tabs -->
            <div class="border-b border-gray-200 mb-6">
                <nav class="-mb-px flex space-x-8">
                    <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id" :class="[
                        activeTab === tab.id
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                        'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
                    ]">
                        {{ tab.name }}
                        <span :class="[
                            activeTab === tab.id ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-900',
                            'ml-2 py-0.5 px-2.5 rounded-full text-xs font-medium'
                        ]">
                            {{ getOrderCountForTab(tab.id) }}
                        </span>
                    </button>
                </nav>
            </div>

            <!-- Loading state -->
            <div v-if="loading" class="flex justify-center py-12">
                <svg class="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none"
                    viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
                    </path>
                </svg>
            </div>

            <!-- Error state -->
            <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"
                            fill="currentColor">
                            <path fill-rule="evenodd"
                                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                                clip-rule="evenodd" />
                        </svg>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-sm font-medium text-red-800">Failed to load orders</h3>
                        <div class="mt-2 text-sm text-red-700">{{ error }}</div>
                        <div class="mt-4">
                            <button @click="fetchOrders"
                                class="px-3 py-2 text-sm font-medium text-red-700 bg-red-100 hover:bg-red-200 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                                Try Again
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- No orders state -->
            <div v-else-if="getOrdersForCurrentTab().length === 0" class="bg-white shadow rounded-lg p-6 text-center">
                <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2">
                    </path>
                </svg>
                <h3 class="mt-2 text-lg font-medium text-gray-900">No {{ activeTab }} orders</h3>
                <p class="mt-1 text-sm text-gray-500">
                    {{ getEmptyStateMessage(activeTab) }}
                </p>
            </div>

            <!-- Order list -->
            <div v-else class="grid gap-4">
                <div v-for="order in getOrdersForCurrentTab()" :key="order.orderID" :class="[
                    'bg-white shadow rounded-lg p-6 border-l-4',
                    getOrderStatusClasses(order.status).border
                ]">
                    <div class="flex justify-between items-start">
                        <div>
                            <h3 class="text-lg font-medium text-gray-900">Order #{{ order.orderID }}</h3>
                            <p class="mt-1 text-sm text-gray-500">Product ID: {{ order.productID }}</p>
                            <p class="mt-1 text-sm text-gray-500">
                                Rental Period: {{ formatDate(order.startDate) }} - {{ formatDate(order.endDate) }}
                            </p>
                            <p class="mt-1 text-sm text-gray-500">Total Amount: ${{ order.paymentAmount }}</p>
                            <p class="mt-1 text-sm text-gray-500">Daily Rate: ${{ order.dailyPayment }}</p>
                        </div>
                        <div class="flex flex-col items-end space-y-2">
                            <span :class="[
                                getOrderStatusClasses(order.status).badge,
                                'px-3 py-1 text-sm font-medium rounded-full'
                            ]">
                                {{ capitalizeFirst(order.status) }}
                            </span>

                            <!-- Action buttons based on order status -->
                            <div v-if="order.status === 'shipping'" class="flex space-x-2">
                                <button @click="confirmDelivery(order)"
                                    class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2">
                                    Confirm Delivery
                                </button>
                            </div>
                            <div v-else-if="order.status === 'completed'" class="flex space-x-2">
                                <button @click="submitDamageReport(order)"
                                    class="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2">
                                    Submit Damage Report
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router' // Add this import

// Constants for API URLs
const ORDER_RECORDS_URL = '/order-records'
const router = useRouter() // Add this line to get the router instance

// State
const activeTab = ref('pending')
const allOrders = ref([])
const loading = ref(false)
const error = ref(null)

// Define tabs
const tabs = [
    { id: 'pending', name: 'Pending' },
    { id: 'fulfilled', name: 'Fulfilled' },
    { id: 'shipping', name: 'Shipping' },
    { id: 'completed', name: 'Completed' },
    { id: 'late', name: 'Late' }
]

// Status to tab mapping
const statusToTab = {
    'pending': 'pending',
    'paid': 'fulfilled',
    'shipping': 'shipping',
    'completed': 'completed',
    'late': 'late',
    'rejected': 'pending' // Show rejected orders in pending tab with different styling
}

// Format date function
const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    })
}

// Capitalize first letter
const capitalizeFirst = (str) => {
    return str.charAt(0).toUpperCase() + str.slice(1)
}

// Get style classes for order status
const getOrderStatusClasses = (status) => {
    const classes = {
        'pending': {
            border: 'border-yellow-400',
            badge: 'bg-yellow-100 text-yellow-800'
        },
        'fulfilled': {
            border: 'border-blue-400',
            badge: 'bg-blue-100 text-blue-800'
        },
        'shipping': {
            border: 'border-purple-400',
            badge: 'bg-purple-100 text-purple-800'
        },
        'completed': {
            border: 'border-green-400',
            badge: 'bg-green-100 text-green-800'
        },
        'late': {
            border: 'border-red-400',
            badge: 'bg-red-100 text-red-800'
        },
        'rejected': {
            border: 'border-gray-400',
            badge: 'bg-gray-100 text-gray-800'
        }
    }

    return classes[status] || classes['pending']
}

// Get orders for current tab
const getOrdersForCurrentTab = () => {
    if (activeTab.value === 'pending') {
        return allOrders.value.filter(order => order.status === 'pending' || order.status === 'rejected')
    } else if (activeTab.value === 'fulfilled') {
        return allOrders.value.filter(order => order.status === 'paid') // Changed from 'fulfilled' to 'paid'
    } else if (activeTab.value === 'shipping') {
        return allOrders.value.filter(order => order.status === 'shipping')
    } else if (activeTab.value === 'completed') {
        return allOrders.value.filter(order => order.status === 'completed')
    } else if (activeTab.value === 'late') {
        return allOrders.value.filter(order => order.status === 'late')
    }
    return []
}

// Get order count for each tab
const getOrderCountForTab = (tabId) => {
    if (tabId === 'pending') {
        return allOrders.value.filter(order => order.status === 'pending' || order.status === 'rejected').length
    } else if (tabId === 'fulfilled') {
        return allOrders.value.filter(order => order.status === 'paid').length // Changed from 'open' to 'paid'
    } else if (tabId === 'shipping') {
        return allOrders.value.filter(order => order.status === 'shipping').length
    } else if (tabId === 'completed') {
        return allOrders.value.filter(order => order.status === 'completed').length
    } else if (tabId === 'late') {
        return allOrders.value.filter(order => order.status === 'late').length
    }
    return 0
}

// Get empty state messages
const getEmptyStateMessage = (tabId) => {
    const messages = {
        'pending': 'You don\'t have any pending orders.',
        'fulfilled': 'You don\'t have any fulfilled orders.',
        'shipping': 'You don\'t have any orders in shipping.',
        'completed': 'You don\'t have any completed orders.',
        'late': 'You don\'t have any late orders.'
    }
    return messages[tabId] || 'No orders found.'
}

// Confirm delivery function
const confirmDelivery = async (order) => {
    try {
        const response = await fetch(`${ORDER_RECORDS_URL}/graphql`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Origin': 'http://localhost:80'
            },
            mode: 'cors',
            credentials: 'include',
            body: JSON.stringify({
                query: `
          mutation UpdateOrderStatus($orderID: String!, $status: String!) {
            updateOrderStatus(orderID: $orderID, status: $status) {
              orderID
              status
            }
          }
        `,
                variables: {
                    orderID: order.orderID,
                    status: 'completed'
                }
            })
        })

        const result = await response.json()

        if (result.data && result.data.updateOrderStatus) {
            // Refresh orders after updating status
            await fetchOrders()
            alert('Delivery confirmed successfully.')
        } else {
            throw new Error('Failed to update order status')
        }
    } catch (err) {
        console.error('Error confirming delivery:', err)
        alert(`Failed to confirm delivery: ${err.message}`)
    }
}

// Add this function to handle damage report submission
const submitDamageReport = (order) => {
    // Navigate to the damage report page with the order and product IDs as query parameters
    router.push({
        path: '/damage-report',
        query: { 
            orderID: order.orderID,
            productID: order.productID 
        }
    })
}

// Fetch orders from API
const fetchOrders = async () => {
    loading.value = true
    error.value = null

    try {
        const userId = localStorage.getItem('userId')

        if (!userId) {
            error.value = 'Please log in to view your orders.'
            loading.value = false
            return
        }

        console.log('Fetching orders for userID:', userId)

        const response = await fetch(`${ORDER_RECORDS_URL}/graphql`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Origin': 'http://localhost:80'
            },
            mode: 'cors',
            credentials: 'include',
            body: JSON.stringify({
                query: `
            query GetOrdersByUser($userID: Int!) {
                ordersByUser(userID: $userID) {
                orderID
                paymentAmount
                dailyPayment
                productID
                renterID
                startDate
                endDate
                status
                userID
                }
            }
            `,
                variables: {
                    userID: parseInt(userId)
                }
            })
        })

        const result = await response.json()

        if (result.errors) {
            console.error('GraphQL Errors:', result.errors)
            error.value = result.errors[0].message
        } else if (result.data && result.data.ordersByUser) {
            allOrders.value = result.data.ordersByUser
            console.log('Orders loaded:', allOrders.value)
        } else {
            error.value = 'No order data available'
        }
    } catch (err) {
        console.error('Error fetching orders:', err)
        error.value = err.message
    } finally {
        loading.value = false
    }
}

// Initialize on component mount
onMounted(() => {
    fetchOrders()
})
</script>