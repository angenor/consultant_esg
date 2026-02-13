# 06 - Frontend Vue.js

## Structure des Pages

```
┌─────────────────────────────────────────────────────────────┐
│  App Layout                                                  │
│  ┌───────────┬──────────────────────────────────────────┐   │
│  │           │                                           │   │
│  │  Sidebar  │            Main Content                   │   │
│  │           │                                           │   │
│  │  - Chat   │  ┌──────────────────────────────────┐    │   │
│  │  - Entrep │  │   ChatView (page principale)      │    │   │
│  │  - Docs   │  │   ou DashboardView                │    │   │
│  │  - Rappts │  │   ou DocumentsView                │    │   │
│  │           │  │   ou AdminView                     │    │   │
│  │  ──────── │  │                                    │    │   │
│  │  Admin    │  └──────────────────────────────────┘    │   │
│  │  (si rôle)│                                           │   │
│  │           │                                           │   │
│  └───────────┴──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Pages et Composants

### 1. LoginView / RegisterView
```
/login   → Formulaire connexion
/register → Formulaire inscription
```

### 2. ChatView (page principale)
```
/chat                    → Nouvelle conversation
/chat/:conversationId    → Conversation existante

┌──────────────────────────────────────────────────┐
│  Conversation avec ESG Advisor AI                 │
├──────────────────────────────────────────────────┤
│                                                    │
│  ┌─────────────────────────────────────────────┐  │
│  │ 🤖 Bonjour ! Je suis votre conseiller ESG.  │  │
│  │ Comment puis-je vous aider aujourd'hui ?     │  │
│  └─────────────────────────────────────────────┘  │
│                                                    │
│  ┌─────────────────────────────────────────────┐  │
│  │ 👤 J'ai une entreprise de recyclage à       │  │
│  │ Abidjan, je veux savoir si je suis éligible │  │
│  │ au Fonds Vert.                               │  │
│  └─────────────────────────────────────────────┘  │
│                                                    │
│  ┌─────────────────────────────────────────────┐  │
│  │ 🤖 Excellent ! Laissez-moi d'abord          │  │
│  │ comprendre votre activité...                 │  │
│  │                                               │  │
│  │ ⚙️ Analyse du profil entreprise...           │  │  ← Indicateur skill
│  │ ✅ Profil récupéré                           │  │
│  │                                               │  │
│  │ Votre entreprise traite environ combien de   │  │
│  │ tonnes de déchets par mois ?                 │  │
│  └─────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────┐ 📎 📄 ▶  │
│  │  Tapez votre message...          │   Envoyer  │
│  └──────────────────────────────────┘            │
└──────────────────────────────────────────────────┘

📎 = Upload document
📄 = Demander un rapport
▶  = Envoyer
```

### 3. DashboardView (multi-référentiel)
```
/dashboard

┌──────────────────────────────────────────────────────────┐
│  Tableau de Bord - [Nom Entreprise]                       │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  Référentiel : [BCEAO Finance Durable ▼]  ← sélecteur    │
│                                                            │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────────────────┐ │
│  │  58  │  │  63  │  │  72  │  │    Score Global       │ │
│  │ /100 │  │ /100 │  │ /100 │  │      62/100           │ │
│  │  E   │  │  S   │  │  G   │  │  Réf: BCEAO 2024     │ │
│  └──────┘  └──────┘  └──────┘  └──────────────────────┘ │
│                                                            │
│  ┌─── Comparaison Multi-Référentiel ──────────────────┐  │
│  │                                                      │  │
│  │  BCEAO 2024             ████████████░░  62/100      │  │
│  │  Fonds Vert Climat      ██████████░░░░  45/100      │  │
│  │  IFC Standards          ████████████░░  58/100      │  │
│  │  BAD Critères Verts     █████████████░  71/100      │  │
│  │                                                      │  │
│  │  ⚠ Fonds Vert Climat : seuil "impact climatique"   │  │
│  │    non atteint (30/100, minimum requis: 40)         │  │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌────────────────────┐  ┌─────────────────────┐         │
│  │  Radar Chart ESG    │  │  Évolution scores   │         │
│  │  (par référentiel)  │  │  (ligne temporelle) │         │
│  └────────────────────┘  └─────────────────────┘         │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Fonds Verts Recommandés                              │ │
│  │  ┌──────────────────────────────────────────────┐    │ │
│  │  │ BAD Ligne Vert     │ Réf: BAD   │ 78%  ████ │    │ │
│  │  │ BOAD Programme     │ Réf: BCEAO │ 65%  ███  │    │ │
│  │  │ Fonds Vert Climat  │ Réf: GCF   │ 45%  ██   │    │ │
│  │  │                    │ ⚠ seuil    │            │    │ │
│  │  └──────────────────────────────────────────────┘    │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Prochaines Actions (basées sur le réf. sélectionné) │ │
│  │  □ Réduire les émissions de 350 à 200 tCO2e/an      │ │
│  │  □ Augmenter la part d'énergie renouvelable à 50%   │ │
│  │  □ Formaliser la politique de gestion des déchets    │ │
│  └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### 4. DocumentsView
```
/documents

Liste des documents uploadés avec statut d'analyse.
Bouton upload. Prévisualisation.
```

### 5. CarbonView
```
/carbon

┌──────────────────────────────────────────────────────────────┐
│  Empreinte Carbone - [Nom Entreprise]                         │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │  Empreinte annuelle   │  │  Répartition par source      │  │
│  │    127 tCO2e/an       │  │  [Pie chart : énergie 45%,   │  │
│  │  ▼ -12% vs N-1       │  │   transport 30%, déchets 15%,│  │
│  └──────────────────────┘  │   achats 10%]                 │  │
│                             └──────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Comparaison sectorielle                                  │ │
│  │  Vous : 127 tCO2e │ Moyenne recyclage CI : 180 tCO2e     │ │
│  │  ✅ En-dessous de la moyenne sectorielle                  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Plan de réduction                                        │ │
│  │  🟢 Quick-win : Remplacer éclairage → -8 tCO2e, 0 XOF   │ │
│  │  🟡 Moyen terme : Solaire 30% → -25 tCO2e, 2M XOF       │ │
│  │  🔴 Long terme : Flotte électrique → -30 tCO2e, 15M XOF  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  [Évolution mensuelle : graphique ligne sur 12 mois]          │
└──────────────────────────────────────────────────────────────┘
```

### 6. CreditScoreView (Module 5 — Innovation 3)
```
/credit-score

┌──────────────────────────────────────────────────────────────┐
│  Score Crédit Vert - [Nom Entreprise]                         │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌────────────────────────────────────────────────┐           │
│  │         Score Combiné : 68/100                  │           │
│  │         [Jauge semi-circulaire colorée]          │           │
│  │         Niveau : Bon                             │           │
│  └────────────────────────────────────────────────┘           │
│                                                                │
│  ┌──────────────────────┐  ┌───────────────────────┐         │
│  │  Solvabilité: 72/100 │  │  Impact vert: 64/100  │         │
│  │  ████████████░░░░░░  │  │  ██████████░░░░░░░░   │         │
│  └──────────────────────┘  └───────────────────────┘         │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Facteurs du score                                        │ │
│  │  ✅ +15 Transactions régulières (36 mois)                 │ │
│  │  ✅ +12 Score ESG > 60 (réf. BCEAO)                      │ │
│  │  ✅ +8  Plan d'action en cours                            │ │
│  │  ⚠️  -5  Pas de certification verte                       │ │
│  │  ⚠️  -3  Pas d'audit externe récent                       │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  [📤 Partager mon score avec une institution]  ← lien sécurisé│
│                                                                │
│  Recommandations pour améliorer votre score :                  │
│  • Obtenir une certification ESG reconnue (+10 pts estimés)   │
│  • Réaliser un audit externe (+5 pts estimés)                 │
└──────────────────────────────────────────────────────────────┘
```

### 7. ActionPlanView (Module 6)
```
/action-plan

┌──────────────────────────────────────────────────────────────┐
│  Plan d'Action ESG - [Nom Entreprise]                         │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  Objectif : 62 → 75/100 (réf. BCEAO)    Horizon : 12 mois   │
│  Progression globale : ████████░░░░░░ 42%  (5/12 actions)    │
│                                                                │
│  ─── Quick-wins (< 3 mois) ─────────────────────────────── │
│  ✅ Formaliser la politique déchets          (+3 pts) Fait    │
│  ✅ Nommer un référent ESG                   (+2 pts) Fait    │
│  🔄 Former les employés aux éco-gestes       (+4 pts) En cours│
│     Échéance : 15 mars 2025                                   │
│                                                                │
│  ─── Moyen terme (3-12 mois) ────────────────────────────── │
│  ⬜ Installer panneaux solaires 30%          (+8 pts) À faire │
│  ⬜ Audit énergétique complet                (+3 pts) À faire │
│  ⬜ Certification ISO 14001                  (+6 pts) À faire │
│                                                                │
│  ─── Long terme (> 12 mois) ─────────────────────────────── │
│  ⬜ Transition flotte véhicules              (+5 pts) À faire │
│                                                                │
│  Coût total estimé : 8.5M XOF                                │
│  Bénéfice annuel estimé : 3.2M XOF (économies énergie)       │
└──────────────────────────────────────────────────────────────┘
```

### 8. AdminView (si rôle admin)
```
/admin/skills            → CRUD Skills (voir 07_admin_skills.md)
/admin/referentiels      → CRUD Référentiels ESG (voir 07_admin_skills.md)
/admin/referentiels/new  → Créer un référentiel (éditeur de grille)
/admin/referentiels/:id  → Modifier un référentiel + simuler scoring
/admin/fonds             → CRUD Fonds Verts (+ lien référentiel)
/admin/templates         → CRUD Templates Rapports
/admin/stats             → Statistiques d'usage
```

## Composants Vue.js Principaux

```
src/
├── views/
│   ├── LoginView.vue
│   ├── RegisterView.vue
│   ├── ChatView.vue              ← Page principale
│   ├── DashboardView.vue
│   ├── DocumentsView.vue
│   ├── CarbonView.vue            ← Empreinte carbone + plan de réduction
│   ├── CreditScoreView.vue       ← Score crédit vert alternatif (Module 5)
│   ├── ActionPlanView.vue        ← Suivi du plan d'action (Module 6)
│   └── admin/
│       ├── AdminLayout.vue
│       ├── SkillsListView.vue
│       ├── SkillEditView.vue
│       ├── ReferentielsListView.vue    ← NOUVEAU
│       ├── ReferentielEditView.vue     ← NOUVEAU
│       ├── FondsListView.vue
│       ├── FondEditView.vue            ← NOUVEAU (lien référentiel)
│       ├── TemplatesListView.vue
│       └── StatsView.vue
│
├── components/
│   ├── chat/
│   │   ├── ChatContainer.vue     ← Conteneur principal du chat
│   │   ├── MessageBubble.vue     ← Bulle de message (user/assistant)
│   │   ├── MessageInput.vue      ← Zone de saisie + boutons
│   │   ├── SkillIndicator.vue    ← "⚙️ Analyse en cours..."
│   │   ├── StreamingText.vue     ← Texte qui s'affiche progressivement
│   │   ├── FileUploadButton.vue  ← Bouton upload dans le chat
│   │   └── AudioRecordButton.vue ← Bouton enregistrement vocal (STT)
│   │
│   ├── carbon/
│   │   ├── CarbonSummary.vue     ← Empreinte totale + répartition par source
│   │   ├── CarbonEvolution.vue   ← Graphique évolution mensuelle/annuelle
│   │   ├── CarbonBySource.vue    ← Pie chart par catégorie (énergie, transport...)
│   │   ├── ReductionPlan.vue     ← Plan de réduction avec quick-wins vs long terme
│   │   └── SectorComparison.vue  ← Comparaison avec moyenne sectorielle
│   │
│   ├── credit/
│   │   ├── CreditScoreGauge.vue  ← Jauge visuelle du score combiné
│   │   ├── ScoreBreakdown.vue    ← Détail solvabilité vs impact vert + facteurs
│   │   └── ShareScoreButton.vue  ← Bouton génération lien de partage sécurisé
│   │
│   ├── actions/
│   │   ├── ActionPlanTimeline.vue ← Timeline visuelle du plan d'action
│   │   ├── ActionItemCard.vue    ← Carte action avec statut, échéance, priorité
│   │   └── ProgressTracker.vue   ← Barre de progression globale du plan
│   │
│   ├── dashboard/
│   │   ├── ScoreCard.vue         ← Carte score E/S/G
│   │   ├── ReferentielSelector.vue ← NOUVEAU : sélecteur de référentiel
│   │   ├── ScoreComparison.vue   ← NOUVEAU : comparaison multi-référentiel
│   │   ├── RadarChart.vue        ← Graphique radar (Chart.js)
│   │   ├── ScoreHistory.vue      ← Graphique évolution
│   │   ├── FundsMatchList.vue    ← Liste fonds recommandés
│   │   └── ActionPlan.vue        ← Checklist plan d'action
│   │
│   ├── admin/
│   │   ├── SkillForm.vue         ← Formulaire création/édition skill
│   │   ├── SkillCodeEditor.vue   ← Éditeur de code Python (CodeMirror)
│   │   ├── SkillTestPanel.vue    ← Panel de test d'un skill
│   │   ├── SchemaBuilder.vue     ← Builder visuel de JSON Schema
│   │   ├── ReferentielForm.vue   ← NOUVEAU : formulaire référentiel
│   │   ├── GrilleEditor.vue      ← NOUVEAU : éditeur visuel de grille ESG
│   │   └── ScoringSimulator.vue  ← NOUVEAU : simuler un scoring test
│   │
│   └── common/
│       ├── AppSidebar.vue
│       ├── NotificationBell.vue  ← Icône cloche + dropdown notifications
│       ├── LoadingSpinner.vue
│       └── ConfirmDialog.vue
│
├── composables/
│   ├── useChat.ts                ← Logique SSE + état du chat
│   ├── useAuth.ts                ← Authentification JWT
│   ├── useApi.ts                 ← Client API (fetch wrapper)
│   ├── useAudioRecorder.ts      ← Logique MediaRecorder + envoi audio
│   └── useNotifications.ts      ← Polling notifications non lues
│
├── stores/
│   ├── auth.ts                   ← Pinia store auth
│   ├── chat.ts                   ← Pinia store conversations
│   ├── entreprise.ts             ← Pinia store entreprise active
│   ├── notifications.ts          ← Pinia store notifications
│   └── admin.ts                  ← Pinia store admin
│
└── router/
    └── index.ts                  ← Routes + guards
```

## Composable SSE pour le Chat

```typescript
// === frontend/src/composables/useChat.ts ===

import { ref, reactive } from 'vue'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  skills?: SkillEvent[]
  isStreaming?: boolean
}

interface SkillEvent {
  name: string
  status: 'running' | 'done'
  params?: Record<string, any>
}

export function useChat(conversationId: string) {
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  const currentSkills = ref<SkillEvent[]>([])

  async function sendMessage(text: string) {
    // 1. Ajouter le message utilisateur
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
    })

    // 2. Préparer la bulle assistant (vide, en streaming)
    const assistantMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      skills: [],
      isStreaming: true,
    }
    messages.value.push(assistantMsg)
    isLoading.value = true

    // 3. Ouvrir le flux SSE
    const response = await fetch(
      `/api/chat/conversations/${conversationId}/message`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ message: text }),
      }
    )

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          const eventType = line.slice(7)
          // Lire la ligne data suivante
          continue
        }
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))

          switch (data.type) {
            case 'text':
              // Ajouter le texte progressivement
              assistantMsg.content += data.content
              break

            case 'skill_start':
              // Afficher l'indicateur de skill
              assistantMsg.skills!.push({
                name: data.skill,
                status: 'running',
                params: data.params,
              })
              break

            case 'skill_result':
              // Marquer le skill comme terminé
              const skill = assistantMsg.skills!.find(
                s => s.name === data.skill && s.status === 'running'
              )
              if (skill) skill.status = 'done'
              break

            case 'done':
              assistantMsg.isStreaming = false
              isLoading.value = false
              break

            case 'error':
              assistantMsg.content += '\n\n⚠️ Une erreur est survenue.'
              assistantMsg.isStreaming = false
              isLoading.value = false
              break
          }
        }
      }
    }
  }

  async function loadHistory() {
    const response = await api.get(
      `/api/chat/conversations/${conversationId}`
    )
    messages.value = response.messages
  }

  return {
    messages,
    isLoading,
    currentSkills,
    sendMessage,
    loadHistory,
  }
}
```

## Indicateur de Skill en Action

```vue
<!-- === frontend/src/components/chat/SkillIndicator.vue === -->

<template>
  <div class="flex items-center gap-2 text-sm text-gray-500 my-2 ml-4">
    <!-- Spinner si en cours -->
    <svg v-if="status === 'running'"
         class="animate-spin h-4 w-4" viewBox="0 0 24 24">
      <!-- ... spinner SVG -->
    </svg>
    <!-- Check si terminé -->
    <span v-else class="text-green-500">✓</span>

    <!-- Libellé adapté au skill -->
    <span>{{ skillLabel }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  name: string
  status: 'running' | 'done'
}>()

const skillLabels: Record<string, { running: string; done: string }> = {
  analyze_document:     { running: 'Analyse du document...', done: 'Document analysé' },
  calculate_esg_score:  { running: 'Calcul du score ESG...', done: 'Score ESG calculé' },
  search_green_funds:   { running: 'Recherche de fonds verts...', done: 'Fonds verts trouvés' },
  calculate_carbon:     { running: 'Calcul empreinte carbone...', done: 'Empreinte calculée' },
  generate_report_section: { running: 'Génération du rapport...', done: 'Section générée' },
  assemble_pdf:         { running: 'Assemblage du PDF...', done: 'PDF prêt' },
  search_knowledge_base:{ running: 'Recherche dans la base...', done: 'Recherche terminée' },
}

const skillLabel = computed(() => {
  const labels = skillLabels[props.name]
  if (!labels) return props.status === 'running' ? `${props.name} en cours...` : `${props.name} terminé`
  return labels[props.status]
})
</script>
```
