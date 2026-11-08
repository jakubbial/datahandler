import { useEffect, useState } from "react";

type HealthResponse = {
  status: string;
  service: string;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
const healthCheckIntervalMs = 5_000;

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    const checkHealth = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/health`);
        if (!response.ok) {
          throw new Error(`Backend returned HTTP ${response.status}`);
        }

        const result = (await response.json()) as HealthResponse;
        if (isActive) {
          setHealth(result);
          setError(null);
        }
      } catch (requestError: unknown) {
        if (isActive) {
          setHealth(null);
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Unknown error",
          );
        }
      }
    };

    void checkHealth();
    const intervalId = window.setInterval(() => {
      void checkHealth();
    }, healthCheckIntervalMs);

    return () => {
      isActive = false;
      window.clearInterval(intervalId);
    };
  }, []);

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>DataHandler</h1>
      <p>Frontend: React + TypeScript + Vite</p>
      <h2>Backend status</h2>
      {health ? (
        <p role="status">
          {health.service}: {health.status}
        </p>
      ) : error ? (
        <p role="alert">Could not reach backend: {error}</p>
      ) : (
        <p>Checking backend…</p>
      )}
    </main>
  );
}

export default App;
