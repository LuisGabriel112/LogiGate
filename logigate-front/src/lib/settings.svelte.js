const DEFAULTS = {
    nombre:    'Luis Venegas',
    rol:       'Administrador',
    beep:      true,
    capacidad: 100,
};

function load() {
    if (typeof localStorage === 'undefined') return { ...DEFAULTS };
    try { return { ...DEFAULTS, ...JSON.parse(localStorage.getItem('lg_settings') || '{}') }; }
    catch { return { ...DEFAULTS }; }
}

export const settings = $state(load());

export function saveSettings() {
    if (typeof localStorage !== 'undefined')
        localStorage.setItem('lg_settings', JSON.stringify({ ...settings }));
}
