<template>
    <div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div class="sm:mx-auto sm:w-full sm:max-w-md">
            <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
                Create your account
            </h2>
            <p class="mt-2 text-center text-sm text-gray-600">
                Or
                <router-link to="/login" class="font-medium text-blue-600 hover:text-blue-500">
                    sign in to your account
                </router-link>
            </p>
        </div>

        <div class="mt-8 sm:mx-auto sm:w-full w-[1000px]">
            <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
                <form class="space-y-6" @submit.prevent="handleSignup">
                    <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
                        <div>
                            <label for="name" class="block text-sm font-medium text-gray-700">
                                Full Name
                            </label>
                            <div class="mt-1">
                                <input id="name" name="name" type="text" v-model="formData.name" required
                                    class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
                            </div>
                        </div>

                        <div>
                            <label for="username" class="block text-sm font-medium text-gray-700">
                                Username
                            </label>
                            <div class="mt-1">
                                <input id="username" name="username" type="text" v-model="formData.username" required
                                    class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
                            </div>
                        </div>
                    </div>

                    <div>
                        <label for="email" class="block text-sm font-medium text-gray-700">
                            Email address
                        </label>
                        <div class="mt-1">
                            <input id="email" name="email" type="email" v-model="formData.email" required
                                class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
                        </div>
                    </div>

                    <div>
                        <label for="phone" class="block text-sm font-medium text-gray-700">
                            Phone Number
                        </label>
                        <div class="mt-1">
                            <input id="phone" name="phone" type="tel" v-model="formData.phone" required
                                class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
                        </div>
                    </div>

                    <div>
                        <label for="street1" class="block text-sm font-medium text-gray-700">
                            Street Address
                        </label>
                        <div class="mt-1">
                            <input id="street1" name="street1" type="text" v-model="formData.street1" required
                                class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
                        </div>
                    </div>

                    <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
                        <div>
                            <label for="city" class="block text-sm font-medium text-gray-700">
                                City
                            </label>
                            <div class="mt-1">
                                <input id="city" name="city" type="text" v-model="formData.city" required
                                    class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
                            </div>
                        </div>

                        <div>
                            <label for="state" class="block text-sm font-medium text-gray-700">
                                State
                            </label>
                            <div class="mt-1">
                                <input id="state" name="state" type="text" v-model="formData.state" required
                                    class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
                        <div>
                            <label for="zip" class="block text-sm font-medium text-gray-700">
                                ZIP Code
                            </label>
                            <div class="mt-1">
                                <input id="zip" name="zip" type="text" v-model="formData.zip" required
                                    class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
                            </div>
                        </div>

                        <div>
                            <label for="country" class="block text-sm font-medium text-gray-700">
                                Country
                            </label>
                            <div class="mt-1">
                                <input id="country" name="country" type="text" v-model="formData.country" required
                                    class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
                            </div>
                        </div>
                    </div>

                    <div>
                        <label for="password" class="block text-sm font-medium text-gray-700">
                            Password
                        </label>
                        <div class="mt-1">
                            <input id="password" name="password" type="password" v-model="formData.password" required
                                class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
                        </div>
                    </div>

                    <div>
                        <button type="submit"
                            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                            Create Account
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const formData = ref({
    name: '',
    username: '',
    email: '',
    phone: '',
    street1: '',
    city: '',
    state: '',
    zip: '',
    country: '',
    password: ''
})
const handleSignup = async () => {
    try {
        const response = await fetch('https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/addUser', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: formData.value.name,
                username: formData.value.username,
                email: formData.value.email,
                phone: formData.value.phone,
                street1: formData.value.street1,
                city: formData.value.city,
                state: formData.value.state,
                zip: formData.value.zip,
                country: formData.value.country,
                password: formData.value.password
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Store authentication state
        localStorage.setItem('isAuthenticated', 'true');
        localStorage.setItem('userId', data.id); // Store user ID if returned from API
        
        // Redirect to rental store page
        router.push('/login');
    } catch (error) {
        console.error('Signup failed:', error);
        // Here you might want to add error handling UI feedback
    }
}
</script> 