<script>
    import { onMount } from 'svelte';
    import { Truck, RefreshCw, Info } from 'lucide-svelte';

    const API = 'https://192.168.1.68:8000';
    const TOTAL = 100;
    const COLS  = 10;

    let stats    = $state({ en_patio: 0, salidas_hoy: 0, denegados: 0, capacidad_total: TOTAL, ocupacion_pct: 0 });
    let loading  = $state(true);
    let refresh  = $state(false);

    // Generamos el grid: los primeros N cajones están "ocupados"
    // El tipo alterna de forma determinista según el índice (sin aleatoriedad)
    const cajones = $derived(
        Array.from({ length: TOTAL }, (_, i) => ({
            id: i + 1,
            ocupado: i < stats.en_patio,
            tipo: i < stats.en_patio ? (i % 4 === 3 ? 'van' : 'trailer') : null,
        }))
    );

    const token = () => localStorage.getItem('token') || '';

    async function cargarStats() {
        refresh = true;
        try {
            const res = await fetch(`${API}/api/v1/stats`, {
                headers: { Authorization: `Bearer ${token()}` },
            });
            if (res.ok) stats = await res.json();
        } finally {
            loading  = false;
            refresh  = false;
        }
    }

    onMount(() => {
        cargarStats();
        const interval = setInterval(cargarStats, 30_000);
        return () => clearInterval(interval);
    });

    const pctColor = (p) =>
        p >= 85 ? 'bg-red-500'
        : p >= 60 ? 'bg-yellow-500'
        : 'bg-green-500';

    const filas = $derived(
        Array.from({ length: TOTAL / COLS }, (_, f) =>
            cajones.slice(f * COLS, f * COLS + COLS)
        )
    );
</script>

<div class="p-4 md:p-8 space-y-4 md:space-y-6 h-full overflow-y-auto custom-scrollbar">

    <!-- Encabezado -->
    <div class="flex items-center justify-between">
        <div>
            <h2 class="text-2xl font-black text-white tracking-tight">Mapa de Patio</h2>
            <p class="text-xs text-slate-500 mt-1">Vista en tiempo real de la ocupación del patio logístico</p>
        </div>
        <button
            onclick={cargarStats}
            disabled={refresh}
            class="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-bold px-4 py-2.5 rounded-lg transition-colors disabled:opacity-50"
        >
            <RefreshCw size={14} class={refresh ? 'animate-spin' : ''} /> Actualizar
        </button>
    </div>

    <!-- Métricas rápidas -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        {#each [
            { label: 'En Patio',       value: stats.en_patio,      color: 'text-orange-500' },
            { label: 'Disponibles',    value: TOTAL - stats.en_patio, color: 'text-green-500' },
            { label: 'Salidas Hoy',    value: stats.salidas_hoy,   color: 'text-blue-400'  },
            { label: 'Denegados',      value: stats.denegados,     color: 'text-red-400'   },
        ] as m}
            <div class="bg-[#1A1F26] border border-slate-800 rounded-xl p-5">
                <p class="text-[9px] font-black uppercase tracking-widest text-slate-500 mb-2">{m.label}</p>
                <p class="text-3xl font-black {m.color}">{loading ? '—' : m.value}</p>
            </div>
        {/each}
    </div>

    <!-- Barra de ocupación -->
    <div class="bg-[#1A1F26] border border-slate-800 rounded-xl p-5">
        <div class="flex justify-between items-center mb-3">
            <span class="text-xs font-black uppercase text-slate-400">Ocupación Global</span>
            <span class="text-sm font-black {stats.ocupacion_pct >= 85 ? 'text-red-400' : stats.ocupacion_pct >= 60 ? 'text-yellow-400' : 'text-green-400'}">
                {stats.ocupacion_pct}%
            </span>
        </div>
        <div class="w-full bg-slate-800 h-3 rounded-full overflow-hidden">
            <div
                class="h-full rounded-full transition-all duration-700 {pctColor(stats.ocupacion_pct)}"
                style="width: {stats.ocupacion_pct}%"
            ></div>
        </div>
        <div class="flex justify-between mt-2 text-[9px] text-slate-600 font-bold">
            <span>0</span><span>Capacidad: {TOTAL} cajones</span>
        </div>
    </div>

    <!-- Grid del patio -->
    <div class="bg-[#1A1F26] border border-slate-800 rounded-xl p-4 md:p-6">
        <div class="flex items-center gap-3 mb-6 flex-wrap">
            <h4 class="text-sm font-black text-white uppercase tracking-widest">Plano del Patio</h4>
            <div class="flex items-center gap-4 ml-auto text-[10px] font-bold">
                <div class="flex items-center gap-1.5">
                    <div class="w-3 h-3 rounded-sm bg-orange-500"></div>
                    <span class="text-slate-400">Ocupado (Trailer)</span>
                </div>
                <div class="flex items-center gap-1.5">
                    <div class="w-3 h-3 rounded-sm bg-orange-300"></div>
                    <span class="text-slate-400">Ocupado (Van)</span>
                </div>
                <div class="flex items-center gap-1.5">
                    <div class="w-3 h-3 rounded-sm bg-slate-800 border border-slate-700"></div>
                    <span class="text-slate-400">Disponible</span>
                </div>
            </div>
        </div>

        {#if loading}
            <div class="h-64 flex items-center justify-center">
                <div class="w-8 h-8 border-4 border-slate-700 border-t-orange-500 rounded-full animate-spin"></div>
            </div>
        {:else}
            <!-- Zona de acceso -->
            <div class="mb-4 flex items-center gap-3">
                <div class="flex-1 h-1 bg-orange-500/30 rounded"></div>
                <span class="text-[9px] font-black uppercase tracking-widest text-orange-500/60">Zona de Acceso Principal</span>
                <div class="flex-1 h-1 bg-orange-500/30 rounded"></div>
            </div>

            <!-- Grid de cajones -->
            <div class="space-y-2">
                {#each filas as fila, fi}
                    <div class="flex items-center gap-2">
                        <span class="text-[9px] text-slate-700 font-mono w-4">{String.fromCharCode(65 + fi)}</span>
                        {#each fila as cajon}
                            <div
                                class="flex-1 aspect-square rounded-sm md:rounded-md border flex items-center justify-center relative group cursor-default
                                    {cajon.ocupado
                                        ? cajon.tipo === 'trailer'
                                            ? 'bg-orange-500/80 border-orange-600'
                                            : 'bg-orange-300/70 border-orange-400'
                                        : 'bg-slate-900 border-slate-800 hover:border-slate-600'}"
                                title="Cajón {cajon.id}"
                            >
                                {#if cajon.ocupado}
                                    <Truck size={12} class="text-black/60" />
                                {/if}
                                <!-- Tooltip -->
                                <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-slate-950 border border-slate-700 rounded text-[9px] text-slate-300 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 font-bold">
                                    {cajon.ocupado ? `Cajón ${cajon.id} · ${cajon.tipo}` : `Cajón ${cajon.id} · libre`}
                                </div>
                            </div>
                        {/each}
                    </div>
                {/each}
            </div>

            <!-- Muelles -->
            <div class="mt-4 flex items-center gap-3">
                <div class="flex-1 h-1 bg-blue-500/30 rounded"></div>
                <span class="text-[9px] font-black uppercase tracking-widest text-blue-500/60">Muelles de Carga</span>
                <div class="flex-1 h-1 bg-blue-500/30 rounded"></div>
            </div>
            <div class="flex gap-2 mt-2">
                {#each Array.from({ length: 5 }, (_, i) => i + 1) as m}
                    <div class="flex-1 h-8 bg-blue-500/10 border border-blue-500/20 rounded-md flex items-center justify-center">
                        <span class="text-[9px] font-black text-blue-400">M{m}</span>
                    </div>
                {/each}
            </div>
        {/if}
    </div>

    <!-- Info -->
    <div class="flex items-start gap-3 bg-slate-900/50 border border-slate-800 rounded-xl p-4">
        <Info size={16} class="text-slate-500 mt-0.5 shrink-0" />
        <p class="text-xs text-slate-500">
            La distribución de cajones es una representación visual estimada basada en los registros activos.
            Se actualiza automáticamente cada 30 segundos.
        </p>
    </div>
</div>
