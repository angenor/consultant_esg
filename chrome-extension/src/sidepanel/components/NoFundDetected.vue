<template>
  <div class="flex flex-col items-center justify-center p-8 text-center">
    <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
      <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    </div>
    <h2 class="text-base font-semibold text-gray-700 mb-2">Aucun fonds detecte</h2>
    <p class="text-sm text-gray-500 mb-4">
      Naviguez vers le site d'un fonds vert pour activer le guide pas-a-pas.
    </p>
    <div class="bg-emerald-50 rounded-lg p-4 text-left w-full">
      <h3 class="text-xs font-semibold text-emerald-800 mb-2">Sites supportes :</h3>
      <ul class="text-xs text-emerald-700 space-y-1">
        <li class="flex items-center gap-2">
          <span class="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
          BOAD - Facilite Verte
        </li>
        <li class="flex items-center gap-2">
          <span class="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
          GCF - Green Climate Fund
        </li>
        <li class="flex items-center gap-2">
          <span class="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
          BAD - Fonds Vert Africain
        </li>
      </ul>
    </div>
    <p class="text-xs text-gray-400 mt-4">
      D'autres fonds seront ajoutes prochainement.
    </p>
  </div>
</template>
