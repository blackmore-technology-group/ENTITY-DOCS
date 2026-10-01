import hashlib, importlib.util, json, pathlib, sys
ROOT=pathlib.Path(r"E:\ENTITY_ACTIVE\ENTITY_ECONOMY_PROOF_20261001")
STATE=ROOT/'derived_state'; STATE.mkdir(exist_ok=True)
REPO=pathlib.Path(r"E:\ENTITY_ACTIVE\ENTITY_V3_4_3_RELEASE_SRC\ENTITY-3.4.3")
def load(name,rel):
 p=REPO/rel; s=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(s); sys.modules[name]=m; s.loader.exec_module(m); return m
identity_mod=load('dvc_identity','src/01_Core_Runtime/identity/canonical_identity.py')
fabric_mod=load('dvc_fabric','src/30_Universal_Transaction_Fabric/canonical_universal_fabric.py')
eep_mod=load('dvc_eep','src/32_V3_Hardening/exchange_protocol.py')
econ_mod=load('dvc_econ','src/33_Economic_Participation/economic_participation.py')
def h(x): return hashlib.sha256(str(x).encode()).hexdigest()
def req(c,m):
 if not c: raise AssertionError(m)
idv=identity_mod.EntityIdentityVault(STATE)
owner_a=idv.create('Source A Originator','business')['entity_id']; owner_b=idv.create('Source B Originator','business')['entity_id']; developer=idv.create('Derived Model Developer','business')['entity_id']; verifier=idv.create('Settlement Verifier','system')['entity_id']; ta=idv.create('Treasury A','business')['entity_id']; tb=idv.create('Treasury B','business')['entity_id']
fabric=fabric_mod.UniversalTransactionFabric(STATE,idv); eep=eep_mod.ExchangeProtocol(STATE,idv,fabric); econ=econ_mod.EconomicParticipationProfile(STATE,idv)
a=fabric.register_digital_commodity(owner_a,'Source Dataset A',h('source-a')); b=fabric.register_digital_commodity(owner_b,'Source Dataset B',h('source-b'))
ra=fabric.grant_right(a['object_id'],owner_a,developer,['TRAIN','DERIVE'],economic_terms={'derivative_participation_bps':1000}); rb=fabric.grant_right(b['object_id'],owner_b,developer,['TRAIN','DERIVE'],economic_terms={'derivative_participation_bps':1000})
ua=fabric.authorize_use(developer,developer,a['object_id'],'TRAIN',quantity=1,nonce='train-a'); ub=fabric.authorize_use(developer,developer,b['object_id'],'TRAIN',quantity=1,nonce='train-b')
child=fabric.register_object(developer,'MODEL','Derived Model AB',descriptor={'sources':2,'test':'derived-value-chain'})
fabric.add_provenance(developer,a['object_id'],child['object_id'],'TRAINED_FROM',contribution_bps=6000,evidence={'method':'declared-test-weight'}); fabric.add_provenance(developer,b['object_id'],child['object_id'],'TRAINED_FROM',contribution_bps=4000,evidence={'method':'declared-test-weight'})
dist=fabric.contribution_distribution(child['object_id'],50000); req(dist['distribution'][a['object_id']]==30000 and dist['distribution'][b['object_id']]==20000,'provenance distribution')
inst_a=eep.define_instrument(owner_a,a['object_id'],'SPOT_LICENSE',{'actions':['TRAIN','DERIVE']},100,'CAD',transferable=True); inst_b=eep.define_instrument(owner_b,b['object_id'],'SPOT_LICENSE',{'actions':['TRAIN','DERIVE']},100,'CAD',transferable=True)
treas_a=econ.create_treasury(owner_a,ta,'Source A Treasury','CA',h('ta')); treas_b=econ.create_treasury(owner_b,tb,'Source B Treasury','CA',h('tb'))
econ.authorize_settlement_verifier(treas_a['treasury_id'],owner_a,verifier); econ.authorize_settlement_verifier(treas_b['treasury_id'],owner_b,verifier)
pol_a=econ.define_participation(owner_a,treas_a['treasury_id'],inst_a['instrument_id'],100,0,'CAD',derivative_participation_bps=1000,terms={'derived_output_required':True}); pol_b=econ.define_participation(owner_b,treas_b['treasury_id'],inst_b['instrument_id'],100,0,'CAD',derivative_participation_bps=1000,terms={'derived_output_required':True})
ea=econ.record_derivative_revenue(pol_a['policy_id'],developer,child['object_id'],30000,'CAD',h('derived-revenue-evidence-a'),occurrence_ref='derived-ab:source-a'); eb=econ.record_derivative_revenue(pol_b['policy_id'],developer,child['object_id'],20000,'CAD',h('derived-revenue-evidence-b'),occurrence_ref='derived-ab:source-b')
req(ea['obligation']['amount_units']==3000 and eb['obligation']['amount_units']==2000,'derivative obligations')
sa=econ.settle_obligation(ea['obligation']['obligation_id'],verifier,'synthetic-bank:derived-a',external_verified=True,evidence_sha256=h('settle-a')); sb=econ.settle_obligation(eb['obligation']['obligation_id'],verifier,'synthetic-bank:derived-b',external_verified=True,evidence_sha256=h('settle-b'))
cycle_blocked=False
try: fabric.add_provenance(developer,child['object_id'],a['object_id'],'DERIVED_FROM',contribution_bps=1000)
except ValueError: cycle_blocked=True
req(cycle_blocked,'provenance cycle must fail closed')
result={'schema':'entity-v343-derived-output-value-chain-v1','runtime_release':'v3.4.3','pass':True,'synthetic_only':True,'source_dcos':[a['object_id'],b['object_id']],'rights_grants':[ra['right_id'],rb['right_id']],'authorized_use_events':[ua['event']['event_id'],ub['event']['event_id']],'derived_object_id':child['object_id'],'root_contribution_bps':dist['root_contribution_bps'],'synthetic_derived_gross_cad_units':50000,'provenance_allocated_gross_cad_units':dist['distribution'],'originator_derivative_obligations_cad_units':{a['object_id']:3000,b['object_id']:2000},'settled_attested_cad_units':5000,'cycle_blocked':cycle_blocked,'settlement_attestation_flags':[sa['verification_is_attestation_not_absolute_truth'],sb['verification_is_attestation_not_absolute_truth']],'claim_boundary':'Synthetic proof of explicit rights, authorized use, derived-object provenance, contribution distribution and derivative participation. Contribution weights are declared test inputs, not universal truth; settlement verification is attestation, not proof of real cash movement or market value.'}
(ROOT/'DERIVED_OUTPUT_VALUE_CHAIN_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
print('DERIVED_CHAIN_PASS',json.dumps(result,sort_keys=True))

