#####USER COMES BACK WITH RUNES BURN AND BTC UNLOCK SIGNED TRANSACTION FILLING HIS SIGNATURES WHEREVER APPROPRIATE , PROTOCOL LOOKS, VERIFIES AND SIGNS AND BROADCASTS#####


###USER CONSTRUCTS UNSIGNED BURN+BTC UNLOCK TRANSACTION

import subprocess
import os
import json
import pexpect 

def run_path_one_unlock():
    # Setup environment
    env = os.environ.copy()
    

    # Absolute path to the directory where ord command should be run
    ORD_DIRECTORY = "/Users/bhanusaienamala/Desktop/bitcoin/USDB_mvp/ord_modified/ord-btclock"

    # Construct the command
    burn_cmd = [
        "ord", "--regtest",
        "--cookie-file", "env/regtest/.cookie",
        "--datadir", "env",
        "wallet", "--name","--user", "burn", "--dry-run", "1000:UNCOMMON.GOODS",
        "--fee-rate", "1"
    ]
    # burn_cmd = [
    #     "ord", "--regtest",
    #     "--cookie-file", "env/regtest/.cookie",
    #     "--datadir", "env",
    #     "wallet", "burn", "--dry-run", "1000:UNCOMMONGOODS",
    #     "--fee-rate", "1"
    # ]

    # Execute the command
    burn_result = subprocess.run(burn_cmd, cwd=ORD_DIRECTORY, env=env, capture_output=True, text=True)

    print("STDOUT:\n", burn_result.stdout)
    print("STDERR:\n", burn_result.stderr)

        # --- Inserted block for extracting PSBT and decoding ---
    burn_output = json.loads(burn_result.stdout)
    psbt = burn_output["psbt"]
    print("PSBT:", psbt)
    decode_cmd = ["bitcoin-cli", "-datadir=env", "decodepsbt", psbt]
    decode_result = subprocess.run(decode_cmd,cwd=ORD_DIRECTORY, capture_output=True, text=True, check=True)
    decoded = json.loads(decode_result.stdout)
    input_txid = decoded["tx"]["vin"][0]["txid"]
    input_vout = decoded["tx"]["vin"][0]["vout"]
    print("Input TXID:", input_txid)
    print("Input VOUT:", input_vout)
    getraw_cmd = ["bitcoin-cli", "-datadir=env", "getrawtransaction", input_txid, "1"]
    raw_result = subprocess.run(getraw_cmd,cwd=ORD_DIRECTORY, capture_output=True, text=True, check=True)
    raw_tx = json.loads(raw_result.stdout)
    btc_locked_address = "bcrt1prk89zmjdchcffnvm5pxw0w5y0cd70d8fujuamfm2tat8svjqrpsqtu5ucx"
    voutBTClocked = None
    for vout_entry in raw_tx['vout']:
        addresses = vout_entry['scriptPubKey'].get('address', [])
        value = float(vout_entry.get('value', 0))
        if btc_locked_address in addresses and value == 0.0001:
            voutBTClocked = vout_entry['n']
            break
    if voutBTClocked is None:
        raise Exception("No matching vout with 0.0001 BTC to target address found.")
    print("BTC Locked VOUT (BTClocked):", voutBTClocked)
    receive_address = subprocess.check_output(
        [
            "ord", "--regtest", "--cookie-file", "env/regtest/.cookie", "--data-dir", "env",
            "wallet", "--name", "user", "receive"
        ],
        cwd=ORD_DIRECTORY,
        stderr=subprocess.STDOUT,
        text=True
    ).strip()
    # receive_address = "bcrt1q6azl2g0gmkrqmjzra6cep4lmaq9ymww0djw6qx"  # Replace with actual address if needed
    # getraw_cmd = ["bitcoin-cli", "-datadir=env", "getrawtransaction", input_txid, "1"]
    # raw_result = subprocess.run(getraw_cmd,cwd=ORD_DIRECTORY, capture_output=True, text=True, check=True)
    inputs = [
    {"txid": input_txid, "vout": input_vout},
    {"txid": input_txid, "vout": voutBTClocked}
  ]

    outputs = [
        {"data": "00ae0201e80700"},
        {receive_address: 0.0001}
    ]

    inputs_json = json.dumps(inputs)
    outputs_json = json.dumps(outputs)

    createraw_cmd = [
        "bitcoin-cli", "-datadir=env", "createrawtransaction",
        inputs_json,
        outputs_json
    ]

    print("Command:", createraw_cmd)

    raw_tx_hex = subprocess.run(
        createraw_cmd,
        cwd=ORD_DIRECTORY,
        capture_output=True,
        text=True,
        check=True
    )
    print("Raw Transaction:", raw_tx_hex.stdout)
    pattern = "00ae0201e80700"
    raw_tx_hex_str = raw_tx_hex.stdout.strip()
    pattern_index = raw_tx_hex_str.find(pattern)

    if pattern_index == -1:
        raise ValueError("Pattern not found in transaction hex")

    # Step 2: Get the byte positions before the pattern
    byte_before_07 = pattern_index - 2
    byte_before_6a = pattern_index - 4
    byte_09_position = pattern_index - 6

    # Step 3: Validate expected values
    if raw_tx_hex_str[pattern_index - 2:pattern_index] != "07":
        raise ValueError("Byte before pattern is not 07")
    if raw_tx_hex_str[pattern_index - 4:pattern_index - 2] != "6a":
        raise ValueError("Byte before 07 is not 6a")
    if raw_tx_hex_str[pattern_index - 6:pattern_index - 4] != "09":
        raise ValueError("Byte before 6a is not 09")

    # Step 4: Replace 09 with 0a and insert 5d before 07
    modified_tx_hex = (
        raw_tx_hex_str[:pattern_index - 6] +   # before 09
        "0a" +                             # replace 09 with 0a
        "6a" +                             # keep 6a
        "5d" +                             # insert 5d
        "07" +                             # keep 07
        raw_tx_hex_str[pattern_index:]        # from pattern onwards
    )

    print("Modified raw transaction hex:")
    print(modified_tx_hex)
    convert_cmd = [
    "bitcoin-cli", "-datadir=env", "converttopsbt", modified_tx_hex
  ]
    convert_result = subprocess.run(
        convert_cmd, cwd=ORD_DIRECTORY, capture_output=True, text=True, check=True
    )
    psbt = convert_result.stdout.strip()
    print("Converted PSBT:", psbt)

    # Step 2: Process PSBT with wallet (sign it)
    process_cmd = [
        "bitcoin-cli", "-datadir=env", "walletprocesspsbt", psbt
    ]
    process_result = subprocess.run(
        process_cmd, cwd=ORD_DIRECTORY, capture_output=True, text=True, check=True
    )
    processed_data = json.loads(process_result.stdout)
    final_psbt = processed_data["psbt"]
    print("Final PSBT:", final_psbt)
    decode_cmd = [
    "bitcoin-cli", "-datadir=env", "decodepsbt", final_psbt
]
    decode_result = subprocess.run(
        decode_cmd, cwd=ORD_DIRECTORY, capture_output=True, text=True, check=True
    )

    decoded = json.loads(decode_result.stdout)

    # Extract final_scriptwitness from the first input
    final_witness = decoded["inputs"][0].get("final_scriptwitness", [])

    # Optionally, store it to a variable or file
    if final_witness:
        script_witness_hex = final_witness[0]
        print("Extracted final_scriptwitness:", script_witness_hex)
        # Example: Write to file
    else:
        print("final_scriptwitness not found in the decoded PSBT.")
    #insert sighash generation  command - @anshika
#     ./target/release/ord --regtest \
#   --cookie-file env/regtest/.cookie \
#   --data-dir env \
#   --rawtxhex <raw_tx_hex> \
#   --rawspendscriptpathhex <raw_spend_script_path_hex> \
#   --scriptPubKeyHexOne <script_pub_key_hex_one> \
#   --scriptPubKeyHexTwo <script_pub_key_hex_two> \
#   --inputIndex <input_index> 

    # Replace with actual values
    sighash = "f7b6a4ec8179632a22fb916932adc9c4149d51cd4860428934c38f397b1dbc48"
    privkey = "4d232b61b03967219060631a3928fe6f2087559e3dc00cfbafbf4153b1aa8003"

    # Spawn a btcdeb shell session
    child = pexpect.spawn("btcdeb")

    # Wait for the btcdeb prompt
    child.expect("btcdeb>")

    # Run the sign_schnorr command
    child.sendline(f"tf sign_schnorr {sighash} {privkey}")

    # Wait for the response
    child.expect("btcdeb>")

    # Extract the output
    output = child.before.decode("utf-8")

    # Parse the output to extract the signature
    protocol_signature = ""
    for line in output.strip().splitlines():
        if len(line.strip()) == 128:
            protocol_signature = line.strip()
            break

    # Display results
    if protocol_signature:
        print("✅ Protocol Schnorr Signature:", protocol_signature)
    else:
        print("❌ Signature not found in output.")

    # Exit btcdeb
    child.sendline("exit")
    privkey = "04f8996da763b7a969b1028ee3007569eaf3a635486ddab211d512c85b9df8fb"

    # Spawn a btcdeb shell session
    child = pexpect.spawn("btcdeb")

    # Wait for the btcdeb prompt
    child.expect("btcdeb>")

    # Run the sign_schnorr command
    child.sendline(f"tf sign_schnorr {sighash} {privkey}")

    # Wait for the response
    child.expect("btcdeb>")

    # Extract the output
    output = child.before.decode("utf-8")

    # Parse the output to extract the signature
    user_signature = ""
    for line in output.strip().splitlines():
        if len(line.strip()) == 128:
            user_signature = line.strip()
            break

    # Display results
    if user_signature:
        print("✅ User Schnorr Signature:", user_signature)
    else:
        print("❌ Signature not found in output.")

    # Exit btcdeb
    child.sendline("exit")
    controlblock = "442025f1a245ff572ac11fc1e5da5f6a5a93c946f17c20f1c317c5bae2a0ef2d821cad20d2c1cb1575d323b6120b6e5bcc9ce5ad373e88e73e675030f1c2c5261b4dbc86ac61c15bf08d58a430f8c222bffaf9127249c5cdff70a2d68b2b45637eb662b6b88eb5747f67099a8ea09f5d9f590c1d12f38f58838872d081646f4e252c90f0ac86d3d29ab618193c0908c50339f77cce4b89935f4df11ed45f3bdff6f7395edd59fb"
    # Build final transaction
    final_tx_hex = ""
    final_tx_hex += modified_tx_hex[:8]               # version
    final_tx_hex += "0001"                       # marker & flag for segwit
    final_tx_hex += modified_tx_hex[8:-8]             # all except final locktime
    final_tx_hex += "0140" + script_witness_hex  # witness 1
    final_tx_hex += "0440" + user_signature      # witness 2
    final_tx_hex += "40" + protocol_signature    # witness 3
    final_tx_hex += controlblock
    final_tx_hex += "00000000"                   # locktime

    print("✅ Final signed Transaction Hex:\n", final_tx_hex)

    sendrawtransaction_cmd = [
    "bitcoin-cli", "-datadir=env", "sendrawtransaction", final_tx_hex
]
    subprocess.run(
        sendrawtransaction_cmd, cwd=ORD_DIRECTORY, capture_output=True, text=True, check=True
    )



