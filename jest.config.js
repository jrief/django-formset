/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  preset: 'ts-jest',
  modulePaths: [
    '<rootDir>/client/'
  ],
  testEnvironment: 'node',
  testMatch: [
    '<rootDir>/client/tests/*.test.ts'
  ]
};
