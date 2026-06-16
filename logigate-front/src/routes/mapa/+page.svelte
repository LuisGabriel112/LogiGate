<script>
    import { onMount } from 'svelte';
    import { Truck, RefreshCw, Grid3x3, X, MapPin, TrendingUp, CircleParking, LogIn } from 'lucide-svelte';
    import { fly, fade } from 'svelte/transition';

    const API   = '';
    const TOTAL = 100;
    const COLS  = 10;
    const FILAS = ['A','B','C','D','E','F','G','H','I','J'];

    const ZONAS = [
        { label: 'Zona Norte',    filas: ['A','B','C'],       color: 'text-blue-400',   border: 'border-blue-500/20',  bg: 'bg-blue-500/5'   },
        { label: 'Zona Central',  filas: ['D','E','F','G'],   color: 'text-orange-400', border: 'border-orange-500/20',bg: 'bg-orange-500/5' },
        { label: 'Zona Sur',      filas: ['H','I','J'],       color: 'text-green-400',  border: 'border-green-500/20', bg: 'bg-green-500/5'  },
    ];

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
            tipo:    i < stats.en_patio ? (i % 5 === 4 ? 'van' : 'trailer') : null,
        }))
    );

    const cajonesMap = $derived(
        Object.fromEntries(cajones.map(c => [`${c.fila}${c.col}`, c]))
    );

    function getFilaCajones(fila) {
        return cajones.filter(c => c.fila === fila);
    }

    function getZonaStats(zona) {
        const cs = cajones.filter(c => zona.filas.includes(c.fila));
        const ocp = cs.filter(c => c.ocupado).length;
        return { total: cs.length, ocupados: ocp, libres: cs.length - ocp, pct: Math.round(ocp / cs.length * 100) };
    }

    async function cargarStats() {
        refresh = true;
        try {
            const res = await fetch(`${API}/api/v1/stats`);
            if (res.ok) stats = await res.json();
        } finally { loading = false; refresh = false; }
    }

    function seleccionar(cajon) { selected = selected?.id === cajon.id ? null : cajon; }
    function cerrar() { selected = null; }

    onMount(() => {
        cargarStats();
        const iv = setInterval(cargarStats, 30_000);
        const esc = (e) => { if (e.key === 'Escape') cerrar(); };
        document.addEventListener('keydown', esc);
        return () => { clearInterval(iv); document.removeEventListener('keydown', esc); };
    });

    const pctColor = (p) => p >= 85 ? 'bg-red-500' : p >= 60 ? 'bg-yellow-500' : 'bg-green-500';
    const pctText  = (p) => p >= 85 ? 'text-red-400' : p >= 60 ? 'text-yellow-400' : 'text-green-400';
    const pctBg    = (p) => p >= 85 ? 'bg-red-500/10 border-red-500/20 text-red-400' : p >= 60 ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400' : 'bg-green-500/10 border-green-500/20 text-green-400';
</script>

<div class="h-full bg-[#080A0E] text-white flex overflow-hidden">

    <!-- Panel principal -->
    <div class="flex-1 flex flex-col overflow-hidden min-w-0">

        <!-- Header -->
        <div class="shrink-0 px-5 py-4 border-b border-slate-800/60 flex items-center justify-between bg-[#0A0D12]">
            <div class="flex items-center gap-3">
                <div class="p-2 bg-orange-500/10 border border-orange-500/20 rounded-xl">
                    <MapPin size={16} class="text-orange-400" />
                </div>
                <div>
                    <h2 class="text-sm font-black text-white tracking-tight">Mapa de Patio</h2>
                    <p class="text-[10px] text-slate-600">Ocupación en tiempo real · auto-actualiza cada 30s</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <!-- Leyenda -->
                <div class="hidden md:flex items-center gap-4 text-[10px] font-bold text-slate-500">
                    <div class="flex items-center gap-1.5"><div class="w-2.5 h-2.5 rounded bg-orange-500/80"></div>Trailer</div>
                    <div class="flex items-center gap-1.5"><div class="w-2.5 h-2.5 rounded bg-orange-300/60"></div>Van</div>
                    <div class="flex items-center gap-1.5"><div class="w-2.5 h-2.5 rounded bg-slate-700 border border-slate-600"></div>Libre</div>
                </div>
                <button
                    onclick={cargarStats}
                    disabled={refresh}
                    class="flex items-center gap-1.5 bg-slate-800/60 hover:bg-slate-700/60 border border-slate-700/60 text-slate-400 text-xs font-bold px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
                >
                    <RefreshCw size={12} class={refresh ? 'animate-spin' : ''} /> Actualizar
                </button>
            </div>
        </div>

        <!-- KPIs -->
        <div class="shrink-0 grid grid-cols-4 border-b border-slate-800/60">
            {#each [
                { label: 'En Patio',    value: stats.en_patio,          color: 'text-orange-400', sub: 'vehículos activos'  },
                { label: 'Disponibles', value: TOTAL - stats.en_patio,  color: 'text-green-400',  sub: 'cajones libres'     },
                { label: 'Salidas Hoy', value: stats.salidas_hoy,       color: 'text-blue-400',   sub: 'movimientos'        },
                { label: 'Denegados',   value: stats.denegados,         color: 'text-red-400',    sub: 'accesos bloqueados' },
            ] as m}
                <div class="px-4 py-3 border-r border-slate-800/60 last:border-r-0">
                    <p class="text-[9px] font-black uppercase tracking-widest text-slate-600">{m.label}</p>
                    <p class="text-2xl font-black {m.color} mt-0.5">{loading ? '—' : m.value}</p>
                    <p class="text-[9px] text-slate-700 mt-0.5">{m.sub}</p>
                </div>
            {/each}
        </div>

        <!-- Mapa -->
        <div class="flex-1 overflow-y-auto custom-scrollbar p-4 md:p-5">

            {#if loading}
                <div class="h-64 flex items-center justify-center">
                    <div class="w-8 h-8 border-2 border-slate-700 border-t-orange-500 rounded-full animate-spin"></div>
                </div>
            {:else}

                <!-- Barra ocupación global -->
                <div class="flex items-center gap-3 mb-5">
                    <span class="text-[10px] font-black text-slate-600 uppercase tracking-wider shrink-0">Ocupación</span>
                    <div class="flex-1 bg-slate-800/50 h-1.5 rounded-full overflow-hidden">
                        <div class="h-full rounded-full transition-all duration-700 {pctColor(stats.ocupacion_pct)}"
                             style="width:{stats.ocupacion_pct}%"></div>
                    </div>
                    <span class="text-xs font-black {pctText(stats.ocupacion_pct)} shrink-0">{stats.ocupacion_pct}%</span>
                </div>

                <!-- Entrada principal -->
                <div class="flex items-center gap-2 mb-3">
                    <div class="flex-1 h-px bg-gradient-to-r from-orange-500/50 to-transparent"></div>
                    <div class="flex items-center gap-1.5 bg-orange-500/10 border border-orange-500/20 px-3 py-1 rounded-full">
                        <LogIn size={11} class="text-orange-400" />
                        <span class="text-[9px] font-black text-orange-400 uppercase tracking-widest">Acceso Principal</span>
                    </div>
                    <div class="flex-1 h-px bg-gradient-to-l from-orange-500/50 to-transparent"></div>
                </div>

                <!-- Números de columna -->
                <div class="flex gap-1 mb-1 pl-6">
                    {#each Array.from({ length: COLS }, (_, i) => i + 1) as col}
                        <div class="flex-1 text-center text-[8px] text-slate-700 font-bold">{col}</div>
                    {/each}
                </div>

                <!-- Zonas con cajones -->
                {#each ZONAS as zona}
                    {@const zs = getZonaStats(zona)}
                    <div class="mb-1">
                        <!-- Etiqueta zona -->
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-[8px] font-black uppercase tracking-widest {zona.color} opacity-60 w-5 text-right shrink-0">{zona.label.split(' ')[1][0]}</span>
                            <div class="flex-1 h-px {zona.border.replace('border-','bg-')} opacity-20"></div>
                            <span class="text-[8px] {zona.color} opacity-50 shrink-0">{zs.ocupados}/{zs.total}</span>
                        </div>

                        <!-- Filas de cajones de esta zona -->
                        {#each zona.filas as fila, fi}
                            <div class="flex items-center gap-1 mb-1">
                                <span class="text-[9px] text-slate-700 font-mono w-5 text-right shrink-0">{fila}</span>
                                {#each getFilaCajones(fila) as cajon}
                                    <button
                                        onclick={() => seleccionar(cajon)}
                                        title="Cajón {cajon.fila}{cajon.col}"
                                        class="flex-1 aspect-[1/1.3] rounded border flex items-center justify-center relative transition-all group
                                            {selected?.id === cajon.id
                                                ? 'ring-1 ring-white/60 ring-offset-1 ring-offset-[#080A0E] scale-110 z-10'
                                                : 'hover:scale-105 hover:z-10'}
                                            {cajon.ocupado
                                                ? cajon.tipo === 'van'
                                                    ? 'bg-orange-300/50 border-orange-400/50 hover:bg-orange-300/70'
                                                    : 'bg-orange-500/70 border-orange-500/70 hover:bg-orange-500/90'
                                                : 'bg-slate-800/30 border-slate-800 hover:border-slate-600 hover:bg-slate-800/50'}"
                                    >
                                        {#if cajon.ocupado}
                                            <Truck size={8} class="text-black/40 pointer-events-none" />
                                        {:else}
                                            <span class="text-[6px] text-slate-700 font-bold opacity-0 group-hover:opacity-100 transition-opacity">{cajon.col}</span>
                                        {/if}
                                    </button>
                                {/each}
                            </div>
                            <!-- Carril entre filas (excepto última de zona) -->
                            {#if fi < zona.filas.length - 1}
                                <div class="flex items-center gap-1 mb-1">
                                    <div class="w-5 shrink-0"></div>
                                    <div class="flex-1 h-2 bg-slate-900/60 border-y border-slate-800/30 rounded-sm flex items-center justify-center">
                                        <div class="flex gap-3">
                                            {#each Array.from({ length: 5 }) as _}
                                                <div class="w-3 h-px bg-yellow-500/20"></div>
                                            {/each}
                                        </div>
                                    </div>
                                </div>
                            {/if}
                        {/each}

                        <!-- Calle entre zonas -->
                        <div class="flex items-center gap-1 my-2">
                            <div class="w-5 shrink-0"></div>
                            <div class="flex-1 h-4 bg-slate-900/40 border border-slate-800/40 rounded flex items-center justify-center gap-4">
                                <div class="w-6 h-px bg-yellow-500/30"></div>
                                <div class="w-6 h-px bg-yellow-500/30"></div>
                                <div class="w-6 h-px bg-yellow-500/30"></div>
                            </div>
                        </div>
                    </div>
                {/each}

                <!-- Muelles de carga -->
                <div class="mt-2">
                    <div class="flex items-center gap-2 mb-2">
                        <div class="flex-1 h-px bg-gradient-to-r from-blue-500/40 to-transparent"></div>
                        <span class="text-[9px] font-black text-blue-400/50 uppercase tracking-widest">Muelles de Carga</span>
                        <div class="flex-1 h-px bg-gradient-to-l from-blue-500/40 to-transparent"></div>
                    </div>
                    <div class="flex gap-2 pl-6">
                        {#each Array.from({ length: 5 }, (_, i) => i + 1) as m}
                            <div class="flex-1 h-8 bg-blue-500/5 border border-blue-500/15 rounded-lg flex items-center justify-center hover:bg-blue-500/10 transition-colors cursor-default">
                                <span class="text-[9px] font-black text-blue-400/60">M{m}</span>
                            </div>
                        {/each}
                    </div>
                </div>

            {/if}
        </div>
    </div>

    <!-- Panel lateral de detalle + stats de zonas -->
    <div class="w-64 shrink-0 border-l border-slate-800/60 flex flex-col bg-[#0A0D12] overflow-y-auto custom-scrollbar">

        <!-- Stats por zona -->
        <div class="p-4 border-b border-slate-800/60">
            <p class="text-[9px] font-black uppercase tracking-widest text-slate-600 mb-3">Ocupación por Zona</p>
            <div class="space-y-3">
                {#each ZONAS as zona}
                    {@const zs = getZonaStats(zona)}
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <span class="text-[10px] font-bold {zona.color}">{zona.label}</span>
                            <span class="text-[10px] font-black text-slate-400">{zs.pct}%</span>
                        </div>
                        <div class="w-full bg-slate-800/50 h-1 rounded-full overflow-hidden">
                            <div class="h-full rounded-full transition-all duration-700 {pctColor(zs.pct)}"
                                 style="width:{zs.pct}%"></div>
                        </div>
                        <div class="flex justify-between mt-0.5">
                            <span class="text-[9px] text-slate-700">{zs.ocupados} ocup.</span>
                            <span class="text-[9px] text-slate-700">{zs.libres} libres</span>
                        </div>
                    </div>
                {/each}
            </div>
        </div>

        <!-- Detalle cajón seleccionado -->
        <div class="flex-1 p-4">
            {#if selected}
                <div in:fade={{ duration: 120 }}>
                    <div class="flex items-center justify-between mb-4">
                        <p class="text-[9px] font-black uppercase tracking-widest text-slate-600">Detalle Cajón</p>
                        <button onclick={cerrar} class="p-1 rounded text-slate-600 hover:text-white hover:bg-slate-800 transition-colors">
                            <X size={12} />
                        </button>
                    </div>

                    <!-- ID cajón grande -->
                    <div class="flex items-center gap-3 mb-4 p-3 rounded-xl {selected.ocupado ? 'bg-orange-500/8 border border-orange-500/20' : 'bg-slate-800/30 border border-slate-800'}">
                        <div class="w-10 h-10 rounded-lg {selected.ocupado ? 'bg-orange-500/20' : 'bg-slate-800'} flex items-center justify-center">
                            {#if selected.ocupado}
                                <Truck size={18} class="text-orange-400" />
                            {:else}
                                <CircleParking size={18} class="text-slate-600" />
                            {/if}
                        </div>
                        <div>
                            <p class="text-lg font-black text-white tracking-wider">{selected.fila}{selected.col}</p>
                            <p class="text-[9px] text-slate-600">ID: C{String(selected.id).padStart(3,'0')}</p>
                        </div>
                    </div>

                    <div class="space-y-2.5">
                        <div class="flex justify-between items-center">
                            <span class="text-[10px] text-slate-600 font-bold uppercase tracking-wider">Estado</span>
                            <span class="text-[10px] font-black px-2 py-0.5 rounded-full border
                                {selected.ocupado ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' : 'bg-green-500/10 text-green-400 border-green-500/20'}">
                                {selected.ocupado ? 'OCUPADO' : 'LIBRE'}
                            </span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-[10px] text-slate-600 font-bold uppercase tracking-wider">Zona</span>
                            <span class="text-[10px] font-bold text-slate-300">
                                {ZONAS.find(z => z.filas.includes(selected.fila))?.label ?? '—'}
                            </span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-[10px] text-slate-600 font-bold uppercase tracking-wider">Fila</span>
                            <span class="text-[10px] font-bold text-slate-300">{selected.fila}</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-[10px] text-slate-600 font-bold uppercase tracking-wider">Posición</span>
                            <span class="text-[10px] font-bold text-slate-300">{selected.col} de {COLS}</span>
                        </div>
                        {#if selected.ocupado}
                            <div class="flex justify-between items-center">
                                <span class="text-[10px] text-slate-600 font-bold uppercase tracking-wider">Tipo</span>
                                <span class="text-[10px] font-bold text-orange-300 capitalize">{selected.tipo}</span>
                            </div>
                        {/if}
                    </div>
                </div>
            {:else}
                <div class="flex flex-col items-center justify-center h-32 gap-2 text-slate-700">
                    <Grid3x3 size={24} />
                    <p class="text-[10px] text-center">Selecciona un cajón<br>para ver detalles</p>
                </div>
            {/if}
        </div>
    </div>
</div>

<style>
    :global(.custom-scrollbar::-webkit-scrollbar) { width: 4px; }
    :global(.custom-scrollbar::-webkit-scrollbar-track) { background: transparent; }
    :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: #1e2530; border-radius: 10px; }
</style>
