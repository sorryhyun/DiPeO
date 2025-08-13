import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { DataList } from "../DataList";

// Minimal mock data
type Item = { id: string; name: string };

function renderBasicList(items: Item[]) {
  return render(
    <DataList<Item>
      items={items}
      renderItem={(it) => <div data-testid="item" className="item">{it.name}</div>}
      ariaLabel="Test list"
      itemKey={(it) => it.id}
    />
  );
}

// Basic render test
test("renders items via renderItem", () => {
  const items: Item[] = [
    { id: "a", name: "Alpha" },
    { id: "b", name: "Beta" },
    { id: "c", name: "Gamma" },
  ];
  renderBasicList(items);
  // We render items via renderItem
  expect(screen.getAllByTestId("item").length).toBe(3);
});

// Keyboard navigation scaffold (focusable items)
test("keyboard navigation can focus items within viewport", () => {
  const items: Item[] = Array.from({ length: 12 }).map((_, i) => ({
    id: `i${i}`,
    name: `Item ${i}`,
  }));
  const { container } = render(
    <DataList<Item>
      items={items}
      renderItem={(it) => <div data-testid={`row-${it.id}`}>{it.name}</div>}
      ariaLabel="Demo list"
      itemKey={(it) => it.id}
      pageSize={20}
    />
  );

  // Focus move simulation (simple: move focus to first item)
  const first = container.querySelector('[data-testid="row-i0"]');
  if (first) (first as HTMLElement).focus();
  expect(document.activeElement).toBe(first);
});

// Infinite loading via fetcher
test("loads via fetcher when provided", async () => {
  type User = { id: string; name: string };
  const fetcher = async ({ page, pageSize }: { page: number; pageSize: number }): Promise<User[]> => {
    // emulate 2 items per page
    const start = (page - 1) * pageSize;
    const list = Array.from({ length: pageSize }).map((_, i) => ({
      id: `u${start + i}`,
      name: `User ${start + i}`,
    }));
    return new Promise((resolve) => setTimeout(() => resolve(list), 10));
  };

  const { getByText, getByRole, getAllByTestId } = render(
    <DataList<User>
      items={[]}
      renderItem={(u) => <div data-testid={`user-${u.id}`}>{u.name}</div>}
      ariaLabel="Users"
      fetcher={fetcher}
      pageSize={4}
    />
  );

  // First page loads
  await waitFor(() => expect(getAllByTestId(/user-u/).length).toBeGreaterThan(0));

  // Load more
  const loadMoreBtn = getByRole("button", { name: /Load more/i });
  fireEvent.click(loadMoreBtn);
  await waitFor(() => expect(getAllByTestId(/user-u/).length).toBeGreaterThan(4));
});

// Resource cleanup and error boundary example would require more elaborate setup.
// This test file is a starting scaffold and can be extended to cover ErrorBoundary and SSR hydration.