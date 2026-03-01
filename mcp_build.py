#!/usr/bin/env python3
"""
SignalBound Phase 1 Builder — sends MCP commands to Unreal Editor.
Run with: python3 mcp_build.py [step_numbers...]

Confirmed API details:
  - Blueprints created at /Game/Blueprints/ (path param ignored)
  - Components need full class path: /Script/Engine.StaticMeshComponent
  - Event exec output pin = "then", CallFunction exec input = "execute", output = "then"
  - Branch: input="execute", true="then", false="else", condition="Condition"
  - Functions: blueprint_name needs /Game/Blueprints/ path
  - Function I/O: param_name, param_type (not input_name/input_type)
  - spawn_blueprint_actor: blueprint_name, actor_name, location
"""
import socket
import json
import sys

HOST = '127.0.0.1'
PORT = 55557

def mcp(cmd_type, params=None, timeout=120):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4194304)
    sock.connect((HOST, PORT))
    command = {"type": cmd_type, "params": params or {}}
    sock.sendall(json.dumps(command).encode('utf-8'))
    chunks = []
    while True:
        try:
            chunk = sock.recv(262144)
            if not chunk: break
            chunks.append(chunk)
            try:
                return json.loads(b''.join(chunks).decode('utf-8'))
            except json.JSONDecodeError: continue
        except socket.timeout: break
    sock.close()
    return {"status": "error", "error": "timeout"}

def ok(resp, label=""):
    status = resp.get("status", "")
    result = resp.get("result", {})
    success = (status == "success") or resp.get("success", False) or (isinstance(result, dict) and result.get("success", False))
    if success:
        print(f"  OK: {label}")
        return True
    err = resp.get("error","") or (result.get("error","") if isinstance(result, dict) else str(result))
    print(f"  FAIL: {label} — {err[:80]}")
    return False

def nid(resp):
    r = resp.get("result", resp)
    return r.get("node_id", "") if isinstance(r, dict) else ""

# Component type constants
SM = "/Script/Engine.StaticMeshComponent"
SPHERE = "/Script/Engine.SphereComponent"
BOX = "/Script/Engine.BoxComponent"
CAPSULE = "/Script/Engine.CapsuleComponent"
SPRING = "/Script/Engine.SpringArmComponent"
CAM = "/Script/Engine.CameraComponent"

BP_PATH = "/Game/Blueprints"

def create_bp(name, parent="Actor"):
    r = mcp("create_blueprint", {"name": name, "parent_class": parent, "path": BP_PATH})
    return ok(r, f"create({name})")

def add_comp(bp, comp_type, comp_name, location=None, scale=None, props=None):
    p = {"blueprint_name": bp, "component_type": comp_type, "component_name": comp_name}
    if location: p["location"] = location
    if scale: p["scale"] = scale
    if props: p["component_properties"] = props
    return ok(mcp("add_component_to_blueprint", p), f"comp({bp}.{comp_name})")

def var(bp, name, vtype, default=None, cat=""):
    p = {"blueprint_name": bp, "variable_name": name, "variable_type": vtype, "is_instance_editable": True}
    if default is not None: p["default_value"] = str(default)
    if cat: p["category"] = cat
    return ok(mcp("create_variable", p), f"var({name}:{vtype}={default})")

def set_var(bp, name, val):
    return ok(mcp("set_blueprint_variable_properties", {"blueprint_name": bp, "variable_name": name, "default_value": str(val)}), f"set({name}={val})")

def event(bp, name, x=0, y=0):
    r = mcp("add_event_node", {"blueprint_name": bp, "event_name": name, "pos_x": x, "pos_y": y})
    i = nid(r)
    ok(r, f"event({name})→{i[:12]}")
    return i

def node(bp, ntype, params=None):
    r = mcp("add_blueprint_node", {"blueprint_name": bp, "node_type": ntype, "node_params": params or {}})
    i = nid(r)
    ok(r, f"node({ntype})→{i[:12]}")
    return i

def conn(bp, src, spin, tgt, tpin, fg=""):
    if not src or not tgt:
        print(f"  SKIP: missing id")
        return False
    p = {"blueprint_name": bp, "source_node_id": src, "source_pin_name": spin, "target_node_id": tgt, "target_pin_name": tpin}
    if fg: p["function_name"] = fg
    return ok(mcp("connect_nodes", p), f"conn({spin}→{tpin})")

def func(bp, name, inputs=None, outputs=None):
    bp_full = f"{BP_PATH}/{bp}"
    ok(mcp("create_function", {"blueprint_name": bp_full, "function_name": name}), f"func({name})")
    for inp in (inputs or []):
        ok(mcp("add_function_input", {"blueprint_name": bp_full, "function_name": name, "param_name": inp["name"], "param_type": inp["type"]}), f"  in({inp['name']})")
    for out in (outputs or []):
        ok(mcp("add_function_output", {"blueprint_name": bp_full, "function_name": name, "param_name": out["name"], "param_type": out["type"]}), f"  out({out['name']})")

def compile(bp):
    return ok(mcp("compile_blueprint", {"blueprint_name": bp}), f"compile({bp})")

def spawn(bp_name, actor_name, loc, rot=None):
    p = {"blueprint_name": bp_name, "actor_name": actor_name, "location": loc}
    if rot: p["rotation"] = rot
    return ok(mcp("spawn_blueprint_actor", p), f"spawn({actor_name})")


# ═══════════════════════════════════════════════════════════════════
# STEP 1: Marker Blueprints
# ═══════════════════════════════════════════════════════════════════

def step1():
    print("\n" + "="*60 + "\nSTEP 1: Marker Blueprints\n" + "="*60)

    # ── BP_SafeNode ──
    bp = "BP_SafeNode"
    print(f"\n--- {bp} ---")
    create_bp(bp)
    add_comp(bp, SM, "BaseMesh", scale=[0.5,0.5,0.1], props={"static_mesh":"/Engine/BasicShapes/Cylinder"})
    add_comp(bp, SM, "GlowMesh", location=[0,0,50], scale=[0.3,0.3,0.3], props={"static_mesh":"/Engine/BasicShapes/Sphere"})
    add_comp(bp, SPHERE, "TriggerVolume", props={"sphere_radius":200})
    var(bp, "bIsActive", "bool", "true", "Config")
    var(bp, "NodeLabel", "string", "Safe Node", "Config")
    var(bp, "HealAmount", "float", "0.0", "Config")

    e1 = event(bp, "ReceiveBeginPlay", 0, 0)
    n1 = node(bp, "VariableGet", {"variable_name":"NodeLabel","pos_x":200,"pos_y":100})
    n2 = node(bp, "CallFunction", {"target_function":"PrintString","pos_x":400,"pos_y":0})
    conn(bp, e1, "then", n2, "execute")
    conn(bp, n1, "NodeLabel", n2, "InString")

    e2 = event(bp, "ReceiveActorBeginOverlap", 0, 300)
    n3 = node(bp, "VariableGet", {"variable_name":"bIsActive","pos_x":200,"pos_y":400})
    n4 = node(bp, "Branch", {"pos_x":400,"pos_y":300})
    n5 = node(bp, "CallFunction", {"target_function":"PrintString","pos_x":600,"pos_y":300,"message":"Safe Node Activated"})
    conn(bp, e2, "then", n4, "execute")
    conn(bp, n3, "bIsActive", n4, "Condition")
    conn(bp, n4, "then", n5, "execute")
    compile(bp)

    # ── BP_AscensionGate ──
    bp = "BP_AscensionGate"
    print(f"\n--- {bp} ---")
    create_bp(bp)
    add_comp(bp, SM, "GateFrameLeft", location=[-100,0,150], scale=[0.1,0.3,3.0], props={"static_mesh":"/Engine/BasicShapes/Cube"})
    add_comp(bp, SM, "GateFrameRight", location=[100,0,150], scale=[0.1,0.3,3.0], props={"static_mesh":"/Engine/BasicShapes/Cube"})
    add_comp(bp, SM, "GateLintel", location=[0,0,310], scale=[2.2,0.3,0.2], props={"static_mesh":"/Engine/BasicShapes/Cube"})
    add_comp(bp, BOX, "TriggerVolume", props={"box_extent":[100,50,150]})
    var(bp, "bIsUnlocked", "bool", "false", "Config")
    var(bp, "RequiredKillCount", "int", "0", "Config")
    var(bp, "GateLabel", "string", "Ascension Gate", "Config")
    var(bp, "DestinationMap", "string", "", "Config")

    e1 = event(bp, "ReceiveActorBeginOverlap", 0, 0)
    n1 = node(bp, "VariableGet", {"variable_name":"bIsUnlocked","pos_x":200,"pos_y":100})
    n2 = node(bp, "Branch", {"pos_x":400,"pos_y":0})
    n3 = node(bp, "CallFunction", {"target_function":"PrintString","pos_x":600,"pos_y":0,"message":"Gate Open"})
    conn(bp, e1, "then", n2, "execute")
    conn(bp, n1, "bIsUnlocked", n2, "Condition")
    conn(bp, n2, "then", n3, "execute")
    compile(bp)

    # ── BP_SystemNoticePlaque ──
    bp = "BP_SystemNoticePlaque"
    print(f"\n--- {bp} ---")
    create_bp(bp)
    add_comp(bp, SM, "PlaqueMesh", scale=[1,0.05,0.6], props={"static_mesh":"/Engine/BasicShapes/Cube"})
    add_comp(bp, BOX, "TriggerVolume", location=[0,100,0], props={"box_extent":[100,100,100]})
    var(bp, "NoticeText", "string", "System Notice", "Config")
    var(bp, "bHasBeenRead", "bool", "false", "State")

    e1 = event(bp, "ReceiveActorBeginOverlap", 0, 0)
    n1 = node(bp, "VariableGet", {"variable_name":"bHasBeenRead","pos_x":200,"pos_y":100})
    n2 = node(bp, "Branch", {"pos_x":400,"pos_y":0})
    n3 = node(bp, "VariableGet", {"variable_name":"NoticeText","pos_x":400,"pos_y":150})
    n4 = node(bp, "CallFunction", {"target_function":"PrintString","pos_x":600,"pos_y":0})
    n5 = node(bp, "VariableSet", {"variable_name":"bHasBeenRead","pos_x":800,"pos_y":0})
    conn(bp, e1, "then", n2, "execute")
    # Use NOT bHasBeenRead as condition: invert the bool
    # Since BooleanNOT doesn't exist as a node type, use Comparison with NOT operator
    # Actually, just branch on bHasBeenRead and use the "else" (false) path
    conn(bp, n1, "bHasBeenRead", n2, "Condition")
    conn(bp, n2, "else", n4, "execute")  # When NOT read (bHasBeenRead=false), go to print
    conn(bp, n3, "NoticeText", n4, "InString")
    conn(bp, n4, "then", n5, "execute")
    compile(bp)

    print("\n✓ Step 1 complete!")


# ═══════════════════════════════════════════════════════════════════
# STEP 2: BP_GameConfig
# ═══════════════════════════════════════════════════════════════════

def step2():
    print("\n" + "="*60 + "\nSTEP 2: BP_GameConfig\n" + "="*60)
    bp = "BP_GameConfig"
    create_bp(bp)
    for n,v in [("MapName_SystemTest","Map_SystemTest"),("MapName_HubCity","Map_HubCitadelCity"),
                ("MapName_Floor01","Map_Floor01_Ironcatacomb"),("MapName_Floor02","Map_Floor02_VerdantRuins"),
                ("MapName_Floor03","Map_Floor03_Skyforge")]:
        var(bp, n, "string", v, "Map Config")
    for f in ["01","02","03"]:
        var(bp, f"Floor{f}_RoomCount", "int", "3", "Floor Config")
        var(bp, f"Floor{f}_SpawnTag", "string", f"SpawnGroup_Floor{f}", "Floor Config")
    var(bp, "Floor01_BossGateKills", "int", "10", "Floor Config")
    var(bp, "Floor02_BossGateKills", "int", "15", "Floor Config")
    var(bp, "Floor03_BossGateKills", "int", "20", "Floor Config")
    func(bp, "GetMapNameForFloor", [{"name":"FloorIndex","type":"int"}], [{"name":"MapName","type":"string"}])
    func(bp, "GetRoomCountForFloor", [{"name":"FloorIndex","type":"int"}], [{"name":"RoomCount","type":"int"}])
    func(bp, "GetSpawnTagForFloor", [{"name":"FloorIndex","type":"int"}], [{"name":"SpawnTag","type":"string"}])
    compile(bp)
    print("\n✓ Step 2 complete!")


# ═══════════════════════════════════════════════════════════════════
# STEP 3: Enemy Framework
# ═══════════════════════════════════════════════════════════════════

def step3():
    print("\n" + "="*60 + "\nSTEP 3: Enemy Framework\n" + "="*60)
    bp = "BP_EnemyBase"
    print(f"\n--- {bp} ---")
    create_bp(bp, "Character")
    add_comp(bp, SPHERE, "DetectionSphere", props={"sphere_radius":1200})
    add_comp(bp, SPHERE, "AttackRangeSphere", props={"sphere_radius":200})
    add_comp(bp, BOX, "WeaponCollision", props={"box_extent":[30,30,50]})

    for n,t,d,c in [
        ("MaxHealth","float","80.0","Health"),("CurrentHealth","float","80.0","Health"),("bIsDead","bool","false","Health"),
        ("AttackDamage","float","15.0","Combat"),("AttackCooldown","float","2.0","Combat"),
        ("WindupDuration","float","0.8","Combat"),("RecoveryDuration","float","1.0","Combat"),
        ("StaggerDuration","float","1.5","Combat"),("StaggerThreshold","float","30.0","Combat"),
        ("AccumulatedStagger","float","0.0","Combat"),("HitReactDuration","float","0.5","Combat"),
        ("ChaseSpeed","float","400.0","Movement"),("AttackRange","float","200.0","Movement"),
        ("DetectionRange","float","1200.0","Movement"),
        ("CurrentStateIndex","int","0","State"),("StateTimer","float","0.0","State"),
        ("bPlayerDetected","bool","false","State"),("bPlayerInRange","bool","false","State"),
        ("bIsRanged","bool","false","Config"),
    ]:
        var(bp, n, t, d, c)

    func(bp, "ReceiveDamage", [{"name":"DamageAmount","type":"float"}])
    func(bp, "EnterState", [{"name":"NewState","type":"int"}])
    func(bp, "TickStateMachine", [{"name":"DeltaTime","type":"float"}])
    for fn in ["TickIdle","TickChase","TickWindup","TickAttack","TickRecover","TickStunned","TickHitReact","Die"]:
        func(bp, fn)

    e1 = event(bp, "ReceiveBeginPlay", 0, 0)
    n1 = node(bp, "CallFunction", {"target_function":"PrintString","pos_x":300,"pos_y":0,"message":"Enemy Spawned"})
    conn(bp, e1, "then", n1, "execute")

    e2 = event(bp, "ReceiveTick", 0, 300)
    n2 = node(bp, "VariableGet", {"variable_name":"bIsDead","pos_x":200,"pos_y":400})
    n3 = node(bp, "Branch", {"pos_x":400,"pos_y":300})
    n4 = node(bp, "CallFunction", {"target_function":"TickStateMachine","pos_x":600,"pos_y":300})
    conn(bp, e2, "then", n3, "execute")
    conn(bp, n2, "bIsDead", n3, "Condition")
    conn(bp, n3, "else", n4, "execute")  # When NOT dead (bIsDead=false), tick state machine
    compile(bp)

    # Child blueprints
    children = {
        "BP_Enemy_Thrall": {"MaxHealth":"60","AttackDamage":"12","ChaseSpeed":"300","WindupDuration":"1.2","RecoveryDuration":"1.5","AttackRange":"180"},
        "BP_Enemy_Skitter": {"MaxHealth":"30","AttackDamage":"8","ChaseSpeed":"600","WindupDuration":"0.4","RecoveryDuration":"0.5","AttackRange":"150","StaggerThreshold":"15"},
        "BP_Enemy_Hexer": {"MaxHealth":"45","AttackDamage":"18","ChaseSpeed":"250","WindupDuration":"1.0","RecoveryDuration":"2.0","AttackRange":"800","DetectionRange":"1500","bIsRanged":"true"},
        "BP_Elite_Oathguard": {"MaxHealth":"200","AttackDamage":"35","ChaseSpeed":"280","WindupDuration":"1.5","RecoveryDuration":"2.0","AttackRange":"250","StaggerThreshold":"60"},
    }
    for child, overrides in children.items():
        print(f"\n--- {child} ---")
        ok(mcp("create_blueprint", {"name":child,"parent_class":"BP_EnemyBase","path":BP_PATH}), f"create({child})")
        for vn, vv in overrides.items():
            set_var(child, vn, vv)
        compile(child)

    print("\n--- Oathguard extras ---")
    var("BP_Elite_Oathguard", "bHasShield", "bool", "true", "Shield")
    var("BP_Elite_Oathguard", "ShieldHealth", "float", "100.0", "Shield")
    compile("BP_Elite_Oathguard")
    print("\n✓ Step 3 complete!")


# ═══════════════════════════════════════════════════════════════════
# STEP 4: BP_PlayerCharacter
# ═══════════════════════════════════════════════════════════════════

def step4():
    print("\n" + "="*60 + "\nSTEP 4: BP_PlayerCharacter\n" + "="*60)
    bp = "BP_PlayerCharacter"
    create_bp(bp, "Character")
    add_comp(bp, SPRING, "CameraBoom")
    add_comp(bp, CAM, "FollowCamera")

    for n,t,d,c in [
        ("MaxHealth","float","100.0","Health"),("CurrentHealth","float","100.0","Health"),("bIsDead","bool","false","Health"),
        ("MaxStamina","float","100.0","Stamina"),("CurrentStamina","float","100.0","Stamina"),
        ("StaminaRegenRate","float","15.0","Stamina"),("StaminaRegenDelay","float","1.0","Stamina"),
        ("bCanRegenStamina","bool","true","Stamina"),("StaminaRegenTimer","float","0.0","Stamina"),
        ("DodgeCost","float","25.0","Stamina"),("BlockDrainRate","float","10.0","Stamina"),
        ("ComboIndex","int","0","Combat"),("bCanCombo","bool","false","Combat"),
        ("bIsAttacking","bool","false","Combat"),("bIsBlocking","bool","false","Combat"),
        ("bIsDodging","bool","false","Combat"),("bParryWindowActive","bool","false","Combat"),
        ("ParryWindowDuration","float","0.2","Combat"),("LightAttackDamage","float","20.0","Combat"),
        ("HeavyAttackDamage","float","45.0","Combat"),("ComboResetTime","float","1.5","Combat"),
        ("LastAttackTime","float","0.0","Combat"),("bIsInvincible","bool","false","Combat"),
        ("bSwordSkillReady","bool","true","SwordSkill"),("SwordSkillCooldown","float","8.0","SwordSkill"),
        ("SwordSkillDamage","float","60.0","SwordSkill"),("SwordSkillCooldownRemaining","float","0.0","SwordSkill"),
        ("bIsLockedOn","bool","false","LockOn"),("LockOnRange","float","1500.0","LockOn"),
        ("HealthPercent","float","1.0","HUD"),("StaminaPercent","float","1.0","HUD"),("CooldownPercent","float","0.0","HUD"),
    ]:
        var(bp, n, t, d, c)

    func(bp, "TakeDamageCustom", [{"name":"DamageAmount","type":"float"}])
    for fn in ["TryLightAttack","TryHeavyAttack","TryDodge","StartBlock","StopBlock","TrySwordSkill","OnParrySuccess","Die"]:
        func(bp, fn)
    func(bp, "UpdateStaminaRegen", [{"name":"DeltaTime","type":"float"}])
    func(bp, "UpdateSwordSkillCooldown", [{"name":"DeltaTime","type":"float"}])
    func(bp, "UpdateHUDValues")
    func(bp, "ResetAttackState")

    e1 = event(bp, "ReceiveBeginPlay", 0, 0)
    n1 = node(bp, "CallFunction", {"target_function":"PrintString","pos_x":300,"pos_y":0,"message":"PlayerCharacter Ready"})
    conn(bp, e1, "then", n1, "execute")

    e2 = event(bp, "ReceiveTick", 0, 250)
    n2 = node(bp, "CallFunction", {"target_function":"UpdateStaminaRegen","pos_x":300,"pos_y":250})
    n3 = node(bp, "CallFunction", {"target_function":"UpdateSwordSkillCooldown","pos_x":550,"pos_y":250})
    n4 = node(bp, "CallFunction", {"target_function":"UpdateHUDValues","pos_x":800,"pos_y":250})
    conn(bp, e2, "then", n2, "execute")
    conn(bp, n2, "then", n3, "execute")
    conn(bp, n3, "then", n4, "execute")
    compile(bp)
    print("\n✓ Step 4 complete!")


# ═══════════════════════════════════════════════════════════════════
# STEP 5: BP_SystemManager
# ═══════════════════════════════════════════════════════════════════

def step5():
    print("\n" + "="*60 + "\nSTEP 5: BP_SystemManager\n" + "="*60)
    bp = "BP_SystemManager"
    create_bp(bp)
    for n,t,d,c in [
        ("CurrentDirective","string","","Directive"),("bDirectiveActive","bool","false","Directive"),
        ("DirectiveDisplayTime","float","5.0","Directive"),("DirectiveTimer","float","0.0","Directive"),
        ("ProviderModeIndex","int","0","Provider"),("ScriptedDirectiveIndex","int","0","Provider"),
        ("DirectiveText_0","string","The Citadel remembers those who strike with purpose.","Directives"),
        ("DirectiveText_1","string","Contracts bind the willing. Seek the next challenge.","Directives"),
        ("DirectiveText_2","string","The Oathguard watches. Approach with caution.","Directives"),
        ("DirectiveText_3","string","Safe nodes offer respite. Use them wisely.","Directives"),
        ("DirectiveText_4","string","Ascension awaits beyond the gate. Prove your worth.","Directives"),
    ]:
        var(bp, n, t, d, c)
    func(bp, "RequestDirective")
    func(bp, "GetScriptedDirective", outputs=[{"name":"DirectiveText","type":"string"}])
    func(bp, "ShowDirective", [{"name":"Text","type":"string"}])
    func(bp, "ClearDirective")
    func(bp, "GetCurrentDirective", outputs=[{"name":"Directive","type":"string"}])

    e1 = event(bp, "ReceiveBeginPlay", 0, 0)
    n1 = node(bp, "CallFunction", {"target_function":"RequestDirective","pos_x":300,"pos_y":0})
    n2 = node(bp, "CallFunction", {"target_function":"PrintString","pos_x":550,"pos_y":0,"message":"SystemManager Init"})
    conn(bp, e1, "then", n1, "execute")
    conn(bp, n1, "then", n2, "execute")
    compile(bp)
    print("\n✓ Step 5 complete!")


# ═══════════════════════════════════════════════════════════════════
# STEP 6: BP_ContractManager
# ═══════════════════════════════════════════════════════════════════

def step6():
    print("\n" + "="*60 + "\nSTEP 6: BP_ContractManager\n" + "="*60)
    bp = "BP_ContractManager"
    create_bp(bp)
    for n,t,d,c in [
        ("ActiveContractType","int","-1","Contract"),("bContractActive","bool","false","Contract"),
        ("ContractTimer","float","0.0","Contract"),("ContractTargetTime","float","30.0","Contract"),
        ("ContractTargetCount","int","3","Contract"),("ParryChainCount","int","0","Tracking"),
        ("KillCount","int","0","Tracking"),("bPlayerTookDamage","bool","false","Tracking"),
        ("bPlayerHealed","bool","false","Tracking"),("ContractDescription","string","","Contract"),
    ]:
        var(bp, n, t, d, c)
    func(bp, "OfferContract", [{"name":"TypeIndex","type":"int"}])
    func(bp, "AcceptContract"); func(bp, "UpdateContract", [{"name":"DeltaTime","type":"float"}])
    func(bp, "ContractSuccess"); func(bp, "ContractFail")
    func(bp, "OnPlayerDamaged"); func(bp, "OnPlayerParried"); func(bp, "OnEnemyKilled"); func(bp, "OnPlayerHealed")
    func(bp, "GetContractDescription", outputs=[{"name":"Description","type":"string"}])

    e1 = event(bp, "ReceiveTick", 0, 0)
    n1 = node(bp, "VariableGet", {"variable_name":"bContractActive","pos_x":200,"pos_y":100})
    n2 = node(bp, "Branch", {"pos_x":400,"pos_y":0})
    n3 = node(bp, "CallFunction", {"target_function":"UpdateContract","pos_x":600,"pos_y":0})
    conn(bp, e1, "then", n2, "execute")
    conn(bp, n1, "bContractActive", n2, "Condition")
    conn(bp, n2, "then", n3, "execute")
    compile(bp)
    print("\n✓ Step 6 complete!")


# ═══════════════════════════════════════════════════════════════════
# STEP 7: BP_HUDManager
# ═══════════════════════════════════════════════════════════════════

def step7():
    print("\n" + "="*60 + "\nSTEP 7: BP_HUDManager\n" + "="*60)
    bp = "BP_HUDManager"
    create_bp(bp)
    var(bp, "bHUDCreated", "bool", "false", "State")
    var(bp, "bMenuOpen", "bool", "false", "State")
    func(bp, "CreateHUD"); func(bp, "UpdateHealth", [{"name":"Percent","type":"float"}])
    func(bp, "UpdateStamina", [{"name":"Percent","type":"float"}]); func(bp, "UpdateCooldown", [{"name":"Percent","type":"float"}])
    func(bp, "ShowNotice", [{"name":"Text","type":"string"},{"name":"Duration","type":"float"}])
    func(bp, "ShowDirective", [{"name":"Text","type":"string"}]); func(bp, "ToggleMenu")

    e1 = event(bp, "ReceiveBeginPlay", 0, 0)
    n1 = node(bp, "CallFunction", {"target_function":"CreateHUD","pos_x":300,"pos_y":0})
    n2 = node(bp, "CallFunction", {"target_function":"PrintString","pos_x":550,"pos_y":0,"message":"HUD Ready"})
    conn(bp, e1, "then", n1, "execute")
    conn(bp, n1, "then", n2, "execute")
    compile(bp)
    print("\n✓ Step 7 complete!")


# ═══════════════════════════════════════════════════════════════════
# STEP 8: BP_SignalBoundGameMode
# ═══════════════════════════════════════════════════════════════════

def step8():
    print("\n" + "="*60 + "\nSTEP 8: BP_SignalBoundGameMode\n" + "="*60)
    bp = "BP_SignalBoundGameMode"
    create_bp(bp, "GameModeBase")
    e1 = event(bp, "ReceiveBeginPlay", 0, 0)
    n1 = node(bp, "CallFunction", {"target_function":"PrintString","pos_x":300,"pos_y":0,"message":"SignalBound GameMode Active"})
    conn(bp, e1, "then", n1, "execute")
    compile(bp)
    print("\n✓ Step 8 complete!")


# ═══════════════════════════════════════════════════════════════════
# STEP 9: Populate Map_HubCitadelCity
# ═══════════════════════════════════════════════════════════════════

def step9():
    print("\n" + "="*60 + "\nSTEP 9: Populate Map_HubCitadelCity\n" + "="*60)

    print("\n--- Safe Nodes ---")
    spawn("BP_SafeNode", "SafeNode_MonumentHall", [-8000, 0, 50])
    spawn("BP_SafeNode", "SafeNode_AltarGrounds", [5000, -5000, 100])
    spawn("BP_SafeNode", "SafeNode_NorthGarden", [0, 8000, 50])

    print("\n--- Ascension Gate ---")
    spawn("BP_AscensionGate", "AscensionGate_GuardianPath", [15000, -3000, 50])

    print("\n--- Notice Plaques ---")
    spawn("BP_SystemNoticePlaque", "Plaque_Welcome", [0, -2000, 80])
    spawn("BP_SystemNoticePlaque", "Plaque_GuardianWarning", [11000, -4000, 100])
    spawn("BP_SystemNoticePlaque", "Plaque_AltarLore", [3000, -6000, 120])

    print("\n--- Enemies ---")
    spawn("BP_Enemy_Thrall", "Thrall_HallPatrol_01", [-5000, -3000, 50])
    spawn("BP_Enemy_Thrall", "Thrall_HallPatrol_02", [-5000, 3000, 50])
    spawn("BP_Enemy_Skitter", "Skitter_Path_01", [3000, 5000, 50])
    spawn("BP_Enemy_Skitter", "Skitter_Path_02", [7000, -3000, 50])
    spawn("BP_Enemy_Hexer", "Hexer_AltarWatch", [8000, -7000, 200])
    spawn("BP_Elite_Oathguard", "Oathguard_Guardian", [13000, -5000, 100])

    print("\n--- System Actors ---")
    spawn("BP_GameConfig", "GameConfig", [0, 0, -100])
    spawn("BP_SystemManager", "SystemManager", [0, 0, -200])
    spawn("BP_ContractManager", "ContractManager", [0, 0, -300])
    spawn("BP_HUDManager", "HUDManager", [0, 0, -400])

    print("\n✓ Step 9 complete!")


# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("SignalBound Phase 1 Builder v2")
    print("Target: Map_HubCitadelCity")
    r = mcp("ping")
    if not r or r.get("status") != "success":
        print("ERROR: MCP not reachable"); sys.exit(1)
    print("Connected!\n")

    ALL = {"1":step1,"2":step2,"3":step3,"4":step4,"5":step5,"6":step6,"7":step7,"8":step8,"9":step9}
    targets = sys.argv[1:] if len(sys.argv) > 1 else sorted(ALL.keys())
    for s in targets:
        if s in ALL: ALL[s]()
    print("\n" + "="*60 + "\nALL DONE!\n" + "="*60)
