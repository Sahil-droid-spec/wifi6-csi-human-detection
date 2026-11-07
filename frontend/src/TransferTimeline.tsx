import {useEffect,useState} from 'react';

type Timeline = {
  points:{elapsed_s:number,accepted_bytes:number}[];
  elapsed_s:number|null;
  observed_bytes:number;
  total_bytes:number;
  average_bytes_per_s:number|null;
  last_interval_bytes_per_s:number|null;
  offset_conflicts:number;
  status:string;
  verified:boolean;
  protocol:string;
};

export function TransferTimeline({id,name}:{id:string,name:string}){
  const [data,setData]=useState<Timeline|null>(null),[error,setError]=useState(false);
  useEffect(()=>{
    const controller=new AbortController();
    let timer:ReturnType<typeof setTimeout>;
    async function refresh(){
      try{
        const response=await fetch('/api/exchange/files/'+id+'/timeline',{signal:controller.signal});
        if(!response.ok)throw Error();
        const next:Timeline=await response.json();
        if(controller.signal.aborted)return;
        setData(next);setError(false);
        if(next.status==='uploading')timer=setTimeout(refresh,650);
      }catch{
        if(!controller.signal.aborted){setError(true);timer=setTimeout(refresh,2000);}
      }
    }
    setData(null);setError(false);void refresh();
    return()=>{controller.abort();clearTimeout(timer);};
  },[id]);
  const final=data?.points.at(-1),end=data?.elapsed_s||1,total=data?.total_bytes||1;
  const points=data?.points.map(p=>[45+p.elapsed_s/end*550,135-p.accepted_bytes/total*100].join(',')).join(' ');
  const speed=(value:number|null)=>value===null?'—':(value/1024).toFixed(1)+' KiB/s';
  return <section className="exchange-timeline" aria-label="Transfer progress graph">
    <h3>{name} · upload timeline</h3>
    {error&&<p role="status">Connection interrupted. Trying to refresh the graph.</p>}
    {!data?<p>Loading server measurements…</p>:data.points.length<2?
      <p>{data.status==='uploading'?'Waiting for the first accepted chunk.':'This upload has no measured chunk history.'}</p>:
      <>
        <svg viewBox="0 0 640 175" role="img" aria-label="Cumulative accepted bytes versus elapsed seconds">
          <path d="M45 30V135H595" fill="none" stroke="currentColor" opacity=".45"/>
          <polyline points={points} fill="none" stroke="var(--blue)" strokeWidth="3"/>
          <text x="45" y="22" fill="currentColor">{final?.accepted_bytes.toLocaleString()} / {data.total_bytes.toLocaleString()} accepted bytes</text>
          <text x="45" y="158" fill="currentColor">0 s</text>
          <text x="595" y="158" textAnchor="end" fill="currentColor">{data.elapsed_s?.toFixed(2)} s</text>
        </svg>
        <p>{data.observed_bytes.toLocaleString()} observed bytes · {data.elapsed_s?.toFixed(2)} s · average {speed(data.average_bytes_per_s)} · latest interval {speed(data.last_interval_bytes_per_s)}.</p>
      </>}
    {data&&<p className="helper">{data.verified?'SHA-256 matched · ':data.status==='cancelled'?'Cancelled · ':''}{data.offset_conflicts} rejected offsets. {data.protocol} Application transfer only.</p>}
  </section>;
}
