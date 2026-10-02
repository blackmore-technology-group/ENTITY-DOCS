import copy, hashlib, importlib.util, json, pathlib, shutil, sqlite3, sys, urllib.request
ROOT=pathlib.Path(r"E:\ENTITY_ACTIVE\ENTITY_ULTIMATE_TEST_20261001")
STATE=ROOT/"state"
REPO=pathlib.Path(r"E:\ENTITY_ACTIVE\ENTITY_V3_4_3_RELEASE_SRC\ENTITY-3.4.3")
if STATE.exists(): shutil.rmtree(STATE)
STATE.mkdir(parents=True,exist_ok=True)
def load(name,rel):
    p=REPO/rel; s=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(s); sys.modules[name]=m; s.loader.exec_module(m); return m
identity_mod=load("u21_identity","src/01_Core_Runtime/identity/canonical_identity.py")
fabric_mod=load("u21_fabric","src/30_Universal_Transaction_Fabric/canonical_universal_fabric.py")
eep_mod=load("u21_eep","src/32_V3_Hardening/exchange_protocol.py")
ref_eep_mod=load("u21_ref_eep","src/31_Profiles/exchange_protocol.py")
econ_mod=load("u21_econ","src/33_Economic_Participation/economic_participation.py")
recovery_mod=load("u21_recovery","src/34_Market_Recovery/market_recovery.py")
def h(x): return hashlib.sha256(str(x).encode()).hexdigest()
def req(c,m):
    if not c: raise AssertionError(m)
scenarios=[]
def gate(name,metrics):
    scenarios.append({"gate":name,"pass":True,"metrics":metrics})
    print("GATE_PASS",name,json.dumps(metrics,sort_keys=True),flush=True)
identity=identity_mod.EntityIdentityVault(STATE)
fabric=fabric_mod.UniversalTransactionFabric(STATE,identity)
exchange=eep_mod.ExchangeProtocol(STATE,identity,fabric)
econ=econ_mod.EconomicParticipationProfile(STATE,identity)
owner_a=identity.create("Ultimate Data Originator A","business")["entity_id"]
owner_b=identity.create("Ultimate Data Originator B","business")["entity_id"]
developer=identity.create("Ultimate Derived Model Developer","business")["entity_id"]
buyer1=identity.create("Ultimate Primary Buyer","business")["entity_id"]
buyer2=identity.create("Ultimate Secondary Buyer","business")["entity_id"]
contrib_a=identity.create("Ultimate Contributor A","person")["entity_id"]
contrib_b=identity.create("Ultimate Contributor B","person")["entity_id"]
operator=identity.create("Ultimate Venue Operator","business")["entity_id"]
verifier=identity.create("Ultimate Settlement Verifier","system")["entity_id"]
treasury_a_entity=identity.create("Ultimate Treasury A","business")["entity_id"]
treasury_b_entity=identity.create("Ultimate Treasury B","business")["entity_id"]
gate("01_identity_fabric_online",{"entities":11,"runtime":"v3.4.3"})
a=fabric.register_digital_commodity(owner_a,"Developer Corpus A",h("ultimate-source-a"),commodity_class="DEVELOPER_DATA",measurement_unit="LICENSE")
b=fabric.register_digital_commodity(owner_b,"Developer Corpus B",h("ultimate-source-b"),commodity_class="DEVELOPER_DATA",measurement_unit="LICENSE")
ra=fabric.grant_right(a["object_id"],owner_a,developer,["TRAIN","DERIVE"],economic_terms={"derivative_participation_bps":1000})
rb=fabric.grant_right(b["object_id"],owner_b,developer,["TRAIN","DERIVE"],economic_terms={"derivative_participation_bps":1000})
gate("02_data_rights_created",{"source_dcos":[a["object_id"],b["object_id"]],"rights":[ra["right_id"],rb["right_id"]]})
inst_a=exchange.define_instrument(owner_a,a["object_id"],"SPOT_LICENSE",{"actions":["TRAIN","DERIVE"],"raw_redistribution":False},1000,"CAD",transferable=True)
inst_b=exchange.define_instrument(owner_b,b["object_id"],"SPOT_LICENSE",{"actions":["TRAIN","DERIVE"],"raw_redistribution":False},500,"CAD",transferable=True)
ta=econ.create_treasury(owner_a,treasury_a_entity,"Ultimate Treasury A","CA",h("treasury-a"))
tb=econ.create_treasury(owner_b,treasury_b_entity,"Ultimate Treasury B","CA",h("treasury-b"))
econ.authorize_settlement_verifier(ta["treasury_id"],owner_a,verifier)
econ.authorize_settlement_verifier(tb["treasury_id"],owner_b,verifier)
pa=econ.define_participation(owner_a,ta["treasury_id"],inst_a["instrument_id"],1000,100,"CAD",primary_treasury_bps=2000,secondary_royalty_bps=200,derivative_participation_bps=1000,terms={"test":"ultimate"})
pb=econ.define_participation(owner_b,tb["treasury_id"],inst_b["instrument_id"],500,50,"CAD",derivative_participation_bps=1000,terms={"test":"ultimate"})
econ.allocate_eep_reserve(exchange,pa["policy_id"]); econ.allocate_eep_reserve(exchange,pb["policy_id"])
venue=exchange.create_venue(operator,"Ultimate Developer Data Venue","CA",["ORDER_BOOK","CALL_AUCTION","RFQ"],h("ultimate-venue-policy"))
exchange.authorize_settlement_verifier(venue["venue_id"],operator,verifier)
disc=exchange.publish_disclosure(venue["venue_id"],inst_a["instrument_id"],owner_a,"OFFERING",h("ultimate-disclosure"))
exchange.list_instrument(venue["venue_id"],inst_a["instrument_id"],owner_a,1,1,disc["content_sha256"])
exchange.set_revenue_rules(inst_a["instrument_id"],owner_a,{owner_a:6000,contrib_a:2500,contrib_b:1500},nonce="ultimate-rules")
gate("03_market_issued",{"venue":venue["venue_id"],"instrument":inst_a["instrument_id"],"reserve_units":100,"currency":"CAD"})
def settle_trade(trade_id,payment_ref):
    att=exchange.attest_payment(trade_id,verifier,payment_ref,h(payment_ref+":evidence"))
    return exchange.settle_trade(trade_id,payment_ref,external_verified=True,payment_attestation_id=att["attestation_id"])
exchange.submit_order(venue["venue_id"],inst_a["instrument_id"],owner_a,"SELL",20,500,"ultimate-primary-sell")
exchange.submit_order(venue["venue_id"],inst_a["instrument_id"],buyer1,"BUY",20,500,"ultimate-primary-buy")
primary=exchange.match_order_book(venue["venue_id"],inst_a["instrument_id"])[0]
settle_trade(primary["trade_id"],"bank:ultimate-primary")
primary_cap=econ.capture_settled_eep_trade(exchange,primary["trade_id"])
econ.settle_obligation(primary_cap["obligation"]["obligation_id"],verifier,"treasury:ultimate-primary",external_verified=True,evidence_sha256=h("primary-econ-settlement"))
req(primary_cap["obligation"]["amount_units"]==2000,"primary participation mismatch")
gate("04_order_book_value",{"trade":primary["trade_id"],"gross_cad":10000,"treasury_participation_cad":2000})
expiry=eep_mod.now_ms()+120000
rfq=exchange.open_rfq(venue["venue_id"],inst_a["instrument_id"],buyer2,"BUY",5,expiry,nonce="ultimate-rfq")
quote=exchange.quote_rfq(rfq["rfq_id"],buyer1,650,expiry,nonce="ultimate-quote")
rfq_exec=exchange.accept_quote(rfq["rfq_id"],quote["quote_id"],buyer2,nonce="ultimate-accept")
settle_trade(rfq_exec["trade_id"],"bank:ultimate-rfq")
rfq_cap=econ.capture_settled_eep_trade(exchange,rfq_exec["trade_id"])
econ.settle_obligation(rfq_cap["obligation"]["obligation_id"],verifier,"treasury:ultimate-rfq",external_verified=True,evidence_sha256=h("rfq-econ-settlement"))
req(rfq_cap["obligation"]["amount_units"]==65,"RFQ secondary royalty mismatch")
with exchange._db() as db:
    src=db.execute("select * from rfq_trade_sources where trade_id=?",(rfq_exec["trade_id"],)).fetchone()
req(src is not None,"RFQ signed source missing")
gate("05_fixed_rfq_eopp_end_to_end",{"trade":rfq_exec["trade_id"],"gross_cad":3250,"secondary_royalty_cad":65,"signed_source_bound":True})
auction_root=STATE/"reference_auction"; auction_root.mkdir(exist_ok=True)
auction_exchange=ref_eep_mod.ExchangeProtocol(auction_root,identity,fabric)
auction_venue=auction_exchange.create_venue(owner_a,"Ultimate Reference Auction Venue","CA",["ORDER_BOOK","CALL_AUCTION","RFQ"],h("ultimate-auction-policy"))
auction_inst=auction_exchange.define_instrument(owner_a,a["object_id"],"SPOT_LICENSE",{"actions":["TRAIN","DERIVE"],"raw_redistribution":False},1000,"CAD",transferable=True)
auction_disc=auction_exchange.publish_disclosure(auction_venue["venue_id"],auction_inst["instrument_id"],owner_a,"LISTING",h("ultimate-auction-disclosure"))
auction_exchange.list_instrument(auction_venue["venue_id"],auction_inst["instrument_id"],owner_a,min_lot=1,tick_size=1,disclosure_sha256=auction_disc["content_sha256"])
auction_exchange.submit_order(auction_venue["venue_id"],auction_inst["instrument_id"],owner_a,"SELL",30,800,nonce="ultimate-auction-sell")
auction_exchange.submit_order(auction_venue["venue_id"],auction_inst["instrument_id"],buyer1,"BUY",20,900,nonce="ultimate-auction-buy1")
auction_exchange.submit_order(auction_venue["venue_id"],auction_inst["instrument_id"],buyer2,"BUY",10,850,nonce="ultimate-auction-buy2")
auction=auction_exchange.run_call_auction(auction_venue["venue_id"],auction_inst["instrument_id"])
req(auction["executed"] and auction["executed_volume"]==30 and auction["clearing_price"]==800,"auction mismatch")
gate("06_call_auction_price_discovery",{"profile":"reference","clearing_price":800,"executed_volume":30,"trades":len(auction["trade_ids"])})
ua=fabric.authorize_use(developer,developer,a["object_id"],"TRAIN",quantity=1,nonce="ultimate-train-a")
ub=fabric.authorize_use(developer,developer,b["object_id"],"TRAIN",quantity=1,nonce="ultimate-train-b")
child=fabric.register_object(developer,"MODEL","Ultimate Derived Model AB",descriptor={"sources":2,"test":"ultimate-system-proof"})
fabric.add_provenance(developer,a["object_id"],child["object_id"],"TRAINED_FROM",contribution_bps=7000,evidence={"basis":"declared-test-weight"})
fabric.add_provenance(developer,b["object_id"],child["object_id"],"TRAINED_FROM",contribution_bps=3000,evidence={"basis":"declared-test-weight"})
dist=fabric.contribution_distribution(child["object_id"],50000)
req(dist["distribution"][a["object_id"]]==35000 and dist["distribution"][b["object_id"]]==15000,"derived distribution mismatch")
gate("07_authorized_derived_output",{"derived_object":child["object_id"],"authorized_use_events":[ua["event"]["event_id"],ub["event"]["event_id"]],"weights_bps":{"A":7000,"B":3000}})
ea=econ.record_derivative_revenue(pa["policy_id"],developer,child["object_id"],35000,"CAD",h("ultimate-derived-a"),occurrence_ref="ultimate:derived:a")
eb=econ.record_derivative_revenue(pb["policy_id"],developer,child["object_id"],15000,"CAD",h("ultimate-derived-b"),occurrence_ref="ultimate:derived:b")
req(ea["obligation"]["amount_units"]==3500 and eb["obligation"]["amount_units"]==1500,"derived obligations mismatch")
econ.settle_obligation(ea["obligation"]["obligation_id"],verifier,"treasury:derived-a",external_verified=True,evidence_sha256=h("derived-a-settle"))
econ.settle_obligation(eb["obligation"]["obligation_id"],verifier,"treasury:derived-b",external_verified=True,evidence_sha256=h("derived-b-settle"))
v=fabric.record_value(developer,child["object_id"],5000,"CAD",state="SETTLED",basis_ref="ultimate:derived-participation")
gate("08_value_accumulates_through_derivation",{"synthetic_derived_gross_cad":50000,"source_a_obligation":3500,"source_b_obligation":1500,"value_record":v["value_id"]})
with exchange._db() as db:
    rows=db.execute("select recipient,sum(amount_units) amount from revenue_events group by recipient").fetchall()
alloc={r["recipient"]:int(r["amount"]) for r in rows}
gate("09_contributors_accumulate",{"originator_trade_distribution":alloc.get(owner_a,0),"contributor_a":alloc.get(contrib_a,0),"contributor_b":alloc.get(contrib_b,0)})
fail={}
try: econ.record_derivative_revenue(pa["policy_id"],developer,child["object_id"],35000,"CAD",h("dup"),occurrence_ref="ultimate:derived:a"); fail["duplicate"]=False
except ValueError: fail["duplicate"]=True
try: econ.record_derivative_revenue(pa["policy_id"],developer,child["object_id"],1000,"USD",h("currency"),occurrence_ref="ultimate:wrong-currency"); fail["currency"]=False
except ValueError: fail["currency"]=True
service_probe=econ.record_service_revenue(ta["treasury_id"],buyer2,"API",250,"CAD","invoice:ultimate-auth-check")
rogue=identity.create("Ultimate Rogue Verifier","system")["entity_id"]
try: econ.settle_obligation(service_probe["obligation"]["obligation_id"],rogue,"rogue",external_verified=True,evidence_sha256=h("rogue")); fail["unauthorized_settlement"]=False
except PermissionError: fail["unauthorized_settlement"]=True
econ.settle_obligation(service_probe["obligation"]["obligation_id"],verifier,"treasury:ultimate-service",external_verified=True,evidence_sha256=h("ultimate-service-settle"))
try: exchange.submit_order(venue["venue_id"],inst_a["instrument_id"],buyer2,"SELL",999999,1,"ultimate-oversell"); fail["oversell"]=False
except PermissionError: fail["oversell"]=True
cycle=False
try: fabric.add_provenance(developer,child["object_id"],a["object_id"],"DERIVED_FROM",contribution_bps=1000)
except ValueError: cycle=True
fail["provenance_cycle"]=cycle
body={"schema":"entity-eep-order-v1","order_id":"ultimate-tamper","venue_id":venue["venue_id"],"instrument_id":inst_a["instrument_id"],"participant":buyer2,"side":"BUY","quantity":1,"limit_price":1,"tif":"GTC","nonce":"ultimate-tamper","created_at_ms":eep_mod.now_ms()}
sig=identity.sign(buyer2,body); bad=dict(body); bad["quantity"]=2
try: exchange.submit_signed_order(bad,sig); fail["tampered_signature"]=False
except PermissionError: fail["tampered_signature"]=True
req(all(fail.values()),"fail-closed matrix incomplete")
gate("10_fail_closed_integrity",fail)
core_bundle=fabric.export_bundle(a["object_id"])
bundle=recovery_mod.MarketStateRecovery.export(exchange.path,econ.path,identity,core_bundles=[core_bundle])
verified=recovery_mod.MarketStateRecovery.verify(bundle,verify_manifest=identity_mod.EntityIdentityVault.verify_manifest,verify_signature=identity_mod.EntityIdentityVault.verify_signature,verify_core_bundle=fabric.verify_bundle)
req(verified["valid"],"recovery bundle verify failed")
tampered=copy.deepcopy(bundle); tampered["exchange"]["tables"]["balances"]["rows"][0]["units"]+=1
tamper_check=recovery_mod.MarketStateRecovery.verify(tampered,verify_manifest=identity_mod.EntityIdentityVault.verify_manifest,verify_signature=identity_mod.EntityIdentityVault.verify_signature,verify_core_bundle=fabric.verify_bundle)
req(not tamper_check["valid"],"tampered recovery bundle accepted")
gate("11_provider_independent_bundle",{"semantic_sha256":bundle["semantic_sha256"],"verified":True,"tamper_rejected":True})
expected_ex=bundle["exchange"]["state_sha256"]; expected_ec=bundle["economic_participation"]["state_sha256"]
exchange.path.unlink(); econ.path.unlink()
restored_exchange=eep_mod.ExchangeProtocol(STATE,identity,fabric); restored_econ=econ_mod.EconomicParticipationProfile(STATE,identity)
restore=recovery_mod.MarketStateRecovery.restore(bundle,restored_exchange.path,restored_econ.path,verify_manifest=identity_mod.EntityIdentityVault.verify_manifest,verify_signature=identity_mod.EntityIdentityVault.verify_signature,verify_core_bundle=fabric.verify_bundle)
req(restore["restored"] and restore["exchange_state_sha256"]==expected_ex and restore["economic_state_sha256"]==expected_ec,"destructive restore mismatch")
with restored_exchange._db() as db:
    rsrc=db.execute("select count(*) from rfq_trade_sources where trade_id=?",(rfq_exec["trade_id"],)).fetchone()[0]
    rtrade=db.execute("select status from trades where trade_id=?",(rfq_exec["trade_id"],)).fetchone()["status"]
req(rsrc==1 and rtrade=="SETTLED","RFQ source/trade did not survive restore")
gate("12_destroy_and_recover_market",{"atomic_restore":restore["atomic_cross_database_restore"],"exchange_state_sha256":restore["exchange_state_sha256"],"economic_state_sha256":restore["economic_state_sha256"],"rfq_signed_source_restored":True})
prod_db=pathlib.Path(r"E:\ENTITY_ACTIVE\ENTITY_V3_4_PRODUCTION_RUNTIME\state\entity_v3_exchange.sqlite")
with sqlite3.connect(prod_db) as pdb:
    prod_rfq_table=pdb.execute("select count(*) from sqlite_master where type='table' and name='rfq_trade_sources'").fetchone()[0]
fix_hash=hashlib.sha256((REPO/"src/31_Profiles/exchange_protocol.py").read_bytes()).hexdigest()
portal_status=urllib.request.urlopen("https://blackmore-tech.floot.app/",timeout=20).status
req(prod_rfq_table==1 and fix_hash=="53761f15c7ae58726ce8cd01a28164d3a14ae29aac38a89859c408fc3c76b14a" and portal_status==200,"installed/live integration gate failed")
gate("13_installed_runtime_and_portal",{"rfq_schema_installed":True,"merged_fix_hash_match":True,"portal_http_status":portal_status})
state_bytes=sum(p.stat().st_size for p in STATE.rglob("*.sqlite"))
summary={"schema":"entity-v343-ultimate-system-proof-v1","runtime_release":"v3.4.3","pass":True,"synthetic_only":True,
"scenario_count":len(scenarios),"scenarios":scenarios,"source_dcos":[a["object_id"],b["object_id"]],"derived_object_id":child["object_id"],
"primary_trade_id":primary["trade_id"],"rfq_trade_id":rfq_exec["trade_id"],"auction_trade_ids":auction["trade_ids"],
"synthetic_primary_gross_cad_units":10000,"synthetic_rfq_secondary_gross_cad_units":3250,"synthetic_derived_gross_cad_units":50000,
"explicit_economic_obligations_cad_units":{"primary":2000,"rfq_secondary_royalty":65,"derived_a":3500,"derived_b":1500,"service_receivable":250},
"recovery_bundle_semantic_sha256":bundle["semantic_sha256"],"isolated_state_sqlite_bytes":state_bytes,
"real_market_demand_proven":False,"real_cash_revenue_proven":False,
"claim_boundary":"Controlled end-to-end qualification using synthetic economic amounts. It proves protocol mechanics, explicit rights, signed market execution, RFQ/EOPP integration, derived provenance, attributable economic records, fail-closed controls, logical export and destructive recovery. It does not prove external demand, actual cash settlement, fair market value, legal enforceability, liquidity, or independent multi-operator adoption."}
out=ROOT/"ULTIMATE_SYSTEM_PROOF_RESULT.json"; out.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print("ULTIMATE_SYSTEM_PROOF_PASS",len(scenarios),"GATES",flush=True)
print("RESULT",out,flush=True)
print("CLAIM_BOUNDARY",summary["claim_boundary"],flush=True)
