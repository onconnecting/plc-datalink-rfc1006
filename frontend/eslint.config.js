// @ts-check
const eslint = require('@eslint/js');
const tseslint = require('typescript-eslint');
const angular = require('angular-eslint');

module.exports = tseslint.config(
  {
    ignores: ['dist/**', 'node_modules/**', '.angular/**', 'out-tsc/**'],
  },
  {
    files: ['**/*.ts'],
    extends: [
      eslint.configs.recommended,
      ...tseslint.configs.recommended,
      ...tseslint.configs.stylistic,
      ...angular.configs.tsRecommended,
    ],
    processor: angular.processInlineTemplates,
    languageOptions: {
      parserOptions: {
        project: ['tsconfig.app.json'],
        tsconfigRootDir: __dirname,
      },
    },
    rules: {
      '@angular-eslint/component-selector': [
        'error',
        { type: 'element', prefix: 'oc', style: 'kebab-case' },
      ],
      '@angular-eslint/directive-selector': [
        'error',
        { type: 'attribute', prefix: 'oc', style: 'camelCase' },
      ],
      '@angular-eslint/prefer-standalone': 'error',
      '@typescript-eslint/no-explicit-any': 'error',
      'no-console': ['warn', { allow: ['warn', 'error'] }],
    },
  },
  {
    files: ['**/*.html'],
    extends: [
      ...angular.configs.templateRecommended,
      ...angular.configs.templateAccessibility,
    ],
    rules: {},
  }
);
