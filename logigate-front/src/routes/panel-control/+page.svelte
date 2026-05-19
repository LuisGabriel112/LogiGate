<script>
    import { onMount } from 'svelte';
    import { Truck, CheckCircle2, Activity, TrendingUp, TrendingDown, ArrowUpRight, RefreshCw, AlertTriangle, Minus } from 'lucide-svelte';

    const API = typeof window !== 'undefined' ? `http://${window.location.hostname}:8000` : 'http://localhost:8000';

    let stats    = $state({ en_patio: 0, salidas_hoy: 0, denegados: 0, capacidad_total: 100, ocupacion_pct: 0 });
    let flujo    = $state([]);
    let actividad = $state([]);
    let loading  = $state(true);
    let error    = $state(null);
    let refreshing = $state(false);
    let display  = $state({ en_patio: 0, salidas_hoy: 0, denegados: 0 });
    let ultimoEscaneo = $state('');

    function animateTo(key, target) {
        const start = display[key];
        if (start === target) return;
        const steps = 24;
        let i = 0;
        const iv = setInterval(() => {
            i++;
            display[key] = Math.round(start + (target - start) * (i / steps));
            if (i >= steps) { display[key] = target; clearInterval(iv); }
        }, 18);
    }

    function updateUltimo() {
        if (!actividad.length) { ultimoEscaneo = ''; return; }
        const diff = Math.floor((Date.now() - new Date(actividad[0].created_at)) / 1000);
        if (diff < 60)   ultimoEscaneo = 'hace un momento';
        else if (diff < 3600) ultimoEscaneo = `hace ${Math.floor(diff / 60)} min`;
        else              ultimoEscaneo = `hace ${Math.floor(diff / 3600)} h`;
    }

    const estadoColor = {
        entrada:  'bg-green-500/10 text-green-400 border-green-500/20',
        salida:   'bg-blue-500/10  text-blue-400  border-blue-500/20',
        denegado: 'bg-red-500/10   text-red-400   border-red-500/20',
    };

    const fmtHora = (iso) => {
        if (!iso) return '—';
        return new Date(iso).toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
    };

    async function cargarDatos() {
        refreshing = true;
        error = null;
        try {
            const [sRes, fRes, aRes] = await Promise.all([
                fetch(`${API}/api/v1/stats`),
                fetch(`${API}/api/v1/flujo?dias=7`),
                fetch(`${API}/api/v1/actividad?limit=6`),
            ]);

            if (sRes.ok) {
                stats = await sRes.json();
                animateTo('en_patio',    stats.en_patio);
                animateTo('salidas_hoy', stats.salidas_hoy);
                animateTo('denegados',   stats.denegados);
            }
            if (fRes.ok) flujo    = await fRes.json();
            if (aRes.ok) { actividad = await aRes.json(); updateUltimo(); }
        } catch (e) {
            error = 'Sin conexión con el servidor';
        } finally {
            loading    = false;
            refreshing = false;
        }
    }

    onMount(() => {
        cargarDatos();
        const iv  = setInterval(cargarDatos, 30_000);
        const iv2 = setInterval(updateUltimo, 60_000);
        return () => { clearInterval(iv); clearInterval(iv2); };
    });

    const maxFlujo = $derived(Math.max(...flujo.map(d => d.count), 1));

    const tendencia = $derived(() => {
        if (flujo.length < 2) return null;
        const hoy  = flujo[flujo.length - 1]?.count ?? 0;
        const ayer = flujo[flujo.length - 2]?.count ?? 0;
        const diff = hoy - ayer;
        if (diff === 0 || ayer === 0) return { dir: 'igual', diff: 0, pct: 0 };
        const pct = ayer > 0 ? Math.round(Math.abs(diff / ayer) * 100) : 0;
        return { dir: diff > 0 ? 'sube' : 'baja', diff: Math.abs(diff), pct };
    });

    const disponibles = $derived(Math.max(0, stats.capacidad_total - stats.en_patio));

    const kpis = $derived([
        {
            label: 'Unidades en Patio',
            value: display.en_patio,
            sub: `de ${stats.capacidad_total} cajones`,
            pct: stats.ocupacion_pct,
            icon: Truck,
            color: 'orange',
        },
        {
            label: 'Cajones Disponibles',
            value: disponibles,
            sub: `${stats.ocupacion_pct}% ocupación`,
            pct: null,
            icon: CheckCircle2,
            color: 'green',
        },
        {
            label: 'Denegados Hoy',
            value: display.denegados,
            sub: `${display.salidas_hoy} salidas registradas`,
            pct: null,
            icon: Activity,
            color: 'red',
        },
    ]);

    const colorMap = {
        orange: { border: 'border-orange-500/20', iconBg: 'bg-orange-500/10', icon: 'text-orange-500', bar: 'bg-orange-500', glow: 'bg-orange-500/6' },
        green:  { border: 'border-green-500/15',  iconBg: 'bg-green-500/10',  icon: 'text-green-500',  bar: 'bg-green-500',  glow: 'bg-green-500/5'  },
        red:    { border: 'border-red-500/15',     iconBg: 'bg-red-500/10',    icon: 'text-red-400',    bar: 'bg-red-500',    glow: 'bg-red-500/5'    },
    };
</script>

<div class="p-6 space-y-5 h-full overflow-y-auto custom-scrollbar">

    <!-- Encabezado con refresh -->
    <div class="flex items-center justify-between">
        <div>
            <p class="text-xs text-slate-600">Actualización automática cada 30 s</p>
            {#if ultimoEscaneo}
                <p class="text-[11px] text-slate-700 mt-0.5">Último escaneo: <span class="text-orange-500/70">{ultimoEscaneo}</span></p>
            {/if}
        </div>
        <button
            onclick={cargarDatos}
            disabled={refreshing}
            class="flex items-center gap-2 bg-[#0E1015] hover:bg-slate-800/60 border border-slate-800/60 text-slate-400 text-xs font-bold px-3 py-2 rounded-xl transition-colors disabled:opacity-50"
        >
            <RefreshCw size={13} class={refreshing ? 'animate-spin' : ''} /> Actualizar
        </button>
    </div>

    <!-- Error banner -->
    {#if error}
        <div class="flex items-center gap-3 bg-red-500/5 border border-red-500/20 rounded-xl px-4 py-3">
            <AlertTriangle size={16} class="text-red-400 shrink-0" />
            <p class="text-xs text-red-400">{error} — mostrando última información disponible</p>
        </div>
    {/if}

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        {#each kpis as s}
            {@const c = colorMap[s.color]}
            {@const Icon = s.icon}
            <div class="bg-[#0E1015] border {c.border} rounded-xl p-5 relative overflow-hidden group transition-all">
                <div class="absolute top-0 right-0 w-32 h-32 {c.glow} rounded-full blur-2xl -translate-y-8 translate-x-8 pointer-events-none"></div>
                <div class="relative">
                    <div class="flex items-start justify-between mb-4">
                        <div class="p-2.5 {c.iconBg} rounded-xl border {c.border}">
                            <Icon size={20} class={c.icon} />
                        </div>
                    </div>
                    <p class="text-[10px] font-black uppercase tracking-widest text-slate-600 mb-1">{s.label}</p>
                    {#if loading}
                        <div class="h-10 w-20 bg-slate-800 rounded-lg animate-pulse mt-1"></div>
                    {:else}
                        <h3 class="text-4xl font-black text-white leading-none">{s.value}</h3>
                    {/if}
                    <p class="text-[10px] text-slate-600 mt-1.5">{s.sub}</p>
                    {#if s.pct !== null}
                        <div class="mt-4">
                            <div class="w-full bg-slate-800/60 h-1.5 rounded-full overflow-hidden">
                                <div class="{c.bar} h-full rounded-full transition-all duration-700" style="width:{s.pct}%"></div>
                            </div>
                        </div>
                    {/if}
                </div>
            </div>
        {/each}
    </div>

    <!-- Gráfico + Actividad -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">

        <!-- Gráfico de flujo -->
        <div class="lg:col-span-2 bg-[#0E1015] border border-slate-800/60 rounded-xl p-5">
            <div class="flex items-start justify-between mb-5">
                <div>
                    <h4 class="text-sm font-bold text-white">Flujo de Unidades</h4>
                    <p class="text-[10px] text-slate-600 mt-0.5">Movimientos totales por día — últimos 7 días</p>
                </div>
                {#if tendencia() && !loading}
                    {@const t = tendencia()}
                    <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[10px] font-black
                        {t.dir === 'sube'  ? 'bg-green-500/10 border-green-500/20 text-green-400' :
                         t.dir === 'baja'  ? 'bg-red-500/10   border-red-500/20   text-red-400'   :
                                             'bg-slate-800/60 border-slate-700    text-slate-500'}">
                        {#if t.dir === 'sube'}
                            <TrendingUp size={11} />
                            +{t.pct}% vs ayer
                        {:else if t.dir === 'baja'}
                            <TrendingDown size={11} />
                            -{t.pct}% vs ayer
                        {:else}
                            <Minus size={11} />
                            igual que ayer
                        {/if}
                    </div>
                {/if}
            </div>

            {#if loading}
                <div class="h-44 flex items-center justify-center">
                    <div class="w-7 h-7 border-2 border-slate-700 border-t-orange-500 rounded-full animate-spin"></div>
                </div>
            {:else if flujo.length === 0}
                <div class="h-44 flex flex-col items-center justify-center gap-2 text-slate-700">
                    <Activity size={28} />
                    <p class="text-xs">Sin movimientos registrados</p>
                </div>
            {:else}
                <div class="flex items-end gap-2 h-44">
                    {#each flujo as dia, i}
                        {@const isToday = i === flujo.length - 1}
                        {@const barH = maxFlujo > 0 ? Math.max(Math.round((dia.count / maxFlujo) * 144), dia.count > 0 ? 4 : 2) : 2}
                        <div class="flex-1 flex flex-col items-center gap-1.5">
                            <span class="text-[10px] font-bold {isToday ? 'text-orange-400' : 'text-slate-600'}">
                                {dia.count > 0 ? dia.count : ''}
                            </span>
                            <div class="w-full rounded-t-md bg-slate-800/50 relative overflow-hidden" style="height:144px">
                                <div
                                    class="absolute bottom-0 inset-x-0 rounded-t-md transition-all duration-700 {isToday ? 'bg-orange-500' : 'bg-slate-600/60 hover:bg-slate-500/70'}"
                                    style="height:{barH}px"
                                ></div>
                            </div>
                            <span class="text-[10px] {isToday ? 'text-orange-400 font-bold' : 'text-slate-700'} text-center leading-tight">
                                {dia.label}
                            </span>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>

        <!-- Actividad reciente -->
        <div class="bg-[#0E1015] border border-slate-800/60 rounded-xl p-5 flex flex-col">
            <div class="flex items-center justify-between mb-4">
                <h4 class="text-sm font-bold text-white">Actividad Reciente</h4>
                <a href="/reportes" class="text-[10px] font-bold text-orange-500 hover:text-orange-400 transition-colors flex items-center gap-1">
                    Ver todo <ArrowUpRight size={12} />
                </a>
            </div>

            {#if loading}
                <div class="space-y-2.5">
                    {#each [1,2,3,4] as _}
                        <div class="h-14 bg-slate-800/40 rounded-xl animate-pulse"></div>
                    {/each}
                </div>
            {:else if actividad.length === 0}
                <div class="flex-grow flex flex-col items-center justify-center gap-2 text-slate-700">
                    <Truck size={24} />
                    <p class="text-xs">Sin actividad reciente</p>
                </div>
            {:else}
                <div class="space-y-2 flex-grow overflow-hidden">
                    {#each actividad as a}
                        <div class="flex items-center gap-3 p-3 bg-slate-800/20 hover:bg-slate-800/40 rounded-xl border border-slate-800/40 transition-all cursor-default">
                            <div class="w-8 h-8 rounded-lg bg-slate-800/60 flex items-center justify-center shrink-0">
                                <Truck size={13} class="text-slate-500" />
                            </div>
                            <div class="flex-grow min-w-0">
                                <p class="text-xs font-black text-white tracking-wider">{a.placa}</p>
                                <p class="text-[10px] text-slate-600 truncate">{a.empresa}</p>
                            </div>
                            <div class="text-right shrink-0">
                                <span class="text-[9px] px-1.5 py-0.5 rounded-full border font-bold {estadoColor[a.estado] ?? 'bg-slate-800 text-slate-500 border-slate-700'} block mb-0.5 whitespace-nowrap">
                                    {a.estado}
                                </span>
                                <p class="text-[9px] text-slate-700">{fmtHora(a.created_at)}</p>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
    </div>

    <!-- Estado del sistema -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        {#each [
            { label: 'Motor IA',          valor: 'Operativo' },
            { label: 'Base de Datos',     valor: error ? 'Desconectada' : 'Conectada' },
            { label: 'Cámara Principal',  valor: 'En línea' },
        ] as s}
            <div class="bg-[#0E1015] border border-slate-800/60 rounded-xl px-4 py-3 flex items-center gap-3">
                <div class="w-1.5 h-1.5 rounded-full {s.valor === 'Desconectada' ? 'bg-red-500' : 'bg-green-500 animate-pulse shadow-sm shadow-green-500/50'} shrink-0"></div>
                <p class="text-[10px] font-black uppercase tracking-widest text-slate-600">{s.label}</p>
                <span class="ml-auto text-[10px] font-bold {s.valor === 'Desconectada' ? 'text-red-400' : 'text-green-400'}">{s.valor}</span>
            </div>
        {/each}
    </div>
</div>
