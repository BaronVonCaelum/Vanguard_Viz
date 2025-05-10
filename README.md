# Tableau WDC Date Range Implementation

## Key Changes Made

### In index.html:
1. Replaced the single date input with two date inputs (start and end date)
2. Updated the help text to explain the date range functionality
3. Modified the date preview section to reference date range
4. Added validation for both date fields and their relationship
5. Updated the JavaScript to set default values (one week ago to today)

### In connector.js:
1. Updated the schema to include both startDate and endDate fields
2. Modified the data retrieval process to use both dates in API requests
3. Enhanced validation and error handling for date parameters
4. Updated the connectionData object to store both dates
5. Added phase-specific error handling for missing date parameters
6. Ensured consistent date formatting throughout the connector

These changes enable Tableau users to select a date range for data visualization rather than being limited to a single day, allowing for more comprehensive trend analysis.

## Date Range Usage

The date range feature allows users to:

1. Select a start date and end date for data analysis
2. Visualize trends over time rather than single-day snapshots
3. Compare data across different time periods

### Validation

The date range implementation includes the following validation:

* Both start and end dates are required
* End date must be after start date
* Dates must be in valid format
* Default values are provided (one week ago to today)

### Testing

Basic unit tests have been added in `public/tests/date-validation.js` to verify:

* Valid date range validation
* Invalid date range detection
* Date formatting consistency
* Default date relationship

# Vanguard_Viz
Tableau WDC for dashboard visualizations
