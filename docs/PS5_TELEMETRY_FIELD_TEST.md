# PS5 Telemetry: Windows Field-Test Guide

**Status:** Proposed experiment, not yet executed. **Date:** 2026-10-10.  
**Scope:** PS5 to Windows PC over a private LAN; no RaceEngineer source changes or simulator adoption.

## Purpose and limits

Prove that an installed F1 title and Gran Turismo 7 can send live UDP telemetry from a PS5 to the development PC. Start with **F1** because the game exposes an officially documented UDP output setting. Then test **GT7**, whose community-documented protocol requires heartbeat and decryption. These are **transport tests**; receiving UDP does not establish correct parsing, race-state quality, strategy, or Linux/AMD qualification.

No software needs to be installed on the PS5. No port forwarding or Internet exposure is needed. The PC can be Windows for discovery; Linux validation is still required later.

## A. Common preparation

1. Connect the PS5 and PC to the same non-isolated home LAN (prefer wired Ethernet).
2. On PS5, open **Settings > Network > Connection Status > View Connection Status** and note the PS5 IPv4 address.
3. On Windows, open PowerShell 7 and run `ipconfig`. Note the IPv4 address of the active Ethernet/Wi-Fi adapter.
4. Record the exact installed F1 title/version and game update. Do not assume F1 24 and F1 25 use identical UDP layouts.
5. Use the private network firewall profile only. Do **not** forward ports on the router.

## B. F1: configure UDP telemetry

Find **UDP Telemetry** in the game's settings (menu wording may vary by edition):

| Setting | Value |
|---|---|
| UDP Telemetry | On |
| UDP IP Address | Windows PC's IPv4 address |
| UDP Port | 20777 |
| UDP Send Rate | 20 Hz or 60 Hz |
| UDP Format | Match the installed title/selected decoder (e.g. 2024 for F1 24; 2025 for F1 25) |
| UDP Broadcast Mode | Off for direct-IP testing, if available |

Run this PowerShell 7 packet counter **before** entering an on-track session:

```powershell
$udp = [System.Net.Sockets.UdpClient]::new(20777)
$udp.Client.ReceiveTimeout = 1000
$remote = [System.Net.IPEndPoint]::new([System.Net.IPAddress]::Any, 0)
$count = 0
Write-Host "Listening on UDP 20777. Press Ctrl+C to stop."
try {
    while ($true) {
        try {
            $data = $udp.Receive([ref]$remote)
            $count++
            if ($count -le 5 -or $count % 100 -eq 0) {
                Write-Host "Packet $count | $($data.Length) bytes | From $($remote.Address)"
            }
        }
        catch [System.Net.Sockets.SocketException] {
            # Expected receive timeout; continue listening.
        }
    }
}
finally {
    $udp.Close()
}
```

Drive for 15–30 seconds. Expect packet counts to increase and source IP to match the PS5. Packet lengths vary by packet type and edition; **do not use example byte lengths as acceptance criteria**. Stop with Ctrl+C. If PowerShell was interrupted before `finally` completed, close that terminal before retrying.

**Success (transport):** at least 100 received datagrams over more than 5 seconds, from the PS5, repeatable after restarting the receiver.  
**Success (decoding, separate follow-up):** an edition-matched decoder reports plausible changing speed, lap, and session data, checked against the in-game HUD.

## C. GT7: heartbeat + encrypted telemetry

GT7 does not expose the same official F1 UDP settings. Community implementations report:

- PC sends periodic **heartbeat** datagrams to **PS5 UDP destination port 33739**.
- PS5 sends **encrypted telemetry** to **PC UDP destination port 33740**.
- The heartbeat must be repeated; a passive UDP listener alone will not initiate the stream.
- Use the PS5 IPv4 address noted above.

**Recommended reference:** [chrshdl/granturismo](https://github.com/chrshdl/granturismo), a MIT-licensed Python library with a `Feed` abstraction handling heartbeat, reception, and decoding. Read its current README, pin a reviewed commit and follow its documented API. This guide intentionally does **not** invent unverified install commands or an exact heartbeat payload. Alternative protocol references: [MacManley/gt7-udp](https://github.com/MacManley/gt7-udp) and [MoebiusX/gt7-telemetry-analyzer](https://github.com/MoebiusX/gt7-telemetry-analyzer).

1. Start GT7 and enter an active driving session.
2. Run a reviewed, documented heartbeat-enabled receiver using the PS5 IP; ensure local inbound UDP 33740 is allowed on the private network.
3. Confirm the receiver sees packets from the PS5 and can decode plausible changing speed, RPM, lap or fuel values.
4. Close the receiver cleanly (the reference warns that failing to close the feed can leave the console streaming).
5. Repeat after restarting the game and receiver. Record packet counts and any interruptions.

**Do not assume** the GT7 community packet contains opponent standings, tyre compound, tyre wear or full race-control state. Their availability is unconfirmed in the surveyed decoder.

## D. Troubleshooting

| Symptom | Check |
|---|---|
| F1 counter stays at zero | Telemetry enabled; on-track session active; correct PC IPv4 and UDP port; same LAN; private-profile firewall; no guest/client isolation |
| Source IP is not PS5 | Check selected network adapter, broadcast mode and other local UDP senders |
| F1 packets arrive but decoder fails | Exact game edition, selected UDP format, packet header/version, and decoder compatibility |
| GT7 receives nothing | Heartbeat really sent to PS5:33739; receiver listening on 33740; correct PS5 IP; game in driving state; firewall |
| GT7 datagrams arrive but values are nonsense | Decryption/parser version, packet variants, firmware/game update; verify against in-game HUD |
| Data is intermittent | Wired network, LAN isolation, packet loss, receiver restarts, heartbeat scheduling |

## E. Evidence checklist

- [ ] Exact F1 title and update recorded.
- [ ] PS5 and PC IPv4 addresses checked (redact at least the final octet in shared logs).
- [ ] F1 UDP settings recorded.
- [ ] F1 receives 100+ packets over >5 seconds from the PS5.
- [ ] F1 packet count remains repeatable after restart.
- [ ] Edition-matched F1 decoder checked against the HUD (separate from transport).
- [ ] GT7 heartbeat-enabled receiver tested.
- [ ] GT7 packet stream and plausible decoded values verified.
- [ ] GT7 restart/reconnection checked.
- [ ] No router port forwarding, no public exposure, no unnecessary personal identifiers captured.

**Report outcomes as PASS / FAIL / NOT TESTED separately.** A packet counter is not proof of telemetry-field correctness, and neither game is an officially adopted RaceEngineer adapter until later project gates.

## F. What this enables, and what it does not

Live telemetry is a prerequisite for driving feedback and strategy, **not proof** of either. Longer-term RaceEngineer goals include a two-way driver/engineer loop: the driver may reject a pit call, ask whether to push or hold, or compare soft and medium tyres. An intent layer would consult session state and deterministic calculations/strategy simulations, update a proposed plan under explicit driver authority, and communicate a grounded response. Voice input, strategy simulation, memory, opponent inference, confidence calibration and nonblocking audio/LLM scheduling remain future, unimplemented work. The system must acknowledge missing fields rather than fabricate recommendations.

## Sources

- Research snapshot (2026-10-10): read-only `report.md` supplied for this planning exercise; physical PS5/Linux tests were not performed.
- GT7: https://github.com/chrshdl/granturismo ; https://github.com/MacManley/gt7-udp
- F1: https://forums.ea.com/t5/s/tghpe58374/attachments/tghpe58374/f1-games-game-info-hub-en/61/4/Data%20Output%20from%20F1%2025%20v3.pdf
- F1 PS5 example: https://github.com/edoofra/F1_2024_telemetry_analyzer
