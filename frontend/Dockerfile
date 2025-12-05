# 1. Use a lightweight Nginx image
FROM nginx:alpine

# 2. Copy your static frontend files (index.html, script.js)
#    into the default Nginx directory to be served.
#    (Assuming index.html and script.js are in the 'frontend' folder)
COPY . /usr/share/nginx/html

# 3. Expose the default Nginx port
EXPOSE 80

# Nginx will automatically start and serve the files when the container runs.