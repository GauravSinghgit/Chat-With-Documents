import nextConfig from "eslint-config-next";

/** @type {import('eslint').Linter.Config[]} */
const config = [
  ...nextConfig,
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "test-results/**",
      "playwright-report/**",
      "coverage/**",
    ],
  },
  {
    rules: {
      // This rule (new in eslint-plugin-react-hooks v7) flags the standard
      // "fetch data on mount" pattern — an idiomatic, React-docs-endorsed
      // use of useEffect, not an actual cascading-render bug. Downgraded
      // to a warning rather than forcing a refactor of working data-fetch
      // effects (ChatSidebar, DocumentsPage, AdminPage, ChatInterface).
      "react-hooks/set-state-in-effect": "warn",
    },
  },
];

export default config;
