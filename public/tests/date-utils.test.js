/**
 * @fileoverview Tests for date utility functions
 */

// Import or use DateUtils based on environment
const DateUtils = typeof require !== 'undefined' ? 
  require('./date-utils.js') : window.DateUtils;

// Simple test runner
function runTests() {
  const testResults = [
    testIsValidDate(),
    testIsValidDateRange(),
    testFormatDate(),
    testGetDateRangeForPastDays()
  ];
  
  const passed = testResults.filter(result => result).length;
  const total = testResults.length;
  
  console.log(`Tests complete: ${passed}/${total} passed`);
  
  return passed === total;
}

// Test isValidDate function
function testIsValidDate() {
  console.log("Testing isValidDate...");
  
  const validTests = [
    DateUtils.isValidDate("2025-05-10"),
    DateUtils.isValidDate("2020-01-01"),
    DateUtils.isValidDate(new Date().toISOString().split('T')[0])
  ];
  
  const invalidTests = [
    !DateUtils.isValidDate(""),
    !DateUtils.isValidDate("not-a-date"),
    !DateUtils.isValidDate("2020/13/45")
  ];
  
  const allTests = [...validTests, ...invalidTests];
  const passed = allTests.every(result => result === true);
  
  console.log(passed ? "PASS: isValidDate tests" : "FAIL: isValidDate tests");
  return passed;
}

// Test isValidDateRange function
function testIsValidDateRange() {
  console.log("Testing isValidDateRange...");
  
  const validTests = [
    DateUtils.isValidDateRange("2025-05-01", "2025-05-10"),
    DateUtils.isValidDateRange("2020-01-01", "2025-01-01")
  ];
  
  const invalidTests = [
    !DateUtils.isValidDateRange("2025-05-10", "2025-05-01"), // End before start
    !DateUtils.isValidDateRange("", "2025-05-10"),           // Missing start
    !DateUtils.isValidDateRange("2025-05-01", ""),           // Missing end
    !DateUtils.isValidDateRange("bad-date", "2025-05-10")    // Invalid date
  ];
  
  const allTests = [...validTests, ...invalidTests];
  const passed = allTests.every(result => result === true);
  
  console.log(passed ? "PASS: isValidDateRange tests" : "FAIL: isValidDateRange tests");
  return passed;
}

// Test formatDate function
function testFormatDate() {
  console.log("Testing formatDate...");
  
  const date = new Date(2025, 4, 10); // May 10, 2025
  const formatted = DateUtils.formatDate(date);
  const passed = formatted === "2025-05-10";
  
  console.log(passed ? "PASS: formatDate test" : "FAIL: formatDate test");
  return passed;
}

// Test getDateRangeForPastDays function
function testGetDateRangeForPastDays() {
  console.log("Testing getDateRangeForPastDays...");
  
  const range = DateUtils.getDateRangeForPastDays(7);
  
  // Check both dates are present and properly formatted
  const hasProperties = range.startDate && range.endDate;
  
  // Check the range is valid
  const isValid = DateUtils.isValidDateRange(range.startDate, range.endDate);
  
  // Check that start date is 7 days before end date
  const startDate = new Date(range.startDate);
  const endDate = new Date(range.endDate);
  const daysDiff = Math.round((endDate - startDate) / (1000 * 60 * 60 * 24));
  
  const passed = hasProperties && isValid && daysDiff === 7;
  
  console.log(passed ? "PASS: getDateRangeForPastDays test" : "FAIL: getDateRangeForPastDays test");
  return passed;
}

// Run tests automatically if in a browser environment
if (typeof window !== 'undefined') {
  document.addEventListener('DOMContentLoaded', runTests);
}

// Export for Node.js environment
if (typeof module !== 'undefined' && module.exports) {
  module.exports = runTests;
}

