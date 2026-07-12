# Этап 1: Сборка React
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Этап 2: Раздача через Nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html

# Простой конфиг для работы роутинга React (чтобы при обновлении страницы не было 404)
RUN echo -e 'server {\n    listen 80;\n    location / {\n        root /usr/share/nginx/html;\n        index index.html;\n        try_files $uri $uri/ /index.html;\n    }\n}' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]