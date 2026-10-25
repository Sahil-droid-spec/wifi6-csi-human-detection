"""Build Orbit's small Android companion with official Android SDK tools and JDK 17+."""

import argparse, os, pathlib, subprocess, zipfile, json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jdk", required=True)
    parser.add_argument("--build-tools", required=True)
    parser.add_argument("--android-jar", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--keystore", required=True)
    args = parser.parse_args()
    root = pathlib.Path(__file__).resolve().parent
    build = root / "build"
    build.mkdir(exist_ok=True)
    classes = build / "classes"
    classes.mkdir(exist_ok=True)
    generated = build / "generated"
    generated.mkdir(exist_ok=True)
    dex = build / "dex"
    dex.mkdir(exist_ok=True)
    jdk = pathlib.Path(args.jdk).resolve()
    tools = pathlib.Path(args.build_tools).resolve()
    android = pathlib.Path(args.android_jar).resolve()
    suffix = ".exe" if os.name == "nt" else ""
    java = jdk / "bin" / ("java" + suffix)
    javac = jdk / "bin" / ("javac" + suffix)
    keytool = jdk / "bin" / ("keytool" + suffix)

    def run(parts):
        print(
            "RUN",
            pathlib.Path(str(parts[0])).name,
            " ".join(str(v) for v in parts[1:3]),
            flush=True,
        )
        subprocess.run([str(v) for v in parts], check=True, cwd=root)

    # SDK package: no Gradle daemon or system-wide tool installation needed.
    resources = build / "resources.zip"
    unsigned = build / "unsigned.apk"
    aligned = build / "aligned.apk"
    run(
        [
            tools / ("aapt2" + suffix),
            "compile",
            "--dir",
            root / "app/src/main/res",
            "-o",
            resources,
        ]
    )
    run(
        [
            tools / ("aapt2" + suffix),
            "link",
            "-o",
            unsigned,
            "--manifest",
            root / "app/src/main/AndroidManifest.xml",
            "-I",
            android,
            "--java",
            generated,
            "--auto-add-overlay",
            resources,
        ]
    )
    sources = list((root / "app/src/main/java").rglob("*.java")) + list(
        generated.rglob("*.java")
    )
    run(
        [
            javac,
            "--release",
            "8",
            "-encoding",
            "UTF-8",
            "-classpath",
            android,
            "-d",
            classes,
            *sources,
        ]
    )
    jar = build / "classes.jar"
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as z:
        for p in (classes / "lab").rglob("*.class"):
            z.write(p, p.relative_to(classes).as_posix())
    run(
        [
            java,
            "-cp",
            tools / "lib/d8.jar",
            "com.android.tools.r8.D8",
            "--release",
            "--min-api",
            "26",
            "--lib",
            android,
            "--output",
            dex,
            jar,
        ]
    )
    with zipfile.ZipFile(unsigned, "a", zipfile.ZIP_DEFLATED) as z:
        z.write(dex / "classes.dex", "classes.dex")
    run([tools / ("zipalign" + suffix), "-P", "16", "-f", "4", unsigned, aligned])
    key = pathlib.Path(args.keystore).resolve()
    key.parent.mkdir(parents=True, exist_ok=True)
    if not key.exists():
        run(
            [
                keytool,
                "-genkeypair",
                "-keystore",
                key,
                "-storetype",
                "PKCS12",
                "-storepass",
                "android",
                "-keypass",
                "android",
                "-alias",
                "orbitclassroom",
                "-keyalg",
                "RSA",
                "-keysize",
                "2048",
                "-validity",
                "3650",
                "-dname",
                "CN=Orbit Classroom Test,O=Local Lab",
            ]
        )
    output = pathlib.Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            java,
            "-jar",
            tools / "lib/apksigner.jar",
            "sign",
            "--ks",
            key,
            "--ks-key-alias",
            "orbitclassroom",
            "--ks-pass",
            "pass:android",
            "--key-pass",
            "pass:android",
            "--v4-signing-enabled",
            "false",
            "--out",
            output,
            aligned,
        ]
    )
    verification = subprocess.run(
        [
            str(java),
            "-jar",
            str(tools / "lib/apksigner.jar"),
            "verify",
            "--verbose",
            "--print-certs",
            str(output),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    print(verification.stdout)
    (build / "signature-verification.txt").write_text(
        verification.stdout, encoding="utf-8"
    )
    run([tools / ("zipalign" + suffix), "-c", "-P", "16", "4", output])
    manifest = subprocess.run(
        [str(tools / ("aapt2" + suffix)), "dump", "badging", str(output)],
        check=True,
        text=True,
        capture_output=True,
    )
    print(manifest.stdout[:2000])
    (build / "package-badging.txt").write_text(manifest.stdout, encoding="utf-8")
    # Validate private-network address parsing independently of Android's framework.
    checks = build / "ServerAddressChecks.java"
    checks.write_text(
        """import lab.orbit.companion.ServerAddress;
public class ServerAddressChecks {
 public static void main(String[] args) throws Exception {
  String[][] ok={{"192.168.1.20","http://192.168.1.20:8765"},{"http://10.1.2.3:9000/#/upload","http://10.1.2.3:9000"},{"172.31.2.3","http://172.31.2.3:8765"}};
  for(String[] row:ok)if(!ServerAddress.normalize(row[0]).equals(row[1]))throw new AssertionError(row[0]);
  String[] bad={"127.0.0.1","localhost","8.8.8.8","https://192.168.1.2","http://user:pass@10.0.0.1","172.32.1.1","10.0.0.999","javascript:alert(1)","example.com","http://10.1.2.3:70000"};
  for(String value:bad){boolean rejected=false;try{ServerAddress.normalize(value);}catch(Exception expected){rejected=true;}if(!rejected)throw new AssertionError(value);}
  System.out.println("13 server-address checks passed.");
 }
}""",
        encoding="utf-8",
    )
    run(
        [
            javac,
            "--release",
            "8",
            "-encoding",
            "UTF-8",
            "-classpath",
            classes,
            "-d",
            classes,
            checks,
        ]
    )
    run([java, "-cp", classes, "ServerAddressChecks"])
    print("APK READY", output, output.stat().st_size, "bytes", flush=True)


if __name__ == "__main__":
    main()
