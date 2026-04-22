<script>
    import "../app.css";
    import favicon from '$lib/assets/favicon.svg';
    import { page } from '$app/state';
    import { onMount } from 'svelte';
    import {
        LayoutDashboard,
        ArrowLeftRight,
        Map,
        FileText,
        Settings,
        Truck,
        Bell,
        LogOut,
        ChevronRight,
        CheckCheck,
        ShieldAlert,
        LogIn,
        LogOut as LogOutIcon,
        X,
    } from 'lucide-svelte';

    let { children } = $props();

    const API = typeof window !== 'undefined' ? `http://${window.location.hostname}:8000` : 'http://localhost:8000';

    const showSidebar = $derived(page.url.pathname !== '/');

    const menuItems = [
        { name: 'Panel de Control',  icon: LayoutDashboard, path: '/panel-control' },
        { name: 'Entradas / Salidas', icon: ArrowLeftRight,  path: '/scanner'       },
        { name: 'Mapa de Patio',     icon: Map,             path: '/mapa'          },
        { name: 'Reportes',          icon: FileText,        path: '/reportes'      },
    ];

    const pageTitle = $derived(
        menuItems.find(i => i.path === page.url.pathname)?.name ?? 'Panel de Control'
    );

    // ── Notificaciones ────────────────────────────────────────────────────────
    let bellOpen       = $state(false);
    let notifs         = $state([]);
    let lastSeenId     = $state(0);   // último id visto (persiste en localStorage)
    let unread         = $derived(notifs.filter(n => n.id > lastSeenId).length);

    const notifIcon = { entrada: LogIn, salida: LogOutIcon, denegado: ShieldAlert };
    const notifColor = {
        entrada:  { text: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' },
        salida:   { text: 'text-blue-400',  bg: 'bg-blue-500/10',  border: 'border-blue-500/20'  },
        denegado: { text: 'text-red-400',   bg: 'bg-red-500/10',   border: 'border-red-500/20'   },
    };
    const notifLabel  = { entrada: 'Entrada registrada', salida: 'Salida registrada', denegado: 'Acceso denegado' };

    const fmtRelativo = (iso) => {
        if (!iso) return '';
        const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
        if (diff < 60)  return 'Hace un momento';
        if (diff < 3600) return `Hace ${Math.floor(diff / 60)} min`;
        if (diff < 86400) return `Hace ${Math.floor(diff / 3600)} h`;
        return new Date(iso).toLocaleDateString('es-MX', { day: '2-digit', month: 'short' });
    };

    async function fetchNotifs() {
        try {
            const res = await fetch(`${API}/api/v1/actividad?limit=20`);
            if (res.ok) notifs = await res.json();
        } catch (_) {}
    }

    function openBell() {
        bellOpen = !bellOpen;
        if (bellOpen && notifs.length > 0) {
            // Marcar como leídas
            lastSeenId = notifs[0].id;
            if (typeof localStorage !== 'undefined')
                localStorage.setItem('lg_last_seen', String(lastSeenId));
        }
    }

    function closeOnOutside(e) {
        if (bellOpen && !e.target.closest('#bell-panel') && !e.target.closest('#bell-btn')) {
            bellOpen = false;
        }
    }

    onMount(() => {
        if (typeof localStorage !== 'undefined') {
            lastSeenId = parseInt(localStorage.getItem('lg_last_seen') || '0');
        }
        fetchNotifs();
        const iv = setInterval(fetchNotifs, 30_000);
        document.addEventListener('click', closeOnOutside);
        return () => {
            clearInterval(iv);
            document.removeEventListener('click', closeOnOutside);
        };
    });
</script>

<svelte:head>
    <link rel="icon" href={favicon} />
    <title>LogiGate AI — Gestión Portuaria</title>
</svelte:head>

<div class="flex h-screen bg-[#080A0E] text-slate-300 font-sans overflow-hidden">

    {#if showSidebar}
        <aside class="w-60 flex flex-col shrink-0 border-r border-slate-800/60 bg-[#0E1015]">

            <!-- Logo -->
            <div class="px-5 py-5 flex items-center gap-3 border-b border-slate-800/60">
                <div class="p-1.5 bg-orange-500/10 rounded-lg border border-orange-500/20 shrink-0">
                    <Truck class="text-orange-500" size={20} strokeWidth={2} />
                </div>
                <div>
                    <h2 class="text-white font-black leading-none tracking-tight text-base">
                        Logi<span class="text-orange-500">Gate</span>
                    </h2>
                    <p class="text-[9px] text-slate-600 uppercase font-bold tracking-[0.2em] mt-0.5">Admin Console</p>
                </div>
            </div>

            <!-- Nav -->
            <nav class="flex-grow px-3 mt-4 space-y-0.5">
                <p class="text-[9px] font-black uppercase tracking-[0.25em] text-slate-700 px-3 mb-2">Navegación</p>

                {#each menuItems as item}
                    {@const active = page.url.pathname === item.path}
                    {@const Icon = item.icon}
                    <a
                        href={item.path}
                        class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all group relative {active
                            ? 'text-orange-400 bg-orange-500/8'
                            : 'text-slate-500 hover:text-slate-200 hover:bg-slate-800/40'}"
                    >
                        {#if active}
                            <div class="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-orange-500 rounded-r-full"></div>
                        {/if}
                        <Icon size={18} class={active ? 'text-orange-500' : 'text-slate-600 group-hover:text-slate-400 transition-colors'} />
                        <span class="text-[13px] font-semibold flex-grow">{item.name}</span>
                        {#if active}
                            <ChevronRight size={14} class="text-orange-500/50" />
                        {/if}
                    </a>
                {/each}

                <div class="pt-4 mt-4 border-t border-slate-800/50">
                    <p class="text-[9px] font-black uppercase tracking-[0.25em] text-slate-700 px-3 mb-2">Sistema</p>
                    <a
                        href="/configuracion"
                        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 hover:text-slate-200 hover:bg-slate-800/40 transition-all group"
                    >
                        <Settings size={18} class="group-hover:rotate-45 transition-transform duration-300" />
                        <span class="text-[13px] font-semibold">Configuración</span>
                    </a>
                </div>
            </nav>

            <!-- User card -->
            <div class="p-3 border-t border-slate-800/60">
                <div class="flex items-center gap-2.5 p-2.5 rounded-xl bg-slate-800/30 hover:bg-slate-800/50 transition-colors cursor-pointer group">
                    <div class="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center text-white font-black text-sm shrink-0">
                        L
                    </div>
                    <div class="flex-grow min-w-0">
                        <p class="text-xs font-bold text-slate-200 truncate">Luis Venegas</p>
                        <p class="text-[10px] text-slate-600">Administrador</p>
                    </div>
                    <button class="text-slate-700 hover:text-red-400 transition-colors p-1 rounded-lg hover:bg-red-500/10">
                        <LogOut size={15} />
                    </button>
                </div>
            </div>
        </aside>
    {/if}

    <main class="flex-grow flex flex-col min-w-0 overflow-hidden relative">
        {#if showSidebar}
            <header class="h-14 border-b border-slate-800/60 flex items-center justify-between px-6 bg-[#080A0E]/80 backdrop-blur-md sticky top-0 z-10">
                <h3 class="text-sm font-bold text-slate-300">{pageTitle}</h3>

                <div class="flex items-center gap-3">
                    <!-- Estado puerta -->
                    <div class="flex items-center gap-2 bg-slate-900/80 px-3 py-1.5 rounded-full border border-slate-800">
                        <div class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse shadow-sm shadow-green-500"></div>
                        <span class="text-[10px] font-bold text-slate-500 tracking-wider">PUERTA 1 · EN LÍNEA</span>
                    </div>

                    <!-- Campana -->
                    <div class="relative">
                        <button
                            id="bell-btn"
                            onclick={openBell}
                            class="relative w-8 h-8 flex items-center justify-center rounded-lg border transition-all
                                {bellOpen
                                    ? 'border-orange-500/40 bg-orange-500/10 text-orange-400'
                                    : 'border-slate-800 bg-slate-900/50 text-slate-500 hover:text-orange-400 hover:border-orange-500/30'}"
                        >
                            <Bell size={16} />
                            {#if unread > 0}
                                <span class="absolute -top-1 -right-1 min-w-[16px] h-4 px-0.5 bg-orange-500 rounded-full border border-[#080A0E] flex items-center justify-center text-[9px] font-black text-black">
                                    {unread > 9 ? '9+' : unread}
                                </span>
                            {/if}
                        </button>

                        <!-- Panel de notificaciones -->
                        {#if bellOpen}
                            <div
                                id="bell-panel"
                                class="absolute right-0 top-11 w-80 bg-[#0E1015] border border-slate-800/80 rounded-2xl shadow-2xl shadow-black/60 overflow-hidden z-50"
                            >
                                <!-- Header del panel -->
                                <div class="flex items-center justify-between px-4 py-3 border-b border-slate-800/60">
                                    <div class="flex items-center gap-2">
                                        <Bell size={14} class="text-orange-500" />
                                        <span class="text-xs font-black text-white">Notificaciones</span>
                                        {#if unread > 0}
                                            <span class="text-[9px] font-black bg-orange-500 text-black px-1.5 py-0.5 rounded-full">{unread} nuevas</span>
                                        {/if}
                                    </div>
                                    <button
                                        onclick={() => bellOpen = false}
                                        class="text-slate-600 hover:text-slate-300 transition-colors p-1 rounded-lg hover:bg-slate-800"
                                    >
                                        <X size={14} />
                                    </button>
                                </div>

                                <!-- Lista -->
                                <div class="max-h-80 overflow-y-auto custom-scrollbar">
                                    {#if notifs.length === 0}
                                        <div class="flex flex-col items-center justify-center gap-2 py-10 text-slate-700">
                                            <CheckCheck size={24} />
                                            <p class="text-xs">Sin notificaciones</p>
                                        </div>
                                    {:else}
                                        {#each notifs as n}
                                            {@const isNew = n.id > lastSeenId}
                                            {@const c = notifColor[n.estado] ?? notifColor.entrada}
                                            {@const NIcon = notifIcon[n.estado] ?? Bell}
                                            <div class="flex items-start gap-3 px-4 py-3 border-b border-slate-800/30 hover:bg-slate-800/20 transition-colors {isNew ? 'bg-orange-500/3' : ''}">
                                                <!-- Indicador de nuevo -->
                                                <div class="mt-1 shrink-0">
                                                    {#if isNew}
                                                        <div class="w-1.5 h-1.5 rounded-full bg-orange-500"></div>
                                                    {:else}
                                                        <div class="w-1.5 h-1.5 rounded-full bg-transparent"></div>
                                                    {/if}
                                                </div>

                                                <!-- Ícono del tipo -->
                                                <div class="p-1.5 {c.bg} rounded-lg border {c.border} shrink-0 mt-0.5">
                                                    <NIcon size={12} class={c.text} />
                                                </div>

                                                <!-- Texto -->
                                                <div class="flex-grow min-w-0">
                                                    <p class="text-xs font-bold text-slate-200 leading-tight">
                                                        {notifLabel[n.estado] ?? n.estado}
                                                    </p>
                                                    <p class="text-[11px] text-slate-500 mt-0.5 truncate">
                                                        Placa <span class="font-black text-slate-300 tracking-wider">{n.placa}</span>
                                                        {#if n.empresa && n.empresa !== '—'}
                                                          · {n.empresa}
                                                        {/if}
                                                    </p>
                                                    <p class="text-[10px] text-slate-700 mt-1">{fmtRelativo(n.created_at)}</p>
                                                </div>
                                            </div>
                                        {/each}
                                    {/if}
                                </div>

                                <!-- Footer -->
                                <div class="px-4 py-2.5 border-t border-slate-800/60 flex items-center justify-between">
                                    <span class="text-[10px] text-slate-700">{notifs.length} registros</span>
                                    <a
                                        href="/reportes"
                                        onclick={() => bellOpen = false}
                                        class="text-[10px] font-bold text-orange-500 hover:text-orange-400 transition-colors"
                                    >
                                        Ver historial completo →
                                    </a>
                                </div>
                            </div>
                        {/if}
                    </div>
                </div>
            </header>
        {/if}

        <div class="flex-grow overflow-y-auto custom-scrollbar">
            {@render children()}
        </div>
    </main>
</div>

<style>
    :global(.custom-scrollbar::-webkit-scrollbar) { width: 5px; }
    :global(.custom-scrollbar::-webkit-scrollbar-track) { background: #080A0E; }
    :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: #1e2530; border-radius: 10px; }
    :global(.custom-scrollbar::-webkit-scrollbar-thumb:hover) { background: #FF8C00; }
</style>
