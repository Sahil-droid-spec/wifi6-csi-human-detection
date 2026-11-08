import {useEffect,useRef,useState} from 'react';
import {sha256} from '@noble/hashes/sha2.js';
import {Trace} from './Showcase';
import {AudioRecorder} from './AudioRecorder';
type D=Record<string,any>;
const hex=(b:Uint8Array)=>Array.from(b,x=>x.toString(16).padStart(2,'0')).join('');
const b64=(b:Uint8Array)=>{let s='';for(const x of b)s+=String.fromCharCode(x);return btoa(s);};
async function api(path:string,options:RequestInit={}){
  const r=await fetch('/api/'+path,{...options,signal:AbortSignal.timeout(180000)}),d=await r.json();
  if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'Check the input and retry.');return d;
}
const post=(path:string,body:D)=>api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});

export function AcousticLink(){
  const [text,setText]=useState(()=>sessionStorage.getItem('orbit-link-text')||'Hello Orbit'),[file,setFile]=useState<File|null>(null),[key,setKey]=useState('');
  const [fec,setFec]=useState(false),[bitRate,setBitRate]=useState(400),[retrying,setRetrying]=useState(false);
  const [encrypted,setEncrypted]=useState(true),[consent,setConsent]=useState(false);
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[filter,setFilter]=useState('raw');
  const [tx,setTx]=useState<D|null>(null),[rx,setRx]=useState<D|null>(null),[received,setReceived]=useState<D[]>([]),[wifi,setWifi]=useState<D|null>(null);
  const [history,setHistory]=useState<D[]>([]),[soundOnly,setSoundOnly]=useState(false),[syntheticPayload,setSyntheticPayload]=useState(false);
  const [receiver,setReceiver]=useState<{file:File,mic:boolean}|null>(null);
  const reliable=useRef<AbortController|null>(null),speaker=useRef<HTMLAudioElement|null>(null);
  useEffect(()=>()=>{reliable.current?.abort();speaker.current?.pause();},[]);
  const refresh=()=>api('link').then(d=>{setReceived(d.received);setHistory(d.transmissions||[]);});
  useEffect(()=>{refresh().catch(()=>{});const timer=setInterval(()=>refresh().catch(()=>{}),3500);return()=>clearInterval(timer);},[]);
  const payload=async()=>file||new File([text],'message.txt',{type:'text/plain'});
  async function action(fn:()=>Promise<void>){setBusy(true);setError('');setNotice('');try{await fn();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  async function transmit(){const f=await payload();if(f.size>8192)throw Error('For sound use at most 8192 bytes. Send the full original over Wi-Fi, or create a small teaching image copy.');
    setTx(await post('link/transmit',{file_base64:b64(new Uint8Array(await f.arrayBuffer())),name:f.name,encrypted,passphrase:key,fec,bit_rate:bitRate,synthetic:syntheticPayload}));}
  async function sendWifi(){
    const f=await payload();if(!f.size||f.size>256*1024**2)throw Error('Choose a file from 1 byte to 256 MiB.');
    const hasher=sha256.create();for(let offset=0;offset<f.size;offset+=1048576)hasher.update(new Uint8Array(await f.slice(offset,offset+1048576).arrayBuffer()));
    const hash=hex(hasher.digest()),began=performance.now();let row=await post('exchange/files',{name:f.name,size:f.size,sha256:hash});
    const duplicate=!!row.duplicate,offset=row.offset;
    while(row.status!=='complete'&&row.offset<f.size)row=await api('exchange/files/'+row.id+'?offset='+row.offset,{method:'PUT',body:f.slice(row.offset,row.offset+1048576)});
    row=await post('exchange/files/'+row.id+'/complete',{});const ms=performance.now()-began;
    if(!duplicate)await post('exchange/files/'+row.id+'/receipt',{sha256:hash,bytes:f.size,transferred_bytes:f.size-offset,elapsed_ms:Math.max(1,ms),retries:0,direction:'upload'});
    setWifi({sha256:hash,size:f.size,ms,duplicate,id:row.id,remote:!['localhost','127.0.0.1','[::1]'].includes(location.hostname)});
    setNotice('Stored on the laptop. Open Transfer & chat on either device to receive it.');
  }
  async function decode(f:File,mic=false){setReceiver({file:f,mic});await action(async()=>{
    if(f.size>32*1024**2)throw Error('Choose a WAV smaller than 32 MiB.');
    setRx(await api('link/receive?preset='+filter+'&source='+encodeURIComponent(mic?'MICROPHONE RECORDING':'UPLOADED MODEM WAV'),{
      method:'POST',headers:{'X-Orbit-Passphrase':b64(new TextEncoder().encode(key))},body:f}));await refresh();
  });}
  async function reliableSend(){
    if(!tx)return;const cancel=new AbortController();reliable.current=cancel;setRetrying(true);
    const wait=(ms:number)=>new Promise<void>((resolve,reject)=>{if(cancel.signal.aborted){reject(Error('Stopped by user.'));return;}const timer=setTimeout(resolve,ms);cancel.signal.addEventListener('abort',()=>{clearTimeout(timer);reject(Error('Stopped by user.'));},{once:true});});
    try{let acknowledged=false;for(let attempt=0;attempt<3;attempt++){
      if(cancel.signal.aborted)break;setNotice('Playing attempt '+(attempt+1)+'; awaiting a decoded return ACK.');
      const sound=new Audio(tx.audio_url);speaker.current=sound;await sound.play();
      await wait(tx.duration_seconds*1000+500);sound.pause();
      for(let second=0;second<45;second++){await wait(1000);const state=await api('link/transmissions/'+tx.id);if(state.acknowledged){acknowledged=true;break;}}
      if(acknowledged)break;if(attempt<2)await post('link/transmissions/'+tx.id+'/retry',{});
    }setNotice(acknowledged?'Matching return ACK decoded. Hardware source remains unverified.':'Three attempts used; no matching decoded ACK. Check recording and retry. No Wi-Fi fallback was used.');}
    finally{speaker.current?.pause();reliable.current=null;setRetrying(false);}
  }
  async function teachingCopy(){
    if(!file||!file.type.startsWith('image/'))throw Error('Choose an image first.');
    const bitmap=await createImageBitmap(file);try{const c=document.createElement('canvas');c.width=64;c.height=64;c.getContext('2d')!.drawImage(bitmap,0,0,64,64);
      const blob=await new Promise<Blob|null>(resolve=>c.toBlob(resolve,'image/jpeg',.45));if(!blob)throw Error('Use a JPEG or PNG.');
      setFile(new File([blob],'teaching-copy-64px.jpg',{type:'image/jpeg'}));setTx(null);setWifi(null);setNotice('Selected a resized 64 × 64 teaching copy. The original on your device was not changed. This tiny image is unsuitable for retinal analysis.');
    }finally{bitmap.close();}
  }
  async function openLab(row:D){await action(async()=>{
    if(!consent)throw Error('Confirm permission for local processing first.');
    const response=await fetch(row.download_url);if(!response.ok)throw Error('Reconnect and receive this file again.');
    const r=await api('retina/import?consent=true&synthetic='+String(!!row.synthetic),{method:'POST',body:await response.blob()});setNotice('Original stored in Retinal Image Lab. On the laptop choose Use this input again.');location.hash='/retina';
  });}
  return <div className="ultimate-tools"><section className="panel"><span className="badge">ONE PAYLOAD · TWO CHANNELS</span><h2>AcousticLink</h2>
    <details><summary>Save files for a demonstration</summary><div className="button-row"><a className="button secondary" href="/api/downloads/Orbit-Link-Hello-Encrypted.wav">Generated encrypted Hello WAV</a><a className="button secondary" href="/api/downloads/Orbit-Link-Hello-Noisy.wav">Simulated noisy Hello WAV</a><a className="button secondary" href="/api/downloads/Orbit-Link-Image-Teaching.jpg">64 px teaching image</a></div><p>Public sample passphrase: orbit-demo-passphrase. Samples are generated audio or explicitly resized images; use your own private key for personal files.</p></details>
    <p>Send text, an image or audio to the shared laptop. Wi-Fi carries the original file. The sound experiment converts a small payload into tones and reconstructs it from received WAV samples.</p>
    <p>Encrypted mode: AES-256-GCM with a fresh salt and nonce, PBKDF2-SHA256 key derivation. Both ends need the same passphrase. The trusted laptop processes the key; local HTTP is not encrypted Wi-Fi transport.</p>
    <label>Text to transfer<textarea value={text} maxLength={1024} disabled={busy||!!file} onChange={e=>{setText(e.target.value);setTx(null);setWifi(null);}}/></label>
    <label>Or choose an image, audio or another file<input disabled={busy} type="file" onChange={e=>{setFile(e.target.files?.[0]||null);setTx(null);setWifi(null);e.target.value='';}}/></label>
    {file&&<p>{file.name} · {file.size.toLocaleString()} bytes <button className="button secondary" disabled={busy} onClick={()=>{setFile(null);setTx(null);setWifi(null);}}>Use text instead</button></p>}
    <details><summary>Record a voice file to send</summary><AudioRecorder onAudio={f=>{setFile(f);setTx(null);setWifi(null);}} maxSeconds={30}/><p>A recorded voice note is reconstructed as audio. Automatic speech transcription is not installed. PCM WAV is large; use Wi-Fi for normal voice notes.</p></details>
    <label><input type="checkbox" checked={syntheticPayload} onChange={e=>setSyntheticPayload(e.target.checked)}/> This payload contains Simulation/generated data</label><label><input type="checkbox" checked={encrypted} onChange={e=>setEncrypted(e.target.checked)}/> Encrypt the sound payload</label>
    <details><summary>Reliability settings</summary><label><input type="checkbox" checked={fec} onChange={e=>setFec(e.target.checked)}/> SECDED Hamming (8,4) payload protection · additional sound duration</label><label>Modem bit rate<select value={bitRate} onChange={e=>setBitRate(+e.target.value)}>{[100,200,400].map(v=><option key={v} value={v}>{v} bit/s</option>)}</select></label><button className="button secondary" disabled={busy} onClick={()=>action(async()=>{const d=await post('workspace/negotiate',{peer_rates:[100,200,400],robust:true,fec:true});setBitRate(d.bit_rate);setFec(d.fec);setNotice(d.protocol+'; selected robust shared profile. This is capability negotiation, not measured hardware adaptation.');})}>AgentLink · negotiate robust profile</button><button className="button secondary" disabled={busy} onClick={()=>action(async()=>{const d=await post('workspace/arq',{text,seed:42,data_loss:.2,ack_loss:.1,retries:3});setNotice(d.protocol+'; success='+d.success+', transmissions='+d.transmissions);})}>Run seeded ACK/retry simulation</button></details><label>Shared passphrase · 12–128 characters<input type="password" autoComplete="off" value={key} maxLength={128} onChange={e=>setKey(e.target.value)}/></label>
    <div className="button-row"><button className="button" disabled={busy} onClick={()=>action(sendWifi)}>Send original by Wi-Fi</button>
      <button className="button secondary" disabled={busy||(encrypted&&key.length<12)} onClick={()=>action(transmit)}>Create sound transmission</button>
      {file?.type.startsWith('image/')&&<button className="button secondary" disabled={busy} onClick={()=>action(teachingCopy)}>Create small teaching image copy</button>}</div>
    <label><input type="checkbox" checked={soundOnly} onChange={e=>setSoundOnly(e.target.checked)}/> Keep acoustic-only choice when asking for advice</label><button className="button secondary" disabled={busy} onClick={()=>action(async()=>{const f=await payload();const r=await post('workspace/transport',{bytes:f.size,encrypted,sound_only:soundOnly});setNotice(r.recommendation+'. '+r.why+' Estimated payload/envelope lower bound: '+r.estimated_payload_seconds.toFixed(1)+' seconds at 400 bit/s; actual framed duration is shown after generation. No method was switched automatically.');})}>Suggest a transport · keep manual control</button><p>Sound limit: 8192 payload bytes, 400 bit/s, 1200/2400 Hz BFSK, sequence frames + CRC32. Large photos and voice notes belong on Wi-Fi. Original file hashes are checked after reconstruction.</p>
    {error&&<p role="alert">{error}</p>}{notice&&<p role="status">{notice}</p>}{busy&&<p role="status">Processing the selected bytes and samples…</p>}
  </section>
  {wifi&&<section className="panel"><h2>Wi-Fi receipt</h2><p>{wifi.duplicate?'Already stored; no new transfer timing comparison.':`${wifi.size} bytes verified in ${(wifi.ms/1000).toFixed(3)} s (browser wall time).`}</p><p>{wifi.remote?'LAN client → laptop HTTP exchange; radio technology unverified.':'Localhost test; this is not a radio measurement.'}</p>
    <a className="button secondary" href="#/transfer">Open shared files &amp; upload graph</a>
    {tx&&<p>{wifi.sha256===tx.sha256?'Same payload SHA-256 for both paths.':'Different payloads: timings cannot be compared.'} Generated sound duration {tx.duration_seconds.toFixed(3)} s. Physical acoustic transfer has not been established by this receipt.</p>}</section>}
  {tx&&<section className="panel"><h2>Transmit audio ready</h2><details><summary>Compare saved generations of this exact payload</summary><p>Same SHA-256 only. Generated WAV duration and envelope/framing/WAV-creation time are not a physical transfer benchmark. Different rate, FEC and encryption settings are shown explicitly.</p><table><thead><tr><th>Encryption</th><th>FEC</th><th>bit/s</th><th>Frames</th><th>WAV seconds</th><th>Generation ms</th></tr></thead><tbody>{history.filter(r=>r.sha256===tx.sha256&&r.duration_seconds!==undefined).map(r=><tr key={r.id}><td>{r.encrypted?'AES-GCM':'plain'}</td><td>{r.fec?'SECDED':'none'}</td><td>{r.bit_rate}</td><td>{r.packet_count}</td><td>{r.duration_seconds.toFixed(3)}</td><td>{r.generation_ms.toFixed(1)}</td></tr>)}</tbody></table></details><button className="button secondary" disabled={busy||retrying} onClick={()=>action(reliableSend)}>Replay until decoded ACK · max 3 attempts</button>{retrying&&<button className="button secondary" onClick={()=>{reliable.current?.abort();speaker.current?.pause();}}>Stop retries</button>}<audio controls src={tx.audio_url}/><a className="button secondary" href={tx.audio_url}>Save modem WAV</a>
    <p>{tx.payload_bytes} payload bytes · {tx.packet_count} frames · {tx.duration_seconds.toFixed(3)} s of generated audio. Keep playback volume comfortable.</p>
    <p className="exchange-hash">Payload SHA-256 {tx.sha256}</p>
    <button className="button secondary" disabled={busy} onClick={()=>action(async()=>{const r=await fetch(tx.audio_url);if(!r.ok)throw Error('Generate again.');const f=new File([await r.blob()],'generated-codec-test.wav');setRx(await api('link/receive?preset='+filter,{method:'POST',headers:{'X-Orbit-Passphrase':b64(new TextEncoder().encode(key))},body:f}));await refresh();})}>Test generated WAV · codec only</button>
    <details><summary>Inspect transmit waveform and spectrum</summary><Trace values={tx.waveform} title="Transmit waveform" source={tx.source} xLabel="s" xEnd={tx.duration_seconds}/><Trace values={tx.spectrum_db_relative} title="Relative FFT power (dB)" source={tx.source} xLabel="Hz" xEnd={8000}/></details>
  </section>}
  <section className="panel"><h2>Receive sound &amp; reconstruct</h2><p>On the receiver, record first. Play the full transmit sound on the other device, stop, then decode. A generated WAV upload tests the codec; it does not prove speaker-to-microphone delivery.</p>
    <label>Receiver filter<select value={filter} disabled={busy} onChange={e=>setFilter(e.target.value)}><option value="raw">Raw · baseline</option><option value="bandpass">Butterworth band-pass · 800–2800 Hz</option><option value="lowpass">Low-pass · 1700 Hz (can harm tone 1)</option><option value="notch">50 Hz notch</option></select></label>
    <AudioRecorder maxSeconds={300} onAudio={f=>decode(f,true)}/>
    <label>Or upload the received PCM WAV · 0.1–300 s<input type="file" accept=".wav,audio/wav" disabled={busy} onChange={e=>{const f=e.target.files?.[0];if(f)decode(f);e.target.value='';}}/></label>
    {receiver&&<button className="button secondary" disabled={busy} onClick={()=>decode(receiver.file,receiver.mic)}>Re-run same receiver WAV · selected filter</button>}
    {rx&&<><h3>{rx.success?'Hash-checked content recovered':'No complete message recovered'}</h3><p>{rx.source} · {rx.reason||rx.protocol}</p>
      <p>Same-WAV comparison: raw {rx.before.crc_valid_packets} CRC-valid packets; selected filter {rx.after.crc_valid_packets}. {rx.elapsed_ms.toFixed(1)} ms computation. No ground-truth bits: BER unavailable.</p>
      <p>Filtered digital level: RMS {rx.rms_dbfs.toFixed(2)} dBFS; peak {rx.peak_dbfs.toFixed(2)} dBFS. These are not RF signal-strength measurements.</p>
      {rx.acknowledgement_received&&<p>Return ACK authenticated for transmission {rx.acknowledgement_received.id}. Sender state updated after decoding.</p>}{rx.ack&&<div><p>{rx.ack.protocol}</p><audio controls src={rx.ack.audio_url}/><a className="button secondary" href={rx.ack.audio_url}>Save return ACK WAV</a></div>}{rx.received?.text&&<blockquote>{rx.received.text}</blockquote>}
      <details><summary>Inspect received waveform and FFT</summary><Trace values={rx.waveform} title="Receiver waveform · selected filter" source={rx.source} xLabel="s" xEnd={rx.duration_seconds}/><Trace values={rx.spectrum_db_relative} title="Relative FFT power (dB)" source={rx.source} xLabel="Hz" xEnd={8000}/></details>
    </>}
  </section>
  <section className="panel"><h2>Shared reconstructed inbox</h2><p>Both screens read this inbox from the laptop. Only successfully decoded, authenticated (if encrypted), SHA-256 checked payloads appear.</p>
    <label><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/> I have permission to process this image locally.</label>
    {received.slice().reverse().map(row=><article key={row.id} className="exchange-item"><h3>{row.name}</h3><p>{row.size} bytes · {row.encrypted?'AES-GCM authenticated':'Plaintext + CRC/hash'} · {row.source}</p>
      {row.text&&<p style={{whiteSpace:'pre-wrap'}}>{row.text}</p>}
      {row.type.startsWith('image/')&&<img src={row.download_url} alt="Reconstructed received image" style={{maxWidth:'100%',maxHeight:300}}/>}
      {row.type.startsWith('audio/')&&<audio controls src={row.download_url}/>}
      <div className="button-row"><a className="button secondary" href={row.download_url}>Save reconstructed file</a><button className="button secondary" disabled={busy} onClick={()=>action(async()=>{const a=await post('workspace/import-reference',{kind:'link_received',id:row.id});location.hash='/workbench?asset='+a.id;})}>Save to shared Library</button>
        {row.type.startsWith('image/')&&<button className="button secondary" disabled={busy||!consent} onClick={()=>openLab(row)}>Save original to Retinal Image Lab</button>}
        {row.type==='audio/wav'&&<button className="button secondary" disabled={busy} onClick={()=>action(async()=>{const item=await post('audio/import-link',{received_id:row.id});location.hash='/audio?item='+item.id;})}>Save &amp; analyze in Audio Studio</button>}
        {['localhost','127.0.0.1','[::1]'].includes(location.hostname)&&<button className="button secondary" disabled={busy} onClick={()=>action(async()=>{if(!confirm('Delete this reconstructed inbox copy? Independent Library copies remain.'))return;await api('link/received/'+row.id,{method:'DELETE'});await refresh();})}>Delete inbox copy…</button>}</div>
      <p className="exchange-hash">SHA-256 {row.sha256}</p></article>)}
    {!received.length&&<p>Receive a transmission to start. Try “Hello Orbit” first.</p>}
  </section></div>;
}
