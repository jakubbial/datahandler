import { useEffect, useId, useState } from "react";
import { ApiError } from "../api/client";
import { fetchVariableData, type UnitData } from "../api/data";
import { fetchUnits, type Unit } from "../api/units";
import type { VariableDetails } from "../api/variables";

type UnitsResult =
  | { key: string; status: "ready"; units: Unit[] }
  | { key: string; status: "error"; error: unknown };

type DataResult =
  | { key: string; status: "ready"; units: UnitData[] }
  | { key: string; status: "error"; error: unknown };

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 404:
        return "Variable not found.";
      case 409:
        return "Data exceeds one page. Select a voivodeship to narrow the request.";
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

function useUnits(level: 2 | 5, parentId: string | null, enabled: boolean) {
  const [result, setResult] = useState<UnitsResult | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const key = `${level}:${parentId ?? ""}:${retryCount}`;

  useEffect(() => {
    if (!enabled) return;
    let active = true;
    fetchUnits(level, parentId ?? undefined).then(
      (units) => {
        if (active) setResult({ key, status: "ready", units });
      },
      (error: unknown) => {
        if (active) setResult({ key, status: "error", error });
      },
    );
    return () => {
      active = false;
    };
  }, [enabled, key, level, parentId]);

  return {
    state: enabled && result?.key === key ? result : null,
    retry: () => setRetryCount((count) => count + 1),
  };
}

function VariableData({ variable }: { variable: VariableDetails }) {
  const years = [...new Set(variable.years)].sort((a, b) => b - a);
  const [selectedYears, setSelectedYears] = useState(() =>
    years.length > 0 ? [years[0]] : [],
  );
  const [voivodeship, setVoivodeship] = useState("");
  const [filterVoivodeship, setFilterVoivodeship] = useState(false);
  const [displayVoivodeship, setDisplayVoivodeship] = useState("");
  const [filterCounty, setFilterCounty] = useState(false);
  const [county, setCounty] = useState("");
  const [applied, setApplied] = useState<{
    years: number[];
    parentId: string | null;
    revision: number;
  } | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [result, setResult] = useState<DataResult | null>(null);
  const yearsId = useId();
  const needsVoivodeship = variable.level >= 3;
  const voivodeships = useUnits(2, null, needsVoivodeship && filterVoivodeship);
  const counties = useUnits(
    5,
    voivodeship || null,
    variable.level >= 6 && filterCounty && voivodeship !== "",
  );
  const requestKey = `${applied?.revision ?? 0}:${retryCount}`;

  useEffect(() => {
    if (applied === null) {
      return;
    }

    const controller = new AbortController();
    let active = true;
    fetchVariableData(
      variable.id,
      applied.years,
      variable.level,
      applied.parentId,
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
  }, [variable.id, variable.level, applied, requestKey]);

  function toggleYear(year: number) {
    setSelectedYears((current) =>
      current.includes(year)
        ? current.filter((item) => item !== year)
        : [...current, year].sort((a, b) => b - a),
    );
  }

  const currentResult = applied && result?.key === requestKey ? result : null;
  const filtersChanged =
    applied !== null &&
    (applied.parentId !== (county || voivodeship || null) ||
      applied.years.join(",") !== selectedYears.join(",") ||
      (filterVoivodeship && !voivodeship) ||
      (filterCounty && !county));
  const allUnits =
    currentResult?.status === "ready"
      ? [...currentResult.units].sort((a, b) =>
          a.unitId < b.unitId ? -1 : a.unitId > b.unitId ? 1 : 0,
        )
      : [];
  const selectedDisplayVoivodeship = allUnits.some(
    (unit) => unit.unitId === displayVoivodeship,
  )
    ? displayVoivodeship
    : "";
  const units = selectedDisplayVoivodeship
    ? allUnits.filter((unit) => unit.unitId === selectedDisplayVoivodeship)
    : allUnits;

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
          {needsVoivodeship && (
            <div className="mb-3">
              <div className="form-check">
                <input
                  id={`${yearsId}-filter-voivodeship`}
                  className="form-check-input"
                  type="checkbox"
                  checked={filterVoivodeship}
                  onChange={(event) => {
                    setFilterVoivodeship(event.target.checked);
                    setVoivodeship("");
                    setCounty("");
                    setFilterCounty(false);
                  }}
                />
                <label
                  className="form-check-label"
                  htmlFor={`${yearsId}-filter-voivodeship`}
                >
                  Choose a voivodeship
                </label>
              </div>
              {!filterVoivodeship && (
                <p className="small text-body-secondary mb-0">
                  All voivodeships (limited to one BDL request).
                </p>
              )}
              {filterVoivodeship && (
                <>
                  <label
                    className="form-label"
                    htmlFor={`${yearsId}-voivodeship`}
                  >
                    Voivodeship
                  </label>
                  <select
                    id={`${yearsId}-voivodeship`}
                    className="form-select"
                    value={voivodeship}
                    disabled={voivodeships.state?.status !== "ready"}
                    onChange={(event) => {
                      setVoivodeship(event.target.value);
                      setCounty("");
                      setFilterCounty(false);
                    }}
                  >
                    <option value="">Select a voivodeship</option>
                    {voivodeships.state?.status === "ready" &&
                      voivodeships.state.units.map((unit) => (
                        <option key={unit.id} value={unit.id}>
                          {unit.name}
                        </option>
                      ))}
                  </select>
                  {voivodeships.state === null && (
                    <p role="status">Loading voivodeships…</p>
                  )}
                  {voivodeships.state?.status === "error" && (
                    <div role="alert" className="alert alert-danger mt-2">
                      {errorMessage(voivodeships.state.error)}{" "}
                      <button type="button" onClick={voivodeships.retry}>
                        Retry
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
          {variable.level >= 6 && voivodeship && (
            <div className="mb-3">
              <div className="form-check">
                <input
                  id={`${yearsId}-filter-county`}
                  className="form-check-input"
                  type="checkbox"
                  checked={filterCounty}
                  onChange={(event) => {
                    setFilterCounty(event.target.checked);
                    setCounty("");
                  }}
                />
                <label
                  className="form-check-label"
                  htmlFor={`${yearsId}-filter-county`}
                >
                  Narrow to a county
                </label>
              </div>
              {filterCounty && (
                <>
                  <label className="form-label" htmlFor={`${yearsId}-county`}>
                    County
                  </label>
                  <select
                    id={`${yearsId}-county`}
                    className="form-select"
                    value={county}
                    disabled={counties.state?.status !== "ready"}
                    onChange={(event) => setCounty(event.target.value)}
                  >
                    <option value="">Select a county</option>
                    {counties.state?.status === "ready" &&
                      counties.state.units.map((unit) => (
                        <option key={unit.id} value={unit.id}>
                          {unit.name}
                        </option>
                      ))}
                  </select>
                  {counties.state === null && (
                    <p role="status">Loading counties…</p>
                  )}
                  {counties.state?.status === "error" && (
                    <div role="alert" className="alert alert-danger mt-2">
                      {errorMessage(counties.state.error)}{" "}
                      <button type="button" onClick={counties.retry}>
                        Retry
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
          <button
            type="button"
            className="btn btn-primary mb-3"
            disabled={
              (filterVoivodeship && !voivodeship) || (filterCounty && !county)
            }
            onClick={() =>
              setApplied((current) => ({
                years: selectedYears,
                parentId: county || voivodeship || null,
                revision: (current?.revision ?? 0) + 1,
              }))
            }
          >
            Load data
          </button>
          {applied === null && (
            <p role="status" className="text-body-secondary">
              Select filters and load data.
            </p>
          )}
          {applied !== null && currentResult === null && (
            <p role="status">Loading territorial data…</p>
          )}
          {filtersChanged && currentResult !== null && (
            <p role="status" className="text-body-secondary">
              Showing the previous selection. Load data to apply the new
              filters.
            </p>
          )}
          {variable.level === 2 &&
            currentResult?.status === "ready" &&
            allUnits.length > 0 && (
              <div className="mb-3">
                <label
                  className="form-label"
                  htmlFor={`${yearsId}-display-unit`}
                >
                  Voivodeship
                </label>
                <select
                  id={`${yearsId}-display-unit`}
                  className="form-select"
                  value={selectedDisplayVoivodeship}
                  onChange={(event) =>
                    setDisplayVoivodeship(event.target.value)
                  }
                >
                  <option value="">All voivodeships</option>
                  {allUnits.map((unit) => (
                    <option key={unit.unitId} value={unit.unitId}>
                      {unit.unitName}
                    </option>
                  ))}
                </select>
              </div>
            )}
          {currentResult?.status === "error" && (
            <div role="alert" className="alert alert-danger">
              {errorMessage(currentResult.error)}{" "}
              {(!(currentResult.error instanceof ApiError) ||
                ![404, 409, 422].includes(currentResult.error.status)) && (
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
                        {applied?.years.map((year) => (
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
                          {applied?.years.map((year) => {
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
