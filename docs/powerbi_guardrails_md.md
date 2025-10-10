# Power BI HTML Visualization Guardrails v2.0

**Version:** 2.0  
**Last Updated:** October 2025  
**Purpose:** Comprehensive standards for production-quality Power BI custom HTML visuals with maximum flexibility

---

## Core Philosophy

These guardrails maximize creative freedom while ensuring accessibility, performance, and Power BI compatibility. All rules include rationale and practical examples to guide implementation decisions.

---

## Quick Start Checklist

Before creating any Power BI HTML visualization, ensure:

- ✓ Single HTML file with inline CSS/JS
- ✓ No localStorage/sessionStorage usage
- ✓ Responsive grid/flexbox layout
- ✓ WCAG AA contrast ratios (4.5:1 minimum)
- ✓ Financial formatting with Intl.NumberFormat
- ✓ Keyboard navigation support
- ✓ Loading states for operations >200ms
- ✓ Test at 1920x1080, 1366x768, 3840x1080 (ultrawide)

---

## 1. Foundation & Architecture
**Priority:** CRITICAL

### F1: Single HTML File Structure

**Requirement:** All HTML, CSS, and JavaScript in ONE file - no external dependencies except CDN libraries

**Example:**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    /* All CSS here */
    body { margin: 0; padding: 0; }
  </style>
</head>
<body>
  <!-- Content -->
  <script>
    // All JS here
  </script>
</body>
</html>
```

**Rationale:** Power BI Custom Visuals iframe limitation prevents external file references

---

### F2: Responsive Design Required

**Requirement:** Use CSS Grid/Flexbox with min-width constraints, test at multiple resolutions

**Target Resolutions:**
- Standard HD: 1920x1080
- Laptop: 1366x768
- Ultrawide: 3840x1080

**Example:**
```css
.container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  padding: 1rem;
}

/* Ultrawide optimization */
@media (min-width: 2560px) {
  .container {
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    max-width: 3840px;
  }
}

/* Tablet/laptop */
@media (max-width: 1366px) {
  .container {
    grid-template-columns: 1fr;
  }
}
```

**Rationale:** Multi-monitor and varying resolution support across different user environments

---

### F3: No External Storage APIs

**Requirement:** NEVER use localStorage, sessionStorage, IndexedDB, or cookies. Use JavaScript objects/arrays only.

**Example:**
```javascript
// ❌ BAD - Will fail in Power BI iframe
localStorage.setItem('userPrefs', JSON.stringify(prefs));
sessionStorage.setItem('filters', JSON.stringify(filters));

// ✅ GOOD - In-memory state management
const appState = {
  userPrefs: { theme: 'dark', currency: 'USD' },
  filters: { period: 'YTD', region: 'EMEA' },
  cachedData: []
};

function updateState(key, value) {
  appState[key] = value;
  render();
}
```

**Rationale:** Browser storage APIs are blocked in Power BI iframe environment for security

---

## 2. Visual Design & Theming
**Priority:** HIGH

### V1: Corporate Color Palette

**Requirement:** Define primary/secondary/accent colors with semantic meaning. Support light/dark themes.

**Example:**
```css
:root {
  /* Primary colors */
  --primary: #0078D4;
  --primary-hover: #106EBE;
  --secondary: #50E6FF;
  --accent: #8764B8;
  
  /* Semantic colors */
  --success: #107C10;
  --warning: #FFB900;
  --danger: #D13438;
  --info: #00BCF2;
  
  /* Backgrounds */
  --bg-primary: #FFFFFF;
  --bg-secondary: #F3F2F1;
  --bg-tertiary: #EDEBE9;
  
  /* Text colors */
  --text-primary: #323130;
  --text-secondary: #605E5C;
  --text-tertiary: #8A8886;
  --text-inverse: #FFFFFF;
  
  /* Borders */
  --border-color: #D2D0CE;
  --border-hover: #8A8886;
}

/* Dark theme */
[data-theme="dark"] {
  --bg-primary: #1B1A19;
  --bg-secondary: #252423;
  --bg-tertiary: #2D2C2B;
  --text-primary: #FFFFFF;
  --text-secondary: #D2D0CE;
  --text-tertiary: #A19F9D;
  --border-color: #3B3A39;
}
```

**Rationale:** Consistent branding and accessibility across all visualizations

---

### V2: WCAG AA Compliance

**Requirement:** Minimum 4.5:1 contrast for normal text, 3:1 for large text (18pt+), 3:1 for UI components

**Contrast Requirements:**
- Normal text: 4.5:1
- Large text (18pt/14pt bold): 3:1
- UI components & borders: 3:1
- Disabled state: No minimum (but indicate clearly)

**Example:**
```css
/* High contrast pairs - WCAG AA compliant */
.dark-bg { 
  background: #1B1A19; 
  color: #FFFFFF; 
} /* 15.3:1 ✓ */

.primary-btn { 
  background: #0078D4; 
  color: #FFFFFF; 
} /* 4.6:1 ✓ */

.success-indicator { 
  background: #107C10; 
  color: #FFFFFF; 
} /* 4.5:1 ✓ */

.warning-bg { 
  background: #FFB900; 
  color: #323130; 
} /* 7.2:1 ✓ */

/* Avoid these combinations */
.bad-contrast { 
  background: #FFB900; 
  color: #FFFFFF; 
} /* 1.9:1 ✗ Fails WCAG */
```

**Testing Tools:**
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- Chrome DevTools: Inspect > Accessibility > Contrast

**Rationale:** Accessibility for all users including those with colorblindness or visual impairments

---

### V3: Financial Data Formatting

**Requirement:** Use Intl.NumberFormat for currency, percentages, and large numbers. Show negatives in parentheses with red color.

**Example:**
```javascript
// Currency formatting
const formatCurrency = (value, currency = 'USD', locale = 'en-US') => {
  const abs = Math.abs(value);
  const formatted = new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(abs).replace(/[A-Z$€£¥]/g, '').trim();
  
  return value < 0 ? `(${formatted})` : formatted;
};

// Percentage formatting
const formatPercent = (value, decimals = 0) => {
  const abs = Math.abs(value);
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(abs);
  
  return value < 0 ? `(${formatted})` : formatted;
};

// Large number formatting with abbreviations
const formatLargeNumber = (value) => {
  const abs = Math.abs(value);
  let formatted;
  
  if (abs >= 1e12) {
    formatted = (abs / 1e12).toFixed(1) + 'T';
  } else if (abs >= 1e9) {
    formatted = (abs / 1e9).toFixed(1) + 'B';
  } else if (abs >= 1e6) {
    formatted = (abs / 1e6).toFixed(1) + 'M';
  } else if (abs >= 1e3) {
    formatted = (abs / 1e3).toFixed(1) + 'K';
  } else {
    formatted = abs.toFixed(0);
  }
  
  return value < 0 ? `(${formatted})` : formatted;
};

// Example usage
console.log(formatCurrency(1234567));      // "1,234,567"
console.log(formatCurrency(-1234567));     // "(1,234,567)"
console.log(formatPercent(0.1543, 1));     // "15.4%"
console.log(formatPercent(-0.0789, 2));    // "(7.89%)"
console.log(formatLargeNumber(2500000));   // "2.5M"
```

**CSS for negative values:**
```css
.negative {
  color: var(--danger);
}

.positive {
  color: var(--success);
}
```

**Rationale:** Standard financial reporting conventions for consistent data presentation

---

### V4: Typography Hierarchy

**Requirement:** Use system font stack. Scale: H1(24-28px), H2(20-24px), H3(16-18px), Body(14px), Small(12px)

**Example:**
```css
body {
  font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', 
               'Helvetica Neue', Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-primary);
}

h1 {
  font-size: 24px;
  font-weight: 600;
  line-height: 1.3;
  margin: 0 0 16px 0;
  color: var(--text-primary);
}

h2 {
  font-size: 20px;
  font-weight: 600;
  line-height: 1.4;
  margin: 0 0 12px 0;
  color: var(--text-primary);
}

h3 {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
  margin: 0 0 8px 0;
  color: var(--text-secondary);
}

.body-text {
  font-size: 14px;
  font-weight: 400;
  line-height: 1.5;
}

.small-text {
  font-size: 12px;
  font-weight: 400;
  line-height: 1.4;
  color: var(--text-secondary);
}

.label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-tertiary);
}

/* Financial metrics - monospace for alignment */
.metric-value {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  font-weight: 400;
  text-align: right;
}
```

**Rationale:** Readability and visual hierarchy for financial data

---

## 3. Data Handling & Performance
**Priority:** CRITICAL

### D1: Data Binding Pattern

**Requirement:** Use data attributes for binding. Avoid inline event handlers. Separate data from presentation.

**Example:**
```html
<!-- Data layer -->
<div class="metric-card" 
     data-value="1234567" 
     data-prior="987654"
     data-variance="0.2499"
     data-format="currency"
     data-metric-id="net-turnover">
  <!-- Rendered via JS -->
</div>

<script>
// Presentation layer
function renderMetricCard(element) {
  const value = parseFloat(element.dataset.value);
  const prior = parseFloat(element.dataset.prior);
  const variance = parseFloat(element.dataset.variance);
  const format = element.dataset.format;
  
  const formattedValue = format === 'currency' 
    ? formatCurrency(value) 
    : formatPercent(value);
  
  const formattedVariance = formatPercent(variance, 1);
  const varianceClass = variance >= 0 ? 'positive' : 'negative';
  
  element.innerHTML = `
    <div class="metric-label">${element.dataset.metricId}</div>
    <div class="metric-value">${formattedValue}</div>
    <div class="metric-variance ${varianceClass}">
      ${formattedVariance}
      <span class="arrow">${variance >= 0 ? '▲' : '▼'}</span>
    </div>
  `;
}

// Initialize all metrics
document.querySelectorAll('.metric-card').forEach(renderMetricCard);

// Event delegation (not inline handlers)
document.addEventListener('click', (e) => {
  const metricCard = e.target.closest('.metric-card');
  if (metricCard) {
    handleMetricClick(metricCard.dataset.metricId);
  }
});
</script>
```

**Rationale:** Maintainability, separation of concerns, and easier debugging

---

### D2: Virtual Scrolling for Large Datasets

**Requirement:** For tables with 100+ rows, implement virtual scrolling or pagination

**Example:**
```javascript
class VirtualScroller {
  constructor(container, data, rowHeight = 40) {
    this.container = container;
    this.data = data;
    this.rowHeight = rowHeight;
    this.visibleRows = Math.ceil(container.clientHeight / rowHeight) + 2;
    this.scrollTop = 0;
    
    this.init();
  }
  
  init() {
    // Create viewport
    this.viewport = document.createElement('div');
    this.viewport.style.height = `${this.data.length * this.rowHeight}px`;
    this.viewport.style.position = 'relative';
    
    // Create content container
    this.content = document.createElement('div');
    this.content.style.position = 'absolute';
    this.content.style.top = '0';
    this.content.style.width = '100%';
    
    this.viewport.appendChild(this.content);
    this.container.appendChild(this.viewport);
    
    // Add scroll listener
    this.container.addEventListener('scroll', () => this.onScroll());
    
    // Initial render
    this.render();
  }
  
  onScroll() {
    this.scrollTop = this.container.scrollTop;
    this.render();
  }
  
  render() {
    const startIndex = Math.floor(this.scrollTop / this.rowHeight);
    const endIndex = Math.min(startIndex + this.visibleRows, this.data.length);
    
    // Clear and render visible rows
    this.content.innerHTML = '';
    this.content.style.top = `${startIndex * this.rowHeight}px`;
    
    for (let i = startIndex; i < endIndex; i++) {
      const row = this.createRow(this.data[i], i);
      this.content.appendChild(row);
    }
  }
  
  createRow(data, index) {
    const row = document.createElement('div');
    row.className = 'virtual-row';
    row.style.height = `${this.rowHeight}px`;
    row.innerHTML = `
      <div class="col">${data.account}</div>
      <div class="col">${formatCurrency(data.actual)}</div>
      <div class="col">${formatCurrency(data.variance)}</div>
    `;
    return row;
  }
}

// Usage
const scroller = new VirtualScroller(
  document.getElementById('table-container'),
  largeDataset,
  40
);
```

**Alternative: Pagination**
```javascript
const ROWS_PER_PAGE = 50;
let currentPage = 1;

function renderPage(page) {
  const start = (page - 1) * ROWS_PER_PAGE;
  const end = start + ROWS_PER_PAGE;
  const pageData = data.slice(start, end);
  
  const tbody = document.querySelector('tbody');
  tbody.innerHTML = pageData.map(row => `
    <tr>
      <td>${row.account}</td>
      <td>${formatCurrency(row.actual)}</td>
      <td>${formatCurrency(row.variance)}</td>
    </tr>
  `).join('');
  
  updatePagination(page, Math.ceil(data.length / ROWS_PER_PAGE));
}
```

**Rationale:** Performance optimization for large financial models (190+ locations, thousands of accounts)

---

### D3: Debounce User Interactions

**Requirement:** Debounce search, filter, and resize events (250-500ms)

**Example:**
```javascript
// Utility function
const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Search input
const searchInput = document.getElementById('search');
const handleSearch = debounce((query) => {
  const results = data.filter(item => 
    item.account.toLowerCase().includes(query.toLowerCase())
  );
  renderTable(results);
}, 300);

searchInput.addEventListener('input', (e) => {
  handleSearch(e.target.value);
});

// Window resize
const handleResize = debounce(() => {
  recalculateLayout();
  updateCharts();
}, 250);

window.addEventListener('resize', handleResize);

// Filter changes
const handleFilterChange = debounce((filters) => {
  const filtered = applyFilters(data, filters);
  updateAllVisuals(filtered);
}, 500);
```

**Rationale:** Prevent excessive DOM manipulation and calculation overhead

---

## 4. Interactivity & User Experience
**Priority:** HIGH

### I1: State Management

**Requirement:** Use single state object with clear update pattern. Document state shape.

**Example:**
```javascript
/**
 * Application state shape
 * @typedef {Object} AppState
 * @property {Object} filters - Active filter selections
 * @property {string} filters.period - Time period (MTD, QTD, YTD, etc.)
 * @property {string} filters.month - Selected month
 * @property {string} filters.fiscalYear - Fiscal year
 * @property {string[]} filters.locations - Selected locations
 * @property {string} view - Current view mode (matrix, chart, detail)
 * @property {Object} sort - Sort configuration
 * @property {string} sort.column - Column to sort by
 * @property {string} sort.direction - Sort direction (asc, desc)
 * @property {string[]} selectedItems - Selected row/item IDs
 * @property {Object} expandedRows - Map of expanded row states
 * @property {boolean} isLoading - Loading state indicator
 * @property {string|null} error - Error message if any
 */

const state = {
  filters: {
    period: 'YTD',
    month: 'MAY 25',
    fiscalYear: 'FY',
    locations: []
  },
  view: 'matrix',
  sort: {
    column: 'account',
    direction: 'asc'
  },
  selectedItems: [],
  expandedRows: {},
  isLoading: false,
  error: null
};

/**
 * Update state and trigger re-render
 * @param {Partial<AppState>} updates - State updates to apply
 */
function updateState(updates) {
  // Deep merge for nested objects
  if (updates.filters) {
    state.filters = { ...state.filters, ...updates.filters };
    delete updates.filters;
  }
  if (updates.sort) {
    state.sort = { ...state.sort, ...updates.sort };
    delete updates.sort;
  }
  
  // Apply remaining updates
  Object.assign(state, updates);
  
  // Persist critical state (in-memory only)
  saveStateSnapshot();
  
  // Trigger re-render
  render();
}

// State snapshot for undo functionality
const stateHistory = [];
const MAX_HISTORY = 10;

function saveStateSnapshot() {
  stateHistory.push(JSON.parse(JSON.stringify(state)));
  if (stateHistory.length > MAX_HISTORY) {
    stateHistory.shift();
  }
}

function undo() {
  if (stateHistory.length > 1) {
    stateHistory.pop(); // Remove current
    const previous = stateHistory[stateHistory.length - 1];
    Object.assign(state, previous);
    render();
  }
}
```

**Rationale:** Predictable state changes, easier debugging, and undo/redo support

---

### I2: Loading & Error States

**Requirement:** Show loading indicators for calculations >200ms. Display user-friendly error messages.

**Example:**
```html
<!-- Loading overlay -->
<div id="loading-overlay" class="loading-overlay" style="display: none;">
  <div class="spinner"></div>
  <p class="loading-text">Calculating variance analysis...</p>
</div>

<!-- Error message -->
<div id="error-message" class="error-message" style="display: none;">
  <div class="error-content">
    <span class="error-icon">⚠️</span>
    <div>
      <strong class="error-title">Unable to load data</strong>
      <p class="error-description"></p>
    </div>
    <button class="error-close" onclick="closeError()">×</button>
  </div>
</div>

<style>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  color: white;
  margin-top: 16px;
  font-size: 14px;
}

.error-message {
  position: fixed;
  top: 20px;
  right: 20px;
  max-width: 400px;
  background: var(--bg-primary);
  border: 1px solid var(--danger);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.error-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.error-icon {
  font-size: 24px;
}

.error-title {
  color: var(--danger);
  font-size: 14px;
  display: block;
  margin-bottom: 4px;
}

.error-description {
  color: var(--text-secondary);
  font-size: 13px;
  margin: 0;
}

.error-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0;
  line-height: 1;
  margin-left: auto;
}
</style>

<script>
function showLoading(message = 'Loading...') {
  const overlay = document.getElementById('loading-overlay');
  overlay.querySelector('.loading-text').textContent = message;
  overlay.style.display = 'flex';
}

function hideLoading() {
  document.getElementById('loading-overlay').style.display = 'none';
}

function showError(title, description) {
  const errorDiv = document.getElementById('error-message');
  errorDiv.querySelector('.error-title').textContent = title;
  errorDiv.querySelector('.error-description').textContent = description;
  errorDiv.style.display = 'block';
  
  // Auto-hide after 10 seconds
  setTimeout(closeError, 10000);
}

function closeError() {
  document.getElementById('error-message').style.display = 'none';
}

// Example usage with async operations
async function loadData() {
  try {
    showLoading('Loading financial data...');
    
    // Simulate data loading
    const data = await fetchFinancialData();
    
    hideLoading();
    renderData(data);
  } catch (error) {
    hideLoading();
    showError(
      'Data Load Failed',
      'Unable to retrieve financial data. Please refresh the page or contact support.'
    );
    console.error('Data load error:', error);
  }
}

// Automatic loading indicator for slow operations
async function withLoading(promise, message, threshold = 200) {
  let timeoutId;
  
  // Show loading after threshold
  timeoutId = setTimeout(() => showLoading(message), threshold);
  
  try {
    const result = await promise;
    clearTimeout(timeoutId);
    hideLoading();
    return result;
  } catch (error) {
    clearTimeout(timeoutId);
    hideLoading();
    throw error;
  }
}

// Usage
await withLoading(
  calculateVarianceAnalysis(),
  'Calculating variance analysis...',
  200
);
</script>
```

**Rationale:** User feedback, perceived performance improvement, and error transparency

---

### I3: Keyboard Navigation

**Requirement:** All interactive elements accessible via Tab, Enter, Space. Visible focus indicators.

**Example:**
```css
/* Focus indicators */
button:focus,
input:focus,
select:focus,
[tabindex]:focus {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

/* Remove default outline and use custom */
*:focus {
  outline: none;
}

button:focus-visible,
input:focus-visible,
select:focus-visible,
[tabindex]:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(0, 120, 212, 0.1);
}

/* Interactive table rows */
tr[tabindex]:hover,
tr[tabindex]:focus {
  background: var(--bg-secondary);
}

tr[tabindex]:focus {
  outline: 2px solid var(--primary);
  outline-offset: -2px;
}
```

```javascript
// Keyboard handlers for custom controls
function makeAccessible(element, onClick) {
  element.setAttribute('tabindex', '0');
  element.setAttribute('role', 'button');
  
  element.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick(e);
    }
  });
  
  element.addEventListener('click', onClick);
}

// Example: Sortable table headers
document.querySelectorAll('th.sortable').forEach(header => {
  makeAccessible(header, () => {
    const column = header.dataset.column;
    sortTable(column);
  });
});

// Arrow key navigation in lists
function enableArrowNavigation(container) {
  const items = container.querySelectorAll('[tabindex]');
  let currentIndex = 0;
  
  container.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      currentIndex = Math.min(currentIndex + 1, items.length - 1);
      items[currentIndex].focus();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      currentIndex = Math.max(currentIndex - 1, 0);
      items[currentIndex].focus();
    }
  });
}

// Apply to metric list
enableArrowNavigation(document.getElementById('metric-list'));
```

**ARIA Labels:**
```html
<button aria-label="Sort by Net Turnover ascending">
  Net Turnover <span aria-hidden="true">▲</span>
</button>

<div role="table" aria-label="Balance Sheet">
  <div role="rowgroup">
    <div role="row">
      <div role="columnheader">Account</div>
      <div role="columnheader">Actual 2025</div>
    </div>
  </div>
</div>
```

**Rationale:** Accessibility compliance and keyboard-only user support

---

### I4: Tooltips & Contextual Help

**Requirement:** Use title attributes or custom tooltips for complex metrics. Show formulas on hover.

**Example:**
```html
<!-- Simple tooltip using title -->
<span class="metric" title="Calculation: (Current - Prior) / Prior × 100">
  +15.4%
</span>

<!-- Custom rich tooltip -->
<div class="metric-container">
  <span class="metric-value">28,648,991</span>
  <button class="info-icon" data-tooltip="net-turnover-info">ⓘ</button>
</div>

<div id="net-turnover-info" class="tooltip" role="tooltip" style="display: none;">
  <strong>Net Turnover</strong><br>
  Total reported revenue across all locations<br>
  <em>Formula: SUMX(Sales, [Amount])</em><br>
  <small>Updated: May 2025</small>
</div>

<style>
.tooltip {
  position: absolute;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-width: 300px;
  font-size: 13px;
  line-height: 1.5;
}

.tooltip strong {
  display: block;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.tooltip em {
  display: block;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border-color);
  font-style: normal;
  font-family: 'Consolas', monospace;
  font-size: 12px;
  color: var(--text-secondary);
}

.tooltip small {
  display: block;
  margin-top: 8px;
  color: var(--text-tertiary);
}

.info-icon {
  background: none;
  border: none;
  color: var(--primary);
  cursor: help;
  font-size: 14px;
  padding: 0 4px;
  vertical-align: middle;
}

.info-icon:hover {
  color: var(--primary-hover);
}
</style>

<script>
// Tooltip positioning and management
class TooltipManager {
  constructor() {
    this.activeTooltip = null;
    this.init();
  }
  
  init() {
    document.addEventListener('click', (e) => {
      const infoIcon = e.target.closest('[data-tooltip]');
      if (infoIcon) {
        e.stopPropagation();
        this.toggle(infoIcon);
      } else if (!e.target.closest('.tooltip')) {
        this.hideAll();
      }
    });
    
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.hideAll();
      }
    });
  }
  
  toggle(trigger) {
    const tooltipId = trigger.dataset.tooltip;
    const tooltip = document.getElementById(tooltipId);
    
    if (this.activeTooltip === tooltip) {
      this.hide(tooltip);
    } else {
      this.hideAll();
      this.show(trigger, tooltip);
    }
  }
  
  show(trigger, tooltip) {
    const rect = trigger.getBoundingClientRect();
    
    tooltip.style.display = 'block';
    
    // Position below trigger
    tooltip.style.left = `${rect.left}px`;
    tooltip.style.top = `${rect.bottom + 8}px`;
    
    // Check if tooltip goes off-screen
    const tooltipRect = tooltip.getBoundingClientRect();
    if (tooltipRect.right > window.innerWidth) {
      tooltip.style.left = `${window.innerWidth - tooltipRect.width - 16}px`;
    }
    
    this.activeTooltip = tooltip;
  }
  
  hide(tooltip) {
    tooltip.style.display = 'none';
    this.activeTooltip = null;
  }
  
  hideAll() {
    document.querySelectorAll('.tooltip').forEach(tooltip => {
      tooltip.style.display = 'none';
    });
    this.activeTooltip = null;
  }
}

const tooltipManager = new TooltipManager();
</script>
```

**Rationale:** User guidance, formula transparency, and self-documenting reports

---

## 5. Power BI Integration Patterns
**Priority:** CRITICAL

### P1: Cross-Filtering Simulation

**Requirement:** Implement click-to-filter with visual feedback. Maintain filter context.

**Example:**
```javascript
// Simulate Power BI cross-filtering
function handleItemClick(itemId, itemType) {
  // Toggle selection
  const index = state.selectedItems.findIndex(s => s.id === itemId);
  
  if (index >= 0) {
    // Deselect
    state.selectedItems.splice(index, 1);
  } else {
    // Select (clear if different type, multi-select if same type with Ctrl)
    if (event.ctrlKey || event.metaKey) {
      state.selectedItems.push({ id: itemId, type: itemType });
    } else {
      state.selectedItems = [{ id: itemId, type: itemType }];
    }
  }
  
  // Apply filters to all visuals
  filterAllVisuals();
  
  // Update visual feedback
  updateSelectionHighlights();
}

function filterAllVisuals() {
  const filtered = applySelectionFilters(state.data, state.selectedItems);
  
  // Update each visual with filtered data
  updateTable(filtered);
  updateChart(filtered);
  updateMetricCards(filtered);
  
  // Update filter status
  updateFilterBadge();
}

function updateSelectionHighlights() {
  // Remove all highlights
  document.querySelectorAll('.selected').forEach(el => {
    el.classList.remove('selected');
  });
  
  // Add highlights to selected items
  state.selectedItems.forEach(item => {
    const element = document.querySelector(`[data-id="${item.id}"]`);
    if (element) {
      element.classList.add('selected');
    }
  });
}

function clearAllFilters() {
  state.selectedItems = [];
  filterAllVisuals();
  updateSelectionHighlights();
}
```

```css
/* Visual feedback for selections */
.selectable {
  cursor: pointer;
  transition: background-color 0.2s;
}

.selectable:hover {
  background: var(--bg-secondary);
}

.selectable.selected {
  background: rgba(0, 120, 212, 0.1);
  border-left: 3px solid var(--primary);
}

/* Filtered state indicator */
.filtered-visual {
  position: relative;
}

.filtered-visual::before {
  content: '🔍';
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 16px;
  opacity: 0.6;
}
```

**Rationale:** Mimic native Power BI cross-filtering behavior for familiar UX

---

### P2: Slicer Panel Design

**Requirement:** Group filters logically. Use checkboxes, dropdowns, or date pickers. Show active filter count.

**Example:**
```html
<div class="slicer-panel">
  <div class="slicer-header">
    <h3>Filters</h3>
    <button class="clear-filters" onclick="clearAllFilters()">Clear All</button>
  </div>
  
  <!-- Time Period Slicer -->
  <div class="slicer-group">
    <label class="slicer-label">Time Period</label>
    <div class="slicer-options">
      <label class="slicer-option">
        <input type="radio" name="period" value="MTD" onchange="updateFilter('period', this.value)">
        <span>Month to Date</span>
      </label>
      <label class="slicer-option">
        <input type="radio" name="period" value="QTD" onchange="updateFilter('period', this.value)">
        <span>Quarter to Date</span>
      </label>
      <label class="slicer-option">
        <input type="radio" name="period" value="YTD" checked onchange="updateFilter('period', this.value)">
        <span>Year to Date</span>
      </label>
    </div>
  </div>
  
  <!-- Month Selector -->
  <div class="slicer-group">
    <label class="slicer-label">Month</label>
    <select class="slicer-dropdown" onchange="updateFilter('month', this.value)">
      <option value="JAN">January</option>
      <option value="FEB">February</option>
      <option value="MAR">March</option>
      <option value="APR">April</option>
      <option value="MAY" selected>May</option>
      <option value="JUN">June</option>
    </select>
  </div>
  
  <!-- Location Multi-select -->
  <div class="slicer-group">
    <label class="slicer-label">
      Locations
      <span class="filter-count" id="location-count">(0)</span>
    </label>
    <div class="slicer-search">
      <input type="text" placeholder="Search locations..." oninput="filterLocations(this.value)">
    </div>
    <div class="slicer-checkbox-list" id="location-list">
      <!-- Populated dynamically -->
    </div>
  </div>
  
  <!-- Active Filters Summary -->
  <div class="filter-summary">
    <div class="filter-badge">
      <strong id="active-filter-count">0</strong> filters active
    </div>
  </div>
</div>

<style>
.slicer-panel {
  width: 280px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  max-height: 80vh;
  overflow-y: auto;
}

.slicer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.slicer-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.clear-filters {
  background: none;
  border: none;
  color: var(--primary);
  font-size: 12px;
  cursor: pointer;
  padding: 4px 8px;
}

.clear-filters:hover {
  text-decoration: underline;
}

.slicer-group {
  margin-bottom: 20px;
}

.slicer-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.filter-count {
  font-weight: 400;
  color: var(--primary);
}

.slicer-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  cursor: pointer;
}

.slicer-option input {
  margin: 0;
  cursor: pointer;
}

.slicer-dropdown {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 14px;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.slicer-search {
  margin-bottom: 8px;
}

.slicer-search input {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 13px;
}

.slicer-checkbox-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 8px;
}

.filter-summary {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.filter-badge {
  background: var(--bg-secondary);
  padding: 8px 12px;
  border-radius: 4px;
  text-align: center;
  font-size: 13px;
  color: var(--text-secondary);
}

.filter-badge strong {
  color: var(--primary);
  font-size: 16px;
}
</style>

<script>
function updateFilter(key, value) {
  state.filters[key] = value;
  applyFilters();
  updateFilterCount();
}

function populateLocationList(locations) {
  const list = document.getElementById('location-list');
  list.innerHTML = locations.map(loc => `
    <label class="slicer-option">
      <input type="checkbox" value="${loc}" onchange="toggleLocation('${loc}')">
      <span>${loc}</span>
    </label>
  `).join('');
}

function toggleLocation(location) {
  const index = state.filters.locations.indexOf(location);
  if (index >= 0) {
    state.filters.locations.splice(index, 1);
  } else {
    state.filters.locations.push(location);
  }
  applyFilters();
  updateFilterCount();
}

function updateFilterCount() {
  const count = Object.values(state.filters)
    .filter(v => Array.isArray(v) ? v.length > 0 : v !== null)
    .length;
  
  document.getElementById('active-filter-count').textContent = count;
  document.getElementById('location-count').textContent = `(${state.filters.locations.length})`;
}

function filterLocations(query) {
  const checkboxes = document.querySelectorAll('#location-list .slicer-option');
  checkboxes.forEach(checkbox => {
    const text = checkbox.textContent.toLowerCase();
    const matches = text.includes(query.toLowerCase());
    checkbox.style.display = matches ? 'flex' : 'none';
  });
}
</script>
```

**Rationale:** Familiar Power BI slicer UX patterns and filter management

---

### P3: Drill-Through Emulation

**Requirement:** Implement hierarchical navigation (e.g., Year → Quarter → Month). Maintain breadcrumb trail.

**Example:**
```html
<div class="drill-through-nav">
  <div class="breadcrumb" id="breadcrumb">
    <!-- Populated dynamically -->
  </div>
  <button class="drill-up-btn" onclick="drillUp()" style="display: none;">
    ← Back
  </button>
</div>

<div class="drill-content" id="drill-content">
  <!-- Content changes based on drill level -->
</div>

<style>
.drill-through-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: 4px;
  margin-bottom: 16px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.breadcrumb-item {
  color: var(--primary);
  cursor: pointer;
  text-decoration: none;
}

.breadcrumb-item:hover {
  text-decoration: underline;
}

.breadcrumb-item.current {
  color: var(--text-primary);
  cursor: default;
  font-weight: 600;
}

.breadcrumb-separator {
  color: var(--text-tertiary);
}

.drill-up-btn {
  background: var(--primary);
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.drill-up-btn:hover {
  background: var(--primary-hover);
}
</style>

<script>
// Drill-through hierarchy
const drillHierarchy = ['year', 'quarter', 'month', 'day'];
let currentDrillLevel = 0;
let drillPath = [];

function drillTo(level, value) {
  // Find level index
  const levelIndex = drillHierarchy.indexOf(level);
  
  // Update drill path
  drillPath = drillPath.slice(0, levelIndex);
  drillPath.push({ level, value });
  
  currentDrillLevel = levelIndex;
  
  // Update content
  renderDrillContent();
  updateBreadcrumb();
  
  // Show/hide drill up button
  document.querySelector('.drill-up-btn').style.display = 
    currentDrillLevel > 0 ? 'block' : 'none';
}

function drillUp() {
  if (currentDrillLevel > 0) {
    drillPath.pop();
    currentDrillLevel--;
    renderDrillContent();
    updateBreadcrumb();
    
    if (currentDrillLevel === 0) {
      document.querySelector('.drill-up-btn').style.display = 'none';
    }
  }
}

function updateBreadcrumb() {
  const breadcrumb = document.getElementById('breadcrumb');
  
  const items = drillPath.map((item, index) => {
    const isCurrent = index === drillPath.length - 1;
    const className = isCurrent ? 'breadcrumb-item current' : 'breadcrumb-item';
    
    return `
      <span class="${className}" 
            ${!isCurrent ? `onclick="drillTo('${item.level}', '${item.value}')"` : ''}>
        ${item.value}
      </span>
      ${!isCurrent ? '<span class="breadcrumb-separator">›</span>' : ''}
    `;
  }).join('');
  
  breadcrumb.innerHTML = items || '<span class="breadcrumb-item current">All Years</span>';
}

function renderDrillContent() {
  const content = document.getElementById('drill-content');
  const currentLevel = drillHierarchy[currentDrillLevel];
  const nextLevel = drillHierarchy[currentDrillLevel + 1];
  
  // Filter data based on drill path
  let filteredData = data;
  drillPath.forEach(pathItem => {
    filteredData = filteredData.filter(d => d[pathItem.level] === pathItem.value);
  });
  
  // Aggregate by next level
  if (nextLevel) {
    const aggregated = aggregateByLevel(filteredData, nextLevel);
    renderDrillTable(aggregated, nextLevel);
  } else {
    // Leaf level - show detail
    renderDetailTable(filteredData);
  }
}

function renderDrillTable(data, level) {
  const content = document.getElementById('drill-content');
  const levelLabel = level.charAt(0).toUpperCase() + level.slice(1);
  
  content.innerHTML = `
    <table class="drill-table">
      <thead>
        <tr>
          <th>${levelLabel}</th>
          <th>Actual</th>
          <th>Variance</th>
          <th>%</th>
        </tr>
      </thead>
      <tbody>
        ${data.map(row => `
          <tr class="clickable" onclick="drillTo('${level}', '${row[level]}')">
            <td>${row[level]}</td>
            <td>${formatCurrency(row.actual)}</td>
            <td class="${row.variance >= 0 ? 'positive' : 'negative'}">
              ${formatCurrency(row.variance)}
            </td>
            <td class="${row.variancePct >= 0 ? 'positive' : 'negative'}">
              ${formatPercent(row.variancePct, 1)}
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

// Initialize
drillTo('year', 'FY 2025');
</script>
```

**Rationale:** Support analytical workflows and hierarchical data exploration

---

### P4: Export Functionality

**Requirement:** Allow CSV/Excel export with formatted values. Include metadata (report name, date, filters).

**Example:**
```javascript
function exportToCSV() {
  const timestamp = new Date().toISOString().slice(0, 19).replace('T', ' ');
  const filterSummary = Object.entries(state.filters)
    .filter(([k, v]) => v && (Array.isArray(v) ? v.length > 0 : true))
    .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
    .join(' | ');
  
  // Metadata header
  const metadata = [
    `Report: Balance Sheet Analysis`,
    `Generated: ${timestamp}`,
    `Filters: ${filterSummary}`,
    ``,
    ``
  ];
  
  // Data headers
  const headers = ['Account', 'Actual 2025', 'Actual 2024', 'Δ Reported', 'Δ%'];
  
  // Data rows with formatting
  const rows = filteredData.map(row => [
    row.account,
    formatCurrency(row.actual2025),
    formatCurrency(row.actual2024),
    formatCurrency(row.deltaReported),
    formatPercent(row.deltaPercent, 1)
  ]);
  
  // Combine all
  const csv = [
    ...metadata,
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n');
  
  // Download
  downloadFile(csv, `balance-sheet-${Date.now()}.csv`, 'text/csv');
}

function exportToExcel() {
  // Create workbook structure
  const wb = {
    SheetNames: ['Balance Sheet', 'Metadata'],
    Sheets: {}
  };
  
  // Balance Sheet data
  const wsData = [
    ['Account', 'Actual 2025', 'Actual 2024', 'Δ Reported', 'Δ%'],
    ...filteredData.map(row => [
      row.account,
      row.actual2025,
      row.actual2024,
      row.deltaReported,
      row.deltaPercent
    ])
  ];
  
  wb.Sheets['Balance Sheet'] = XLSX.utils.aoa_to_sheet(wsData);
  
  // Metadata sheet
  const metadata = [
    ['Report Name', 'Balance Sheet Analysis'],
    ['Generated', new Date().toISOString()],
    ['Filters Applied', ''],
    ...Object.entries(state.filters).map(([k, v]) => [
      k, 
      Array.isArray(v) ? v.join(', ') : v
    ])
  ];
  
  wb.Sheets['Metadata'] = XLSX.utils.aoa_to_sheet(metadata);
  
  // Generate and download
  const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
  downloadFile(
    new Blob([wbout], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }),
    `balance-sheet-${Date.now()}.xlsx`,
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  );
}

function downloadFile(content, filename, mimeType) {
  const blob = content instanceof Blob ? content : new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Export button UI
function renderExportButtons() {
  return `
    <div class="export-menu">
      <button class="export-btn" onclick="toggleExportMenu()">
        Export ▼
      </button>
      <div class="export-dropdown" id="export-dropdown" style="display: none;">
        <button onclick="exportToCSV()">📄 Export as CSV</button>
        <button onclick="exportToExcel()">📊 Export as Excel</button>
        <button onclick="exportToPDF()">📑 Export as PDF</button>
      </div>
    </div>
  `;
}
```

**Rationale:** Data portability, offline analysis, and integration with other tools

---

## 6. Testing & Validation
**Priority:** MEDIUM

### T1: Browser Compatibility

**Requirement:** Test in Edge (Chromium), Chrome, Firefox. No browser-specific features without fallbacks.

**Example:**
```javascript
// Feature detection pattern
function initializeApp() {
  // Check for required features
  const hasIntersectionObserver = 'IntersectionObserver' in window;
  const hasResizeObserver = 'ResizeObserver' in window;
  const hasGridSupport = CSS.supports('display', 'grid');
  
  if (!hasGridSupport) {
    console.warn('CSS Grid not supported, using flexbox fallback');
    document.body.classList.add('no-grid');
  }
  
  // Intersection Observer with fallback
  if (hasIntersectionObserver) {
    setupLazyLoading();
  } else {
    console.warn('IntersectionObserver not supported, loading all content immediately');
    loadAllContent();
  }
  
  // Resize Observer with fallback
  if (hasResizeObserver) {
    setupResizeObserver();
  } else {
    console.warn('ResizeObserver not supported, using window resize events');
    window.addEventListener('resize', debounce(handleResize, 250));
  }
}

// Polyfill for older browsers
if (!Array.prototype.flat) {
  Array.prototype.flat = function(depth = 1) {
    return depth > 0
      ? this.reduce((acc, val) => acc.concat(Array.isArray(val) ? val.flat(depth - 1) : val), [])
      : this.slice();
  };
}

// CSS fallback in stylesheet
@supports not (display: grid) {
  .container {
    display: flex;
    flex-wrap: wrap;
  }
  
  .item {
    flex: 1 1 300px;
    margin: 8px;
  }
}
```

**Browser Testing Checklist:**
- ✓ Edge (Chromium) - Latest version
- ✓ Chrome - Latest version
- ✓ Firefox - Latest version
- ✓ Safari - Latest version (if Mac users present)

**Rationale:** Power BI Web runs on various browsers in different organizations

---

### T2: Data Edge Cases

**Requirement:** Test with: null/undefined values, zero values, extreme numbers (±999T), empty datasets

**Example:**
```javascript
// Robust value formatting
function formatValue(value, type = 'currency') {
  // Handle null/undefined
  if (value === null || value === undefined) {
    return '<span class="na-value">N/A</span>';
  }
  
  // Handle zero
  if (value === 0) {
    return type === 'currency' ? '0' : '0%';
  }
  
  // Handle extreme values
  if (Math.abs(value) > 999999999999) {
    return `<span title="${value}">&gt;999T</span>`;
  }
  
  if (Math.abs(value) < 0.0001 && value !== 0) {
    return `<span title="${value}">&lt;0.0001</span>`;
  }
  
  // Normal formatting
  if (type === 'currency') {
    return formatCurrency(value);
  } else if (type === 'percent') {
    return formatPercent(value);
  }
  
  return value.toString();
}

// Empty state handling
function renderTable(data) {
  const tbody = document.querySelector('tbody');
  
  if (!data || data.length === 0) {
    tbody.innerHTML = `
      <tr class="empty-state">
        <td colspan="5">
          <div class="empty-state-content">
            <div class="empty-icon">📊</div>
            <p class="empty-title">No data available</p>
            <p class="empty-description">
              Try adjusting your filters or check your data source connection.
            </p>
          </div>
        </td>
      </tr>
    `;
    return;
  }
  
  // Render data...
}

// Division by zero safety
function calculateVariance(current, prior) {
  if (!prior || prior === 0) {
    return current === 0 ? 0 : Infinity;
  }
  return ((current - prior) / Math.abs(prior));
}

// Test data generators for edge cases
const testCases = {
  nullValues: { actual: null, prior: 1000 },
  zeroValues: { actual: 0, prior: 0 },
  extremePositive: { actual: 999999999999999, prior: 1000 },
  extremeNegative: { actual: -999999999999999, prior: 1000 },
  tinyValues: { actual: 0.00001, prior: 0.00002 },
  emptyDataset: []
};

// Run edge case tests
function runEdgeCaseTests() {
  console.group('Edge Case Tests');
  
  Object.entries(testCases).forEach(([name, data]) => {
    try {
      const result = processData(data);
      console.log(`✓ ${name}: ${JSON.stringify(result)}`);
    } catch (error) {
      console.error(`✗ ${name}: ${error.message}`);
    }
  });
  
  console.groupEnd();
}
```

**Rationale:** Robust error handling prevents crashes with real-world data anomalies

---

### T3: Performance Benchmarks

**Requirement:** Initial render <500ms, filter operations <200ms, table sort <100ms for 1000 rows

**Example:**
```javascript
// Performance monitoring utilities
class PerformanceMonitor {
  constructor() {
    this.metrics = {};
  }
  
  start(label) {
    this.metrics[label] = performance.now();
  }
  
  end(label, threshold) {
    if (!this.metrics[label]) return;
    
    const duration = performance.now() - this.metrics[label];
    const status = duration < threshold ? '✓' : '⚠️';
    
    console.log(`${status} ${label}: ${duration.toFixed(2)}ms (threshold: ${threshold}ms)`);
    
    delete this.metrics[label];
    return duration;
  }
  
  measure(fn, label, threshold) {
    this.start(label);
    const result = fn();
    this.end(label, threshold);
    return result;
  }
  
  async measureAsync(fn, label, threshold) {
    this.start(label);
    const result = await fn();
    this.end(label, threshold);
    return result;
  }
}

const perfMon = new PerformanceMonitor();

// Usage examples
function initializeApp() {
  perfMon.start('initialRender');
  
  // Load data
  perfMon.start('dataLoad');
  const data = loadData();
  perfMon.end('dataLoad', 100);
  
  // Render table
  perfMon.start('tableRender');
  renderTable(data);
  perfMon.end('tableRender', 300);
  
  // Render charts
  perfMon.start('chartRender');
  renderCharts(data);
  perfMon.end('chartRender', 500);
  
  perfMon.end('initialRender', 500);
}

function handleFilter(filters) {
  perfMon.start('filterOperation');
  
  const filtered = applyFilters(data, filters);
  updateAllVisuals(filtered);
  
  perfMon.end('filterOperation', 200);
}

function sortTable(column) {
  const duration = perfMon.measure(
    () => {
      data.sort((a, b) => a[column] - b[column]);
      renderTable(data);
    },
    'tableSort',
    100
  );
  
  if (duration > 100) {
    console.warn(`Sort performance degraded. Consider optimization.`);
  }
}

// Automated performance testing
function runPerformanceTests() {
  console.group('Performance Benchmarks');
  
  // Test 1: Initial render with 1000 rows
  const testData1000 = generateTestData(1000);
  perfMon.measure(
    () => renderTable(testData1000),
    'render1000Rows',
    500
  );
  
  // Test 2: Filter operation
  perfMon.measure(
    () => applyFilters(testData1000, { period: 'YTD' }),
    'filterOperation',
    200
  );
  
  // Test 3: Sort operation
  perfMon.measure(
    () => sortData(testData1000, 'actual', 'desc'),
    'sortOperation',
    100
  );
  
  // Test 4: Aggregation
  perfMon.measure(
    () => aggregateData(testData1000, 'category'),
    'aggregation',
    150
  );
  
  console.groupEnd();
}

// Memory leak detection
function detectMemoryLeaks() {
  const before = performance.memory ? performance.memory.usedJSHeapSize : 0;
  
  // Perform operations that might leak
  for (let i = 0; i < 100; i++) {
    renderTable(testData);
    clearTable();
  }
  
  // Force garbage collection if available (Chrome DevTools)
  if (window.gc) {
    window.gc();
  }
  
  const after = performance.memory ? performance.memory.usedJSHeapSize : 0;
  const growth = after - before;
  
  console.log(`Memory growth: ${(growth / 1024 / 1024).toFixed(2)} MB`);
  
  if (growth > 10 * 1024 * 1024) { // 10MB
    console.warn('Potential memory leak detected!');
  }
}
</script>
```

**Performance Optimization Techniques:**

1. **Debouncing/Throttling** - Reduce event handler frequency
2. **Virtual Scrolling** - Render only visible rows
3. **Request Animation Frame** - Smooth animations
4. **Web Workers** - Offload heavy calculations (if needed)
5. **Memoization** - Cache expensive computations

```javascript
// Memoization example
const memoize = (fn) => {
  const cache = new Map();
  return (...args) => {
    const key = JSON.stringify(args);
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
};

const expensiveCalculation = memoize((data, filters) => {
  // Complex calculation here
  return result;
});
```

**Rationale:** User experience quality and responsiveness

---

## 7. Advanced Patterns & Best Practices

### A1: Progressive Enhancement

**Requirement:** Build core functionality first, then enhance with advanced features

**Example:**
```javascript
// Core functionality - works everywhere
function renderBasicTable(data) {
  const tbody = document.querySelector('tbody');
  tbody.innerHTML = data.map(row => `
    <tr>
      <td>${row.account}</td>
      <td>${formatCurrency(row.actual)}</td>
      <td>${formatCurrency(row.variance)}</td>
    </tr>
  `).join('');
}

// Enhanced functionality - added progressively
function enhanceTable() {
  // Add sorting if supported
  if (typeof Array.prototype.sort === 'function') {
    addSortingCapability();
  }
  
  // Add animations if supported
  if (CSS.supports('animation', 'fadeIn 0.3s')) {
    addAnimations();
  }
  
  // Add advanced interactions
  if ('IntersectionObserver' in window) {
    addLazyLoading();
  }
}

// Initialize
renderBasicTable(data);
enhanceTable();
```

---

### A2: Semantic HTML & Accessibility

**Requirement:** Use proper HTML5 semantic elements and ARIA attributes

**Example:**
```html
<!-- Semantic structure -->
<main role="main" aria-label="Financial Dashboard">
  <header>
    <h1>Balance Sheet Analysis</h1>
    <nav aria-label="Report filters">
      <!-- Filters -->
    </nav>
  </header>
  
  <section aria-labelledby="assets-heading">
    <h2 id="assets-heading">Assets</h2>
    <table role="table" aria-label="Assets breakdown">
      <thead>
        <tr>
          <th scope="col" role="columnheader">Account</th>
          <th scope="col" role="columnheader">Actual 2025</th>
          <th scope="col" role="columnheader">Variance</th>
        </tr>
      </thead>
      <tbody>
        <!-- Data rows -->
      </tbody>
    </table>
  </section>
  
  <aside aria-label="Key metrics">
    <!-- Metric cards -->
  </aside>
</main>

<!-- Screen reader announcements -->
<div role="status" aria-live="polite" aria-atomic="true" class="sr-only">
  <span id="status-message"></span>
</div>

<style>
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>

<script>
// Announce updates to screen readers
function announce(message) {
  const statusEl = document.getElementById('status-message');
  statusEl.textContent = message;
  
  // Clear after 1 second
  setTimeout(() => {
    statusEl.textContent = '';
  }, 1000);
}

// Usage
announce('Filter applied. Showing 45 of 200 accounts.');
</script>
```

---

### A3: Error Boundaries & Graceful Degradation

**Requirement:** Implement try-catch blocks and fallback mechanisms

**Example:**
```javascript
// Global error handler
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
  
  showError(
    'Unexpected Error',
    'An error occurred while processing your request. Please refresh the page.'
  );
  
  // Log to external service if available
  if (window.errorLogger) {
    window.errorLogger.log({
      message: event.error.message,
      stack: event.error.stack,
      timestamp: new Date().toISOString()
    });
  }
});

// Try-catch wrapper for critical functions
function safeExecute(fn, fallback, errorMessage) {
  try {
    return fn();
  } catch (error) {
    console.error(errorMessage, error);
    
    if (fallback) {
      return fallback();
    }
    
    showError('Operation Failed', errorMessage);
    return null;
  }
}

// Usage
const data = safeExecute(
  () => JSON.parse(rawData),
  () => [],
  'Failed to parse data'
);

// Component-level error boundaries
class SafeComponent {
  constructor(container, renderFn) {
    this.container = container;
    this.renderFn = renderFn;
  }
  
  render(data) {
    try {
      this.renderFn(this.container, data);
    } catch (error) {
      console.error('Component render error:', error);
      this.container.innerHTML = `
        <div class="component-error">
          <p>Unable to display this component</p>
          <button onclick="location.reload()">Refresh Page</button>
        </div>
      `;
    }
  }
}
```

---

### A4: Code Organization & Maintainability

**Requirement:** Use clear naming conventions, comments, and modular structure

**Example:**
```javascript
/**
 * Financial Dashboard Application
 * @version 2.0
 * @author Finance Team
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const CONFIG = {
  DEFAULT_CURRENCY: 'USD',
  DEFAULT_LOCALE: 'en-US',
  ROWS_PER_PAGE: 50,
  DEBOUNCE_DELAY: 300,
  ANIMATION_DURATION: 200,
  MAX_FILTER_SELECTIONS: 100
};

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

const state = {
  /* ... as defined in I1 ... */
};

function updateState(updates) {
  /* ... */
}

// ============================================================================
// DATA OPERATIONS
// ============================================================================

/**
 * Apply filters to dataset
 * @param {Array} data - Source data array
 * @param {Object} filters - Filter configuration
 * @returns {Array} Filtered data
 */
function applyFilters(data, filters) {
  return data.filter(row => {
    // Period filter
    if (filters.period && !matchesPeriod(row, filters.period)) {
      return false;
    }
    
    // Location filter
    if (filters.locations.length > 0 && !filters.locations.includes(row.location)) {
      return false;
    }
    
    return true;
  });
}

/**
 * Sort data by column
 * @param {Array} data - Data to sort
 * @param {string} column - Column name
 * @param {string} direction - 'asc' or 'desc'
 * @returns {Array} Sorted data
 */
function sortData(data, column, direction = 'asc') {
  const sorted = [...data].sort((a, b) => {
    const aVal = a[column];
    const bVal = b[column];
    
    if (typeof aVal === 'number') {
      return aVal - bVal;
    }
    
    return String(aVal).localeCompare(String(bVal));
  });
  
  return direction === 'desc' ? sorted.reverse() : sorted;
}

// ============================================================================
// FORMATTING UTILITIES
// ============================================================================

const formatCurrency = (value, currency = CONFIG.DEFAULT_CURRENCY) => {
  /* ... as defined in V3 ... */
};

const formatPercent = (value, decimals = 0) => {
  /* ... */
};

// ============================================================================
// UI RENDERING
// ============================================================================

function renderTable(data) {
  /* ... */
}

function renderCharts(data) {
  /* ... */
}

function renderMetricCards(data) {
  /* ... */
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

function handleFilterChange(key, value) {
  updateState({ filters: { [key]: value } });
}

function handleSort(column) {
  const newDirection = 
    state.sort.column === column && state.sort.direction === 'asc' 
      ? 'desc' 
      : 'asc';
  
  updateState({ 
    sort: { column, direction: newDirection } 
  });
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  initializeApp();
});

function initializeApp() {
  console.log('Initializing Financial Dashboard v2.0');
  
  // Load initial data
  loadData()
    .then(data => {
      state.data = data;
      render();
    })
    .catch(error => {
      showError('Initialization Failed', error.message);
    });
}
```

**Naming Conventions:**
- `camelCase` for variables and functions
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Descriptive names: `calculateVariance` not `calcVar`
- Boolean prefixes: `isLoading`, `hasData`, `canEdit`

---

## 8. Documentation & Handoff

### D1: Code Documentation

**Requirement:** Include JSDoc comments for functions, clear inline comments for complex logic

**Example:**
```javascript
/**
 * Calculate Time-Weighted Return (TWR) for investment portfolio
 * 
 * TWR measures portfolio performance independent of cash flows,
 * calculated by geometrically linking sub-period returns.
 * 
 * @param {Array<Object>} cashFlows - Array of cash flow events
 * @param {number} cashFlows[].date - Transaction date (timestamp)
 * @param {number} cashFlows[].amount - Cash flow amount (+ inflow, - outflow)
 * @param {number} cashFlows[].valueBefore - Portfolio value before transaction
 * @param {number} cashFlows[].valueAfter - Portfolio value after transaction
 * @returns {number} TWR as decimal (0.15 = 15% return)
 * 
 * @example
 * const twr = calculateTWR([
 *   { date: 1609459200000, amount: 10000, valueBefore: 0, valueAfter: 10000 },
 *   { date: 1612137600000, amount: 5000, valueBefore: 11000, valueAfter: 16000 }
 * ]);
 * console.log(formatPercent(twr, 2)); // "15.00%"
 */
function calculateTWR(cashFlows) {
  if (!cashFlows || cashFlows.length === 0) {
    return 0;
  }
  
  // Sort by date to ensure chronological processing
  const sorted = [...cashFlows].sort((a, b) => a.date - b.date);
  
  // Calculate sub-period returns
  let cumulativeReturn = 1;
  
  for (let i = 0; i < sorted.length - 1; i++) {
    const current = sorted[i];
    const next = sorted[i + 1];
    
    // Sub-period return = (Ending Value - Cash Flow) / Beginning Value
    const subPeriodReturn = 
      (next.valueBefore - current.amount) / current.valueAfter;
    
    // Geometric linking
    cumulativeReturn *= (1 + subPeriodReturn);
  }
  
  // Convert to percentage return
  return cumulativeReturn - 1;
}
```

---

### D2: README Documentation

**Requirement:** Include setup instructions, feature list, known limitations

**Example:**
```markdown
# Balance Sheet Analysis Dashboard

## Overview
Interactive HTML dashboard for financial consolidation and variance analysis across 190+ locations.

## Features
- ✅ Multi-currency balance sheet consolidation
- ✅ Period-over-period variance analysis
- ✅ Drill-through from year → quarter → month
- ✅ Interactive slicers (Period, Location, Cost Center)
- ✅ Export to CSV/Excel with metadata
- ✅ Responsive design (supports ultrawide 3840x1080)
- ✅ WCAG AA accessible

## Browser Support
- ✅ Microsoft Edge (Chromium) - Recommended
- ✅ Google Chrome
- ✅ Mozilla Firefox
- ⚠️ Safari (limited testing)

## Setup Instructions
1. Open the HTML file in a text editor
2. Locate the `DATA_SOURCE` constant (line 45)
3. Update with your data source endpoint or embed data directly
4. Save and open in supported browser
5. For Power BI: Import as Custom Visual

## Data Structure
Expected JSON format:
```json
[
  {
    "account": "Cash at bank and in hand",
    "category": "Current assets",
    "actual2025": 11483653,
    "actual2024": 10552721,
    "location": "BE-Brussels",
    "costCenter": "CC001",
    "currency": "EUR"
  }
]
```

## Configuration
Edit the `CONFIG` object (line 12) to customize:
- `DEFAULT_CURRENCY`: Default display currency
- `ROWS_PER_PAGE`: Pagination size
- `ANIMATION_DURATION`: UI animation speed

## Known Limitations
- ⚠️ No localStorage support (Power BI iframe restriction)
- ⚠️ Maximum 10,000 rows before performance degradation
- ⚠️ Single-page application (no routing)
- ⚠️ No real-time data refresh (manual reload required)

## Performance Benchmarks
Tested with 5,000 rows × 8 columns:
- Initial render: 340ms ✅
- Filter operation: 145ms ✅
- Sort operation: 78ms ✅
- Export CSV: 1,240ms ✅

## Troubleshooting

### Issue: Data not loading
**Solution:** Check browser console for errors. Verify data format matches expected structure.

### Issue: Layout broken on ultrawide
**Solution:** Ensure viewport meta tag is present: `<meta name="viewport" content="width=device-width, initial-scale=1.0">`

### Issue: Slow performance with large dataset
**Solution:** Enable virtual scrolling by setting `USE_VIRTUAL_SCROLL = true` (line 23)

## Support
Contact: finance-analytics@company.com
Documentation: https://company.sharepoint.com/sites/finance/dashboards
```

---

## 9. Deployment Checklist

Before deploying to production, verify:

### Pre-Deployment
- [ ] All CRITICAL guardrails implemented (F1, F2, F3, D1, D2, P1, P2)
- [ ] WCAG AA contrast ratios verified (use WebAIM checker)
- [ ] Tested in Edge, Chrome, Firefox
- [ ] Tested at 1920x1080, 1366x768, 3840x1080
- [ ] Performance benchmarks met (initial render <500ms)
- [ ] No console errors or warnings
- [ ] No localStorage/sessionStorage usage
- [ ] All data edge cases handled (null, zero, extreme values)
- [ ] Export functionality working (CSV/Excel)
- [ ] Keyboard navigation tested (Tab, Enter, Space, Arrows)

### Data Validation
- [ ] Data source connection tested
- [ ] Currency conversion logic verified
- [ ] Variance calculations accurate
- [ ] Aggregations match source system
- [ ] Row Level Security respected (if applicable)

### User Acceptance
- [ ] Stakeholder review completed
- [ ] Filters match business requirements
- [ ] Export format approved by finance team
- [ ] Visual design matches corporate branding
- [ ] Mobile/tablet view acceptable (if required)

### Documentation
- [ ] Inline code comments for complex logic
- [ ] README with setup instructions
- [ ] Known limitations documented
- [ ] Support contact information included
- [ ] Version number updated

---

## 10. Quick Reference

### Color Palette
```css
--primary: #0078D4        /* Primary actions, links */
--success: #107C10        /* Positive variances */
--danger: #D13438         /* Negative variances */
--warning: #FFB900        /* Warnings, alerts */
--bg-primary: #FFFFFF     /* Main background */
--text-primary: #323130   /* Body text */
```

### Typography Scale
- H1: 24px / 600 weight
- H2: 20px / 600 weight
- H3: 16px / 600 weight
- Body: 14px / 400 weight
- Small: 12px / 400 weight

### Performance Targets
- Initial render: <500ms
- Filter operation: <200ms
- Sort operation: <100ms (1000 rows)
- Export generation: <2000ms

### Accessibility Requirements
- Contrast: 4.5:1 (normal text), 3:1 (large text/UI)
- Keyboard: Tab, Enter, Space, Arrow keys
- ARIA: roles, labels, live regions
- Focus indicators: 2px solid outline

### Testing Resolutions
- Standard HD: 1920×1080
- Laptop: 1366×768
- Ultrawide: 3840×1080

---

## Version History

**v2.0** (October 2025)
- Comprehensive guardrail system
- Power BI integration patterns
- Performance benchmarks
- Accessibility standards

**v1.0** (Initial Release)
- Basic HTML/CSS/JS guidelines
- Simple validation rules

---

## Additional Resources

### Tools
- **WebAIM Contrast Checker:** https://webaim.org/resources/contrastchecker/
- **Chrome DevTools:** Lighthouse accessibility audit
- **MDN Web Docs:** https://developer.mozilla.org/
- **Power BI Custom Visuals:** https://learn.microsoft.com/power-bi/developer/visuals/

### Learning Resources
- **WCAG Guidelines:** https://www.w3.org/WAI/WCAG21/quickref/
- **JavaScript Performance:** https://web.dev/fast/
- **Financial Reporting Standards:** IFRS, GAAP documentation

---

## License & Usage

These guardrails are designed for Finvision internal use and Power BI visualization development. Adapt as needed for your specific requirements while maintaining the core principles of accessibility, performance, and Power BI compatibility.

**Last Updated:** October 2025  
**Maintained By:** Finvision Analytics Team  
**Questions:** Contact Bjorn Braet