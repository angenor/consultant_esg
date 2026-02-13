<script setup lang="ts">
import { ref } from 'vue'
import { useAdminStore, type SkillTestResult } from '../../stores/admin'
import SkillCodeEditor from './SkillCodeEditor.vue'

const props = defineProps<{
  skillId: string | null
}>()

const adminStore = useAdminStore()

const testParams = ref('{\n  \n}')
const testResult = ref<SkillTestResult | null>(null)
const testing = ref(false)
const testError = ref<string | null>(null)

async function runTest() {
  if (!props.skillId) {
    testError.value = 'Sauvegardez le skill avant de le tester'
    return
  }

  testing.value = true
  testResult.value = null
  testError.value = null

  try {
    const params = JSON.parse(testParams.value)
    testResult.value = await adminStore.testSkill(props.skillId, params)
  } catch (e: unknown) {
    if (e instanceof SyntaxError) {
      testError.value = 'JSON invalide dans les paramètres de test'
    } else {
      testError.value = e instanceof Error ? e.message : 'Erreur lors du test'
    }
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
    <h3 class="font-semibold text-gray-900 mb-3">Tester le skill</h3>

    <div class="mb-3">
      <label class="block text-sm font-medium text-gray-700 mb-1">Paramètres de test (JSON)</label>
      <SkillCodeEditor v-model="testParams" language="json" :height="100" placeholder='{"entreprise_id": "test-123"}' />
    </div>

    <button
      @click="runTest"
      :disabled="testing || !skillId"
      class="inline-flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
    >
      <svg v-if="testing" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <span>{{ testing ? 'Test en cours...' : 'Tester' }}</span>
    </button>

    <p v-if="!skillId" class="mt-2 text-xs text-gray-500">
      Sauvegardez le skill pour pouvoir le tester
    </p>

    <!-- Parse error -->
    <div v-if="testError" class="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
      <p class="text-sm text-red-700 font-medium">Erreur</p>
      <p class="text-sm text-red-600 mt-1">{{ testError }}</p>
    </div>

    <!-- Test result -->
    <div
      v-if="testResult"
      class="mt-3 p-3 rounded-lg border"
      :class="testResult.success ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'"
    >
      <p class="font-medium text-sm" :class="testResult.success ? 'text-emerald-700' : 'text-red-700'">
        {{ testResult.success ? 'Succès' : 'Erreur' }}
        <span v-if="testResult.duration_ms" class="font-normal text-gray-500 ml-2">
          ({{ testResult.duration_ms }}ms)
        </span>
      </p>
      <pre class="mt-2 text-xs font-mono overflow-auto max-h-60 whitespace-pre-wrap">{{
        JSON.stringify(testResult.success ? testResult.result : testResult.error, null, 2)
      }}</pre>
    </div>
  </div>
</template>
