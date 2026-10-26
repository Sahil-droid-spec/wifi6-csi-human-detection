# Orbit Android companion
Native Android WebView companion for the paired local laptop server. It supports private IPv4 addresses, Orbit login, Android file selection/upload and authenticated downloads saved through Android's document UI. It does not contain Python models or acquire CSI from a phone's Wi-Fi chipset. Only INTERNET permission is requested; record media with the phone camera app, then select it for upload.

Intended minimum: Android 8/API 26 with up-to-date Android System WebView. Compile/target SDK: 35. The classroom APK uses a local test signing key. Verification covers v2/v3 signatures, alignment, package metadata and 13 address-parser cases. Physical-device runtime validation is still needed.

Build with official Android SDK Build Tools 35, Android 35 android.jar and portable JDK 17+:
python android/build_apk.py --jdk PATH_TO_JDK --build-tools PATH_TO_BUILD_TOOLS --android-jar PATH_TO_ANDROID_JAR --output PATH_TO_APK --keystore PATH_TO_LOCAL_TEST_P12

The script uses AAPT2, javac, D8, zipalign and apksigner. Keep signing material outside Git. The script's android password is for a disposable classroom test key, not a production signing process. Use managed private signing for a release. A different signing key cannot update an already installed app signed by the old key.

Phone and laptop must share a trusted network. Start laptop LAN mode, enter its LAN URL in the APK, then enter the terminal access code. The laptop must stay running.


Step 1: build with --lan-host for each exact RFC1918 laptop IPv4 allowed for HTTP. Default cleartext is denied; WebView subresources stay on the paired origin. Changed IP: rebuild the APK or use the browser. Physical-device policy verification: NOT EXECUTED.
