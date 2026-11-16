FROM mcr.microsoft.com/devcontainers/typescript-node:20-bookworm

WORKDIR /app

COPY package*.json ./

RUN npm install

EXPOSE 3100

CMD ["npm", "run", "dev"]
