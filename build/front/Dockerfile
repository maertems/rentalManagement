FROM node:22-alpine

WORKDIR /app

# Install deps first for better layer caching
COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
