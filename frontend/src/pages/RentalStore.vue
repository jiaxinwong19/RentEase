<template>
    <div class="min-h-screen bg-gray-50">
        <!-- Toaster Notification -->
        <div v-if="showToaster" 
            class="fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 transform transition-all duration-500"
            :class="{ 'translate-x-0': showToaster, 'translate-x-full': !showToaster }">
            {{ toasterMessage }}
        </div>

        <!-- Main Content -->
        <main class="container mx-auto px-4 py-8 pt-20 max-w-7xl">
            <!-- Hero Section -->
            <div class="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-8 mb-8 text-white">
                <h2 class="text-3xl font-bold mb-2">Find the Perfect Rental</h2>
                <p class="mb-4 max-w-lg">Browse our wide selection of high-quality rental items for any occasion.</p>
                <div class="relative max-w-md">
                    <search-icon class="absolute left-5 top-3 h-5 w-5 text-gray-400" />
                    <input v-model="searchQuery" type="text" placeholder="Search for items..."
                        class="w-full pl-10 pr-4 py-2 rounded-lg text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-300" />
                </div>
            </div>

            <!-- Filters and Products -->
            <div class="flex flex-col md:flex-row gap-8">
                <!-- Products Grid -->
                <div class="flex-1">
                    <!-- Sort Options -->
                    <div class="flex justify-between items-center mb-6">
                        <p class="text-gray-600">{{ filteredProducts.length }} items found</p>
                        <select v-model="sortOption"
                            class="border rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-300">
                            <option value="recommended">Recommended</option>
                            <option value="price-asc">Price: Low to High</option>
                            <option value="price-desc">Price: High to Low</option>
                            <option value="newest">Newest First</option>
                        </select>
                    </div>

                    <!-- Products -->
                    <div v-if="filteredProducts.length > 0" class="grid grid-cols-2 md:grid-cols-2 gap-8">
                        <div v-for="product in filteredProducts" :key="product.productID"
                            class="bg-white rounded-lg overflow-hidden shadow hover:shadow-md transition">
                            <div class="relative h-64 bg-gray-200">
                                <img :src="product.originalImageUrl" :alt="product.productName"
                                    class="w-full h-full object-cover" />
                                <span v-if="!product.availability"
                                    class="absolute top-2 right-2 bg-red-500 text-white text-xs px-2 py-1 rounded">
                                    Unavailable
                                </span>
                            </div>
                            <div class="p-4">
                                <div class="flex justify-between items-start">
                                    <h3 class="font-medium text-lg">{{ product.productName }}</h3>
                                    <span class="font-bold text-blue-600">${{ product.price }}/day</span>
                                </div>
                                <p class="mt-2 text-sm text-gray-500 line-clamp-2">{{ product.productDesc }}</p>
                                <div class="mt-4 flex justify-between items-center">
                                    <button class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                                        @click="showProductDetails(product)">
                                        View Details
                                    </button>
                                    <button :disabled="!product.availability" :class="[
                                        'px-3 py-1.5 rounded text-sm font-medium',
                                        product.availability
                                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                                            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                    ]" @click="showRentalDetails(product)">
                                        Rent
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Empty State -->
                    <div v-else class="bg-white rounded-lg p-8 text-center">
                        <package-x-icon class="h-12 w-12 mx-auto text-gray-400" />
                        <h3 class="mt-4 text-lg font-medium">No products found</h3>
                        <p class="mt-2 text-gray-500">Try adjusting your search query</p>
                    </div>
                </div>
            </div>
        </main>

        <!-- Product Details Modal -->
        <div v-if="selectedProduct"
            class="fixed inset-0 bg-white/30 backdrop-blur-md flex items-center justify-center p-4 z-50">
            <div class="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto shadow-2xl">
                <div class="p-8">
                    <div class="flex justify-between items-start mb-6">
                        <h2 class="text-3xl font-bold text-gray-800">{{ selectedProduct.productName }}</h2>
                        <button @click="selectedProduct = null" class="text-gray-500 hover:text-gray-700">
                            <x-icon class="h-8 w-8" />
                        </button>
                    </div>
                    <div class="flex flex-col md:flex-row gap-8">
                        <div class="w-full md:w-1/2 h-96 overflow-hidden rounded-lg shadow-lg">
                            <img :src="selectedProduct.originalImageUrl" :alt="selectedProduct.productName"
                                class="w-full h-full object-cover" />
                        </div>
                        <div class="flex-1">
                            <div class="flex justify-between items-center mb-6">
                                <span class="text-2xl font-bold text-blue-600">${{ selectedProduct.price }}/day</span>
                                <span :class="[
                                    'px-3 py-1.5 rounded-full text-sm font-medium',
                                    selectedProduct.availability ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                ]">
                                    {{ selectedProduct.availability ? 'Available' : 'Unavailable' }}
                                </span>
                            </div>
                            <p class="text-gray-700 text-lg mb-6">{{ selectedProduct.productDesc }}</p>
                            <div class="space-y-4 mb-8">
                                <div class="flex items-center">
                                    <span class="w-32 text-gray-500 text-lg">Status:</span>
                                    <span class="text-lg">{{ selectedProduct.availability ? 'Available' : 'Unavailable' }}</span>
                                </div>
                            </div>
                            <button :disabled="!selectedProduct.availability" :class="[
                                'w-full py-3 rounded-lg font-medium text-lg',
                                selectedProduct.availability
                                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            ]" @click="showRentalDetails(selectedProduct)">
                                {{ selectedProduct.availability ? 'Rent' : 'Currently Unavailable' }}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Rental Details Modal -->
        <div v-if="showRentalModal" class="fixed inset-0 bg-white/30 backdrop-blur-md flex items-center justify-center p-4 z-50">
            <div class="bg-white rounded-lg max-w-4xl w-full shadow-2xl">
                <div class="p-8">
                    <div class="flex justify-between items-start mb-6">
                        <h2 class="text-2xl font-bold text-gray-800">Rental Details</h2>
                        <button @click="showRentalModal = false" class="text-gray-500 hover:text-gray-700">
                            <x-icon class="h-6 w-6" />
                        </button>
                    </div>
                    
                    <div class="space-y-6">
                        <!-- Product Info -->
                        <div class="flex items-center gap-4">
                            <img :src="rentalProduct.originalImageUrl" :alt="rentalProduct.productName" class="w-24 h-24 object-cover rounded-lg" />
                            <div>
                                <h3 class="font-medium text-lg">{{ rentalProduct.productName }}</h3>
                                <p class="text-blue-600 font-bold">${{ rentalProduct.price }}/day</p>
                            </div>
                        </div>

                        <!-- Dates -->
                        <div class="grid grid-cols-2 gap-6">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
                                <input type="date" v-model="startDate" 
                                    :min="getMinStartDate"
                                    class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-300" />
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">End Date</label>
                                <input type="date" v-model="endDate"
                                    :min="startDate"
                                    class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-300" />
                            </div>
                        </div>

                        <!-- Total Price -->
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <div class="flex justify-between items-center">
                                <span class="text-gray-600">Total Price:</span>
                                <span class="text-2xl font-bold text-blue-600">${{ calculateRentalTotal }}</span>
                            </div>
                        </div>

                        <!-- Add to Cart Button -->
                        <button @click="addToCart" 
                            class="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">
                            Rent
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { SearchIcon, XIcon, PackageXIcon } from 'lucide-vue-next'

const products = ref([])
const searchQuery = ref('')
const sortOption = ref('recommended')
const selectedProduct = ref(null)
const showRentalModal = ref(false)
const rentalProduct = ref(null)
const startDate = ref('')
const endDate = ref('')
const showToaster = ref(false)
const toasterMessage = ref('')

// Fetch products from API
const fetchProducts = async () => {
    try {
        const response = await fetch("http://localhost:5020/inventory/products", {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            console.error('Server response:', response.status, response.statusText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Products fetched successfully:', data);
        // Log the first product's complete structure
        if (data.length > 0) {
            console.log('First product complete data:', data[0]);
            console.log('Available fields:', Object.keys(data[0]));
        }
        products.value = data;
    } catch (error) {
        console.error('Error details:', {
            message: error.message,
            name: error.name,
            stack: error.stack
        });
    }
}

onMounted(fetchProducts)

// Computed property to filter and sort products
const filteredProducts = computed(() => {
    return products.value
        .filter(product =>
            (!searchQuery.value || product.productName.toLowerCase().includes(searchQuery.value.toLowerCase()))
        )
        .sort((a, b) => {
            if (sortOption.value === 'price-asc') return a.price - b.price
            if (sortOption.value === 'price-desc') return b.price - a.price
            if (sortOption.value === 'newest') return new Date(b.dateAdded) - new Date(a.dateAdded)
            return 0 // Default: recommended (no sorting)
        })
})

// Function to show product details
const showProductDetails = (product) => {
    selectedProduct.value = product
}

// Calculate minimum start date (4 days from today)
const getMinStartDate = computed(() => {
    const date = new Date()
    date.setDate(date.getDate() + 4)
    return date.toISOString().split('T')[0]
})

// Function to show rental details
const showRentalDetails = (product) => {
    rentalProduct.value = product
    // Set default dates (4 days from today for start, 7 days after start for end)
    const defaultStartDate = new Date()
    defaultStartDate.setDate(defaultStartDate.getDate() + 4)
    startDate.value = defaultStartDate.toISOString().split('T')[0]
    
    const defaultEndDate = new Date(defaultStartDate)
    defaultEndDate.setDate(defaultEndDate.getDate() + 7)
    endDate.value = defaultEndDate.toISOString().split('T')[0]
    
    showRentalModal.value = true
}

// Calculate rental total
const calculateRentalTotal = computed(() => {
    if (!startDate.value || !endDate.value) return 0
    const start = new Date(startDate.value)
    const end = new Date(endDate.value)
    const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24))
    return (days * rentalProduct.value.price).toFixed(2)
})

// Add to cart
const addToCart = async () => {
    try {
        // Get the user ID from localStorage
        const userId = localStorage.getItem('userId')
        if (!userId) {
            console.error('User not authenticated')
            return
        }

        // Calculate total price based on duration
        const start = new Date(startDate.value)
        const end = new Date(endDate.value)
        const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24))
        const totalPrice = days * rentalProduct.value.price

        // Log the complete rental product data
        console.log('Rental Product Complete Data:', rentalProduct.value)
        console.log('Available fields:', Object.keys(rentalProduct.value))

        // Prepare the order data with correct field names
        const orderData = {
            price: totalPrice, // Total price for the entire rental period
            renterID: rentalProduct.value.userID, // Try all possible field names
            productId: rentalProduct.value.productID,
            prodDesc: rentalProduct.value.productDesc,
            startDate: startDate.value,
            endDate: endDate.value,
            userID: userId,
        }

        // Log the order data before sending
        console.log('Order Data:', orderData)

        // Make the POST request to the order microservice
        const response = await fetch('http://localhost:5001/order_com/orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        console.log('Order created successfully:', data)
        
        // Show success toaster
        toasterMessage.value = 'Order sent to renter for verification'
        showToaster.value = true
        
        // Hide toaster after 3 seconds
        setTimeout(() => {
            showToaster.value = false
        }, 3000)
        
        // Close modal and reset form
        showRentalModal.value = false
        selectedProduct.value = null
        startDate.value = ''
        endDate.value = ''
    } catch (error) {
        console.error('Failed to create order:', error)
        // Show error toaster
        toasterMessage.value = 'Failed to create order. Please try again.'
        showToaster.value = true
        setTimeout(() => {
            showToaster.value = false
        }, 3000)
    }
}
</script>


<style scoped>
/* Additional styles can be added here if needed */
.line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
</style>