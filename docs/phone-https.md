# Connect a phone to the local recording page

This step establishes phone access. Record a test only after the page opens without a certificate warning. Use your own trusted Wi-Fi, with the laptop and test phone on the same network.

## What was prepared

`scripts/phone_https.py` uses OpenSSL from the existing Git for Windows installation. It creates a local certificate authority (CA) and a server certificate for the laptop's Wi-Fi IP address. A certificate lets the browser verify the server's identity; HTTPS encrypts the connection.

Generated files live in `.local-https/`, which is excluded from Git. `pothole-test-ca.cer` is the public certificate to install on a test phone. `root-ca.key` and `server.key` are private keys and must stay on the laptop. Trusting the test CA makes the phone trust certificates signed with its private key; remove this test trust after the experiment. Future users of a publicly hosted site will use its normal public HTTPS certificate without this installation step.

No new packages, system certificates or firewall rules were installed. The server certificate lasts 30 days; the CA lasts one year. This is a free local setup, with no hosting account or service quota.

## Start the local servers

In a new PowerShell terminal:

```powershell
Set-Location 'C:\Users\kshit\Documents\pothole_project'
.\.pothholevenv\Scripts\python.exe scripts\phone_https.py serve
```

The script prints two addresses using the IP saved during setup:

- An HTTP URL on port **8002**, serving only the public certificate for initial installation.
- An HTTPS URL on port **8443**, serving the recording page and API.

Keep the terminal open. Press Ctrl+C when finished to stop both servers. The earlier laptop server on port 8001 can remain running. This helper does not reload automatically after code changes: restart it when needed.

## iPhone with Safari

1. In Safari, open the **Install certificate** URL printed in the terminal. Allow the profile download when asked.
2. Open **Settings > Profile Downloaded**. Check the certificate is named **Pothole Phone Test CA**, tap **Install**, and follow the phone's prompts. Install it promptly; iOS removes a pending profile after eight minutes. [Apple's profile installation instructions](https://support.apple.com/en-us/102400)
3. Open **Settings > General > About > Certificate Trust Settings** and enable full trust for **Pothole Phone Test CA**. [Apple's certificate trust instructions](https://support.apple.com/en-us/102390)
4. Return to Safari and open the **Then open recorder** HTTPS URL printed in the terminal.
5. Confirm the recording page opens without a certificate warning. Stop here for this checkpoint; next we will grant camera/location permissions and record a short outdoor test.

## Android with Chrome

Use the same two URLs and generated public certificate. Download the `.cer` in Chrome, then use Android Settings' **Install a certificate > CA certificate** option. Menu locations differ by phone/version; search Settings for certificate installation if necessary. This is a CA certificate for browser HTTPS trust, not a Wi-Fi client certificate. Once installed, reopen the HTTPS recording URL in Chrome. Record the actual phone model, Android version and Chrome version before testing.

Android can also use the [USB localhost-forwarding alternative](https://developer.chrome.com/docs/devtools/remote-debugging/local-server) described in the recording guide.

## If connection fails

- **Server reports the address is unavailable:** the laptop's IP likely changed. Find the active Wi-Fi IPv4 address with `ipconfig`, then regenerate the server certificate using the command below. Setup preserves the existing CA, so a normal IP change does not require reinstalling the phone's root certificate.
- **Phone cannot open either URL:** verify both devices are on the same Wi-Fi and the terminal is still running. Guest/campus Wi-Fi may isolate devices, and Windows Firewall may block incoming connections. Report the exact error and whether this is a home or shared network before changing network/firewall settings. Do not disable the firewall.
- **Certificate downloads, but HTTPS shows a trust warning:** check that the same CA was installed, iPhone full trust is enabled, both devices have correct clocks, and the URL exactly matches the printed IP. An expired server certificate also needs regeneration.
- **Windows blocks incoming connections:** use a narrowly scoped rule for this local test once the network context is confirmed. No firewall changes were made automatically.

Regenerate a server certificate for a new IP, or renew it after 30 days. Replace the example IP below with the laptop's actual Wi-Fi address; stop the helper first, then restart it afterwards:

```powershell
.\.pothholevenv\Scripts\python.exe scripts\phone_https.py setup --ip 192.168.1.50
.\.pothholevenv\Scripts\python.exe scripts\phone_https.py serve
```

## Verification and cleanup

Laptop checks passed: trusted HTTPS handshake, matching server IP, health and capture page responses, public certificate download, rejection of an incorrect hostname, and 404 responses for private-key paths/directory listings. The default client did not trust this CA without explicitly supplying it. The user has since confirmed that the HTTPS page opens on the iPhone after installing the test certificate. Android access and actual recording on both platforms remain pending.

When finished, stop the terminal server. On iPhone, remove the **Pothole Phone Test CA** profile under Settings > General > VPN & Device Management. On Android, remove only this test CA from the installed/user certificate list; do not clear unrelated certificates. The helper does not install a CA into Windows, so no Windows trust removal is needed.

Suggested commit message: `Add local HTTPS setup for phone recording tests`.
