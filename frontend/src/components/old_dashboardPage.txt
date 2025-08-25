<template>
  <div class="min-h-screen gradient-bg">
    <header class="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center space-x-3">
            <ShieldCheckIcon class="w-8 h-8 text-blue-500" />
            <h1 class="text-xl font-bold text-white">WebShieldAI Dashboard</h1>
          </div>
          <button
            @click="
              () => {
                isAddModalOpen = true;
              }
            "
            class="btn-primary flex items-center space-x-2"
          >
            <PlusIcon class="w-4 h-4" />
            <span>Add Website</span>
          </button>
        </div>
        <button @click="logout" class="text-sm text-white hover:text-red-400">
          Logout
        </button>
      </div>
    </header>

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

      <!-- Charts Section -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <SecurityChart title="Attacks Over Time" :data="attacksOverTime" type="line" />
        <SecurityChart
          title="Threat Distribution"
          :data="threatDistribution"
          type="doughnut"
        />
      </div>

      <!-- Websites Grid -->
      <div class="mb-8">
        <h2 class="text-2xl font-bold text-white mb-6">Protected Websites</h2>
        <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          <WebsiteCard
            v-for="website in websites"
            :key="website.id"
            :website="website"
            @toggle-protection="toggleProtection"
            @remove="removeWebsite"
            @details="openWebsiteDetails"
            @refresh="refreshWebsiteData"
          />
        </div>
      </div>

      <!-- Attack Logs -->
      <div class="mb-8">
        <h2 class="text-2xl font-bold text-white mb-6">Global Attack Logs</h2>
        <AttackLogs :attacks="allAttacks" />
      </div>
    </main>

    <!-- Modals -->
    <AddWebsiteModal
      :isOpen="isAddModalOpen"
      @close="isAddModalOpen = false"
      @add="addWebsite"
    />
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
import MetricsCard from "./Dashboard/MetricsCard.vue";
import WebsiteCard from "./Dashboard/WebsiteCard.vue";
import SecurityChart from "./Dashboard/SecurityChart.vue";
import AttackLogs from "./Dashboard/AttackLogs.vue";
import AddWebsiteModal from "./UI/AddWebsiteModal.vue";
import SecurityDetailsModal from "./UI/SecurityDetailsModal.vue";
import api from "../composables/axios";

const router = useRouter();
const { user, checkAuth } = useAuth();

onMounted(async () => {
  await checkAuth();
  if (!user.value) {
    router.push("/login");
  }
});

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
  refreshWebsiteData,
} = useDashboard();

const logout = async () => {
  await api.post("http://localhost:8000/logout", {}, { withCredentials: true });
  user.value = null;
  router.push("/login");
};


// import { ref } from 'vue';
// import WebsiteCard from '../components/Dashboard/WebsiteCard.vue';
// import AddWebsiteModal from '../components/Dashboard/AddWebsiteModal.vue';
// import { useDashboard } from '../composables/useDashboard';

// const isAddModalOpen = ref(false);
// const { websites, addWebsite } = useDashboard();
// const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

// const handleAddWebsite = async (name: string, url: string) => {
//   await addWebsite({
//     name,
//     url,
//     user_id: currentUser.id,
//     defacement_enabled: false,
//     sqli_enabled: false,
//     dom_enabled: false,
//   });
//   isAddModalOpen.value = false;
// };
</script>


