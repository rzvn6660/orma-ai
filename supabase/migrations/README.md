# ORMA AI — Supabase / PostgreSQL Schema Migrations

This directory is the **single source of truth** for all PostgreSQL schema evolution in ORMA AI.

The project relies **exclusively on the official Supabase CLI** for migration authoring, inspection, and deployment. No custom Python migration runners or ad-hoc table tracking mechanisms exist in this project.

---

## 1. Core Architectural Invariants

1. **Supabase CLI as the Sole Tool:**
   * All schema modifications (tables, columns, indexes, constraints, views) must originate as version-controlled `.sql` files in this directory.
   * **Never** modify the production schema directly through the Supabase Dashboard SQL Editor or Table Editor once migration management is established. Manual edits cause immediate drift against Git.
   * Runtime application startup (`backend/main.py`) strictly bypasses `Base.metadata.create_all()` in PostgreSQL mode and will never execute DDL.

2. **Native Migration Tracking Only:**
   * Migration state is managed exclusively by the Supabase platform and CLI within `supabase_migrations.schema_migrations`.
   * **Do not** manually create, drop, or alter `supabase_migrations.schema_migrations` or any custom tracking tables (such as `_schema_migrations` in `public`).

3. **Supabase Data API & Oct 30, 2026 Security Model:**
   * ORMA AI's frontend communicates exclusively with the FastAPI backend via standard REST endpoints; database tables are **not** exposed to the Supabase Data API (PostgREST).
   * **`anon` and `authenticated` roles must NEVER be granted access** by default.
   * **`service_role` must NOT be granted access by default.** Only grant minimum necessary CRUD privileges (`SELECT, INSERT, UPDATE, DELETE`) if a table explicitly requires access through the Supabase Data API or an authorized service-role workflow.
   * **`GRANT ALL` is strictly prohibited.**
   * **Row Level Security (RLS) is mandatory** on all public tables as defense-in-depth (`ALTER TABLE public.<table_name> ENABLE ROW LEVEL SECURITY;`).

---

## 2. Standard Supabase CLI Workflow

All migration tasks must be performed using the official Supabase CLI:

```bash
# 1. Create a new timestamped migration file
supabase migration new <descriptive_action_name>

# 2. Inspect applied vs. pending migrations across local / remote
supabase migration list

# 3. Preview pending migrations against target database without applying (Strictly Read-Only)
supabase db push --dry-run

# 4. Apply approved migrations to target database (Mutating — requires explicit approval)
supabase db push

# 5. Reset local database schema to match migrations (Local dev only)
supabase db reset

# 6. Repair out-of-sync migration history (Use ONLY when history is genuinely desynchronized)
supabase migration repair <version> --status <applied|reverted>
```

---

## 3. Table Ownership & Design Models

Every new table migration must explicitly choose its appropriate primary key, foreign keys, RLS policy model, and access privileges. Do **not** assume every table has a `user_id`:

### Model A: User-Owned / Tenant Tables
*(e.g., patient health records, medication schedules, personal memories, wellness logs)*
* **Structure:** Scoped to an individual user via `user_id REFERENCES public.users(id) ON DELETE CASCADE`.
* **Security:** Mandatory RLS. If Data API exposure is ever granted, policies must strictly enforce `(select auth.uid()) = user_id`.
```sql
CREATE TABLE IF NOT EXISTS public.patient_vitals (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    systolic INT NOT NULL,
    diastolic INT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_patient_vitals_user ON public.patient_vitals(user_id);
ALTER TABLE public.patient_vitals ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.patient_vitals FROM anon, authenticated;
```

### Model B: Caregiver & Subject Relationship Tables
*(e.g., caregiver pairing links, consent records, shared access tokens)*
* **Structure:** Joins multiple actors (e.g. `elder_id`, `caregiver_id`) with state machine statuses (`pending`, `approved`, `revoked`).
* **Security:** Mandatory RLS. Requires active caregiver relationship verification.
```sql
CREATE TABLE IF NOT EXISTS public.caregiver_delegations (
    id VARCHAR(64) PRIMARY KEY,
    elder_id VARCHAR(64) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    caregiver_id VARCHAR(64) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE public.caregiver_delegations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.caregiver_delegations FROM anon, authenticated;
```

### Model C: Global Reference / Catalog Tables
*(e.g., medical dictionary, standard drug interactions, ICD diagnostic codes, supported locales)*
* **Structure:** System-wide reference data with no individual `user_id`.
* **Security:** Mandatory RLS. Zero public write access.
```sql
CREATE TABLE IF NOT EXISTS public.medical_dictionaries (
    code VARCHAR(32) PRIMARY KEY,
    display_name TEXT NOT NULL,
    category VARCHAR(64) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
ALTER TABLE public.medical_dictionaries ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.medical_dictionaries FROM anon, authenticated;
```

### Model D: Configuration & Governance Tables
*(e.g., clinical governance policies, safety rules, system feature flags)*
* **Structure:** Platform-level rules (like `tsgp_policies`) managed by administrative workflows or deployment scripts.
* **Security:** Mandatory RLS. Zero public access.
```sql
CREATE TABLE IF NOT EXISTS public.governance_rules (
    rule_id VARCHAR(64) PRIMARY KEY,
    description TEXT NOT NULL,
    severity VARCHAR(32) NOT NULL DEFAULT 'medium',
    is_enforced BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE public.governance_rules ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.governance_rules FROM anon, authenticated;
```

---

## 4. Production Reconciliation Procedure (For Future Onboarding)

The production Supabase database already contains existing application tables. 

To bring the existing production database safely under Supabase CLI migration tracking without modifying or breaking existing data:

1. **Do NOT run `supabase db push` against production yet.** Pushing before reconciliation risks schema conflicts.
2. **Reconciliation Steps (To be executed when authorized):**
   * **Step 1: Baseline Generation:** Run `supabase db pull` or inspect the live database to generate an authoritative initial schema snapshot.
   * **Step 2: Review:** Verify that the generated baseline migration matches the existing production schema without destructive operations (`DROP` or data alteration).
   * **Step 3: Baseline Repair:** Use `supabase migration repair <baseline_version> --status applied` against the production database so the Supabase CLI recognizes that the baseline has already been satisfied on production.
   * **Step 4: Future Migrations:** All subsequent migrations can then be safely previewed (`supabase db push --dry-run`) and deployed (`supabase db push`).
