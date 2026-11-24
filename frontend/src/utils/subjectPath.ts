import type { Subject } from "../api/subjects";

const subjectIdPattern = /^[A-Za-z0-9]{1,16}$/;
const maxSlugLength = 60;

export function toSlug(name: string): string {
  return name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/ł/g, "l")
    .replace(/Ł/g, "L")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .slice(0, maxSlugLength)
    .replace(/^-+|-+$/g, "");
}

export function toSegment(subject: Subject): string {
  const slug = toSlug(subject.name);
  return slug ? `${subject.id}-${slug}` : subject.id;
}

export const localDataBankBasePath = "/local-data-bank";

export function buildSubjectPath(subjects: Subject[]): string {
  return [localDataBankBasePath, ...subjects.map(toSegment)].join("/");
}

export function parseSegment(segment: string): string | null {
  const id = segment.split("-", 1)[0];
  return subjectIdPattern.test(id) ? id : null;
}
