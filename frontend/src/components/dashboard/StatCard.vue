<script setup>
import { computed } from 'vue';

const props = defineProps({
  title: String,
  value: [String, Number],
  icon: [Object, Function],
  color: {
    type: String,
    default: 'admira' // Cambiamos el default para que por defecto sea tu marca
  },
  sub: String
});

const colorClasses = computed(() => {
  const map = {
    blue: 'bg-blue-50 text-blue-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    red: 'bg-rose-50 text-rose-600',
    amber: 'bg-amber-50 text-amber-600',
    admira: 'bg-admira-50 text-admira-600'
  };
  return map[props.color] || map.admira;
});
</script>

<template>
  <div class="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
    <div :class="`absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-20 transition-transform group-hover:scale-110 ${colorClasses.split(' ')[0]}`"></div>
    
    <div class="flex justify-between items-start mb-4 relative z-10">
      <h3 class="text-[11px] font-bold text-slate-400 uppercase tracking-widest">{{ title }}</h3>
      <div :class="`p-2.5 rounded-xl ${colorClasses}`">
        <component :is="icon" class="w-5 h-5" />
      </div>
    </div>
    
    <div class="relative z-10">
      <div class="text-3xl font-black text-slate-800 tracking-tight">{{ value }}</div>
      <p class="text-xs text-slate-400 mt-2 font-medium">{{ sub }}</p>
    </div>
  </div>
</template>