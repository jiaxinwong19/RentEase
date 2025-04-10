<template>
  <div class="min-h-screen bg-gray-50 py-8 pt-24">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-8">Orders</h1>

      <!-- Tabs -->
      <div class="border-b border-gray-200 mb-8">
        <nav class="-mb-px flex space-x-8">
          <button
            @click="activeTab = 'pending'"
            :class="[
              activeTab === 'pending'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
            ]"
          >
            Pending Orders
          </button>
          <button
            @click="activeTab = 'fulfilled'"
            :class="[
              activeTab === 'fulfilled'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
            ]"
          >
            Fulfilled Orders
          </button>
          <button
            @click="activeTab = 'completed'"
            :class="[
              activeTab === 'completed'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
            ]"
          >
            Shipping Orders
          </button>
        </nav>
      </div>

      <!-- Pending Orders Section -->
      <div v-if="activeTab === 'pending'">
        <div v-if="pendingOrders.length === 0" class="text-gray-500 text-center py-8 bg-white rounded-lg shadow">
          No pending orders
        </div>
        <div v-else class="grid gap-4">
          <div v-for="order in pendingOrders" :key="order.orderID" 
               class="bg-white shadow rounded-lg p-6 border-l-4 border-yellow-400">
            <div class="flex justify-between items-start">
              <div>
                <h3 class="text-lg font-medium text-gray-900">Order #{{ order.orderID }}</h3>
                <p class="mt-1 text-sm text-gray-500">Product ID: {{ order.productID }}</p>
                <p class="mt-1 text-sm text-gray-500">
                  Rental Period: {{ formatDate(order.startDate) }} - {{ formatDate(order.endDate) }}
                </p>
                <p class="mt-1 text-sm text-gray-500">Total Amount: ${{ order.paymentAmount }}</p>
                <p class="mt-1 text-sm text-gray-500">Daily Rate: ${{ order.dailyPayment }}</p>
                <p class="mt-1 text-sm" :class="getScoreColorClass(userScores[order.userID])">
                  User Score: {{ userScores[order.userID] || 0 }}
                </p>
              </div>
              <div class="flex flex-col items-end space-y-2">
                <span class="px-3 py-1 text-sm font-medium bg-yellow-100 text-yellow-800 rounded-full">
                  Pending
                </span>
                <div class="flex space-x-2">
                  <button
                    @click="acceptOrder(order)"
                    class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  >
                    Accept Order
                  </button>
                  <button
                    @click="openRejectModal(order)"
                    class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                  >
                    Reject Order
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Rejection Modal -->
      <div v-if="showRejectModal" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center">
        <div class="bg-white rounded-lg p-6 max-w-md w-full">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Reject Order</h3>
          <p class="text-sm text-gray-500 mb-4">Please provide a reason for rejecting this order.</p>
          <textarea
            v-model="rejectionReason"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            rows="4"
            placeholder="Enter rejection reason..."
          ></textarea>
          <div class="mt-4 flex justify-end space-x-3">
            <button
              @click="closeRejectModal"
              class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            >
              Cancel
            </button>
            <button
              @click="rejectOrder"
              class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
            >
              Confirm Rejection
            </button>
          </div>
        </div>
      </div>

      <!-- Fulfilled Orders Section -->
      <div v-if="activeTab === 'fulfilled'">
        <div v-if="fulfilledOrders.length === 0" class="text-gray-500 text-center py-8 bg-white rounded-lg shadow">
          No paid orders
        </div>
        <div v-else class="grid gap-4">
          <div v-for="order in fulfilledOrders" :key="order.orderID" 
               class="bg-white shadow rounded-lg p-6 border-l-4" 
               :class="{
                 'border-green-400': order.status === 'paid',
                 'border-blue-400': order.status === 'shipping',
                 'border-purple-400': order.status === 'packed'
               }">
            <div class="flex justify-between items-start">
              <div>
                <h3 class="text-lg font-medium text-gray-900">Order #{{ order.orderID }}</h3>
                <p class="mt-1 text-sm text-gray-500">Product ID: {{ order.productID }}</p>
                <p class="mt-1 text-sm text-gray-500">
                  Rental Period: {{ formatDate(order.startDate) }} - {{ formatDate(order.endDate) }}
                </p>
                <p class="mt-1 text-sm text-gray-500">Total Amount: ${{ order.paymentAmount }}</p>
                <p class="mt-1 text-sm text-gray-500">Daily Rate: ${{ order.dailyPayment }}</p>
                <div v-if="order.trackingNumber" class="mt-2">
                  <p class="text-sm font-medium text-gray-700">Tracking Number:</p>
                  <p class="text-sm text-blue-600">{{ order.trackingNumber }}</p>
                </div>
              </div>
              <div class="flex flex-col items-end">
                <span class="px-3 py-1 text-sm font-medium rounded-full mb-2"
                      :class="{
                        'bg-green-100 text-green-800': order.status === 'paid',
                        'bg-blue-100 text-blue-800': order.status === 'shipping',
                        'bg-purple-100 text-purple-800': order.status === 'packed'
                      }">
                  {{ order.status.charAt(0).toUpperCase() + order.status.slice(1) }}
                </span>
                <div class="space-y-2">
                  <!-- Get Airway Bill button - only show if paid and no airway bill yet -->
                  <button
                    v-if="order.status === 'paid' && !order.airwayBillUrl"
                    @click="getAirwayBill(order)"
                    class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  >
                    Get Airway Bill
                  </button>

                  <!-- Mark as Packed button - only show if has airway bill and status is paid -->
                  <button
                    v-if="order.airwayBillUrl && order.status === 'paid'"
                    @click="markAsPacked(order)"
                    class="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                  >
                    Mark as Packed & Dropped Off
                  </button>

                  <!-- View Airway Bill button - show if airway bill exists -->
                  <button
                    v-if="order.airwayBillUrl"
                    @click="viewAirwayBill(order)"
                    class="w-full px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                  >
                    View Airway Bill
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Completed Orders Section -->
      <div v-if="activeTab === 'completed'">
        <div v-if="completedOrders.length === 0" class="text-gray-500 text-center py-8 bg-white rounded-lg shadow">
          No shipping orders
        </div>
        <div v-else class="grid gap-4">
          <div v-for="order in completedOrders" :key="order.orderID" 
               class="bg-white shadow rounded-lg p-6 border-l-4 border-blue-400">
            <div class="flex justify-between items-start">
              <div>
                <h3 class="text-lg font-medium text-gray-900">Order #{{ order.orderID }}</h3>
                <p class="mt-1 text-sm text-gray-500">Product ID: {{ order.productID }}</p>
                <p class="mt-1 text-sm text-gray-500">
                  Rental Period: {{ formatDate(order.startDate) }} - {{ formatDate(order.endDate) }}
                </p>
                <p class="mt-1 text-sm text-gray-500">Total Amount: ${{ order.paymentAmount }}</p>
                <p class="mt-1 text-sm text-gray-500">Daily Rate: ${{ order.dailyPayment }}</p>
                <div v-if="order.trackingNumber" class="mt-2">
                  <p class="text-sm font-medium text-gray-700">Tracking Number:</p>
                  <p class="text-sm text-blue-600">{{ order.trackingNumber }}</p>
                </div>
              </div>
              <div class="flex flex-col items-end">
                <span class="px-3 py-1 text-sm font-medium bg-blue-100 text-blue-800 rounded-full mb-2">
                  Shipping
                </span>
                <button
                  v-if="order.airwayBillUrl"
                  @click="viewAirwayBill(order)"
                  class="w-full px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  View Airway Bill
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
import { ref, onMounted } from 'vue'

const activeTab = ref('pending')
const pendingOrders = ref([])
const fulfilledOrders = ref([])
const completedOrders = ref([])
const userScores = ref({})
const showRejectModal = ref(false)
const rejectionReason = ref('')
const selectedOrder = ref(null)

// Add API base URLs as constants
const ORDER_RECORDS_URL = '/order-records'
const ORDER_COMPOSITE_URL = 'http://localhost:5001'
const SHIPPING_URL = 'http://localhost:5009'

// Format date function
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// Fetch user score
const fetchUserScore = async (userId) => {
  try {
    console.log('Fetching score for user:', userId)
    const response = await fetch(`https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getUserScore/?id=${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    })
    const result = await response.json()
    console.log('User score result:', result)
    return result.userScore || 0
  } catch (error) {
    console.error(`Error fetching user score for user ${userId}:`, error)
    return 0
  }
}

// Fetch orders from the GraphQL endpoint
const fetchOrders = async () => {
  try {
    const userId = localStorage.getItem('userId')
    console.log('Current user ID:', userId)
    
    if (!userId) {
      console.error('No user ID found')
      return
    }

    console.log('Fetching orders for renterID:', parseInt(userId))

    // First, fetch orders
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
    console.log("Raw GraphQL response:", result)

    if (result.errors) {
      console.error("GraphQL Errors:", result.errors)
      return
    }

    if (result.data && result.data.ordersByRenter) {
      const userOrders = result.data.ordersByRenter
      console.log("All orders received:", userOrders)
      
      // Debug each order's status and renterID
      userOrders.forEach(order => {
        console.log(`Order ${order.orderID}:
          - Status: "${order.status}"
          - RenterID: ${order.renterID}
          - UserID: ${order.userID}
          - Type of status: ${typeof order.status}
        `)
      })
      
      // Separate orders into three categories
      const pending = userOrders.filter(order => {
        const isPending = order.status === 'pending'
        console.log(`Order ${order.orderID} - Is Pending? ${isPending}`)
        return isPending
      })
      
      const fulfilled = userOrders.filter(order => {
        const isFulfilled = ['paid', 'accepted'].includes(order.status)
        console.log(`Order ${order.orderID} - Is Fulfilled? ${isFulfilled}`)
        return isFulfilled
      })
      
      const completed = userOrders.filter(order => {
        const isShipping = order.status === 'shipping'
        console.log(`Order ${order.orderID} - Is Shipping? ${isShipping}`)
        return isShipping
      })
      
      console.log("Filtered pending orders:", pending.length, pending)
      console.log("Filtered fulfilled orders:", fulfilled.length, fulfilled)
      console.log("Filtered completed orders:", completed.length, completed)

      // For pending orders only, fetch user scores
      for (const order of pending) {
        if (order.userID) {
          const score = await fetchUserScore(order.userID)
          userScores.value[order.userID] = score
        }
      }

      // Update the reactive refs
      pendingOrders.value = pending
      fulfilledOrders.value = fulfilled
      completedOrders.value = completed

      console.log("Final state - Pending orders:", pendingOrders.value)
      console.log("Final state - Fulfilled orders:", fulfilledOrders.value)
      console.log("Final state - Completed orders:", completedOrders.value)
    } else {
      console.error("No ordersByRenter data in response:", result)
    }
  } catch (error) {
    console.error('Error fetching orders:', error)
  }
}

// Accept order function
const acceptOrder = async (order) => {
  try {
    console.log('Accepting order:', order)
    
    // First, update the order status
    const statusResponse = await fetch(`${ORDER_RECORDS_URL}/graphql`, {
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
          status: 'paid'
        }
      })
    })

    if (!statusResponse.ok) {
      const errorData = await statusResponse.json()
      throw new Error(errorData.error || `Failed to update order status: ${statusResponse.status}`)
    }

    const statusResult = await statusResponse.json()
    console.log("Update status result:", statusResult)

    if (statusResult.data && statusResult.data.updateOrderStatus) {
      // Then, send confirmation to order composite
      console.log('Sending confirmation for order:', order.orderID)
      try {
        const confirmResponse = await fetch(`${ORDER_COMPOSITE_URL}/order_com/confirm/${order.orderID}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'http://localhost:80'
          },
          mode: 'cors',
          credentials: 'include'
        })

        if (!confirmResponse.ok) {
          const errorData = await confirmResponse.json()
          throw new Error(errorData.error || `Failed to confirm order: ${confirmResponse.status}`)
        }

        const confirmResult = await confirmResponse.json()
        console.log("Confirmation result:", confirmResult)

        // Add a small delay before fetching orders
        await new Promise(resolve => setTimeout(resolve, 1000))
        // Refresh orders after both operations are successful
        await fetchOrders()
        // Switch to fulfilled tab
        activeTab.value = 'fulfilled'
      } catch (confirmError) {
        console.error('Error confirming order:', confirmError)
        alert(`Failed to confirm order: ${confirmError.message}`)
      }
    } else {
      throw new Error('Failed to update order status: Invalid response')
    }
  } catch (error) {
    console.error('Error accepting order:', error)
    alert(`Error accepting order: ${error.message}`)
  }
}

// Get airway bill function
const getAirwayBill = async (order) => {
  try {
    console.log("Getting airway bill for order:", order.orderID)
    
    // First get all shipping info
    const infoResponse = await fetch(`${SHIPPING_URL}/shipping/${order.orderID}/label`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      mode: 'cors',
      credentials: 'include'
    })


    if (!infoResponse.ok) {
      const errorData = await infoResponse.json()
      throw new Error(errorData.error || 'Failed to get shipping information')
    }

    const shippingInfo = await infoResponse.json()
    console.log("Shipping info:", shippingInfo)

    if (!shippingInfo || !shippingInfo.label_url) {
      throw new Error('Shipping label not yet generated. Please try again in a few moments.')
    }

    // Update the order with shipping information but DO NOT update the status
    order.airwayBillUrl = shippingInfo.label_url
    order.trackingNumber = shippingInfo.tracking_number

    // Open the airway bill in a new tab
    window.open(shippingInfo.label_url, '_blank')
    
    return true
  } catch (error) {
    console.error('Error getting airway bill:', error.message)
    alert(`Failed to get airway bill: ${error.message}\n\nPlease try again in a few moments.`)
    return false
  }
}

// View existing airway bill
const viewAirwayBill = (order) => {
  if (order.airwayBillUrl) {
    window.open(order.airwayBillUrl, '_blank')
  }
}

// Helper function to update order status
const updateOrderStatus = async (orderID, status) => {
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
        mutation UpdateOrderStatus($orderID: String!, $status: String!) {
          updateOrderStatus(orderID: $orderID, status: $status) {
            orderID
            status
          }
        }
      `,
      variables: {
        orderID: orderID,
        status: status
      }
    })
  })
  return response.json()
}

// Mark as packed function
const markAsPacked = async (order) => {
  try {
    // Update the order status to shipping
    const result = await updateOrderStatus(order.orderID, 'shipping')
    console.log("Mark as shipping result:", result)

    if (result.data && result.data.updateOrderStatus) {
      // After marking as shipping, notify shipping service
      console.log("Notifying shipping service for order:", order.orderID)
      const notifyResponse = await fetch(`${ORDER_COMPOSITE_URL}/order_com/notify-shipping/${order.orderID}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Origin': 'http://localhost:80'
        },
        mode: 'cors',
        credentials: 'include'
      })

      if (!notifyResponse.ok) {
        const errorData = await notifyResponse.json()
        throw new Error(errorData.error || 'Failed to notify shipping service')
      }

      // Refresh orders to update status
      await fetchOrders()
      
      // Switch to the completed (shipping) tab
      activeTab.value = 'completed'
    }
  } catch (error) {
    console.error('Error marking order as shipped:', error)
    alert(`Error: ${error.message}\nPlease try again.`)
  }
}

// Add helper function for score colors
const getScoreColorClass = (score) => {
  if (score === undefined || score === null) return 'text-gray-500'
  if (score >= 4) return 'text-green-600 font-semibold'
  if (score >= 3) return 'text-blue-600 font-semibold'
  if (score >= 2) return 'text-yellow-600 font-semibold'
  return 'text-red-600 font-semibold'
}

const openRejectModal = (order) => {
  selectedOrder.value = order
  showRejectModal.value = true
}

const closeRejectModal = () => {
  showRejectModal.value = false
  rejectionReason.value = ''
  selectedOrder.value = null
}

const rejectOrder = async () => {
  if (!rejectionReason.value.trim()) {
    alert('Please provide a reason for rejection')
    return
  }

  try {
    console.log('Starting rejection process for order:', selectedOrder.value)
    
    // First, update the order status to rejected
    const statusResponse = await fetch(`${ORDER_RECORDS_URL}/graphql`, {
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
          orderID: selectedOrder.value.orderID,
          status: 'rejected'
        }
      })
    })

    if (!statusResponse.ok) {
      throw new Error('Failed to update order status')
    }
    
    // Get the full order details including userID
    console.log('Fetching complete order details')
    const orderResponse = await fetch(`${ORDER_RECORDS_URL}/graphql`, {
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
          query GetOrder($orderID: String!) {
            order(orderID: $orderID) {
              orderID
              userID
              productID
            }
          }
        `,
        variables: {
          orderID: selectedOrder.value.orderID
        }
      })
    })
    
    const orderData = await orderResponse.json()
    console.log('Order details:', orderData)
    
    if (!orderData.data || !orderData.data.order) {
      throw new Error('Failed to fetch order details')
    }
    
    const userID = orderData.data.order.userID
    const productID = orderData.data.order.productID
    console.log(productID)
    
    // Fetch user email from user service
    console.log('Fetching user email for userID:', userID)
    const userResponse = await fetch(`https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getEmail/?id=${userID}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (!userResponse.ok) {
      throw new Error('Failed to fetch user data')
    }
    
    const userData = await userResponse.json()
    console.log('User data:', userData)
    
    if (!userData || !userData.email) {
      throw new Error('User email not found')
    }
    
    // Use a simple product name based on productID
    const productName = `Product #${productID}`
    
    // Send rejection notification
    console.log('Sending rejection notification with email:', userData.email)
    const notificationResponse = await fetch('http://localhost:5010/notification/order/reject', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        orderID: selectedOrder.value.orderID,
        userEmail: userData.email,
        productName: productName,
        rejectionReason: rejectionReason.value
      })
    })

    if (!notificationResponse.ok) {
      console.error('Failed to send notification:', await notificationResponse.text())
      throw new Error('Failed to send rejection notification')
    }

    // Refresh orders and close modal
    await fetchOrders()
    closeRejectModal()
    alert('Order rejected successfully and notification sent.')
  } catch (error) {
    console.error('Error rejecting order:', error)
    alert(`Failed to reject order: ${error.message}. Please try again.`)
  }
}

// Fetch orders when component mounts
onMounted(() => {
  fetchOrders()
})
</script>