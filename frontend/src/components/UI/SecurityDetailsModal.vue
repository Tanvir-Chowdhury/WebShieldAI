<template>
  <div
    v-if="isOpen && website"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50"
    @click.self="$emit('close')"
  >
    <div class="card p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto animate-slide-up">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <div class="status-indicator" :class="statusClass"></div>
          <div>
            <h2 class="text-xl font-semibold text-white">{{ website.name }}</h2>
            <p class="text-sm text-gray-400">{{ website.url }}</p>
          </div>
        </div>
        <button
          @click="$emit('close')"
          class="p-2 text-gray-400 hover:text-white transition-colors duration-200"
        >
          <XMarkIcon class="w-6 h-6" />
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="space-y-4">
          <h3 class="text-lg font-medium text-white">Security Metrics</h3>
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-slate-700 rounded-lg p-4">
              <p class="text-sm text-gray-400">Total Requests</p>
              <p class="text-2xl font-bold text-white">{{ formatNumber(website.metrics.totalRequests) }}</p>
            </div>
            <div class="bg-slate-700 rounded-lg p-4">
              <p class="text-sm text-gray-400">Blocked Attacks</p>
              <p class="text-2xl font-bold text-red-400">{{ website.metrics.blockedAttacks }}</p>
            </div>
            <div class="bg-slate-700 rounded-lg p-4">
              <p class="text-sm text-gray-400">Uptime</p>
              <p class="text-2xl font-bold text-green-400">{{ website.metrics.uptime }}%</p>
            </div>
            <div class="bg-slate-700 rounded-lg p-4">
              <p class="text-sm text-gray-400">Response Time</p>
              <p class="text-2xl font-bold text-blue-400">{{ website.metrics.responseTime }}ms</p>
            </div>
          </div>
        </div>

        <div class="space-y-4">
          <h3 class="text-lg font-medium text-white">Protection Status</h3>
          <div class="space-y-3">
            <div class="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
              <span class="text-white">SQL Injection Protection</span>
              <span
                class="px-2 py-1 text-xs font-medium rounded-full"
                :class="website.protections.sqlInjection ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'"
              >
                {{ website.protections.sqlInjection ? 'ENABLED' : 'DISABLED' }}
              </span>
            </div>
            <div class="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
              <span class="text-white">XSS Protection</span>
              <span
                class="px-2 py-1 text-xs font-medium rounded-full"
                :class="website.protections.xssProtection ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'"
              >
                {{ website.protections.xssProtection ? 'ENABLED' : 'DISABLED' }}
              </span>
            </div>
            <div class="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
              <span class="text-white">Dom Protection</span>
              <span
                class="px-2 py-1 text-xs font-medium rounded-full"
                :class="website.protections.domProtection ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'"
              >
                {{ website.protections.domProtection ? 'ENABLED' : 'DISABLED' }}
              </span>
            </div>
            <div class="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
              <span class="text-white">Defacement Protection</span>
              <span
                class="px-2 py-1 text-xs font-medium rounded-full"
                :class="website.protections.defacementProtection ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'"
              >
                {{ website.protections.defacementProtection ? 'ENABLED' : 'DISABLED' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 class="text-lg font-medium text-white mb-4">Recent Attack Activity</h3>
        <AttackLogs :attacks="website.attacks" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { XMarkIcon } from '@heroicons/vue/24/outline';
import type { Website } from '../../types/dashboard';
import AttackLogs from '../Dashboard/AttackLogs.vue';

interface Props {
  isOpen: boolean;
  website: Website | null;
}

interface Emits {
  (e: 'close'): void;
}

const props = defineProps<Props>();
defineEmits<Emits>();

const statusClass = computed(() => {
  if (!props.website) return 'status-safe';
  
  switch (props.website.status) {
    case 'safe':
      return 'status-safe';
    case 'warning':
      return 'status-warning';
    case 'danger':
      return 'status-danger';
    default:
      return 'status-safe';
  }
});

const formatNumber = (num: number): string => {
  return new Intl.NumberFormat().format(num);
};
</script>