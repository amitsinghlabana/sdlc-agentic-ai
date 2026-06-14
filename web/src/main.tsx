import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "./lib/router";
import ErrorBoundary from "./components/ErrorBoundary";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <RouterProvider>
        <App />
      </RouterProvider>
    </ErrorBoundary>
  </React.StrictMode>
);

