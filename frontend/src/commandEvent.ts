/** Non-secret command deduplication ID; works on paired HTTP LAN pages too. */
export function commandEventId(): string {
  const source = globalThis.crypto;
  if (typeof source?.randomUUID === 'function') return source.randomUUID();
  if (typeof source?.getRandomValues === 'function') {
    const bytes = source.getRandomValues(new Uint8Array(16));
    return Array.from(bytes, value => value.toString(16).padStart(2, '0')).join('');
  }
  throw new Error('This browser cannot create a command ID. Update the phone browser or Orbit APK, then reconnect.');
}
