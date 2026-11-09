import test from 'node:test';
import assert from 'node:assert/strict';
import {advanceTimeline,packetAt,heldOutAt,qualityAt,scenarioForFrame} from '../.timeline-test/sensingTimeline.js';

test('packet cursor clamps to the same finite buffer for scene, plots and verdict',()=>{
  assert.equal(packetAt(40.9,100),40);assert.equal(packetAt(-4,100),0);
  assert.equal(packetAt(500,100),99);assert.equal(packetAt(NaN,100),0);
});
test('playback rate and speed advance the same cursor and stop without wrapping',()=>{
  assert.deepEqual(advanceTimeline(0,.25,100,2,100),{cursor:50,ended:false});
  assert.deepEqual(advanceTimeline(90,1,100,.25,100),{cursor:99,ended:true});
  for(const rate of [0,-1,NaN])assert.throws(()=>advanceTimeline(0,1,rate,1,100));
});
test('held-out window lookup excludes end, gaps, other captures and seen-data inference',()=>{
  const r={capture_id:'recording-a',mode:'held_out',windows:[{start:32,end:64,prediction:1},{start:96,end:128,prediction:0}]};
  assert.equal(heldOutAt(r,32,'recording-a').prediction,1);
  assert.equal(heldOutAt(r,63,'recording-a').prediction,1);
  assert.equal(heldOutAt(r,64,'recording-a'),null);assert.equal(heldOutAt(r,70,'recording-a'),null);
  assert.equal(heldOutAt(r,96,'recording-a').prediction,0);
  assert.equal(heldOutAt(r,32,'recording-b'),null);
  assert.equal(heldOutAt({...r,mode:'final_model'},32,'recording-a'),null);
});
test('quality state distinguishes warm-up, missing packet, gap-affected window and usable',()=>{
  const trace=Array(40).fill(1),score=Array(40).fill(null);score[35]=.2;trace[25]=null;
  assert.equal(qualityAt(trace,score,0),'Collecting 16 valid packets');
  assert.equal(qualityAt(trace,score,25),'Window skipped · quality');
  assert.equal(qualityAt(trace,score,30),'Window skipped · quality');
  assert.equal(qualityAt(trace,score,35),'usable');
});
test('recorded avatars reflect an actual valid decision, while simulation remains explicit ground truth',()=>{
  const yes={start:0,end:32,prediction:1},no={...yes,prediction:0};
  assert.equal(scenarioForFrame(undefined,null,true),'unknown');
  assert.equal(scenarioForFrame(undefined,yes,false),'unknown');
  assert.equal(scenarioForFrame(undefined,yes,true),'still');
  assert.equal(scenarioForFrame(undefined,no,true),'empty');
  assert.equal(scenarioForFrame('walking',no,true),'walking');
});
