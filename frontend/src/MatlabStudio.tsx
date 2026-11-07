import {useEffect,useRef,useState} from 'react';
import {Trace} from './Showcase';

type Mode='fir'|'image'|'simulink';
type Result={mode:Mode,source:string,matlab_version:string,protocol:string,shape:number[],
  max_abs_difference:number,input:number[]|number[][],python:number[]|number[][][],matlab:number[]|number[][][]};

function ImageTile({values,title}:{values:number[][],title:string}){
  const canvas=useRef<HTMLCanvasElement>(null);
  useEffect(()=>{
    const c=canvas.current;if(!c)return;
    const ctx=c.getContext('2d');if(!ctx)return;
    const image=ctx.createImageData(c.width,c.height);
    values.flat().forEach((x,i)=>{
      const value=Math.max(0,Math.min(255,Math.round(x*255)));
      image.data.set([value,value,value,255],4*i);
    });
    ctx.putImageData(image,0,0);
  },[values]);
  return <figure><canvas ref={canvas} width={values[0].length} height={values.length} aria-label={title}/><figcaption>{title}</figcaption></figure>;
}

export function MatlabStudio(){
  const [status,setStatus]=useState<{available:boolean,can_run:boolean}|null>(null);
  const [busy,setBusy]=useState<Mode|null>(null),[error,setError]=useState(''),[result,setResult]=useState<Result|null>(null);
  useEffect(()=>{
    fetch('/api/matlab/status').then(r=>{if(!r.ok)throw Error();return r.json();}).then(setStatus)
      .catch(()=>setError('Reload this page after starting Orbit.'));
  },[]);
  async function run(mode:Mode){
    setBusy(mode);setError('');setResult(null);
    try{
      const response=await fetch('/api/matlab/'+mode,{method:'POST',signal:AbortSignal.timeout(160000)});
      const data=await response.json();
      if(!response.ok)throw Error(data.detail||'Open MATLAB and check the license.');
      setResult(data);
    }catch(e){setError(e instanceof Error?e.message:'Check MATLAB and try again.');}
    finally{setBusy(null);}
  }
  return <div className="ultimate-tools">
    <section className="panel"><span className="badge">GENERATED VALIDATION INPUT</span><h2>MATLAB Studio</h2>
      <p>Run a fixed experiment in MATLAB or Simulink on this laptop. Orbit compares each returned value with Python using the same input. MATLAB and the required toolboxes must be licensed on this laptop.</p>
      <p>{!status?'Checking installation…':!status.can_run?'Open this page on the laptop.':status.available?'MATLAB installation found. Each run checks whether its required toolbox starts.':'MATLAB was not found. Install a licensed MATLAB or add it to PATH.'}</p>
      <div className="button-row">
        <button className="button" disabled={!status?.available||!status?.can_run||!!busy} onClick={()=>run('fir')}>Compare FIR filter</button>
        <button className="button secondary" disabled={!status?.available||!status?.can_run||!!busy} onClick={()=>run('image')}>Compare image processing</button>
        <button className="button secondary" disabled={!status?.available||!status?.can_run||!!busy} onClick={()=>run('simulink')}>Run Simulink gain model</button>
      </div>
      {busy&&<p role="status">Waiting for MATLAB to finish the {busy} experiment. Startup can take a minute.</p>}
      {error&&<p role="alert">{error}</p>}
    </section>
    {result&&<section className="panel"><h2>Python and MATLAB comparison</h2>
      <p>{result.matlab_version} · {result.source}</p>
      <p><strong>Maximum absolute difference {result.max_abs_difference.toExponential(3)}</strong> across {result.shape.join(' × ')} values. {result.protocol}</p>
      {result.mode==='image'?<div className="matlab-tiles">
        <ImageTile values={result.input as number[][]} title="Input pattern"/>
        {['Smoothed image','Absolute edge response','Threshold mask'].map((title,i)=><ImageTile key={title} values={(result.matlab as number[][][]).map(row=>row.map(pixel=>pixel[i]))} title={title}/>)}
      </div>:<>
        <Trace values={result.input as number[]} title="Shared input" xLabel="sample index" source={result.source}/>
        <Trace values={result.matlab as number[]} title="MATLAB or Simulink output" xLabel="sample index" source={result.source}/>
        <Trace values={(result.matlab as number[]).map((x,i)=>x-(result.python as number[])[i])} title="MATLAB minus Python" xLabel="sample index" source={result.source}/>
      </>}
    </section>}
  </div>;
}
