import hashlib, importlib.util, json, pathlib, sqlite3, sys, time
ROOT=pathlib.Path(r"E:\ENTITY_ACTIVE\ENTITY_ECONOMY_PROOF_20261001")
STATE=ROOT/'scenario_state'
REPO=pathlib.Path(r"E:\ENTITY_ACTIVE\ENTITY_V3_4_3_RELEASE_SRC\ENTITY-3.4.3")

def load(name,rel):
    p=REPO/rel; spec=importlib.util.spec_from_file_location(name,p); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
identity_mod=load('evs_identity','src/01_Core_Runtime/identity/canonical_identity.py')
fabric_mod=load('evs_fabric','src/30_Universal_Transaction_Fabric/canonical_universal_fabric.py')
hard_mod=load('evs_hard','src/32_V3_Hardening/exchange_protocol.py')
ref_mod=load('evs_ref','src/31_Profiles/exchange_protocol.py')
econ_mod=load('evs_econ','src/33_Economic_Participation/economic_participation.py')

def h(x): return hashlib.sha256(str(x).encode()).hexdigest()
def require(cond,msg):
    if not cond: raise AssertionError(msg)
scenarios=[]
def record(name,metrics): scenarios.append({'scenario':name,'pass':True,'metrics':metrics}); print('SCENARIO_PASS',name,json.dumps(metrics,sort_keys=True))

identity=identity_mod.EntityIdentityVault(STATE)
originator=identity.create('Developer Data Originator','business')['entity_id']
treasury_entity=identity.create('Developer Data Treasury','business')['entity_id']
buyer1=identity.create('Developer Buyer One','business')['entity_id']
buyer2=identity.create('Developer Buyer Two','business')['entity_id']
contrib_a=identity.create('Contributor A','person')['entity_id']
contrib_b=identity.create('Contributor B','person')['entity_id']
verifier=identity.create('Synthetic Settlement Verifier','system')['entity_id']
fabric=fabric_mod.UniversalTransactionFabric(STATE,identity)
exchange=hard_mod.ExchangeProtocol(STATE,identity,fabric)
profile=econ_mod.EconomicParticipationProfile(STATE,identity)

# DCO 1: originator participation across primary, secondary, derivative and service paths.
dco1=fabric.register_digital_commodity(originator,'Wildfire Training Corpus',h('wildfire-corpus'),commodity_class='ENVIRONMENTAL_TELEMETRY')
inst1=exchange.define_instrument(originator,dco1['object_id'],'SPOT_LICENSE',{'actions':['TRAIN','DERIVE'],'raw_redistribution':False},1000,'CAD',transferable=True)
treasury=profile.create_treasury(originator,treasury_entity,'Developer Data Treasury','CA',h('treasury-policy'))
profile.authorize_settlement_verifier(treasury['treasury_id'],originator,verifier)
policy1=profile.define_participation(originator,treasury['treasury_id'],inst1['instrument_id'],1000,200,'CAD',primary_treasury_bps=2500,secondary_royalty_bps=150,derivative_participation_bps=100,terms={'raw_redistribution':'PROHIBITED'})
profile.allocate_eep_reserve(exchange,policy1['policy_id'])
venue=exchange.create_venue(originator,'Developer Rights Venue','CA',['ORDER_BOOK','RFQ'],h('venue-policy'))
disc=exchange.publish_disclosure(venue['venue_id'],inst1['instrument_id'],originator,'OFFERING',h('wildfire-disclosure'))
exchange.list_instrument(venue['venue_id'],inst1['instrument_id'],originator,1,1,disc['content_sha256'])
require(exchange.balance(inst1['instrument_id'],treasury_entity)==200,'reserve allocation')
record('01_dco_issue_and_reserve',{'dco_id':dco1['object_id'],'instrument_id':inst1['instrument_id'],'originator_units':800,'treasury_reserve_units':200,'protocol_tax_bps':0})

def settle_trade(eep,trade,payref,attestor=originator):
    att=eep.attest_payment(trade['trade_id'],attestor,payref,h(payref+':evidence'))
    return eep.settle_trade(trade['trade_id'],payref,external_verified=True,payment_attestation_id=att['attestation_id'])
def trade_orderbook(eep,venue_id,instrument_id,seller,buyer,qty,price,tag):
    eep.submit_order(venue_id,instrument_id,seller,'SELL',qty,price,tag+'-sell')
    eep.submit_order(venue_id,instrument_id,buyer,'BUY',qty,price,tag+'-buy')
    trades=eep.match_order_book(venue_id,instrument_id); require(len(trades)==1,tag+' trade count')
    settle_trade(eep,trades[0],'synthetic-payment:'+tag)
    return trades[0]
def settle_obligation(result,tag):
    oid=result['obligation']['obligation_id']
    return profile.settle_obligation(oid,verifier,'synthetic-bank:'+tag,external_verified=True,evidence_sha256=h(tag+':settlement-evidence'))

# Scenario 2: primary sale creates explicit treasury participation obligation.
primary=trade_orderbook(exchange,venue['venue_id'],inst1['instrument_id'],originator,buyer1,100,200,'primary-100x200')
primary_cap=profile.capture_settled_eep_trade(exchange,primary['trade_id'])
require(primary_cap['trade_class']=='PRIMARY','primary class')
require(primary_cap['gross_amount_units']==20000,'primary gross')
require(primary_cap['obligation']['amount_units']==5000,'primary treasury amount')
primary_settle=settle_obligation(primary_cap,'primary')
require(primary_settle['external_verified'] is True,'primary settlement attestation')
record('02_primary_sale_value_accumulation',{'gross_cad_units':20000,'treasury_obligation_cad_units':5000,'bps':2500,'buyer_entitlement_units':exchange.balance(inst1['instrument_id'],buyer1),'external_settlement_attested':True})

# Scenario 3: a holder resells part of the rights and the originator accrues a royalty.
secondary=trade_orderbook(exchange,venue['venue_id'],inst1['instrument_id'],buyer1,buyer2,25,300,'secondary-25x300')
secondary_cap=profile.capture_settled_eep_trade(exchange,secondary['trade_id'])
require(secondary_cap['trade_class']=='SECONDARY','secondary class')
require(secondary_cap['gross_amount_units']==7500,'secondary gross')
require(secondary_cap['obligation']['amount_units']==112,'secondary royalty floor')
secondary_settle=settle_obligation(secondary_cap,'secondary')
record('03_secondary_resale_originator_royalty',{'gross_cad_units':7500,'originator_royalty_cad_units':112,'bps':150,'seller_remaining_units':exchange.balance(inst1['instrument_id'],buyer1),'buyer2_units':exchange.balance(inst1['instrument_id'],buyer2),'external_settlement_attested':secondary_settle['external_verified']})

# Scenario 4: derivative economic consequences accumulate independently over time.
derivative_results=[]
for tag,gross in [('model-a',100000),('model-b',250000),('model-c',75000)]:
    r=profile.record_derivative_revenue(policy1['policy_id'],buyer1,'derivative:'+tag,gross,'CAD',h('derivative-evidence:'+tag),occurrence_ref='occurrence:'+tag)
    derivative_results.append(r)
require([x['obligation']['amount_units'] for x in derivative_results]==[1000,2500,750],'derivative amounts')
settle_obligation(derivative_results[0],'derivative-a'); settle_obligation(derivative_results[1],'derivative-b')
record('04_derivative_revenue_participation',{'gross_events_cad_units':[100000,250000,75000],'originator_participation_cad_units':[1000,2500,750],'bps':100,'settled_cad_units':3500,'accrued_cad_units':750})

# Scenario 5: service receivables can accumulate beside rights-market economics.
service_results=[]
for service,amount,tag in [('MARKET_DATA',500,'svc-market'),('API',1250,'svc-api'),('CERTIFICATION',750,'svc-cert')]:
    service_results.append(profile.record_service_revenue(treasury['treasury_id'],buyer2,service,amount,'CAD','invoice:'+tag))
settle_obligation(service_results[0],'svc-market'); settle_obligation(service_results[1],'svc-api')
record('05_service_revenue_accumulation',{'service_receivables_cad_units':[500,1250,750],'settled_cad_units':1750,'accrued_cad_units':750,'provider_asserted_receivable':True})

# Scenario 6: multi-contributor revenue distribution binds at trade execution.
dco2=fabric.register_digital_commodity(originator,'Agriculture Observation Corpus',h('agri-corpus'),commodity_class='AGRICULTURE_OBSERVATIONS')
inst2=exchange.define_instrument(originator,dco2['object_id'],'SPOT_LICENSE',{'actions':['TRAIN','DERIVE']},1000,'CAD',transferable=True)
disc2=exchange.publish_disclosure(venue['venue_id'],inst2['instrument_id'],originator,'OFFERING',h('agri-disclosure'))
exchange.list_instrument(venue['venue_id'],inst2['instrument_id'],originator,1,1,disc2['content_sha256'])
exchange.set_revenue_rules(inst2['instrument_id'],originator,{originator:7000,contrib_a:2000,contrib_b:1000},nonce='split-v1')
trade2=trade_orderbook(exchange,venue['venue_id'],inst2['instrument_id'],originator,buyer2,10,1000,'multi-split')
with exchange._db() as db:
    rev2=[dict(r) for r in db.execute('SELECT * FROM revenue_events WHERE trade_id=? ORDER BY recipient',(trade2['trade_id'],)).fetchall()]
amounts2={r['recipient']:int(r['amount_units']) for r in rev2}
require(amounts2=={originator:7000,contrib_a:2000,contrib_b:1000},'multi contributor split')
record('06_multi_contributor_trade_distribution',{'gross_cad_units':10000,'distribution_cad_units':{'originator':7000,'contributor_a':2000,'contributor_b':1000},'trade_time_rule_bound':True})

# Scenario 7: RFQ path uses a later rule set, then remains bound even if rules change before settlement.
exchange.set_revenue_rules(inst2['instrument_id'],originator,{originator:6000,contrib_a:2500,contrib_b:1500},nonce='split-v2')
expiry=hard_mod.now_ms()+60000
rfq=exchange.open_rfq(venue['venue_id'],inst2['instrument_id'],buyer1,'BUY',5,expiry,'rfq-buy-5')
quote=exchange.quote_rfq(rfq['rfq_id'],originator,1200,expiry,'rfq-quote-originator')
accepted=exchange.accept_quote(rfq['rfq_id'],quote['quote_id'],buyer1,'rfq-accept')
exchange.set_revenue_rules(inst2['instrument_id'],originator,{originator:10000},nonce='split-v3-after-trade')
rfq_trade={'trade_id':accepted['trade_id']}
settle_trade(exchange,rfq_trade,'synthetic-payment:rfq')
with exchange._db() as db:
    rev_rfq=[dict(r) for r in db.execute('SELECT * FROM revenue_events WHERE trade_id=? ORDER BY recipient',(accepted['trade_id'],)).fetchall()]
rfq_amounts={r['recipient']:int(r['amount_units']) for r in rev_rfq}
require(rfq_amounts=={originator:3600,contrib_a:1500,contrib_b:900},'RFQ trade-time split')
record('07_rfq_negotiated_trade_and_rule_binding',{'gross_cad_units':6000,'quote_price':1200,'quantity':5,'distribution_cad_units':{'originator':3600,'contributor_a':1500,'contributor_b':900},'later_rule_change_did_not_rewrite_trade':True})

# Scenario 8: reference CALL_AUCTION performs deterministic batch price discovery.
dco3=fabric.register_digital_commodity(originator,'Code Training Corpus',h('code-corpus'),commodity_class='SOFTWARE_TRAINING_CORPUS')
ref_root=STATE/'reference_auction'; ref_root.mkdir(exist_ok=True)
ref=ref_mod.ExchangeProtocol(ref_root,identity,fabric)
ref_venue=ref.create_venue(originator,'Reference Auction Venue','CA',['ORDER_BOOK','CALL_AUCTION','RFQ'],h('auction-policy'))
ref_inst=ref.define_instrument(originator,dco3['object_id'],'SPOT_LICENSE',{'actions':['TRAIN','DERIVE'],'raw_redistribution':False},1000,'CAD',transferable=True)
ref_disc=ref.publish_disclosure(ref_venue['venue_id'],ref_inst['instrument_id'],originator,'LISTING',h('auction-disclosure'))
ref.list_instrument(ref_venue['venue_id'],ref_inst['instrument_id'],originator,min_lot=1,tick_size=1,disclosure_sha256=ref_disc['content_sha256'])
ref.submit_order(ref_venue['venue_id'],ref_inst['instrument_id'],originator,'SELL',100,80,nonce='auction-sell')
ref.submit_order(ref_venue['venue_id'],ref_inst['instrument_id'],buyer1,'BUY',60,100,nonce='auction-buy1')
ref.submit_order(ref_venue['venue_id'],ref_inst['instrument_id'],buyer2,'BUY',40,90,nonce='auction-buy2')
auction=ref.run_call_auction(ref_venue['venue_id'],ref_inst['instrument_id'])
require(auction['executed'] and auction['clearing_price']==80 and auction['executed_volume']==100,'call auction')
for i,tid in enumerate(auction['trade_ids']):
    pay='synthetic-auction-payment:'+str(i); att=ref.attest_payment(tid,originator,pay,h(pay+':evidence')); ref.settle_trade(tid,payment_ref=pay,external_verified=True,payment_attestation_id=att['attestation_id'])
ref.set_revenue_rule(ref_inst['instrument_id'],{originator:8000,contrib_a:2000},issuer=originator,nonce='auction-contractual-split')
auction_distribution=ref.distribute_revenue(ref_inst['instrument_id'],8000)
record('08_call_auction_price_discovery',{'clearing_price':80,'executed_volume':100,'gross_cad_units':8000,'buyer1_units':ref.balance(ref_inst['instrument_id'],buyer1),'buyer2_units':ref.balance(ref_inst['instrument_id'],buyer2),'contractual_distribution_example':auction_distribution['distributions'],'distribution_is_calculation_not_settlement_event':True})

# Scenario 9: compute-to-data rights permit computation but fail closed on raw-copy delivery.
dco4=fabric.register_digital_commodity(originator,'Sensitive Sensor Corpus',h('sensor-corpus'),commodity_class='SENSITIVE_SENSOR_DATA')
inst4=exchange.define_instrument(originator,dco4['object_id'],'COMPUTE_TO_DATA',{'actions':['TRAIN','COPY']},100,'CAD',transferable=False,delivery_mode='COMPUTE_TO_DATA')
disc4=exchange.publish_disclosure(venue['venue_id'],inst4['instrument_id'],originator,'OFFERING',h('sensor-disclosure'))
exchange.list_instrument(venue['venue_id'],inst4['instrument_id'],originator,1,1,disc4['content_sha256'])
t4=trade_orderbook(exchange,venue['venue_id'],inst4['instrument_id'],originator,buyer1,1,50,'compute-license')
train_usage=exchange.meter_usage(inst4['instrument_id'],buyer1,'TRAIN',3,'usage-train')
copy_blocked=False
try: exchange.meter_usage(inst4['instrument_id'],buyer1,'COPY',1,'usage-copy')
except PermissionError: copy_blocked=True
require(copy_blocked,'compute-to-data copy must fail closed')
record('09_compute_to_data_entitlement_enforcement',{'entitlement_units':1,'train_usage_units':train_usage['units'],'copy_blocked':copy_blocked,'ownership_of_underlying_transferred':False})

# Scenario 10: policy changes affect future economics but cannot rewrite a prior trade.
old_policy_trade=trade_orderbook(exchange,venue['venue_id'],inst1['instrument_id'],originator,buyer1,4,250,'policy-old')
time.sleep(0.02)
policy2=profile.define_participation(originator,treasury['treasury_id'],inst1['instrument_id'],1000,200,'CAD',primary_treasury_bps=5000,secondary_royalty_bps=500,derivative_participation_bps=500,version=2,terms={'raw_redistribution':'PROHIBITED'})
old_capture=profile.capture_settled_eep_trade(exchange,old_policy_trade['trade_id'])
require(old_capture['obligation']['bps']==2500 and old_capture['obligation']['amount_units']==250,'historical trade policy binding')
settle_obligation(old_capture,'policy-old')
future_trade=trade_orderbook(exchange,venue['venue_id'],inst1['instrument_id'],originator,buyer1,2,250,'policy-new')
future_capture=profile.capture_settled_eep_trade(exchange,future_trade['trade_id'])
require(future_capture['obligation']['bps']==5000 and future_capture['obligation']['amount_units']==250,'future policy economics')
settle_obligation(future_capture,'policy-new')
record('10_policy_versioning_no_retroactive_rewrite',{'prior_trade_gross_cad_units':1000,'prior_trade_bps':2500,'prior_obligation_cad_units':250,'future_trade_gross_cad_units':500,'future_trade_bps':5000,'future_obligation_cad_units':250,'no_retroactive_economic_rights':True})

# Scenario 11: fail-closed controls block synthetic value inflation and unauthorized state changes.
fail_closed={}
try: exchange.submit_order(venue['venue_id'],inst1['instrument_id'],buyer1,'SELL',10000,1,'oversell')
except PermissionError: fail_closed['oversell_blocked']=True
rogue=identity.create('Unauthorized Settlement Actor','system')['entity_id']
try: profile.settle_obligation(service_results[2]['obligation']['obligation_id'],rogue,'synthetic-bank:rogue',external_verified=True,evidence_sha256=h('rogue'))
except PermissionError: fail_closed['unauthorized_settlement_blocked']=True
try: profile.record_derivative_revenue(policy1['policy_id'],buyer1,'derivative:model-a',100000,'CAD',h('derivative-evidence:model-a'),occurrence_ref='occurrence:model-a')
except ValueError: fail_closed['duplicate_derivative_blocked']=True
try: profile.record_derivative_revenue(policy1['policy_id'],buyer1,'derivative:wrong-currency',1000,'USD',h('wrong-currency'),occurrence_ref='occurrence:wrong-currency')
except ValueError: fail_closed['wrong_currency_blocked']=True
body={'schema':'entity-eep-order-v1','order_id':'tampered-order','venue_id':venue['venue_id'],'instrument_id':inst1['instrument_id'],'participant':buyer1,'side':'BUY','quantity':1,'limit_price':100,'tif':'GTC','nonce':'tamper-nonce','created_at_ms':hard_mod.now_ms()}
sig=identity.sign(buyer1,body); tampered=dict(body,quantity=2)
try: exchange.submit_signed_order(tampered,sig)
except PermissionError: fail_closed['tampered_signature_blocked']=True
require(all(fail_closed.get(k) for k in ['oversell_blocked','unauthorized_settlement_blocked','duplicate_derivative_blocked','wrong_currency_blocked','tampered_signature_blocked']),'fail closed matrix')
record('11_value_integrity_fail_closed_matrix',fail_closed)

# Scenario 12: aggregate the synthetic portfolio without calling it fair market value.
pos=profile.position(treasury['treasury_id'],exchange)
mark=profile.indicative_mark(treasury['treasury_id'],exchange,'LAST')
snapshot=profile.seal_snapshot(treasury['treasury_id'],originator,exchange)
with profile._db() as db:
    obs=[dict(r) for r in db.execute("SELECT * FROM obligations WHERE currency='CAD'").fetchall()]
    ev_count=int(db.execute('SELECT COUNT(*) FROM economic_events').fetchone()[0])
with exchange._db() as db:
    rev_events=[dict(r) for r in db.execute('SELECT * FROM revenue_events').fetchall()]
    ex_counts={t:int(db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]) for t in ['instruments','listings','orders','trades','clearing','entitlements','usage','rfqs','quotes','rfq_acceptances','revenue_rule_sets','trade_revenue_bindings']}
settled=sum(int(o['amount_units']) for o in obs if o['status']=='SETTLED')
accrued=sum(int(o['amount_units']) for o in obs if o['status']=='ACCRUED')
eopp_total=sum(int(o['amount_units']) for o in obs)
inst2_revenue=sum(int(r['amount_units']) for r in rev_events if r['trade_id'] in {trade2['trade_id'],accepted['trade_id']})
require(eopp_total==12362,'expected EOPP total')
require(settled==10862 and accrued==1500,'expected obligation states')
require(inst2_revenue==16000,'expected contributor distribution total')
synthetic_recorded=eopp_total+inst2_revenue
record('12_portfolio_accumulation_and_snapshot',{'eopp_obligations_total_cad_units':eopp_total,'eopp_settled_attested_cad_units':settled,'eopp_accrued_cad_units':accrued,'multi_contributor_trade_distributions_cad_units':inst2_revenue,'synthetic_recorded_economic_allocations_or_obligations_cad_units':synthetic_recorded,'indicative_mark':mark,'indicative_mark_is_not_accounting_fair_value':True,'snapshot_id':snapshot.get('snapshot_id'),'exchange_counts':ex_counts,'economic_event_count':ev_count})

result={
 'schema':'entity-v343-developer-economy-scenario-suite-v1',
 'runtime_release':'v3.4.3',
 'source_tree':str(REPO),
 'synthetic_only':True,
 'currency':'CAD',
 'amount_semantics':'integer CAD-denominated synthetic test units; not real money movement unless explicitly described as a synthetic external-settlement attestation',
 'dco_count':4,
 'execution_models_exercised':['ORDER_BOOK','RFQ','CALL_AUCTION'],
 'scenarios':scenarios,
 'scenario_count':len(scenarios),
 'pass':all(x['pass'] for x in scenarios),
 'portfolio_summary':{'eopp_obligations_total_cad_units':eopp_total,'settled_attested_cad_units':settled,'accrued_cad_units':accrued,'multi_contributor_distribution_events_cad_units':inst2_revenue,'synthetic_recorded_economic_allocations_or_obligations_cad_units':synthetic_recorded},
 'claim_boundary':'Proves that ENTITY can represent, bind, accumulate, distribute, reconcile and preserve synthetic economic consequences attached to data rights under explicit policies and test transactions. It does not prove market demand, fair market value, revenue, receivables, cash balances, investment returns, or legal enforceability.'
}
out=ROOT/'ECONOMY_VALUE_SCENARIOS_RESULT.json'; out.write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
print('ECONOMY_VALUE_SCENARIOS_PASS',result['pass'],'SCENARIOS',len(scenarios),'SYNTHETIC_RECORDED',synthetic_recorded,'SETTLED',settled,'ACCRUED',accrued)

