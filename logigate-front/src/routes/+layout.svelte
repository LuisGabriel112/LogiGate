<script>
    import "../app.css";
    import favicon from '$lib/assets/favicon.svg';
    import { page } from '$app/state'; // Svelte 5 way to access page state
    import { 
        LayoutDashboard, 
        ArrowLeftRight, 
        Map, 
        FileText, 
        Settings, 
        User, 
        Truck,
        Bell,
        LogOut
    } from 'lucide-svelte';

    let { children } = $props();

    // Determinamos si mostrar el sidebar (oculto en el login "/")
    const showSidebar = $derived(page.url.pathname !== '/');

    const menuItems = [
        { name: 'Inicio', icon: LayoutDashboard, path: '/panel-control' },
        { name: 'Entradas/Salidas', icon: ArrowLeftRight, path: '/scanner' },
        { name: 'Mapa de Patio', icon: Map, path: '/mapa' },
        { name: 'Reportes', icon: FileText, path: '/reportes' }
    ];
</script>

<svelte:head>
    <link rel="icon" href={favicon} />
    <title>LogiGate AI - Gestión Portuaria</title>
</svelte:head>

<div class="flex h-screen bg-[#0B0C10] text-slate-300 font-sans overflow-hidden">
    
    {#if showSidebar}
        <aside class="w-64 bg-[#1A1F26] border-r border-slate-800 flex flex-col shrink-0">
            <div class="p-6 flex items-center gap-3 border-b border-slate-800/50">
                <Truck class="text-orange-500" size={32} strokeWidth={2.5} />
                <div>
                    <h2 class="text-white font-black leading-none tracking-tighter text-xl">LOGIGATE <span class="text-orange-500">AI</span></h2>
                    <p class="text-[9px] text-slate-500 uppercase font-black tracking-[0.2em] mt-1">Admin Console</p>
                </div>
            </div>

            <nav class="flex-grow px-4 mt-6 space-y-1">
                {#each menuItems as item}
                    <a 
                        href={item.path} 
                        class="flex items-center gap-3 px-4 py-3 rounded-lg transition-all group {page.url.pathname === item.path ? 'bg-orange-500 text-black font-bold shadow-lg shadow-orange-500/10' : 'hover:bg-slate-800/50 text-slate-400 hover:text-white'}"
                    >
                        <svelte:component this={item.icon} size={20} />
                        <span class="text-sm tracking-wide">{item.name}</span>
                    </a>
                {/each}

                <div class="pt-8 mt-8 border-t border-slate-800/50">
                    <a href="/configuracion" class="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800/50 text-slate-500 hover:text-white transition-all">
                        <Settings size={20} />
                        <span class="text-sm">Configuración</span>
                    </a>
                </div>
            </nav>

            <div class="p-4 bg-[#12161B] border-t border-slate-800 m-4 rounded-xl flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-orange-500">
                    <User size={20} />
                </div>
                <div class="flex-grow min-w-0">
                    <p class="text-xs font-bold text-white truncate">Luis Venegas</p>
                    <p class="text-[9px] text-slate-500 uppercase font-black">Fullstack Dev</p>
                </div>
                <button class="text-slate-600 hover:text-red-500 transition-colors">
                    <LogOut size={16} />
                </button>
            </div>
        </aside>
    {/if}

    <main class="flex-grow flex flex-col min-w-0 overflow-hidden relative">
        {#if showSidebar}
            <header class="h-16 border-b border-slate-800 flex items-center justify-between px-8 bg-[#0B0C10]/50 backdrop-blur-md sticky top-0 z-10">
                <h3 class="text-sm font-black uppercase tracking-[0.2em] text-slate-400">
                    {menuItems.find(i => i.path === page.url.pathname)?.name || 'Panel de Control'}
                </h3>
                <div class="flex items-center gap-5 text-slate-500">
                    <div class="flex items-center gap-2 bg-slate-900 px-3 py-1 rounded-full border border-slate-800">
                        <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                        <span class="text-[10px] font-bold text-slate-400">PUERTA 1: ONLINE</span>
                    </div>
                    <button class="hover:text-orange-500 transition-colors relative">
                        <Bell size={20} />
                        <span class="absolute -top-1 -right-1 w-2 h-2 bg-orange-500 rounded-full border-2 border-[#0B0C10]"></span>
                    </button>
                </div>
            </header>
        {/if}

        <div class="flex-grow overflow-y-auto custom-scrollbar">
            {@render children()}
        </div>
    </main>
</div>

<style>
    /* Scrollbar con estilo industrial */
    :global(.custom-scrollbar::-webkit-scrollbar) {
        width: 6px;
    }
    :global(.custom-scrollbar::-webkit-scrollbar-track) {
        background: #0B0C10;
    }
    :global(.custom-scrollbar::-webkit-scrollbar-thumb) {
        background: #1A1F26;
        border-radius: 10px;
    }
    :global(.custom-scrollbar::-webkit-scrollbar-thumb:hover) {
        background: #FF8C00;
    }
</style>