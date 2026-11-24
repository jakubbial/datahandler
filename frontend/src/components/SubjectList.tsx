import { Link } from "react-router-dom";
import type { Subject } from "../api/subjects";
import { buildSubjectPath } from "../utils/subjectPath";

type SubjectListProps = {
  breadcrumb: Subject[];
  items: Subject[];
  selectedId: string | null;
};

function SubjectList({ breadcrumb, items, selectedId }: SubjectListProps) {
  if (items.length === 0) {
    return (
      <p role="status" className="text-body-secondary mb-0">
        No subjects in this category.
      </p>
    );
  }

  return (
    <div className="list-group shadow-sm">
      {items.map((subject) => {
        const isSelected = subject.id === selectedId;
        return (
          <Link
            key={subject.id}
            to={buildSubjectPath([...breadcrumb, subject])}
            className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center gap-3${
              isSelected ? " active" : ""
            }`}
            aria-current={isSelected ? "true" : undefined}
          >
            <span>
              <span className="d-block">{subject.name}</span>
              <small className={isSelected ? "" : "text-body-secondary"}>
                {subject.id}
              </small>
            </span>
            {subject.hasVariables ? (
              <span className="badge text-bg-info">Variables</span>
            ) : (
              <span aria-hidden="true">›</span>
            )}
          </Link>
        );
      })}
    </div>
  );
}

export default SubjectList;
