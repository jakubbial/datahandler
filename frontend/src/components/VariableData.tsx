import { useEffect, useId, useState } from "react";
import { ApiError } from "../api/client";
import { fetchVariableData, type UnitData } from "../api/data";
import type { VariableDetails } from "../api/variables";

type DataResult =
  | { key: string; status: "ready"; units: UnitData[] }
  | { key: string; status: "error"; error: unknown };

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 404:
        return "Variable not found.";
      case 422:
        return "Invalid data request.";
      case 429:
        return "Too many requests to the BDL API. Please try again in a moment.";
      case 502:
        return "The BDL API is currently unavailable.";
    }
  }
  return "Cannot load data. Check your connection and try again.";
}

function VariableData({ variable }: { variable: VariableDetails }) {
  const years = [...new Set(variable.years)].sort((a, b) => b - a);
  const [selection, setSelection] = useState(() => ({
    years: years.length > 0 ? [years[0]] : [],
    revision: 0,
  }));
  const selectedYears = selection.years;
  const [retryCount, setRetryCount] = useState(0);
  const [result, setResult] = useState<DataResult | null>(null);
  const yearsId = useId();
  const requestKey = `${selection.revision}:${retryCount}`;

  useEffect(() => {
    if (selectedYears.length === 0) {
      return;
    }

    const controller = new AbortController();
    let active = true;
    fetchVariableData(
      variable.id,
      selectedYears,
      variable.level,
      controller.signal,
    ).then(
      (units) => {
        if (active) {
          setResult({ key: requestKey, status: "ready", units });
        }
      },
      (error: unknown) => {
        if (active) {
          setResult({ key: requestKey, status: "error", error });
        }
      },
    );

    return () => {
      active = false;
      controller.abort();
    };
  }, [variable.id, variable.level, selectedYears, requestKey]);

  function toggleYear(year: number) {
    setSelection((current) => ({
      years: current.years.includes(year)
        ? current.years.filter((item) => item !== year)
        : [...current.years, year].sort((a, b) => b - a),
      revision: current.revision + 1,
    }));
  }

  const currentResult = result?.key === requestKey ? result : null;
  const units =
    currentResult?.status === "ready"
      ? [...currentResult.units].sort((a, b) =>
          a.unitId < b.unitId ? -1 : a.unitId > b.unitId ? 1 : 0,
        )
      : [];

  return (
    <section className="mt-4" aria-labelledby={`${yearsId}-title`}>
      <h2 id={`${yearsId}-title`} className="h4">
        Territorial data
      </h2>
      {years.length === 0 ? (
        <p role="status" className="text-body-secondary">
          No years with data.
        </p>
      ) : (
        <>
          <fieldset className="mb-3">
            <legend className="fs-6 mb-1">Years</legend>
            <p className="small text-body-secondary mb-2">
              Select 1 to 30 years.
            </p>
            <div className="d-flex flex-wrap gap-3">
              {years.map((year) => {
                const checked = selectedYears.includes(year);
                return (
                  <div className="form-check" key={year}>
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id={`${yearsId}-${year}`}
                      checked={checked}
                      disabled={
                        checked
                          ? selectedYears.length === 1
                          : selectedYears.length === 30
                      }
                      onChange={() => toggleYear(year)}
                    />
                    <label
                      className="form-check-label"
                      htmlFor={`${yearsId}-${year}`}
                    >
                      {year}
                    </label>
                  </div>
                );
              })}
            </div>
          </fieldset>
          {currentResult === null && (
            <p role="status">Loading territorial data…</p>
          )}
          {currentResult?.status === "error" && (
            <div role="alert" className="alert alert-danger">
              {errorMessage(currentResult.error)}{" "}
              {(!(currentResult.error instanceof ApiError) ||
                ![404, 422].includes(currentResult.error.status)) && (
                <button
                  type="button"
                  className="btn btn-outline-dark btn-sm"
                  onClick={() => setRetryCount((count) => count + 1)}
                >
                  Retry
                </button>
              )}
            </div>
          )}
          {currentResult?.status === "ready" &&
            (units.length === 0 ? (
              <p role="status" className="text-body-secondary">
                No data for the selected years.
              </p>
            ) : (
              <>
                <p className="small text-body-secondary">
                  — indicates a missing value or a value with a non-normal
                  attribute.
                </p>
                <div className="table-responsive">
                  <table className="table table-striped">
                    <thead>
                      <tr>
                        <th scope="col">Unit ID</th>
                        <th scope="col">Unit name</th>
                        {selectedYears.map((year) => (
                          <th key={year} scope="col">
                            {year}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {units.map((unit) => (
                        <tr key={unit.unitId}>
                          <th scope="row">{unit.unitId}</th>
                          <td>{unit.unitName}</td>
                          {selectedYears.map((year) => {
                            const value = unit.values.find(
                              (item) => item.year === year,
                            );
                            return (
                              <td key={year}>
                                {value?.attributeId === 1 &&
                                value.value !== null
                                  ? value.value
                                  : "—"}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ))}
        </>
      )}
    </section>
  );
}

export default VariableData;
