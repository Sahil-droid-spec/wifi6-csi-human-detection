import {useRef,useState} from 'react';
import {sha256} from '@noble/hashes/sha2.js';
import {TransferTimeline} from './TransferTimeline';

type D=Record<string,any>;
type Command=(action:string,payload?:D)=>Promise<boolean>;
const hex=(bytes:Uint8Array)=>Array.from(bytes,value=>value.toString(16).padStart(2,'0')).join('');
async function request(path:string,options:RequestInit={}){
 const response=await fetch('/api/'+path,{...options,signal:AbortSignal.timeout(30000)});
 if(!response.ok){let detail;try{detail=(await response.json()).detail;}catch{}throw Error(typeof detail==='string'?detail:'Reconnect in Connect, then retry this transfer.');}
 return response;
}
async function post(path:string,body:D){return (await request(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json();}

export function CommandBridge({shared,command,onSignals}:{shared:D|null;command:Command;onSignals:()=>void}){
 const nativeRole=/Android|iPhone/i.test(navigator.userAgent)?'phone':'laptop';
 const [role,setRole]=useState(nativeRole),[sample,setSample]=useState('walking'),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[error,setError]=useState(''),[progress,setProgress]=useState<D|null>(null);
 const picker=useRef<HTMLInputElement>(null);
 const direction=shared?.transfer_route||'phone_to_laptop',sender=direction==='phone_to_laptop'?'phone':'laptop',receiver=sender==='phone'?'laptop':'phone',handoff=shared?.handoff;
 const owner=!!shared?.device_id&&shared.controller===shared.device_id;
 async function control(){if(owner)return true;return command('claim',{label:role==='phone'?'Phone controller':'Laptop controller'});}
 async function run(job:()=>Promise<void>){setBusy(true);setError('');setMessage('');try{await job();}catch(e:any){setError(e.message);}finally{setBusy(false);}}
 async function send(file:File){
  if(file.size>32*1024**2)throw Error('Choose a signal dataset under 32 MiB for the shared room. Larger files can use Transfer below.');
  const hash=sha256.create();setProgress({bytes:0,total:file.size,label:'Hashing original file'});
  for(let offset=0;offset<file.size;offset+=1048576)hash.update(new Uint8Array(await file.slice(offset,offset+1048576).arrayBuffer()));
  const digest=hex(hash.digest()),start=performance.now();
  let row=await post('exchange/files',{name:file.name,size:file.size,sha256:digest});
  const duplicate=!!row.duplicate,initial=row.offset;
  if(!await command('handoff',{file_id:row.id,direction}))throw Error('The file is staged. Reconnect and send again to share its transfer graph.');
  while(row.status!=='complete'&&row.offset<file.size){
   row=await (await request('exchange/files/'+row.id+'?offset='+row.offset,{method:'PUT',body:file.slice(row.offset,row.offset+1048576)})).json();
   setProgress({bytes:row.offset,total:file.size,label:'Server accepted bytes'});
  }
  row=await post('exchange/files/'+row.id+'/complete',{});
  if(!duplicate)await post('exchange/files/'+row.id+'/receipt',{sha256:digest,bytes:file.size,transferred_bytes:file.size-initial,elapsed_ms:Math.max(1,performance.now()-start),retries:0,direction:'upload'});
  await command('handoff',{file_id:row.id,direction});
  setProgress({bytes:file.size,total:file.size,label:duplicate?'Already stored · duplicate hash matched; no new upload timing':'Stored on laptop · SHA-256 verified'});
  setMessage('Ready. On the '+receiver+' press Receive & open shared data. Uploading alone does not prove the other screen downloaded it.');
 }
 async function receive(){
  if(!handoff)throw Error('Send a file from the other screen first.');
  const file=await (await request('exchange/files/'+handoff.file_id)).json();
  if(file.status!=='complete')throw Error('Wait for the sender to finish uploading, then press Receive again.');
  const start=performance.now(),response=await request('exchange/files/'+file.id+'/download'),reader=response.body!.getReader(),digest=sha256.create();let bytes=0;
  setProgress({bytes:0,total:file.size,label:'Receiving and checking original bytes'});
  while(true){const chunk=await reader.read();if(chunk.done)break;digest.update(chunk.value);bytes+=chunk.value.length;setProgress({bytes,total:file.size,label:'Receiving and checking original bytes'});}
  if(bytes!==file.size||hex(digest.digest())!==file.sha256)throw Error('Received file hash did not match. Retry Receive before opening the data.');
  await post('exchange/files/'+file.id+'/receipt',{sha256:file.sha256,bytes,transferred_bytes:bytes,elapsed_ms:Math.max(1,performance.now()-start),retries:0,direction:'download'});
  const asset=await post('workspace/import-reference',{kind:'exchange',id:file.id});
  if(!await control())throw Error('Bytes verified and saved. Press Take control to open the dataset.');
  if(!await command('asset',{asset_id:asset.id}))throw Error('Bytes saved in Library. Choose a supported signal dataset in Signals & DSP.');
  if(!await command('play'))throw Error('Dataset opened. Press Play shared replay to animate it.');
  setMessage('Last receive: '+file.name+' matched SHA-256, was saved in Library and opened on both screens. Scenario buttons start a new Simulation; DSP changes process the selected input.');
  setProgress({bytes,total:file.size,label:'Receive verified · shared replay started'});onSignals();
 }
 const phones=shared?.peers?.filter((p:D)=>p.role==='phone').length||0,laptops=shared?.peers?.filter((p:D)=>p.role==='laptop').length||0;
 return <section className="panel command-bridge" aria-label="Send and receive shared experiment">
  <div className="bridge-heading"><div><span className="badge">CONNECTED EXPERIMENT</span><h2>Send. Receive. Explore together.</h2><p>Stay here for file transfer, the 3D room and DSP. Either screen can explicitly take control.</p></div><label>This screen<select aria-label="This screen role" value={role} disabled={busy} onChange={e=>setRole(e.target.value)}><option value="phone">Phone</option><option value="laptop">Laptop</option></select></label></div>
  <details className="bridge-map"><summary>Connection map · {phones?'Phone session active':'Waiting for phone session'} · ESP32-S3 setup</summary><div className="bridge-topology" aria-label="Connection status"><div><strong>Phone</strong><span>{phones?phones+' active phone session(s)':'No active phone session detected'}</span></div><span aria-hidden="true">↔</span><div><strong>Laptop · ORBIT server</strong><span>{laptops?laptops+' active desktop session(s)':'Open the laptop Command Centre'}</span></div><span aria-hidden="true">↔</span><div><strong>Router / modem · shared LAN</strong><span>Radio standard and physical wiring not verified</span></div><div className="bridge-esp"><strong>ESP32-S3 · external sensing hardware</strong><span>Live ESP capture not verified. These sample files are Simulation.</span></div></div><p>Connect phone and laptop to the same router/hotspot. An ESP32-S3 needs compatible capture firmware and its own network/USB setup; it does not automatically supply CSI or human positions when plugged in.</p></details>
  <div className="bridge-actions"><label>Send direction<select aria-label="Send direction" value={direction} disabled={busy} onChange={e=>{const next=e.target.value;void run(async()=>{if(await control())await command('route',{direction:next});});}}><option value="phone_to_laptop">Phone → Laptop</option><option value="laptop_to_phone">Laptop → Phone</option></select></label><label>Demonstration dataset<select aria-label="Demonstration dataset" value={sample} disabled={busy} onChange={e=>setSample(e.target.value)}><option value="still">One standing</option><option value="walking">One walking</option><option value="two_still">Two standing</option><option value="two">Two walking</option><option value="mixed">Standing + walking</option></select></label>
   <button className="button" disabled={busy||role!==sender} title={'Sends actual labelled Simulation file bytes from this '+sender+' session to the laptop server.'} onClick={()=>void run(async()=>{const response=await request('shared/sample?scenario='+sample);await send(new File([await response.blob()],'Simulation-'+sample+'.npz',{type:'application/octet-stream'}));})}>Send selected Simulation data</button>
   <button className="button secondary" disabled={busy||role!==sender} onClick={()=>picker.current?.click()}>Send my data file</button><input ref={picker} type="file" hidden accept=".npz,.json,.csv,.npy,.wav" onChange={e=>{const file=e.target.files?.[0];e.target.value='';if(file)void run(()=>send(file));}}/>
   <button className="button" disabled={busy||!handoff||role!==receiver} onClick={()=>void run(receive)}>Receive & open shared data</button>
  </div><p>Sender: {sender} · receiver: {receiver}. {role===sender?'Send here, then press Receive on the other screen.':'Press Receive here after the sender finishes.'} This screen role is a display choice, not hardware detection.</p>
  {handoff&&<p>Shared incoming file: <strong>{handoff.name}</strong> · {handoff.direction==='phone_to_laptop'?'Phone → Laptop':'Laptop → Phone'}.</p>}
  {progress&&<div role="status"><progress value={progress.bytes} max={progress.total||1}/><p>{progress.label} · {progress.bytes.toLocaleString()} / {progress.total.toLocaleString()} bytes</p></div>}
  {message&&<p role="status">{message}</p>}{error&&<div role="alert"><p>{error}</p><button className="button secondary" disabled={busy} onClick={()=>void run(receive)}>Retry receive</button></div>}
  {handoff&&<details><summary>Transfer graph · actual accepted bytes</summary><TransferTimeline key={handoff.file_id} id={handoff.file_id} name={handoff.name}/><p>A small upload can finish before the next refresh. Cached duplicate data has no new upload timing. This measures application bytes, not RF signal strength.</p></details>}
 </section>;
}
