FROM node:18.2-alpine

WORKDIR /app

RUN npm i -g serve pnpm

RUN npm i -g typescript

COPY . /app/

RUN pnpm install --frozen-lockfile

RUN pnpm build

EXPOSE 3000

CMD serve -s dist