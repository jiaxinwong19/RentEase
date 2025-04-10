# === Build Stage ===
FROM node:20 as build-stage

WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the app
COPY . .

# ✅ Inject all Vite env variables into the .env file used at build time
# Replace values as needed (or use ARG + --build-arg for CI pipelines)
RUN echo "VITE_API_BASE_URL=http://kong:8000" >> .env && \
    echo "VITE_FIREBASE_API_KEY=AIzaSyCAGIEUx9UPZj2ELLDqdjM9SSLaLagwhA" >> .env && \
    echo "VITE_FIREBASE_AUTH_DOMAIN=esd-image.firebaseapp.com" >> .env && \
    echo "VITE_FIREBASE_PROJECT_ID=esd-image" >> .env && \
    echo "VITE_FIREBASE_STORAGE_BUCKET=esd-image.firebasestorage.app" >> .env && \
    echo "VITE_FIREBASE_MESSAGING_SENDER_ID=821729599525" >> .env && \
    echo "VITE_FIREBASE_APP_ID=1:821729599525:web:a3b673a8751b4b883a5fcc" >> .env

# Build the app with Vite (Vite will read the .env here)
RUN npm run build

# === Production Stage ===
FROM nginx:stable-alpine as production-stage

# Copy built frontend files to Nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]