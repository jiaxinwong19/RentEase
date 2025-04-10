<template>
    <div class="min-h-screen bg-gray-50 py-8 pt-24">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <!-- User Profile Header - Enhanced version -->
            <div class="bg-white shadow rounded-lg overflow-hidden mb-8">
                <div class="bg-gradient-to-r from-blue-500 to-purple-600 h-32"></div>
                <div class="p-6 sm:p-8 -mt-16">
                    <div class="flex items-end space-x-5">
                        <div class="flex-shrink-0">
                            <div class="relative">
                                <div class="h-24 w-24 rounded-full bg-gray-200 border-4 border-white flex items-center justify-center">
                                    <user-icon class="h-12 w-12 text-gray-500" />
                                </div>
                                <span class="absolute inset-0 rounded-full shadow-inner"></span>
                            </div>
                        </div>
                        <div class="pt-16 sm:flex-1 sm:flex sm:items-center sm:justify-between">
                            <div>
                                <h1 class="text-2xl font-bold text-gray-900">
                                    {{ userData.name }}
                                </h1>
                                <div class="mt-2 flex items-center text-sm text-gray-500">
                                    <svg class="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                        <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                                        <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                                    </svg>
                                    <span>{{ userData.email || 'Email loading...' }}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Add user details section -->
                <div class="px-6 py-5 border-t border-gray-200">
                    <dl class="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                        <div class="sm:col-span-1">
                            <dt class="text-sm font-medium text-gray-500">Name</dt>
                            <dd class="mt-1 text-sm text-gray-900">{{ userData.Name }}</dd>
                        </div>
                        <div class="sm:col-span-1">
                            <dt class="text-sm font-medium text-gray-500">Email address</dt>
                            <dd class="mt-1 text-sm text-gray-900">{{ userData.email || '' }}</dd>
                        </div>
                        <div class="sm:col-span-1" v-if="userData.phoneNo">
                            <dt class="text-sm font-medium text-gray-500">Phone number</dt>
                            <dd class="mt-1 text-sm text-gray-900">{{ userData.phoneNo }}</dd>
                        </div>
                    </dl>
                </div>
            </div>

            <!-- User Score Card -->
            <div class="bg-white shadow rounded-lg overflow-hidden mb-8 p-6">
                <h2 class="text-lg font-medium text-gray-900 mb-4">User Score</h2>
                <div class="flex items-center">
                    <div class="flex-1">
                        <div class="flex items-center">
                            <div class="text-4xl font-bold pr-8" :class="getScoreColorClass(userData.userScore)">
                                {{ userData.userScore || 0 }}
                            </div>
                            <div class="ml-4">
                                <p class="text-sm text-gray-500">Your current user score</p>
                                <p class="text-xs text-gray-400 mt-1">
                                    Scores are calculated based on your rental history and behavior
                                </p>
                            </div>
                        </div>
                    </div>
                    <div class="w-32 h-32 relative">
                        <div class="absolute inset-0 flex items-center justify-center">
                            <div class="text-sm font-medium">Score</div>
                        </div>
                        <svg class="w-full h-full" viewBox="0 0 100 100">
                            <circle cx="50" cy="50" r="45" fill="none" stroke="#e5e7eb" stroke-width="8" />
                            <circle cx="50" cy="50" r="45" fill="none" :stroke="getScoreColor(userData.userScore)"
                                stroke-width="8" :stroke-dasharray="`${userData.userScore * 2.83} 283`"
                                stroke-dashoffset="0" transform="rotate(-90 50 50)" />
                        </svg>
                    </div>
                </div>
            </div>

            <!-- Order History Tabs -->
            <div class="bg-white shadow rounded-lg overflow-hidden">
                <div class="border-b border-gray-200">
                    <nav class="flex">
                        <button v-for="tab in orderTabs" :key="tab.id" @click="activeOrderTab = tab.id" :class="[
                            activeOrderTab === tab.id
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                            'flex-1 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm text-center'
                        ]">
                            {{ tab.name }}
                        </button>
                    </nav>
                </div>

                <!-- Orders I Rented Tab -->
                <div v-if="activeOrderTab === 'rented'" class="p-6">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">Orders I Rented</h3>
                    <div v-if="loading" class="flex justify-center py-12">
                        <svg class="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none"
                            viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4">
                            </circle>
                            <path class="opacity-75" fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
                            </path>
                        </svg>
                    </div>
                    <div v-else-if="ordersIRented.length === 0" class="text-center py-8">
                        <package-icon class="h-12 w-12 text-gray-400 mx-auto" />
                        <h3 class="mt-2 text-sm font-medium text-gray-900">No orders</h3>
                        <p class="mt-1 text-sm text-gray-500">You haven't rented any items yet.</p>
                    </div>
                    <div v-else class="space-y-4">
                        <div v-for="order in ordersIRented" :key="order.orderID" class="border rounded-lg p-4">
                            <div class="flex justify-between">
                                <div>
                                    <h4 class="font-medium">Order #{{ order.orderID }}</h4>
                                    <p class="text-sm text-gray-500">Product ID: {{ order.productID }}</p>
                                    <p class="text-sm text-gray-500">Rental Period: {{ formatDate(order.startDate) }} -
                                        {{ formatDate(order.endDate) }}</p>
                                    <p class="text-sm text-gray-500">Total: ${{ order.paymentAmount }}</p>
                                </div>
                                <div>
                                    <span :class="[
                                        getOrderStatusClasses(order.status).badge,
                                        'px-2 py-1 text-xs font-medium rounded-full'
                                    ]">
                                        {{ capitalizeFirst(order.status) }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Orders I Rented Out Tab -->
                <div v-if="activeOrderTab === 'rentedOut'" class="p-6">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">Orders I Rented Out</h3>
                    <div v-if="loading" class="flex justify-center py-12">
                        <svg class="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none"
                            viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4">
                            </circle>
                            <path class="opacity-75" fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
                            </path>
                        </svg>
                    </div>
                    <div v-else-if="ordersIRentedOut.length === 0" class="text-center py-8">
                        <package-icon class="h-12 w-12 text-gray-400 mx-auto" />
                        <h3 class="mt-2 text-sm font-medium text-gray-900">No orders</h3>
                        <p class="mt-1 text-sm text-gray-500">You haven't rented out any items yet.</p>
                    </div>
                    <div v-else class="space-y-4">
                        <div v-for="order in ordersIRentedOut" :key="order.orderID" class="border rounded-lg p-4">
                            <div class="flex justify-between">
                                <div>
                                    <h4 class="font-medium">Order #{{ order.orderID }}</h4>
                                    <p class="text-sm text-gray-500">Product ID: {{ order.productID }}</p>
                                    <p class="text-sm text-gray-500">Rental Period: {{ formatDate(order.startDate) }} -
                                        {{ formatDate(order.endDate) }}</p>
                                    <p class="text-sm text-gray-500">Total: ${{ order.paymentAmount }}</p>
                                </div>
                                <div>
                                    <span :class="[
                                        getOrderStatusClasses(order.status).badge,
                                        'px-2 py-1 text-xs font-medium rounded-full'
                                    ]">
                                        {{ capitalizeFirst(order.status) }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { PackageIcon, UserIcon } from 'lucide-vue-next'

// State
const userData = ref({})
const ordersIRented = ref([])
const ordersIRentedOut = ref([])
const loading = ref(false)
const error = ref(null)

// Tabs
const activeOrderTab = ref('rented')
const orderTabs = [
    { id: 'rented', name: 'Orders I Rented' },
    { id: 'rentedOut', name: 'Orders I Rented Out' }
]

// Format date
const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    })
}

// Capitalize first letter
const capitalizeFirst = (str) => {
    if (!str) return ''
    return str.charAt(0).toUpperCase() + str.slice(1)
}

// Get order status classes
const getOrderStatusClasses = (status) => {
    const classes = {
        'pending': {
            border: 'border-yellow-400',
            badge: 'bg-yellow-100 text-yellow-800'
        },
        'paid': {
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

// Get score color class
const getScoreColorClass = (score) => {
    if (!score) return 'text-gray-500'
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-blue-600'
    if (score >= 40) return 'text-yellow-600'
    if (score >= 20) return 'text-orange-600'
    return 'text-red-600'
}

// Get score color for SVG
const getScoreColor = (score) => {
    if (!score) return '#9ca3af'
    if (score >= 80) return '#16a34a'
    if (score >= 60) return '#2563eb'
    if (score >= 40) return '#ca8a04'
    if (score >= 20) return '#ea580c'
    return '#dc2626'
}

// Constants
const ORDER_RECORDS_URL = '/order-records'

// Fetch user data
const fetchUserData = async () => {
    const userId = localStorage.getItem('userId')

    if (!userId) {
        console.error('No user ID found')
        return
    }

    try {
        console.log('Fetching user data for ID:', userId)
        const response = await fetch(`https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getUserInfo?id=${userId}`)

        if (!response.ok) {
            throw new Error(`Failed to fetch user data: ${response.status}`)
        }

        const data = await response.json()
        console.log('User data received:', data)
        
        // Check if data is in expected format
        userData.value = {
            username: data.details.username,
            name: data.details.name,
            email: data.details.email,
            userScore: data.details.userScore,
            phoneNo: data.details.phoneNo,
        }

        // If user score is not included in user data, fetch it separately
        if (userData.value.userScore === undefined) {
            await fetchUserScore(userId)
        }
    } catch (error) {
        console.error('Error fetching user data:', error)
    }
}

// Fetch user score if not included in user data
const fetchUserScore = async (userId) => {
    try {
        const response = await fetch(`https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getUserScore/?id=${userId}`)

        if (!response.ok) {
            throw new Error('Failed to fetch user score')
        }

        const data = await response.json()
        userData.value.userScore = data.userScore || 0
    } catch (error) {
        console.error('Error fetching user score:', error)
    }
}

// Fetch orders where user is the renter
const fetchOrdersAsRenter = async () => {
    const userId = localStorage.getItem('userId')
    if (!userId) return
    
    try {
        console.log('Fetching orders as renter for userId:', userId)
        const response = await fetch(`${ORDER_RECORDS_URL}/graphql`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                query: `
                    query GetOrdersByRenter($renterID: Int!) {
                        ordersByRenter(renterID: $renterID) {
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
                    renterID: parseInt(userId)
                }
            })
        })

        const result = await response.json()
        console.log('Orders as renter response:', result)

        if (result.errors) {
            console.error('GraphQL errors:', result.errors)
            throw new Error(result.errors[0].message)
        } else if (result.data && result.data.ordersByRenter) {
            ordersIRentedOut.value = result.data.ordersByRenter
            console.log('Orders as renter loaded:', ordersIRentedOut.value)
        } else {
            console.warn('No orders as renter found or unexpected response structure')
        }
    } catch (error) {
        console.error('Error fetching orders as renter:', error)
    }
}

// Fetch orders where user is the customer
const fetchOrdersAsCustomer = async () => {
    const userId = localStorage.getItem('userId')
    if (!userId) return
    
    try {
        console.log('Fetching orders as customer for userId:', userId)
        const response = await fetch(`${ORDER_RECORDS_URL}/graphql`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Origin': 'http://localhost:80'
            },
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
        console.log('Orders as customer response:', result)

        if (result.errors) {
            console.error('GraphQL errors:', result.errors)
            throw new Error(result.errors[0].message)
        } else if (result.data && result.data.ordersByUser) {
            ordersIRented.value = result.data.ordersByUser
            console.log('Orders as customer loaded:', ordersIRented.value)
        } else {
            console.warn('No orders as customer found or unexpected response structure')
        }
    } catch (error) {
        console.error('Error fetching orders as customer:', error)
    }
}

// Fetch all data
const fetchAllData = async () => {
    loading.value = true
    try {
        await fetchUserData()
        await Promise.all([
            fetchOrdersAsRenter(),
            fetchOrdersAsCustomer()
        ])
    } catch (err) {
        error.value = err.message
    } finally {
        loading.value = false
    }
}

// Initialize on component mount
onMounted(() => {
    fetchAllData()
})
</script>