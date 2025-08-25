<template>
  <div class="bg-[#1f2937] rounded-lg p-5 shadow-lg relative">
    <!-- Top Row -->
    <div class="flex justify-between items-center mb-3">
      <div class="flex items-center gap-2">
        <span :class="statusClass(website.status)" class="w-3 h-3 rounded-full"></span>
        <h3 class="text-md font-semibold text-white">{{ website.name }}</h3>
      </div>
      <div class="flex items-center gap-2 text-gray-400">
        <button class="hover:text-white" @click="emitRefresh" title="Refresh"><ArrowPathIcon class="w-4 h-4" /></button>
        <button class="hover:text-white" @click="emitDetails" title="View Details">
          <EyeIcon class="w-4 h-4" />
        </button>
        <button class="hover:text-white" @click="emitRemove" title="Delete"><TrashIcon class="w-4 h-4" /></button>
      </div>
    </div>

    <!-- Website URL -->
    <p class="text-blue-400 text-sm mb-4">{{ website.url }}</p>

    <!-- Metrics -->
    <div class="grid grid-cols-2 gap-3 mb-4">
      <div class="bg-gray-700 p-3 text-center rounded-md">
        <p class="text-gray-400 text-xs">Total Requests</p>
        <p class="text-white text-lg font-bold">
          {{ formatNumber(website.metrics.totalRequests) }}
        </p>
      </div>
      <div class="bg-gray-700 p-3 text-center rounded-md">
        <p class="text-gray-400 text-xs">Blocked Attacks</p>
        <p class="text-red-400 text-lg font-bold">
          {{ formatNumber(website.metrics.blockedAttacks) }}
        </p>
      </div>
      <div class="bg-gray-700 p-3 text-center rounded-md">
        <p class="text-gray-400 text-xs">Uptime</p>
        <p class="text-green-400 text-lg font-bold">{{ website.metrics.uptime }}%</p>
      </div>
      <div class="bg-gray-700 p-3 text-center rounded-md">
        <p class="text-gray-400 text-xs">Response Time</p>
        <p class="text-blue-400 text-lg font-bold">
          {{ website.metrics.responseTime }}ms
        </p>
      </div>
    </div>

    <!-- Protections -->
    <h4 class="text-gray-300 font-medium mb-2">Security Protections</h4>
    <div class="space-y-2">
      <div class="flex justify-between items-center">
        <span class="text-sm text-gray-400">SQL Injection Protection</span>
        <ToggleSwitch
          v-model="protections[0].state"
          @attemptToggle="() => onAttemptToggle(0)"
        />
      </div>
      <div class="flex justify-between items-center">
        <span class="text-sm text-gray-400">XSS Protection</span>
        <ToggleSwitch
          v-model="protections[1].state"
          @attemptToggle="() => onAttemptToggle(1)"
        />
      </div>
      <div class="flex justify-between items-center">
        <span class="text-sm text-gray-400">Dom Protection</span>
        <ToggleSwitch
          v-model="protections[2].state"
          @attemptToggle="() => onAttemptToggle(2)"
        />
      </div>
      <div class="flex justify-between items-center">
        <span class="text-sm text-gray-400">Defacement Protection</span>
        <ToggleSwitch
          v-model="protections[3].state"
          @attemptToggle="() => onAttemptToggle(3)"
        />
      </div>
    </div>

    <p class="text-xs text-gray-500 mt-4">
      Last checked: {{ formatDate(website.lastChecked) }}
    </p>

    <!-- Modals -->
    <SQLToggleModal
      v-if="showModal && targetToggleIndex === 0"
      :code="sqlCode"
      :website-id="website.id"
      @confirm="confirmToggle"
      @cancel="cancelToggle"
      @close="cancelToggle"
    />

    <XSSToggleModal
      v-if="showModal && targetToggleIndex === 1"
      :code="xssCode"
      :website-id="website.id"
      @confirm="confirmToggle"
      @cancel="cancelToggle"
      @close="cancelToggle"
    />
    <DomToggleModal
      v-if="showModal && targetToggleIndex === 2"
      :code="domCode"
      :website-id="website.id"
      @confirm="confirmToggle"
      @cancel="cancelToggle"
      @close="cancelToggle"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, toRefs, watchEffect } from "vue";
import ToggleSwitch from "../UI/ToggleSwitch.vue";
import XSSToggleModal from "../UI/XSSToggleModal.vue";
import DomToggleModal from "../UI/DomToggleModal.vue";
import SQLToggleModal from "../UI/SQLToggleModal.vue";
import api from "../../composables/axios";
import { onMounted } from "vue";
import { EyeIcon, TrashIcon, ArrowPathIcon} from '@heroicons/vue/24/outline';

// Props
const props = defineProps<{ website: any }>();
const { website } = toRefs(props);

// Emits
const emit = defineEmits<{
  (e: "refresh", websiteId: string): void;
  (e: "details", website: any): void;
  (e: "remove", websiteId: string): void;
}>();

// Reactive protections state
const protections = ref([
  { name: "SQL Injection", state: false },
  { name: "XSS", state: false },
  { name: "Dom", state: false },
  { name: "Defacement", state: false },
]);

onMounted(async () => {
  await fetchWebsiteData();
});

async function fetchWebsiteData() {
  try {
    const web_response = await api.get(`/websites/${website.value.id}`, {
      withCredentials: true,
    });
    // console.log("Website data fetched:", web_response.data);

    protections.value = [
      { name: "SQL Injection", state: web_response.data.sqli_enabled },
      { name: "XSS", state: web_response.data.xss_enabled },
      { name: "Dom", state: web_response.data.dom_enabled },
      { name: "Defacement", state: web_response.data.defacement_enabled },
    ];

    if (web_response.data.sqli_enabled) {
      targetToggleIndex.value = 0;
      confirmToggle();
    }
    if (web_response.data.xss_enabled) {
      targetToggleIndex.value = 1;
      confirmToggle();
    }
    if (web_response.data.dom_enabled) {
      targetToggleIndex.value = 2;
      confirmToggle();
    }
    if (web_response.data.defacement_enabled) {
      targetToggleIndex.value = 3;
      confirmToggle();
    }
  } catch (error) {
    console.error("Failed to fetch website data:", error);
    alert("Failed to load website data. Please try again.");
  }
}

// Modal handling
const showModal = ref(false);
const targetToggleIndex = ref<number | null>(null);

// Example script codes
const sqlCode = `<script src="http://127.0.0.1:8000/cdn/webshield-sql-agent.js?wid=${website.value.id}"><\/script>`;
const xssCode = `<script src="http://127.0.0.1:8000/cdn/webshield-xss-agent.js?wid=${website.value.id}"><\/script>`;
const domCode = `<script src="http://127.0.0.1:8000/cdn/dom-defacement-agent.js?wid=${website.value.id}"><\/script>`;

// Emit helpers
function emitRefresh() {
  emit("refresh", website.value.id);
}
function emitDetails() {
  emit("details", website.value);
}
function emitRemove() {
  emit("remove", website.value.id);
}

// UI helpers
function statusClass(status: string) {
  return status === "online"
    ? "bg-green-400"
    : status === "warning"
    ? "bg-yellow-400"
    : "bg-red-500";
}

function formatNumber(num: number) {
  return num.toLocaleString();
}

function formatDate(date: string) {
  const d = new Date(date);
  return d.toLocaleString();
}

async function onAttemptToggle(index: number) {
  const currentState = protections.value[index].state;

  if (!currentState) {
    targetToggleIndex.value = index;
    if (index == 3) {
      try {
        await api.post(
          `/websites/${website.value.id}/toggle-defacement?enable=true`,
          {},
          { withCredentials: true }
        );
      } catch (error) {
        console.error("Failed to toggle defacement protection:", error);
      }
      showModal.value = true;
      confirmToggle();
      return;
    } else {
      showModal.value = true;
    }
  } else {
    protections.value[index].state = false;
    if (index == 3) {
      try {
        await api.post(
          `/websites/${website.value.id}/toggle-defacement?enable=false`,
          {},
          { withCredentials: true }
        );
      } catch (error) {
        console.error("Failed to toggle defacement protection:", error);
      }
      return;
    } else {
      try {
      await api.post(
        `/websites/${website.value.id}/update-protection`,
        {
          protection_type: getProtectionType(index),
          enabled: false,
        },
        { withCredentials: true }
      );
    } catch (error) {
      console.error("Failed to disable protection:", error);
      alert("Failed to update server.");
    }
    }
    
  }
}

function getProtectionType(index: number): "xss" | "sqli" | "dom" | "defacement" {
  if (index === 0) return "sqli";
  if (index === 1) return "xss";
  if (index === 2) return "dom";
  return "defacement";
}

// Confirm/Cancel Toggle
function confirmToggle() {
  if (targetToggleIndex.value !== null) {
    protections.value[targetToggleIndex.value].state = true;
  }
  closeModal();
}
function cancelToggle() {
  if (targetToggleIndex.value !== null) {
    protections.value[targetToggleIndex.value].state = false;
  }
  closeModal();
}
function closeModal() {
  showModal.value = false;
  targetToggleIndex.value = null;
}
</script>
