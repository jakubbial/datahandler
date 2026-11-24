import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { fetchSubjects, type Subject } from "../api/subjects";
import { parseSegment } from "../utils/subjectPath";

export type SubjectsErrorKind =
  "invalid-id" | "not-found" | "rate-limit" | "unavailable" | "unknown";

export type SubjectPathState =
  | { status: "loading" }
  | { status: "error"; error: SubjectsErrorKind }
  | {
      status: "ready";
      breadcrumb: Subject[];
      items: Subject[];
      selected: Subject | null;
    };

const subjectsCache = new Map<string, Promise<Subject[]>>();

function loadSubjects(parentId: string | null): Promise<Subject[]> {
  const key = parentId ?? "";
  const cached = subjectsCache.get(key);
  if (cached) {
    return cached;
  }

  const request = fetchSubjects(parentId);
  subjectsCache.set(key, request);
  // Failed requests must not stay cached, so a retry sends a new request.
  request.catch(() => {
    if (subjectsCache.get(key) === request) {
      subjectsCache.delete(key);
    }
  });
  return request;
}

class SubjectNotFoundError extends Error {}

function toErrorKind(error: unknown): SubjectsErrorKind {
  if (error instanceof SubjectNotFoundError) {
    return "not-found";
  }
  if (error instanceof ApiError) {
    switch (error.status) {
      case 404:
        return "not-found";
      case 422:
        return "invalid-id";
      case 429:
        return "rate-limit";
      case 502:
        return "unavailable";
    }
  }
  return "unknown";
}

async function resolvePath(ids: string[]) {
  const breadcrumb: Subject[] = [];
  let items = await loadSubjects(null);

  for (const [index, id] of ids.entries()) {
    const subject = items.find((item) => item.id === id);
    if (!subject) {
      throw new SubjectNotFoundError();
    }

    if (subject.hasVariables) {
      // A subject with variables is a leaf: it can only be the last segment.
      if (index !== ids.length - 1) {
        throw new SubjectNotFoundError();
      }
      return { breadcrumb, items, selected: subject };
    }

    breadcrumb.push(subject);
    items = await loadSubjects(subject.id);
  }

  return { breadcrumb, items, selected: null };
}

export function useSubjectPath(segments: string[]) {
  const pathKey = segments.join("/");
  const [result, setResult] = useState<{
    pathKey: string;
    state: SubjectPathState;
  } | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let isActive = true;
    const ids = pathKey ? pathKey.split("/").map(parseSegment) : [];

    if (ids.some((id) => id === null)) {
      setResult({ pathKey, state: { status: "error", error: "invalid-id" } });
      return;
    }

    setResult(null);
    resolvePath(ids as string[]).then(
      (resolved) => {
        if (isActive) {
          setResult({ pathKey, state: { status: "ready", ...resolved } });
        }
      },
      (error: unknown) => {
        if (isActive) {
          setResult({
            pathKey,
            state: { status: "error", error: toErrorKind(error) },
          });
        }
      },
    );

    return () => {
      isActive = false;
    };
  }, [pathKey, retryCount]);

  const retry = useCallback(() => setRetryCount((count) => count + 1), []);

  // A result for a previous path must not be shown after the path changes.
  const state: SubjectPathState =
    result && result.pathKey === pathKey ? result.state : { status: "loading" };

  return { state, retry };
}
