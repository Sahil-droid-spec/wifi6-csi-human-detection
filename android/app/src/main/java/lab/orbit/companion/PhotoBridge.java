package lab.orbit.companion;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Bitmap;
import android.provider.MediaStore;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import java.io.ByteArrayOutputStream;
import java.util.function.BooleanSupplier;
import org.json.JSONObject;

/** System camera owns capture/confirmation; only an explicit accepted thumbnail is returned. */
public final class PhotoBridge {
    static final int REQUEST=503;
    private final Activity activity;private final WebView web;private final BooleanSupplier allowed;
    PhotoBridge(Activity a,WebView w,BooleanSupplier check){activity=a;web=w;allowed=check;}
    @JavascriptInterface public void capture(){activity.runOnUiThread(()->{
        if(!allowed.getAsBoolean())return;
        new AlertDialog.Builder(activity).setTitle("Take a phone photo?").setMessage("The system camera opens. Only a photo you accept returns to Orbit for preview. Save is a separate action. This is not a retinal camera.")
            .setPositiveButton("Open camera",(d,n)->{try{activity.startActivityForResult(new Intent(MediaStore.ACTION_IMAGE_CAPTURE),REQUEST);}catch(Exception e){event(null,"No system camera app. Use Choose/import image instead.");}}).setNegativeButton("Cancel",null).show();
    });}
    void result(int result,Intent data){
        if(!allowed.getAsBoolean()||result!=Activity.RESULT_OK||data==null||data.getExtras()==null)return;
        Object object=data.getExtras().get("data");if(!(object instanceof Bitmap)){event(null,"This camera did not return a thumbnail. Save the photo with your camera app and import it.");return;}
        Bitmap bitmap=(Bitmap)object;ByteArrayOutputStream raw=new ByteArrayOutputStream();bitmap.compress(Bitmap.CompressFormat.JPEG,85,raw);
        event(Base64.encodeToString(raw.toByteArray(),Base64.NO_WRAP),null);
    }
    private void event(String image,String error){try{JSONObject d=new JSONObject();if(image!=null)d.put("base64",image);if(error!=null)d.put("error",error);web.evaluateJavascript("window.dispatchEvent(new CustomEvent('orbit-photo',{detail:"+d.toString()+"}));",null);}catch(Exception ignored){}}
}
