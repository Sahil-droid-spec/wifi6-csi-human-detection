package lab.orbit.companion;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.CookieManager;
import android.webkit.URLUtil;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceResponse;
import android.security.NetworkSecurityPolicy;
import java.io.ByteArrayInputStream;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.util.ArrayList;

/** Native phone companion. Scientific processing remains on the paired laptop. */
public class MainActivity extends Activity {
    private static final int PICK_FILE = 501;
    private static final int SAVE_FILE = 502;
    private LinearLayout root;
    private WebView web;
    private TextView status;
    private EditText address;
    private String base = "";
    private ValueCallback<Uri[]> fileCallback;
    private String downloadUrl;
    private String downloadCookie;
    private boolean pageError;
    private String launchUrl;
    private ArrayList<Uri> shared = new ArrayList<>();

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        handleIntent(getIntent());
    }

    @Override protected void onNewIntent(Intent intent){super.onNewIntent(intent);setIntent(intent);handleIntent(intent);}
    private void handleIntent(Intent intent){
        launchUrl=null;
        if(Intent.ACTION_SEND_MULTIPLE.equals(intent.getAction())){ArrayList<Uri> values=intent.getParcelableArrayListExtra(Intent.EXTRA_STREAM);if(values!=null)for(Uri u:values)if(shared.size()<32 && "content".equals(u.getScheme()))shared.add(u);}
        if(Intent.ACTION_SEND.equals(intent.getAction())){Uri u=intent.getParcelableExtra(Intent.EXTRA_STREAM);if(u!=null && "content".equals(u.getScheme()))shared.add(u);}
        String target=intent.getData()!=null?intent.getData().toString():intent.getStringExtra(Intent.EXTRA_TEXT);
        if(target!=null && target.startsWith("orbit://connect")) target=Uri.parse(target).getQueryParameter("url");
        String previous=getPreferences(MODE_PRIVATE).getString("server","");
        try{
            if(target!=null && target.startsWith("http://")){base=ServerAddress.normalize(target);if(!NetworkSecurityPolicy.getInstance().isCleartextTrafficPermitted(new URI(base).getHost()))throw new Exception("Laptop address changed; use the phone browser or an APK built for this LAN address.");launchUrl=target;getPreferences(MODE_PRIVATE).edit().putString("server",base).apply();showWorkspace();}
            else if(!previous.isEmpty()){base=ServerAddress.normalize(previous);showWorkspace();}
            else showConnect(null);
            if(!shared.isEmpty())Toast.makeText(this,shared.size()+" shared files ready. Open Import wizard and tap Choose files.",Toast.LENGTH_LONG).show();
        }catch(Exception e){showConnect(e.getMessage());}
    }

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    private LinearLayout column() {
        LinearLayout view = new LinearLayout(this);
        view.setOrientation(LinearLayout.VERTICAL);
        return view;
    }
    private TextView text(String value, int size, int color) {
        TextView view = new TextView(this);
        view.setText(value); view.setTextSize(size); view.setTextColor(color);
        view.setPadding(0, dp(8), 0, dp(8));
        return view;
    }
    private Button button(String label, View.OnClickListener action) {
        Button button = new Button(this);
        button.setText(label); button.setAllCaps(false); button.setTextColor(Color.rgb(26, 115, 232));
        button.setOnClickListener(action); return button;
    }
    private void setRoot(LinearLayout view) {
        root = view; root.setBackgroundColor(Color.rgb(246,248,252));
        root.setOnApplyWindowInsetsListener((v, insets) -> {
            v.setPadding(0, insets.getSystemWindowInsetTop(), 0, insets.getSystemWindowInsetBottom());
            return insets;
        });
        setContentView(root); root.requestApplyInsets();
    }
    private void destroyWeb() {
        if (web != null) { web.stopLoading(); web.destroy(); web = null; }
        if (fileCallback != null) { fileCallback.onReceiveValue(null); fileCallback = null; }
    }
    private void showConnect(String message) {
        destroyWeb();
        LinearLayout outer = column(); setRoot(outer);
        ScrollView scroll = new ScrollView(this); outer.addView(scroll);
        LinearLayout card = column(); card.setPadding(dp(26),dp(30),dp(26),dp(30)); scroll.addView(card);
        ImageView logo = new ImageView(this); logo.setImageResource(R.drawable.ic_orbit);
        card.addView(logo, new LinearLayout.LayoutParams(dp(76),dp(76)));
        TextView title = text("orbit",36,Color.rgb(35,52,73)); title.setTypeface(null,Typeface.BOLD); card.addView(title);
        card.addView(text("YOUR LOCAL LAB",11,Color.rgb(79,111,151)));
        card.addView(text("One lab. Two screens.",25,Color.rgb(35,52,73)));
        card.addView(text("Start Orbit on your laptop, connect both devices to the same Wi-Fi, then enter the laptop address shown in Server & settings.",15,Color.rgb(92,110,133)));
        address = new EditText(this); address.setSingleLine(true); address.setTextSize(16);
        address.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_VARIATION_URI);
        address.setHint("http://192.168.1.20:8765");
        address.setText(getPreferences(MODE_PRIVATE).getString("server", "")); card.addView(address);
        card.addView(button("Connect to my laptop", v -> connect()));
        card.addView(button("Save Simulation examples on this phone", v -> saveExample()));
        if (message != null) card.addView(text(message,14,Color.rgb(168,63,73)));
        card.addView(text("Scan the one-time QR in Connect to pair without typing a code. The phone gets the same library, DSP tools and model workspace while the laptop server runs.",14,Color.rgb(92,110,133)));
        card.addView(text("The laptop must remain on. This app transfers files and opens the local lab; it does not capture Wi-Fi CSI directly from your phone.",13,Color.rgb(92,110,133)));
    }
    private void saveExample(){
        String[] names={"Empty channel", "One person still", "One person moving", "Two people"};
        String[] files={"Simulation-Empty.zip","Simulation-One-Still.zip","Simulation-One-Moving.zip","Simulation-Two-People.zip"};
        new AlertDialog.Builder(this).setTitle("Generated Simulation data").setItems(names,(dialog,which)->{
            downloadUrl="asset:"+files[which];downloadCookie=null;
            Intent save=new Intent(Intent.ACTION_CREATE_DOCUMENT);save.addCategory(Intent.CATEGORY_OPENABLE);save.setType("application/zip");save.putExtra(Intent.EXTRA_TITLE,files[which]);
            try{startActivityForResult(save,SAVE_FILE);}catch(ActivityNotFoundException e){Toast.makeText(this,"Open this phone's document picker to save the example.",Toast.LENGTH_LONG).show();}
        }).show();
    }
    private void connect() {
        try {
            String entered=address.getText().toString();
            base=ServerAddress.normalize(entered);
            launchUrl=entered.contains("#/pair?")?entered:null;
            if(!NetworkSecurityPolicy.getInstance().isCleartextTrafficPermitted(new URI(base).getHost())) throw new Exception("This APK is restricted to the laptop addresses allowed at build time. Use the phone browser with the new LAN address, or rebuild the APK for that address.");
            getPreferences(MODE_PRIVATE).edit().putString("server",base).apply();
            showWorkspace();
        } catch(Exception e) { Toast.makeText(this,e.getMessage(),Toast.LENGTH_LONG).show(); }
    }
    private boolean isServerUrl(String value) {
        try { URI u=new URI(value), expected=new URI(base); return "http".equalsIgnoreCase(u.getScheme()) && expected.getHost().equals(u.getHost()) && expected.getPort()==u.getPort() && u.getRawUserInfo()==null; }
        catch(Exception e) { return false; }
    }
    private void showWorkspace() {
        LinearLayout outer=column(); setRoot(outer);
        LinearLayout toolbar=new LinearLayout(this); toolbar.setGravity(Gravity.CENTER_VERTICAL); toolbar.setPadding(dp(10),dp(2),dp(10),dp(2));
        TextView brand=text("orbit",21,Color.rgb(35,52,73)); brand.setTypeface(null,Typeface.BOLD);
        toolbar.addView(brand,new LinearLayout.LayoutParams(0,dp(50),1));
        toolbar.addView(button("Upload",v -> web.loadUrl(base+"/#/upload")));
        toolbar.addView(button("Inbox",v -> web.loadUrl(base+"/#/inbox")));
        toolbar.addView(button("Connect",v -> showConnect(null)));
        outer.addView(toolbar);
        status=text("Connecting to "+base,11,Color.rgb(92,110,133)); status.setPadding(dp(12),0,dp(12),dp(5)); outer.addView(status);
        web=new WebView(this); outer.addView(web,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,0,1));
        WebSettings settings=web.getSettings(); settings.setJavaScriptEnabled(true); settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false); settings.setAllowContentAccess(true);
        settings.setAllowFileAccessFromFileURLs(false); settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        CookieManager.getInstance().setAcceptCookie(true); CookieManager.getInstance().setAcceptThirdPartyCookies(web,false);
        web.setWebChromeClient(new WebChromeClient(){
            @Override public boolean onShowFileChooser(WebView view,ValueCallback<Uri[]> callback,FileChooserParams params){
                if(!shared.isEmpty()){callback.onReceiveValue(shared.toArray(new Uri[0]));shared.clear();return true;}
                if(fileCallback!=null) fileCallback.onReceiveValue(null); fileCallback=callback;
                Intent picker=new Intent(Intent.ACTION_OPEN_DOCUMENT);picker.addCategory(Intent.CATEGORY_OPENABLE);picker.setType("*/*");
                ArrayList<String> types=new ArrayList<>();
                for(String accept:params.getAcceptTypes())if(accept!=null)for(String type:accept.split(",")){type=type.trim();if(type.contains("/") && !type.startsWith("."))types.add(type);}
                boolean mediaOnly=!types.isEmpty();for(String type:types)if(!(type.startsWith("image/")||type.startsWith("video/")||type.startsWith("audio/")))mediaOnly=false;
                // MAT extensions do not have a reliable Android MIME type. Keep the generic document picker for CSI files.
                if(mediaOnly && types.size()==1)picker.setType(types.get(0));else if(mediaOnly)picker.putExtra(Intent.EXTRA_MIME_TYPES,types.toArray(new String[0]));
                picker.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,params.getMode()==FileChooserParams.MODE_OPEN_MULTIPLE);
                try{startActivityForResult(picker,PICK_FILE);}catch(ActivityNotFoundException e){fileCallback.onReceiveValue(null);fileCallback=null;Toast.makeText(MainActivity.this,"No file picker is available on this phone.",Toast.LENGTH_LONG).show();}
                return true;
            }
        });
        web.setWebViewClient(new WebViewClient(){
            @Override public WebResourceResponse shouldInterceptRequest(WebView view,WebResourceRequest request){
                if(isServerUrl(request.getUrl().toString()))return null;
                return new WebResourceResponse("text/plain","UTF-8",403,"Blocked",java.util.Collections.emptyMap(),new ByteArrayInputStream(new byte[0]));
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest request){
                String url=request.getUrl().toString(); if(isServerUrl(url))return false;
                if(request.hasGesture() && ("https".equals(request.getUrl().getScheme()) || "http".equals(request.getUrl().getScheme()))) {
                    try{startActivity(new Intent(Intent.ACTION_VIEW,request.getUrl()));}catch(ActivityNotFoundException ignored){}
                }
                return true;
            }
            @Override public void onPageStarted(WebView view,String url,android.graphics.Bitmap icon){pageError=false;status.setText("Connecting to "+base);}
            @Override public void onPageFinished(WebView view,String url){if(!pageError)status.setText("Laptop workspace · "+base);CookieManager.getInstance().flush();}
            @Override public void onReceivedError(WebView view,WebResourceRequest request,WebResourceError error){
                if(request.isForMainFrame()){pageError=true;status.setText("Cannot reach laptop. Check Wi-Fi, server sharing, address and private-network firewall permission. Tap Laptop to edit.");}
            }
        });
        web.setDownloadListener((url,userAgent,contentDisposition,mimeType,length)->{
            if(!isServerUrl(url)){Toast.makeText(this,"Only paired-laptop downloads are supported.",Toast.LENGTH_LONG).show();return;}
            downloadUrl=url;downloadCookie=CookieManager.getInstance().getCookie(url);
            Intent save=new Intent(Intent.ACTION_CREATE_DOCUMENT);save.addCategory(Intent.CATEGORY_OPENABLE);
            save.setType(mimeType==null?"application/octet-stream":mimeType);save.putExtra(Intent.EXTRA_TITLE,URLUtil.guessFileName(url,contentDisposition,mimeType));
            try{startActivityForResult(save,SAVE_FILE);}catch(ActivityNotFoundException e){Toast.makeText(this,"No document save picker is available. Open Orbit in your phone browser to download.",Toast.LENGTH_LONG).show();}
        });
        web.loadUrl(launchUrl!=null && isServerUrl(launchUrl)?launchUrl:base+"/#/overview");
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request==PICK_FILE && fileCallback!=null){
            Uri[] values=null;
            if(result==RESULT_OK && data!=null){
                if(data.getClipData()!=null){values=new Uri[data.getClipData().getItemCount()];for(int i=0;i<values.length;i++)values[i]=data.getClipData().getItemAt(i).getUri();}
                else if(data.getData()!=null)values=new Uri[]{data.getData()};
            }
            fileCallback.onReceiveValue(values);fileCallback=null;
        }
        if(request==SAVE_FILE && result==RESULT_OK && data!=null && data.getData()!=null && downloadUrl!=null){
            Uri target=data.getData();String url=downloadUrl,cookie=downloadCookie;downloadUrl=null;downloadCookie=null;
            Toast.makeText(this,"Saving file from laptop…",Toast.LENGTH_SHORT).show();
            new Thread(()->{
                HttpURLConnection connection=null;
                try{
                    if(url.startsWith("asset:")){
                        try(InputStream input=getAssets().open(url.substring(6));OutputStream output=getContentResolver().openOutputStream(target,"w")){
                            if(output==null)throw new Exception("Cannot save this example.");byte[] buffer=new byte[65536];int read;while((read=input.read(buffer))!=-1)output.write(buffer,0,read);
                        }
                        runOnUiThread(()->Toast.makeText(this,"Simulation example saved on this phone. Pair with your laptop, then upload it from Import wizard.",Toast.LENGTH_LONG).show());return;
                    }
                    connection=(HttpURLConnection)new URL(url).openConnection();connection.setInstanceFollowRedirects(false);connection.setConnectTimeout(15000);connection.setReadTimeout(60000);
                    if(cookie!=null)connection.setRequestProperty("Cookie",cookie);
                    if(connection.getResponseCode()!=200)throw new Exception("Download failed. Reconnect and enter the laptop access code first.");
                    try(InputStream input=connection.getInputStream();OutputStream output=getContentResolver().openOutputStream(target,"w")){
                        if(output==null)throw new Exception("Cannot write the selected file.");byte[] buffer=new byte[65536];int read;while((read=input.read(buffer))!=-1)output.write(buffer,0,read);
                    }
                    runOnUiThread(()->Toast.makeText(this,"Saved. You can now select this file for upload.",Toast.LENGTH_LONG).show());
                }catch(Exception e){runOnUiThread(()->Toast.makeText(this,e.getMessage(),Toast.LENGTH_LONG).show());}
                finally{if(connection!=null)connection.disconnect();}
            },"orbit-download").start();
        }
    }
    @Override public void onBackPressed(){if(web!=null && web.canGoBack())web.goBack();else if(web!=null)showConnect(null);else super.onBackPressed();}
    @Override protected void onDestroy(){destroyWeb();super.onDestroy();}
}
