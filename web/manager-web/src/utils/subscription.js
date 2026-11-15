// [custom minizjp] API hạn sử dụng tài khoản (dịch vụ /auth của xiaozhi-google-auth)
import store from '@/store';

function authHeader() {
  try {
    return { Authorization: 'Bearer ' + JSON.parse(store.getters.getToken).token };
  } catch (e) {
    return {};
  }
}

async function call(path, options = {}) {
  const res = await fetch('/auth' + path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...authHeader(), ...(options.headers || {}) }
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || ('HTTP ' + res.status));
  return body.data;
}

export const subscriptionApi = {
  mine: () => call('/me/subscription'),
  list: (ids) => call('/admin/subscriptions?ids=' + encodeURIComponent(ids.join(','))),
  extend: (userid, months) => call('/admin/subscriptions/extend', {
    method: 'POST', body: JSON.stringify({ userid: String(userid), months })
  })
};

export function formatSubscription(s) {
  if (!s) return { text: '…', type: 'info' };
  if (s.unlimited) return { text: 'Không giới hạn', type: 'success' };
  if (s.expired) return { text: `Hết hạn (${s.expire_at.slice(0, 10)})`, type: 'danger' };
  const days = Math.ceil(s.days_left);
  return { text: `Còn ${days} ngày (${s.expire_at.slice(0, 10)})`, type: days <= 3 ? 'warning' : 'success' };
}
