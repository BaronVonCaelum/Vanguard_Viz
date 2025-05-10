/**
 * @fileoverview Date utilities for reuse across the application.
 * This provides common date functions needed for the date range feature.
 */

const DateUtils = {
  /**
   * Validates that a date string is in a valid format
   * @param {string} dateStr - The date string to validate
   * @returns {boolean} True if the date is valid
   */
  isValidDate: function(dateStr) {
    if (!dateStr) return false;
    const date = new Date(dateStr);
    return !isNaN(date.getTime());
  },

  /**
   * Validates that end date comes after start date
   * @param {string} startDate - The start date string
   * @param {string} endDate - The end date string
   * @returns {boolean} True if the date range is valid
   */
  isValidDateRange: function(startDate, endDate) {
    if (!this.isValidDate(startDate) || !this.isValidDate(endDate)) {
      return false;
    }
    return new Date(endDate) > new Date(startDate);
  },

  /**
   * Formats a Date object to YYYY-MM-DD string
   * @param {Date} date - The date to format
   * @returns {string} Formatted date string
   */
  formatDate: function(date) {
    return date.toISOString().split('T')[0];
  },

  /**
   * Gets a date range for the past N days
   * @param {number} days - Number of days to go back
   * @returns {Object} Object with startDate and endDate properties
   */
  getDateRangeForPastDays: function(days) {
    const endDate = new Date();
    const startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - days);
    
    return {
      startDate: this.formatDate(startDate),
      endDate: this.formatDate(endDate)
    };
  }
};

// Make this available for both browser and Node.js environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DateUtils;
} else if (typeof window !== 'undefined') {
  window.DateUtils = DateUtils;
}

