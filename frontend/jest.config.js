/** @type {import('jest').Config} */
module.exports = {
  preset: 'jest-preset-angular',
  setupFilesAfterEnv: ['<rootDir>/setup-jest.ts'],
  testEnvironment: 'jsdom',
  testPathIgnorePatterns: ['/node_modules/', '/dist/'],
  moduleFileExtensions: ['ts', 'html', 'js', 'mjs'],
  testMatch: ['<rootDir>/test/unit/**/*.spec.ts'],
  collectCoverageFrom: ['src/app/**/*.ts'],
};
