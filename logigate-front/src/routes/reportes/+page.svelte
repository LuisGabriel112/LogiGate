<script>
    import { onMount } from 'svelte';
    import { TrendingUp, Clock, Truck, Download, Search, AlertTriangle, ChevronLeft, ChevronRight } from 'lucide-svelte';

    const API = 'https://192.168.1.68:8000';

    let registros  = $state([]);
    let loading    = $state(true);
    let busqueda   = $state('');
    let filtroEstado = $state('Todos');
    let pagina     = $state(1);
    const POR_PAG  = 10;

    const token = () => localStorage.getItem('token') || '';

    const ESTADOS = ['Todos', 'entrada', 'salida', 'denegado'];

    const estadoLabel = { entrada: 'Entrada', salida: 'Salida', denegado: 'Denegado' };
    const estadoClass = {
        entrada:  'bg-green-500/10 text-green-400 border-green-500/30',
        salida:   'bg-blue-500/10  text-blue-400  border-blue-500/30',
        denegado: 'bg-red-500/10   text-red-400   border-red-500/30',
    };

    const fmtFecha = (iso) => {
        if (!iso) return '—';
        const d = new Date(iso);
        return d.toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' });
    };
    const fmtHora = (iso) => {
        if (!iso) return '—';
        return new Date(iso).toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
    };

    // ── Carga de datos ────────────────────────────────────────
    onMount(async () => {
        try {
            const res = await fetch(`${API}/api/v1/registros?limit=200`, {
                headers: { Authorization: `Bearer ${token()}` },
            });
            if (res.ok) registros = await res.json();
        } finally {
            loading = false;
        }
    });

    // ── Métricas calculadas ───────────────────────────────────
    const totalEntradas   = $derived(registros.filter(r => r.estado === 'entrada').length);
    const totalSalidas    = $derived(registros.filter(r => r.estado === 'salida').length);
    const enPatio         = $derived(Math.max(0, totalEntradas - totalSalidas));
    const tasaAutorizacion = $derived(
        registros.length > 0
            ? Math.round(((registros.length - registros.filter(r => r.estado === 'denegado').length) / registros.length) * 100)
            : 0
    );

    // Confianza promedio
    const confProm = $derived(() => {
        const vals = registros.filter(r => r.confianza != null).map(r => r.confianza);
        return vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0;
    });

    // Flujo por día (últimos 7 días para el gráfico)
    const flujoDias = $derived(() => {
        const hoy = new Date();
        const dias = Array.from({ length: 7 }, (_, i) => {
            const d = new Date(hoy);
            d.setDate(hoy.getDate() - (6 - i));
            return {
                label: d.toLocaleDateString('es-MX', { weekday: 'short', day: 'numeric' }),
                fecha: d.toDateString(),
                count: 0,
            };
        });
        registros.forEach(r => {
            const f = new Date(r.created_at).toDateString();
            const d = dias.find(d => d.fecha === f);
            if (d) d.count++;
        });
        return dias;
    });

    const maxFlujo = $derived(Math.max(...flujoDias().map(d => d.count), 1));

    // ── Filtrado y paginación ─────────────────────────────────
    const filtrados = $derived(
        registros.filter(r => {
            const matchBusq = !busqueda || r.placa?.toLowerCase().includes(busqueda.toLowerCase()) || r.empresa?.toLowerCase().includes(busqueda.toLowerCase());
            const matchEst  = filtroEstado === 'Todos' || r.estado === filtroEstado;
            return matchBusq && matchEst;
        })
    );

    const totalPaginas = $derived(Math.max(1, Math.ceil(filtrados.length / POR_PAG)));
    const paginados    = $derived(filtrados.slice((pagina - 1) * POR_PAG, pagina * POR_PAG));

    function cambiarFiltro(estado) {
        filtroEstado = estado;
        pagina = 1;
    }
</script>

<div class="p-4 md:p-8 space-y-5 md:space-y-8 overflow-y-auto custom-scrollbar h-full">

    <!-- Encabezado -->
    <div class="flex flex-col sm:flex-row sm:items-start gap-3 sm:justify-between">
        <div>
            <h2 class="text-xl md:text-2xl font-black text-white tracking-tight">Reportes Históricos</h2>
            <p class="text-xs text-slate-500 mt-1">Análisis de rendimiento operativo.</p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
            <button class="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-bold px-3 py-2 rounded-lg transition-colors">
                <Download size={13} /> PDF
            </button>
            <button class="flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-black text-xs font-black px-3 py-2 rounded-lg transition-colors">
                <Download size={13} /> Excel
            </button>
        </div>
    </div>

    <!-- Métricas -->
    {#if loading}
        <div class="grid grid-cols-3 gap-6">
            {#each [1, 2, 3] as _}
                <div class="bg-[#1A1F26] rounded-xl border border-slate-800 p-6 h-28 animate-pulse"></div>
            {/each}
        </div>
    {:else}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="bg-[#1A1F26] rounded-xl border border-slate-800 p-6">
                <div class="flex items-center gap-2 mb-3">
                    <Clock size={16} class="text-orange-500" />
                    <p class="text-[10px] font-black uppercase tracking-widest text-slate-500">Unidades en Patio</p>
                </div>
                <h3 class="text-4xl font-black text-white">{enPatio}</h3>
                <p class="text-[10px] text-slate-500 mt-2">{totalEntradas} entradas · {totalSalidas} salidas registradas</p>
            </div>

            <div class="bg-[#1A1F26] rounded-xl border border-slate-800 p-6">
                <div class="flex items-center gap-2 mb-3">
                    <TrendingUp size={16} class="text-green-500" />
                    <p class="text-[10px] font-black uppercase tracking-widest text-slate-500">Tasa de Autorización</p>
                </div>
                <h3 class="text-4xl font-black text-white">{tasaAutorizacion}<span class="text-2xl text-slate-500">%</span></h3>
                <div class="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
                    <div class="bg-green-500 h-full transition-all" style="width: {tasaAutorizacion}%"></div>
                </div>
            </div>

            <div class="bg-[#1A1F26] rounded-xl border border-slate-800 p-6">
                <div class="flex items-center gap-2 mb-3">
                    <Truck size={16} class="text-blue-500" />
                    <p class="text-[10px] font-black uppercase tracking-widest text-slate-500">Total Movimientos</p>
                </div>
                <h3 class="text-4xl font-black text-white">{registros.length}</h3>
                <p class="text-[10px] text-slate-500 mt-2">Confianza IA promedio: {confProm()}%</p>
            </div>
        </div>
    {/if}

    <!-- Gráfico de flujo por día -->
    <div class="bg-[#1A1F26] rounded-xl border border-slate-800 p-6">
        <div class="flex items-center justify-between mb-6">
            <div>
                <h4 class="text-base font-black text-white">Flujo de Unidades por Día</h4>
                <p class="text-[10px] text-slate-500 mt-0.5">Últimos 7 días</p>
            </div>
        </div>
        <div class="flex items-end gap-3 h-40">
            {#each flujoDias() as dia}
                <div class="flex-1 flex flex-col items-center gap-2">
                    <span class="text-[10px] font-bold text-slate-400">{dia.count > 0 ? dia.count : ''}</span>
                    <div class="w-full rounded-t-md bg-slate-800 relative overflow-hidden" style="height: 96px;">
                        <div
                            class="absolute bottom-0 inset-x-0 bg-orange-500 rounded-t-md transition-all duration-700"
                            style="height: {dia.count > 0 ? Math.round((dia.count / maxFlujo) * 96) : 2}px;"
                        ></div>
                    </div>
                    <span class="text-[9px] text-slate-500 capitalize text-center">{dia.label}</span>
                </div>
            {/each}
        </div>
    </div>

    <!-- Tabla de operaciones -->
    <div class="bg-[#1A1F26] rounded-xl border border-slate-800">
        <div class="px-4 md:px-6 py-4 border-b border-slate-800 flex flex-col gap-3">
            <div>
                <h4 class="text-base font-black text-white">Detalle de Operaciones</h4>
                <p class="text-[10px] text-slate-500 mt-0.5">{filtrados.length} registros encontrados</p>
            </div>
            <div class="flex flex-col sm:flex-row gap-2">
                <!-- Búsqueda -->
                <div class="relative flex-1">
                    <Search size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input bind:value={busqueda} placeholder="Buscar placa o empresa..."
                        class="w-full bg-[#0D1117] border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-orange-500 transition-colors" />
                </div>
                <!-- Filtro estado -->
                <div class="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 overflow-x-auto">
                    {#each ESTADOS as est}
                        <button onclick={() => cambiarFiltro(est)}
                            class="shrink-0 px-2.5 py-1.5 rounded-md text-[10px] font-black uppercase transition-all {filtroEstado === est ? 'bg-orange-500 text-black' : 'text-slate-500 hover:text-white'}">
                            {est === 'Todos' ? 'Todos' : estadoLabel[est]}
                        </button>
                    {/each}
                </div>
            </div>
        </div>

        {#if loading}
            <div class="p-12 flex items-center justify-center">
                <div class="w-8 h-8 border-4 border-slate-700 border-t-orange-500 rounded-full animate-spin"></div>
            </div>
        {:else if paginados.length === 0}
            <div class="p-12 text-center">
                <AlertTriangle size={32} class="text-slate-700 mx-auto mb-3" />
                <p class="text-slate-500 text-sm">No se encontraron registros.</p>
            </div>
        {:else}
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b border-slate-800 text-[10px] uppercase tracking-widest text-slate-500 font-black">
                            <th class="px-6 py-3 text-left">Fecha</th>
                            <th class="px-4 py-3 text-left">Placa</th>
                            <th class="px-4 py-3 text-left">Empresa</th>
                            <th class="px-4 py-3 text-left">Tipo</th>
                            <th class="px-4 py-3 text-left">Entrada</th>
                            <th class="px-4 py-3 text-left">Estado</th>
                            <th class="px-4 py-3 text-left">IA %</th>
                            <th class="px-4 py-3 text-left">Autorizado por</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800/50">
                        {#each paginados as r}
                            <tr class="hover:bg-slate-800/20 transition-colors">
                                <td class="px-6 py-3.5 text-slate-400 whitespace-nowrap">{fmtFecha(r.created_at)}</td>
                                <td class="px-4 py-3.5">
                                    <span class="font-black text-white tracking-wider bg-slate-800 px-2 py-1 rounded text-xs">{r.placa}</span>
                                </td>
                                <td class="px-4 py-3.5 text-slate-300">{r.empresa || '—'}</td>
                                <td class="px-4 py-3.5 text-slate-400">{r.tipo_unidad || '—'}</td>
                                <td class="px-4 py-3.5 text-slate-400 whitespace-nowrap">{fmtHora(r.created_at)}</td>
                                <td class="px-4 py-3.5">
                                    <span class="text-[10px] font-black px-2.5 py-1 rounded-full border {estadoClass[r.estado] || 'bg-slate-800 text-slate-500 border-slate-700'}">
                                        {estadoLabel[r.estado] ?? r.estado}
                                    </span>
                                </td>
                                <td class="px-4 py-3.5 text-slate-400">{r.confianza != null ? r.confianza + '%' : '—'}</td>
                                <td class="px-4 py-3.5 text-slate-400">{r.autorizado_por || '—'}</td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>

            <!-- Paginación -->
            <div class="px-6 py-4 border-t border-slate-800 flex items-center justify-between">
                <p class="text-[11px] text-slate-500">
                    Mostrando {(pagina - 1) * POR_PAG + 1}–{Math.min(pagina * POR_PAG, filtrados.length)} de {filtrados.length} resultados
                </p>
                <div class="flex items-center gap-2">
                    <button
                        onclick={() => pagina--}
                        disabled={pagina === 1}
                        class="w-8 h-8 rounded-lg border border-slate-700 flex items-center justify-center text-slate-400 hover:border-orange-500 hover:text-orange-500 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                        <ChevronLeft size={16} />
                    </button>
                    {#each Array.from({ length: totalPaginas }, (_, i) => i + 1) as p}
                        <button
                            onclick={() => pagina = p}
                            class="w-8 h-8 rounded-lg text-xs font-bold transition-colors {pagina === p ? 'bg-orange-500 text-black' : 'border border-slate-700 text-slate-400 hover:border-orange-500'}"
                        >
                            {p}
                        </button>
                    {/each}
                    <button
                        onclick={() => pagina++}
                        disabled={pagina === totalPaginas}
                        class="w-8 h-8 rounded-lg border border-slate-700 flex items-center justify-center text-slate-400 hover:border-orange-500 hover:text-orange-500 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                        <ChevronRight size={16} />
                    </button>
                </div>
            </div>
        {/if}
    </div>
</div>
