import {useEffect,useMemo,useRef} from 'react';
import {useFrame,useLoader} from '@react-three/fiber';
import {AnimationMixer,Box3,Color,Group,Mesh,MeshStandardMaterial,Quaternion,SkeletonHelper,Vector3} from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone} from 'three/addons/utils/SkeletonUtils.js';

/** Quaternius Universal Animation Library mannequin and clips, CC0. Bundled offline.
 * Root-motion-free rig. ORBIT supplies position, materials and shared timing.
 */
export function RiggedHuman({position,phase,color,style,moving,playing=true,activity='walking',joints=false,onSelect}:{position:number[];phase:number;color:string;style:string;moving:boolean;playing?:boolean;activity?:string;joints?:boolean;onSelect?:()=>void}){
 const [gltf,animationLibrary]=useLoader(GLTFLoader,['/models/Orbit-Human.glb','/models/Orbit-Mannequin.glb']);
 const root=useRef<Group>(null),latest=useRef({position,phase,playing});latest.current={position,phase,playing};
 const model=useMemo(()=>{
  const scene=clone(gltf.scene),materials:MeshStandardMaterial[]=[];
  scene.traverse(o=>{if(o instanceof Mesh){const original=Array.isArray(o.material)?o.material:[o.material];const replacements=original.map((m,i)=>{const material=new MeshStandardMaterial({color:new Color(o.name.toLowerCase().includes('eye')?(o.name.toLowerCase().includes('brow')?'#18263c':'#e7e7e7'):color),roughness:.62,metalness:.08,wireframe:style==='wireframe',transparent:style==='hologram'||style==='skeleton',opacity:style==='skeleton'?0:style==='hologram'?.52:1,emissive:color,emissiveIntensity:style==='hologram'?.2:.01});materials.push(material);return material;});o.material=Array.isArray(o.material)?replacements:replacements[0];o.castShadow=style!=='skeleton';o.receiveShadow=true;}});
  scene.updateMatrixWorld(true);const box=new Box3().setFromObject(scene),scale=1.78/box.getSize(new Vector3()).y;scene.scale.multiplyScalar(scale);scene.position.y-=box.min.y*scale;
  const mixer=new AnimationMixer(scene);
  const clips={idle:animationLibrary.animations.find(a=>a.name==='Idle_Loop')!,walk:animationLibrary.animations.find(a=>a.name==='Walk_Loop')!,run:animationLibrary.animations.find(a=>a.name==='Jog_Fwd_Loop')!,hand:animationLibrary.animations.find(a=>a.name==='Idle_Talking_Loop')!};
  const actions={idle:mixer.clipAction(clips.idle),walk:mixer.clipAction(clips.walk),run:mixer.clipAction(clips.run),hand:mixer.clipAction(clips.hand)};
  actions.idle.play();const skeleton=new SkeletonHelper(scene);return {scene,mixer,clips,actions,materials,skeleton};
 },[gltf,animationLibrary,color,style]);
 const mode=activity==='hand'?'hand':moving?(activity==='running'?'run':'walk'):'idle';
 const previousModel=useRef<typeof model|null>(null),previousMode=useRef('');
 useEffect(()=>{const target=model.actions[mode],crossfade=previousModel.current===model&&previousMode.current!==mode&&latest.current.playing;Object.values(model.actions).forEach(a=>{if(a!==target){if(crossfade)a.fadeOut(.4);else a.stop();}});target.reset().setEffectiveWeight(1).play();if(crossfade)target.fadeIn(.4);previousModel.current=model;previousMode.current=mode;},[mode,model]);
 useEffect(()=>()=>{model.mixer.stopAllAction();model.mixer.uncacheRoot(model.scene);model.materials.forEach(m=>m.dispose());model.skeleton.dispose();},[model]);
 const ready=useRef(false);
 useFrame((_,dt)=>{const data=latest.current,g=root.current;if(!g)return;const target=new Vector3(data.position[0]||0,0,data.position[1]||0),q=new Quaternion().setFromAxisAngle(new Vector3(0,1,0),data.position[2]||0);
  const blend=!ready.current||!data.playing?1:1-Math.exp(-14*Math.min(dt,.1));g.position.lerp(target,blend);g.quaternion.slerp(q,blend);ready.current=true;
  model.actions[mode].time=data.phase%model.clips[mode].duration;model.mixer.update(data.playing?Math.min(dt,.5):0);
 });
 return <group ref={root} onClick={e=>{e.stopPropagation();onSelect?.();}}><primitive object={model.scene}/>{(joints||style==='skeleton')&&<primitive object={model.skeleton}/>}</group>;
}
