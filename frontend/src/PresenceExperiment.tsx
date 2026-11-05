import {useEffect,useState} from 'react';
import {Trace} from './Showcase';

type Metrics={accuracy:number,balanced_accuracy:number,f1:number,support:number,confusion_matrix:number[][]};
type Recording={id:string,name:string,date:string,truth:number,windows:{start:number,end:number}[],quality_skipped:number};
type Result={source:string,protocol:string,filter_delay_packets:number,coefficients:number[],frequency:number[],response_db:number[],
  metrics:{baseline:Metrics,hamming:Metrics},recordings:Recording[],skipped_recordings:{id:string,reason:string}[],
  folds:{held_out_date:string,train_ids:string[],test_ids:string[]}[]};
type Job={id:string,status:string,progress:number,message:string,result?:Result};
type Window={start:number,end:number,raw:(number|null)[],filtered:(number|null)[],baseline:number,hamming:number,truth:number};
type Dataset={id:string,name:string};

async function request<T>(url:string,body?:object):Promise<T>{
  const response=await fetch('/api/'+url,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},
    body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(20000)});
  const value=await response.json();
  if(!response.ok)throw Error(typeof value.detail==='string'?value.detail:'Check the recording and settings.');
  return value;
}

function SignalPair({window}:{window:Window}){
  const finite=[...window.raw,...window.filtered].filter((v):v is number=>v!==null);
  const low=Math.min(...finite),high=Math.max(...finite),span=high-low||1;
  function path(values:(number|null)[]){
    let pen=false;
    return values.map((value,i)=>{
      if(value===null){pen=false;return '';}
      const mark=pen?'L':'M';pen=true;
      return mark+(40+560*i/Math.max(1,values.length-1))+','+(135-99*(value-low)/span);
    }).join(' ');
  }
  return <svg className="presence-trace" viewBox="0 0 640 190" role="img" aria-label="Raw and Hamming-filtered CSI on a shared packet and amplitude axis">
    <path d="M40 33V135H600" fill="none" stroke="currentColor" opacity=".35"/>
    <path d={path(window.raw)} fill="none" stroke="var(--blue)" strokeWidth="2"/>
    <path d={path(window.filtered)} fill="none" stroke="var(--orange)" strokeWidth="2" strokeDasharray="6 3"/>
    <text x="40" y="22" fill="currentColor">Median CSI amplitude · {low.toPrecision(3)}–{high.toPrecision(3)}</text>
    <text x="40" y="160" fill="currentColor">Packet {window.start}</text>
    <text x="600" y="160" textAnchor="end" fill="currentColor">{window.end-1}</text>
    <text x="40" y="182" fill="currentColor">Solid: raw · dashed: Hamming FIR · gaps: unusable packets</text>
  </svg>;
}

const label=(x:number)=>x?'Present':'Absent';
const percent=(x:number)=>(x*100).toFixed(1)+'%';
export function PresenceExperiment({datasets,simulation}:{datasets:Dataset[],simulation:boolean}){
  const [dataset,setDataset]=useState(''),[bandwidth,setBandwidth]=useState(20),[taps,setTaps]=useState(15),[cutoff,setCutoff]=useState(.08);
  const [job,setJob]=useState<Job|null>(null),[error,setError]=useState(''),[starting,setStarting]=useState(false);
  const [id,setId]=useState(''),[index,setIndex]=useState(0),[window,setWindow]=useState<Window|null>(null);
  const active=job?.status==='queued'||job?.status==='running';
  const result=job?.result;
  const recording=result?.recordings.find(r=>r.id===id);
  useEffect(()=>{
    if(!active||!job)return;
    let cancelled=false,timer:ReturnType<typeof setTimeout>;
    const poll=async()=>{
      try{
        const next=await request<Job>('jobs/'+job.id);
        if(cancelled)return;
        setJob(next);
        if(next.result?.recordings.length){setId(next.result.recordings[0].id);setIndex(0);}
        if(next.status==='queued'||next.status==='running')timer=setTimeout(poll,850);
      }catch(e){if(!cancelled){setError((e as Error).message);timer=setTimeout(poll,2000);}}
    };
    timer=setTimeout(poll,650);
    return()=>{cancelled=true;clearTimeout(timer);};
  },[active,job?.id]);
  useEffect(()=>{
    setWindow(null);if(!recording||!job)return;
    let cancelled=false;
    request<Window>('presence/'+job.id+'/'+recording.id+'/window?index='+index).then(x=>{if(!cancelled)setWindow(x);})
      .catch(e=>{if(!cancelled)setError(e.message);});
    return()=>{cancelled=true;};
  },[recording?.id,index,job?.id]);
  useEffect(()=>{setDataset('');},[simulation]);
  return <div className="ultimate-tools">
    <section className="panel">
      <span className="badge">{simulation?'SIMULATION':'RECORDED DATA'}</span><h2>Presence Detection Experiment</h2>
      <p>Compare the current CSI features with the same four features after Hamming FIR. Both paths use the same Random Forest settings and hold out each recording date in turn.</p>
      <fieldset disabled={active||starting} className="control-grid">
        <label>Dataset<select value={dataset} onChange={e=>setDataset(e.target.value)}><option value="">All eligible datasets in this library</option>
          {datasets.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></label>
        <label>Bandwidth<select value={bandwidth} onChange={e=>setBandwidth(+e.target.value)}><option>20</option><option>40</option></select></label>
        <label>Odd taps<input type="number" min={3} max={63} step={2} value={taps} onChange={e=>setTaps(+e.target.value)}/></label>
        <label>Cutoff (cycles/packet)<input type="number" min={.001} max={.499} step={.01} value={cutoff} onChange={e=>setCutoff(+e.target.value)}/></label>
      </fieldset>
      <div className="button-row">
        <button className="button" disabled={active||starting} onClick={async()=>{
          setStarting(true);setError('');
          try{setJob(await request<Job>('presence',{dataset_id:dataset||null,bandwidth,synthetic:simulation,taps,cutoff}));}
          catch(e){setError((e as Error).message);}
          finally{setStarting(false);}
        }}>Run matched experiment</button>
        {active&&job&&<button className="button secondary" onClick={()=>request('jobs/'+job.id+'/cancel',{}).catch(e=>setError(e.message))}>Cancel after current fit</button>}
      </div>
      {active&&job&&<p role="status">{job.message} · {job.progress}%</p>}
      {(error||job?.status==='failed'||job?.status==='cancelled')&&<p role="alert">{error||job?.message}</p>}
      <p className="helper">Pick FIR settings before evaluation. Repeatedly choosing settings from the same held-out scores makes those scores exploratory.</p>
    </section>
    {result&&<>
      <section className="panel"><span className="badge">{result.source}</span><h2>Capture-level results</h2>
        <p>{result.protocol}</p>
        <div className="table-scroll"><table><thead><tr><th>Path</th><th>Captures</th><th>Accuracy</th><th>Balanced accuracy</th><th>Presence F1</th><th>False alarms</th><th>Misses</th></tr></thead>
          <tbody>{Object.entries(result.metrics).map(([name,m])=><tr key={name}>
            <th>{name==='baseline'?'Baseline':'Hamming FIR'}</th><td>{m.support}</td><td>{percent(m.accuracy)}</td><td>{percent(m.balanced_accuracy)}</td>
            <td>{percent(m.f1)}</td><td>{m.confusion_matrix[0][1]}</td><td>{m.confusion_matrix[1][0]}</td>
          </tr>)}</tbody></table></div>
        <p>Hamming minus baseline balanced accuracy: {((result.metrics.hamming.balanced_accuracy-result.metrics.baseline.balanced_accuracy)*100).toFixed(1)} percentage points on this cohort.</p>
        <p>{result.skipped_recordings.length} recordings excluded by the shared quality gate. FIR delay {result.filter_delay_packets} packets.</p>
        <details><summary>Filter response, coefficients and held-out folds</summary>
          <Trace source={result.source} title="Hamming FIR response (dB)" values={result.response_db} xLabel="cycles/packet" xEnd={result.frequency.at(-1)}/>
          <p>{result.coefficients.map(c=>c.toFixed(6)).join(', ')}</p>
          {result.folds.map(f=><p key={f.held_out_date}>{f.held_out_date} held out · {f.train_ids.length} training recordings · {f.test_ids.length} test recordings</p>)}
        </details>
      </section>
      <section className="panel"><h2>Compare held-out windows</h2>
        <label>Recording<select value={id} onChange={e=>{setId(e.target.value);setIndex(0);}}>{result.recordings.map(r=><option key={r.id} value={r.id}>{r.name} · {r.date}</option>)}</select></label>
        {recording&&<><label>Accepted window {index+1} of {recording.windows.length}
          <input type="range" min={0} max={recording.windows.length-1} value={index} onChange={e=>setIndex(+e.target.value)}/></label>
          <p>{recording.quality_skipped} windows skipped for quality or length.</p></>}
        {window&&<><p>Recorded label: {label(window.truth)} · Baseline: {label(window.baseline)} · Hamming: {label(window.hamming)}</p><SignalPair window={window}/></>}
      </section>
    </>}
  </div>;
}
