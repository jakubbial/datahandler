import { useEffect, useState } from "react";

type HealthResponse = {
  status: string;
  service: string;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
const healthCheckIntervalMs = 5_000;

function DashboardPage() {
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
    <div>
      <header className="mb-4">
        <p className="text-primary fw-semibold text-uppercase small mb-2">
          DataHandler
        </p>
        <h1 className="display-6 fw-bold mb-1">System dashboard</h1>
        <p className="text-body-secondary mb-0">
          Overview of the application status and backend connection.
        </p>
      </header>

      <section className="row g-4" aria-label="Service status">
        <div className="col-12 col-lg-8">
          <article className="card border-0 shadow-sm h-100">
            <div className="card-body p-4">
              <div className="d-flex justify-content-between align-items-start gap-3 mb-3">
                <div>
                  <h2 className="h5 card-title mb-1">Backend</h2>
                  <p className="text-body-secondary mb-0">
                    API service connection status
                  </p>
                </div>
                <span
                  className={`badge rounded-pill ${
                    health
                      ? "text-bg-success"
                      : error
                        ? "text-bg-danger"
                        : "text-bg-secondary"
                  }`}
                >
                  {health ? "Available" : error ? "Error" : "Checking"}
                </span>
              </div>

              {health ? (
                <p role="status" className="mb-0">
                  <span className="fw-semibold">{health.service}</span>:{" "}
                  {health.status}
                </p>
              ) : error ? (
                <p role="alert" className="mb-0">
                  Cannot connect to the backend: {error}
                </p>
              ) : (
                <p role="status" className="mb-0">
                  Checking backend connection…
                </p>
              )}
            </div>
          </article>
        </div>

        <div className="col-12 col-lg-4">
          <article className="card border-0 shadow-sm h-100">
            <div className="card-body p-4">
              <h2 className="h5 card-title mb-2">Frontend</h2>
              <p className="text-body-secondary mb-3">
                Application user interface layer
              </p>
              <span className="badge text-bg-primary">
                React + TypeScript + Vite
              </span>
            </div>
          </article>
        </div>
      </section>
    </div>
  );
}

export default DashboardPage;
