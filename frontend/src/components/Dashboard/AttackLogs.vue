<template>
  <div class="card p-6">
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-lg font-semibold text-white">Recent Attack Logs</h3>
      <div class="flex items-center space-x-2">
        <select
          v-model="selectedSeverity"
          class="bg-slate-700 border border-slate-600 text-white text-sm rounded-lg px-3 py-1"
        >
          <option value="">All Severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <select
          v-model="selectedType"
          class="bg-slate-700 border border-slate-600 text-white text-sm rounded-lg px-3 py-1"
        >
          <option value="">All Types</option>
          <option value="sql_injection">SQL Injection</option>
          <option value="xss">XSS</option>
          <option value="defacement">Defacement</option>
          <option value="dom">DOM manipulation</option>
        </select>
      </div>
    </div>

    <div class="space-y-3 max-h-96 overflow-y-auto">
      <div
        v-for="attack in filteredAttacks"
        :key="attack.id"
        class="bg-slate-700 rounded-lg p-4 border-l-4"
        :class="getBorderColor(attack.severity)"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center space-x-3 mb-2">
              <span
                class="px-2 py-1 text-xs font-medium rounded-full"
                :class="getSeverityClass(attack.severity)"
              >
                {{ attack.severity.toUpperCase() }}
              </span>
              <span
                class="px-2 py-1 text-xs font-medium rounded-full"
                :class="getTypeClass(attack.type)"
              >
                {{ formatAttackType(attack.type) }}
              </span>
              <!-- <span
                v-if="attack.blocked"
                class="px-2 py-1 text-xs font-medium rounded-full bg-green-500/20 text-green-400"
              >
                BLOCKED
              </span>
              <span
                v-else
                class="px-2 py-1 text-xs font-medium rounded-full bg-red-500/20 text-red-400"
              >
                ALLOWED
              </span> -->
            </div>
            <p class="text-sm text-white mb-1">{{ attack.details }}</p>
            
          </div>
          <div class="flex items-center space-x-2">
          <div class="flex items-center space-x-4 text-xs text-gray-400">
              <span>IP: {{ attack.sourceIp }}</span>
              <span v-if="attack.location">{{ attack.location }}</span>
              <span>{{ formatDate(attack.timestamp) }}</span>
            </div>
            <!-- <button
              class="p-1 text-gray-400 hover:text-red-500 transition-colors duration-200"
              title="Block IP"
            >
              <ShieldExclamationIcon class="w-5 h-5" />
            </button> -->
          </div>
        </div>
      </div>
    </div>

    <div v-if="filteredAttacks.length === 0" class="text-center py-8">
      <ShieldCheckIcon class="w-12 h-12 text-gray-400 mx-auto mb-3" />
      <p class="text-gray-400">No attacks found matching the selected filters.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { EyeIcon, ShieldExclamationIcon, ShieldCheckIcon } from '@heroicons/vue/24/outline';
import type { Attack } from '../../types/dashboard';

interface Props {
  attacks: Attack[];
}

const props = defineProps<Props>();

const selectedSeverity = ref('');
const selectedType = ref('');

// const filteredAttacks = computed(() => {
//   if (!Array.isArray(props.attacks)) return [];

//   return props.attacks
//     .filter(attack => {
//       if (selectedSeverity.value && attack.severity !== selectedSeverity.value) {
//         return false;
//       }
//       if (selectedType.value && attack.type !== selectedType.value) {
//         return false;
//       }
//       return true;
//     })
//     .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
//     .slice(0, 20);
// });

const filteredAttacks = computed(() => {
  if (!Array.isArray(props.attacks)) return [];

  return props.attacks
    .filter(a => !selectedSeverity.value || a.severity === selectedSeverity.value)
    .filter(a => !selectedType.value || a.type === selectedType.value)
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 20);
});

const formatDate = (ts: string | Date) => {
  const d = new Date(ts);
  return isNaN(d.getTime()) ? 'Invalid date' : 
    new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(d);
};


const getSeverityClass = (severity: Attack['severity']) => {
  switch (severity) {
    case 'low':
      return 'bg-blue-500/20 text-blue-400';
    case 'high':
      return 'bg-orange-500/20 text-orange-400';
    default:
      return 'bg-gray-500/20 text-gray-400';
  }
};

const getTypeClass = (type: Attack['type']) => {
  switch (type) {
    case 'sql_injection':
      return 'bg-purple-500/20 text-purple-400';
    case 'xss':
      return 'bg-pink-500/20 text-pink-400';
    case 'defacement':
      return 'bg-indigo-500/20 text-indigo-400';
    case 'dom':
      return 'bg-cyan-500/20 text-cyan-400';
    default:
      return 'bg-gray-500/20 text-gray-400';
  }
};

const getBorderColor = (severity: Attack['severity']) => {
  switch (severity) {
    case 'low':
      return 'border-blue-500';
    case 'high':
      return 'border-orange-500';
    default:
      return 'border-gray-500';
  }
};

const formatAttackType = (type: Attack['type']) => {
  return type.replace('_', ' ').toUpperCase();
};

// const formatDate = (date: Date) => {
//   return new Intl.DateTimeFormat('en-US', {
//     month: 'short',
//     day: 'numeric',
//     hour: '2-digit',
//     minute: '2-digit',
//   }).format(date);
// };
</script>