#!/bin/bash
# Generate the React frontend from the template
bash create-frontend.sh

# Build it for production
cd web-ui
npm install
npm run build

echo "Frontend built successfully!"
echo "Build output is in: web-ui/build/"
