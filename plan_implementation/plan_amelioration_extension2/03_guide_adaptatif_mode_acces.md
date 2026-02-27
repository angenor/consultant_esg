# Phase 3 : Guide adaptatif par mode d'acces

## Dependances

**Prerequis :** Phases 1 et 2 (scoring fiable + flux candidature fonctionnel)
**Bloque :** Phase 4 (le guide doit exister pour y integrer la checklist interactive)

## Progression

- [ ] 3.1 Definir les parcours type par mode_acces (mapping config)
- [ ] 3.2 Creer le composant `AccessGuide.vue` dans le side panel
- [ ] 3.3 Adapter les etapes du `StepNavigator` selon le mode d'acces
- [ ] 3.4 Ajouter les informations intermediaire dans la reponse API
- [ ] 3.5 Creer les templates de guide par mode (direct, intermediaire, appel a propositions)
- [ ] 3.6 Integrer les conseils contextuels (tips) par mode d'acces
- [ ] 3.7 Ajouter l'etat "en attente intermediaire" dans le suivi
- [ ] 3.8 Tests unitaires des parcours adaptatifs

## Objectif

Adapter le guide pas-a-pas du side panel au mode d'acces du fonds. Un fonds en acces direct n'a pas le meme parcours qu'un fonds necessitant un intermediaire bancaire. Le guide doit orienter l'utilisateur vers les bonnes demarches selon le mode.

## Etat actuel

### Ce qui existe
- Side panel avec `StepNavigator` + `StepContent` generiques
- `FundSiteConfig` avec `steps[]` definis par fonds
- `mode_acces` retourne dans la reponse API (`fund-recommendations`)
- 6 modes d'acces connus : `direct`, `banque_partenaire`, `appel_propositions`, `entite_accreditee`, `garantie_bancaire`, `banque_multilaterale`
- `acces_details` dans `criteres_json` avec `intermediaire`, `etapes`, `delai_estime`, `periodicite`, `documents_requis`

### Ce qui manque
- **Parcours adaptes** : le side panel affiche les memes etapes quel que soit le mode d'acces
- **Guide intermediaire** : pas d'etape "Contacter votre banque partenaire" pour les fonds via intermediaire
- **Etapes pre-candidature** : pour les modes indirects, des etapes prealables sont necessaires (identifier l'intermediaire, obtenir l'accord, etc.)
- **Conseil contextuel** : les tips ne tiennent pas compte du mode d'acces
- **Statut intermediaire** : pas de suivi de l'etat "en attente de reponse intermediaire"

## Implementation detaillee

### 3.1 Mapping des parcours par mode_acces

**Fichier a creer :** `chrome-extension/src/shared/access-mode-config.ts`

```typescript
export interface AccessModeConfig {
  key: string
  label: string
  description: string
  color: string           // pour le badge
  preSteps: PreStep[]     // etapes avant la candidature proprement dite
  tips: string[]          // conseils specifiques
  requires_intermediary: boolean
}

export interface PreStep {
  title: string
  description: string
  action?: 'contact_bank' | 'find_entity' | 'check_calendar' | 'prepare_dossier'
  completed_by?: 'user_confirm' | 'auto'
}

export const ACCESS_MODE_CONFIGS: Record<string, AccessModeConfig> = {
  direct: {
    key: 'direct',
    label: 'Acces direct',
    description: 'Soumettez votre candidature directement aupres du fonds.',
    color: 'emerald',
    preSteps: [],
    tips: [
      'Verifiez les dates limites de soumission',
      'Preparez tous les documents avant de commencer le formulaire',
    ],
    requires_intermediary: false,
  },
  banque_partenaire: {
    key: 'banque_partenaire',
    label: 'Via banque partenaire',
    description: 'Votre banque locale sert d\'intermediaire pour acceder a ce fonds.',
    color: 'blue',
    preSteps: [
      {
        title: 'Identifier votre banque partenaire',
        description: 'Contactez votre banque pour verifier qu\'elle est accreditee aupres de ce fonds.',
        action: 'contact_bank',
        completed_by: 'user_confirm',
      },
      {
        title: 'Obtenir l\'accord de principe',
        description: 'Votre banque doit valider votre eligibilite avant de soumettre au fonds.',
        action: 'prepare_dossier',
        completed_by: 'user_confirm',
      },
    ],
    tips: [
      'Les banques partenaires ajoutent generalement 2-4 semaines au delai',
      'Preparez un business plan solide — la banque evaluera votre solvabilite',
    ],
    requires_intermediary: true,
  },
  appel_propositions: {
    key: 'appel_propositions',
    label: 'Appel a propositions',
    description: 'Ce fonds lance des appels periodiques. Candidatez pendant la fenetre ouverte.',
    color: 'purple',
    preSteps: [
      {
        title: 'Verifier le calendrier',
        description: 'Confirmez que l\'appel a propositions est actuellement ouvert.',
        action: 'check_calendar',
        completed_by: 'user_confirm',
      },
    ],
    tips: [
      'Les appels ont des delais stricts — soumettez quelques jours avant la date limite',
      'Respectez scrupuleusement le format demande pour la note conceptuelle',
    ],
    requires_intermediary: false,
  },
  entite_accreditee: {
    key: 'entite_accreditee',
    label: 'Via entite accreditee',
    description: 'Une entite nationale accreditee porte votre projet aupres du fonds.',
    color: 'amber',
    preSteps: [
      {
        title: 'Identifier l\'entite accreditee',
        description: 'Trouvez l\'entite nationale accreditee (AND, BOAD, banque de developpement locale).',
        action: 'find_entity',
        completed_by: 'user_confirm',
      },
      {
        title: 'Soumettre une note conceptuelle',
        description: 'L\'entite accreditee evalue votre projet via une note conceptuelle.',
        action: 'prepare_dossier',
        completed_by: 'user_confirm',
      },
      {
        title: 'Attendre la validation',
        description: 'L\'entite accreditee prepare et soumet le dossier au fonds.',
        completed_by: 'user_confirm',
      },
    ],
    tips: [
      'Le processus via entite accreditee prend souvent 6-12 mois',
      'La note conceptuelle est l\'etape la plus critique — soyez precis sur l\'impact ESG',
    ],
    requires_intermediary: true,
  },
  garantie_bancaire: {
    key: 'garantie_bancaire',
    label: 'Garantie bancaire',
    description: 'Ce fonds fournit une garantie a votre banque pour securiser votre pret.',
    color: 'indigo',
    preSteps: [
      {
        title: 'Obtenir un accord de pret',
        description: 'Negociez d\'abord un pret conditionnel avec votre banque.',
        action: 'contact_bank',
        completed_by: 'user_confirm',
      },
      {
        title: 'Demander la garantie',
        description: 'Votre banque soumet la demande de garantie au fonds.',
        action: 'prepare_dossier',
        completed_by: 'user_confirm',
      },
    ],
    tips: [
      'La garantie couvre generalement 50-80% du montant du pret',
      'Votre banque reste votre interlocuteur principal',
    ],
    requires_intermediary: true,
  },
  banque_multilaterale: {
    key: 'banque_multilaterale',
    label: 'Via banque multilaterale',
    description: 'Le financement transite par une banque de developpement multilaterale (BAD, BEI, etc.).',
    color: 'cyan',
    preSteps: [
      {
        title: 'Contacter la representation locale',
        description: 'Identifiez le bureau local de la banque multilaterale dans votre pays.',
        action: 'find_entity',
        completed_by: 'user_confirm',
      },
      {
        title: 'Verifier les lignes de credit actives',
        description: 'La banque multilaterale doit avoir une ligne de credit ouverte pour votre secteur.',
        action: 'check_calendar',
        completed_by: 'user_confirm',
      },
    ],
    tips: [
      'Les banques multilaterales ont des criteres E&S stricts — votre score ESG est determinant',
      'Le financement passe souvent par une institution financiere locale',
    ],
    requires_intermediary: true,
  },
}
```

### 3.2 Composant AccessGuide.vue

**Fichier a creer :** `chrome-extension/src/sidepanel/components/AccessGuide.vue`

```vue
<template>
  <div class="px-4 py-3 bg-white border-b border-gray-200">
    <!-- Badge mode d'acces -->
    <div class="flex items-center gap-2 mb-2">
      <span :class="`bg-${modeConfig.color}-100 text-${modeConfig.color}-700`"
            class="text-xs px-2 py-1 rounded-full font-medium">
        {{ modeConfig.label }}
      </span>
      <span v-if="modeConfig.requires_intermediary"
            class="text-[10px] text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
        Intermediaire requis
      </span>
    </div>

    <!-- Description du mode -->
    <p class="text-xs text-gray-500 mb-3">{{ modeConfig.description }}</p>

    <!-- Pre-etapes (si mode intermediaire) -->
    <div v-if="modeConfig.preSteps.length > 0" class="space-y-2">
      <h4 class="text-xs font-semibold text-gray-600 uppercase tracking-wide">
        Etapes prealables
      </h4>
      <div v-for="(preStep, i) in modeConfig.preSteps" :key="i"
           class="flex items-start gap-2 p-2 rounded-lg"
           :class="preStepCompleted[i] ? 'bg-emerald-50' : 'bg-gray-50'">
        <button @click="togglePreStep(i)"
                class="w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5"
                :class="preStepCompleted[i]
                  ? 'bg-emerald-500 border-emerald-500'
                  : 'border-gray-300 hover:border-emerald-400'">
          <svg v-if="preStepCompleted[i]" class="w-3 h-3 text-white" ...>
            <path d="M5 13l4 4L19 7" />
          </svg>
        </button>
        <div>
          <p class="text-xs font-medium" :class="preStepCompleted[i] ? 'text-emerald-700' : 'text-gray-700'">
            {{ preStep.title }}
          </p>
          <p class="text-[11px] text-gray-500">{{ preStep.description }}</p>
        </div>
      </div>
    </div>

    <!-- Conseil specifique -->
    <div v-if="currentTip" class="mt-3 bg-blue-50 rounded-lg p-2">
      <p class="text-[11px] text-blue-700">{{ currentTip }}</p>
    </div>
  </div>
</template>
```

**Principe :** Ce composant s'affiche en haut du side panel, avant le `StepNavigator`. Il montre le mode d'acces, les etapes prealables a cocher, et un conseil contextuel.

### 3.3 Adapter StepNavigator

**Fichier :** `chrome-extension/src/sidepanel/components/StepNavigator.vue`

Modifier pour gerer 2 types d'etapes :
1. **Pre-etapes** (issues du `AccessModeConfig`) : cochables par l'utilisateur
2. **Etapes formulaire** (issues du `FundSiteConfig.steps`) : progression automatique

```typescript
// Props etendues
const props = defineProps<{
  steps: FundStep[]
  preSteps?: PreStep[]
  currentStep: number
  preStepCompleted?: boolean[]
}>()

// Etapes combinées = preSteps + steps
const allSteps = computed(() => [
  ...props.preSteps?.map((ps, i) => ({
    title: ps.title,
    isPreStep: true,
    completed: props.preStepCompleted?.[i] ?? false,
  })) ?? [],
  ...props.steps.map((s, i) => ({
    title: s.title,
    isPreStep: false,
    completed: i < props.currentStep,
  })),
])
```

### 3.4 Informations intermediaire dans l'API

**Fichier :** `backend/app/api/extension.py` → `get_fund_recommendations()`

Enrichir la reponse avec les donnees intermediaire :
```python
# Pour chaque fonds, si mode_acces implique un intermediaire,
# charger l'intermediaire associe depuis la table Intermediaire
if f.mode_acces in ('banque_partenaire', 'entite_accreditee', 'banque_multilaterale'):
    # Chercher les intermediaires lies a ce fonds
    intermediaires = await db.execute(
        select(Intermediaire)
        .where(Intermediaire.fonds_ids.contains([str(f.id)]))
        .limit(3)
    )
    intermediaire_list = [
        {"nom": i.nom, "type": i.type, "pays": i.pays, "contact": i.contact_url}
        for i in intermediaires.scalars().all()
    ]
else:
    intermediaire_list = []
```

Ajouter dans la reponse :
```python
"intermediaires": intermediaire_list,
```

**Fichier :** `chrome-extension/src/shared/types.ts`

Ajouter le type intermediaire dans `FondsVert` :
```typescript
export interface FondsVert {
  // ...existant...
  intermediaires?: {
    nom: string
    type: string
    pays: string
    contact: string | null
  }[]
}
```

### 3.5 Templates de guide par mode

**Fichier a creer :** `chrome-extension/src/sidepanel/components/ModeDirectGuide.vue`

Guide simplifie pour acces direct : progression lineaire standard avec les etapes du `FundSiteConfig`.

**Fichier a creer :** `chrome-extension/src/sidepanel/components/ModeIntermediaireGuide.vue`

Guide pour modes avec intermediaire :
- Phase 1 : Identification et contact intermediaire (pre-etapes)
- Phase 2 : Preparation du dossier (etapes specifiques)
- Phase 3 : Soumission via l'intermediaire

**Fichier a creer :** `chrome-extension/src/sidepanel/components/ModeAppelGuide.vue`

Guide pour appels a propositions :
- Verification calendrier et eligibilite
- Preparation note conceptuelle
- Soumission dans les delais

### 3.6 Conseils contextuels par mode

**Fichier :** `chrome-extension/src/sidepanel/components/StepContent.vue`

Modifier le `tip` computed pour integrer les conseils specifiques au mode d'acces :
```typescript
const tip = computed(() => {
  // 1. Conseil specifique a l'etape (existant)
  const stepTip = findStepTip()
  if (stepTip) return stepTip

  // 2. Conseil specifique au mode d'acces
  const modeConfig = ACCESS_MODE_CONFIGS[props.fundConfig.mode_acces || 'direct']
  const modeIndex = currentStep.value % modeConfig.tips.length
  return modeConfig.tips[modeIndex] || null
})
```

### 3.7 Statut "en attente intermediaire"

**Fichier backend :** `backend/app/models/fund_application.py`

Ajouter le statut `en_attente_intermediaire` aux statuts possibles :
```python
# Status: brouillon, en_cours, en_attente_intermediaire, soumise, acceptee, refusee, abandonnee
```

**Fichier extension :** `chrome-extension/src/shared/types.ts`

```typescript
export type ApplicationStatus =
  | 'brouillon'
  | 'en_cours'
  | 'en_attente_intermediaire'  // Nouveau
  | 'soumise'
  | 'acceptee'
  | 'refusee'
  | 'abandonnee'
```

**Fichier frontend :** `frontend/src/components/candidatures/StatusBadge.vue`

Ajouter la config pour le nouveau statut :
```typescript
en_attente_intermediaire: {
  bg: 'bg-indigo-100',
  text: 'text-indigo-800',
  label: 'En attente intermediaire'
}
```

### 3.8 Tests unitaires

**Fichier :** `chrome-extension/tests/access-mode.test.ts`

```typescript
// Cas a tester :
// - ACCESS_MODE_CONFIGS contient tous les 6 modes
// - Mode 'direct' a 0 pre-etapes
// - Mode 'banque_partenaire' a 2 pre-etapes
// - Mode 'entite_accreditee' a 3 pre-etapes
// - Les pre-etapes s'ajoutent avant les etapes du FundSiteConfig
// - Le statut 'en_attente_intermediaire' est valide
// - Le composant AccessGuide affiche les bonnes infos par mode
// - Les tips contextuels changent selon le mode
```

## Fichiers a creer

| Fichier | Description |
|---------|-------------|
| `chrome-extension/src/shared/access-mode-config.ts` | Configuration des parcours par mode |
| `chrome-extension/src/sidepanel/components/AccessGuide.vue` | Composant guide mode d'acces |
| `chrome-extension/src/sidepanel/components/ModeDirectGuide.vue` | Guide acces direct |
| `chrome-extension/src/sidepanel/components/ModeIntermediaireGuide.vue` | Guide intermediaire |
| `chrome-extension/src/sidepanel/components/ModeAppelGuide.vue` | Guide appel a propositions |
| `chrome-extension/tests/access-mode.test.ts` | Tests unitaires modes d'acces |

## Fichiers a modifier

| Fichier | Modification |
|---------|-------------|
| `backend/app/api/extension.py` | Ajouter intermediaires dans fund-recommendations |
| `backend/app/models/fund_application.py` | Ajouter statut `en_attente_intermediaire` |
| `chrome-extension/src/shared/types.ts` | Ajouter type intermediaire, statut |
| `chrome-extension/src/sidepanel/App.vue` | Integrer AccessGuide, passer mode_acces |
| `chrome-extension/src/sidepanel/components/StepNavigator.vue` | Gerer pre-etapes + etapes |
| `chrome-extension/src/sidepanel/components/StepContent.vue` | Tips contextuels par mode |
| `frontend/src/components/candidatures/StatusBadge.vue` | Nouveau statut badge |

## Criteres de validation

- [ ] Le guide s'adapte au mode d'acces du fonds detecte
- [ ] Les pre-etapes s'affichent pour les modes avec intermediaire
- [ ] L'utilisateur peut cocher les pre-etapes manuellement
- [ ] Les intermediaires sont affiches si disponibles
- [ ] Le statut "en attente intermediaire" fonctionne dans le suivi
- [ ] Les conseils contextuels changent selon le mode
- [ ] Les 3 templates de guide (direct, intermediaire, appel) sont fonctionnels
- [ ] Tests unitaires passent
