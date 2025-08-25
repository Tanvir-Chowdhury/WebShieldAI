<template>
  <div class="card p-6">
    <h3 class="text-lg font-semibold text-white mb-4">{{ title }}</h3>
    <div class="relative h-64">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  LineController,     
  BarController,      
  DoughnutController, 
} from 'chart.js';
import type { ChartData } from '../../types/dashboard';


ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  LineController,
  BarController,
  DoughnutController
);

interface Props {
  title: string;
  data: ChartData;
  type: 'line' | 'bar' | 'doughnut';
}

const props = defineProps<Props>();

const chartCanvas = ref<HTMLCanvasElement>();
let chartInstance: ChartJS | null = null;

const createChart = () => {
  if (!chartCanvas.value) return;

  const ctx = chartCanvas.value.getContext('2d');
  if (!ctx) return;

  if (chartInstance) {
    chartInstance.destroy();
  }

  const config: any = {
    type: props.type,
    data: props.data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: '#ffffff',
            font: { size: 12 },
          },
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          titleColor: '#ffffff',
          bodyColor: '#ffffff',
          borderColor: '#3b82f6',
          borderWidth: 1,
        },
      },
      scales: props.type !== 'doughnut' ? {
        x: {
          ticks: { color: '#9ca3af' },
          grid: { color: 'rgba(156, 163, 175, 0.1)' },
        },
        y: {
          ticks: { color: '#9ca3af' },
          grid: { color: 'rgba(156, 163, 175, 0.1)' },
        },
      } : undefined,
    },
  };

  chartInstance = new ChartJS(ctx, config);
};

onMounted(() => {
  createChart();
});

watch(() => props.data, () => {
  createChart();
}, { deep: true });

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy();
  }
});
</script>
