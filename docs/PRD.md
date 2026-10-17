# PRD: Azure DevOps Ticket Intelligence MCP Server

| Field | Value |
|---|---|
| Status | Draft v0.4 |
| Owner | Karol |
| Last updated | 2026-10-17 |
| Related | [ARCHITECTURE.md](ARCHITECTURE.md) |

## 1. Summary

A remote MCP server, built with FastMCP (Python), that lets an AI assistant (Claude Desktop, Claude Code, VS Code, other MCP clients) work with Azure DevOps Services tickets **as the signed-in user**. It helps engineers analyze work items, assess the impact of a change, draft an implementation plan and produce technical documentation. Anything that writes back to Azure DevOps goes through an explicit human approval step.

The server calls Azure DevOps with the user's own identity, obtained through Microsoft Entra ID and the OAuth 2.0 On-Behalf-Of (OBO) flow. The assistant can never see or do more than the user could in the Azure DevOps web UI.

## 2. Problem

- Engineers spend significant time reading a ticket, chasing linked items, PRs, commits and wiki pages before they understand what a change touches.
- Impact assessment and implementation plans are written ad hoc, with inconsistent depth, and often not recorded back on the ticket.
- Generic AI assistants either have no access to Azure DevOps, or access it with a shared PAT, which breaks least privilege and audit attribution.
- Letting an AI write to the tracker unattended is not acceptable: ticket content is untrusted input and model output can be wrong.

## 3. Goals

| ID | Goal |
|---|---|
| G1 | Give an MCP client curated, token-efficient context about a work item and its surroundings (links, history, PRs, commits, wiki). |
| G2 | Support three guided workflows: ticket analysis, change impact assessment, implementation planning. |
| G3 | Produce technical documentation (ticket summary, design notes, release notes) as drafts the user can review. |
| G4 | Every write to Azure DevOps requires explicit approval by the human user, outside the model's control. |
| G5 | All Azure DevOps calls run under the signed-in user's identity (Entra ID + OBO). No PATs, no shared service account for user actions. |
| G6 | Every write is auditable: who approved it, what exactly was written, when. |

## 4. Non-goals (for v1)

- Running an LLM inside the server. The reasoning happens in the MCP client; the server provides data, workflow prompts and gated actions. (Revisit with MCP sampling later, see Architecture ADR-004.)
- Code changes, branch creation, PR creation or pipeline runs.
- Azure DevOps Server (on-premises). Only Azure DevOps Services (cloud).
- Multi-tenant SaaS. One Entra tenant, one or a few Azure DevOps organizations.
- Approval by someone other than the requesting user (delegated or multi-party approval).
- Organizations not backed by Entra ID (personal Microsoft accounts).

## 5. Users and personas

| Persona | Needs |
|---|---|
| Developer | Understand a ticket fast, see what else it touches, get a step-by-step plan. |
| Tech lead / architect | Consistent impact assessments, risk flags, plans recorded on the ticket. |
| QA engineer | Derive test scenarios and acceptance-criteria gaps from a ticket. |
| Product owner (secondary) | Clarity checks on ticket quality (missing acceptance criteria, ambiguities). |

All personas already have Azure DevOps access; the server never grants more.

## 6. User stories

1. As a developer, I ask "analyze ticket 1234" and get a summary, open questions, missing acceptance criteria and related items, based on real data from Azure DevOps.
2. As a developer, I ask "what is the impact of changing X in ticket 1234" and get affected areas (repos, files, components, linked items, recent PRs), risks and a confidence statement.
3. As a tech lead, I ask for an implementation plan for ticket 1234 and get ordered steps, estimates and test approach, citing the evidence it used.
4. As a developer, I ask to post the plan as a comment on the ticket. I see the exact content, approve or reject it, and only then is it written. The comment marks itself as AI-assisted and approved by me.
5. As a QA engineer, I ask for test scenarios derived from the acceptance criteria.
6. As any user, if I lack permission for an item, the assistant tells me so instead of guessing.

## 7. Functional requirements

### 7.1 Read and context gathering

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Get a work item by ID with curated fields (title, type, state, description, acceptance criteria, area/iteration path, tags, assignee), HTML converted to plain text or Markdown. | Must |
| FR-2 | Get comments and revision history of a work item (summarized/limited). | Must |
| FR-3 | List linked work items (parent, children, related, predecessor/successor) to a configurable depth. | Must |
| FR-4 | List artifact links: PRs, commits, branches, builds linked to a work item. | Must |
| FR-5 | Query work items with WIQL, read-only, with a result cap. | Should |
| FR-6 | Get PR details: title, description, changed files, status. | Should |
| FR-7 | Code search across repos (Azure DevOps Code Search) for symbols/terms mentioned in a ticket. | Should |
| FR-8 | Read and search wiki pages. | Should |
| FR-9 | All outputs are size-bounded and paginated; large bodies are truncated with an explicit marker. | Must |

### 7.2 Guided workflows (MCP prompts)

| ID | Requirement | Priority |
|---|---|---|
| FR-10 | `analyze_ticket` prompt: structured analysis template (summary, intent, ambiguities, missing ACs, dependencies). | Must |
| FR-11 | `assess_impact` prompt: impact template (affected components, data, APIs, consumers, risks, rollback, confidence). | Must |
| FR-12 | `plan_implementation` prompt: plan template (steps, order, test strategy, estimate, open questions). | Must |
| FR-13 | `write_tech_doc` prompt: documentation template (design note, release note, runbook snippet). | Should |
| FR-14 | Templates live in versioned files, not hard-coded, so they can be tuned without code changes. | Should |

### 7.3 Write-back with approval

| ID | Requirement | Priority |
|---|---|---|
| FR-15 | Propose a comment on a work item. | Must |
| FR-16 | Propose field updates, limited to the v1 allowlist: **tags** (add only, never remove) and **description** (only when the current description is empty). | Should |
| FR-17 | Propose creating a child task / wiki page from a plan. | Could |
| FR-18 | No write executes without a human approval captured outside the model (MCP elicitation in v1). If the client cannot ask the user, the write is refused (fail closed). | Must |
| FR-19 | The approved payload is exactly what gets written (content hash check between proposal and execution). | Must |
| FR-20 | Proposals expire (default 15 min) and are single-use. | Must |
| FR-21 | Written content carries an AI-assisted marker and the approving user's identity. | Must |
| FR-22 | Optimistic concurrency: a field update fails if the work item changed since the proposal (revision check). | Should |

### 7.4 Identity and access

| ID | Requirement | Priority |
|---|---|---|
| FR-23 | Users sign in with Entra ID through the MCP client's standard OAuth flow. | Must |
| FR-24 | The server exchanges the user's token for an Azure DevOps token via OBO; the user's token is never forwarded as-is. | Must |
| FR-25 | Access is limited by a server-side allowlist on top of the user's own permissions. v1: organization `myTicketOrg`, project `myTicketProject` only. | Must |
| FR-26 | Conditional Access / MFA challenges from OBO are surfaced to the user as a clear "re-authenticate" error. | Must |

## 8. Non-functional requirements

| ID | Area | Requirement |
|---|---|---|
| NFR-1 | Security | No secrets in code or config files; client secret/certificate from Key Vault or environment. Token caches encrypted at rest. |
| NFR-2 | Security | Ticket, comment, wiki and code content is treated as untrusted (prompt injection). Tool outputs mark it, write payloads are sanitized (no external images or links, no invisible characters), and write tools are never auto-approved. Threat model and tests: [ARCHITECTURE.md, section 10.1](ARCHITECTURE.md). |
| NFR-3 | Least privilege | The server exposes only allowlisted operations, because the Azure DevOps delegated permission (`user_impersonation`) is broad. |
| NFR-4 | Audit | Structured audit log in **Application Insights** for every proposal, decision and write: user OID/UPN, work item, payload hash, timestamp, result. |
| NFR-5 | Performance | p95 under 3 s for single-item read tools; OBO tokens cached per user until near expiry. |
| NFR-6 | Resilience | Honors Azure DevOps throttling (`Retry-After`, `X-RateLimit-*`), bounded retries with backoff. |
| NFR-7 | Observability | OpenTelemetry traces and metrics; no tokens or ticket bodies in logs. |
| NFR-8 | Compatibility | Streamable HTTP transport. Day-one clients: Claude Code CLI and Claude Code in VS Code (extension); MCP Inspector for development. Other clients are best effort. |
| NFR-9 | Maintainability | Python 3.12+, typed, tested; Azure DevOps access behind one client module. |

## 9. Release plan

The roadmap, with the requirements each step delivers and its exit criteria, lives in [ARCHITECTURE.md, section 13](ARCHITECTURE.md). It is kept in one place to avoid two diverging plans.

## 10. Success metrics

- Time from opening a ticket to a written plan: target 50% reduction (self-reported, then sampled).
- Share of AI proposals approved without edits; share rejected (quality signal).
- Zero writes without a recorded approval (hard requirement, verified from audit log).
- Zero incidents of access beyond the user's own permissions.

## 11. Assumptions and dependencies

- The Azure DevOps organization is connected to the company Entra ID tenant.
- A tenant admin can register an app and grant admin consent for the Azure DevOps delegated permission.
- MCP clients in use support OAuth for remote servers; for approval, they support MCP elicitation. Claude Code supports elicitation since v2.1.76; the VS Code extension's behavior must be verified in build step 7.
- Karol owns the Entra app registration. Granting admin consent for the Azure DevOps permission may still need a tenant administrator, depending on tenant consent settings.
- Azure DevOps REST API version 7.1 (or later GA version).

## 12. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Prompt injection in ticket text leads the model to propose harmful writes. | High | Human approval with exact payload shown, allowlisted operations, no destructive operations at all. |
| Client lacks elicitation support. | Medium | Fail closed in v1; web approval page as a later fallback. |
| Entra lacks Dynamic Client Registration / Client ID Metadata Documents. | Medium | FastMCP OAuth proxy (AzureProvider) bridges this. |
| Conditional Access blocks OBO (`interaction_required`). | Medium | Surface claims challenge; document required CA policy exceptions. |
| Azure DevOps throttling under bulk queries. | Low | Caps, caching, backoff. |
| Microsoft's own Azure DevOps remote MCP server covers the read side. | Low | Our value is the workflows, approval gate and audit; we can reuse it as reference. |

## 13. Build vs. reuse note

Microsoft ships an Azure DevOps MCP server (local, and a hosted remote endpoint GA since August 2026). As of that release the remote endpoint does not support Claude clients, because Entra does not offer dynamic client registration. It also provides generic CRUD tools, not guided analysis or an approval gate. This project focuses on those differentiators, and is also an explicit learning exercise in MCP, Entra ID and OBO.

## 14. Decisions (resolved 2026-10-16)

| # | Question | Decision |
|---|---|---|
| D1 | Day-one MCP clients | Claude Code CLI and Claude Code in VS Code. |
| D2 | Organizations and projects | Single organization `myTicketOrg`, single project `myTicketProject`. |
| D3 | Hosting and app registration | Azure Container Apps; Karol owns the Entra app registration. |
| D4 | Writable fields (FR-16) | Comments; tags (add only); description (only when empty). |
| D5 | Audit log | Application Insights. |
| D6 | Code Search | Enabled in the organization; FR-7 is in scope. |
| D7 | Admin consent | Personal learning tenant; Karol is tenant administrator and grants consent himself. |
| D8 | MFA / Conditional Access | Keep Entra Security Defaults (free baseline MFA). No Conditional Access in v1 (needs Entra ID P1). MFA happens at sign-in and carries into the OBO token. |
| D9 | Test identity | Use a dedicated work account in the tenant (`<user>@<tenant>.onmicrosoft.com`), not a personal Microsoft account, for Azure DevOps and sign-in tests. The `myTicketOrg` organization is connected to this tenant. |

## 15. Open questions

None at the moment.
