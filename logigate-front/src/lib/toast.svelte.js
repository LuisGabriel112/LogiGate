let _list = $state([]);
let _id = 0;

export const toasts = { get list() { return _list; } };

export function addToast(msg, type = 'success', ms = 3500) {
    const id = _id++;
    _list.push({ id, msg, type });
    setTimeout(() => {
        const i = _list.findIndex(t => t.id === id);
        if (i > -1) _list.splice(i, 1);
    }, ms);
}
