# DomeSim Code House Investor Summary

*A humble starting home built around single mothers and veterans*

I am building DomeSim to make a humble, efficient dome home attainable for single mothers, veterans, and people working toward stability. The aim is a practical place to begin: useful shelter, manageable upkeep, and a way to add space or capability as resources grow. I call it a "code-house": a home that applies software development principles to its parts, construction, maintenance, and future upgrades.

This purpose is personal. I grew up with a single mother whose housing burden took money and time our family needed. As a Navy veteran and programmer, I want to build something that gives people a firmer starting point. For a mother, that can mean more room in her budget and more time with her children. For a veteran, it can mean an independent home and opportunities to use fabrication and repair skills in a community. Their practical needs should shape the product.

The codebase connects design, fabrication planning, production economics, and communication. Shared geodesic geometry and costing models generate dimensions, material quantities, cut lists, and cost and labor estimates. Interactive design tools let people inspect panels, layers, utilities, foundations, and whole sites. Fabrication exports turn solved parts into drawings and jig instructions. Assembly-line simulations examine bottlenecks, staffing, throughput, and sensitivity to assumptions. The project also supports illustrated books, narrated lessons, campaign releases, and a website with commerce and community features.

The physical design follows the same logic as maintainable software: reuse standardized parts, define connections clearly, separate functions, and change one component without rebuilding everything. Repeated panel designs, reusable jigs, replaceable enclosure layers, and a concentrated utility core are intended to make assembly, repair, and upgrades easier. Standard pad connections support the longer-term vision of owners improving their home and moving it between host sites. In the software, shared specifications, geometric checks, and versioned outputs keep revisions traceable.

Process optimization begins by simplifying the core workflow. A deliberately small recurring set of frame and panel fabrication operations gives training, batching, fixtures, and bottleneck improvement a focused target. The goal is to pay for precision and setup once, reuse them across builds, and measure whether each iteration reduces errors, waste, and effort. The proposed business opportunity includes plans, kits, components, utility cores, and compatible upgrades, supported by a proposed network of owners, pad hosts, paid quilters, and veteran builders.

The next investment should fund measured prototypes, engineering review, enclosure and moisture testing through the seasons, tooling, and an initial repeatable production run. Working software and early frame experimentation provide a starting point; compliant residential use, full delivered cost, durability, and customer demand still require validation. Success means demonstrating a modest home people can afford to begin with and improve over time, while earning a sustainable business from making that process dependable.

Project source and documentation: [DomeSimulator](https://github.com/dkzeanah/DomeSimulator).

---

# DomeSim Investor Numbers

*USD model estimates recomputed October 14 2026*

Reference is the **base infrastructure article**: customer-supplied trees, soft cap, utility core, window AC and **zero quilt insulation**. Solver geometry: 19.42 ft across; 277 sq ft of ten-sided floor; 40 panels of two shapes and 120 members. This is not a finished residential-home price.

| Model input | Declared assumption | Model input | Declared assumption |
| --- | --- | --- | --- |
| Loaded labor rate | $28/hour | Shop overhead | 18.0% of direct cost |
| Warranty reserve | 4.0% of direct cost | Maker markup | 20.0% of build cost |
| Regional freight | $1,250 | Timber acquisition | $0; owner supplies trees |

| Unit economics | USD |
| --- | --- |
| Materials and components | $6,337.23 |
| Shop/yard labor (67.3 hours) | $1,884.26 |
| Direct cost subtotal | $8,221.49 |
| Overhead allowance | $1,479.87 |
| Warranty reserve | $328.86 |
| Modeled build cost | $10,030.22 |
| Base article list price | $12,036.26 |
| Price less build cost | $2,006.04 |
| Share of selling price | 16.7% |

**Margin math:** $10,030.22 x (1 + 20.0%) = $12,036.26. ($12,036.26 - $10,030.22) / $12,036.26 = 16.7%. This is surplus after modeled overhead and warranty, not after-tax profit or investor return.

| Campaign allocation | USD |
| --- | --- |
| Production tooling | $60,800 |
| Validation and R&D | $34,850 |
| Quilts and fulfillment | $14,350 |
| Declared total | $110,000 |

**Budget reconciliation:** the test dome/pad line is $4,200; the modeled base build plus pad is $16,270. If that line must fund this scope, its gap is $12,070. Replacing only it gives $122,070 before fees and contingency. Salary and marketing are not itemized in the declared goal.

**Placement scope:** buyer dome plus freight $13,286; separate host pad $6,240; combined base infrastructure $19,526. Land, tax, complete site development, residential fit-out/insulation, and customer-site setup remain outside this package.

| Build-cost scenario | Modeled cost | Price less cost | Share of price |
| --- | --- | --- | --- |
| Baseline | $10,030.22 | $2,006.04 | 16.7% |
| Cost +10% | $11,033.24 | $1,003.02 | 8.3% |
| Cost +20% | $12,036.26 | $0.00 | 0.0% |

**Repeatability target:** 20% fewer modeled labor hours would save 13.5 hours and $460/unit including proportional overhead/warranty, at unchanged rates. This is a scenario, not an achieved improvement. Sale price is held fixed in the sensitivity table.

**Before underwriting scale:** measure person-hours, site setup, finished occupancy costs, production capacity, demand and working capital. The 67.3-hour estimate is shop/yard work, not a complete-home schedule. Model validators passed; physical performance and operating break-even still need evidence.

Calculation sources: seed_model.quote(), seed_model.seed_geometry(), kickstarter.cost_stack() and kickstarter.goal_lines(). Material rates and the campaign budget are project allowances, not new supplier quotations.
