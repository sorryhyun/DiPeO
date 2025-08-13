# DataList (TypeScript, React 18)

A production-ready, reusable DataList scaffold that renders arbitrary item types T with a clean API. Supports:
- Uncontrolled (items) and fetcher-based (pagination) modes
- Tailwind-friendly classNames
- Accessible ARIA roles, keyboard navigation, and RTL-friendly hooks
- Optional virtualization (fixed itemHeight; dynamic heights via itemHeightFn in future)
- SSR/CSR guards and server components readiness markers
- Lazy-loading opportunities for heavy subcomponents (via React.lazy)

Usage patterns

1) Basic usage (uncontrolled)
  DataList<MyItem> props: {
    items: myItems,
    renderItem: (it) => <div className="p-2">{it.label}</div>
  }

2) Fetcher-backed
  DataList<MyItem> props: {
    fetcher: (p) => api.fetchPage(p.page, p.pageSize),
    renderItem: (it) => <div className="p-2">{it.label}</div>,
    itemKey: (it) => it.id
  }

3) Virtualized with fixed item height
  DataList<MyItem> props: {
    items: initialRows,
    height: 600,
    itemHeight: 52,
    virtualized: true,
    renderItem: (it) => <div className="p-2">{it.label}</div>
  }

Design-system alignment notes
- Tailwind CSS-first: pass Tailwind utility classes through className props
- i18n: use t('dataList.loading') keys in UI strings
- RTL support: ensure direction-sensitive layout and focus order when localeAware is true

Tests
- RTL-based unit tests for rendering, keyboard navigation, and ARIA attributes
- Integration tests for fetcher path and error handling
- SSR guards (no window/document access during server render)