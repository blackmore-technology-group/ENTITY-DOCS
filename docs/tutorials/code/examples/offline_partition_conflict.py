from pathlib import Path
import importlib.util, hashlib, os, shutil, time
ROOT=Path(os.environ.get("ENTITY_ROOT", Path.cwd())).resolve(); STATE=ROOT/".tutorial-test-state"/"offline-partition"
if STATE.exists(): shutil.rmtree(STATE)
def load_source(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
identity_mod=load_source("src/01_Core_Runtime/identity/canonical_identity.py","entity_identity")
topo_mod=load_source("src/35_Global_Infrastructure/topology_crypto.py","entity_topology")
identity=identity_mod.EntityIdentityVault(STATE); op_a=identity.create("Edge Operator A","organization"); op_b=identity.create("Edge Operator B","organization")
topology=topo_mod.TopologyRegistry(STATE,identity); topology.register_node(op_a["entity_id"],"edge-a","EDGE","CA","tutorial-edge-a",["OFFLINE_CAPTURE"]); topology.register_node(op_b["entity_id"],"edge-b","EDGE","CA","tutorial-edge-b",["OFFLINE_CAPTURE"])
payload={"observation":"sample","sequence":1}; envelope=topo_mod.OfflineEnvelope.create(identity,op_a["entity_id"],"edge-a","partition-a",1,payload,expires_at_ms=int(time.time()*1000)+60000); assert topo_mod.OfflineEnvelope.verify(identity,envelope)["valid"] is True
sync=topo_mod.PartitionSync(STATE,identity); root_a=hashlib.sha256(b"state-a").hexdigest(); root_b=hashlib.sha256(b"state-b").hexdigest()
sync.publish("edge-a",op_a["entity_id"],"partition-a",sequence=1,epoch=1,state_root_sha256=root_a,vector_clock={"edge-a":1})
sync.publish("edge-b",op_b["entity_id"],"partition-a",sequence=1,epoch=1,state_root_sha256=root_b,vector_clock={"edge-b":1})
conflict=sync.merge("partition-a"); assert conflict["resolved"] is False; assert conflict["reason"]=="CONCURRENT_DIVERGENT_STATE"; assert conflict["automatic_last_writer_wins_prohibited"] is True
print(f"OFFLINE_ENVELOPE={envelope['envelope_id']}"); print("OFFLINE_SIGNATURE_VERIFY=PASS"); print("PARTITION_MERGE=CONCURRENT_DIVERGENT_STATE"); print("AUTOMATIC_LAST_WRITER_WINS=BLOCKED"); print(f"CONFLICT_ID={conflict['conflict_id']}"); print("CLAIM_BOUNDARY=causal conflict detection preserves ambiguity instead of inventing convergence")
