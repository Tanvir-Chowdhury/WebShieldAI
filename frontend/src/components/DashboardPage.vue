<template>
  <div class="min-h-screen gradient-bg">
    <!-- Header -->
    <header class="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center space-x-3">
            <ShieldCheckIcon class="w-8 h-8 text-blue-500" />
            <h1 class="text-xl font-bold text-white">WebShieldAI Dashboard</h1>
          </div>
          <div class="flex items-center space-x-4">
            <button
              @click="isAddModalOpen = true"
              class="btn-primary flex items-center space-x-2"
            >
              <PlusIcon class="w-4 h-4" />
              <span>Add Website</span>
            </button>
            <button
              @click="logout"
              class="btn-primary bg-[red] hover:bg-[darkred] space-x-2 text-sm text-white"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Metrics Overview -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricsCard
          title="Total Websites"
          :value="securityMetrics.totalWebsites"
          change="+2 this week"
          change-type="positive"
          icon="shield"
        />
        <MetricsCard
          title="Active Threats"
          :value="securityMetrics.activeThreats"
          change="-5 from yesterday"
          change-type="positive"
          icon="warning"
        />
        <MetricsCard
          title="Blocked Attacks"
          :value="securityMetrics.blockedAttacks"
          change="+12% this month"
          change-type="positive"
          icon="chart"
        />
        <MetricsCard
          title="Average Uptime"
          :value="`${securityMetrics.uptime}%`"
          change="+0.5% this week"
          change-type="positive"
          icon="clock"
        />
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <SecurityChart title="Attacks Over Time" :data="attacksOverTime" type="line" />
        <SecurityChart
          title="Threat Distribution"
          :data="threatDistribution"
          type="doughnut"
        />
      </div>

      <!-- Website Cards -->
      <div class="mb-8">
        <h2 class="text-2xl font-bold text-white mb-6">Protected Websites</h2>
        <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          <WebsiteCard
            v-for="site in websites"
            :key="site.id"
            :website="site"
            @refresh="refreshWebsite"
            @remove="removeWebsite(Number(site.id))"
            @details="viewDetails"
          />
        </div>
      </div>

      <!-- Attack Logs Placeholder -->
      <div class="mb-8">
        <h2 class="text-2xl font-bold text-white mb-6">Global Attack Logs</h2>
        <AttackLogs :attacks="allAttacks" />
      </div>
    </main>

    <!-- Add Website Modal -->
    <AddWebsiteModal
      v-if="isAddModalOpen"
      :modelValue="isAddModalOpen"
      @close="isAddModalOpen = false"
      @add="loadWebsitesFromDB"
    />

    <!-- Security Details Modal -->
    <SecurityDetailsModal
      :is-open="isDetailsModalOpen"
      :website="selectedWebsite"
      @close="isDetailsModalOpen = false"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth";
import { useDashboard } from "../composables/useDashboard";
import { ShieldCheckIcon, PlusIcon } from "@heroicons/vue/24/outline";
import api from "../composables/axios";
import AttackLogs from "./Dashboard/AttackLogs.vue";
import MetricsCard from "./Dashboard/MetricsCard.vue";
import WebsiteCard from "./Dashboard/WebsiteCard.vue";
import SecurityChart from "./Dashboard/SecurityChart.vue";
// import AttackLogs from "./Dashboard/AttackLogs.vue";
import AddWebsiteModal from "./UI/AddWebsiteModal.vue";
import SecurityDetailsModal from "./UI/SecurityDetailsModal.vue";


const router = useRouter();
const { user, checkAuth } = useAuth();
export interface Attack {
  id: string;
  type: 'sql_injection' | 'xss' | 'dom' | 'defacement';
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp:  string;
  sourceIp: string;
  blocked: boolean;
  details: string;
  location?: string;
}

const {
  websites,
  selectedWebsite,
  isAddModalOpen,
  isDetailsModalOpen,
  securityMetrics,
  attacksOverTime,
  threatDistribution,
  addWebsite,
  removeWebsite,
  toggleProtection,
  openWebsiteDetails,
  refreshWebsite,
  viewDetails,
  loadWebsitesFromDB,
  fetchAttackLogs,
  fetchAllAttackLogsForUser,
} = useDashboard();

const allAttacks = ref<Attack[]>([]);
onMounted(async () => {
  await checkAuth();
  if (!user.value) {
    router.push("/login");
  } else {
    await loadWebsitesFromDB();
    const { allAttacks: globalLogs } = await fetchAllAttackLogsForUser();
    allAttacks.value = globalLogs;
  }
});

// Logout
const logout = async () => {
  await api.post("http://localhost:8000/logout", {}, { withCredentials: true });
  user.value = null;
  router.push("/login");
};
</script>
