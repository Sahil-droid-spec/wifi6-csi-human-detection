import {useEffect,useRef,useState} from 'react';
import {workApi} from './Workbench';
type D=Record<string,any>;
export function LiveConnection(){
  const [code,setCode]=useState(''),[joined,setJoined]=useState(false),[consent,setConsent]=useState(false),[videoEnabled,setVideoEnabled]=useState(true);
  const [status,setStatus]=useState('Not joined'),[error,setError]=useState(''),[incoming,setIncoming]=useState<D|null>(null),[stats,setStats]=useState<D|null>(null);
  const local=useRef<HTMLVideoElement>(null),remote=useRef<HTMLVideoElement>(null),pc=useRef<RTCPeerConnection|null>(null),media=useRef<MediaStream|null>(null);
  const cursor=useRef(0),candidates=useRef<RTCIceCandidateInit[]>([]),room=useRef(''),alive=useRef(true),busy=useRef(false);
  const secure=window.isSecureContext&&!!navigator.mediaDevices?.getUserMedia;
  function release(){pc.current?.close();pc.current=null;media.current?.getTracks().forEach(t=>t.stop());media.current=null;if(local.current)local.current.srcObject=null;if(remote.current)remote.current.srcObject=null;candidates.current=[];setIncoming(null);}
  function hangup(){const current=room.current;release();setJoined(false);setStatus('Stopped · microphone and camera released');if(current)workApi('live/rooms/'+current+'/member','DELETE').catch(()=>{});room.current='';}
  useEffect(()=>{alive.current=true;const hidden=()=>{if(document.hidden)hangup();};document.addEventListener('visibilitychange',hidden);window.addEventListener('orbit-native-background',hangup);return()=>{alive.current=false;window.removeEventListener('orbit-native-background',hangup);document.removeEventListener('visibilitychange',hidden);hangup();};},[]);
  const send=(kind:string,payload:D)=>workApi('live/rooms/'+room.current+'/signal','POST',{kind,payload});
  async function flush(){if(pc.current?.remoteDescription)while(candidates.current.length)await pc.current.addIceCandidate(candidates.current.shift()!);}
  useEffect(()=>{
    if(!joined)return;let running=false;
    const timer=setInterval(async()=>{if(running)return;running=true;try{
      const r=await workApi('live/rooms/'+room.current+'?after='+cursor.current);cursor.current=r.cursor;
      for(const s of r.signals){if(s.kind==='offer')setIncoming(s.payload);else if(s.kind==='answer'&&pc.current){await pc.current.setRemoteDescription(s.payload);await flush();}else if(s.kind==='ice'){candidates.current.push(s.payload);await flush();}else if(s.kind==='hangup'){release();setStatus('Other device ended the call');}}
      if(pc.current){const reports=await pc.current.getStats();let sent=0,received=0;reports.forEach(s=>{if(s.type==='outbound-rtp')sent+=s.bytesSent||0;if(s.type==='inbound-rtp')received+=s.bytesReceived||0;});setStats({sent,received});}
    }catch(e){if(alive.current)setError((e as Error).message);}finally{running=false;}},1000);
    return()=>clearInterval(timer);
  },[joined]);
  async function peer(){
    if(!secure)throw Error('Live browser calls need HTTPS trusted by both devices or localhost. Phone LAN HTTP cannot grant browser media. Use the APK voice-note/photo controls, or configure trusted HTTPS; no browser security bypass is applied.');
    const stream=await navigator.mediaDevices.getUserMedia({audio:true,video:videoEnabled});if(!alive.current){stream.getTracks().forEach(t=>t.stop());throw Error('Call page closed.');}
    media.current=stream;if(local.current)local.current.srcObject=stream;
    const connection=new RTCPeerConnection({iceServers:[]});pc.current=connection;for(const track of stream.getTracks())connection.addTrack(track,stream);
    connection.onicecandidate=e=>{if(e.candidate)send('ice',e.candidate.toJSON()).catch(err=>setError(err.message));};
    connection.ontrack=e=>{if(remote.current)remote.current.srcObject=e.streams[0];};
    connection.onconnectionstatechange=()=>setStatus('WebRTC '+connection.connectionState);
    return connection;
  }
  async function run(fn:()=>Promise<void>){if(busy.current)return;busy.current=true;setError('');try{await fn();}catch(e){release();setError((e as Error).message);}finally{busy.current=false;}}
  return <section className="panel"><h2>Two-device calls &amp; camera sharing</h2><p>Local signaling, browser WebRTC audio/video, no external STUN/TURN service. Both devices must explicitly join and grant media permission. Calls are not recorded or saved automatically.</p>
    {!secure&&<p>PERMISSION REQUIRED: this HTTP phone context cannot use browser live media. Native APK voice notes and photo capture remain available in Record &amp; preview. Full browser calls require a trusted secure context.</p>}
    <label>Call code<input value={code} maxLength={8} onChange={e=>setCode(e.target.value.toUpperCase())}/></label>
    <label><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/> I want to join and share microphone/camera with the paired device</label>
    <label><input type="checkbox" checked={videoEnabled} disabled={!!pc.current} onChange={e=>setVideoEnabled(e.target.checked)}/> Include camera video</label>
    <div className="button-row"><button className="button secondary" disabled={joined} onClick={()=>run(async()=>{const r=await workApi('live/rooms','POST',{});setCode(r.code);setStatus('Share this code with your paired phone; expires in 30 minutes');})}>Create call code · laptop</button>
    <button className="button secondary" disabled={!consent||code.length!==8||joined} onClick={()=>run(async()=>{await workApi('live/rooms/'+code+'/join','POST',{consent});room.current=code;cursor.current=0;setJoined(true);setStatus('Signaling joined; media not connected yet');})}>Join code</button>
    <button className="button" disabled={!joined||!secure||!!pc.current} onClick={()=>run(async()=>{const p=await peer();const offer=await p.createOffer();await p.setLocalDescription(offer);await send('offer',offer as unknown as D);setStatus('Calling · awaiting explicit acceptance');})}>Start call · request permission</button>
    {incoming&&<button className="button" disabled={!secure||!joined} onClick={()=>run(async()=>{const p=await peer();await p.setRemoteDescription(incoming as RTCSessionDescriptionInit);await flush();const answer=await p.createAnswer();await p.setLocalDescription(answer);await send('answer',answer as unknown as D);setIncoming(null);})}>Accept incoming call · request permission</button>}
    <button className="button secondary" disabled={!joined} onClick={hangup}>Hang up / leave</button></div>
    <p role="status">{status}</p>{error&&<p role="alert">{error}</p>}
    <div className="control-grid"><div><p>Your preview · muted</p><video ref={local} autoPlay muted playsInline style={{width:'100%'}}/></div><div><p>Other device · press play if autoplay is blocked</p><video ref={remote} autoPlay controls playsInline style={{width:'100%'}}/></div></div>
    {stats&&<p>Browser RTP counters: {stats.sent} bytes sent, {stats.received} bytes received. These are browser media counters, not RF strength or Wi-Fi 6 PHY measurements.</p>}
    <p>Physical two-device call acceptance remains required. LAN client isolation, firewalls and unsupported codecs can prevent a connection; no successful call is inferred from joining the signaling room.</p>
  </section>;
}
