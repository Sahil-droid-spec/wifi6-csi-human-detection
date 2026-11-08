import {useEffect,useRef,useState} from 'react';

declare global {interface Window {OrbitAudio?:{start:(seconds:number)=>void,stop:()=>void,cancel:()=>void}}}

export function pcmWav(a:Float32Array,rate:number){
  const b=new ArrayBuffer(44+a.length*2),v=new DataView(b);
  const str=(i:number,s:string)=>{for(let j=0;j<s.length;j++)v.setUint8(i+j,s.charCodeAt(j));};
  str(0,'RIFF');v.setUint32(4,36+a.length*2,true);str(8,'WAVE');str(12,'fmt ');v.setUint32(16,16,true);
  v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,rate,true);v.setUint32(28,rate*2,true);
  v.setUint16(32,2,true);v.setUint16(34,16,true);str(36,'data');v.setUint32(40,a.length*2,true);
  for(let i=0;i<a.length;i++)v.setInt16(44+i*2,Math.max(-1,Math.min(1,a[i]))*32767,true);
  return new File([b],'microphone.wav',{type:'audio/wav'});
}

export function AudioRecorder({onAudio,maxSeconds=60}:{onAudio:(file:File)=>void,maxSeconds?:number}){
  const [recording,setRecording]=useState(false),[error,setError]=useState('');
  const ref=useRef<any>(null),alive=useRef(true),nativeActive=useRef(false),callback=useRef(onAudio);callback.current=onAudio;
  const native=!!window.OrbitAudio,secure=window.isSecureContext&&!!navigator.mediaDevices?.getUserMedia;
  const dispose=async(deliver:boolean)=>{
    const q=ref.current;ref.current=null;setRecording(false);if(!q)return;
    clearTimeout(q.timer);q.node.disconnect();q.input.disconnect();q.stream.getTracks().forEach((t:MediaStreamTrack)=>t.stop());await q.ctx.close();
    if(deliver&&q.length&&alive.current){const a=new Float32Array(q.length);let n=0;for(const chunk of q.chunks){a.set(chunk,n);n+=chunk.length;}callback.current(pcmWav(a,q.rate));}
  };
  useEffect(()=>{
    alive.current=true;
    const event=(e:Event)=>{if(!nativeActive.current)return;const d=(e as CustomEvent).detail;setRecording(d.status==='recording');
      if(d.status==='stopped')nativeActive.current=false;
      if(d.error)setError(d.error);
      if(d.base64){const raw=atob(d.base64),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));callback.current(new File([bytes],'phone-microphone.wav',{type:'audio/wav'}));}
    };
    window.addEventListener('orbit-audio',event);
    const hidden=()=>{if(document.hidden){nativeActive.current=false;window.OrbitAudio?.cancel();dispose(false);}};
    document.addEventListener('visibilitychange',hidden);
    return()=>{alive.current=false;document.removeEventListener('visibilitychange',hidden);window.removeEventListener('orbit-audio',event);window.OrbitAudio?.cancel();const q=ref.current;ref.current=null;if(q){clearTimeout(q.timer);q.node.disconnect();q.stream.getTracks().forEach((t:MediaStreamTrack)=>t.stop());q.ctx.close();}};
  },[]);
  async function start(){
    setError('');if(native){nativeActive.current=true;window.OrbitAudio!.start(maxSeconds);return;}
    let stream:MediaStream|undefined,ctx:AudioContext|undefined;
    try{
      stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:false,noiseSuppression:false,autoGainControl:false}});
      if(!alive.current||document.hidden){stream.getTracks().forEach(t=>t.stop());return;}
      ctx=new AudioContext();await ctx.resume();if(!alive.current||document.hidden){stream.getTracks().forEach(t=>t.stop());await ctx.close();return;}const input=ctx.createMediaStreamSource(stream),node=ctx.createScriptProcessor(4096,1,1);
      const q={stream,ctx,input,node,rate:ctx.sampleRate,chunks:[] as Float32Array[],length:0,timer:0};ref.current=q;
      node.onaudioprocess=e=>{if(ref.current!==q)return;const input=e.inputBuffer.getChannelData(0),remaining=Math.max(0,Math.floor(q.rate*maxSeconds)-q.length);const a=new Float32Array(input.subarray(0,remaining));if(a.length){q.chunks.push(a);q.length+=a.length;}if(q.length>=q.rate*maxSeconds)dispose(true);};
      input.connect(node);node.connect(ctx.destination);setRecording(true);q.timer=window.setTimeout(()=>dispose(true),maxSeconds*1000);
    }catch{stream?.getTracks().forEach(t=>t.stop());ctx?.close();setError('Allow microphone access, or choose a PCM WAV recorded with another app.');}
  }
  return <div><div className="button-row"><button className="button secondary" disabled={recording||(!native&&!secure)} onClick={start}>Record microphone · asks permission</button>
    <button className="button" disabled={!recording} onClick={()=>native?window.OrbitAudio!.stop():dispose(true)}>Stop &amp; use recording</button></div>
    {recording&&<p role="status">Microphone recording in progress. Keep this page open. Maximum {maxSeconds} seconds.</p>}
    {!native&&!secure&&<p>Phone browser HTTP blocks microphone access. Use the updated APK recorder or upload an existing WAV.</p>}
    {error&&<p role="alert">{error}</p>}</div>;
}
