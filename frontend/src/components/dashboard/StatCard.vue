<script setup>
import { computed } from 'vue';

const props = defineProps({
  title: String,
  value: [String, Number],
  icon: [Object, Function],
  color: {
    type: String,
    default: 'admira' 
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
  <div class="bg-white rounded-2xl p-4 md:p-5 lg:p-6 border border-gray-200 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group w-full">
    <div :class="`absolute -right-4 -top-4 w-20 h-20 md:w-24 md:h-24 rounded-full opacity-20 transition-transform group-hover:scale-110 ${colorClasses.split(' ')[0]}`"></div>
    
    <div class="flex justify-between items-start mb-3 md:mb-4 relative z-10">
      <h3 class="text-[10px] md:text-[11px] font-bold text-slate-400 uppercase tracking-widest pr-2 leading-tight">{{ title }}</h3>
      <div :class="`p-2 md:p-2.5 rounded-xl shrink-0 ${colorClasses}`">
        <component :is="icon" class="w-4 h-4 md:w-5 md:h-5" />
      </div>
    </div>
    
    <div class="relative z-10">
      <div class="text-2xl md:text-3xl font-black text-slate-800 tracking-tight truncate">{{ value }}</div>
      <p class="text-[10px] md:text-xs text-slate-400 mt-1 md:mt-2 font-medium truncate">{{ sub }}</p>
    </div>
  </div>
</template>