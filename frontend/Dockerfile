FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG NEXT_PUBLIC_BASE_PATH=/ai
ARG NEXT_PUBLIC_API_URL=https://admin.gennomx.com/api/ai
ENV NEXT_PUBLIC_BASE_PATH=$NEXT_PUBLIC_BASE_PATH \
    NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    HOSTNAME=0.0.0.0 \
    PORT=3000

RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
