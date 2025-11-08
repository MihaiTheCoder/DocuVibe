# Living App Architecture Specification

## Purpose

This document specifies the technical architecture that enables users to extend and build on top of applications, transforming them from static products into living ecosystems.

**Core Principle**: Good gods design and assign power in a controlled manner.

---

## Design Philosophy

### The Power Spectrum

```
CHAOS ←────────────────────────────────────→ DEAD
(Too much power)              (No power)

                    ↓
            BEAUTIFUL GARDEN
         (Architected power)
```

**Chaos**: Users can change gravity for everyone (no boundaries)
**Dead**: Users can't even paint (no creativity)
**Garden**: Users have clearly defined extension points with proper isolation

---

## Architecture Layers

### Layer 1: Core System (Immutable)
**Owner**: Platform developers
**Power Level**: Full control
**User Access**: Read-only

**What's Protected**:
- Database schema
- Authentication/authorization
- Multi-tenant isolation
- Core API contracts
- Security boundaries

**Why**: These are "gravity" - if anyone can change them, the system collapses for everyone.

---

### Layer 2: Extension Points (User Extensible)
**Owner**: Users (per organization)
**Power Level**: Create, modify, delete within their scope
**Isolation**: Changes only affect their organization

#### 2.1 Custom Workflows

**What Users Can Build**:
- Custom document processing pipelines
- Automated routing rules
- Approval workflows
- Integration hooks

**Technical Implementation**:
```javascript
// User-defined workflow
{
  trigger: "document.uploaded",
  conditions: [
    { field: "category", operator: "equals", value: "invoice" },
    { field: "amount", operator: "greaterThan", value: 1000 }
  ],
  actions: [
    { type: "notify", target: "finance_team" },
    { type: "webhook", url: "https://their-system.com/api" }
  ]
}
```

**Boundaries**:
- ✅ Can: Define triggers, conditions, actions
- ❌ Cannot: Access other organizations' data
- ❌ Cannot: Override security rules
- ✅ Sandboxed: Webhooks have rate limits and timeout

---

#### 2.2 Custom Fields & Metadata

**What Users Can Build**:
- Organization-specific document fields
- Custom metadata schemas
- Computed fields based on existing data

**Technical Implementation**:
```javascript
// User-defined custom field
{
  name: "internal_project_code",
  type: "string",
  validation: {
    pattern: "^PRJ-[0-9]{4}$",
    required: true
  },
  appliesTo: ["invoice", "contract"],
  visibleTo: ["admin", "finance"]
}
```

**Boundaries**:
- ✅ Can: Add fields to their documents
- ❌ Cannot: Modify core fields (id, created_at, organization_id)
- ✅ Can: Define validation rules
- ❌ Cannot: Access system tables

---

#### 2.3 Custom UI Components

**What Users Can Build**:
- Custom dashboards
- Organization-specific views
- Branded document viewers
- Custom reports

**Technical Implementation**:
```javascript
// User-defined dashboard widget
{
  type: "custom-widget",
  name: "Monthly Invoice Summary",
  query: {
    collection: "documents",
    filters: {
      category: "invoice",
      date: "last_30_days"
    },
    aggregate: "sum",
    field: "total_amount"
  },
  visualization: "bar-chart"
}
```

**Boundaries**:
- ✅ Can: Query their own data
- ✅ Can: Use approved component library
- ❌ Cannot: Inject arbitrary JavaScript
- ❌ Cannot: Access DOM outside their widget scope
- ✅ Sandboxed: Runs in isolated iframe with CSP

---

#### 2.4 Custom Integrations

**What Users Can Build**:
- Connections to external systems
- Data sync pipelines
- Third-party service hooks

**Technical Implementation**:
```javascript
// User-defined integration
{
  name: "Sync to Hospital ERP",
  provider: "custom_webhook",
  events: ["document.classified", "document.approved"],
  endpoint: "https://hospital-erp.resita.ro/api/documents",
  auth: {
    type: "bearer",
    token: "${ENCRYPTED_TOKEN}"
  },
  rateLimit: {
    maxRequests: 100,
    perMinutes: 1
  }
}
```

**Boundaries**:
- ✅ Can: Send data via webhooks
- ✅ Can: Store encrypted credentials
- ❌ Cannot: Exceed rate limits
- ❌ Cannot: Access other orgs' integration configs
- ✅ Monitored: All outbound calls are logged

---

#### 2.5 Custom Classification Rules

**What Users Can Build**:
- Domain-specific document classifiers
- Custom extraction patterns
- Organization-specific categories

**Technical Implementation**:
```javascript
// User-defined classification rule
{
  category: "medical_report",
  keywords: ["diagnostic", "rezultate analize", "recomandări"],
  extractionRules: [
    {
      field: "patient_id",
      pattern: "\\bPacient:\\s*([A-Z0-9]+)\\b"
    },
    {
      field: "test_date",
      pattern: "\\bData:\\s*(\\d{2}\\.\\d{2}\\.\\d{4})\\b"
    }
  ],
  confidence_threshold: 0.85
}
```

**Boundaries**:
- ✅ Can: Train on their own documents
- ✅ Can: Define custom categories
- ❌ Cannot: Override system classification for regulated docs
- ✅ Scoped: Only affects their organization

---

### Layer 3: Extension Marketplace (Community)
**Owner**: Community contributors
**Power Level**: Published extensions vetted by platform
**Isolation**: Users opt-in to install

**What Community Can Build**:
- Pre-built workflow templates
- Integration connectors for popular services
- Custom report templates
- UI themes and components

**Example**:
```
Extension: "Romanian Invoice Compliance Pack"
- Pre-configured fields for ANAF requirements
- Validation rules for Romanian tax IDs
- Automated submission workflows
- 1,200+ downloads
- Maintained by: @community-contributor
```

**Boundaries**:
- ✅ Can: Publish to marketplace after review
- ✅ Can: Charge for extensions (revenue share)
- ❌ Cannot: Access user data without explicit permission
- ✅ Reviewed: All extensions go through security audit

---

## Permission Model

### Role-Based Extension Building

```
User Role          | Can View | Can Create | Can Modify | Can Publish
-------------------|----------|------------|------------|-------------
Org Admin          | ✅       | ✅         | ✅         | ✅
Org Member         | ✅       | ❌         | ❌         | ❌
Extension Builder  | ✅       | ✅         | Own only   | ✅
External           | Installed| ❌         | ❌         | ❌
```

### Scope Isolation

Every user-created extension has a scope:

```javascript
{
  extension_id: "uuid",
  organization_id: "uuid",
  scope: {
    data_access: ["documents", "users"], // What data it can read
    actions: ["create_workflow", "send_webhook"], // What it can do
    ui_locations: ["dashboard", "document_viewer"] // Where it appears
  },
  created_by: "user_id",
  approved_by: "admin_user_id"
}
```

---

## Technical Implementation

### Extension Runtime

**Architecture**:
```
┌─────────────────────────────────────────┐
│         Core Application                │
│  (Protected, Version Controlled)        │
└──────────────┬──────────────────────────┘
               │
               │ Extension API (Stable Contract)
               │
┌──────────────┴──────────────────────────┐
│     Extension Sandbox Layer             │
│  - Rate Limiting                        │
│  - Permission Checks                    │
│  - Resource Quotas                      │
│  - Audit Logging                        │
└──────────────┬──────────────────────────┘
               │
     ┌─────────┴─────────┐
     │                   │
┌────▼─────┐      ┌─────▼──────┐
│ Workflow │      │ Custom UI  │
│ Engine   │      │ Renderer   │
└──────────┘      └────────────┘
```

### API Contract

**Stable Extension API**:
```typescript
// This contract NEVER breaks backward compatibility
interface ExtensionAPI {
  // Data access
  documents: {
    query(filter: DocumentFilter): Promise<Document[]>;
    create(doc: DocumentInput): Promise<Document>;
    update(id: string, doc: Partial<Document>): Promise<Document>;
  };

  // Workflow actions
  workflows: {
    trigger(event: WorkflowEvent): Promise<void>;
    schedule(workflow: ScheduledWorkflow): Promise<void>;
  };

  // UI extensions
  ui: {
    registerWidget(widget: WidgetConfig): void;
    registerAction(action: ActionConfig): void;
  };

  // External integrations
  http: {
    post(url: string, data: unknown): Promise<Response>;
    // Rate limited, logged, with timeout
  };
}
```

**Versioning**:
- API version is explicit: `/v1/extensions/api`
- New versions are additive only
- Old versions supported for 2 years minimum
- Breaking changes require new major version

---

## Resource Limits

### Preventing "Noisy Neighbor" Problems

**Per-Organization Quotas**:
```javascript
{
  workflows: {
    maxActive: 50,
    maxExecutionsPerHour: 1000
  },
  customFields: {
    maxFieldsPerDocument: 50
  },
  webhooks: {
    maxEndpoints: 10,
    maxRequestsPerMinute: 100,
    timeout: 5000 // ms
  },
  storage: {
    maxCustomDataMB: 100
  }
}
```

**Enforcement**:
- Soft limits: Warning emails at 80% usage
- Hard limits: Extension execution paused, admin notified
- Upgrade path: Contact for enterprise quotas

---

## Security Model

### Principle: Defense in Depth

**1. Isolation**:
- Each organization's extensions run in separate namespace
- No cross-organization data access
- Database queries automatically scoped to `organization_id`

**2. Sandboxing**:
- Custom code runs in isolated containers
- No file system access
- No network access except approved webhooks
- Memory and CPU limits enforced

**3. Audit Trail**:
- All extension actions logged
- Who created, modified, executed
- What data was accessed
- Performance metrics tracked

**4. Review Process** (for Marketplace):
- Automated security scans
- Manual code review for high-risk permissions
- Community rating and feedback
- Revokable certificates

---

## Developer Experience

### Extension Development Flow

**1. Local Development**:
```bash
# Initialize extension
vibe-cli init --type workflow

# Local testing with mock data
vibe-cli test --extension ./my-workflow.json

# Validate against API contract
vibe-cli validate
```

**2. Deployment**:
```bash
# Deploy to organization (requires admin approval)
vibe-cli deploy --org resita-hospital

# Publish to marketplace (requires review)
vibe-cli publish --marketplace
```

**3. Monitoring**:
```bash
# View extension logs
vibe-cli logs --extension-id uuid

# Performance metrics
vibe-cli metrics --extension-id uuid
```

### Extension Templates

**Starter Templates**:
- `workflow-automation`: Basic trigger → action pattern
- `custom-dashboard`: Pre-wired dashboard with charts
- `external-integration`: OAuth + webhook boilerplate
- `classifier-extension`: Document classification template

---

## Examples: What Users Will Build

### Example 1: Librimir's Custom Workflow

**Problem**: When invoices over 5000 RON arrive, they need automatic approval workflow.

**Solution**:
```javascript
{
  name: "High-Value Invoice Approval",
  trigger: "document.classified",
  conditions: [
    { field: "category", equals: "invoice" },
    { field: "extracted.total_amount", greaterThan: 5000 },
    { field: "extracted.currency", equals: "RON" }
  ],
  actions: [
    {
      type: "notify",
      channels: ["email", "slack"],
      recipients: ["finance_director", "hospital_director"]
    },
    {
      type: "set_status",
      value: "pending_approval"
    },
    {
      type: "create_task",
      assignTo: "finance_director",
      dueDate: "+2_business_days"
    }
  ]
}
```

**Impact**: Zero code, built in UI workflow builder, saves 4 hours/week.

---

### Example 2: Department-Specific Dashboard

**Problem**: Each department wants to see only relevant document stats.

**Solution**:
```javascript
{
  name: "Finance Department Dashboard",
  widgets: [
    {
      type: "metric-card",
      title: "Pending Invoices",
      query: {
        collection: "documents",
        filter: {
          category: "invoice",
          status: "pending_approval"
        },
        aggregate: "count"
      }
    },
    {
      type: "chart",
      title: "Monthly Spending",
      query: {
        collection: "documents",
        filter: { category: "invoice" },
        groupBy: "month",
        aggregate: "sum",
        field: "extracted.total_amount"
      },
      visualization: "line-chart"
    }
  ],
  permissions: {
    visibleTo: ["finance_team"]
  }
}
```

**Impact**: Self-service BI, no developer needed.

---

### Example 3: ERP Integration

**Problem**: Need to sync approved invoices to hospital's existing ERP system.

**Solution**:
```javascript
{
  name: "ERP Sync for Approved Invoices",
  trigger: "document.status_changed",
  conditions: [
    { field: "category", equals: "invoice" },
    { field: "status", equals: "approved" }
  ],
  actions: [
    {
      type: "webhook",
      url: "https://erp.resita-hospital.ro/api/invoices",
      method: "POST",
      headers: {
        "Authorization": "Bearer ${ENCRYPTED_ERP_TOKEN}",
        "Content-Type": "application/json"
      },
      body: {
        invoice_number: "${document.extracted.invoice_number}",
        vendor: "${document.extracted.vendor}",
        amount: "${document.extracted.total_amount}",
        date: "${document.extracted.date}",
        document_url: "${document.url}"
      },
      retry: {
        maxAttempts: 3,
        backoff: "exponential"
      }
    }
  ]
}
```

**Impact**: Real-time sync, reduces manual data entry by 95%.

---

## Monitoring & Observability

### For Platform Operators

**Metrics to Track**:
- Extension execution success rate
- Average execution time per extension type
- Resource utilization per organization
- API error rates
- User-created extensions vs marketplace installs

**Alerts**:
- Extension exceeding resource quotas
- High failure rates for specific extension
- Security scan failures
- Unusual data access patterns

### For Extension Users

**Dashboard**:
- Extension health status
- Execution logs (last 30 days)
- Performance metrics
- Cost attribution (if usage-based pricing)
- User feedback and ratings (marketplace)

---

## Migration Path

### For Existing Applications

**Phase 1: Identify Extension Points**
- Audit current feature requests
- Map to extension categories (workflows, UI, integrations)
- Design API contracts

**Phase 2: Build Extension Runtime**
- Implement sandboxing layer
- Create permission model
- Build developer tools

**Phase 3: Launch with Templates**
- Release 5-10 high-quality templates
- Invite beta users (like Librimir)
- Gather feedback, iterate

**Phase 4: Open Marketplace**
- Enable community contributions
- Establish review process
- Revenue sharing model

---

## Success Metrics

### Platform Health
- **Extension Adoption**: % of organizations with at least 1 active extension
- **User Empowerment**: % of feature requests satisfied by user-built extensions
- **Community Growth**: # of marketplace extensions, downloads
- **System Stability**: Extension error rate < 1%

### User Satisfaction
- **Time to Value**: Days from idea → deployed extension
- **User Sentiment**: "I can build what I need" agreement rate
- **Retention**: Organizations using extensions vs not

---

## The Architecture of Empowerment

This isn't just a plugin system. This is:

**Architected Power**:
- Clear boundaries (what users can and cannot change)
- Proper isolation (changes don't affect others)
- Safety guarantees (quotas, sandboxing, monitoring)
- Growing ecosystem (marketplace, templates, community)

**From Monument → Garden**:
- Monument: Request feature → wait → maybe get it
- Garden: Build it yourself → deploy instantly → share with community

**Good Gods**:
- Design the extension points (power allocation)
- Maintain the core (gravity stays constant)
- Enable the community (others become creators)
- Monitor and protect (garden doesn't become chaos)

---

## Appendix: Extension Categories Reference

| Category | What Users Build | Boundaries | Example |
|----------|------------------|------------|---------|
| Workflows | Trigger-action automations | No system triggers, rate limited | Auto-approve low-value invoices |
| Custom Fields | Metadata schemas | No core field modification | Patient ID extraction |
| UI Extensions | Dashboards, views | Sandboxed rendering | Department dashboard |
| Integrations | External system hooks | Rate limited, logged | ERP sync |
| Classifiers | Document categorization | Org-scoped training | Medical report detection |
| Reports | Custom analytics | Query their data only | Monthly compliance report |
| Templates | Reusable patterns | Shared in marketplace | Invoice processing workflow |

---

**This is the spec for a living app.**
**This is how we architect empowerment.**
**This is how monuments become gardens.**
