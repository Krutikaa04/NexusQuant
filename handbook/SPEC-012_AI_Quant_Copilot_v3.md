
# SPEC-012 — AI Quant Copilot
**AegisOS | Version 3.0 | AI Implementation Contract**

## 1. Purpose

Provide an AI orchestration layer that assists quantitative researchers by
routing requests to platform services, explaining results, reviewing research,
and generating reports. The AI never bypasses platform governance or directly
places trades.

---

## 2. Responsibilities

Owns
- Intent routing
- Tool orchestration
- Report generation
- Research review
- Strategy review
- Portfolio explanation
- Risk explanation
- Documentation generation

Never Owns
- Trading decisions
- Risk approval
- Broker execution
- Direct database writes

---

## 3. Core Components

- Intent Router
- Tool Registry
- Conversation Manager
- Prompt Builder
- Response Formatter
- Report Generator
- Audit Logger

---

## 4. Canonical Types

ChatSession
ToolInvocation
AIResponse
ResearchReview
StrategyReview
ReportRequest
ReportDocument

---

## 5. Tool Registry

Market Intelligence
- get_market_data()
- get_market_regime()

Research OS
- get_projects()
- review_experiment()

Alpha Factory
- review_strategy()
- explain_features()

Validation Platform
- summarize_validation()

Decision & Risk
- explain_decision()

Portfolio Intelligence
- analyze_portfolio()

Execution Intelligence
- execution_summary()

Every tool is read-only unless explicitly approved.

---

## 6. Domain Interfaces

CopilotService
- chat()
- invoke_tool()
- generate_report()
- summarize()

ToolRouter
- register_tool()
- resolve_tool()
- authorize()

ConversationService
- create_session()
- load_context()
- archive_session()

---

## 7. API Contracts

POST /ai/chat
POST /ai/report
POST /ai/review
GET  /ai/history
GET  /ai/tools

---

## 8. Event Contracts

Consumes
- ValidationCompleted
- PortfolioUpdated
- TradeRejected
- RiskViolationDetected

Publishes
- AIReportGenerated
- ResearchReviewCompleted
- ToolInvocationLogged

---

## 9. Business Rules

- AI must use platform APIs.
- Responses distinguish facts from opinions.
- Every tool invocation is audited.
- Recommendations include supporting evidence.
- No hidden business logic inside prompts.

---

## 10. Response Schema

Includes
- Summary
- Evidence
- Sources
- Confidence
- Recommended Actions
- Limitations

---

## 11. Configuration

MAX_CONTEXT_LENGTH
MAX_TOOL_CALLS
REPORT_TEMPLATE
DEFAULT_MODEL
SESSION_TTL

---

## 12. Performance

Intent routing <50ms
Tool orchestration async
Streaming responses supported

---

## 13. Security

JWT authentication
RBAC
Tool-level authorization
Prompt injection protection
Conversation audit logging

---

## 14. Testing

Unit
- Intent routing
- Tool resolution
- Response formatting

Integration
- Multi-tool workflows

Security
- Prompt injection
- Permission validation

---

## 15. File Structure

services/ai_copilot/

controllers/
services/
router/
tools/
prompts/
reports/
events/
tests/

---

## 16. Dependency Matrix

Depends On
- SPEC-001..SPEC-011

Requires
- Event Fabric
- All public domain APIs

Out of Scope
- Model training
- Broker execution
- Strategy implementation

---

## 17. Claude Implementation Sequence

1. Canonical types
2. Tool registry
3. Intent router
4. Conversation manager
5. Report generator
6. REST APIs
7. Event integration
8. Tests

---

## 18. Acceptance Criteria

- AI accesses domains only through APIs.
- Tool invocations are auditable.
- Responses include evidence and confidence.
- Tool authorization enforced.
- >90% core test coverage.
