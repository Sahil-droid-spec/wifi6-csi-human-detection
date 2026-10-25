package lab.orbit.companion;
import java.net.URI;
public final class ServerAddress {
    private ServerAddress() {}
    public static String normalize(String input) throws Exception {
        String value = input.trim(); if (!value.contains("://")) value = "http://" + value;
        URI uri = new URI(value);
        if (!"http".equalsIgnoreCase(uri.getScheme()) || uri.getRawUserInfo() != null)
            throw new Exception("Use the private http:// address shown by your laptop.");
        String host = uri.getHost(); if (host == null) throw new Exception("Enter the laptop's numeric Wi-Fi address.");
        String[] parts = host.split("\\."); if (parts.length != 4) throw new Exception("Use the laptop's private IPv4 address, not localhost or a public website.");
        int[] octets = new int[4];
        for (int i=0;i<4;i++) { if (!parts[i].matches("[0-9]{1,3}")) throw new Exception("Invalid address."); octets[i]=Integer.parseInt(parts[i]); if(octets[i]>255) throw new Exception("Invalid address."); }
        boolean privateIp = octets[0]==10 || (octets[0]==192 && octets[1]==168) || (octets[0]==172 && octets[1]>=16 && octets[1]<=31);
        if (!privateIp) throw new Exception("Use a private laptop address such as 192.168.x.x, 10.x.x.x or 172.16–31.x.x.");
        int port = uri.getPort()==-1 ? 8765 : uri.getPort(); if(port<1 || port>65535) throw new Exception("Invalid port.");
        return "http://"+octets[0]+"."+octets[1]+"."+octets[2]+"."+octets[3]+":"+port;
    }
}
