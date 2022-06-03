const express = require("express");
const cors = require("cors");

const app = express();
const PORT = 4000;

app.use(cors());

app.get("/hello", (req, res) => {
  res.json("Welcome, fellow! nice to see you!");
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
