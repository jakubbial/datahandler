import type { Variable } from "../api/variables";

const nameSeparator = " - ";

export type VariableGroup = {
  // null for variables whose name has no separator; such groups have no heading.
  title: string | null;
  items: { variable: Variable; label: string }[];
};

export function normalizeText(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/ł/g, "l")
    .replace(/Ł/g, "L")
    .toLowerCase();
}

export function groupVariables(variables: Variable[]): VariableGroup[] {
  const groups: VariableGroup[] = [];
  const groupsByTitle = new Map<string, VariableGroup>();

  for (const variable of variables) {
    const separatorIndex = variable.name.indexOf(nameSeparator);
    if (separatorIndex === -1) {
      const previous = groups[groups.length - 1];
      if (previous && previous.title === null) {
        previous.items.push({ variable, label: variable.name });
      } else {
        groups.push({
          title: null,
          items: [{ variable, label: variable.name }],
        });
      }
      continue;
    }

    const title = variable.name.slice(0, separatorIndex);
    const label = variable.name.slice(separatorIndex + nameSeparator.length);
    let group = groupsByTitle.get(title);
    if (!group) {
      group = { title, items: [] };
      groupsByTitle.set(title, group);
      groups.push(group);
    }
    group.items.push({ variable, label });
  }

  return groups;
}
