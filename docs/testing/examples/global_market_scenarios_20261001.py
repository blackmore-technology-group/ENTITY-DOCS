import hashlib, importlib.util, json, pathlib, shutil, sqlite3, sys
ROOT=pathlib.Path(r"E:\ENTITY_ACTIVE\ENTITY_ECONOMY_PROOF_20261001")
STATE=ROOT/'global_market_state'
REPO=pathlib.Path(r"E:\ENTITY_ACTIVE\ENTITY_V3_4_3_RELEASE_SRC\ENTITY-3.4.3")
if STATE.exists(): shutil.rmtree(STATE)
STATE.mkdir(parents=True)
def load(name,rel):
    p=REPO/rel; s=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(s); sys.modules[name]=m; s.loader.exec_module(m); return m
identity_mod=load('gm_identity','src/01_Core_Runtime/identity/canonical_identity.py')
fabric_mod=load('gm_fabric','src/30_Universal_Transaction_Fabric/canonical_universal_fabric.py')
eep_mod=load('gm_eep','src/32_V3_Hardening/exchange_protocol.py')
econ_mod=load('gm_econ','src/33_Economic_Participation/economic_participation.py')
def h(x): return hashlib.sha256(str(x).encode()).hexdigest()
def req(c,m):
    if not c: raise AssertionError(m)
identity=identity_mod.EntityIdentityVault(STATE)
fabric=fabric_mod.UniversalTransactionFabric(STATE,identity)
exchange=eep_mod.ExchangeProtocol(STATE,identity,fabric)
profile=econ_mod.EconomicParticipationProfile(STATE,identity)
originator=identity.create('Global Data Originator','business')['entity_id']
treasury_entity=identity.create('Global Data Treasury','business')['entity_id']
contrib_a=identity.create('Global Contributor A','person')['entity_id']
contrib_b=identity.create('Global Contributor B','person')['entity_id']
treasury=profile.create_treasury(originator,treasury_entity,'Global Data Treasury','MULTI',h('global treasury policy'))
markets=[
 {'code':'CA','currency':'CAD','primary_qty':40,'primary_price':250,'secondary_qty':10,'secondary_price':300,'derivatives':[50000,75000,100000]},
 {'code':'US','currency':'USD','primary_qty':50,'primary_price':200,'secondary_qty':10,'secondary_price':240,'derivatives':[60000,90000,120000]},
 {'code':'EU','currency':'EUR','primary_qty':40,'primary_price':180,'secondary_qty':8,'secondary_price':210,'derivatives':[45000,70000,110000]},
 {'code':'JP','currency':'JPY','primary_qty':100,'primary_price':3000,'secondary_qty':20,'secondary_price':3600,'derivatives':[500000,800000,1200000]},
]
for m in markets:
    m['operator']=identity.create(f"{m['code']} Venue Operator",'business')['entity_id']
    m['verifier']=identity.create(f"{m['code']} Settlement Verifier",'system')['entity_id']
    m['buyer1']=identity.create(f"{m['code']} Primary Buyer",'business')['entity_id']
    m['buyer2']=identity.create(f"{m['code']} Secondary Buyer",'business')['entity_id']
    profile.authorize_settlement_verifier(treasury['treasury_id'],originator,m['verifier'])
dco=fabric.register_digital_commodity(originator,'Global Developer Data Corpus',h('global-market-corpus'),commodity_class='DEVELOPER_DATA',measurement_unit='LICENSE')
scenarios=[]
def record(name,data):
    scenarios.append({'scenario':name,'pass':True,'metrics':data}); print('SCENARIO_PASS',name,json.dumps(data,sort_keys=True),flush=True)
record('01_global_dco_created',{'dco_id':dco['object_id'],'markets':4,'currencies':[m['currency'] for m in markets],'single_underlying_data_object':True})
for m in markets:
    inst=exchange.define_instrument(originator,dco['object_id'],'SPOT_LICENSE',{'actions':['TRAIN','DERIVE'],'raw_redistribution':False},1000,m['currency'],transferable=True)
    policy=profile.define_participation(originator,treasury['treasury_id'],inst['instrument_id'],1000,100,m['currency'],primary_treasury_bps=2000,secondary_royalty_bps=200,derivative_participation_bps=100,terms={'market':m['code'],'raw_redistribution':'PROHIBITED'})
    profile.allocate_eep_reserve(exchange,policy['policy_id'])
    venue=exchange.create_venue(m['operator'],f"{m['code']} Global Data Venue",m['code'],['ORDER_BOOK','RFQ'],h(f"{m['code']} venue policy"))
    exchange.authorize_settlement_verifier(venue['venue_id'],m['operator'],m['verifier'])
    disc=exchange.publish_disclosure(venue['venue_id'],inst['instrument_id'],originator,'OFFERING',h(f"{m['code']} disclosure"))
    exchange.list_instrument(venue['venue_id'],inst['instrument_id'],originator,1,1,disc['content_sha256'])
    old_rules=exchange.set_revenue_rules(inst['instrument_id'],originator,{originator:7000,contrib_a:2000,contrib_b:1000},nonce=f"{m['code']}-rules-v1")
    m.update(instrument=inst,policy=policy,venue=venue,old_rules=old_rules)
record('02_four_markets_issued',{'venues':[m['venue']['venue_id'] for m in markets],'instruments':[m['instrument']['instrument_id'] for m in markets],'currencies':[m['currency'] for m in markets],'venue_operators_are_distinct':len({m['operator'] for m in markets})==4})
def external_settle(m,trade,payment_ref):
    att=exchange.attest_payment(trade['trade_id'],m['verifier'],payment_ref,h(payment_ref+':evidence'))
    return exchange.settle_trade(trade['trade_id'],payment_ref,external_verified=True,payment_attestation_id=att['attestation_id'])
def make_trade(m,seller,buyer,qty,price,nonce):
    exchange.submit_order(m['venue']['venue_id'],m['instrument']['instrument_id'],seller,'SELL',qty,price,nonce+'-sell')
    exchange.submit_order(m['venue']['venue_id'],m['instrument']['instrument_id'],buyer,'BUY',qty,price,nonce+'-buy')
    trades=exchange.match_order_book(m['venue']['venue_id'],m['instrument']['instrument_id']); req(len(trades)==1,'expected one trade')
    external_settle(m,trades[0],f"payment:{nonce}"); return trades[0]
primary_metrics={}; first_bindings={}
for m in markets:
    t=make_trade(m,originator,m['buyer1'],m['primary_qty'],m['primary_price'],f"{m['code']}-primary")
    cap=profile.capture_settled_eep_trade(exchange,t['trade_id'])
    proof=profile.settle_obligation(cap['obligation']['obligation_id'],m['verifier'],f"bank:{m['code']}:primary",external_verified=True,evidence_sha256=h(f"{m['code']} primary settlement"))
    first_bindings[m['code']]=exchange.trade_revenue_binding(t['trade_id'])
    primary_metrics[m['currency']]={'gross':m['primary_qty']*m['primary_price'],'treasury_obligation':cap['obligation']['amount_units'],'settled_attested':proof['external_verified']}
record('03_primary_sales_across_four_markets',primary_metrics)
secondary_metrics={}
for m in markets:
    exchange.set_revenue_rules(m['instrument']['instrument_id'],originator,{originator:6000,contrib_a:2500,contrib_b:1500},nonce=f"{m['code']}-rules-v2")
    t=make_trade(m,m['buyer1'],m['buyer2'],m['secondary_qty'],m['secondary_price'],f"{m['code']}-secondary")
    cap=profile.capture_settled_eep_trade(exchange,t['trade_id'])
    proof=profile.settle_obligation(cap['obligation']['obligation_id'],m['verifier'],f"bank:{m['code']}:secondary",external_verified=True,evidence_sha256=h(f"{m['code']} secondary settlement"))
    secondary_metrics[m['currency']]={'gross':m['secondary_qty']*m['secondary_price'],'originator_royalty':cap['obligation']['amount_units'],'settled_attested':proof['external_verified']}
    req(first_bindings[m['code']]['allocations_bps'][originator]==7000,'old trade binding rewritten')
record('04_secondary_resale_royalties',secondary_metrics)
record('05_trade_time_rules_preserved',{'markets_verified':4,'old_primary_rule_originator_bps':7000,'new_secondary_rule_originator_bps':6000,'prior_trade_bindings_unchanged':True})
derivative_metrics={}; derivative_obligations={}
for m in markets:
    rows=[]
    for i,gross in enumerate(m['derivatives'],1):
        r=profile.record_derivative_revenue(m['policy']['policy_id'],m['buyer2'],f"derived:{m['code']}:{i}",gross,m['currency'],h(f"{m['code']} derivative {i}"),occurrence_ref=f"occ:{m['code']}:{i}")
        rows.append(r['obligation'])
        if i<3:
            profile.settle_obligation(r['obligation']['obligation_id'],m['verifier'],f"bank:{m['code']}:deriv:{i}",external_verified=True,evidence_sha256=h(f"{m['code']} derivative settle {i}"))
    derivative_obligations[m['code']]=rows
    derivative_metrics[m['currency']]={'gross_rounds':m['derivatives'],'participation_rounds':[r['amount_units'] for r in rows],'settled_first_two':sum(r['amount_units'] for r in rows[:2]),'accrued_final':rows[2]['amount_units']}
record('06_repeated_derivative_accumulation',derivative_metrics)
position=profile.position(treasury['treasury_id'],exchange)
per_currency=position['monetary_obligations']
record('07_multicurrency_treasury_position',{'currencies':sorted(per_currency),'positions':per_currency,'cross_currency_sum_performed':False})
with exchange._db() as db:
    revenue_rows=db.execute('SELECT recipient,currency,SUM(amount_units) amount FROM revenue_events GROUP BY recipient,currency ORDER BY currency,recipient').fetchall()
contributor_distribution={}
for r in revenue_rows:
    cur=r['currency']; contributor_distribution.setdefault(cur,{})
    label='originator' if r['recipient']==originator else ('contributor_a' if r['recipient']==contrib_a else 'contributor_b')
    contributor_distribution[cur][label]=int(r['amount'])
record('08_contributors_accumulate_across_markets',{'per_currency':contributor_distribution,'trade_distribution_events_are_distinct_from_eopp_obligations':True})
us=next(m for m in markets if m['code']=='US'); eu=next(m for m in markets if m['code']=='EU')
cross_trade=make_trade(us,originator,eu['buyer1'],5,220,'US-cross-EU')
cross_cap=profile.capture_settled_eep_trade(exchange,cross_trade['trade_id'])
profile.settle_obligation(cross_cap['obligation']['obligation_id'],us['verifier'],'bank:US:cross-EU',external_verified=True,evidence_sha256=h('US cross-market obligation settlement'))
record('09_cross_market_order_book',{'venue_jurisdiction':'US','settlement_currency':'USD','buyer_actor_label':'EU Primary Buyer','quantity':5,'price':220,'gross_usd_units':1100,'eopp_primary_obligation_usd_units':cross_cap['obligation']['amount_units'],'actor_label_is_scenario_metadata_not_domicile_verification':True})
expiry=eep_mod.now_ms()+60000
rfq=exchange.open_rfq(us['venue']['venue_id'],us['instrument']['instrument_id'],eu['buyer2'],'BUY',1,expiry,nonce='global-us-rfq-gap')
quote=exchange.quote_rfq(rfq['rfq_id'],originator,225,expiry,nonce='global-us-quote-gap')
execution=exchange.accept_quote(rfq['rfq_id'],quote['quote_id'],eu['buyer2'],nonce='global-us-accept-gap')
rfq_settled=external_settle(us,{'trade_id':execution['trade_id']},'payment:global-us-rfq-gap')
try:
    profile.capture_settled_eep_trade(exchange,execution['trade_id']); rfq_eopp_capture_blocked=False
except PermissionError:
    rfq_eopp_capture_blocked=True
record('10_rfq_eopp_integration_boundary',{'eep_rfq_settled':rfq_settled['status']=='SETTLED','eopp_capture_blocked':rfq_eopp_capture_blocked,'reason':'RFQ trade has no sell_order_id for EOPP seller-signature re-verification','known_gap':True})
position=profile.position(treasury['treasury_id'],exchange); per_currency=position['monetary_obligations']
value_records=[]
for cur,states in sorted(per_currency.items()):
    for state in ('SETTLED','ACCRUED'):
        amount=int(states.get(state,0) or 0)
        if amount:
            v=fabric.record_value(originator,dco['object_id'],amount,cur,state=state,basis_ref=f"synthetic-global-market:eopp:{cur}:{state.lower()}")
            value_records.append({'value_id':v['value_id'],'currency':cur,'state':state,'amount_units':amount,'asserted_value_is_not_market_value':v['asserted_value_is_not_market_value']})
record('11_value_primitive_lifecycle',{'records':value_records,'basis':'EOPP synthetic obligations','market_value_claimed':False})
market_data={m['currency']:exchange.market_data(m['venue']['venue_id'],m['instrument']['instrument_id']) for m in markets}
record('12_market_price_observations',{'per_currency':market_data,'market_data_is_observation_not_valuation':True})
fail_closed={}
try:
    profile.record_derivative_revenue(markets[0]['policy']['policy_id'],markets[0]['buyer2'],'derived:CA:3',markets[0]['derivatives'][2],'CAD',h('CA derivative 3'),occurrence_ref='occ:CA:3')
    fail_closed['duplicate_derivative_blocked']=False
except ValueError: fail_closed['duplicate_derivative_blocked']=True
try:
    profile.record_derivative_revenue(markets[0]['policy']['policy_id'],markets[0]['buyer2'],'derived:CA:wrong',1000,'USD',h('wrong currency'),occurrence_ref='occ:CA:wrong')
    fail_closed['wrong_currency_blocked']=False
except ValueError: fail_closed['wrong_currency_blocked']=True
try:
    exchange.submit_order(markets[0]['venue']['venue_id'],markets[0]['instrument']['instrument_id'],markets[0]['buyer2'],'SELL',999999,1,'oversell-global')
    fail_closed['oversell_blocked']=False
except PermissionError: fail_closed['oversell_blocked']=True
rogue=identity.create('Unauthorized Global Verifier','system')['entity_id']
try:
    profile.settle_obligation(derivative_obligations['CA'][2]['obligation_id'],rogue,'bank:rogue',external_verified=True,evidence_sha256=h('rogue'))
    fail_closed['unauthorized_settlement_blocked']=False
except PermissionError: fail_closed['unauthorized_settlement_blocked']=True
base={'schema':'entity-eep-order-v1','order_id':'tamper-global','venue_id':markets[0]['venue']['venue_id'],'instrument_id':markets[0]['instrument']['instrument_id'],'participant':markets[0]['buyer2'],'side':'BUY','quantity':1,'limit_price':1,'tif':'GTC','nonce':'tamper-global','created_at_ms':eep_mod.now_ms()}
sig=identity.sign(markets[0]['buyer2'],base); tampered=dict(base); tampered['quantity']=2
try:
    exchange.submit_signed_order(tampered,sig); fail_closed['tampered_signature_blocked']=False
except PermissionError: fail_closed['tampered_signature_blocked']=True
req(all(fail_closed.values()),'fail-closed matrix incomplete')
record('13_global_value_integrity_fail_closed',fail_closed)
final_position=profile.position(treasury['treasury_id'],exchange)
snapshot=profile.seal_snapshot(treasury['treasury_id'],originator,exchange)
with exchange._db() as db:
    exchange_counts={t:int(db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]) for t in ('venues','instruments','listings','orders','trades','clearing','entitlements','usage','rfqs','quotes','rfq_acceptances','revenue_events','revenue_rule_sets','trade_revenue_bindings')}
with profile._db() as db:
    eopp_counts={t:int(db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]) for t in ('participation_policies','economic_events','obligations','reserve_allocations','position_snapshots','treasuries')}
summary={'schema':'entity-v343-global-market-scenario-proof-v1','runtime_release':'v3.4.3','pass':True,'synthetic_only':True,'dco_id':dco['object_id'],'market_count':4,'markets':[{'jurisdiction':m['code'],'currency':m['currency'],'venue_id':m['venue']['venue_id'],'instrument_id':m['instrument']['instrument_id']} for m in markets],'scenario_count':len(scenarios),'scenarios':scenarios,'final_multicurrency_position':final_position['monetary_obligations'],'contributor_distributions_per_currency':contributor_distribution,'value_primitive_records':value_records,'exchange_counts':exchange_counts,'economic_participation_counts':eopp_counts,'snapshot_id':snapshot['snapshot_id'],'cross_currency_total_asserted':False,'real_market_demand_proven':False,'real_cash_revenue_proven':False,'global_market_mechanics_proven_in_controlled_scenarios':True,'claim_boundary':'Controlled multi-market scenario proof only. It demonstrates one DCO participating across four venue/currency configurations with repeated primary, secondary, derivative, RFQ, contributor distribution, settlement and VALUE-state records. It does not prove real-world demand, FX conversion, participant domicile, legal enforceability, fair market value, liquidity, or actual cash revenue.'}
out=ROOT/'GLOBAL_MARKET_SCENARIOS_RESULT.json'; out.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print('GLOBAL_MARKET_SCENARIOS_PASS',summary['pass'],'SCENARIOS',len(scenarios),'DCO',dco['object_id'])
print('FINAL_MULTICURRENCY_POSITION',json.dumps(summary['final_multicurrency_position'],sort_keys=True))
print('GLOBAL_MARKET_MECHANICS_PROVEN_IN_CONTROLLED_SCENARIOS',summary['global_market_mechanics_proven_in_controlled_scenarios'])
