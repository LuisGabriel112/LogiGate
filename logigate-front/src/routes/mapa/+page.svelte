<script>
    import { onMount } from 'svelte';
    import { Truck, RefreshCw, Info, Grid3x3, X } from 'lucide-svelte';
    import { fly } from 'svelte/transition';

    const API = typeof window !== 'undefined' ? `http://${window.location.hostname}:8000` : 'http://localhost:8000';
    const TOTAL = 100;
    const COLS  = 10;
    const FILAS = ['A','B','C','D','E','F','G','H','I','J'];

    let stats    = $state({ en_patio: 0, salidas_hoy: 0, denegados: 0, capacidad_total: TOTAL, ocupacion_pct: 0 });
    let loading  = $state(true);
    let refresh  = $state(false);
    let selected = $state(null);

    const cajones = $derived(
        Array.from({ length: TOTAL }, (_, i) => ({
            id:      i + 1,
            fila:    FILAS[Math.floor(i / COLS)],
            col:     (i % COLS) + 1,
            ocupado: i < stats.en_patio,
            tipo:    i < stats.en_patio ? (i % 4 === 3 ? 'van' : 'trailer') : null,
        }))
    );

    const token = () => (typeof localStorage !== 'undefined' ? localStorage.getItem('token') : '') || '';

    async function cargarStats() {
        refresh = true;
        try {
            const res = await fetch(`${API}/api/v1/stats`, { headers: { Authorization: `Bearer ${token()}` } });
            if (res.ok) stats = await res.json();
        } finally { loading = false; refresh = false; }
    }

    function seleccionar(cajon) { selected = selected?.id === cajon.id ? null : cajon; }
    function cerrar() { selected = null; }

    onMount(() => {
        cargarStats();
        const iv = setInterval(cargarStats, 30_000);
        const closeEsc = (e) => { if (e.key === 'Escape') cerrar(); };
        document.addEventListener('keydown', closeEsc);
        return () => { clearInterval(iv); document.removeEventListener('keydown', closeEsc); };
    });

    const pctColor = (p) => p >= 85 ? 'bg-red-500'    : p >= 60 ? 'bg-yellow-500' : 'bg-green-500';
    const pctText  = (p) => p >= 85 ? 'text-red-400'  : p >= 60 ? 'text-yellow-400' : 'text-green-400';

    const filas = $derived(
        Array.from({ length: TOTAL / COLS }, (_, f) => cajones.slice(f * COLS, f * COLS + COLS))
    );
</script>

<div class="p-4 md:p-6 space-y-5 h-full overflow-y-auto custom-scrollbar">

    <!-- Encabezado -->
    <div class="flex items-center justify-between">
        <div>
            <h2 class="text-xl font-black text-white tracking-tight">Mapa de Patio</h2>
            <p class="text-xs text-slate-600 mt-0.5">Ocupación en tiempo real · actualiza cada 30 s</p>
        </div>
        <button
            onclick={cargarStats}
            disabled={refresh}
            class="flex items-center gap-2 bg-[#0E1015] hover:bg-slate-800/60 border border-slate-800/60 text-slate-400 text-xs font-bold px-4 py-2 rounded-xl transition-colors disabled:opacity-50"
        >
            <RefreshCw size={13} class={refresh ? 'animate-spin' : ''} /> Actualizar
        </button>
    </div>

    <!-- KPIs -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        {#each [
            { label: 'En Patio',    value: stats.en_patio,           color: 'text-orange-400', bg: 'border-orange-500/15' },
            { label: 'Disponibles', value: TOTAL - stats.en_patio,   color: 'text-green-400',  bg: 'border-green-500/15'  },
            { label: 'Salidas Hoy', value: stats.salidas_hoy,        color: 'text-blue-400',   bg: 'border-blue-500/15'   },
            { label: 'Denegados',   value: stats.denegados,          color: 'text-red-400',    bg: 'border-red-500/15'    },
        ] as m}
            <div class="bg-[#0E1015] border {m.bg} rounded-xl p-4">
                <p class="text-[9px] font-black uppercase tracking-widest text-slate-600 mb-2">{m.label}</p>
                <p class="text-3xl font-black {m.color}">{loading ? '—' : m.value}</p>
            </div>
        {/each}
    </div>

    <!-- Barra de ocupación global -->
    <div class="bg-[#0E1015] border border-slate-800/60 rounded-xl p-5">
        <div class="flex justify-between items-center mb-3">
            <span class="text-xs font-bold text-slate-400">Ocupación Global</span>
            <span class="text-sm font-black {pctText(stats.ocupacion_pct)}">{stats.ocupacion_pct}%</span>
        </div>
        <div class="w-full bg-slate-800/50 h-2 rounded-full overflow-hidden">
            <div
                class="h-full rounded-full transition-all duration-700 {pctColor(stats.ocupacion_pct)}"
                style="width:{stats.ocupacion_pct}%"
            ></div>
        </div>
        <div class="flex justify-between mt-2 text-[9px] text-slate-700 font-bold">
            <span>0 cajones</span>
            <span>Capacidad máx: {TOTAL}</span>
        </div>
    </div>

    <!-- Grid del patio -->
    <div class="bg-[#0E1015] border border-slate-800/60 rounded-xl p-5">
        <!-- Header del grid -->
        <div class="flex items-center gap-3 mb-5 flex-wrap">
            <div class="flex items-center gap-2">
                <Grid3x3 size={16} class="text-slate-500" />
                <h4 class="text-sm font-black text-white uppercase tracking-wider">Plano del Patio</h4>
            </div>
            <div class="flex items-center gap-4 ml-auto text-[10px] font-bold">
                <div class="flex items-center gap-1.5">
                    <div class="w-3 h-3 rounded-sm bg-orange-500"></div>
                    <span class="text-slate-500">Trailer</span>
                </div>
                <div class="flex items-center gap-1.5">
                    <div class="w-3 h-3 rounded-sm bg-orange-300/70"></div>
                    <span class="text-slate-500">Van</span>
                </div>
                <div class="flex items-center gap-1.5">
                    <div class="w-3 h-3 rounded-sm bg-slate-800 border border-slate-700"></div>
                    <span class="text-slate-500">Libre</span>
                </div>
            </div>
        </div>

        {#if loading}
            <div class="h-64 flex items-center justify-center">
                <div class="w-8 h-8 border-2 border-slate-700 border-t-orange-500 rounded-full animate-spin"></div>
            </div>
        {:else}
            <!-- Zona de acceso -->
            <div class="mb-4 flex items-center gap-3">
                <div class="flex-1 h-px bg-gradient-to-r from-transparent to-orange-500/40 rounded"></div>
                <span class="text-[9px] font-black uppercase tracking-widest text-orange-500/50">Zona de Acceso Principal</span>
                <div class="flex-1 h-px bg-gradient-to-l from-transparent to-orange-500/40 rounded"></div>
            </div>

            <!-- Grid -->
            <div class="space-y-1.5">
                {#each filas as fila, fi}
                    <div class="flex items-center gap-1.5">
                        <span class="text-[9px] text-slate-700 font-mono w-4 shrink-0">{String.fromCharCode(65 + fi)}</span>
                        {#each fila as cajon}
                            <button
                                onclick={() => seleccionar(cajon)}
                                class="flex-1 aspect-square rounded-md border flex items-center justify-center relative transition-all cursor-pointer
                                    {selected?.id === cajon.id
                                        ? 'ring-2 ring-white/60 ring-offset-1 ring-offset-[#080A0E] scale-110 z-10'
                                        : 'hover:scale-105'}
                                    {cajon.ocupado
                                        ? cajon.tipo === 'trailer'
                                            ? 'bg-orange-500/80 border-orange-600/80 hover:bg-orange-500'
                                            : 'bg-orange-300/60 border-orange-400/60 hover:bg-orange-300/80'
                                        : 'bg-slate-800/40 border-slate-800 hover:border-slate-600 hover:bg-slate-800/60'}"
                            >
                                {#if cajon.ocupado}
                                    <Truck size={10} class="text-black/50 pointer-events-none" />
                                {/if}
                            </button>
                        {/each}
                    </div>
                {/each}
            </div>

            <!-- Muelles -->
            <div class="mt-5 flex items-center gap-3">
                <div class="flex-1 h-px bg-gradient-to-r from-transparent to-blue-500/30 rounded"></div>
                <span class="text-[9px] font-black uppercase tracking-widest text-blue-500/40">Muelles de Carga</span>
                <div class="flex-1 h-px bg-gradient-to-l from-transparent to-blue-500/30 rounded"></div>
            </div>
            <div class="flex gap-2 mt-2">
                {#each Array.from({ length: 5 }, (_, i) => i + 1) as m}
                    <div class="flex-1 h-9 bg-blue-500/8 border border-blue-500/15 rounded-xl flex items-center justify-center hover:bg-blue-500/15 transition-colors cursor-default">
                        <span class="text-[10px] font-black text-blue-400/70">M{m}</span>
                    </div>
                {/each}
            </div>
        {/if}
    </div>

    <!-- Nota informativa -->
    <div class="flex items-start gap-3 bg-slate-900/30 border border-slate-800/40 rounded-xl p-4">
        <Info size={15} class="text-slate-600 mt-0.5 shrink-0" />
        <p class="text-xs text-slate-600">
            Representación visual estimada basada en registros activos. Haz clic en un cajón para ver detalle.
        </p>
    </div>
</div>

<!-- Popup cajón seleccionado -->
{#if selected}
    <!-- Overlay -->
    <button
        class="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm cursor-default"
        onclick={cerrar}
        aria-label="Cerrar"
    ></button>

    <!-- Panel -->
    <div
        transition:fly={{ y: 20, duration: 180 }}
        class="fixed bottom-20 md:bottom-6 left-1/2 -translate-x-1/2 z-50 w-72 bg-[#0E1015] border rounded-2xl shadow-2xl shadow-black/60 overflow-hidden
            {selected.ocupado ? 'border-orange-500/30' : 'border-slate-700/60'}"
    >
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-slate-800/60">
            <div class="flex items-center gap-2.5">
                <div class="p-2 rounded-lg {selected.ocupado ? 'bg-orange-500/10 border border-orange-500/20' : 'bg-slate-800/60 border border-slate-700'}">
                    <Truck size={14} class="{selected.ocupado ? 'text-orange-400' : 'text-slate-600'}" />
                </div>
                <div>
                    <p class="text-xs font-black text-white tracking-wider">Cajón {selected.fila}{selected.col}</p>
                    <p class="text-[10px] text-slate-600">Fila {selected.fila} · Posición {selected.col}</p>
                </div>
            </div>
            <button onclick={cerrar} class="text-slate-600 hover:text-slate-300 transition-colors p-1 rounded-lg hover:bg-slate-800">
                <X size={14} />
            </button>
        </div>

        <!-- Body -->
        <div class="px-4 py-4 space-y-3">
            <div class="flex items-center justify-between">
                <span class="text-[10px] font-black uppercase tracking-widest text-slate-600">Estado</span>
                <span class="text-[10px] font-black px-2.5 py-1 rounded-full border
                    {selected.ocupado ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' : 'bg-green-500/10 text-green-400 border-green-500/20'}">
                    {selected.ocupado ? 'OCUPADO' : 'LIBRE'}
                </span>
            </div>
            {#if selected.ocupado}
                <div class="flex items-center justify-between">
                    <span class="text-[10px] font-black uppercase tracking-widest text-slate-600">Tipo</span>
                    <span class="text-xs font-bold text-slate-300 capitalize">{selected.tipo}</span>
                </div>
            {/if}
            <div class="flex items-center justify-between">
                <span class="text-[10px] font-black uppercase tracking-widest text-slate-600">ID</span>
                <span class="text-xs font-mono text-slate-400">C{String(selected.id).padStart(3,'0')}</span>
            </div>
        </div>
    </div>
{/if}
