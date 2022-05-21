FROM node:10

WORKDIR /Users/antares/Documents/Ybigta/Docker/section5

COPY package.json ./

RUN npm install

COPY ./ ./

CMD ["node", "server.js"]