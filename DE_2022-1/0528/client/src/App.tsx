import { useState } from "react";
import logo from "./logo.svg";
import "./App.css";

const fetchHelloWorld = async () => {
  const res = await fetch("http://127.0.0.1:4000/hello", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (res.status === 200) {
    const data = await res.json();
    window.alert(data);
  }
};

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>Hello Vite + React!</p>
        <p>
          <button type="button" onClick={fetchHelloWorld}>
            Hello Docker-compose!
          </button>
        </p>
        <p>click button to get server response!</p>
      </header>
    </div>
  );
}

export default App;
