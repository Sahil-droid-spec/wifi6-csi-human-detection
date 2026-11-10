import assert from 'node:assert/strict';
import {test} from 'node:test';
import {webcrypto} from 'node:crypto';
import {commandEventId} from '../.command-test/commandEvent.js';

test('command IDs work on HTTPS/localhost and HTTP LAN with randomUUID unavailable', () => {
  const descriptor = Object.getOwnPropertyDescriptor(globalThis, 'crypto');
  try {
    Object.defineProperty(globalThis, 'crypto', {configurable:true, value:webcrypto});
    assert.match(commandEventId(), /^[\da-f-]{36}$/);
    // HTTP LAN browsers expose getRandomValues but may withhold randomUUID.
    Object.defineProperty(globalThis, 'crypto', {configurable:true, value:{getRandomValues:webcrypto.getRandomValues.bind(webcrypto)}});
    const ids = Array.from({length:1000}, () => commandEventId());
    assert.equal(new Set(ids).size, ids.length);
    for (const id of ids) assert.match(id, /^[\da-f]{32}$/);
    Object.defineProperty(globalThis, 'crypto', {configurable:true, value:undefined});
    assert.throws(commandEventId, /Update the phone browser or Orbit APK/);
  } finally {
    if (descriptor) Object.defineProperty(globalThis, 'crypto', descriptor);
    else delete globalThis.crypto;
  }
});
