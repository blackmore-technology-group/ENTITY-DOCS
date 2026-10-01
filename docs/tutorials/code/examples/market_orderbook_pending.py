from pathlib import Path
import importlib.util, hashlib, os, shutil, sqlite3
ROOT=Path(os.environ.get("ENTITY_ROOT", Path.cwd())).resolve(); STATE=ROOT/".tutorial-test-state"/"market-orderbook"
if STATE.exists(): shutil.rmtree(STATE)
def load_source(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
identity_mod=load_source("src/01_Core_Runtime/identity/canonical_identity.py","entity_identity")
fabric_mod=load_source("src/30_Universal_Transaction_Fabric/canonical_universal_fabric.py","entity_fabric")
exchange_mod=load_source("src/32_V3_Hardening/exchange_protocol.py","entity_exchange")
identity=identity_mod.EntityIdentityVault(STATE)
issuer=identity.create("Tutorial Issuer","organization"); buyer=identity.create("Tutorial Buyer","organization"); venue_op=identity.create("Tutorial Venue Operator","organization")
fabric=fabric_mod.UniversalTransactionFabric(STATE,identity); obj=fabric.register_object(issuer["entity_id"],"DATASET","Tutorial Market Dataset")
exchange=exchange_mod.ExchangeProtocol(STATE,identity,fabric)
policy_sha=hashlib.sha256(b"tutorial venue policy").hexdigest(); venue=exchange.create_venue(venue_op["entity_id"],"Tutorial Venue","CA",["ORDER_BOOK"],policy_sha)
instrument=exchange.define_instrument(issuer["entity_id"],obj["object_id"],"SPOT_LICENSE",{"actions":["READ","TRAIN"],"purpose":"research"},10,"CAD",transferable=True)
disclosure_sha=hashlib.sha256(b"tutorial rights disclosure").hexdigest(); exchange.publish_disclosure(venue["venue_id"],instrument["instrument_id"],issuer["entity_id"],"RIGHTS_TERMS",disclosure_sha)
exchange.list_instrument(venue["venue_id"],instrument["instrument_id"],issuer["entity_id"],1,1,disclosure_sha)
exchange.submit_order(venue["venue_id"],instrument["instrument_id"],buyer["entity_id"],"BUY",2,100,"tutorial-buy-1")
exchange.submit_order(venue["venue_id"],instrument["instrument_id"],issuer["entity_id"],"SELL",2,90,"tutorial-sell-1")
trades=exchange.match_order_book(venue["venue_id"],instrument["instrument_id"]); assert len(trades)==1; trade=trades[0]
with sqlite3.connect(exchange.path) as db:
    row=db.execute("SELECT status,external_verified FROM clearing WHERE trade_id=?",(trade["trade_id"],)).fetchone()
assert row[0]=="PENDING" and int(row[1])==0; assert exchange.balance(instrument["instrument_id"],buyer["entity_id"])==0
market=exchange.market_data(venue["venue_id"],instrument["instrument_id"]); assert market["volume_units"]==2 and market["market_data_is_observation_not_valuation"] is True
print(f"VENUE={venue['venue_id']}"); print(f"INSTRUMENT={instrument['instrument_id']}"); print(f"TRADE={trade['trade_id']}"); print("TRADE_STATUS=EXECUTED"); print("CLEARING_STATUS=PENDING"); print("EXTERNAL_PAYMENT_VERIFIED=FALSE"); print("BUYER_ENTITLEMENT_BEFORE_SETTLEMENT=0"); print("MARKET_DATA_OBSERVATION_NOT_VALUATION=TRUE"); print("CLAIM_BOUNDARY=execution does not prove payment or transfer underlying ownership")
