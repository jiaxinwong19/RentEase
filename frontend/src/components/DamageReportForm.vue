<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import {
  ref as storageRef,
  uploadBytes,
  getDownloadURL
} from "firebase/storage";
import { storage } from "../firebase"; // update path if needed

// Define props to receive orderID and productID from parent component
const props = defineProps({
  orderID: {
    type: [String, Number],
    default: ''
  },
  productID: {
    type: [String, Number],
    default: ''
  }
});

interface DamageReport {
  description: string;
  image: File | null;
}

const report = ref<DamageReport>({
  description: '',
  image: null
});

const imagePreview = ref<string>('');
const isSubmitting = ref(false);
const submitStatus = ref<'idle' | 'success' | 'error'>('idle');
const damageType = ref('');
const orderID = ref(props.orderID || '');
const productID = ref(props.productID || '');

// Watch for changes to props and update the local refs
watch(() => props.orderID, (newVal) => {
  if (newVal) {
    orderID.value = newVal;
    console.log('Updated orderID from props:', orderID.value);
  }
});

watch(() => props.productID, (newVal) => {
  if (newVal) {
    productID.value = newVal;
    console.log('Updated productID from props:', productID.value);
  }
});

// Log props on component mount
onMounted(() => {
  console.log('DamageReportForm mounted with props:', props);
  console.log('Initial orderID:', orderID.value);
  console.log('Initial productID:', productID.value);
});

const handleImageChange = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    report.value.image = input.files[0];
    imagePreview.value = URL.createObjectURL(input.files[0]);
    console.log('🖼️ Image selected:', report.value.image);
  }
};

const removeImage = () => {
  report.value.image = null;
  imagePreview.value = '';
};

const submitReport = async () => {
  if (!damageType.value) {
    console.warn('⚠️ Damage type not selected!');
    return;
  }

  isSubmitting.value = true;
  submitStatus.value = 'idle';

  try {
    let imageUrl = '';

    if (report.value.image) {
      console.log('⬆️ Uploading image to Firebase...');

      const uniqueFilename = `damage-images/${Date.now()}-${report.value.image.name}`;
      const imageRef = storageRef(storage, uniqueFilename);

      await uploadBytes(imageRef, report.value.image);
      imageUrl = await getDownloadURL(imageRef);

      console.log('✅ Image uploaded to Firebase:', imageUrl);
    }

    const userID = localStorage.getItem('userId') || '';

    const payload = {
      userID,
      orderID: orderID.value,
      productID: productID.value,
      description: report.value.description,
      damageType: damageType.value,
      reportImageUrl: imageUrl
    };

    console.log('📦 Sending damage report to backend...');
    console.log('🧾 Payload:', payload);

    const response = await fetch('http://localhost:5004/report-damage', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error('Submission failed');
    console.log('✅ Report submitted successfully');

    submitStatus.value = 'success';

    report.value = { description: '', image: null };
    imagePreview.value = '';
    damageType.value = '';
    orderID.value = '';
    productID.value = '';
  } catch (error) {
    console.error('❌ Error submitting report:', error);
    submitStatus.value = 'error';
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<template>
  <div class="w-full min-h-screen bg-gray-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="bg-white rounded-lg shadow-lg p-8">
        <h2 class="text-4xl font-bold text-gray-800 mb-6">Report Damage</h2>

        <form @submit.prevent="submitReport" class="space-y-6">

          <!-- Order ID Input - Read-only if provided via props -->
          <div>
            <label for="order-id" class="block text-sm font-medium text-gray-700 mb-2">Order ID</label>
            <input id="order-id" v-model="orderID" type="text" placeholder="Enter your order ID"
              :class="[
                'w-full px-6 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg',
                props.orderID ? 'bg-gray-100 border-gray-200' : 'border-gray-300'
              ]"
              :readonly="!!props.orderID" 
              required />
          </div>

          <!-- Product ID Input - Read-only if provided via props -->
          <div class="mt-4">
            <label for="product-id" class="block text-sm font-medium text-gray-700 mb-2">Product ID</label>
            <input id="product-id" v-model="productID" type="text" placeholder="Enter your product ID"
              :class="[
                'w-full px-6 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg',
                props.productID ? 'bg-gray-100 border-gray-200' : 'border-gray-300'
              ]"
              :readonly="!!props.productID" 
              required />
          </div>

          <!-- Damage Type Selection -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">Damage Type</label>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button type="button" @click="damageType = 'arrival'" :class="[
                'p-6 rounded-lg border-2 text-center transition-colors',
                damageType === 'arrival'
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 hover:border-blue-300'
              ]">
                <package-x-icon class="w-8 h-8 mx-auto mb-3" />
                <span class="font-medium text-lg">Damage Upon Arrival</span>
              </button>
              <button type="button" @click="damageType = 'user'" :class="[
                'p-6 rounded-lg border-2 text-center transition-colors',
                damageType === 'use'
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 hover:border-blue-300'
              ]">
                <alert-triangle-icon class="w-8 h-8 mx-auto mb-3" />
                <span class="font-medium text-lg">Damage After Using</span>
              </button>
            </div>
            <p v-if="!damageType" class="mt-2 text-sm text-red-500">Please select a damage type</p>
          </div>

          <!-- Description Input -->
          <div>
            <label for="description" class="block text-sm font-medium text-gray-700 mb-2">Description</label>
            <textarea id="description" v-model="report.description" rows="6"
              class="w-full px-6 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
              placeholder="Detailed description of the damage..." required></textarea>
          </div>

          <!-- Image Upload -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Upload Image</label>
            <div class="mt-1 flex justify-center px-6 pt-8 pb-8 border-2 border-gray-300 border-dashed rounded-lg">
              <div class="space-y-2 text-center">
                <camera-icon class="mx-auto h-16 w-16 text-gray-400" />
                <div class="flex text-base text-gray-600 justify-center">
                  <label for="image-upload"
                    class="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
                    <span>Upload a file</span>
                    <input id="image-upload" type="file" class="sr-only" accept="image/*" @change="handleImageChange" />
                  </label>
                  <p class="pl-1">&nbsp;or drag and drop</p>
                </div>
                <p class="text-sm text-gray-500">PNG, JPG, GIF up to 10MB</p>
              </div>
            </div>
            <!-- Image Preview -->
            <div v-if="imagePreview" class="mt-6">
              <img :src="imagePreview" alt="Preview" class="max-h-64 rounded-lg mx-auto" />
              <button type="button" @click="removeImage"
                class="mt-3 text-sm text-red-600 hover:text-red-800 flex items-center justify-center">
                <trash-2-icon class="w-5 h-5 mr-1" />
                Remove Image
              </button>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="flex justify-end">
            <button type="submit" :disabled="isSubmitting || !damageType" :class="[
              'px-8 py-3 rounded-lg font-medium text-white transition-colors text-lg',
              isSubmitting || !damageType
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            ]">
              <span v-if="isSubmitting" class="flex items-center">
                <loader-2-icon class="w-5 h-5 mr-2 animate-spin" />
                Submitting...
              </span>
              <span v-else>Submit Report</span>
            </button>
          </div>

          <!-- Success Message -->
          <div v-if="submitStatus === 'success'"
            class="p-6 bg-green-50 border border-green-200 rounded-lg text-green-700 text-lg">
            <check-circle-icon class="w-6 h-6 inline-block mr-2" />
            Report submitted successfully!
          </div>

          <!-- Error Message -->
          <div v-if="submitStatus === 'error'"
            class="p-6 bg-red-50 border border-red-200 rounded-lg text-red-700 text-lg">
            <x-circle-icon class="w-6 h-6 inline-block mr-2" />
            Failed to submit report. Please try again.
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}
</style>