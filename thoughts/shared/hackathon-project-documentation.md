# VibeDocs - Living Apps Hackathon Project

**Tagline**: Document management that lets users extend it themselves

**Demo**: [Link to live demo or video]
**Code**: [Link to GitHub repo]

---

## The Challenge

Hospital managers in Romania (like Librimir at Resita Hospital, managing 1000+ employees) are drowning in documents:
- Invoices, contracts, medical reports, compliance documents
- Manual classification and routing
- No integration with existing systems
- Every hospital has unique workflows

**Traditional solution**: Build fixed features, users request changes, wait months for updates.

**The problem**: Apps die when you ship them. Users are powerless.

---

## Our Solution

VibeDocs is a **living app** - a document management system where users can extend and customize it without waiting for us:

**Core Features**:
- AI-powered document classification (OCR + ML)
- Hybrid search (vector + full-text)
- Multi-tenant architecture
- Open source, local deployment

**The Innovation - Extension Architecture**:
- Users can create custom workflows
- Users can add custom fields
- Users can build integrations
- Users can share extensions in marketplace

**Philosophy**: "Good gods design power in a controlled manner"
- Not chaos (users can't break core security)
- Not dead (users can paint, add features, extend)
- Beautiful garden (architected extension points)

---

## Approach & Workflow

### Day 1 (Hackathon Timeline)

**Phase 1: Core Foundation (4 hours)**
1. Set up FastAPI backend with multi-tenant database
2. Implement document upload and basic OCR pipeline
3. Build React frontend with document viewer
4. Add authentication (Google OAuth)

**Phase 2: Extension System (3 hours)**
1. Design extension API contract
2. Implement workflow engine (trigger → condition → action)
3. Create UI for building custom workflows
4. Add sandboxing and rate limiting

**Phase 3: Demo Scenarios (1 hour)**
1. Build example: "High-value invoice approval workflow"
2. Build example: "Custom field for hospital department"
3. Build example: "Integration webhook to external ERP"
4. Polish demo flow

### Architecture Decisions

**Power Spectrum Design**:
```
CHAOS ←────── GARDEN ──────→ DEAD
(too much)   (architected)   (none)
```

**Protected (Users CANNOT change)**:
- Database schema
- Authentication/authorization
- Multi-tenant isolation
- Core security boundaries

**Extensible (Users CAN change)**:
- Workflows (automation rules)
- Custom fields (metadata schemas)
- UI components (dashboards)
- Integrations (webhooks)

Each extension:
- Scoped to organization
- Rate limited
- Sandboxed execution
- Audit logged

---

## Tools & Technologies

### Core Stack
- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic
- **Frontend**: React, TanStack Query, Tailwind CSS
- **Database**: PostgreSQL (multi-tenant with organization_id scoping)
- **Vector Search**: Qdrant (hybrid search with BM25 + vector embeddings)
- **Storage**: Azure Blob Storage
- **OCR**: Mistral OCR for document processing

### AI Tools Used
- **Claude (Anthropic)**:
  - Architecture planning and design
  - Code generation for boilerplate
  - API contract design
  - Extension system design
  - Documentation writing
- **GitHub Copilot**: Code completion and suggestions

### Development Tools
- **VS Code**: Primary IDE
- **Git**: Version control
- **Docker**: Local development environment
- **Postman**: API testing

### AI-Assisted Workflow
1. Used Claude to design the extension architecture
2. Claude helped structure the "power spectrum" concept
3. Generated boilerplate for extension API contracts
4. Copilot for rapid component development
5. Claude for documentation and pitch creation

---

## Key Features Demonstrated

### 1. Core Document Management
- Upload PDF/image documents
- Automatic OCR and text extraction
- AI classification into categories
- Full-text + semantic search

### 2. User-Built Workflows
**Example: High-Value Invoice Approval**
```javascript
{
  trigger: "document.classified",
  conditions: [
    { field: "category", equals: "invoice" },
    { field: "amount", greaterThan: 5000 }
  ],
  actions: [
    { type: "notify", recipients: ["finance_director"] },
    { type: "set_status", value: "pending_approval" }
  ]
}
```
Built in UI, no code required, deployed instantly.

### 3. Custom Fields
Users add organization-specific metadata:
```javascript
{
  name: "hospital_department",
  type: "enum",
  values: ["Emergency", "Surgery", "Radiology"],
  appliesTo: ["invoice", "report"]
}
```

### 4. Sandbox Safety
- Resource quotas per organization
- Rate limiting on webhooks
- Isolated execution environments
- Cannot access other organizations' data

---

## The Paradigm Shift

**Old Testament (Traditional Apps)**:
- Developer controls all features
- Users file tickets and wait
- App is dead on delivery
- Monument architecture

**Evangelion (Living Apps)**:
- Users extend the app themselves
- Users become creators, not just consumers
- App grows with community
- Garden architecture

**The Question**: What will your next project be? A monument or a garden?

---

## What We Built in 1 Day

✅ Multi-tenant document management core
✅ AI-powered classification pipeline
✅ Extension API with sandboxing
✅ Workflow builder UI (no-code)
✅ Custom field system
✅ Webhook integration support
✅ Working demo with 3 example extensions

**Lines of Code**: ~2,500 (backend) + ~1,800 (frontend)
**AI Assistance**: ~40% faster development with Claude + Copilot

---

## Try It Yourself

**Demo Scenario**:
1. Upload an invoice document
2. Watch it auto-classify
3. Build a custom workflow: "Notify when invoice > 1000 RON"
4. Add a custom field: "Project code"
5. Create a webhook to external system
6. All without touching core code

**The Magic**: Librimir (or any user) can extend the app without waiting for us.

---

## Future Vision

**Marketplace**:
- Users publish extensions
- Community-built templates
- "Romanian Invoice Compliance Pack"
- Revenue sharing for extension authors

**More Extension Types**:
- Custom UI themes
- Classification trainers
- Report templates
- Integration connectors

**The Architecture of Empowerment**: This isn't just a document manager. It's proof that apps can be living gardens, not dead monuments.

---

## Team & Acknowledgments

**Built by**: [Your name/team]
**AI Pair Programming**: Claude (Anthropic) for architecture and planning
**Inspired by**: The hospital managers who need this yesterday

**Contact**: [Your contact info]
**GitHub**: [Repo link]
**Demo**: [Demo link]

---

**"Good gods design and assign power in a controlled manner."**

This is what the architecture of empowerment looks like.

---

# Pitch-ul Final (Versiunea în Română)

## Scenariul Complet - 3 Minute

### Act 1: Realitatea (45 secunde)

"Am construit un sistem de management documente pentru managerii de spitale din România":
- Nu e sexy. E destul de plictisitor, de fapt.
- Dar fiecare manager de spital din România are nevoie de asta
- Librimir de la Spitalul Reșița - 1000+ angajați - **așteaptă asta chiar acum**
- Toți se îneacă în documente, conformitate, haos
- Acest blocaj? **Costă vieți.**

"Și asta te privește personal":
- Cineva pe care îl iubești va merge la spital
- Management bun salvează vieți
- Management prost? Întârzieri. Erori. Tratamente ratate.
- Ajutându-i pe ei, **ne ajutăm pe toți**

"Așa că l-am construit":
- Cu inteligență artificială, modele locale pentru confidențialitate
- Open source, rulează pe infrastructura lor
- Rezolvă problema astăzi

---

### Act 2: Realizarea - Zeii Cruzi (30 secunde)

"Iată adevărul incomod":
- **Suntem zei în lumile noastre software**
- Creăm regulile, limitele, posibilitățile
- Și ce fel de zei am ales să fim?

"Zei cruzi":
- Utilizatorii nu pot schimba o culoare fără permisiunea noastră
- Nu pot adăuga o funcție fără roadmap-ul nostru
- Nu pot construi nimic dacă nu permitem noi explicit
- I-am făcut **subiecți fără putere** în lumile pe care le controlăm

---

### Act 3: Alegerea (60 secunde)

"Dar am putea alege diferit":

"Zeii buni nu acumulează putere - o împart":
- Dar **cât de multă putere** contează
- Dacă toată lumea poate schimba gravitația pentru toți userii? Lumea se prăbușește
- Dacă nimeni nu poate măcar să picteze? Lumea rămâne moartă
- **Zeii buni proiectează și atribuie putere într-un mod controlat**

"E vorba de alegerea între":
- Haos → Grădină Frumoasă → Monument Mort
- Arta constă în **arhitectarea cantității potrivite de putere**

"Îți amintești primul tău proiect software?":
- Acea bucurie când cineva a folosit lucrul TĂU?
- Când ei au rezolvat problema LOR cu ce ai construit TU?
- **Ce-ar fi dacă i-am da lui Librimir acea putere?**

"El trece de la supus → **creator**":
- Își modelează lumea sa
- Construiește ce are nevoie spitalul său
- De la monument → **grădină**

---

### Act 4: Evanghelia (30 secunde)

"Asta e EVANGELION - vestea bună":
- Nu mai trebuie să fim zei cruzi
- Putem construi software care **împuternicește** în loc să constrângă
- Aplicații unde utilizatorii devin creatori
- De la regate → **lumi deschise**

"Managerul de documente?":
- Doar dovada că putem face asta
- Produsul real: **Arhitectura împuternicirii**

---

### Încheierea (15 secunde)

"Deci iată întrebarea":
- Care va fi următorul tău proiect?
- **Un monument sau o grădină?**
- Acesta e viitorul. **Hai să-l construim.**

---

## Fraze Cheie de Subliniat

1. **"Librimir... așteaptă asta chiar acum"** - Fă-l real
2. **"Suntem zei în lumile noastre software"** - Adevărul incomod
3. **"Zei cruzi"** - Lasă să pătrundă
4. **"Haos → Grădină Frumoasă → Monument Mort"** - Spectrul
5. **"Îți amintești primul tău proiect software?"** - Ancora emoțională
6. **"Ce-ar fi dacă i-am da lui Librimir acea putere?"** - Transformarea
7. **"Un monument sau o grădină?"** - Forțează alegerea

---

## Arcul Emoțional

```
Credibilitate (Librimir + spitale)
    ↓
Disconfort (zei cruzi)
    ↓
Sofisticare (spectrul puterii)
    ↓
Emoție (prima bucurie → Librimir)
    ↓
Acțiune (monument sau grădină?)
```

**Durata totală: ~3 minute**

**Filozofia**: "Zeii buni proiectează și atribuie putere într-un mod controlat."

Asta înseamnă arhitectura împuternicirii.
