import {useEffect, useRef, useState} from 'react';
import {Trace} from './Showcase';

type Box = [number, number, number, number];
type Frame = {faces:Box[], eyes:Box[], qr:string, width:number, height:number};
type Sample = [number,number,number,number,number];
type Pulse = {bpm:number|null, duration_s:number, sample_rate_hz:number, reason:string, protocol:string,
  times?:number[],rgb?:number[][],filtered?:number[],frequency_hz?:number[],power?:number[]};
type Capture = {url:string,name:string,video:boolean,blob:Blob};

async function post<T>(path:string,body:BodyInit,contentType:string):Promise<T>{
  const laptop=['127.0.0.1','localhost','[::1]'].includes(location.hostname);
  const endpoint=laptop?path:'shared-'+path+'?consent=true';
  const response=await fetch('/api/vision/'+endpoint,{method:'POST',body,headers:{'Content-Type':contentType},signal:AbortSignal.timeout(6500)});
  const data=await response.json();
  if(!response.ok)throw Error(data.detail||'Try a new image or reopen Camera Studio.');
  return data;
}

export function CameraStudio(){
  const [on,setOn]=useState(false),[opening,setOpening]=useState(false),[consent,setConsent]=useState(false);
  const [error,setError]=useState(''),[frame,setFrame]=useState<Frame|null>(null),[motion,setMotion]=useState<number|null>(null);
  const [capture,setCapture]=useState<Capture|null>(null),[recording,setRecording]=useState(false);
  const [pulseTime,setPulseTime]=useState<number|null>(null),[pulse,setPulse]=useState<Pulse|null>(null);
  const video=useRef<HTMLVideoElement>(null),view=useRef<HTMLCanvasElement>(null),camera=useRef<MediaStream|null>(null);
  const alive=useRef(false),epoch=useRef(0),pending=useRef(false),detected=useRef<Frame|null>(null);
  const recorder=useRef<MediaRecorder|null>(null),recordLimit=useRef<ReturnType<typeof setTimeout>|undefined>(undefined);
  const pulseRun=useRef<{start:number,samples:Sample[],lastVideoTime:number,previous:Uint8ClampedArray|null}|null>(null);
  const allowed=window.isSecureContext;
  const supported=allowed&&!!navigator.mediaDevices?.getUserMedia;

  function stop(){
    epoch.current++;
    clearTimeout(recordLimit.current);
    if(recorder.current?.state==='recording')recorder.current.stop();
    camera.current?.getTracks().forEach(track=>track.stop());
    camera.current=null;
    pulseRun.current=null;detected.current=null;
    setOn(false);setRecording(false);setOpening(false);setPulseTime(null);setFrame(null);setMotion(null);
  }

  useEffect(()=>{
    alive.current=true;
    const hide=()=>{if(document.hidden)stop();};
    document.addEventListener('visibilitychange',hide);
    window.addEventListener('pagehide',stop);
    return()=>{
      alive.current=false;stop();
      document.removeEventListener('visibilitychange',hide);
      window.removeEventListener('pagehide',stop);
    };
  },[]);
  useEffect(()=>()=>{if(capture)URL.revokeObjectURL(capture.url);},[capture]);

  async function start(){
    setError('');setOpening(true);
    const generation=++epoch.current;
    try{
      const stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:480},frameRate:{ideal:24}},audio:false});
      if(!alive.current||generation!==epoch.current||document.hidden||!video.current){
        stream.getTracks().forEach(track=>track.stop());return;
      }
      camera.current=stream;
      stream.getVideoTracks().forEach(track=>{track.onended=stop;});
      video.current.srcObject=stream;
      await video.current.play();
      if(generation===epoch.current)setOn(true);
    }catch{
      if(generation===epoch.current){stop();setError('Allow the camera in Windows and in this browser, then try again. Close another app if it is using the camera.');}
    }finally{if(generation===epoch.current)setOpening(false);}
  }

  useEffect(()=>{
    if(!on)return;
    const source=document.createElement('canvas'),colors=document.createElement('canvas');
    colors.width=20;colors.height=14;
    const ctx=source.getContext('2d')!, rgbCtx=colors.getContext('2d',{willReadFrequently:true})!;
    let lastInspection=0,lastMotion=0,prior:Uint8ClampedArray|null=null;
    const generation=epoch.current;
    const tick=()=>{
      const v=video.current,display=view.current;
      if(!v?.videoWidth||!display||v.readyState<2)return;
      const scale=Math.min(1,640/Math.max(v.videoWidth,v.videoHeight));
      const width=Math.round(v.videoWidth*scale),height=Math.round(v.videoHeight*scale);
      if(source.width!==width||source.height!==height){source.width=display.width=width;source.height=display.height=height;}
      ctx.drawImage(v,0,0,width,height);
      const paint=display.getContext('2d')!;
      paint.drawImage(source,0,0);
      const found=detected.current;
      if(found?.width===width&&found?.height===height){
        paint.lineWidth=2;paint.strokeStyle='#56B4E9';
        found.faces.forEach(b=>paint.strokeRect(...b));
        paint.strokeStyle='#E69F00';found.eyes.forEach(b=>paint.strokeRect(...b));
      }
      const now=performance.now();
      if(now-lastInspection>=850&&!pending.current){
        pending.current=true;lastInspection=now;
        source.toBlob(async blob=>{
          try{
            if(!blob||generation!==epoch.current)return;
            const result=await post<Frame>('frame',blob,'image/jpeg');
            if(generation===epoch.current){detected.current=result;setFrame(result);}
          }catch(e){
            if(generation===epoch.current){detected.current=null;setFrame(null);setError(e instanceof Error?e.message:'Frame inspection failed.');}
          }finally{pending.current=false;}
        },'image/jpeg',0.8);
      }
      if(now-lastMotion>=350){
        lastMotion=now;rgbCtx.drawImage(source,0,0,20,14);
        const pixels=rgbCtx.getImageData(0,0,20,14).data;
        if(prior)setMotion(pixels.reduce((sum,value,i)=>i%4===3?sum:sum+Math.abs(value-prior![i]),0)/(20*14*3*255));
        prior=pixels;
      }
      const run=pulseRun.current;
      if(!run)return;
      const elapsed=(now-run.start)/1000;
      setPulseTime(Math.floor(elapsed));
      if(elapsed>=24){
        pulseRun.current=null;setPulseTime(null);
        if(run.samples.length<2){setError('Keep one face in view throughout the pulse sample.');return;}
        post<Pulse>('pulse',JSON.stringify({samples:run.samples}),'application/json')
          .then(result=>{if(generation===epoch.current)setPulse(result);})
          .catch(e=>{if(generation===epoch.current)setError(e.message);});
      }else if(found?.faces.length===1&&v.currentTime!==run.lastVideoTime&&found.width===width&&found.height===height){
        const [x,y,w,h]=found.faces[0];
        rgbCtx.drawImage(source,x+w*.19,y+h*.54,w*.62,h*.20,0,0,20,14);
        const rgba=rgbCtx.getImageData(0,0,20,14).data;
        const channels=[0,0,0];let delta=0;
        for(let i=0;i<rgba.length;i+=4)for(let c=0;c<3;c++){
          channels[c]+=rgba[i+c];if(run.previous)delta+=Math.abs(rgba[i+c]-run.previous[i+c]);
        }
        run.samples.push([elapsed,channels[0]/280,channels[1]/280,channels[2]/280,delta/(280*3*255)]);
        run.previous=rgba;run.lastVideoTime=v.currentTime;
      }
    };
    const timer=setInterval(tick,50);
    return()=>clearInterval(timer);
  },[on]);

  function snapshot(){
    const v=video.current;if(!v?.videoWidth)return;
    const canvas=document.createElement('canvas');canvas.width=v.videoWidth;canvas.height=v.videoHeight;
    canvas.getContext('2d')!.drawImage(v,0,0);
    canvas.toBlob(blob=>{if(blob&&alive.current)setCapture({url:URL.createObjectURL(blob),name:'Orbit-camera.jpg',video:false,blob});},'image/jpeg',0.9);
  }
  function record(){
    if(!camera.current||recorder.current||!window.MediaRecorder)return;
    try{
      const r=new MediaRecorder(camera.current,{videoBitsPerSecond:1200000}),chunks:Blob[]=[];
      recorder.current=r;
      r.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
      r.onstop=()=>{
        recorder.current=null;clearTimeout(recordLimit.current);
        if(!alive.current)return;
        setRecording(false);
        if(chunks.length){const blob=new Blob(chunks,{type:r.mimeType});setCapture({url:URL.createObjectURL(blob),name:r.mimeType.includes('mp4')?'Orbit-camera.mp4':'Orbit-camera.webm',video:true,blob});}
      };
      r.start(500);setRecording(true);
      recordLimit.current=setTimeout(()=>{if(r.state==='recording')r.stop();},30000);
    }catch{recorder.current=null;setError('Video recording is unavailable in this browser. Try a photo.');}
  }
  return <div className="ultimate-tools">
    <section className="panel">
      <span className="badge">LIVE · CONSENTED CAMERA</span><h2>Camera Studio</h2>
      <p>Preview a consented webcam feed, inspect face and eye candidate boxes, scan QR text, or save a local photo or short silent clip.</p>
      <label className="camera-consent"><input type="checkbox" checked={consent} disabled={on||opening} onChange={e=>setConsent(e.target.checked)}/> Everyone in view consents to local camera analysis.</label>
      <div className="button-row">
        <button className="button" disabled={!supported||!consent||on||opening} onClick={start}>{opening?'Waiting for camera…':'Start camera'}</button>
        <button className="button secondary" disabled={!on&&!opening} onClick={stop}>Stop camera</button>
      </div>
      {!supported&&<p>Use localhost on the laptop or trusted HTTPS on the phone. For ordinary phone HTTP, use Connected workbench → Record & preview → Take phone photo, or send an existing clip in <a href="#/transfer">Transfer & chat</a>.</p>}
      {error&&<p role="alert">{error}</p>}
      <video ref={video} hidden autoPlay playsInline muted/>
      <canvas ref={view} hidden={!on} className="camera-preview" aria-label="Live camera with face and eye boxes"/>
      {on&&<>
        <p role="status">Camera active{recording?' · Recording silent video (up to 30 seconds)':''}</p>
        <p>{frame?'Face candidates '+frame.faces.length+' · Eye candidates '+frame.eyes.length:'Inspecting frames…'}{motion===null?'':' · Mean frame brightness/color change '+(motion*100).toFixed(1)+'% (downsampled RGB pixel difference)'}</p>
        {frame?.qr&&<p className="camera-qr"><strong>QR text</strong> {frame.qr}</p>}
        <div className="button-row">
          <button className="button secondary" disabled={recording} onClick={snapshot}>Capture photo</button>
          {recording?<button className="button" onClick={()=>{if(recorder.current?.state==='recording')recorder.current.stop();}}>Stop recording</button>:<button className="button secondary" disabled={!window.MediaRecorder} onClick={record}>Record silent video</button>}
        </div>
      </>}
      {capture&&<section><h3>Local capture</h3>{capture.video?<video className="camera-preview" src={capture.url} controls/>:<img className="camera-preview" src={capture.url} alt="Local camera capture"/>}
        <div className="button-row"><button className="button" onClick={async()=>{try{const form=new FormData();form.append('file',capture.blob,capture.name);form.append('source','CONSENTED CAMERA CAPTURE');const r=await fetch('/api/workspace/import',{method:'POST',body:form});const d=await r.json();if(!r.ok)throw Error(d.detail||'Try saving again.');setCapture(null);location.hash='/workbench?asset='+d.id;}catch(e){setError((e as Error).message);}}}>Save to shared laptop Library</button>{!navigator.userAgent.includes('OrbitCompanion/')&&<a className="button secondary" download={capture.name} href={capture.url}>Download capture</a>}<button className="button secondary" onClick={()=>setCapture(null)}>Discard preview</button></div>
      </section>}
      <p className="helper">Orbit keeps frame analysis on this laptop. The preview stops when this tab becomes hidden. Captures stay in memory until you save or discard them.</p>
    </section>
    <section className="panel">
      <span className="badge">EDUCATIONAL · NON-CLINICAL</span><h2>Pulse signal lab</h2>
      <p>Hold one face still under steady light. Orbit samples mean facial RGB for 24 seconds, band-passes the normalized colour difference, and reports a pulse estimate only if its quality checks pass.</p>
      <button className="button" disabled={!on||frame?.faces.length!==1||pulseTime!==null||recording} onClick={()=>{
        setPulse(null);setError('');setPulseTime(0);
        pulseRun.current={start:performance.now(),samples:[],lastVideoTime:-1,previous:null};
      }}>Start 24-second pulse sample</button>
      {pulseTime!==null&&<p role="status">Collecting colour samples · {pulseTime}/24 s <button className="button secondary" onClick={()=>{pulseRun.current=null;setPulseTime(null);}}>Cancel sample</button></p>}
      {pulse&&<>
        <h3>{pulse.bpm===null?'Estimate withheld':pulse.bpm.toFixed(1)+' bpm · experimental estimate'}</h3>
        <p>{pulse.reason} {pulse.protocol} {pulse.duration_s.toFixed(1)} s, observed median sampling {pulse.sample_rate_hz.toFixed(1)} Hz. No reference reading in this run.</p>
        {pulse.rgb&&<details><summary>Inspect raw RGB and filtered signal</summary>
          {['Red','Green','Blue'].map((name,i)=><Trace key={name} values={pulse.rgb!.map(v=>v[i])} xLabel="seconds" xEnd={pulse.times?.at(-1)} title={name+' · mean intensity'} source="Live camera RGB"/>)}
          {pulse.filtered&&<Trace values={pulse.filtered} xLabel="seconds" xEnd={pulse.times?.at(-1)} title="Filtered normalized colour difference" source="Live camera RGB"/>}
          {pulse.power&&pulse.frequency_hz&&<Trace values={pulse.power} xLabel="pulse-band frequency (Hz)" xStart={pulse.frequency_hz[0]} xEnd={pulse.frequency_hz.at(-1)} title="Hann periodogram · relative peak structure" source="Live camera RGB"/>}
        </details>}
      </>}
      <p className="helper">Motion, flicker and camera auto-exposure can create a false peak. This experiment provides no diagnosis, clinical measurement or blood-pressure estimate.</p>
    </section>
  </div>;
}
