<script>
    import { onMount } from 'svelte';
    import { Truck, CheckCircle2, ArrowUpRight, Clock } from 'lucide-svelte';

    const API = 'https://192.168.1.68:8000';
    const token = () => localStorage.getItem('token') || '';

    let stats     = $state(null);
    let recientes = $state([]);
    let loading   = $state(true);

    const fmtHora = (iso) => {
        if (!iso) return '—';
        return new Date(iso).toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
    };

    const tiempoEnPatio = (iso) => {
        if (!iso) return '—';
        const mins = Math.round((Date.now() - new Date(iso)) / 60000);
        if (mins < 60) return `${mins}m`;
        return `${Math.floor(mins / 60)}h ${mins % 60}m`;
    };

    const estadoEstilo = {
        entrada:  'bg-green-500/10 text-green-400',
        salida:   'bg-blue-500/10 text-blue-400',
        denegado: 'bg-red-500/10 text-red-400',
    };

    onMount(async () => {
        const headers = { Authorization: `Bearer ${token()}` };
        try {
            const [sRes, rRes] = await Promise.all([
                fetch(`${API}/api/v1/stats`,     { headers }),
                fetch(`${API}/api/v1/registros?limit=5`, { headers }),
            ]);
            if (sRes.ok) stats     = await sRes.json();
            if (rRes.ok) recientes = await rRes.json();
        } finally {
            loading = false;
        }
    });

    const ocupPct   = $derived(stats?.ocupacion_pct ?? 0);
    const enPatio   = $derived(stats?.en_patio       ?? 0);
    const disponibles = $derived((stats?.capacidad_total ?? 100) - enPatio);
    const estadoPatio = $derived(
        ocupPct >= 85 ? { texto: 'Saturado',  color: 'text-red-400',    dot: 'bg-red-500'    }
        : ocupPct >= 60 ? { texto: 'Cargado',   color: 'text-yellow-400', dot: 'bg-yellow-500' }
        :                 { texto: 'Operativo', color: 'text-green-400',  dot: 'bg-green-500'  }
    );
</script>

<div class="p-4 md:p-8 space-y-5 md:space-y-8 h-full overflow-y-auto custom-scrollbar">

    <!-- Métricas principales -->
    {#if loading}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            {#each [1, 2, 3] as _}
                <div class="bg-[#1A1F26] p-6 rounded-xl border border-slate-800 h-32 animate-pulse"></div>
            {/each}
        </div>
    {:else}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">

            <!-- Unidades en patio -->
            <div class="bg-[#1A1F26] p-6 rounded-xl border border-slate-800">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <p class="text-xs font-black uppercase text-slate-500 tracking-widest">Unidades en Patio</p>
                        <h3 class="text-4xl font-bold text-white mt-1">
                            {enPatio} <span class="text-xl text-slate-500">/ {stats?.capacidad_total ?? 100}</span>
                        </h3>
                    </div>
                    <div class="bg-slate-800/50 p-3 rounded-lg"><Truck class="text-orange-500" /></div>
                </div>
                <div class="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div class="bg-orange-500 h-full transition-all duration-700" style="width: {ocupPct}%"></div>
                </div>
                <p class="text-[10px] text-orange-500 mt-2 font-bold uppercase">Ocupación actual: {ocupPct}%</p>
            </div>

            <!-- Cajones disponibles -->
            <div class="bg-[#1A1F26] p-6 rounded-xl border border-slate-800">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <p class="text-xs font-black uppercase text-slate-500 tracking-widest">Cajones Disponibles</p>
                        <h3 class="text-4xl font-bold text-white mt-1">{disponibles}</h3>
                    </div>
                    <div class="bg-slate-800/50 p-3 rounded-lg text-green-500"><CheckCircle2 /></div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-[10px] bg-slate-800 text-slate-400 px-2 py-1 rounded font-bold">
                        {stats?.salidas_hoy ?? 0} salidas hoy
                    </span>
                    <p class="text-[10px] text-slate-500 uppercase font-bold">
                        {stats?.denegados ?? 0} denegados
                    </p>
                </div>
            </div>

            <!-- Estado del patio -->
            <div class="bg-[#1A1F26] p-6 rounded-xl border border-slate-800">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <p class="text-xs font-black uppercase text-slate-500 tracking-widest">Estado del Patio</p>
                        <h3 class="text-3xl font-bold text-white mt-1 italic {estadoPatio.color}">
                            {estadoPatio.texto}
                        </h3>
                    </div>
                    <div class="bg-slate-800/50 p-3 rounded-lg text-orange-500"><ArrowUpRight /></div>
                </div>
                <div class="flex items-center gap-2">
                    <div class="w-2 h-2 rounded-full {estadoPatio.dot} animate-pulse"></div>
                    <p class="text-[10px] {estadoPatio.color} uppercase font-black tracking-widest">
                        {ocupPct}% de capacidad utilizada
                    </p>
                </div>
            </div>
        </div>
    {/if}

    <!-- Gráfico + Actividad reciente -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <!-- Gráfico de arrihos (estático decorativo) -->
        <div class="lg:col-span-2 bg-[#1A1F26] p-6 rounded-xl border border-slate-800">
            <div class="flex justify-between items-center mb-8">
                <div>
                    <h4 class="text-lg font-bold text-white">Predicción de Arribos (IA)</h4>
                    <p class="text-[10px] text-slate-500 uppercase font-bold">Volumen de Arribo: Real vs Estimado</p>
                </div>
                <select class="bg-slate-800 border-none text-xs rounded-md text-white px-3 py-2 outline-none">
                    <option>Hoy</option>
                    <option>Mañana</option>
                </select>
            </div>
            <div class="h-64 w-full bg-[#12161B] rounded-lg flex items-center justify-center border border-slate-800/50 relative overflow-hidden">
                <svg class="absolute inset-0 w-full h-full" viewBox="0 0 400 100" preserveAspectRatio="none">
                    <path d="M0 80 Q 100 20, 200 60 T 400 40" fill="none" stroke="#FF8C00" stroke-width="3" stroke-linecap="round" />
                    <path d="M0 85 Q 100 30, 200 70 T 400 50" fill="none" stroke="#475569" stroke-width="2" stroke-dasharray="5,5" />
                </svg>
                <span class="text-slate-600 text-xs font-mono uppercase tracking-widest">Datos procesados por IA</span>
            </div>
        </div>

        <!-- Actividad reciente (real) -->
        <div class="bg-[#1A1F26] p-6 rounded-xl border border-slate-800 flex flex-col">
            <div class="flex justify-between items-center mb-6">
                <h4 class="text-lg font-bold text-white">Actividad Reciente</h4>
                <a href="/reportes" class="text-orange-500 text-[10px] font-bold uppercase hover:underline">Ver todo</a>
            </div>

            {#if loading}
                <div class="space-y-3">
                    {#each [1, 2, 3] as _}
                        <div class="h-14 bg-slate-800/40 rounded-lg animate-pulse"></div>
                    {/each}
                </div>
            {:else if recientes.length === 0}
                <div class="flex-grow flex flex-col items-center justify-center text-center gap-3 text-slate-600">
                    <Clock size={28} />
                    <p class="text-xs font-bold uppercase tracking-wide">Sin registros aún</p>
                    <p class="text-[10px]">Los registros aparecerán aquí cuando el guardia autorice accesos.</p>
                </div>
            {:else}
                <div class="space-y-3 flex-grow overflow-y-auto">
                    {#each recientes as r}
                        <div class="flex items-center justify-between p-3 bg-[#12161B] rounded-lg border border-slate-800/50">
                            <div class="flex items-center gap-3">
                                <Truck size={16} class="text-slate-500 shrink-0" />
                                <div>
                                    <p class="text-xs font-bold text-white tracking-wider">{r.placa}</p>
                                    <p class="text-[9px] text-slate-500">{fmtHora(r.created_at)}</p>
                                </div>
                            </div>
                            <span class="text-[10px] px-2 py-1 rounded font-bold {estadoEstilo[r.estado] ?? 'bg-slate-800 text-slate-400'}">
                                {r.estado}
                            </span>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
    </div>
</div>
