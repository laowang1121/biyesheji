// 通用API请求
const api = (url, options = {}) => {
    const opts = {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options
    };
    if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData)) {
        opts.body = JSON.stringify(opts.body);
    }
    return fetch(url, opts).then(r => r.json());
};

// 显示消息
function showMsg(el, text, isErr = false) {
    if (!el) return;
    el.textContent = text;
    el.className = 'msg ' + (isErr ? 'err' : 'ok');
    el.classList.remove('hidden');
    setTimeout(() => el.classList.add('hidden'), 3000);
}
