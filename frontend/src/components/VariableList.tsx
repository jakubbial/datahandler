import { useId, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { Variable } from "../api/variables";
import { groupVariables, normalizeText } from "../utils/variableGroups";

type VariableListProps = {
  variables: Variable[];
  subjectPath: string;
  selectedId: number | null;
};

function VariableList({
  variables,
  subjectPath,
  selectedId,
}: VariableListProps) {
  const [filter, setFilter] = useState("");
  const filterInputId = useId();
  const groups = useMemo(() => groupVariables(variables), [variables]);
  const showHeadings = groups.length > 1;

  if (variables.length === 0) {
    return (
      <p role="status" className="text-body-secondary mb-0">
        This subject has no variables.
      </p>
    );
  }

  const query = normalizeText(filter.trim());
  const visibleGroups = groups
    .map((group) => ({
      ...group,
      items: query
        ? group.items.filter(({ variable }) =>
            normalizeText(variable.name).includes(query),
          )
        : group.items,
    }))
    .filter((group) => group.items.length > 0);

  return (
    <div>
      <div className="mb-3">
        <label htmlFor={filterInputId} className="form-label small mb-1">
          Filter variables
        </label>
        <input
          id={filterInputId}
          type="search"
          className="form-control"
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
        />
      </div>

      {visibleGroups.length === 0 ? (
        <p role="status" className="text-body-secondary mb-0">
          No variables match the filter.
        </p>
      ) : (
        visibleGroups.map((group, index) => (
          <section
            key={group.title ?? `ungrouped-${index}`}
            className="mb-3"
            aria-label={group.title ?? undefined}
          >
            {showHeadings && group.title !== null && (
              <h3 className="h6 text-body-secondary mb-2">{group.title}</h3>
            )}
            <div className="list-group shadow-sm">
              {group.items.map(({ variable, label }) => {
                const isSelected = variable.id === selectedId;
                return (
                  <Link
                    key={variable.id}
                    to={{
                      pathname: subjectPath,
                      search: `?variable=${variable.id}`,
                    }}
                    className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center gap-3${
                      isSelected ? " active" : ""
                    }`}
                    aria-current={isSelected ? "true" : undefined}
                    title={variable.name}
                  >
                    <span>{showHeadings ? label : variable.name}</span>
                    <small
                      className={`text-nowrap${
                        isSelected ? "" : " text-body-secondary"
                      }`}
                    >
                      {variable.measureUnitName ?? "No unit"}
                    </small>
                  </Link>
                );
              })}
            </div>
          </section>
        ))
      )}
    </div>
  );
}

export default VariableList;
