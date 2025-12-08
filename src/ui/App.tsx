import { useState } from "react";

function App() {
    const [count, setCount] = useState(0);

    return (
        <>
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
