# Civic SahAI — Project Context & Engineering Handoff

**Last updated:** 12 October 2026  
**Project type:** Google AI Builder Hackathon project  
**Current phase:** MVP development  
**Primary objective:** Build an AI-assisted civic incident reporting and municipal resource allocation platform.

---

## 1. Project Overview

### What is Civic SahAI?

Civic SahAI is a unified platform that helps citizens report civic issues and helps city administrators prioritize incidents and allocate municipal resources more effectively.

Examples of civic issues include:
- Potholes and damaged roads
- Garbage accumulation and sanitation problems
- Broken streetlights
- Water leakage and drainage problems
- Damaged public infrastructure
- Other municipal maintenance issues

The platform has two primary user experiences:

1. **Citizen application:** Citizens report problems, track complaints, view incident details, and discover similar complaints.
2. **City administrator dashboard:** Municipal administrators monitor incidents across zones, understand citywide workload, identify high-priority problems, and evaluate resource allocation recommendations.

The platform should use Google Cloud technologies as extensively as practical because it is being developed for a Google AI Builder hackathon.

### Core problem statement

Municipal bodies receive complaints across multiple areas, but deciding which incidents to address first and how to distribute limited personnel, equipment, and other resources is difficult.

Civic SahAI aims to turn individual citizen complaints into structured civic incidents and use incident severity, affected population, location context, complaint volume, and incident age to support more effective prioritization and resource allocation.

### Product vision

Move from a complaint-centric system to an **incident-centric, data-driven civic operations platform**.

Multiple complaints about the same underlying issue should ideally contribute to a consolidated incident rather than create unnecessary duplicate work.

---

## 2. Confirmed Technology Decisions

| Layer | Decision |
|---|---|
| Citizen frontend | React + TypeScript |
| Administrator frontend | React + TypeScript, within the unified application |
| Backend | Python + FastAPI |
| Primary database | Google Cloud SQL, using a relational database approach |
| Cloud platform | Google Cloud Platform |
| Deployment target | Google Cloud Run |
| Repository | One unified repository |
| API style | HTTP REST APIs |
| Architecture | Modular monolith with clear separation of concerns |
| AI | Google Cloud AI capabilities, selected according to specific MVP use cases |

### Important database decision

Firestore was initially considered, but the project subsequently switched to **Cloud SQL** because the domain contains relational entities and workflows, such as users, complaints, incidents, zones, resources, and allocations.

Do not revert to Firestore without an explicit architectural decision.

The precise Cloud SQL engine (PostgreSQL or MySQL) should be verified in the existing repository and configuration rather than assumed.

### Google Cloud principles

Prefer GCP-native services when they materially improve the solution:

- Cloud Run for application deployment
- Cloud SQL for relational persistence
- Cloud Storage for complaint image attachments, if required
- Google Cloud AI services for suitable AI-powered features
- Cloud Logging and Monitoring for operational visibility
- Secret Manager and service accounts for secure configuration and service identity

These are architectural preferences and potential integrations, not confirmation that every service has already been configured.

---

## 3. Architecture and Repository Principles

The application should remain a unified codebase, with explicit boundaries between frontend functionality and backend responsibilities.

Expected logical separation:

- Citizen-facing UI
- Administrator-facing UI
- Shared frontend components and API clients
- Backend API layer
- Domain/business logic
- Data access layer
- Database models and schemas
- Configuration and infrastructure
- Automated tests

The backend should follow enterprise-level coding practices:

- Clear separation of concerns
- Small, cohesive modules
- Explicit request and response schemas
- Centralized configuration
- Consistent error handling
- Dependency injection where appropriate
- Database transactions for related updates
- Database constraints and indexes
- Type hints and readable naming
- Automated unit and integration tests
- Security-conscious authorization and validation
- Maintainable, extensible code rather than a monolithic route implementation

Do not create unnecessary microservices for the MVP. A modular monolith is the preferred starting point unless the current repository demonstrates a compelling reason otherwise.

### Repository structure

The original implementation prompt called for a unified repository with clear frontend/backend separation. The actual current directory structure must be inspected before modifying it.

A possible logical structure is:

```text
civic-sahai/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── features/
│   │   │   ├── citizen/
│   │   │   └── administrator/
│   │   ├── components/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types/
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   └── main.py
│   ├── tests/
│   └── pyproject.toml
├── infra/
├── docs/
├── .env.example
└── README.md
```

**This is illustrative, not a verified copy of the existing repository.** Preserve the established structure unless an actual need for change is identified.

---

## 4. Functional Scope

### 4.1 Citizen application

The citizen experience has been discussed around the following screens.

**A. Homepage / citizen dashboard**

Purpose:
- Introduce the service and guide citizens toward reporting an issue.
- Show relevant homepage content and calls to action.
- Provide access to existing complaints and complaint tracking.
- Surface similar or nearby reported issues where appropriate.

The homepage API was discussed with a requirement to return all text and content required to render the homepage, aligned with the supplied Figma design rather than hardcoding all copy in the frontend.

**B. Register complaint**

Purpose:
- Allow citizens to submit a new civic complaint.
- Capture the issue type, description, location, and other fields required by the agreed design.
- Potentially accept supporting images.
- Associate the report with the reporting citizen.
- Return a useful confirmation and complaint identifier.

The API contract was discussed against a supplied Figma screen.

The exact fields, validation rules, and JSON property names should be recovered from the original contract or the current repository.

**C. Complaint details**

Purpose:
- Show the full information for a particular complaint or its associated incident.
- Display status, description, location, and timestamps.
- Show available incident progress information.
- Surface related or similar complaints if included in the approved screen.

An API contract for this screen was discussed using a supplied Figma design.

**D. All complaints**

Purpose:
- Retrieve the citizen's complaints.
- Support a list or history view.
- Display relevant information such as complaint reference, issue category, location, status, and reporting date.

An API contract for retrieving all complaints was discussed.

**E. Similar complaints**

A similar-complaints section was explicitly added to the citizen experience.

The intent is to help citizens discover reports that may refer to the same underlying civic problem. Similarity could eventually use location proximity, issue category, text similarity, or AI-assisted matching.

The exact matching algorithm and whether duplicate reports automatically link to an existing incident have not been finalized.

### 4.2 City administrator dashboard

The administrator experience is intended to support city operations rather than merely display complaint counts.

The planned dashboard includes:

- Reported incidents
- Open incidents
- Citywide operational burden
- Incident priority rankings
- Zone-level workload
- Resource availability and utilization
- Resource allocation suggestions
- Views that highlight urgent or underserved areas

The project has also discussed building additional administrator screens to make incident priority and resource allocation strategies visible.

The exact list of screens, navigation, and data visualizations should be verified against the current Figma designs and repository.

---

## 5. Incident Prioritization Model

The project has explicitly identified four core factors for determining incident priority:

1. **Affected population:** How many people are impacted.
2. **Surrounding landmarks:** The importance of nearby public facilities or other significant landmarks.
3. **Issue type:** The nature and severity of the civic problem.
4. **Incident age:** How long the incident has remained unresolved.

The number of complaints associated with the incident is an additional explicitly discussed signal.

A future priority model could normalize these inputs and calculate a weighted score.

For example:

```text
priority_score =
    population_impact_score * population_weight
  + landmark_impact_score   * landmark_weight
  + issue_severity_score    * issue_weight
  + age_score               * age_weight
  + complaint_volume_score  * volume_weight
```

This is a conceptual example, not a finalized scoring formula. The weights, scales, normalization method, and treatment of missing data must be defined and tested.

### Zone-level versus citywide priority

The project explicitly discussed whether incident rankings should be within a zone or across zones.

The direction is to support **both local and citywide views**:

- Within-zone ranking helps a local team decide which incidents to address first.
- Cross-zone ranking helps city administrators compare demand and determine where limited resources should be deployed.

These are different decision contexts and should not be treated as interchangeable rankings.

For example, an incident can be a moderate priority within one zone but still be among the city's most urgent incidents when compared with all open incidents.

### Important design distinction

Keep the following concepts separate:

- Incident severity or priority
- Zone workload or burden
- Resource availability
- Allocation feasibility
- Allocation recommendation

A high-priority incident does not automatically mean that resources can be assigned immediately. The recommendation must also consider resource types, quantities, skills, travel or geographic constraints, and other relevant operational limitations.

---

## 6. Resource Allocation Logic

Resource allocation is a central capability of Civic SahAI.

The administrator should be able to understand:

- Which incidents need attention first.
- Which zones are experiencing the greatest demand.
- What resources are available.
- Where current resources are deployed.
- Which alternative allocation strategies are feasible.
- Why a particular recommendation is being made.

A reasonable conceptual workflow is:

1. Retrieve unresolved incidents.
2. Calculate or retrieve incident priority scores.
3. Aggregate demand by zone.
4. Retrieve available resources and current assignments.
5. Identify resource requirements for each incident.
6. Generate feasible allocation candidates.
7. Rank candidates according to priority, urgency, and operational constraints.
8. Present recommendations with clear explanations.
9. Allow authorized administrators to review and approve allocations.
10. Persist approved allocations and update resource availability.

This is a proposed logical workflow, not a claim that an allocation engine has already been implemented.

### Explainability

Recommendations should provide a human-readable rationale, such as:

- High estimated population impact
- A critical public landmark nearby
- Long unresolved duration
- Multiple reports indicating a recurring problem
- Insufficient resource coverage in the affected zone

AI may help summarize evidence or explain recommendations, but core allocation constraints and arithmetic should be deterministic and testable.

---

## 7. Data Model and Domain Concepts

The domain has evolved from simple complaint tracking toward incident management and resource allocation.

The main concepts discussed or implied by the approved scope include:

| Entity | Responsibility |
|---|---|
| User / Citizen | Represents the person submitting complaints |
| Complaint | Records an individual citizen's report |
| Incident | Represents an underlying civic issue that may have multiple related complaints |
| Zone | Represents a geographic or administrative subdivision of the city |
| Location | Represents the geographic position of a complaint or incident |
| Resource | Represents personnel, equipment, or other operational capacity |
| Resource allocation | Records an assignment of resources to an incident or zone |
| Incident status / lifecycle | Tracks progress from reporting through resolution |
| Priority assessment | Stores or derives incident prioritization information |
| Landmark | Represents nearby public facilities or significant places used in impact assessment |

This table is a domain overview, not a statement that each concept exists as a separate database table.

### Important relationship

A useful target relationship is:

```text
Citizen
   |
   | submits
   v
Complaint --------\
Complaint ---------> Incident
Complaint --------/
                      |
                      | occurs in
                      v
                     Zone
                      |
Incident <--- Allocation ---> Resource
```

The actual schema may contain additional junction tables, historical records, assessment records, or status-history entities.

### Data-model implementation status

As of the latest project discussion:

- A data model had already been implemented and shared for review.
- The model was reviewed for gaps.
- The project then requested a prompt to bridge the identified gaps in the existing schema.
- The user explicitly clarified that the current data model is already implemented.
- There is currently no existing data to preserve and no migration concern.
- The next task is to make only the missing data-model changes, not to build services.

**Critical instruction for the next agent:** Do not recreate the data model from scratch. Inspect the current models, compare them against the gap analysis and approved domain requirements, and make only the necessary additive or corrective schema changes.

The exact list of previously identified schema gaps is not reproduced in this handoff. Retrieve the original review and gap-bridging discussion, or inspect the latest shared schema document, before implementing them.

---

## 8. Citizen Identity for the MVP

An explicit decision was made for the MVP:

**The backend should accept a user ID that uniquely identifies the citizen in a request header.**

This is a pragmatic identity mechanism for early development and testing.

The exact header name should be recovered from the existing API contracts. Do not assume that it is `X-User-Id` unless that name is already documented.

The implementation must consistently apply the agreed identity mechanism across citizen endpoints.

This is not a production authentication strategy. Before production use, the project should adopt appropriate authentication, identity verification, and authorization mechanisms rather than trusting an arbitrary client-supplied identifier.

---

## 9. API Contracts Discussed

The following endpoints or endpoint responsibilities have been discussed.

The table lists logical operations, not guaranteed final URLs.

| API operation | Purpose | Discussion status |
|---|---|---|
| Get homepage content | Return all homepage content required by the Figma screen | Contract discussed |
| Submit complaint | Accept a citizen's civic issue report | Contract discussed |
| Get complaint details | Retrieve the details of a complaint | Contract discussed |
| Get all complaints | Retrieve the citizen's complaint list | Contract discussed |
| Get register-complaint page content | Return the content needed to render the registration screen | Explicitly asked about |
| Get similar complaints | Discover related complaints | Feature discussed; contract needs verification |
| Get administrator dashboard | Retrieve city and incident metrics | Scope discussed |
| Get incident rankings | Retrieve priority-ranked incidents | Scope discussed |
| Get allocation suggestions | Retrieve recommended resource allocations | Scope discussed |

The original API contract discussions were based on supplied Figma screenshots, with a preference for returning screen content through APIs where agreed.

### API contract preservation rules

Before implementing or modifying endpoints:

1. Inspect the existing OpenAPI documentation, route handlers, schema definitions, and API documentation.
2. Recover the previously agreed request and response JSON structures.
3. Preserve exact header names, field names, enum values, and error response conventions.
4. Do not invent new endpoint paths if contracts already exist.
5. Keep screen configuration/content endpoints distinct from transactional operations.
6. Ensure response schemas are explicit and typed.
7. Confirm whether complaint detail endpoints operate on complaint IDs, incident IDs, or both.

Do not interpret “contract discussed” as proof that the endpoint is implemented or working.

---

## 10. AI Strategy

The project is intended to use AI in meaningful ways rather than simply adding a chatbot.

Potential AI capabilities consistent with the product vision include:

- Classifying complaint descriptions into issue categories.
- Extracting structured information from free-text reports.
- Identifying similar complaints.
- Helping detect reports that may concern the same incident.
- Summarizing incidents for city administrators.
- Generating human-readable explanations of allocation recommendations.
- Helping administrators understand citywide patterns.

These are candidate capabilities. The exact model, service, prompts, and MVP feature commitments should be checked against the existing implementation plan.

### Recommended separation of responsibilities

Use deterministic backend logic for:

- Database integrity
- Identity and authorization enforcement
- Priority-score calculations
- Resource availability and capacity constraints
- Allocation feasibility
- Transactional state changes

Use AI where it offers genuine value, such as:

- Understanding unstructured descriptions
- Similarity analysis
- Summarization
- Natural-language explanations

AI-generated classifications and recommendations should be validated and should not silently override operational constraints.

---

## 11. GCP Deployment and Operations

The agreed deployment target is Google Cloud Run, with Cloud SQL as the relational database.

Potential deployment considerations include:

- Separate configuration for local development and deployed environments.
- Cloud Run service configuration and environment variables.
- Secure Cloud SQL connectivity.
- Least-privilege service accounts.
- Secret Manager for sensitive configuration.
- Structured logging and health checks.
- Database connection pooling and connection limits.
- CORS and frontend/backend URL configuration.
- Reproducible build and deployment instructions.

GCP project creation, service enablement, IAM configuration, container builds, and deployment should be verified rather than assumed complete.

The original project also requested GCP setup commands and environment configuration. Retrieve the current README and infrastructure configuration to determine which setup tasks have already been completed.

---

## 12. Confirmed Progress and Decisions So Far

The following progress is supported by the project discussions.

### Product and architecture

- Civic SahAI was selected as the project name.
- The project was framed as a civic sustainability and municipal operations solution.
- Citizen and administrator experiences were defined.
- Resource allocation was established as a central differentiator.
- The priority factors were discussed.
- The need for both zone-level and cross-zone ranking was discussed.
- The unified repository approach was selected.
- React + TypeScript and FastAPI were selected.
- The database decision changed from Firestore to Cloud SQL.
- Cloud Run was selected as the deployment target.

### Citizen experience

- Citizen homepage/dashboard requirements were discussed against a Figma screenshot.
- Complaint submission API requirements were discussed.
- The content endpoint for the registration page was discussed.
- Complaint detail API requirements were discussed.
- All-complaints API requirements were discussed.
- A similar-complaints section was added.
- The MVP citizen identity mechanism using a unique user ID in a request header was agreed upon.

### Administrator experience

- A city administrator dashboard was conceptualized.
- Reported incidents, city burden, and open incidents were identified as dashboard metrics.
- Incident priority and allocation strategies were identified as important views.
- The distinction between zone-local and citywide rankings was discussed.

### Data model

- An initial data model was already implemented and shared.
- A review for schema gaps was requested.
- The next step was narrowed to bridging those gaps in the existing model.
- No existing records or migration requirements need to be considered.
- Service implementation was explicitly excluded from that schema-gap task.

### What is not confirmed

This handoff does not establish that:

- All frontend screens have been implemented.
- All API endpoints have been implemented.
- The database schema is complete.
- The allocation algorithm is implemented.
- AI integrations are working.
- Cloud infrastructure has been deployed.
- End-to-end tests pass.

Verify these claims against the actual repository.

---

## 13. Current Priority: Bridge Existing Data-Model Gaps

The latest explicit implementation task is to complete the missing parts of the existing data model.

The implementation agent should:

1. Read the current repository structure and engineering instructions.
2. Locate all existing ORM models, database schemas, enums, and related tests.
3. Retrieve the previously shared schema-gap analysis.
4. Compare the current implementation with the documented domain and API requirements.
5. Identify only the confirmed missing entities, fields, relationships, constraints, and indexes.
6. Make the minimum necessary changes to the existing data model.
7. Add or update model-level tests where appropriate.
8. Validate imports, type checks, schema consistency, and tests that can run locally.
9. Document any unresolved design decisions.

### Explicit restrictions

For this task:

- Do not rebuild the existing schema.
- Do not implement API routes or controllers.
- Do not implement business services.
- Do not implement resource allocation logic.
- Do not add AI integrations.
- Do not start or deploy backend services.
- Do not introduce data migrations solely for hypothetical existing records.
- Do not modify unrelated frontend functionality.
- Do not add speculative entities or fields without tracing them to an approved requirement.

The absence of existing data removes the need to preserve current production records, but database constraints, referential integrity, and a sound schema design remain essential.

The scope is **data-model changes only**.

---

## 14. Recommended Instructions for the Next Agent

Use the following as the starting instruction when opening the project in an agentic coding environment:

> You are continuing development of Civic SahAI, an AI-assisted civic incident reporting and municipal resource allocation platform.
>
> Read this handoff document and the repository's existing engineering instructions before making changes. Treat the current repository as the source of truth for implementation status.
>
> The project uses React + TypeScript for the frontend, Python + FastAPI for the backend, Cloud SQL for relational persistence, and Google Cloud Run for deployment. It is a unified repository with clear architectural boundaries.
>
> The latest task is to bridge gaps in an already implemented data model. The existing schema has been reviewed, and specific gaps were identified in an earlier conversation. Recover that gap analysis if available; otherwise, inspect the latest schema document and repository to establish the gaps before changing code.
>
> Make only the required data-model changes. Do not recreate the schema, implement backend services or API endpoints, build the resource allocation engine, add AI functionality, deploy infrastructure, or modify unrelated features.
>
> There is currently no data that needs migration or preservation. Nevertheless, maintain relational integrity, appropriate constraints, indexes, type safety, naming consistency, and readable code.
>
> First summarize the existing schema and identified gaps. Then implement the smallest correct set of changes. Add focused tests where appropriate, run relevant local validations, and report changed files, design decisions, test results, and anything that remains unresolved.
>
> Do not claim a feature or test is complete unless you have verified it in the repository.

---

## 15. Repository Handoff Checklist

Before continuing, the next agent should establish the following facts.

- [ ] Locate the current repository and read its `README`.
- [ ] Read project-specific agent instructions and contribution guidelines.
- [ ] Inspect the current Git branch, working tree, and recent commits.
- [ ] Identify the database engine and ORM in actual use.
- [ ] Locate the existing data models and their tests.
- [ ] Retrieve the original schema-gap review and implementation prompt.
- [ ] Inspect existing API contracts and the Figma-linked requirements.
- [ ] Verify the user-ID request header convention.
- [ ] Identify which APIs and screens are implemented versus planned.
- [ ] Confirm the current GCP and deployment configuration.
- [ ] Make only the currently authorized changes.
- [ ] Record implementation progress and remaining work in project documentation.

---

## 16. Long-Term MVP Direction

After the data-model gap work is complete, a sensible implementation sequence is:

1. Finalize and validate the relational data model.
2. Freeze API request and response contracts.
3. Implement database access and the complaint lifecycle.
4. Implement citizen complaint submission and retrieval.
5. Implement similar-complaint discovery.
6. Implement incident priority calculations.
7. Implement zone-level and citywide administrator views.
8. Implement resource availability and allocation recommendations.
9. Integrate selected AI capabilities.
10. Connect the frontend to the backend.
11. Add end-to-end testing, observability, and deployment configuration.
12. Validate the complete MVP against the hackathon demonstration scenario.

This is a recommended order, not a claim that the work has already occurred.

---

## Final Handoff Summary

**Civic SahAI is an AI-assisted civic complaint and municipal resource allocation platform, being built as a Google AI Builder hackathon MVP.** Its agreed stack is React + TypeScript, Python + FastAPI, Cloud SQL, and Cloud Run, using a unified repository with clear separation of concerns.

The product includes a citizen reporting and complaint-tracking experience and an administrator dashboard for incident prioritization, citywide workload analysis, and resource allocation recommendations. Priority is intended to account for affected population, nearby landmarks, issue type, incident age, and complaint volume. Both zone-level and cross-zone ranking are relevant.

The most important current engineering instruction is to **continue from the existing implementation, not start over**. The data model already exists, a gap review has been performed, and the immediate task is to bridge those gaps only. No data migration is required, and services are explicitly out of scope for that task.

The next agent must recover the exact earlier schema-gap findings and inspect the current repository before implementing changes. This handoff provides the project context and decisions, while the repository and original schema review remain authoritative for exact code, contract details, and completion status.

# Civic SahAI — Day-by-Day Implementation Plan

**Duration:** 7 days  
**Goal:** Deliver a working, demonstrable civic incident reporting and intelligent resource allocation MVP using Google Cloud technologies.

## Day 1 — Foundation and Data Model

**Objective:** Establish the application foundation and finalize the domain model.

### Tasks
- Review the existing repository, architecture, and engineering conventions.
- Finalize gaps in the existing relational data model.
- Verify relationships among citizens, complaints, incidents, zones, resources, and allocations.
- Establish database configuration and environment-variable conventions.
- Validate ORM models, constraints, relationships, and indexes.
- Establish or verify frontend and backend application entry points.
- Define and validate API contracts against the approved Figma screens.
- Document local development and GCP setup instructions.

### Deliverables
- Completed data-model gap fixes.
- Validated database models and focused tests.
- Working frontend/backend project structure.
- Agreed API contracts.
- Local development instructions.

### Acceptance criteria
- Existing schema is extended rather than rebuilt.
- Models import and pass relevant validations.
- API contracts are documented.
- No unnecessary services or unrelated features are implemented during schema-only work.

## Day 2 — Citizen Complaint Workflow

**Objective:** Make complaint reporting and retrieval work end to end.

### Tasks
- Implement homepage content retrieval.
- Implement complaint registration page content retrieval where required by the design.
- Implement complaint submission.
- Implement complaint details retrieval.
- Implement retrieval of all complaints belonging to a citizen.
- Apply the agreed MVP user-ID request header convention.
- Add request validation, consistent error responses, and database transactions where necessary.
- Connect the React screens to the backend.
- Add basic tests for successful submissions and validation failures.

### Deliverables
- Functional citizen reporting workflow.
- Persisted complaints in Cloud SQL.
- Complaint list and detail screens connected to real APIs.
- Basic API tests.

### Acceptance criteria
A citizen can submit a complaint, receive a reference, see it in their complaint list, and open its details.

## Day 3 — Incident Consolidation and Similar Complaints

**Objective:** Make complaint data useful for identifying underlying civic incidents.

### Tasks
- Implement the relationship between individual complaints and underlying incidents.
- Implement similar-complaint discovery using available signals such as:
  - Geographic proximity.
  - Issue category.
  - Description similarity.
- Define how new complaints are associated with existing incidents.
- Avoid silently merging unrelated issues.
- Add incident and complaint status handling as required.
- Display similar complaints in the citizen interface.
- Add representative test cases for matching and non-matching reports.

### Deliverables
- Similar-complaint functionality.
- A defined complaint-to-incident association flow.
- Citizen-facing related-complaint section.
- Tests for core matching scenarios.

### Acceptance criteria
Related reports can be surfaced together without automatically treating every nearby complaint as the same incident.

## Day 4 — Incident Prioritization and Administrator Dashboard

**Objective:** Enable administrators to identify the incidents requiring the most attention.

### Tasks
- Implement a deterministic incident-priority calculation.
- Include the agreed factors:
  - Affected population.
  - Nearby landmarks and their importance.
  - Issue type and severity.
  - Incident age.
  - Number of associated complaints.
- Normalize input values and configure weights.
- Define priority tiers and tie-breaking behavior.
- Support rankings within zones and across the city.
- Implement APIs for administrator metrics and ranked incidents.
- Connect dashboard views to real data.

### Deliverables
- Incident-priority calculation.
- Zone-level and citywide incident rankings.
- Administrator dashboard with reported/open incidents and workload indicators.
- Tests for scoring and ranking.

### Acceptance criteria
Given the same input data and configuration, the ranking is reproducible and explainable. Administrators can understand why an incident received its priority.

## Day 5 — Resource Allocation Recommendations

**Objective:** Translate incident priorities into actionable resource allocation suggestions.

### Tasks
- Define resource types, availability, capacity, and assignment constraints.
- Associate resource requirements with incidents.
- Implement a deterministic allocation strategy using incident priority and available capacity.
- Consider zone workload and geographic constraints where data is available.
- Prevent over-allocation of unavailable or already committed resources.
- Provide an explanation for each recommendation.
- Build administrator views for suggested assignments and resource utilization.
- Implement allocation approval and persistence if time permits.

### Deliverables
- Allocation recommendation engine.
- Resource availability and utilization indicators.
- Suggested incident-to-resource assignments.
- Administrator-facing explanations.

### Acceptance criteria
Recommendations respect the implemented resource constraints, explain their rationale, and can be evaluated against representative scenarios.

**Scope control:** Prefer a simple, explainable allocation heuristic over a complex optimization engine that cannot be validated within the deadline.

## Day 6 — AI Integration and GCP Deployment

**Objective:** Add a meaningful AI capability and make the MVP deployable.

### Tasks
- Select one or two AI use cases with clear value.
- Prefer complaint categorization, incident summarization, or semantic similarity if they improve the existing workflow.
- Integrate the selected Google Cloud AI service.
- Keep core scoring, resource constraints, and allocation calculations deterministic.
- Validate AI outputs and handle failures gracefully.
- Configure Cloud SQL connectivity and Cloud Run deployment.
- Configure environment variables, secrets, service accounts, and CORS.
- Add structured logging and health checks.
- Run integration tests against the deployed environment.

### Deliverables
- At least one working AI-assisted feature.
- Deployed or deployment-ready application.
- Verified database connectivity.
- Basic operational logging and error handling.

### Acceptance criteria
The application runs in the target environment, and its essential workflows remain usable if an optional AI capability fails.

## Day 7 — End-to-End Validation and Hackathon Demo

**Objective:** Stabilize the application and demonstrate its full value.

### Tasks
- Execute end-to-end citizen and administrator workflows.
- Verify complaint submission, retrieval, and similar-complaint discovery.
- Verify incident rankings across zones.
- Test allocation recommendations against known scenarios.
- Fix critical defects and obvious UI inconsistencies.
- Seed a representative demonstration dataset.
- Verify that metrics and dashboard rankings reflect the seeded data.
- Prepare a concise product narrative and demo script.
- Capture screenshots or a backup recording if needed.
- Verify deployment, configuration, and fallback behavior.

### Deliverables
- Stable MVP.
- Representative demo dataset.
- End-to-end validation results.
- Hackathon demonstration script.
- Deployment and troubleshooting notes.

### Acceptance criteria
The team can demonstrate the complete journey without relying on manually fabricated dashboard results.

---

## Daily Engineering Practices

Every day should include:

- A short team planning session.
- Explicit ownership of frontend, backend, data, and infrastructure tasks.
- Incremental integration rather than waiting until the end.
- Focused tests for newly implemented behavior.
- A working commit at the end of the day.
- A brief update to the README or project progress notes.

Keep unfinished features visible and prioritize a working vertical slice over a broad collection of incomplete screens.

## Priority Order if the Deadline Slips

| Priority | Capability |
|---|---|
| P0 — Essential | Complaint submission and retrieval |
| P0 — Essential | Persistent relational data |
| P0 — Essential | Administrator incident dashboard |
| P1 — High | Explainable incident priority ranking |
| P1 — High | Basic resource allocation recommendations |
| P1 — High | Cloud deployment |
| P2 — Valuable | Similar-complaint discovery |
| P2 — Valuable | One meaningful AI-assisted capability |
| P3 — Optional | Advanced optimization, sophisticated maps, and nonessential analytics |

The priority order is a contingency plan, not permission to disregard existing commitments. If a feature is already implemented, focus on validation rather than rebuilding it.

## Definition of Done

Civic SahAI is ready for its MVP demonstration when:

1. A citizen can submit and track a complaint.
2. Complaints are stored reliably in Cloud SQL.
3. Related reports can be surfaced or grouped appropriately.
4. An administrator can view open incidents and their priorities.
5. Priorities reflect the agreed factors and can be explained.
6. The system can recommend feasible resource assignments.
7. At least one AI capability contributes meaningful value.
8. The main application workflow is demonstrable in the target environment.
