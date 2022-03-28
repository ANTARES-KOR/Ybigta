const express = require("express");
const redis = require("redis");

const client = redis.createClient({
  // use container name set in docker-compose.yml
  host: "",
  // redis initial port
  port: 6379,
});

const app = express();

client.set("visit", 0);

app.get("/", (req, res) => {
  client.get("visit", (err, visit) => {
    client.set("visit", parseInt(visit) + 1);
    res.send("Hello World! I have been visited " + visit + " times");
  });
});

app.listen(8080);
console.log("Server is Running");
