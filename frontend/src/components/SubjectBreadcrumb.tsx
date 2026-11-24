import { Link } from "react-router-dom";
import type { Subject } from "../api/subjects";
import { buildSubjectPath } from "../utils/subjectPath";

type SubjectBreadcrumbProps = {
  breadcrumb: Subject[];
};

function SubjectBreadcrumb({ breadcrumb }: SubjectBreadcrumbProps) {
  const upPath =
    breadcrumb.length > 0 ? buildSubjectPath(breadcrumb.slice(0, -1)) : null;

  return (
    <div className="d-flex align-items-center gap-3 mb-3">
      {upPath ? (
        <Link to={upPath} className="btn btn-outline-secondary btn-sm">
          ↑ Up
        </Link>
      ) : (
        <button
          type="button"
          className="btn btn-outline-secondary btn-sm"
          disabled
        >
          ↑ Up
        </button>
      )}
      <nav aria-label="breadcrumb">
        <ol className="breadcrumb mb-0">
          {breadcrumb.length === 0 ? (
            <li className="breadcrumb-item active" aria-current="page">
              All categories
            </li>
          ) : (
            <li className="breadcrumb-item">
              <Link to={buildSubjectPath([])}>All categories</Link>
            </li>
          )}
          {breadcrumb.map((subject, index) =>
            index === breadcrumb.length - 1 ? (
              <li
                key={subject.id}
                className="breadcrumb-item active"
                aria-current="page"
              >
                {subject.name}
              </li>
            ) : (
              <li key={subject.id} className="breadcrumb-item">
                <Link to={buildSubjectPath(breadcrumb.slice(0, index + 1))}>
                  {subject.name}
                </Link>
              </li>
            ),
          )}
        </ol>
      </nav>
    </div>
  );
}

export default SubjectBreadcrumb;
