# Open Questions — Blocking v1 Scope

Before any build work, five questions need answers. The answers determine the product.

## 1. Target user

Certified Belt (Green / Black) or untrained ops manager?

- Belt: product is a faster workflow around tools they already know. Competes head-on with Minitab.
- Untrained ops manager: product teaches + executes DMAIC for someone who has never been trained. Different UX, different pricing, different marketing. Much larger market, lower willingness-to-pay per user.

Research implication: Minitab's mid-market reviews show most licenses go unused because "too complex" — that's the signal that untrained is the underserved segment.

## 2. Industry wedge

General-purpose or anchored to a specific vertical?

Shawn's ops background (logistics, EV conversions, operations across diverse sectors) is a natural wedge. Anchor choices:

- Logistics / supply chain ops
- Manufacturing (Edco-type deployments)
- Services operations (call centers, healthcare ops)
- Horizontal, sell to anyone with a process

Horizontal is harder to market; vertical is easier to close but caps TAM.

## 3. Data inputs

CSV / spreadsheet upload only, or live connectors to external systems?

- CSV only: simple MVP, but every customer does the work of pulling data
- Connectors (Qualtrics, SurveyMonkey, Zendesk, ERP, SCADA): much bigger engineering lift, much stickier product

Recommend starting CSV + one survey integration (Qualtrics or SurveyMonkey) and adding others per customer demand.

## 4. Guided style

Conversational coach (chat-driven walk-through of DMAIC) or wizard-driven artifact generator (form-based flow producing named deliverables: charter, SIPOC, fishbone, control plan)?

- Conversational: feels modern, risk of drift, harder to produce consistent outputs
- Wizard: predictable outputs, feels more like existing enterprise software

Hybrid is possible and probably the right answer — wizard for structure, chat for Q&A inside each phase.

## 5. Deployment model

External SaaS from day one, or prove it internally (Edco-type deployment) first and productize once it's working?

- SaaS-first: faster to market feedback, needs pricing/billing/support infra
- Internal-first: zero distribution risk, battle-tested before launch, slower to revenue, but the article/portfolio value is enormous — "here's the tool I built that cut our LSS project time in half"

Internal-first also aligns with Shawn's career-positioning strategy (portfolio / article pipeline).

## Cross-cutting

These aren't independent — answer 1 (target user) constrains 2-5. If target is the untrained manager, you bias toward wizard UX, simpler connectors, internal-first proof. If target is the Belt, conversational + power connectors + SaaS.
