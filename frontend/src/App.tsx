import { useEffect, useState } from 'react';

type HealthResponse = {
  status: string;
  service: string;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api';

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${apiBaseUrl}/health`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Backend returned HTTP ${response.status}`);
        }
        return (await response.json()) as HealthResponse;
      })
      .then(setHealth)
      .catch((requestError: unknown) => {
        setError(requestError instanceof Error ? requestError.message : 'Unknown error');
      });
  }, []);

  return (
    <main style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>DataHandler</h1>
      <p>Frontend: React + TypeScript + Vite</p>
      <h2>Backend status</h2>
      {health ? (
        <p role="status">{health.service}: {health.status}</p>
      ) : error ? (
        <p role="alert">Could not reach backend: {error}</p>
      ) : (
        <p>Checking backend…</p>
      )}
    </main>
  );
}

export default App;
