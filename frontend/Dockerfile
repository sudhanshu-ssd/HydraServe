FROM node:20-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Set API URL for production build to use Nginx proxy
ENV VITE_API_URL=/api
RUN npm run build

FROM nginx:alpine

RUN apk add --no-cache certbot certbot-nginx

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"]
