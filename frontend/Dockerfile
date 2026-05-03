# Frontend Dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 4200

# Start development server with Docker proxy config
CMD ["ng", "serve", "--proxy-config", "proxy.conf.docker.json", "--host", "0.0.0.0", "--port", "4200"]