import { useEffect } from "react";
import {
  Link,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import type { Subject } from "../api/subjects";
import type { Variable } from "../api/variables";
import SubjectBreadcrumb from "../components/SubjectBreadcrumb";
import SubjectList from "../components/SubjectList";
import VariableData from "../components/VariableData";
import VariableList from "../components/VariableList";
import {
  useSubjectPath,
  type SubjectsErrorKind,
} from "../hooks/useSubjectPath";
import { useVariableDetails } from "../hooks/useVariableDetails";
import { useVariables } from "../hooks/useVariables";
import { buildSubjectPath, localDataBankBasePath } from "../utils/subjectPath";

const errorMessages: Record<Exclude<SubjectsErrorKind, "unknown">, string> = {
  "invalid-id": "Invalid subject identifier.",
  "not-found": "Subject not found.",
  "rate-limit":
    "Too many requests to the BDL API. Please try again in a moment.",
  unavailable: "The BDL API is currently unavailable.",
};

const retryableErrors: SubjectsErrorKind[] = [
  "rate-limit",
  "unavailable",
  "unknown",
];

const variableIdPattern = /^[1-9][0-9]*$/;

type LoadErrorAlertProps = {
  error: SubjectsErrorKind;
  resource: "subjects" | "variables";
  onRetry: () => void;
};

function LoadErrorAlert({ error, resource, onRetry }: LoadErrorAlertProps) {
  return (
    <div
      role="alert"
      className={`alert ${
        error === "rate-limit" ? "alert-warning" : "alert-danger"
      } d-flex justify-content-between align-items-center gap-3`}
    >
      <span>
        {error === "unknown"
          ? `Cannot load ${resource}. Check your connection and try again.`
          : errorMessages[error]}
      </span>
      {retryableErrors.includes(error) ? (
        <button
          type="button"
          className="btn btn-outline-dark btn-sm"
          onClick={onRetry}
        >
          Retry
        </button>
      ) : (
        <Link
          to={localDataBankBasePath}
          className="btn btn-outline-dark btn-sm"
        >
          Back to all categories
        </Link>
      )}
    </div>
  );
}

function LoadingStatus({ text }: { text: string }) {
  return (
    <div role="status" className="d-flex align-items-center gap-2">
      <span
        className="spinner-border spinner-border-sm text-primary"
        aria-hidden="true"
      />
      <span>{text}</span>
    </div>
  );
}

type SelectedVariable =
  | { status: "none" }
  | { status: "pending" }
  | { status: "not-found" }
  | { status: "found"; variable: Variable };

function LocalDataBankPage() {
  const splat = useParams()["*"] ?? "";
  const segments = splat.split("/").filter(Boolean);
  const { state, retry } = useSubjectPath(segments);
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();

  const selectedSubject: Subject | null =
    state.status === "ready" ? state.selected : null;
  const { state: variablesState, retry: retryVariables } = useVariables(
    selectedSubject?.id ?? null,
  );

  const canonicalPath =
    state.status === "ready"
      ? buildSubjectPath(
          state.selected
            ? [...state.breadcrumb, state.selected]
            : state.breadcrumb,
        )
      : null;
  const currentPath = [localDataBankBasePath, ...segments].join("/");

  useEffect(() => {
    if (canonicalPath && canonicalPath !== currentPath) {
      navigate(
        { pathname: canonicalPath, search: location.search },
        { replace: true },
      );
    }
  }, [canonicalPath, currentPath, location.search, navigate]);

  const variableParam = searchParams.get("variable");
  let selectedVariable: SelectedVariable = { status: "none" };
  if (selectedSubject && variableParam !== null) {
    if (!variableIdPattern.test(variableParam)) {
      selectedVariable = { status: "not-found" };
    } else if (variablesState.status === "ready") {
      const variable = variablesState.variables.find(
        (item) => item.id === Number(variableParam),
      );
      selectedVariable = variable
        ? { status: "found", variable }
        : { status: "not-found" };
    } else {
      selectedVariable = { status: "pending" };
    }
  }

  const { state: variableDetailsState, retry: retryVariableDetails } =
    useVariableDetails(
      selectedVariable.status === "found" ? selectedVariable.variable.id : null,
    );

  return (
    <div>
      <header className="mb-4">
        <p className="text-primary fw-semibold text-uppercase small mb-2">
          DataHandler
        </p>
        <h1 className="display-6 fw-bold mb-1">Local Data Bank</h1>
        <p className="text-body-secondary mb-0">
          Browse subjects of the Local Data Bank (BDL) and select a variable.
        </p>
      </header>

      {state.status === "loading" && <LoadingStatus text="Loading subjects…" />}

      {state.status === "error" && (
        <LoadErrorAlert
          error={state.error}
          resource="subjects"
          onRetry={retry}
        />
      )}

      {state.status === "ready" && !state.selected && (
        <section aria-label="Subjects">
          <SubjectBreadcrumb breadcrumb={state.breadcrumb} />
          <SubjectList
            breadcrumb={state.breadcrumb}
            items={state.items}
            selectedId={null}
          />
        </section>
      )}

      {state.status === "ready" && state.selected && (
        <div className="row g-4">
          <section className="col-12 col-lg-8" aria-label="Variables">
            <SubjectBreadcrumb
              breadcrumb={[...state.breadcrumb, state.selected]}
            />
            {variablesState.status === "loading" && (
              <LoadingStatus text="Loading variables…" />
            )}
            {variablesState.status === "error" && (
              <LoadErrorAlert
                error={variablesState.error}
                resource="variables"
                onRetry={retryVariables}
              />
            )}
            {variablesState.status === "ready" && (
              <VariableList
                key={state.selected.id}
                variables={variablesState.variables}
                subjectPath={buildSubjectPath([
                  ...state.breadcrumb,
                  state.selected,
                ])}
                selectedId={
                  selectedVariable.status === "found"
                    ? selectedVariable.variable.id
                    : null
                }
              />
            )}
          </section>

          <aside className="col-12 col-lg-4" aria-label="Selection">
            <article className="card border-0 shadow-sm">
              <div className="card-body p-4">
                <p className="text-body-secondary small mb-1">
                  Selected subject
                </p>
                <h2 className="h5 card-title mb-1">{state.selected.name}</h2>
                <p className="text-body-secondary mb-2">{state.selected.id}</p>
                <p className="mb-3">
                  Unit levels:{" "}
                  {state.selected.levels.length > 0
                    ? state.selected.levels.join(", ")
                    : "none"}
                </p>
                <Link
                  to={buildSubjectPath(state.breadcrumb)}
                  className="btn btn-outline-secondary btn-sm"
                >
                  Clear subject selection
                </Link>

                {selectedVariable.status === "found" && (
                  <div className="border-top mt-4 pt-3">
                    <p className="text-body-secondary small mb-1">
                      Selected variable
                    </p>
                    <h3 className="h6 mb-2">
                      {selectedVariable.variable.name}
                    </h3>
                    <dl className="row small mb-3">
                      <dt className="col-5 fw-normal text-body-secondary">
                        ID
                      </dt>
                      <dd className="col-7 mb-1">
                        {selectedVariable.variable.id}
                      </dd>
                      <dt className="col-5 fw-normal text-body-secondary">
                        Level
                      </dt>
                      <dd className="col-7 mb-1">
                        {selectedVariable.variable.level}
                      </dd>
                      <dt className="col-5 fw-normal text-body-secondary">
                        Measure unit
                      </dt>
                      <dd className="col-7 mb-0">
                        {selectedVariable.variable.measureUnitName ?? "No unit"}
                      </dd>
                    </dl>
                    {variableDetailsState.status === "loading" && (
                      <LoadingStatus text="Loading variable details…" />
                    )}
                    {variableDetailsState.status === "ready" && (
                      <div className="small mb-3">
                        <p className="mb-2">
                          <span className="fw-semibold">Years with data: </span>
                          {variableDetailsState.details.years.length > 0
                            ? variableDetailsState.details.years.length === 1
                              ? `${variableDetailsState.details.years[0]} (1)`
                              : `${variableDetailsState.details.years[0]}–${variableDetailsState.details.years[variableDetailsState.details.years.length - 1]} (${variableDetailsState.details.years.length})`
                            : "No years with data."}
                        </p>
                        {variableDetailsState.details.description !== null && (
                          <p className="mb-0">
                            <span className="fw-semibold">Description: </span>
                            {variableDetailsState.details.description}
                          </p>
                        )}
                      </div>
                    )}
                    {variableDetailsState.status === "error" && (
                      <div
                        role="alert"
                        className={`alert ${
                          variableDetailsState.error === "rate-limit"
                            ? "alert-warning"
                            : "alert-danger"
                        } d-flex justify-content-between align-items-center gap-3`}
                      >
                        <span>
                          {variableDetailsState.error === "not-found"
                            ? "Variable not found."
                            : variableDetailsState.error === "invalid-id"
                              ? "Invalid variable identifier."
                              : variableDetailsState.error === "rate-limit"
                                ? "Too many requests to the BDL API. Please try again in a moment."
                                : variableDetailsState.error === "unavailable"
                                  ? "The BDL API is currently unavailable."
                                  : "Cannot load variable details. Check your connection and try again."}
                        </span>
                        {retryableErrors.includes(
                          variableDetailsState.error,
                        ) && (
                          <button
                            type="button"
                            className="btn btn-outline-dark btn-sm"
                            onClick={retryVariableDetails}
                          >
                            Retry
                          </button>
                        )}
                      </div>
                    )}
                    <Link
                      to={buildSubjectPath([
                        ...state.breadcrumb,
                        state.selected,
                      ])}
                      className="btn btn-outline-secondary btn-sm"
                    >
                      Clear variable selection
                    </Link>
                  </div>
                )}

                {selectedVariable.status === "not-found" && (
                  <div
                    role="alert"
                    className="alert alert-warning mt-4 mb-0 d-flex justify-content-between align-items-center gap-3"
                  >
                    <span>Variable not found.</span>
                    <Link
                      to={buildSubjectPath([
                        ...state.breadcrumb,
                        state.selected,
                      ])}
                      className="btn btn-outline-dark btn-sm"
                    >
                      Clear
                    </Link>
                  </div>
                )}
              </div>
            </article>
          </aside>
        </div>
      )}
      {selectedVariable.status === "found" &&
        variableDetailsState.status === "ready" && (
          <VariableData
            key={selectedVariable.variable.id}
            variable={variableDetailsState.details}
          />
        )}
    </div>
  );
}

export default LocalDataBankPage;
