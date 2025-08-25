<template>
  <div class="bg-gray-900 min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-gray-800 text-white rounded-lg shadow-lg p-8 my-16">
      <!-- Logo and Title -->
      <div class="flex items-center justify-center mb-6">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-8 w-8 text-blue-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 12l2 2 4-4M5 4a12 12 0 0114 0"
          />
        </svg>
        <span class="ml-2 text-xl font-bold">WebShieldAI</span>
      </div>

      <!-- Heading -->
      <h2 class="text-xl font-bold mb-4 text-center">Create your account</h2>

      <!-- Signup Form -->
      <form @submit.prevent="handleSignup">
        <label class="block mb-2 text-sm">First Name</label>
        <input
          v-model="firstName"
          type="text"
          required
          class="w-full mb-4 px-3 py-2 rounded bg-gray-700 border border-gray-600 focus:ring-2 focus:ring-blue-500"
        />

        <label class="block mb-2 text-sm">Last Name</label>
        <input
          v-model="lastName"
          type="text"
          required
          class="w-full mb-4 px-3 py-2 rounded bg-gray-700 border border-gray-600 focus:ring-2 focus:ring-blue-500"
        />

        <label class="block mb-2 text-sm">Email</label>
        <input
          v-model="email"
          type="email"
          required
          class="w-full mb-4 px-3 py-2 rounded bg-gray-700 border border-gray-600 focus:ring-2 focus:ring-blue-500"
        />

        <label class="block mb-2 text-sm">Password</label>
        <input
          v-model="password"
          type="password"
          required
          class="w-full mb-4 px-3 py-2 rounded bg-gray-700 border border-gray-600 focus:ring-2 focus:ring-blue-500"
        />

        <label class="block mb-2 text-sm">Confirm Password</label>
        <input
          v-model="confirmPassword"
          type="password"
          required
          class="w-full mb-4 px-3 py-2 rounded bg-gray-700 border border-gray-600 focus:ring-2 focus:ring-blue-500"
        />

        <label class="block text-sm mb-4">
          <input
            v-model="agreeTerms"
            type="checkbox"
            required
            class="mr-2 align-middle"
          />
          <span class="align-middle">
            I agree to the
            <a href="#" class="text-blue-400 hover:text-blue-300 underline"
              >Terms of Service</a
            >
            and
            <a href="#" class="text-blue-400 hover:text-blue-300 underline"
              >Privacy Policy</a
            >.
          </span>
        </label>

        <button
          type="submit"
          class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
        >
          Create Account
        </button>
      </form>

      <!-- Sign-in Link -->
      <p class="text-sm text-center mt-4 text-gray-400">
        Already have an account?
        <router-link to="/login" class="text-blue-400 hover:text-blue-300"
          >Sign in</router-link
        >
      </p>

      <!-- Footer -->
      <p class="mt-6 text-center text-xs text-gray-500">
        © 2023 WebShieldAI. All rights reserved.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";

const router = useRouter();
const firstName = ref("");
const lastName = ref("");
const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const agreeTerms = ref(false);
import api from "../composables/axios"
async function handleSignup() {
  if (password.value !== confirmPassword.value) {
    alert("Passwords do not match!");
    return;
  }

  try {
    const response = await api.post("http://localhost:8000/users/", {
      name: `${firstName.value} ${lastName.value}`,
      email: email.value,
      password: password.value,
      plan: "free",
    });
    router.push("/login");
  } catch (err) {
    alert("Signup failed!");
    console.error(err);
  }
}
</script>
