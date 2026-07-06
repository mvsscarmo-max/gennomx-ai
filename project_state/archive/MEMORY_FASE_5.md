> ⚠️ **Histórico consolidado em `project_state/progress.md`.** Preservado como registro detalhado da fase (regra `AGENTS.md` §14).

# MEMORY — Fase 5: Frontend Next.js — Design System, Auth, Layout, Overview + Search

**Data de conclusão:** 2026-06-09  
**Status:** ✅ Concluída (MVP funcional)

---

## Objetivo

Criar o frontend Next.js 14 (App Router) com o Design System GennomX, layout de dashboard,
página de visão geral, lista de ativos com busca/filtros, lista de ensaios e monitoramento de fontes.

---

## Stack Frontend

| Tecnologia | Versão | Função |
|---|---|---|
| Next.js | 14.2.29 | Framework React — App Router + Server Components |
| TypeScript | 5.6.x | Tipagem forte |
| Tailwind CSS | 3.4.x | Design system utilitário |
| Lucide React | 0.462.x | Ícones |
| next/font | built-in | Carregamento Montserrat + Inter do Google Fonts |
| Sonner | 1.7.x | Toast notifications (futuro) |

---

## Design System GennomX — Tokens

```
Cor primária (brand):  #F2829B (rose)
Cor secundária:        Slate 600-900 (institucional)
Fundo:                 #F8FAFC (surface-subtle)
Superfície de card:    #FFFFFF
Borda de card:         rgba(226, 232, 240, 0.6)
Sombra de card:        0 1px 3px rgb(0 0 0 / 0.08)
Border radius card:    12px
Fonte display:         Montserrat (headings, títulos)
Fonte body:            Inter (corpo, labels, tabelas)
Sucesso:               #10B981
Warning:               #F59E0B
Perigo:                #EF4444
Info:                  #3B82F6
```

---

## Arquivos Criados

### Configuração

| Arquivo | Descrição |
|---|---|
| `frontend/package.json` | Dependências Next.js 14, Tailwind, Lucide, TypeScript |
| `frontend/tsconfig.json` | TS strict, paths `@/*` → `src/*` |
| `frontend/tailwind.config.ts` | Tokens de design (brand, surface, shadows, border-radius, animações) |
| `frontend/postcss.config.js` | Tailwind + autoprefixer |
| `frontend/next.config.ts` | `NEXT_PUBLIC_API_URL`, `typedRoutes` experimental |

### Código-fonte (`src/`)

| Arquivo | Descrição |
|---|---|
| `src/app/globals.css` | Tokens CSS, componentes utilitários Tailwind (`card`, `badge`, `btn`, `input`, `stat-card`, etc.) |
| `src/app/layout.tsx` | Root layout: `Inter + Montserrat` via `next/font`, metadata padrão |
| `src/lib/types.ts` | Interfaces TypeScript: `DrugAssetSummary`, `DrugAssetDetail`, `TrialSummary`, `CompanySummary`, `DataSourceSummary`, `IngestionJobSummary`, `OverviewStats`, `PaginatedResponse<T>` |
| `src/lib/api.ts` | API client: `apiFetch`, `assetsApi`, `trialsApi`, `sourcesApi`, `jobsApi`, `healthApi`, `fetchOverviewStats` |
| `src/lib/utils.ts` | Utilitários: `cn`, `formatDate`, `formatRelative`, `formatNumber`, `confidenceColor`, `phaseLabel`, `statusVariant` |

### Componentes UI

| Arquivo | Componentes |
|---|---|
| `src/components/ui/card.tsx` | `Card`, `CardHeader`, `CardTitle` |
| `src/components/ui/badge.tsx` | `Badge` com variantes: rose, slate, success, warning, danger, info |
| `src/components/ui/skeleton.tsx` | `Skeleton`, `SkeletonCard`, `SkeletonRow` |
| `src/components/ui/search-input.tsx` | `SearchInput` com debounce por `setTimeout` no consumidor |
| `src/components/ui/pagination.tsx` | `Pagination` com chevrons |

### Layout

| Arquivo | Componentes |
|---|---|
| `src/components/layout/sidebar.tsx` | `Sidebar` — nav com grupos Ciência/Operações, logo GennomX, link ativo por pathname |
| `src/components/layout/header.tsx` | `Header` — título de página, busca global (redireciona para /assets?q=), avatar |

### Páginas

| Arquivo | Tipo | Descrição |
|---|---|---|
| `src/app/(dashboard)/layout.tsx` | Server | Dashboard wrapper: Sidebar + Header + `<main>` |
| `src/app/(dashboard)/page.tsx` | Server + Suspense | Visão geral: stat cards, painel de fontes, jobs recentes |
| `src/app/(dashboard)/assets/page.tsx` | Client | Lista de ativos com busca, filtros (indicação, fase), tabela, paginação |
| `src/app/(dashboard)/assets/[id]/page.tsx` | Server | Detalhe do ativo: header, ciência, desenvolvimento, indicações, status regulatório |
| `src/app/(dashboard)/trials/page.tsx` | Client | Lista de ensaios com busca, filtros (fase, status), tabela, paginação |
| `src/app/(dashboard)/sources/page.tsx` | Server | Monitoramento de fontes com cards de status |
| `src/app/(dashboard)/companies/page.tsx` | Server | Stub — Fase 3 |
| `src/app/(dashboard)/indications/page.tsx` | Server | Stub — Fase 3 |
| `src/app/(dashboard)/targets/page.tsx` | Server | Stub — Fase 3 |
| `src/app/(dashboard)/jobs/page.tsx` | Server | Stub — Fase 3 |
| `src/app/(dashboard)/mcp-logs/page.tsx` | Server | Stub — Fase 4 |
| `src/app/(dashboard)/security/page.tsx` | Server | Stub — Fase 4 |

---

## Decisões Técnicas

### 1. Server Components para páginas de leitura
**Decisão:** Páginas de listagem (Overview, Sources) usam Server Components com `revalidate`.  
**Motivo:** Dados estáticos/semi-estáticos se beneficiam de ISR sem overhead de client-side fetch.

### 2. Client Components para filtros interativos
**Decisão:** Assets e Trials são `"use client"` com estado local de filtros + debounce de 300ms.  
**Motivo:** Filtros dinâmicos precisam de reatividade; não há SSR ganho com parâmetros de query que mudam a cada keystroke.

### 3. Design System via Tailwind `@layer components`
**Decisão:** Classes compostas (`.card`, `.btn-primary`, `.nav-item`) definidas em `globals.css` com `@layer components`.  
**Motivo:** Evita duplicação nos JSX; componentes ficam legíveis; Tailwind purge funciona via `content`.

### 4. API client centralizado em `lib/api.ts`
**Decisão:** Todos os fetches passam por `apiFetch()` com base URL da env var.  
**Motivo:** Facilita troca de URL base, adição de auth headers futuros (JWT Supabase) e tratamento de erros uniforme.

### 5. Sem autenticação no MVP frontend
**Decisão:** Auth Supabase prevista mas não implementada — páginas abertas por enquanto.  
**Motivo:** Stack auth (Supabase SSR middleware + `@supabase/ssr`) foi incluída no `package.json` mas a implementação fica para a iteração seguinte quando o `SUPABASE_URL/ANON_KEY` estiver configurado no ambiente.

---

## Estrutura de Rotas

```
/ — Visão Geral (Server + Suspense)
/assets — Lista de Ativos (Client)
/assets/[id] — Detalhe do Ativo (Server)
/companies — Stub
/trials — Lista de Ensaios (Client)
/indications — Stub
/targets — Stub
/sources — Monitoramento de Fontes (Server)
/jobs — Stub
/mcp-logs — Stub
/security — Stub
```

---

## Pendências para fases seguintes

- [ ] Autenticação: Supabase SSR middleware + proteção de rotas
- [ ] Páginas Companies, Indications, Targets, Jobs (Fase 3)
- [ ] Páginas MCP Logs, Security (Fase 4)
- [ ] Testes Playwright para Assets list e Asset detail
- [ ] Testes de acessibilidade (axe-core)
- [ ] Notificações toast (Sonner) para ações
- [ ] Favicon e Open Graph metadata
