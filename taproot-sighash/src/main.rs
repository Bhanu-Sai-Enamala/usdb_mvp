

//**************************************************for script path sighash***************************************************
use bitcoin::consensus::encode::deserialize;
use bitcoin::sighash::{Prevouts, SighashCache, TapSighashType, ScriptPath};
use bitcoin::{Transaction, TxOut, Amount, ScriptBuf};
use bitcoin::taproot::ControlBlock;
use hex::decode;
use bitcoin::TapLeafHash;
use bitcoin::taproot::LeafVersion;
fn main() {

    let raw_tx_hex = "0200000002e9822f4a1b50487b832f194adaf567aaae92396792fd34013a1d515f3b67b5fb0100000000fdffffffe9822f4a1b50487b832f194adaf567aaae92396792fd34013a1d515f3b67b5fb0300000000fdffffff0200000000000000000a6a5d0700ae0201e807008403000000000000160014d745f521e8dd860dc843eeb190d7fbe80a4db9cf00000000";


    let tx_bytes = decode(raw_tx_hex).expect("Invalid hex");
    let transaction: Transaction = deserialize(&tx_bytes).expect("Deserialization failed");

  
    let script = ScriptBuf::from(decode("2025f1a245ff572ac11fc1e5da5f6a5a93c946f17c20f1c317c5bae2a0ef2d821cad20d2c1cb1575d323b6120b6e5bcc9ce5ad373e88e73e675030f1c2c5261b4dbc86ac").expect("Invalid script hex")); // Replace with actual script hex


    

    let script_path = ScriptPath::new(&script, LeafVersion::TapScript);

    
    let prev_output1 = TxOut {
    value: Amount::from_sat(10_000),
    script_pubkey: ScriptBuf::from(decode("5120dc19c5c8e8e28ec95845a9ba6f0dd2e86333d727607becf630321762b1bb000e").expect("Invalid script_pubkey hex")),
    };

    let prev_output2 = TxOut {
        value: Amount::from_sat(10_000),
        script_pubkey: ScriptBuf::from(decode("51201d8e516e4dc5f094cd9ba04ce7ba847e1be7b4e9e4b9dda76a5f567832401860").expect("Invalid script_pubkey hex")),
    };

    let binding = [prev_output1,prev_output2];
    let prevouts = Prevouts::All(&binding);

    let sighash_type = TapSighashType::Default;
   
    let leaf_hash = TapLeafHash::from(script_path.clone());
let sighash = SighashCache::new(&transaction)
    .taproot_script_spend_signature_hash(
        1,
        &prevouts,
        leaf_hash,
        sighash_type,
    )
    .expect("Failed to generate sighash");

    println!("Taproot Script Path Sighash: {}", sighash);
}

//*************************************************************************************************************
d dded