FROM node:20-alpine AS base

FROM base AS builder
# Hedef dizin
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Geliştirme ortamında çalışacağız (Hot Reload için cmd olacak)
# Ancak prod ortamı için build alınabilir.
# RUN npm run build

FROM base AS runner
WORKDIR /app

ENV NODE_ENV=development
ENV HOST=0.0.0.0
ENV PORT=3000

COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app ./

EXPOSE 3000

# Geliştirme ortamı başlat
CMD ["npm", "run", "dev"]
