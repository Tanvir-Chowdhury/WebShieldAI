<template>
  <div class="card card-hover p-6">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-sm font-medium text-gray-400">{{ title }}</p>
        <p class="text-3xl font-bold text-white mt-2">{{ value }}</p>
        <!-- <p class="text-sm mt-2" :class="changeClass">
          <span class="inline-flex items-center">
            <component :is="changeIcon" class="w-4 h-4 mr-1" />
            {{ change }}
          </span>
        </p> -->
      </div>
      <div class="p-3 rounded-full" :class="iconBgClass">
        <component :is="icon" class="w-8 h-8" :class="iconClass" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { 
  ShieldCheckIcon, 
  ExclamationTriangleIcon, 
  ChartBarIcon,
  ClockIcon,
  ArrowUpIcon,
  ArrowDownIcon
} from '@heroicons/vue/24/outline';

interface Props {
  title: string;
  value: string | number;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: 'shield' | 'warning' | 'chart' | 'clock';
}

const props = defineProps<Props>();

const iconMap = {
  shield: ShieldCheckIcon,
  warning: ExclamationTriangleIcon,
  chart: ChartBarIcon,
  clock: ClockIcon,
};

const icon = computed(() => iconMap[props.icon]);

const iconBgClass = computed(() => {
  switch (props.icon) {
    case 'shield':
      return 'bg-green-500/20';
    case 'warning':
      return 'bg-red-500/20';
    case 'chart':
      return 'bg-blue-500/20';
    case 'clock':
      return 'bg-purple-500/20';
    default:
      return 'bg-gray-500/20';
  }
});

const iconClass = computed(() => {
  switch (props.icon) {
    case 'shield':
      return 'text-green-500';
    case 'warning':
      return 'text-red-500';
    case 'chart':
      return 'text-blue-500';
    case 'clock':
      return 'text-purple-500';
    default:
      return 'text-gray-500';
  }
});

const changeClass = computed(() => {
  switch (props.changeType) {
    case 'positive':
      return 'text-green-500';
    case 'negative':
      return 'text-red-500';
    default:
      return 'text-gray-400';
  }
});

const changeIcon = computed(() => {
  return props.changeType === 'positive' ? ArrowUpIcon : ArrowDownIcon;
});
</script>