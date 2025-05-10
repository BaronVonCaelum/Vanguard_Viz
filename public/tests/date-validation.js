// Simple unit tests for date validation logic
(function() {
  console.log("Running date validation tests...");
  
  function runTests() {
    testValidDateRange();
    testInvalidDateRange();
    testDateFormatting();
    testDefaultDates();
    console.log("All tests complete!");
  }
  
  function testValidDateRange() {
    console.log("Testing valid date range...");
    const startDate = "2025-05-01";
    const endDate = "2025-05-10";
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (!(end >= start)) {
      console.error("FAIL: Valid date range test failed");
    } else {
      console.log("PASS: Valid date range test passed");
    }
  }
  
  function testInvalidDateRange() {
    console.log("Testing invalid date range...");
    const startDate = "2025-05-10";
    const endDate = "2025-05-01";
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (end >= start) {
      console.error("FAIL: Invalid date range test failed");
    } else {
      console.log("PASS: Invalid date range test passed");
    }
  }
  
  function testDateFormatting() {
    console.log("Testing date formatting...");
    const date = new Date(2025, 4, 10); // May 10, 2025
    const formatted = date.toISOString().split('T')[0];
    
    if (formatted !== "2025-05-10") {
      console.error("FAIL: Date formatting test failed");
    } else {
      console.log("PASS: Date formatting test passed");
    }
  }
  
  function testDefaultDates() {
    console.log("Testing default dates...");
    const today = new Date();
    const weekAgo = new Date(today);
    weekAgo.setDate(today.getDate() - 7);
    
    if (weekAgo > today) {
      console.error("FAIL: Default dates test failed");
    } else {
      console.log("PASS: Default dates test passed");
    }
  }
  
  // Run tests when loaded
  if (typeof QUnit !== 'undefined') {
    // If QUnit is available, integrate with it
    QUnit.module("Date Validation");
    
    QUnit.test("Valid date range", function(assert) {
      const startDate = "2025-05-01";
      const endDate = "2025-05-10";
      const start = new Date(startDate);
      const end = new Date(endDate);
      assert.ok(end >= start, "End date should be after start date");
    });
    
    QUnit.test("Invalid date range", function(assert) {
      const startDate = "2025-05-10";
      const endDate = "2025-05-01";
      const start = new Date(startDate);
      const end = new Date(endDate);
      assert.notOk(end >= start, "End date should not be before start date");
    });
  } else {
    // Otherwise run console tests
    runTests();
  }
})();

