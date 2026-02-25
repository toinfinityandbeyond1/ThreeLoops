# Frontend service - builds and serves the React app

# Stage 1: Generate frontend from template and build for production
FROM node:18-alpine AS builder

WORKDIR /app

# Install bash (Alpine uses sh by default)
RUN apk add --no-cache bash

# Copy the create-frontend.sh script
COPY create-frontend.sh .

# Make sure it's executable and run it with bash explicitly
RUN bash -x create-frontend.sh

# Build the React app for production
WORKDIR /app/web-ui
RUN npm install && npm run build

# Stage 2: Serve the built frontend with a lightweight server
FROM node:18-alpine

WORKDIR /app

# Install serve to run the frontend
RUN npm install -g serve

# Copy the built app from the builder stage
COPY --from=builder /app/web-ui/build ./build

# Expose port
EXPOSE 3000

# Set environment variables for frontend
ENV REACT_APP_API_URL=${REACT_APP_API_URL:-http://localhost:8000}

# Serve the app
CMD ["serve", "-s", "build", "-l", "3000"]
