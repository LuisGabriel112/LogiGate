<script>
    import { Settings, User, Volume2, VolumeX, Warehouse, Info, Save, RotateCcw, Check } from 'lucide-svelte';
    import { settings, saveSettings } from '$lib/settings.svelte.js';
    import { addToast } from '$lib/toast.svelte.js';

    let saved = $state(false);

    function guardar() {
        saveSettings();
        saved = true;
        addToast('Configuración guardada', 'success');
        setTimeout(() => saved = false, 2000);
    }

    function resetear() {
        settings.nombre    = 'Luis Venegas';
        settings.rol       = 'Administrador';
        settings.beep      = true;
        settings.capacidad = 100;
        saveSettings();
        addToast('Configuración restablecida', 'info');
    }

    const ROLES = ['Administrador', 'Guardia', 'Supervisor'];
</script>

<div class="p-4 md:p-8 max-w-2xl mx-auto space-y-5 overflow-y-auto custom-scrollbar h-full">

    <!-- Header -->
    <div class="flex items-center justify-between">
        <div>
            <h2 class="text-xl font-black text-white tracking-tight">Configuración</h2>
            <p class="text-xs text-slate-500 mt-1">Preferencias del sistema y perfil de operador.</p>
        </div>
        <div class="flex gap-2">
            <button
                onclick={resetear}
                class="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-400 text-xs font-bold px-3 py-2 rounded-xl transition-colors"
            >
                <RotateCcw size={13} /> Restablecer
            </button>
            <button
                onclick={guardar}
                class="flex items-center gap-2 text-xs font-black px-4 py-2 rounded-xl transition-all shadow-lg
                    {saved ? 'bg-green-500 text-black shadow-green-500/20' : 'bg-orange-500 hover:bg-orange-400 text-black shadow-orange-500/20'}"
            >
                {#if saved}
                    <Check size={13} /> Guardado
                {:else}
                    <Save size={13} /> Guardar
                {/if}
            </button>
        </div>
    </div>

    <!-- Perfil -->
    <div class="bg-[#0E1015] border border-slate-800/60 rounded-xl overflow-hidden">
        <div class="flex items-center gap-3 px-5 py-4 border-b border-slate-800/40">
            <div class="p-2 bg-orange-500/10 border border-orange-500/20 rounded-lg">
                <User size={15} class="text-orange-400" />
            </div>
            <div>
                <p class="text-sm font-black text-white">Perfil de Operador</p>
                <p class="text-[10px] text-slate-600">Nombre e identidad mostrada en el sistema</p>
            </div>
        </div>
        <div class="p-5 space-y-4">
            <div class="space-y-1.5">
                <label class="text-[10px] font-black uppercase tracking-widest text-slate-500">Nombre completo</label>
                <input
                    bind:value={settings.nombre}
                    type="text"
                    placeholder="Nombre del operador"
                    class="w-full bg-[#080A0E] border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white placeholder:text-slate-700 focus:outline-none focus:border-orange-500 transition-colors"
                />
            </div>
            <div class="space-y-1.5">
                <label class="text-[10px] font-black uppercase tracking-widest text-slate-500">Rol</label>
                <div class="flex gap-2">
                    {#each ROLES as rol}
                        <button
                            onclick={() => settings.rol = rol}
                            class="flex-1 py-2 rounded-lg text-xs font-black uppercase tracking-wider transition-all border
                                {settings.rol === rol
                                    ? 'bg-orange-500 border-orange-500 text-black'
                                    : 'bg-slate-800/50 border-slate-700 text-slate-500 hover:text-white hover:border-slate-500'}"
                        >
                            {rol}
                        </button>
                    {/each}
                </div>
            </div>
        </div>
    </div>

    <!-- Escáner -->
    <div class="bg-[#0E1015] border border-slate-800/60 rounded-xl overflow-hidden">
        <div class="flex items-center gap-3 px-5 py-4 border-b border-slate-800/40">
            <div class="p-2 bg-slate-800 border border-slate-700 rounded-lg">
                {#if settings.beep}
                    <Volume2 size={15} class="text-slate-400" />
                {:else}
                    <VolumeX size={15} class="text-slate-600" />
                {/if}
            </div>
            <div>
                <p class="text-sm font-black text-white">Escáner</p>
                <p class="text-[10px] text-slate-600">Comportamiento al detectar placas</p>
            </div>
        </div>
        <div class="p-5">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-bold text-slate-200">Sonido al escanear</p>
                    <p class="text-[11px] text-slate-600 mt-0.5">Beep de confirmación al detectar placa</p>
                </div>
                <button
                    onclick={() => settings.beep = !settings.beep}
                    class="relative w-11 h-6 rounded-full transition-colors {settings.beep ? 'bg-orange-500' : 'bg-slate-700'}"
                >
                    <div class="absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-all {settings.beep ? 'left-5.5' : 'left-0.5'}"></div>
                </button>
            </div>
        </div>
    </div>

    <!-- Patio -->
    <div class="bg-[#0E1015] border border-slate-800/60 rounded-xl overflow-hidden">
        <div class="flex items-center gap-3 px-5 py-4 border-b border-slate-800/40">
            <div class="p-2 bg-slate-800 border border-slate-700 rounded-lg">
                <Warehouse size={15} class="text-slate-400" />
            </div>
            <div>
                <p class="text-sm font-black text-white">Patio</p>
                <p class="text-[10px] text-slate-600">Parámetros del espacio físico</p>
            </div>
        </div>
        <div class="p-5 space-y-1.5">
            <label class="text-[10px] font-black uppercase tracking-widest text-slate-500">Capacidad total de cajones</label>
            <input
                bind:value={settings.capacidad}
                type="number"
                min="1"
                max="500"
                class="w-full bg-[#080A0E] border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-orange-500 transition-colors"
            />
            <p class="text-[10px] text-slate-700">Afecta el mapa y el % de ocupación mostrado</p>
        </div>
    </div>

    <!-- Acerca de -->
    <div class="bg-[#0E1015] border border-slate-800/60 rounded-xl overflow-hidden">
        <div class="flex items-center gap-3 px-5 py-4 border-b border-slate-800/40">
            <div class="p-2 bg-slate-800 border border-slate-700 rounded-lg">
                <Info size={15} class="text-slate-400" />
            </div>
            <p class="text-sm font-black text-white">Acerca de LogiGate</p>
        </div>
        <div class="p-5 space-y-2">
            {#each [
                ['Versión',     'v2.4.1'],
                ['Frontend',    'SvelteKit 5 + Tailwind CSS 4'],
                ['Backend',     'FastAPI + SQLite'],
                ['Motor IA',    'YOLOv11 + EasyOCR'],
                ['Desarrollado por', 'JOLTEC'],
            ] as [k, v]}
                <div class="flex items-center justify-between py-2 border-b border-slate-800/30 last:border-0">
                    <span class="text-[11px] font-black uppercase tracking-widest text-slate-600">{k}</span>
                    <span class="text-xs text-slate-300 font-mono">{v}</span>
                </div>
            {/each}
        </div>
    </div>

</div>
