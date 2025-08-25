<template>
  <!-- v-if="isOpen" -->
  <div
    
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50"
    @click.self="$emit('close')"
  >
    <div class="card p-6 w-full max-w-md animate-slide-up">
      <h2 class="text-xl font-semibold text-white mb-4">Add New Website</h2>

      <form @submit.prevent="handleSubmit">
        <div class="space-y-4">
          <div>
            <label for="name" class="block text-sm font-medium text-gray-300 mb-2">
              Website Name
            </label>
            <input
              id="name"
              v-model="form.name"
              type="text"
              required
              class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="My Website"
            />
          </div>

          <div>
            <label for="url" class="block text-sm font-medium text-gray-300 mb-2">
              Website URL
            </label>
            <input
              id="url"
              v-model="form.url"
              type="url"
              required
              class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="https://example.com"
            />
          </div>
        </div>

        <div class="flex justify-end space-x-3 mt-6">
          <button type="button" @click="$emit('close')" class="btn-secondary">Cancel</button>
          <button type="submit" class="btn-primary">Add Website</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">

import { ref, onMounted } from "vue";
import api from "../../composables/axios"; // assumes axios instance is in composables

const emit = defineEmits<{
  (e: 'add'): void;
  (e: 'close'): void;
}>();

// const props = defineProps<{ modelValue: boolean }>();
const existingWebsites = ref<string[]>([]);

const form = ref({
  name: '',
  url: ''
});

const isSubmitting = ref(false);

onMounted(async () => {
  try {
    const userRes = await api.get("http://localhost:8000/me", { withCredentials: true });
    const userId = userRes.data.id;

    const websitesRes = await api.get("http://localhost:8000/websites/", { withCredentials: true });
    existingWebsites.value = websitesRes.data.map(site => site.url.toLowerCase());
  } catch (error) {
    console.error("Failed to fetch user or websites", error);
  }
});

const handleSubmit = async () => {
  if (!form.value.name || !form.value.url || isSubmitting.value) return;

  const enteredUrl = form.value.url.trim().toLowerCase();

  if (existingWebsites.value.includes(enteredUrl)) {
    alert("This website URL is already added.");
    return;
  }
  try {
    isSubmitting.value = true;
    const sessionResponse = await api.get("http://localhost:8000/me", { withCredentials: true });
    const userId = sessionResponse.data.id;

    if (!userId) throw new Error("User not logged in");

    const response = await api.post("http://localhost:8000/websites/", {
      name: form.value.name,
      url: form.value.url,
      user_id: userId
    }, {
      withCredentials: true
    });

    console.log("Website added:", response.data);
    emit('add');  
    form.value.name = '';
    form.value.url = '';
    emit("close");
  } catch (error) {
    console.error("Failed to add website:", error);
  }finally {
    isSubmitting.value = false;
  }
};

// interface Emits {
//   (e: 'close'): void;
//   (e: 'add', name: string, url: string): void;
// }

// defineProps<Props>();
// const emit = defineEmits<Emits>();

// const form = reactive({
//   name: '',
//   url: '',
// });

// const handleSubmit = () => {
//   if (form.name && form.url) {
//     console.log("Adding website:", form.name, form.url);
//     emit('add', form.name, form.url);
//     form.name = '';
//     form.url = '';
//   }
// };
</script>
