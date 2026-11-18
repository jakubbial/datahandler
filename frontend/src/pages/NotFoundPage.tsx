import { Link } from "react-router-dom";

function NotFoundPage() {
  return (
    <section>
      <h1 className="display-6 fw-bold mb-1">Page not found</h1>
      <p className="text-body-secondary">
        The page you are looking for does not exist.
      </p>
      <Link to="/" className="btn btn-primary">
        Back to dashboard
      </Link>
    </section>
  );
}

export default NotFoundPage;
