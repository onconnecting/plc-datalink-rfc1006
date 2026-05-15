/** @type {import('jest').Config} */
// Integration tests fire real HTTP at a running backend (and indirectly at the
// external ZKS-Mock through it). We intentionally do NOT use jest-preset-angular
// here — these specs are framework-agnostic HTTP contract tests, so testEnvironment
// is 'node' (which has native fetch in Node 22+) and ts-jest handles TS only.
//
// Slower than unit tests — give each test 30 s and run them serially so port
// races don't appear.
module.exports = {
  testEnvironment: 'node',
  testPathIgnorePatterns: ['/node_modules/', '/dist/'],
  moduleFileExtensions: ['ts', 'js'],
  testMatch: ['<rootDir>/test/integration/**/*.spec.ts'],
  testTimeout: 30000,
  maxWorkers: 1,
  transform: {
    '^.+\\.ts$': ['ts-jest', {
      tsconfig: { target: 'ES2022', module: 'CommonJS', esModuleInterop: true },
    }],
  },
};
