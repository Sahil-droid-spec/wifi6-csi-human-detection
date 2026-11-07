package lab.orbit.companion;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.pm.PackageManager;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.function.BooleanSupplier;
import org.json.JSONObject;

/** Foreground, user-confirmed PCM recording; no background service or key storage. */
public final class AudioBridge {
    private final Activity activity;
    private final WebView web;
    private final BooleanSupplier allowed;
    private volatile boolean recording=false, deliver=false, pending=false;
    private final Object captureLock=new Object();
    private AudioRecord active;
    private Thread worker;
    AudioBridge(Activity a,WebView w,BooleanSupplier check){activity=a;web=w;allowed=check;}
    private void event(String status,String error,String data){
        activity.runOnUiThread(()->{
            if(!allowed.getAsBoolean())return;
            try{JSONObject obj=new JSONObject();obj.put("status",status);if(error!=null)obj.put("error",error);if(data!=null)obj.put("base64",data);
                web.evaluateJavascript("window.dispatchEvent(new CustomEvent('orbit-audio',{detail:"+obj.toString()+"}));",null);
            }catch(Exception ignored){}
        });
    }
    @JavascriptInterface public void start(int seconds){final int limit=Math.max(1,Math.min(300,seconds));activity.runOnUiThread(()->{
        if(!allowed.getAsBoolean()||recording||pending||worker!=null&&worker.isAlive())return;
        pending=true;
        new AlertDialog.Builder(activity).setTitle("Record microphone?")
            .setMessage("Orbit will record while this screen stays open, for up to "+limit+" seconds. Stop to send the WAV to your paired laptop. Leaving the app discards this recording.")
            .setPositiveButton("Record",(dialog,which)->{
                pending=false;
                if(activity.checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){
                    activity.requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},620);
                    event("stopped","After granting permission, tap Record microphone again.",null);
                }else begin(limit);
            }).setNegativeButton("Cancel",(dialog,which)->pending=false).setOnCancelListener(dialog->pending=false).show();
    });}
    private void begin(int seconds){
        if(!allowed.getAsBoolean())return;
        recording=true;deliver=true;
        worker=new Thread(()->{
            AudioRecord recorder=null;
            try{
                int minimum=AudioRecord.getMinBufferSize(16000,AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT);
                if(minimum<=0)throw new Exception("This phone does not support 16 kHz PCM recording. Upload a WAV instead.");
                recorder=new AudioRecord(MediaRecorder.AudioSource.UNPROCESSED,16000,AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT,Math.max(8192,minimum*2));
                if(recorder.getState()!=AudioRecord.STATE_INITIALIZED)throw new Exception("Microphone could not start. Close other recording apps and try again.");
                ByteArrayOutputStream output=new ByteArrayOutputStream();byte[] buffer=new byte[4096];
                synchronized(captureLock){
                    if(!recording||!deliver)return;
                    active=recorder;recorder.startRecording();
                }
                event("recording",null,null);
                int cap=seconds*32000;
                while(recording&&output.size()<cap){int count=recorder.read(buffer,0,Math.min(buffer.length,cap-output.size()));if(count<=0){if(!recording)break;throw new Exception("No microphone samples. Stop and retry.");}output.write(buffer,0,count);}
                recording=false;
                if(deliver&&output.size()>=3200){
                    byte[] pcm=output.toByteArray();ByteBuffer wav=ByteBuffer.allocate(44+pcm.length).order(ByteOrder.LITTLE_ENDIAN);
                    wav.put(new byte[]{'R','I','F','F'}).putInt(36+pcm.length).put(new byte[]{'W','A','V','E','f','m','t',' '}).putInt(16).putShort((short)1).putShort((short)1).putInt(16000).putInt(32000).putShort((short)2).putShort((short)16).put(new byte[]{'d','a','t','a'}).putInt(pcm.length).put(pcm);
                    event("stopped",null,Base64.encodeToString(wav.array(),Base64.NO_WRAP));
                }else event("stopped",deliver?"Record at least 0.1 seconds before stopping.":null,null);
            }catch(Exception e){event("stopped",e.getMessage(),null);}
            finally{recording=false;synchronized(captureLock){active=null;if(recorder!=null){try{recorder.stop();}catch(Exception ignored){}recorder.release();}}}
        },"orbit-foreground-audio");worker.start();
    }
    @JavascriptInterface public void stop(){recording=false;}
    @JavascriptInterface public void cancel(){synchronized(captureLock){deliver=false;recording=false;if(active!=null){try{active.stop();}catch(Exception ignored){}}}}
}
