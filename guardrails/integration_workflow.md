\*\*Content\*\*: (Create this file)



```markdown

\# Component Library Integration Workflow



\## Claude's Decision Process



1\. \*\*Receive User Request\*\*

&nbsp;  - Parse intent

&nbsp;  - Identify dashboard type

&nbsp;  - Extract requirements



2\. \*\*Call html:guardrails\*\*

&nbsp;  ```javascript

&nbsp;  const result = await html\_guardrails();

&nbsp;  const token = result.guardrail\_token;

&nbsp;  ```



3\. \*\*Analyze Requirements Against Library\*\*

&nbsp;  ```javascript

&nbsp;  const needs = {

&nbsp;    metrics: \['revenue', 'growth', 'margin'],

&nbsp;    visualizations: \['trend', 'comparison'],

&nbsp;    interactions: \['filter', 'date-select'],

&nbsp;    layout: 'executive-summary'

&nbsp;  };

&nbsp;  

&nbsp;  const components = mapNeedsToComponents(needs);

&nbsp;  // Returns: \['kpi-strip', 'kpi-standard', 'line-chart', 'button-group']

&nbsp;  ```



4\. \*\*Select Layout Archetype\*\*

&nbsp;  - Executive Summary → KPI Strip + Golden Split

&nbsp;  - Financial Analysis → Nested KPIs + Three Column

&nbsp;  - Operational → Sidebar + Main Content

&nbsp;  - Comparison → Hierarchical Table + Bars



5\. \*\*Compose HTML\*\*

&nbsp;  - Start with base template

&nbsp;  - Add selected components

&nbsp;  - Apply theme (light default)

&nbsp;  - Integrate icons (Lucide)

&nbsp;  - Ensure responsiveness



6\. \*\*Validate\*\*

&nbsp;  ```javascript

&nbsp;  const validation = await html\_validate\_mockup({

&nbsp;    guardrail\_token: token,

&nbsp;    html: generatedHTML,

&nbsp;    expected\_library: "Lucide",

&nbsp;    expected\_theme: "light"

&nbsp;  });

&nbsp;  ```



7\. \*\*Iterate if Needed\*\*

&nbsp;  - Fix violations

&nbsp;  - Revalidate

&nbsp;  - Deliver final HTML



\## Automatic Screenshot Learning



When user provides screenshot:



1\. \*\*Visual Analysis\*\*

&nbsp;  - Extract colors, spacing, typography

&nbsp;  - Identify components (known vs unknown)

&nbsp;  - Measure proportions and layouts



2\. \*\*Pattern Extraction\*\*

&nbsp;  - Detect new component patterns

&nbsp;  - Document variations of existing components

&nbsp;  - Note innovative interactions



3\. \*\*Library Update\*\*

&nbsp;  - Add new components to component\_library.md

&nbsp;  - Generate HTML/CSS templates

&nbsp;  - Update decision tree

&nbsp;  - Create validation rules



4\. \*\*Log \& Version\*\*

&nbsp;  - Add to screenshot\_analysis\_log.md

&nbsp;  - Increment library version

&nbsp;  - Update component\_metadata.json

```



---



\### 3. docs/component\_catalog.md



\*\*Content\*\*: (Already created in artifact - "Component Catalog \& Usage Guide")



\*\*Purpose\*\*:

\- Quick reference for Claude and users

\- Component selection matrix

\- Common patterns and combinations

\- Copy-paste templates



---

