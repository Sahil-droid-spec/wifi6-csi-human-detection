import {useEffect,useRef,useState} from 'react';
import {Trace} from './Showcase';

type Item={id:string,title:string,name:string,size:number,parent_id?:string,trashed?:boolean,source?:string,clipped_samples?:number};
type Analysis={source:string,rate:number,channels:number,frames:number,duration:number,protocol:string,
  waveform:[number,number][],spectrum_hz:number[],spectrum_db:number[],stft_hz:number[],stft_seconds:number[],stft_db:number[][]};
type MatlabResult={matlab_version:string,protocol:string,max_abs_difference:number,library_id:string,shape:number[]};

async function call<T>(path:string,method='GET',body?:object):Promise<T>{
  const r=await fetch('/api/'+path,{method,headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined,
    signal:AbortSignal.timeout(path.startsWith('matlab/')?160000:30000)});
  const result=await r.json();
  if(!r.ok)throw Error(typeof result.detail==='string'?result.detail:'Check the selected file or filter settings.');
  return result;
}

function Waveform({data}:{data:Analysis}){
  const path=data.waveform.map(([lo,hi],i)=>{
    const x=28+580*i/Math.max(1,data.waveform.length-1);
    return `M${x} ${86-59*lo}V${86-59*hi}`;
  }).join(' ');
  return <svg viewBox="0 0 640 178" role="img" aria-label="Audio waveform in seconds, full scale amplitude">
    <path d="M28 23V148H608 M28 86H608" stroke="currentColor" opacity=".3" fill="none"/>
    <path d={path} stroke="var(--blue)" strokeWidth="1.5" fill="none"/>
    <text x="28" y="17" fill="currentColor">Waveform · normalized amplitude</text>
    <text x="608" y="169" textAnchor="end" fill="currentColor">{data.duration.toFixed(3)} s</text>
  </svg>;
}

function Spectrogram({data}:{data:Analysis}){
  const canvas=useRef<HTMLCanvasElement>(null);
  useEffect(()=>{
    const ctx=canvas.current?.getContext('2d');if(!ctx)return;
    const cols=data.stft_seconds.length,rows=data.stft_hz.length;
    const bitmap=ctx.createImageData(cols,rows);
    data.stft_db.forEach((row,j)=>row.forEach((db,i)=>{
      const fraction=Math.min(1,Math.max(0,(db+85)/85));
      bitmap.data.set([25+210*fraction,29+145*fraction,62+35*fraction,255],((rows-1-j)*cols+i)*4);
    }));
    ctx.putImageData(bitmap,0,0);
  },[data]);
  return <figure><canvas className="audio-spectrogram" ref={canvas} width={data.stft_seconds.length} height={data.stft_hz.length}
    role="img" aria-label="Spectrogram of the selected audio channel"/>
    <figcaption>{data.stft_seconds[0]?.toFixed(3)}–{data.stft_seconds.at(-1)?.toFixed(3)} s horizontally · 0–{data.stft_hz.at(-1)?.toFixed(0)} Hz from bottom to top · −85 to 0 dBFS.</figcaption>
  </figure>;
}

export function AudioStudio(){
  const requested=()=>new URLSearchParams(location.hash.split('?')[1]).get('item')||'';
  const [items,setItems]=useState<Item[]>([]),[id,setId]=useState(requested),[analysis,setAnalysis]=useState<Analysis|null>(null);
  const [original,setOriginal]=useState<Analysis|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const [kind,setKind]=useState('lowpass'),[cutoff,setCutoff]=useState(1200),[upper,setUpper]=useState(2500);
  const [title,setTitle]=useState(''),[matlab,setMatlab]=useState<MatlabResult|null>(null),[canMatlab,setCanMatlab]=useState(false);
  const [confirmDelete,setConfirmDelete]=useState('');
  const selected=items.find(item=>item.id===id&&!item.trashed);
  const parent=items.find(item=>item.id===selected?.parent_id&&!item.trashed);
  const refresh=async()=>setItems(await call<Item[]>('audio'));
  const local=['127.0.0.1','localhost','[::1]'].includes(location.hostname);
  useEffect(()=>{
    refresh().catch(e=>setError(e.message));
    call<{available:boolean,can_run:boolean}>('matlab/status').then(r=>setCanMatlab(r.available&&r.can_run)).catch(()=>{});
    const change=()=>setId(requested());window.addEventListener('hashchange',change);
    return()=>window.removeEventListener('hashchange',change);
  },[]);
  useEffect(()=>{
    let active=true;setAnalysis(null);setOriginal(null);setMatlab(null);
    if(selected){
      call<Analysis>('audio/'+selected.id+'/analysis').then(r=>{if(active)setAnalysis(r);}).catch(e=>{if(active)setError(e.message);});
      if(parent)call<Analysis>('audio/'+parent.id+'/analysis').then(r=>{if(active)setOriginal(r);}).catch(()=>{});
    }
    return()=>{active=false;};
  },[selected?.id,parent?.id]);
  useEffect(()=>{setTitle(selected?.title||'');},[selected?.title,selected?.id]);
  async function action(work:()=>Promise<void>){
    setBusy(true);setError('');
    try{await work();}catch(e){setError(e instanceof Error?e.message:'Try again with a supported WAV.');}
    finally{setBusy(false);}
  }
  return <div className="ultimate-tools">
    <section className="panel"><span className="badge">LOCAL LIBRARY</span><h2>Audio Studio</h2>
      <p>Send a WAV through <a href="#/transfer">Transfer &amp; chat</a> and choose <strong>Save &amp; analyze WAV</strong>, or add a recording in the <a href="#/media">Lab notebook</a>. Analysis supports 16-bit PCM WAV, mono or stereo, 8–48 kHz, up to 60 seconds and 12 MiB.</p>
      <label>Library recording<select disabled={busy} value={id} onChange={e=>{setError('');setId(e.target.value);}}>
        <option value="">Choose a saved WAV</option>
        {items.filter(item=>!item.trashed).map(item=><option key={item.id} value={item.id}>{item.title}{item.parent_id?' · processed copy':''}</option>)}
      </select></label>
      {error&&<p role="alert">{error}</p>}
      {busy&&<p role="status">Working on the selected audio…</p>}
    </section>
    {selected&&<section className="panel"><h2>{selected.title}</h2>
      {parent&&<><h3>Original input · {parent.title}</h3><audio controls preload="metadata" src={'/api/media/'+parent.id+'/file'}/></>}
      <h3>{selected.parent_id?'Processed copy':'Original recording'}</h3>
      <audio key={id} controls preload="metadata" src={'/api/media/'+id+'/file'}/>
      <div className="button-row">
        <a className="button secondary" download={selected.name} href={'/api/media/'+id+'/file'}>Export WAV</a>
        {local&&<button className="button secondary" disabled={busy} onClick={()=>action(async()=>{await call('audio/'+id+'/trash','POST');setId('');await refresh();})}>Move to Trash</button>}
      </div>
      <label>Library title<input maxLength={160} value={title} onChange={e=>setTitle(e.target.value)}/></label>
      <button className="button secondary" disabled={busy||title===selected.title||!title.trim()} onClick={()=>action(async()=>{await call('audio/'+id,'PATCH',{title});await refresh();})}>Rename in Library</button>
      {analysis&&<>
        <p>{analysis.source} · {analysis.rate} Hz · {analysis.channels} channel(s) · {analysis.frames.toLocaleString()} frames. {analysis.protocol}</p>
        {selected.clipped_samples!==undefined&&<p>{selected.clipped_samples} channel samples clipped during PCM16 export.</p>}
        {original&&<><h3>Input waveform</h3><Waveform data={original}/></>}
        <Waveform data={analysis}/>
        <details><summary>Inspect spectrum and spectrogram</summary>
          <Trace values={analysis.spectrum_db} title="Power spectrum (dBFS²/Hz)" source={analysis.source} xLabel="Hz" xEnd={analysis.spectrum_hz.at(-1)}/>
          <Spectrogram data={analysis}/>
        </details>
        <div className="control-grid">
          <label>Filter<select value={kind} onChange={e=>setKind(e.target.value)}>
            <option value="lowpass">Butterworth low-pass</option><option value="highpass">Butterworth high-pass</option>
            <option value="bandpass">Butterworth band-pass</option><option value="notch">Notch</option><option value="hamming">Hamming FIR low-pass</option>
          </select></label>
          <label>{kind==='notch'?'Notch centre (Hz)':'Cutoff (Hz)'}<input type="number" min={1} max={analysis.rate/2-1} value={cutoff} onChange={e=>setCutoff(+e.target.value)}/></label>
          {kind==='bandpass'&&<label>Upper cutoff (Hz)<input type="number" min={cutoff+1} max={analysis.rate/2-1} value={upper} onChange={e=>setUpper(+e.target.value)}/></label>}
        </div>
        <div className="button-row">
          <button className="button" disabled={busy} onClick={()=>action(async()=>{const result=await call<Item>('audio/'+id+'/filter','POST',{kind,cutoff_hz:cutoff,upper_hz:upper});await refresh();setId(result.id);})}>Apply filter &amp; save copy</button>
          {canMatlab&&<button className="button secondary" disabled={busy} onClick={()=>action(async()=>setMatlab(await call<MatlabResult>('matlab/audio/'+id,'POST')))}>Compare in MATLAB</button>}
        </div>
        {matlab?.library_id===id&&<p>{matlab.matlab_version} · maximum absolute difference {matlab.max_abs_difference.toExponential(3)} across {matlab.shape[0]} samples. {matlab.protocol}</p>}
      </>}
    </section>}
    {local&&<section className="panel"><details><summary>Trash · {items.filter(item=>item.trashed).length}</summary>
      <p>Deleting here removes the Library copy. An independent copy in Transfer &amp; chat may still exist.</p>
      {items.filter(item=>item.trashed).map(item=><div key={item.id}><p>{item.title}</p>
        <div className="button-row">
          <button className="button secondary" disabled={busy} onClick={()=>action(async()=>{await call('audio/'+item.id+'/restore','POST');await refresh();setId(item.id);})}>Restore</button>
          {confirmDelete!==item.id?<button className="button secondary" disabled={busy} onClick={()=>setConfirmDelete(item.id)}>Permanent delete…</button>:
            <><button className="button secondary" disabled={busy} onClick={()=>action(async()=>{await call('audio/'+item.id,'DELETE');setConfirmDelete('');await refresh();})}>Confirm permanent delete</button>
            <button className="button secondary" onClick={()=>setConfirmDelete('')}>Cancel</button></>}
        </div>
      </div>)}
    </details></section>}
  </div>;
}
