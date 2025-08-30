# ---- Build Stage ----
FROM node:18-alpine AS builder
WORKDIR /app
COPY package.json ./
# If a lockfile exists, copy it to leverage cached installs
COPY package-lock.json ./
COPY yarn.lock ./
COPY pnpm-lock.yaml ./
RUN if [ -f package-lock.json ]; then npm ci; \
    elif [ -f yarn.lock ]; then yarn install --frozen-lockfile; \
    elif [ -f pnpm-lock.yaml ]; then npm i -g pnpm && pnpm i --frozen-lockfile; \
    else npm i; fi
COPY . .
RUN npm run build

# ---- Run Stage ----
FROM node:18-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]

