// API base URL configuration for Kong Gateway
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API endpoints
export const API_ENDPOINTS = {
  // Order endpoints
  ORDER: {
    CREATE: `${API_BASE_URL}/order/orders`,
    CONFIRM: (orderId) => `${API_BASE_URL}/order/confirm/${orderId}`,
    NOTIFY_SHIPPING: (orderId) => `${API_BASE_URL}/order/notify-shipping/${orderId}`,
  },
  
  // Inventory endpoints
  INVENTORY: {
    GET_ALL: `${API_BASE_URL}/inventory/products`,
    GET_BY_ID: (id) => `${API_BASE_URL}/inventory/products/${id}`,
    UPDATE: `${API_BASE_URL}/inventory/products`,
  },
  
  // Notification endpoints
  NOTIFICATION: {
    RENTER: `${API_BASE_URL}/notification/renter/notify`,
    ORDER_CONFIRM: `${API_BASE_URL}/notification/order/confirm`,
    DAMAGE_REPORT: `${API_BASE_URL}/notification/damage/report`,
  },
  
  // Condition checking endpoints
  CONDITION: {
    CHECK: `${API_BASE_URL}/condition/compareImages`,
  },
  
  // Transaction endpoints
  TRANSACTION: {
    PURCHASE: `${API_BASE_URL}/transaction/purchase`,
    REFUND: `${API_BASE_URL}/transaction/refund`,
  },
  
  // Shipping endpoints
  SHIPPING: {
    GET_LABEL: (orderId) => `${API_BASE_URL}/shipping/${orderId}/label`,
    GET_INFO: (orderId) => `${API_BASE_URL}/shipping/${orderId}`,
  },
  
  // Report damage endpoints
  DAMAGE: {
    REPORT: `${API_BASE_URL}/damage/report-damage`,
  },
  
  // External services (unchanged)
  EXTERNAL: {
    USER_EMAIL: 'https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getEmail/',
    USER_INFO: 'https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getUserInfo',
    LOGIN: 'https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/login',
    SIGNUP: 'https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/addUser',
    STRIPE_CUSTOMER: 'https://personal-s5llcxwn.outsystemscloud.com/userMS/rest/user/getStripeCusID/',
  }
};

// Example function to make API requests
export const apiRequest = async (url, options = {}) => {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Request Error:', error);
    throw error;
  }
};