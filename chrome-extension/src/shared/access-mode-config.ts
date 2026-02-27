/**
 * Configuration des parcours par mode d'accès aux fonds verts.
 * Chaque mode définit des pré-étapes, des conseils contextuels et un flag intermédiaire.
 */

export interface PreStep {
  title: string
  description: string
  action?: 'contact_bank' | 'find_entity' | 'check_calendar' | 'prepare_dossier'
  completed_by: 'user_confirm' | 'auto'
}

export interface AccessModeConfig {
  key: string
  label: string
  description: string
  color: string
  preSteps: PreStep[]
  tips: string[]
  requires_intermediary: boolean
}

export const ACCESS_MODE_CONFIGS: Record<string, AccessModeConfig> = {
  direct: {
    key: 'direct',
    label: 'Accès direct',
    description: 'Soumettez votre candidature directement auprès du fonds.',
    color: 'emerald',
    preSteps: [],
    tips: [
      'Vérifiez les dates limites de soumission',
      'Préparez tous les documents avant de commencer le formulaire',
    ],
    requires_intermediary: false,
  },
  banque_partenaire: {
    key: 'banque_partenaire',
    label: 'Via banque partenaire',
    description: "Votre banque locale sert d'intermédiaire pour accéder à ce fonds.",
    color: 'blue',
    preSteps: [
      {
        title: 'Identifier votre banque partenaire',
        description: "Contactez votre banque pour vérifier qu'elle est accréditée auprès de ce fonds.",
        action: 'contact_bank',
        completed_by: 'user_confirm',
      },
      {
        title: "Obtenir l'accord de principe",
        description: 'Votre banque doit valider votre éligibilité avant de soumettre au fonds.',
        action: 'prepare_dossier',
        completed_by: 'user_confirm',
      },
    ],
    tips: [
      'Les banques partenaires ajoutent généralement 2-4 semaines au délai',
      'Préparez un business plan solide — la banque évaluera votre solvabilité',
    ],
    requires_intermediary: true,
  },
  appel_propositions: {
    key: 'appel_propositions',
    label: 'Appel à propositions',
    description: 'Ce fonds lance des appels périodiques. Candidatez pendant la fenêtre ouverte.',
    color: 'purple',
    preSteps: [
      {
        title: 'Vérifier le calendrier',
        description: "Confirmez que l'appel à propositions est actuellement ouvert.",
        action: 'check_calendar',
        completed_by: 'user_confirm',
      },
    ],
    tips: [
      'Les appels ont des délais stricts — soumettez quelques jours avant la date limite',
      'Respectez scrupuleusement le format demandé pour la note conceptuelle',
    ],
    requires_intermediary: false,
  },
  entite_accreditee: {
    key: 'entite_accreditee',
    label: 'Via entité accréditée',
    description: 'Une entité nationale accréditée porte votre projet auprès du fonds.',
    color: 'amber',
    preSteps: [
      {
        title: "Identifier l'entité accréditée",
        description: "Trouvez l'entité nationale accréditée (AND, BOAD, banque de développement locale).",
        action: 'find_entity',
        completed_by: 'user_confirm',
      },
      {
        title: 'Soumettre une note conceptuelle',
        description: "L'entité accréditée évalue votre projet via une note conceptuelle.",
        action: 'prepare_dossier',
        completed_by: 'user_confirm',
      },
      {
        title: 'Attendre la validation',
        description: "L'entité accréditée prépare et soumet le dossier au fonds.",
        completed_by: 'user_confirm',
      },
    ],
    tips: [
      'Le processus via entité accréditée prend souvent 6-12 mois',
      "La note conceptuelle est l'étape la plus critique — soyez précis sur l'impact ESG",
    ],
    requires_intermediary: true,
  },
  garantie_bancaire: {
    key: 'garantie_bancaire',
    label: 'Garantie bancaire',
    description: 'Ce fonds fournit une garantie à votre banque pour sécuriser votre prêt.',
    color: 'indigo',
    preSteps: [
      {
        title: 'Obtenir un accord de prêt',
        description: "Négociez d'abord un prêt conditionnel avec votre banque.",
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
      'La garantie couvre généralement 50-80% du montant du prêt',
      'Votre banque reste votre interlocuteur principal',
    ],
    requires_intermediary: true,
  },
  banque_multilaterale: {
    key: 'banque_multilaterale',
    label: 'Via banque multilatérale',
    description: 'Le financement transite par une banque de développement multilatérale (BAD, BEI, etc.).',
    color: 'cyan',
    preSteps: [
      {
        title: 'Contacter la représentation locale',
        description: 'Identifiez le bureau local de la banque multilatérale dans votre pays.',
        action: 'find_entity',
        completed_by: 'user_confirm',
      },
      {
        title: 'Vérifier les lignes de crédit actives',
        description: 'La banque multilatérale doit avoir une ligne de crédit ouverte pour votre secteur.',
        action: 'check_calendar',
        completed_by: 'user_confirm',
      },
    ],
    tips: [
      'Les banques multilatérales ont des critères E&S stricts — votre score ESG est déterminant',
      "Le financement passe souvent par une institution financière locale",
    ],
    requires_intermediary: true,
  },
}

export function getAccessModeConfig(modeAcces: string | null | undefined): AccessModeConfig {
  return ACCESS_MODE_CONFIGS[modeAcces || 'direct'] || ACCESS_MODE_CONFIGS.direct
}
