const token = location.hash.slice(1);
const app = document.getElementById('app');
const browser = document.getElementById('browser');
const message = document.getElementById('message');

if (/^[a-zA-Z0-9_-]{43}$/.test(token)) {
  app.href = 'orbit://connect?url=' + encodeURIComponent(location.origin + '/#/pair?token=' + token);
  app.hidden = false;
  browser.hidden = false;
  browser.addEventListener('click', async () => {
    browser.disabled = true;
    app.hidden = true;
    message.textContent = 'Connecting…';
    try {
      const response = await fetch('/api/pair/claim', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({token}),
        signal: AbortSignal.timeout(8000),
      });
      if (!response.ok) {
        message.textContent = 'Create a fresh QR on the laptop, then scan again.';
        return;
      }
      location.replace('/#/transfer');
    } catch {
      message.textContent = 'Keep the laptop server open. Reconnect to the same Wi-Fi, then create a fresh QR.';
    }
  });
} else {
  message.textContent = 'Open Connect on the laptop, create a fresh QR and scan it.';
}
