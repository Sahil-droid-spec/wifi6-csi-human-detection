import {useEffect,useRef,useState} from 'react';

type Settings={radius:number,minimum_area:number,sensitivity:number,size:number,engine:'python'|'matlab',source_kind:'uploaded'|'simulation'};
type Saved={id:string,title:string,retina_role:string,parent_id:string|null,synthetic:boolean};
type Result={source:string,processing_ms:number,source_dimensions:number[],processed_dimensions:number[],
  candidate_pixels:number,field_pixels:number,protocol:string,engine_version:string,engine_note:string,
  images:Record<string,string>,saved:Saved[]};

async function json<T>(url:string,options:RequestInit={}):Promise<T>{
  const response=await fetch('/api/retina'+url,{...options,signal:AbortSignal.timeout(165000)});
  const data=await response.json();
  if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'Check the image and processing settings.');
  return data;
}

export function RetinalStudio(){
  const [file,setFile]=useState<File|null>(null),[consent,setConsent]=useState(false),[busy,setBusy]=useState(false);
  const [settings,setSettings]=useState<Settings>({radius:9,minimum_area:12,sensitivity:.45,size:768,engine:'python',source_kind:'uploaded'});
  const [result,setResult]=useState<Result|null>(null),[saved,setSaved]=useState<Saved[]>([]),[error,setError]=useState('');
  const [tab,setTab]=useState('overlay'),[confirm,setConfirm]=useState(''),[matlab,setMatlab]=useState(false);
  const fileInput=useRef<HTMLInputElement>(null),alive=useRef(false),controller=useRef<AbortController|null>(null);
  const local=['127.0.0.1','localhost','[::1]'].includes(location.hostname);
  const refresh=async()=>setSaved(await json<Saved[]>(''));
  useEffect(()=>{
    alive.current=true;
    refresh().catch(e=>setError(e.message));
    fetch('/api/matlab/status').then(r=>r.ok?r.json():null).then(r=>{if(alive.current)setMatlab(!!r?.available);}).catch(()=>{});
    return()=>{alive.current=false;controller.current?.abort();};
  },[]);
  const change=(patch:Partial<Settings>)=>{setSettings(current=>({...current,...patch}));setResult(null);setError('');};
  async function run(save:boolean){
    if(!file||!consent)return;
    setBusy(true);setError('');setResult(null);
    const cancel=new AbortController();controller.current=cancel;
    const timeout=setTimeout(()=>cancel.abort(),165000);
    try{
      const params=new URLSearchParams({...Object.fromEntries(Object.entries(settings).map(([k,v])=>[k,String(v)])),consent:'true',save:String(save)});
      const response=await fetch('/api/retina/analyse?'+params,{method:'POST',body:file,
        headers:{'Content-Type':file.type||'application/octet-stream'},signal:cancel.signal});
      const value=await response.json();
      if(!response.ok)throw Error(typeof value.detail==='string'?value.detail:'Choose a readable fundus photo.');
      if(alive.current){setResult(value);setTab('overlay');await refresh();}
    }catch(e){if(alive.current)setError(e instanceof Error?e.message:'Try another readable image.');}
    finally{clearTimeout(timeout);if(alive.current)setBusy(false);controller.current=null;}
  }
  return <div className="ultimate-tools">
    <section className="panel">
      <span className="badge">FUNDUS IMAGE RESEARCH</span><h2>Retinal Image Lab</h2>
      <p>Open a fundus photograph from appropriate imaging equipment or a licensed dataset. Inspect grayscale processing, contrast enhancement, vessel candidates and an overlay. The laptop processes the image for both devices.</p>
      <label><input type="checkbox" checked={consent} disabled={busy} onChange={e=>setConsent(e.target.checked)}/> I have permission to process this fundus photo and consent to local processing.</label>
      <label>Choose a fundus JPEG or PNG · up to 8 MiB
        <input ref={fileInput} type="file" accept="image/jpeg,image/png" disabled={busy} onChange={e=>{
          const chosen=e.target.files?.[0]||null;
          setFile(chosen);setResult(null);setError(chosen&&chosen.size>8*1024**2?'Choose an image smaller than 8 MiB.':'');
        }}/>
      </label>
      <div className="button-row">
        <button className="button" disabled={!file||!consent||busy||file.size>8*1024**2} onClick={()=>run(false)}>Process preview</button>
        <button className="button secondary" disabled={!file||!consent||busy||file.size>8*1024**2} onClick={()=>run(true)}>Process &amp; save to Library</button>
        <button className="button secondary" disabled={busy||!file} onClick={()=>{setFile(null);setResult(null);if(fileInput.current)fileInput.current.value='';}}>Discard preview</button>
      </div>
      <details><summary>Processing settings</summary><fieldset disabled={busy} className="control-grid">
        <label>Image source<select value={settings.source_kind} onChange={e=>change({source_kind:e.target.value as Settings['source_kind']})}>
          <option value="uploaded">Uploaded fundus photograph</option><option value="simulation">Generated test image</option>
        </select></label>
        <label>Engine<select value={settings.engine} onChange={e=>change({engine:e.target.value as Settings['engine']})}>
          <option value="python">Python / OpenCV</option><option value="matlab" disabled={!matlab}>MATLAB · requires licensed Image Processing Toolbox</option>
        </select></label>
        <label>Maximum processing side<select value={settings.size} onChange={e=>change({size:+e.target.value})}><option value={256}>256 pixels</option><option value={512}>512 pixels</option><option value={768}>768 pixels</option><option value={1024}>1024 pixels</option></select></label>
        <label>Vessel-enhancement radius (pixels)<input type="number" min={3} max={20} value={settings.radius} onChange={e=>change({radius:+e.target.value})}/></label>
        <label>Minimum component area (pixels)<input type="number" min={0} max={400} value={settings.minimum_area} onChange={e=>change({minimum_area:+e.target.value})}/></label>
        <label>Threshold sensitivity<input type="range" min={.1} max={.8} step={.05} value={settings.sensitivity} onChange={e=>change({sensitivity:+e.target.value})}/>{settings.sensitivity.toFixed(2)}</label>
      </fieldset><p>Python uses the green channel, CLAHE, median filtering, morphological black-hat enhancement, adaptive thresholding and component cleanup. MATLAB uses its corresponding image-processing functions. Each engine has its own defaults.</p>
      <a className="button secondary" href="/api/retina/matlab-script" download>Download default MATLAB script</a></details>
      {busy&&<p role="status">Processing on the laptop{settings.engine==='matlab'?' · MATLAB startup can take a minute':''}…</p>}
      {error&&<p role="alert">{error}</p>}
      <p className="helper">Educational vessel candidates. Clinical use requires reference annotations, validation and appropriate medical review. Live retinal capture requires dedicated imaging hardware.</p>
    </section>
    {result&&<section className="panel">
      <span className="badge">{result.source}</span><h2>Segmentation preview</h2>
      <div className="button-row">{[['preview','Input'],['enhanced','Enhanced'],['response','Vessel response'],['mask','Binary mask'],['overlay','Overlay']].map(([key,label])=>
        <button key={key} className={key===tab?'button':'button secondary'} onClick={()=>setTab(key)}>{label}</button>)}</div>
      <img className="retina-preview" src={result.images[tab]} alt={'Fundus processing · '+tab}/>
      {navigator.userAgent.includes('OrbitCompanion/')?
        <p>Use a saved-image download below to save on this phone.</p>:
        <a className="button secondary" href={result.images[tab]} download={'Orbit-fundus-'+tab+'.png'}>Download this view</a>}
      <p>{result.source_dimensions.join(' × ')} source pixels → {result.processed_dimensions.join(' × ')} processing pixels.
        Measured processing time {result.processing_ms.toFixed(1)} ms, including decoding and PNG encoding on the laptop. Upload time is additional.</p>
      <p>{result.candidate_pixels.toLocaleString()} candidate foreground pixels within {result.field_pixels.toLocaleString()} field pixels.
        {result.saved.length?' Saved to the local Library.':' Preview is in this browser.'}</p>
      <p>{result.protocol} {result.engine_note} Engine {result.engine_version}.</p>
    </section>}
    <section className="panel"><h2>Saved fundus images</h2>
      {!saved.length&&<p>Save an experiment to keep its original, enhanced image, mask and overlay in the Lab notebook.</p>}
      {saved.map(item=><article className="exchange-item" key={item.id}>
        <p>{item.title}</p><div className="button-row">
          <a className="button secondary" href={'/api/media/'+item.id+'/file'} target="_blank" rel="noreferrer">Open saved image</a>
          <a className="button secondary" href={'/api/media/'+item.id+'/file'} download={'Orbit-fundus-'+item.retina_role+'.png'}>Download saved image</a>
          {item.retina_role==='original'&&<button className="button secondary" disabled={busy} onClick={async()=>{
            try{
              const response=await fetch('/api/media/'+item.id+'/file');
              if(!response.ok)throw Error('The saved image is unavailable.');
              const blob=await response.blob();setFile(new File([blob],item.title,{type:blob.type}));
              setSettings(current=>({...current,source_kind:item.synthetic?'simulation':'uploaded'}));setResult(null);setError('');
            }catch(e){setError((e as Error).message);}
          }}>Use this input again</button>}
          {local&&(confirm!==item.id?<button className="button secondary" disabled={busy} onClick={()=>setConfirm(item.id)}>Delete image…</button>:
            <><button className="button secondary" disabled={busy} onClick={async()=>{try{await json('/media/'+item.id,{method:'DELETE'});setConfirm('');await refresh();}catch(e){setError((e as Error).message);}}}>Confirm permanent delete</button><button className="button secondary" onClick={()=>setConfirm('')}>Cancel</button></>)}
        </div>
      </article>)}
    </section>
  </div>;
}
