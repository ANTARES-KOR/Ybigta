FROM node:18.2-alpine

WORKDIR /app

RUN npm i -g nodemon pnpm

COPY . /app/

RUN pnpm install --frozen-lockfile

EXPOSE 4000

CMD pnpm start