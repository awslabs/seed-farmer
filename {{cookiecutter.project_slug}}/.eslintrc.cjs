// See https://w.amazon.com/bin/view/AWS/Teams/Proserve/CustomerEngineering/Assets/ProcessesAndTemplates/Standards/TypeScript/#HStaticAnalyzers

module.exports = {
  root: true,
  parser: "@typescript-eslint/parser",
  parserOptions: {
    project: ["tsconfig.json"],
  },
  plugins: ["@typescript-eslint"],
  extends: [
    "plugin:@typescript-eslint/strict-type-checked",
    "plugin:@typescript-eslint/stylistic-type-checked",
    "plugin:import/recommended",
    "plugin:import/typescript",
    "plugin:prettier/recommended",
    "eslint-config-prettier",
  ],
  overrides: [
    {
      files: ["*.md", "*.mdx"],
      extends: ["plugin:mdx/recommended"],
    },
  ],
  // For the list of rules supported by @typescript-eslint/eslint-plugin,
  // see: https://typescript-eslint.io/rules/
  rules: {},
  settings: {
    "import/resolver": {
      typescript: {
        // Always try to resolve types under `<root>@types` directory even
        // it doesn't contain any source code, like `@types/aws-lambda`
        alwaysTryTypes: true,
      },
    },
  },
};
