<template>
  <label class="flex items-center cursor-pointer">
    <input
      type="checkbox"
      class="hidden"
      :checked="modelValue"
      @change="handleClick"
    />
    <div
      :class="[
        'w-10 h-5 rounded-full transition-colors duration-300',
        modelValue ? 'bg-blue-500' : 'bg-gray-600'
      ]"
    >
      <div
        :class="[
          'w-5 h-5 bg-white rounded-full shadow transform transition-transform duration-300',
          modelValue ? 'translate-x-5' : 'translate-x-0'
        ]"
      ></div>
    </div>
  </label>
</template>

<script setup lang="ts">
defineProps<{ modelValue: boolean }>();
const emit = defineEmits(['update:modelValue', 'attemptToggle']);

function handleClick() {
  emit('attemptToggle');
}
</script>
