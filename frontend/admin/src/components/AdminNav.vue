<script setup lang="ts">
import {computed, onMounted} from "vue";
import {useStore} from "@nanostores/vue";
import {$activeTab, $currentUser, hydrateCurrentUser} from "../stores/auth";
import {tabsForRole} from "../lib/nav";
import type {SessionUser} from "../lib/auth";

/**
 * The dashboard tab bar -- `renderShell()`'s nav block from docs/proto/shared.js,
 * as the app's first hydrated island.
 *
 * Props carry the SSR render (the stores are deliberately empty on the server;
 * see stores/auth.ts). `onMounted` then hands the same values to the stores, so
 * the markup is identical before and after hydration -- no mismatch, no flash --
 * and every later island can read `$currentUser` instead of prop-drilling.
 */
const props = defineProps<{
    user: SessionUser;
    activeTab: string | null;
}>();

onMounted(() => hydrateCurrentUser(props.user, props.activeTab));

const storeUser = useStore($currentUser);
const storeTab = useStore($activeTab);

// Props win until hydration fills the stores in; identical values either way.
const user = computed(() => storeUser.value ?? props.user);
const activeTab = computed(() => storeTab.value ?? props.activeTab);
const tabs = computed(() => tabsForRole(user.value));
</script>

<template>
    <nav class="max-w-6xl mx-auto px-6 flex gap-6 text-sm font-medium text-inksoft">
        <a
            v-for="tab in tabs"
            :key="tab.id"
            :href="tab.href"
            :aria-current="tab.id === activeTab ? 'page' : undefined"
            :class="[
                'py-3 border-b-2 transition-colors',
                tab.id === activeTab
                    ? 'border-teal text-ink font-semibold'
                    : 'border-transparent text-inksoft hover:text-ink',
            ]"
        >
            {{ tab.label }}
        </a>
    </nav>
</template>
