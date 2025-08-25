<template>
  <div
    class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50"
  >
    <div class="bg-[#1f2937] rounded-xl shadow-2xl p-8 w-[600px] relative">

      <button
        class="absolute top-3 right-3 text-gray-400 hover:text-gray-200 text-xl"
        @click="emitClose"
      >
        ✕
      </button>

      <h2 class="text-xl font-semibold mb-4 text-center text-white">
        Enable XSS Protection
      </h2>
      <p class="text-sm text-gray-400 mb-3 text-center">
        Copy the code below and add it to the <strong>&lt;head&gt;</strong> section of your website:
      </p>

      <!-- Code Box -->
      <div class="relative bg-gray-800 border border-gray-600 rounded mb-6">
        <div class="absolute bottom-2 right-2 flex gap-2">
          <button
            @click="copyCode"
            class="text-xs px-2 py-1 border border-gray-500 rounded text-gray-300 hover:bg-gray-700"
          >
            {{ copied ? "Copied!" : "Copy" }}
          </button>
        </div>
        <textarea
          readonly
          class="w-full p-4 rounded bg-transparent text-gray-200 text-sm resize-none"
          rows="3"
        >{{ code }}</textarea>
      </div>

      <!-- Buttons -->
      <div class="flex justify-center gap-4">
        <button
          v-if="!checkComplete"
          @click="checkCDNCode"
          class="bg-blue-500 text-white px-5 py-2 rounded hover:bg-blue-600"
          :disabled="checking"
        >
          {{ checking ? "Checking..." : "Check" }}
        </button>
        <button
          v-if="checkComplete"
          @click="emitConfirm"
          class="bg-green-500 text-white px-5 py-2 rounded hover:bg-green-600"
        >
          OK
        </button>
        <button
          v-if="!checkComplete"
          @click="emitCancel"
          class="bg-gray-500 text-white px-5 py-2 rounded hover:bg-gray-600"
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import api from "../../composables/axios"; // adjust path as needed

const props = defineProps<{
  code: string;
  websiteId: number;
}>();

const emit = defineEmits(["confirm", "cancel", "close"]);

const copied = ref(false);
const checkComplete = ref(false);
const checking = ref(false);

function copyCode() {
  navigator.clipboard.writeText(props.code);
  copied.value = true;
}

// Auto-check via FastAPI endpoint
async function checkCDNCode() {
  checking.value = true;

  const scriptToCheck = `<script src="http://127.0.0.1:8000/cdn/webshield-xss-agent.js?wid=${props.websiteId}"><\/script>`;

  try {
    const response = await api.get("/check-cdn-code", {
      params: {
        wid: props.websiteId,
        expected_script: scriptToCheck,
      },
      withCredentials: true,
    });

    if (response.data.success) {
      checkComplete.value = true;
    } else {
      alert("CDN code not found on the site.");
    }
  } catch (err) {
    alert("Error checking CDN code.");
    console.error(err);
  } finally {
    checking.value = false;
  }
}

async function emitConfirm() {
  try {
    await api.post(`/websites/${props.websiteId}/update-protection`, {
      protection_type: "xss",  
      enabled: true,
    }, { withCredentials: true });

    emit("confirm");  
  } catch (error) {
    console.error("Failed to update protection in database:", error);
    alert("Failed to update protection. Please try again.");
  }
}

function emitCancel() {
  emit("cancel");
}
function emitClose() {
  emit("close");
}
</script>
