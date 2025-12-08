import "@/styles/App.css";

import reactLogo from "@/assets/react.svg";

import { useState } from "react";

function App() {
    const [count, setCount] = useState(0);

    return (
        <>
            <div>
                <a href="https://react.dev" target="_blank">
                    <img src={reactLogo} className="logo react" alt="React logo" />
                </a>
            </div>
            <h1>Q&A Prototype</h1>
            <div className="card">
                <button onClick={() => setCount((count) => count + 1)}>count is {count}</button>
                <p>
                    Edit <code>src/App.tsx</code> and save to test HMR
                </p>
            </div>
            <p className="read-the-docs">Q&A Prototype</p>
        </>
    );
}

export default App;
