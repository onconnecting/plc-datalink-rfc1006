# Stage 1: Build the Angular 19 application.
FROM node:22-alpine AS build-stage

WORKDIR /app

# Install dependencies first to take advantage of layer caching.
COPY package.json package-lock.json* /app/
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund

# Copy the rest of the project and produce a production bundle.
COPY . /app/
RUN npm run build -- --output-path=/app/dist/plc-datalink-rfc1006-frontend

# Stage 2: Serve the bundle via nginx Alpine.
FROM nginx:stable-alpine

RUN rm /etc/nginx/conf.d/default.conf /etc/nginx/nginx.conf

COPY config/nginx-custom.conf /etc/nginx/conf.d/default.conf
COPY config/nginx-main.conf  /etc/nginx/nginx.conf

# Angular @angular/build (esbuild) emits SPA assets under dist/<name>/browser.
COPY --from=build-stage /app/dist/plc-datalink-rfc1006-frontend /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
